#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5: アンサンブル統合スクリプト（距離カテゴリ対応）

Binary/Ranking/Regression 予測結果を統合して最終順位を決定
距離カテゴリ（SHORT/MILE/LONG）ごとに適切なモデル結果を使用
"""

import sys
import os
import pandas as pd
import numpy as np
import argparse
import warnings
warnings.filterwarnings('ignore')

def get_distance_category(kyori):
    """
    距離からカテゴリを判定
    
    Parameters
    ----------
    kyori : int
        レース距離（メートル）
    
    Returns
    -------
    str
        'SHORT', 'MILE', 'LONG'
    """
    if kyori <= 1200:
        return 'SHORT'
    elif kyori <= 1700:
        return 'MILE'
    else:
        return 'LONG'

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
    
    if max_val == min_val or pd.isna(min_val) or pd.isna(max_val):
        # 全て同じ値またはNANの場合は0.5を返す
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

def ensemble_predictions_distance_category(
    binary_csv, ranking_csv, regression_csv, output_path,
    weight_binary=0.3, weight_ranking=0.5, weight_regression=0.2
):
    """
    Phase 5: Binary/Ranking/Regression の予測結果をアンサンブル統合
    
    Parameters
    ----------
    binary_csv : str
        二値分類予測結果（距離カテゴリ対応）
    ranking_csv : str
        ランキング予測結果（距離カテゴリ対応）
    regression_csv : str
        回帰予測結果（距離カテゴリ対応）
    output_path : str
        統合結果の出力先
    weight_binary : float
        二値分類の重み（デフォルト: 0.3）
    weight_ranking : float
        ランキングの重み（デフォルト: 0.5）
    weight_regression : float
        回帰予測の重み（デフォルト: 0.2）
    
    Returns
    -------
    pd.DataFrame
        統合結果
    """
    print(f"\n{'='*80}")
    print(f"Phase 5: アンサンブル統合（距離カテゴリ対応）")
    print(f"{'='*80}")
    
    # 重みの検証
    total_weight = weight_binary + weight_ranking + weight_regression
    if not np.isclose(total_weight, 1.0):
        print(f"⚠️  警告: 重みの合計が1.0ではありません ({total_weight:.2f})")
        print(f"  - 自動正規化します")
        weight_binary /= total_weight
        weight_ranking /= total_weight
        weight_regression /= total_weight
    
    print(f"\n重み設定:")
    print(f"  - 二値分類 (Binary)    : {weight_binary:.1%}")
    print(f"  - ランキング (Ranking)  : {weight_ranking:.1%}")
    print(f"  - 回帰予測 (Regression) : {weight_regression:.1%}")
    
    # データ読み込み
    print(f"\n[1/6] データ読み込み")
    
    # Binary
    try:
        df_binary = pd.read_csv(binary_csv, encoding='shift-jis')
        print(f"  ✅ Binary: {len(df_binary)}件")
    except:
        df_binary = pd.read_csv(binary_csv, encoding='utf-8')
        print(f"  ✅ Binary: {len(df_binary)}件 (UTF-8)")
    
    # Ranking
    try:
        df_ranking = pd.read_csv(ranking_csv, encoding='shift-jis')
        print(f"  ✅ Ranking: {len(df_ranking)}件")
    except:
        df_ranking = pd.read_csv(ranking_csv, encoding='utf-8')
        print(f"  ✅ Ranking: {len(df_ranking)}件 (UTF-8)")
    
    # Regression
    try:
        df_regression = pd.read_csv(regression_csv, encoding='shift-jis')
        print(f"  ✅ Regression: {len(df_regression)}件")
    except:
        df_regression = pd.read_csv(regression_csv, encoding='utf-8')
        print(f"  ✅ Regression: {len(df_regression)}件 (UTF-8)")
    
    # 距離カテゴリの追加（race_idから判定）
    print(f"\n[2/6] 距離カテゴリ判定")
    
    # 距離情報がない場合は警告
    if 'kyori' not in df_binary.columns:
        print(f"  ⚠️  警告: 'kyori'列が見つかりません。distance_categoryを使用します。")
    else:
        df_binary['distance_category'] = df_binary['kyori'].apply(get_distance_category)
        df_ranking['distance_category'] = df_ranking['kyori'].apply(get_distance_category)
        df_regression['distance_category'] = df_regression['kyori'].apply(get_distance_category)
    
    # データ結合
    print(f"\n[3/6] データ結合 (race_id + umaban)")
    
    # race_id と umaban でマージ
    merge_keys = ['race_id', 'umaban']
    
    df = df_binary.merge(
        df_ranking[[col for col in ['race_id', 'umaban', 'ranking_score', 'predicted_rank', 'distance_category'] if col in df_ranking.columns]],
        on=merge_keys,
        how='inner',
        suffixes=('', '_ranking')
    )
    
    df = df.merge(
        df_regression[[col for col in ['race_id', 'umaban', 'predicted_time', 'time_rank', 'distance_category'] if col in df_regression.columns]],
        on=merge_keys,
        how='inner',
        suffixes=('', '_regression')
    )
    
    print(f"  ✅ 結合後データ件数: {len(df)}件")
    print(f"  ✅ レース数: {df['race_id'].nunique()}件")
    
    if 'distance_category' in df.columns:
        print(f"\n  距離カテゴリ別内訳:")
        for cat in ['SHORT', 'MILE', 'LONG']:
            count = len(df[df['distance_category'] == cat])
            if count > 0:
                print(f"    - {cat}: {count}件")
    
    # スコア正規化
    print(f"\n[4/6] スコア正規化 (0〜1)")
    
    # レースごとに正規化
    df['binary_normalized'] = df.groupby('race_id')['binary_probability'].transform(
        lambda x: normalize_score(x, ascending=False)
    )
    
    df['ranking_normalized'] = df.groupby('race_id')['ranking_score'].transform(
        lambda x: normalize_score(x, ascending=False)
    )
    
    df['regression_normalized'] = df.groupby('race_id')['predicted_time'].transform(
        lambda x: normalize_score(x, ascending=True)  # 時間は小さいほど良い
    )
    
    print(f"  ✅ Binary正規化: 平均={df['binary_normalized'].mean():.4f}")
    print(f"  ✅ Ranking正規化: 平均={df['ranking_normalized'].mean():.4f}")
    print(f"  ✅ Regression正規化: 平均={df['regression_normalized'].mean():.4f}")
    
    # アンサンブルスコア計算
    print(f"\n[5/6] アンサンブルスコア計算")
    
    df['ensemble_score'] = (
        weight_binary * df['binary_normalized'] +
        weight_ranking * df['ranking_normalized'] +
        weight_regression * df['regression_normalized']
    )
    
    print(f"  ✅ アンサンブルスコア平均: {df['ensemble_score'].mean():.4f}")
    print(f"  ✅ アンサンブルスコア最大: {df['ensemble_score'].max():.4f}")
    print(f"  ✅ アンサンブルスコア最小: {df['ensemble_score'].min():.4f}")
    
    # 最終順位決定
    print(f"\n[6/6] 最終順位決定")
    
    # レース内でアンサンブルスコアを正規化（0〜1）
    df['ensemble_score_normalized'] = df.groupby('race_id')['ensemble_score'].transform(
        lambda x: normalize_score(x, ascending=False)
    )
    
    # レース内での最終順位
    df['final_rank'] = df.groupby('race_id')['ensemble_score'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    # 出力用のカラム選択
    base_output_cols = [
        'race_id', 'umaban', 
        'binary_probability', 'ranking_score', 'predicted_time',
        'ensemble_score', 'ensemble_score_normalized', 'final_rank'
    ]
    
    # 追加のID列があれば含める
    additional_cols = [
        'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
        'ketto_toroku_bango', 'kyori', 'distance_category'
    ]
    
    output_cols = base_output_cols.copy()
    for col in additional_cols:
        if col in df.columns and col not in output_cols:
            # race_idの後に挿入
            insert_pos = output_cols.index('race_id') + 1
            output_cols.insert(insert_pos, col)
    
    # 存在するカラムのみ選択
    output_cols = [col for col in output_cols if col in df.columns]
    result_df = df[output_cols].copy()
    
    # レースごとの1位予測を表示
    print(f"\n  【レース別1位予測サマリー】")
    top_predictions = result_df[result_df['final_rank'] == 1].sort_values('race_id')
    
    for idx, (_, row) in enumerate(top_predictions.head(5).iterrows(), 1):
        race_id = row['race_id']
        umaban = int(row['umaban'])
        score = row['ensemble_score_normalized']
        
        detail = f"    {idx}. レース{race_id}: {umaban}番"
        if 'distance_category' in row:
            detail += f" ({row['distance_category']})"
        detail += f" - スコア: {score:.4f}"
        
        print(detail)
    
    if len(top_predictions) > 5:
        print(f"    ... 他 {len(top_predictions) - 5}レース")
    
    # 距離カテゴリ別の統計
    if 'distance_category' in result_df.columns:
        print(f"\n  【距離カテゴリ別統計】")
        for cat in ['SHORT', 'MILE', 'LONG']:
            cat_data = result_df[result_df['distance_category'] == cat]
            if len(cat_data) > 0:
                avg_score = cat_data['ensemble_score'].mean()
                print(f"    - {cat}: {len(cat_data)}件, 平均スコア: {avg_score:.4f}")
    
    # 結果を保存
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        result_df.to_csv(output_path, index=False, encoding='shift-jis')
        print(f"\n✅ 統合結果を保存（Shift-JIS）: {output_path}")
    except:
        output_path_utf8 = output_path.replace('.csv', '_utf8.csv')
        result_df.to_csv(output_path_utf8, index=False, encoding='utf-8')
        print(f"\n✅ 統合結果を保存（UTF-8）: {output_path_utf8}")
        output_path = output_path_utf8
    
    print(f"  - レコード数: {len(result_df):,}件")
    print(f"  - カラム数: {len(result_df.columns)}個")
    print(f"  - レース数: {result_df['race_id'].nunique()}件")
    
    return result_df

def main():
    parser = argparse.ArgumentParser(
        description='Phase 5: アンサンブル統合（距離カテゴリ対応）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python ensemble_distance_category.py \\
    --binary data/predictions/binary/urawa_20250207_binary.csv \\
    --ranking data/predictions/ranking/urawa_20250207_ranking.csv \\
    --regression data/predictions/regression/urawa_20250207_regression.csv \\
    --output data/predictions/ensemble/urawa_20250207_ensemble.csv

重みのカスタマイズ:
  python ensemble_distance_category.py ... \\
    --weight-binary 0.3 --weight-ranking 0.5 --weight-regression 0.2
        """
    )
    
    parser.add_argument('--binary', required=True, help='二値分類予測結果CSV')
    parser.add_argument('--ranking', required=True, help='ランキング予測結果CSV')
    parser.add_argument('--regression', required=True, help='回帰予測結果CSV')
    parser.add_argument('--output', required=True, help='統合結果の出力先CSV')
    parser.add_argument('--weight-binary', type=float, default=0.3, 
                       help='二値分類の重み（デフォルト: 0.3）')
    parser.add_argument('--weight-ranking', type=float, default=0.5,
                       help='ランキングの重み（デフォルト: 0.5）')
    parser.add_argument('--weight-regression', type=float, default=0.2,
                       help='回帰予測の重み（デフォルト: 0.2）')
    
    args = parser.parse_args()
    
    try:
        result_df = ensemble_predictions_distance_category(
            args.binary, args.ranking, args.regression, args.output,
            args.weight_binary, args.weight_ranking, args.weight_regression
        )
        
        print("\n" + "="*80)
        print("✅ Phase 5 アンサンブル統合完了")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
