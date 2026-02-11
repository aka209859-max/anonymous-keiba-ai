#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5 アンサンブル統合スクリプト（新モデル用・Phase 7-8-5）

Phase 7-8 (Binary/Ranking/Regression) の予測結果を統合して最終順位を決定
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

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

def ensemble_optimized_predictions(binary_csv, ranking_csv, regression_csv, output_path,
                                  weight_binary=0.3, weight_ranking=0.5, weight_regression=0.2):
    """
    Phase 7-8 の予測結果をアンサンブル統合
    
    Parameters
    ----------
    binary_csv : str
        Phase 7-8 二値分類予測結果
    ranking_csv : str
        Phase 8 ランキング予測結果
    regression_csv : str
        Phase 8 回帰予測結果
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
    print(f"Phase 5 アンサンブル統合（新モデル: Phase 7-8-5）")
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
    print(f"\n[1/5] データ読み込み")
    
    # Phase 7-8: Binary
    try:
        df_binary = pd.read_csv(binary_csv, encoding='shift-jis')
        print(f"  ✅ Phase 7-8 (Binary): {len(df_binary)}件")
    except:
        df_binary = pd.read_csv(binary_csv, encoding='utf-8')
        print(f"  ✅ Phase 7-8 (Binary): {len(df_binary)}件 (UTF-8)")
    
    # Phase 8: Ranking
    try:
        df_ranking = pd.read_csv(ranking_csv, encoding='shift-jis')
        print(f"  ✅ Phase 8 (Ranking): {len(df_ranking)}件")
    except:
        df_ranking = pd.read_csv(ranking_csv, encoding='utf-8')
        print(f"  ✅ Phase 8 (Ranking): {len(df_ranking)}件 (UTF-8)")
    
    # Phase 8: Regression
    try:
        df_regression = pd.read_csv(regression_csv, encoding='shift-jis')
        print(f"  ✅ Phase 8 (Regression): {len(df_regression)}件")
    except:
        df_regression = pd.read_csv(regression_csv, encoding='utf-8')
        print(f"  ✅ Phase 8 (Regression): {len(df_regression)}件 (UTF-8)")
    
    # データ結合
    print(f"\n[2/5] データ結合 (race_id + umaban)")
    
    # race_id と umaban でマージ
    df = df_binary.merge(
        df_ranking[['race_id', 'umaban', 'ranking_score', 'predicted_rank']],
        on=['race_id', 'umaban'],
        how='inner',
        suffixes=('', '_ranking')
    )
    
    df = df.merge(
        df_regression[['race_id', 'umaban', 'predicted_time', 'time_rank']],
        on=['race_id', 'umaban'],
        how='inner',
        suffixes=('', '_regression')
    )
    
    print(f"  ✅ 結合後データ件数: {len(df)}件")
    print(f"  ✅ レース数: {df['race_id'].nunique()}件")
    
    # スコア正規化
    print(f"\n[3/5] スコア正規化 (0〜1)")
    
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
    print(f"\n[4/5] アンサンブルスコア計算")
    
    df['ensemble_score'] = (
        weight_binary * df['binary_normalized'] +
        weight_ranking * df['ranking_normalized'] +
        weight_regression * df['regression_normalized']
    )
    
    print(f"  ✅ アンサンブルスコア平均: {df['ensemble_score'].mean():.4f}")
    print(f"  ✅ アンサンブルスコア最大: {df['ensemble_score'].max():.4f}")
    print(f"  ✅ アンサンブルスコア最小: {df['ensemble_score'].min():.4f}")
    
    # 最終順位決定
    print(f"\n[5/5] 最終順位決定")
    
    # レース内でアンサンブルスコアを正規化（0〜1）
    df['ensemble_score_normalized'] = df.groupby('race_id')['ensemble_score'].transform(
        lambda x: normalize_score(x, ascending=False)
    )
    
    # レース内での最終順位
    df['final_rank'] = df.groupby('race_id')['ensemble_score'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    # 出力用のカラム選択
    output_cols = [
        'race_id', 'umaban', 
        'binary_probability', 'ranking_score', 'predicted_time',
        'ensemble_score', 'ensemble_score_normalized', 'final_rank'
    ]
    
    # 追加のID列があれば含める
    for col in ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 
                'ketto_toroku_bango']:
        if col in df.columns and col not in output_cols:
            output_cols.insert(output_cols.index('race_id') + 1, col)
    
    result_df = df[output_cols].copy()
    
    # レースごとの1位予測を表示
    print(f"\n  レース別1位予測:")
    top_predictions = result_df[result_df['final_rank'] == 1].sort_values('race_id')
    for _, row in top_predictions.head(10).iterrows():
        print(f"    - {row['race_id']}: {row['umaban']}番 "
              f"(スコア: {row['ensemble_score_normalized']:.4f})")
    
    if len(top_predictions) > 10:
        print(f"    ... 他 {len(top_predictions) - 10}レース")
    
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
    
    return result_df

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("使用法: python ensemble_optimized.py <binary_csv> <ranking_csv> <regression_csv> <output_csv> [weights]")
        print("\n例:")
        print("  python ensemble_optimized.py \\")
        print("    data\\predictions\\phase7_binary\\佐賀_20260207_phase7_binary.csv \\")
        print("    data\\predictions\\phase8_ranking\\佐賀_20260207_phase8_ranking.csv \\")
        print("    data\\predictions\\phase8_regression\\佐賀_20260207_phase8_regression.csv \\")
        print("    data\\predictions\\phase5\\佐賀_20260207_ensemble_optimized.csv")
        print("\n重み指定（オプション）:")
        print("  python ensemble_optimized.py ... --weights 0.3 0.5 0.2")
        print("    (デフォルト: Binary=0.3, Ranking=0.5, Regression=0.2)")
        sys.exit(1)
    
    binary_csv = sys.argv[1]
    ranking_csv = sys.argv[2]
    regression_csv = sys.argv[3]
    output_path = sys.argv[4]
    
    # オプション: 重み指定
    weight_binary = 0.3
    weight_ranking = 0.5
    weight_regression = 0.2
    
    if len(sys.argv) >= 8 and sys.argv[5] == '--weights':
        try:
            weight_binary = float(sys.argv[6])
            weight_ranking = float(sys.argv[7])
            weight_regression = float(sys.argv[8])
            print(f"\n✅ カスタム重み設定: Binary={weight_binary}, Ranking={weight_ranking}, Regression={weight_regression}")
        except:
            print(f"⚠️  警告: 重みの解析に失敗しました。デフォルト値を使用します。")
    
    try:
        result_df = ensemble_optimized_predictions(
            binary_csv, ranking_csv, regression_csv, output_path,
            weight_binary, weight_ranking, weight_regression
        )
        print("\n" + "="*80)
        print("✅ Phase 5 アンサンブル統合完了（新モデル: Phase 7-8-5）")
        print("="*80)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
