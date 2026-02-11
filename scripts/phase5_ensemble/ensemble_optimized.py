#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ensemble_optimized.py
Phase 5 最適化アンサンブル統合スクリプト

Phase 7 (Boruta特徴選択) + Phase 8 (Optuna最適化) の結果を統合し、
3つの最適化モデル（Binary, Ranking, Regression）をアンサンブル統合します。

統合戦略:
    1. Binary分類 (30%): 複勝圏内確率
    2. Ranking予測 (50%): 相対的な強さ順位
    3. Regression予測 (20%): 走破タイム予測
    
最適化ポイント:
    - Phase 7で各モデル専用に選択された特徴量を使用
    - Phase 8でOptunaチューニング済みのモデルを使用
    - レースごとにスコア正規化して公平に統合
    
使用法:
    python ensemble_optimized.py <会場名> <予測対象CSVファイル> [オプション]
    
例:
    python ensemble_optimized.py funabashi test_data/funabashi_20260210.csv
    python ensemble_optimized.py kawasaki test_data/kawasaki_20260210.csv --output-dir predictions/
    
オプション:
    --output-dir DIR           出力ディレクトリ（デフォルト: data/predictions/phase5_optimized/）
    --weight-binary WEIGHT     Binary分類の重み（デフォルト: 0.3）
    --weight-ranking WEIGHT    Ranking予測の重み（デフォルト: 0.5）
    --weight-regression WEIGHT Regression予測の重み（デフォルト: 0.2）
    
出力:
    - {venue}_{date}_ensemble_optimized.csv: アンサンブル統合予測結果
    - {venue}_{date}_ensemble_optimized_summary.json: 統計サマリー
"""

import sys
import os
import pandas as pd
import numpy as np
import json
import argparse
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# LightGBMはモデル読み込み時にのみインポート
try:
    import lightgbm as lgb
except ImportError:
    print("❌ エラー: lightgbmがインストールされていません")
    print("  pip install lightgbm")
    sys.exit(1)


def normalize_score(series, ascending=True):
    """
    スコアを0〜1に正規化
    
    Parameters
    ----------
    series : pd.Series
        正規化するスコア
    ascending : bool
        True: 小さいほど良い（時間など）
        False: 大きいほど良い（確率など）
    
    Returns
    -------
    pd.Series
        正規化されたスコア（0〜1）
    """
    min_val = series.min()
    max_val = series.max()
    
    if max_val == min_val:
        # 全て同じ値の場合は0.5を返す
        return pd.Series([0.5] * len(series), index=series.index)
    
    if ascending:
        # 小さいほど良い場合（時間など）
        # 最小値→1.0, 最大値→0.0
        normalized = 1.0 - (series - min_val) / (max_val - min_val)
    else:
        # 大きいほど良い場合（確率など）
        # 最小値→0.0, 最大値→1.0
        normalized = (series - min_val) / (max_val - min_val)
    
    return normalized


def load_selected_features(venue, model_type):
    """
    Phase 7で選択された特徴量リストを読み込み
    
    Args:
        venue: 会場名（例: 'funabashi', 'kawasaki'）
        model_type: モデルタイプ（'binary', 'ranking', 'regression'）
    
    Returns:
        list: 選択された特徴量名のリスト
    """
    features_dir = project_root / "data" / "features" / "selected"
    
    if model_type == "binary":
        # Binary用特徴量（Phase 7標準）
        feature_file = features_dir / f"{venue}_selected_features.csv"
    elif model_type == "ranking":
        # Ranking専用特徴量
        feature_file = features_dir / f"{venue}_ranking_selected_features.csv"
    elif model_type == "regression":
        # Regression専用特徴量
        feature_file = features_dir / f"{venue}_regression_selected_features.csv"
    else:
        raise ValueError(f"未対応のモデルタイプ: {model_type}")
    
    if not feature_file.exists():
        print(f"⚠️  警告: 特徴量ファイルが見つかりません - {feature_file}")
        return None
    
    df_features = pd.read_csv(feature_file, encoding='utf-8')
    features = df_features['feature'].tolist()
    
    print(f"  ✅ {model_type.capitalize()}用特徴量読み込み完了: {len(features)}個")
    return features


def load_tuned_model(venue, model_type):
    """
    Phase 8でOptunaチューニング済みのモデルを読み込み
    
    Args:
        venue: 会場名（例: 'funabashi', 'kawasaki'）
        model_type: モデルタイプ（'binary', 'ranking', 'regression'）
    
    Returns:
        lgb.Booster: 読み込んだLightGBMモデル
    """
    models_dir = project_root / "data" / "models" / "tuned"
    
    if model_type == "binary":
        # Binary分類モデル
        model_file = models_dir / f"{venue}_tuned_model.txt"
    elif model_type == "ranking":
        # Rankingモデル
        model_file = models_dir / f"{venue}_ranking_tuned_model.txt"
    elif model_type == "regression":
        # Regressionモデル
        model_file = models_dir / f"{venue}_regression_tuned_model.txt"
    else:
        raise ValueError(f"未対応のモデルタイプ: {model_type}")
    
    if not model_file.exists():
        raise FileNotFoundError(f"モデルファイルが見つかりません: {model_file}")
    
    model = lgb.Booster(model_file=str(model_file))
    print(f"  ✅ {model_type.capitalize()}モデル読み込み完了: {model_file.name}")
    
    return model


def predict_with_model(df, venue, model_type, selected_features=None):
    """
    指定されたモデルタイプで予測を実行
    
    Args:
        df: 予測対象データ
        venue: 会場名
        model_type: モデルタイプ（'binary', 'ranking', 'regression'）
        selected_features: 使用する特徴量リスト（Noneの場合は全特徴量）
    
    Returns:
        np.ndarray: 予測結果
    """
    # モデル読み込み
    model = load_tuned_model(venue, model_type)
    
    # 特徴量選択
    if selected_features is None:
        # デフォルトの特徴量カラムを取得
        exclude_cols = {'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
                       'race_bango', 'ketto_toroku_bango', 'umaban',
                       'binary_target', 'rank_target', 'time'}
        feature_cols = [col for col in df.columns if col not in exclude_cols]
    else:
        # Boruta選択済み特徴量を使用
        feature_cols = selected_features
    
    # 欠損している特徴量をチェック
    missing_features = [f for f in feature_cols if f not in df.columns]
    if missing_features:
        print(f"⚠️  警告: 以下の特徴量がデータに存在しません:")
        for f in missing_features[:5]:
            print(f"    - {f}")
        if len(missing_features) > 5:
            print(f"    ... 他 {len(missing_features) - 5}個")
        
        # 存在する特徴量のみ使用
        feature_cols = [f for f in feature_cols if f in df.columns]
    
    X = df[feature_cols].copy()
    
    # 予測実行
    if model_type == "binary":
        # Binary分類: 確率を返す
        predictions = model.predict(X)
    elif model_type == "ranking":
        # Ranking: スコアを返す（高いほど上位）
        predictions = model.predict(X)
    elif model_type == "regression":
        # Regression: 走破タイム（1/10秒単位）
        predictions = model.predict(X)
    else:
        raise ValueError(f"未対応のモデルタイプ: {model_type}")
    
    return predictions


def ensemble_optimized_predictions(df, venue, 
                                   weight_binary=0.3, 
                                   weight_ranking=0.5, 
                                   weight_regression=0.2):
    """
    Phase 7 + Phase 8 最適化結果をアンサンブル統合
    
    Args:
        df: 予測対象データ
        venue: 会場名
        weight_binary: Binary分類の重み（デフォルト: 0.3）
        weight_ranking: Ranking予測の重み（デフォルト: 0.5）
        weight_regression: Regression予測の重み（デフォルト: 0.2）
    
    Returns:
        pd.DataFrame: アンサンブル統合後の予測結果
    """
    print("\n" + "=" * 80)
    print(f"Phase 5 最適化アンサンブル統合（会場: {venue.upper()}）")
    print("=" * 80)
    
    # 重みの検証
    total_weight = weight_binary + weight_ranking + weight_regression
    if not np.isclose(total_weight, 1.0):
        print(f"⚠️  警告: 重みの合計が1.0ではありません ({total_weight:.2f})")
        print(f"  - 自動正規化します")
        weight_binary /= total_weight
        weight_ranking /= total_weight
        weight_regression /= total_weight
    
    print(f"\n重み設定:")
    print(f"  - Binary分類    : {weight_binary:.1%}")
    print(f"  - Ranking予測   : {weight_ranking:.1%}")
    print(f"  - Regression予測: {weight_regression:.1%}")
    
    # データ確認
    print(f"\n[1/6] データ確認")
    print(f"  - レコード数: {len(df):,}件")
    print(f"  - レース数: {df['race_id'].nunique()}件")
    print(f"  - カラム数: {len(df.columns)}個")
    
    # Phase 7特徴量読み込み
    print(f"\n[2/6] Phase 7 Boruta選択済み特徴量読み込み")
    binary_features = load_selected_features(venue, "binary")
    ranking_features = load_selected_features(venue, "ranking")
    regression_features = load_selected_features(venue, "regression")
    
    # Phase 8モデル予測
    print(f"\n[3/6] Phase 8 最適化モデルで予測実行")
    
    print(f"  [Binary分類] 予測中...")
    df['binary_probability'] = predict_with_model(df, venue, "binary", binary_features)
    print(f"    - 平均確率: {df['binary_probability'].mean():.4f}")
    
    print(f"  [Ranking予測] 予測中...")
    df['ranking_score'] = predict_with_model(df, venue, "ranking", ranking_features)
    print(f"    - 平均スコア: {df['ranking_score'].mean():.4f}")
    
    print(f"  [Regression予測] 予測中...")
    df['predicted_time'] = predict_with_model(df, venue, "regression", regression_features)
    print(f"    - 平均タイム: {df['predicted_time'].mean():.2f} (1/10秒単位)")
    
    # スコア正規化
    print(f"\n[4/6] スコア正規化（レース単位で0〜1に変換）")
    
    # レースごとに正規化
    df['binary_normalized'] = df.groupby('race_id')['binary_probability'].transform(
        lambda x: normalize_score(x, ascending=False)
    )
    print(f"  ✅ Binary正規化完了")
    
    df['ranking_normalized'] = df.groupby('race_id')['ranking_score'].transform(
        lambda x: normalize_score(x, ascending=False)
    )
    print(f"  ✅ Ranking正規化完了")
    
    df['regression_normalized'] = df.groupby('race_id')['predicted_time'].transform(
        lambda x: normalize_score(x, ascending=True)
    )
    print(f"  ✅ Regression正規化完了")
    
    # アンサンブルスコア計算
    print(f"\n[5/6] アンサンブルスコア計算")
    
    df['ensemble_score'] = (
        df['binary_normalized'] * weight_binary +
        df['ranking_normalized'] * weight_ranking +
        df['regression_normalized'] * weight_regression
    )
    
    print(f"  ✅ アンサンブルスコア計算完了")
    print(f"    - 平均スコア: {df['ensemble_score'].mean():.4f}")
    print(f"    - 最大スコア: {df['ensemble_score'].max():.4f}")
    print(f"    - 最小スコア: {df['ensemble_score'].min():.4f}")
    
    # 最終順位決定
    print(f"\n[6/6] 最終順位決定（レース単位）")
    
    df['final_rank'] = df.groupby('race_id')['ensemble_score'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    # 各モデルの順位も計算（比較用）
    df['binary_rank'] = df.groupby('race_id')['binary_probability'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    df['ranking_rank'] = df.groupby('race_id')['ranking_score'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    df['time_rank'] = df.groupby('race_id')['predicted_time'].rank(
        ascending=True, method='min'
    ).astype(int)
    
    print(f"  ✅ 最終順位計算完了")
    
    # レース別サマリー表示
    print(f"\n  【レース別予測サマリー（最初の5レース）】")
    for race_id in sorted(df['race_id'].unique())[:5]:
        race_data = df[df['race_id'] == race_id].sort_values('final_rank')
        top3 = race_data.head(3)
        race_num = int(str(race_id)[-2:])
        
        print(f"\n  第{race_num}R:")
        for idx, row in top3.iterrows():
            print(f"    {int(row['final_rank'])}位: {int(row['umaban'])}番 "
                  f"(統合スコア: {row['ensemble_score']:.4f})")
            print(f"        Binary={row['binary_probability']:.3f}(順位{int(row['binary_rank'])}), "
                  f"Ranking={row['ranking_score']:.2f}(順位{int(row['ranking_rank'])}), "
                  f"Time={row['predicted_time']:.1f}(順位{int(row['time_rank'])})")
    
    if df['race_id'].nunique() > 5:
        print(f"\n  ... 他 {df['race_id'].nunique() - 5}レース")
    
    return df


def save_predictions(df, venue, output_dir):
    """
    予測結果を保存
    
    Args:
        df: 予測結果データ
        venue: 会場名
        output_dir: 出力ディレクトリ
    
    Returns:
        str: 保存したファイルパス
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル名生成（日付を含む）
    if 'kaisai_tsukihi' in df.columns:
        first_date = df['kaisai_tsukihi'].iloc[0]
        date_str = str(first_date)
    else:
        date_str = datetime.now().strftime("%Y%m%d")
    
    output_file = output_dir / f"{venue}_{date_str}_ensemble_optimized.csv"
    
    # 出力カラム選択
    output_cols = [
        'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
        'ketto_toroku_bango', 'umaban',
        'ensemble_score', 'final_rank',
        'binary_probability', 'binary_rank',
        'ranking_score', 'ranking_rank',
        'predicted_time', 'time_rank'
    ]
    
    # 存在するカラムのみ選択
    output_cols = [col for col in output_cols if col in df.columns]
    df_output = df[output_cols].copy()
    
    # CSV保存
    try:
        df_output.to_csv(output_file, index=False, encoding='shift-jis')
        print(f"\n✅ 予測結果を保存（Shift-JIS）: {output_file}")
    except:
        output_file = output_dir / f"{venue}_{date_str}_ensemble_optimized_utf8.csv"
        df_output.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n✅ 予測結果を保存（UTF-8）: {output_file}")
    
    print(f"  - レコード数: {len(df_output):,}件")
    print(f"  - カラム数: {len(df_output.columns)}個")
    
    # サマリーJSONも保存
    summary = {
        'venue': venue,
        'date': date_str,
        'total_records': len(df_output),
        'total_races': df_output['race_id'].nunique(),
        'ensemble_score_stats': {
            'mean': float(df_output['ensemble_score'].mean()),
            'std': float(df_output['ensemble_score'].std()),
            'min': float(df_output['ensemble_score'].min()),
            'max': float(df_output['ensemble_score'].max())
        },
        'binary_probability_stats': {
            'mean': float(df_output['binary_probability'].mean()),
            'std': float(df_output['binary_probability'].std())
        },
        'ranking_score_stats': {
            'mean': float(df_output['ranking_score'].mean()),
            'std': float(df_output['ranking_score'].std())
        },
        'predicted_time_stats': {
            'mean': float(df_output['predicted_time'].mean()),
            'std': float(df_output['predicted_time'].std())
        }
    }
    
    summary_file = output_dir / f"{venue}_{date_str}_ensemble_optimized_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"  - サマリー: {summary_file}")
    
    return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description="Phase 5 最適化アンサンブル統合スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python ensemble_optimized.py funabashi test_data/funabashi_20260210.csv
  python ensemble_optimized.py kawasaki test_data/kawasaki_20260210.csv --output-dir predictions/
  python ensemble_optimized.py ohi test_data/ohi_20260210.csv --weight-binary 0.4 --weight-ranking 0.4 --weight-regression 0.2
        """
    )
    
    parser.add_argument('venue', type=str, help='会場名（例: funabashi, kawasaki, ohi）')
    parser.add_argument('input_csv', type=str, help='予測対象CSVファイル')
    parser.add_argument('--output-dir', type=str, 
                       default='data/predictions/phase5_optimized',
                       help='出力ディレクトリ（デフォルト: data/predictions/phase5_optimized/）')
    parser.add_argument('--weight-binary', type=float, default=0.3,
                       help='Binary分類の重み（デフォルト: 0.3）')
    parser.add_argument('--weight-ranking', type=float, default=0.5,
                       help='Ranking予測の重み（デフォルト: 0.5）')
    parser.add_argument('--weight-regression', type=float, default=0.2,
                       help='Regression予測の重み（デフォルト: 0.2）')
    
    args = parser.parse_args()
    
    # 入力ファイル確認
    if not os.path.exists(args.input_csv):
        print(f"❌ エラー: 入力ファイルが見つかりません - {args.input_csv}")
        sys.exit(1)
    
    # データ読み込み
    print("\n" + "=" * 80)
    print("データ読み込み中...")
    print("=" * 80)
    print(f"入力ファイル: {args.input_csv}")
    
    try:
        df = pd.read_csv(args.input_csv, encoding='shift-jis')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(args.input_csv, encoding='utf-8')
        except:
            df = pd.read_csv(args.input_csv, encoding='cp932')
    
    print(f"✅ データ読み込み完了: {len(df):,}件")
    
    # 必須カラム確認
    required_cols = ['race_id', 'umaban']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ エラー: 必須カラムが不足しています: {missing_cols}")
        sys.exit(1)
    
    try:
        # アンサンブル予測実行
        df_result = ensemble_optimized_predictions(
            df, args.venue,
            weight_binary=args.weight_binary,
            weight_ranking=args.weight_ranking,
            weight_regression=args.weight_regression
        )
        
        # 結果保存
        output_file = save_predictions(df_result, args.venue, args.output_dir)
        
        print("\n" + "=" * 80)
        print("✅ Phase 5 最適化アンサンブル統合完了")
        print("=" * 80)
        print(f"出力ファイル: {output_file}")
        
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 引数なしで実行された場合はヘルプを表示
        print(__doc__)
        sys.exit(0)
    
    main()
