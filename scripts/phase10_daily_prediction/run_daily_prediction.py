#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_daily_prediction.py
Phase 10: Phase 8最適化モデルを使った日次予測システム

Phase 8で最適化されたモデル（tuned_model.txt）とPhase 7で選択された特徴量を使用して、
当日の出走表データから予測を実行し、期待値ベースの購入推奨を生成します。

使用法:
    python run_daily_prediction.py --venue monbetsu --date 2026-02-11
    python run_daily_prediction.py --venue 44 --date 2026-02-11
    python run_daily_prediction.py --venue-code 44 --date 2026-02-11 --bankroll 100000

入力:
    - data/models/tuned/{venue}_tuned_model.txt: Phase 8で学習済みのモデル
    - data/features/selected/{venue}_selected_features.csv: Phase 7で選択された特徴量リスト
    - 当日の出走表データ（run_all.bat Phase 0-4で生成）
    
出力:
    - data/predictions/phase10/{venue}_{date}_predictions.csv: 予測結果
    - data/predictions/phase10/{venue}_{date}_recommended_bets.csv: 購入推奨
    - data/predictions/phase10/{venue}_{date}_summary.txt: サマリー
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import lightgbm as lgb
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Phase 9ベッティング戦略エンジンをインポート
try:
    from scripts.phase9_betting_strategy.betting_strategy_engine import BettingStrategyEngine
except ImportError:
    print("⚠️ Phase 9ベッティング戦略エンジンが見つかりません")
    BettingStrategyEngine = None


# 競馬場コード→名前の辞書
VENUE_CODE_TO_NAME = {
    '30': 'monbetsu', '35': 'morioka', '36': 'mizusawa', '42': 'urawa',
    '43': 'funabashi', '44': 'ooi', '45': 'kawasaki', '46': 'kanazawa',
    '47': 'kasamatsu', '48': 'nagoya', '50': 'sonoda', '51': 'himeji',
    '54': 'kochi', '55': 'saga',
}

VENUE_NAME_TO_JA = {
    'monbetsu': '門別', 'morioka': '盛岡', 'mizusawa': '水沢', 'urawa': '浦和',
    'funabashi': '船橋', 'ooi': '大井', 'kawasaki': '川崎', 'kanazawa': '金沢',
    'kasamatsu': '笠松', 'nagoya': '名古屋', 'sonoda': '園田', 'himeji': '姫路',
    'kochi': '高知', 'saga': '佐賀',
}


def load_tuned_model(venue_name):
    """
    Phase 8で学習済みのLightGBMモデルを読み込む
    
    Args:
        venue_name: 競馬場名（英語、例: monbetsu）
    
    Returns:
        lgb.Booster: 学習済みモデル
    """
    model_path = project_root / 'data' / 'models' / 'tuned' / f'{venue_name}_tuned_model.txt'
    
    if not model_path.exists():
        raise FileNotFoundError(f"❌ モデルファイルが見つかりません: {model_path}")
    
    print(f"✅ モデル読み込み: {model_path}")
    model = lgb.Booster(model_file=str(model_path))
    return model


def load_selected_features(venue_name):
    """
    Phase 7で選択された特徴量リストを読み込む
    
    Args:
        venue_name: 競馬場名（英語）
    
    Returns:
        list: 特徴量名のリスト
    """
    features_path = project_root / 'data' / 'features' / 'selected' / f'{venue_name}_selected_features.csv'
    
    if not features_path.exists():
        raise FileNotFoundError(f"❌ 特徴量ファイルが見つかりません: {features_path}")
    
    print(f"✅ 特徴量読み込み: {features_path}")
    df = pd.read_csv(features_path, encoding='utf-8')
    selected_features = df['feature'].tolist()
    print(f"  - 選択特徴量数: {len(selected_features)}個")
    
    return selected_features


def load_race_data(venue_code, target_date):
    """
    当日の出走表データを読み込む（Phase 1で生成された特徴量データ）
    
    Args:
        venue_code: 競馬場コード（例: 44）
        target_date: 対象日（例: 2026-02-11）
    
    Returns:
        pd.DataFrame: レースデータ
    """
    date_short = target_date.replace('-', '')  # 20260211形式
    
    # Phase 1の特徴量データのみを探す（50カラムの完全な特徴量データ）
    # data/features/YYYY/MM/*YYYYMMDD*_features.csv 形式
    year = target_date.split('-')[0]
    month = target_date.split('-')[1]
    
    search_patterns = [
        project_root / 'data' / 'features' / year / month / f'*{date_short}*features.csv',
        project_root / 'data' / 'features' / year / month / f'*{date_short}*.csv',
    ]
    
    for pattern in search_patterns:
        if not pattern.parent.exists():
            continue
            
        matches = list(pattern.parent.glob(pattern.name))
        
        # ensemble.csv を除外（Phase 5のアンサンブル結果は特徴量が含まれていない）
        matches = [m for m in matches if 'ensemble' not in m.name.lower()]
        
        if matches:
            csv_path = matches[0]
            print(f"✅ レースデータ読み込み: {csv_path}")
            
            # エンコーディング自動検出
            try:
                df = pd.read_csv(csv_path, encoding='shift-jis')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_path, encoding='utf-8')
            
            print(f"  - レコード数: {len(df)}件")
            print(f"  - カラム数: {len(df.columns)}個")
            
            # カラム数チェック（Phase 1のデータは通常40-50カラム）
            if len(df.columns) < 30:
                print(f"⚠️ 警告: カラム数が少ない({len(df.columns)}個)。Phase 1のデータではない可能性があります。")
                continue
            
            return df
    
    raise FileNotFoundError(
        f"❌ Phase 1の特徴量データが見つかりません\n"
        f"   競馬場コード: {venue_code}\n"
        f"   対象日: {target_date}\n"
        f"   探索パス: data/features/{year}/{month}/*{date_short}*features.csv\n"
        f"   \n"
        f"   Phase 1のデータを生成してください:\n"
        f"   > run_all.bat {venue_code} {target_date}"
    )


def predict(model, X, selected_features):
    """
    予測を実行
    
    Args:
        model: LightGBMモデル
        X: 入力データ（DataFrame）
        selected_features: Phase 7で選択された特徴量リスト
    
    Returns:
        np.ndarray: 予測確率
    """
    # デバッグ: 入力データのカラムを表示
    print(f"  - 入力データのカラム数: {len(X.columns)}個")
    
    # 選択された特徴量がデータに存在するか確認
    missing_features = [f for f in selected_features if f not in X.columns]
    if missing_features:
        print(f"⚠️ 警告: 以下の特徴量がデータに存在しません:")
        for i, feat in enumerate(missing_features[:10], 1):
            print(f"     {i}. {feat}")
        if len(missing_features) > 10:
            print(f"     ... 他 {len(missing_features) - 10}個")
        
        # 存在する特徴量のみを使用
        available_features = [f for f in selected_features if f in X.columns]
        print(f"  - 使用可能な特徴量: {len(available_features)}/{len(selected_features)}個")
        
        if len(available_features) == 0:
            raise ValueError("❌ 使用可能な特徴量が1つもありません")
        
        selected_features = available_features
    
    # 選択された特徴量のみを使用
    X_selected = X[selected_features].copy()
    
    # 欠損値を0で埋める
    X_selected = X_selected.fillna(0)
    
    # object型を数値に変換
    for col in X_selected.select_dtypes(include=['object']).columns:
        X_selected[col] = pd.to_numeric(X_selected[col], errors='coerce').fillna(0)
    
    print(f"✅ 予測実行中...")
    print(f"  - 使用特徴量: {len(selected_features)}個")
    print(f"  - サンプル数: {len(X_selected)}件")
    
    # 予測
    y_pred = model.predict(X_selected)
    
    return y_pred


def calculate_betting_recommendations(df, predictions, bankroll=100000, kelly_fraction=0.25):
    """
    期待値ベースの購入推奨を計算
    
    Args:
        df: レースデータ（馬番、オッズ情報を含む）
        predictions: 予測確率
        bankroll: 総資金（円）
        kelly_fraction: Kelly比率
    
    Returns:
        pd.DataFrame: 購入推奨リスト
    """
    if BettingStrategyEngine is None:
        print("⚠️ ベッティング戦略エンジンが利用できません")
        return pd.DataFrame()
    
    # ベッティング戦略エンジンを初期化
    engine = BettingStrategyEngine(
        bankroll=bankroll,
        kelly_fraction=kelly_fraction,
        max_bet_pct=0.05,
        min_ev=0.05
    )
    
    # オッズ情報を抽出（仮のダミーオッズ、実際は外部APIから取得）
    # 注: 実際の運用では、オッズAPIから最新オッズを取得する必要があります
    df['predicted_prob'] = predictions
    df['dummy_odds'] = 1.0 / df['predicted_prob']  # ダミーオッズ
    
    # 期待値を計算
    df['ev'] = engine.calculate_expected_value(df['predicted_prob'], df['dummy_odds'])
    
    # 期待値が正の馬のみを推奨
    recommendations = df[df['ev'] > engine.min_ev].copy()
    
    if len(recommendations) == 0:
        print("⚠️ 期待値が正の馬が見つかりませんでした")
        return pd.DataFrame()
    
    # Kelly基準で賭け金を計算
    recommendations['kelly_bet'] = recommendations.apply(
        lambda row: engine.calculate_kelly_bet(row['predicted_prob'], row['dummy_odds'], row['ev']),
        axis=1
    )
    
    # 最大賭け率でクリップ
    max_bet = bankroll * engine.max_bet_pct
    recommendations['recommended_bet'] = recommendations['kelly_bet'].clip(upper=max_bet)
    
    print(f"✅ 購入推奨計算完了")
    print(f"  - 推奨馬数: {len(recommendations)}頭")
    print(f"  - 総推奨金額: {recommendations['recommended_bet'].sum():,.0f}円")
    
    return recommendations[['umaban', 'predicted_prob', 'dummy_odds', 'ev', 'recommended_bet']]


def save_results(df, predictions, recommendations, venue_name, target_date):
    """
    予測結果を保存
    
    Args:
        df: レースデータ
        predictions: 予測確率
        recommendations: 購入推奨
        venue_name: 競馬場名（英語）
        target_date: 対象日
    """
    output_dir = project_root / 'data' / 'predictions' / 'phase10'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_short = target_date.replace('-', '')
    
    # 予測結果CSV
    df_output = df.copy()
    df_output['predicted_prob'] = predictions
    predictions_path = output_dir / f'{venue_name}_{date_short}_predictions.csv'
    df_output.to_csv(predictions_path, index=False, encoding='utf-8-sig')
    print(f"✅ 予測結果保存: {predictions_path}")
    
    # 購入推奨CSV
    if len(recommendations) > 0:
        recommendations_path = output_dir / f'{venue_name}_{date_short}_recommended_bets.csv'
        recommendations.to_csv(recommendations_path, index=False, encoding='utf-8-sig')
        print(f"✅ 購入推奨保存: {recommendations_path}")
    
    # サマリーTXT
    summary_path = output_dir / f'{venue_name}_{date_short}_summary.txt'
    venue_ja = VENUE_NAME_TO_JA.get(venue_name, venue_name)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"{'='*60}\n")
        f.write(f"Phase 10: 日次予測サマリー\n")
        f.write(f"{'='*60}\n")
        f.write(f"競馬場: {venue_ja} ({venue_name})\n")
        f.write(f"対象日: {target_date}\n")
        f.write(f"予測時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n")
        f.write(f"【予測統計】\n")
        f.write(f"  - 総レース数: {len(df)}件\n")
        f.write(f"  - 平均予測確率: {predictions.mean():.4f}\n")
        f.write(f"  - 最大予測確率: {predictions.max():.4f}\n")
        f.write(f"  - 最小予測確率: {predictions.min():.4f}\n")
        f.write(f"\n")
        
        if len(recommendations) > 0:
            f.write(f"【購入推奨】\n")
            f.write(f"  - 推奨馬数: {len(recommendations)}頭\n")
            f.write(f"  - 総推奨金額: {recommendations['recommended_bet'].sum():,.0f}円\n")
            f.write(f"  - 平均期待値: {recommendations['ev'].mean():.4f}\n")
            f.write(f"\n")
            f.write(f"【トップ5推奨馬】\n")
            top5 = recommendations.nlargest(5, 'ev')
            for idx, row in top5.iterrows():
                f.write(f"  馬番{int(row['umaban']):2d}: ")
                f.write(f"確率{row['predicted_prob']:.3f} ")
                f.write(f"EV{row['ev']:+.3f} ")
                f.write(f"推奨{row['recommended_bet']:,.0f}円\n")
        else:
            f.write(f"【購入推奨】\n")
            f.write(f"  ⚠️ 期待値が正の馬が見つかりませんでした\n")
        
        f.write(f"\n")
        f.write(f"{'='*60}\n")
        f.write(f"Phase 10完了\n")
        f.write(f"{'='*60}\n")
    
    print(f"✅ サマリー保存: {summary_path}")


def main():
    parser = argparse.ArgumentParser(description='Phase 10: 日次予測システム')
    parser.add_argument('--venue', type=str, help='競馬場名（英語、例: monbetsu）またはコード（例: 30）')
    parser.add_argument('--venue-code', type=str, help='競馬場コード（例: 44）')
    parser.add_argument('--date', type=str, required=True, help='対象日（例: 2026-02-11）')
    parser.add_argument('--bankroll', type=int, default=100000, help='総資金（円）')
    parser.add_argument('--kelly-fraction', type=float, default=0.25, help='Kelly比率')
    
    args = parser.parse_args()
    
    # 競馬場名を正規化
    if args.venue_code:
        venue_name = VENUE_CODE_TO_NAME.get(args.venue_code)
        if venue_name is None:
            print(f"❌ 無効な競馬場コード: {args.venue_code}")
            sys.exit(1)
        venue_code = args.venue_code
    elif args.venue:
        if args.venue in VENUE_CODE_TO_NAME:
            venue_code = args.venue
            venue_name = VENUE_CODE_TO_NAME[venue_code]
        elif args.venue in VENUE_CODE_TO_NAME.values():
            venue_name = args.venue
            venue_code = [k for k, v in VENUE_CODE_TO_NAME.items() if v == venue_name][0]
        else:
            print(f"❌ 無効な競馬場: {args.venue}")
            sys.exit(1)
    else:
        print("❌ --venue または --venue-code を指定してください")
        sys.exit(1)
    
    venue_ja = VENUE_NAME_TO_JA.get(venue_name, venue_name)
    
    print(f"\n{'='*60}")
    print(f"Phase 10: 日次予測システム")
    print(f"{'='*60}")
    print(f"競馬場: {venue_ja} ({venue_name})")
    print(f"対象日: {args.date}")
    print(f"総資金: {args.bankroll:,}円")
    print(f"Kelly比率: {args.kelly_fraction}")
    print(f"{'='*60}\n")
    
    try:
        # [1/6] Phase 8モデル読み込み
        print(f"[1/6] Phase 8モデル読み込み中...")
        model = load_tuned_model(venue_name)
        print()
        
        # [2/6] Phase 7特徴量読み込み
        print(f"[2/6] Phase 7特徴量読み込み中...")
        selected_features = load_selected_features(venue_name)
        print()
        
        # [3/6] レースデータ読み込み
        print(f"[3/6] レースデータ読み込み中...")
        df = load_race_data(venue_code, args.date)
        print()
        
        # [4/6] 予測実行
        print(f"[4/6] 予測実行中...")
        predictions = predict(model, df, selected_features)
        print(f"  - 予測完了: 平均確率 {predictions.mean():.4f}")
        print()
        
        # [5/6] 購入推奨計算
        print(f"[5/6] 購入推奨計算中...")
        recommendations = calculate_betting_recommendations(
            df, predictions, args.bankroll, args.kelly_fraction
        )
        print()
        
        # [6/6] 結果保存
        print(f"[6/6] 結果保存中...")
        save_results(df, predictions, recommendations, venue_name, args.date)
        print()
        
        print(f"{'='*60}")
        print(f"✅ Phase 10完了！")
        print(f"{'='*60}")
        print(f"次のステップ: Phase 6配信用テキスト生成")
        print(f"コマンド: scripts\\phase6_betting\\DAILY_OPERATION.bat {venue_code} {args.date}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
