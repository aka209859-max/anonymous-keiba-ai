#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5 アンサンブル統合スクリプト

Phase 3 (二値分類), Phase 4-1 (ランキング), Phase 4-2 (回帰) の
予測結果を統合して最終順位を決定
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

def ensemble_predictions(binary_csv, ranking_csv, regression_csv, output_path,
                        weight_binary=0.3, weight_ranking=0.5, weight_regression=0.2):
    """
    Phase 3〜4 の予測結果をアンサンブル統合
    
    Parameters
    ----------
    binary_csv : str
        Phase 3 二値分類予測結果
    ranking_csv : str
        Phase 4-1 ランキング予測結果
    regression_csv : str
        Phase 4-2 回帰予測結果
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
    print(f"Phase 5 アンサンブル統合")
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
    
    # Phase 3: Binary
    try:
        df_binary = pd.read_csv(binary_csv, encoding='shift-jis')
        print(f"  ✅ Phase 3 (Binary): {len(df_binary)}件")
    except:
        df_binary = pd.read_csv(binary_csv, encoding='utf-8')
        print(f"  ✅ Phase 3 (Binary): {len(df_binary)}件 (UTF-8)")
    
    # Phase 4-1: Ranking
    try:
        df_ranking = pd.read_csv(ranking_csv, encoding='shift-jis')
        print(f"  ✅ Phase 4-1 (Ranking): {len(df_ranking)}件")
    except:
        df_ranking = pd.read_csv(ranking_csv, encoding='utf-8')
        print(f"  ✅ Phase 4-1 (Ranking): {len(df_ranking)}件 (UTF-8)")
    
    # Phase 4-2: Regression
    try:
        df_regression = pd.read_csv(regression_csv, encoding='shift-jis')
        print(f"  ✅ Phase 4-2 (Regression): {len(df_regression)}件")
    except:
        df_regression = pd.read_csv(regression_csv, encoding='utf-8')
        print(f"  ✅ Phase 4-2 (Regression): {len(df_regression)}件 (UTF-8)")
    
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
        lambda x: normalize_score(x, ascending=True)
    )
    
    print(f"  ✅ Binary正規化完了")
    print(f"  ✅ Ranking正規化完了")
    print(f"  ✅ Regression正規化完了")
    
    # アンサンブルスコア計算
    print(f"\n[4/5] アンサンブルスコア計算")
    
    df['ensemble_score'] = (
        df['binary_normalized'] * weight_binary +
        df['ranking_normalized'] * weight_ranking +
        df['regression_normalized'] * weight_regression
    )
    
    print(f"  ✅ アンサンブルスコア計算完了")
    print(f"  - 平均スコア: {df['ensemble_score'].mean():.4f}")
    print(f"  - 最大スコア: {df['ensemble_score'].max():.4f}")
    print(f"  - 最小スコア: {df['ensemble_score'].min():.4f}")
    
    # 最終順位決定
    print(f"\n[5/5] 最終順位決定")
    
    df['final_rank'] = df.groupby('race_id')['ensemble_score'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    print(f"  ✅ 最終順位計算完了")
    
    # レース別サマリー
    print(f"\n  【レース別予測サマリー（最初の5レース）】")
    for race_id in sorted(df['race_id'].unique())[:5]:
        race_data = df[df['race_id'] == race_id].sort_values('final_rank')
        top3 = race_data.head(3)
        race_num = int(str(race_id)[-2:])
        
        print(f"\n  第{race_num}R:")
        for idx, row in top3.iterrows():
            print(f"    {int(row['final_rank'])}位: {int(row['umaban'])}番 "
                  f"(スコア: {row['ensemble_score']:.4f}, "
                  f"Binary: {row['binary_probability']:.3f}, "
                  f"Ranking: {int(row['predicted_rank'])}, "
                  f"Time: {row['predicted_time']:.2f}秒)")
    
    if df['race_id'].nunique() > 5:
        print(f"\n  ... 他 {df['race_id'].nunique() - 5}レース")
    
    # 結果保存
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 出力カラムの選択
    output_cols = [
        'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
        'ketto_toroku_bango', 'umaban',
        'ensemble_score', 'final_rank',
        'binary_probability', 'predicted_class',
        'ranking_score', 'predicted_rank',
        'predicted_time', 'time_rank'
    ]
    
    # 存在するカラムのみ選択
    output_cols = [col for col in output_cols if col in df.columns]
    df_output = df[output_cols].copy()
    
    # 保存
    try:
        df_output.to_csv(output_path, index=False, encoding='shift-jis')
        print(f"\n✅ アンサンブル結果を保存（Shift-JIS）: {output_path}")
    except:
        output_path_utf8 = output_path.replace('.csv', '_utf8.csv')
        df_output.to_csv(output_path_utf8, index=False, encoding='utf-8')
        print(f"\n✅ アンサンブル結果を保存（UTF-8）: {output_path_utf8}")
        output_path = output_path_utf8
    
    print(f"  - レコード数: {len(df_output):,}件")
    print(f"  - カラム数: {len(df_output.columns)}個")
    
    return df_output

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("使用法: python ensemble_predictions.py <binary_csv> <ranking_csv> <regression_csv> <output_csv> [<weight_binary> <weight_ranking> <weight_regression>]")
        print("\n例:")
        print("  python ensemble_predictions.py \\")
        print("         data/predictions/phase3/川崎_20260205_phase3_binary.csv \\")
        print("         data/predictions/phase4_ranking/川崎_20260205_phase4_ranking.csv \\")
        print("         data/predictions/phase4_regression/川崎_20260205_phase4_regression.csv \\")
        print("         data/predictions/phase5/川崎_20260205_ensemble.csv")
        print("\nオプション: 重みの指定（デフォルト: 0.3 0.5 0.2）")
        print("  python ensemble_predictions.py ... 0.3 0.5 0.2")
        sys.exit(1)
    
    binary_csv = sys.argv[1]
    ranking_csv = sys.argv[2]
    regression_csv = sys.argv[3]
    output_path = sys.argv[4]
    
    # 重みの指定（オプション）
    weight_binary = float(sys.argv[5]) if len(sys.argv) > 5 else 0.3
    weight_ranking = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
    weight_regression = float(sys.argv[7]) if len(sys.argv) > 7 else 0.2
    
    try:
        df_result = ensemble_predictions(
            binary_csv, ranking_csv, regression_csv, output_path,
            weight_binary, weight_ranking, weight_regression
        )
        print("\n" + "="*80)
        print("✅ Phase 5 アンサンブル統合完了")
        print("="*80)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)