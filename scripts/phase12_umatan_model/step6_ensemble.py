#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: Step 6 - アンサンブル予測（バイナリ + ランキング + 回帰）
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def ensemble_predictions(binary_csv, ranking_csv, regression_csv, output_csv, 
                        weight_binary=0.3, weight_ranking=0.5, weight_regression=0.2):
    """Phase 12 アンサンブル予測"""
    print(f"\n{'='*80}")
    print(f"Phase 12: Step 6 - アンサンブル予測")
    print(f"{'='*80}")
    
    # データ読み込み
    print(f"\n[1/4] 予測結果読み込み")
    print(f"  - バイナリ分類: {binary_csv}")
    try:
        df_binary = pd.read_csv(binary_csv, encoding='shift-jis')
    except:
        df_binary = pd.read_csv(binary_csv, encoding='utf-8')
    print(f"    データ件数: {len(df_binary):,}")
    
    print(f"  - ランキング: {ranking_csv}")
    try:
        df_ranking = pd.read_csv(ranking_csv, encoding='shift-jis')
    except:
        df_ranking = pd.read_csv(ranking_csv, encoding='utf-8')
    print(f"    データ件数: {len(df_ranking):,}")
    
    print(f"  - 回帰: {regression_csv}")
    try:
        df_regression = pd.read_csv(regression_csv, encoding='shift-jis')
    except:
        df_regression = pd.read_csv(regression_csv, encoding='utf-8')
    print(f"    データ件数: {len(df_regression):,}")
    
    # データ結合
    print(f"\n[2/4] データ結合")
    
    # 識別列を使って結合（馬名も保持）
    id_cols = ['race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
               'race_bango', 'ketto_toroku_bango', 'umaban']
    merge_cols = [col for col in id_cols if col in df_binary.columns]
    
    # 馬名列を探す
    bamei_col = None
    for col in df_binary.columns:
        if '馬名' in col or 'bamei' in col.lower() or col == 'name':
            bamei_col = col
            break
    
    # 結合する列リスト
    binary_cols = merge_cols + ['binary_proba', 'binary_pred']
    if bamei_col and bamei_col in df_binary.columns:
        binary_cols.append(bamei_col)
    
    df = df_binary[binary_cols].copy()
    df = df.merge(df_ranking[merge_cols + ['ranking_score', 'ranking_rank']], 
                  on=merge_cols, how='inner')
    df = df.merge(df_regression[merge_cols + ['predicted_time', 'time_rank']], 
                  on=merge_cols, how='inner')
    
    print(f"  ✅ 結合完了: {len(df):,}行")
    
    # アンサンブルスコア計算
    print(f"\n[3/4] アンサンブルスコア計算")
    print(f"  - バイナリ重み: {weight_binary}")
    print(f"  - ランキング重み: {weight_ranking}")
    print(f"  - 回帰重み: {weight_regression}")
    
    # 各スコアを0-1に正規化
    df['binary_norm'] = df['binary_proba']  # 既に0-1
    
    # ランキングスコアを0-1に正規化（レースごと）
    df['ranking_norm'] = df.groupby('race_id')['ranking_score'].transform(
        lambda x: (x - x.min()) / (x.max() - x.min() + 1e-10)
    )
    
    # タイムスコアを0-1に正規化（レースごと、タイムが小さいほど高スコア）
    df['time_norm'] = df.groupby('race_id')['predicted_time'].transform(
        lambda x: 1 - (x - x.min()) / (x.max() - x.min() + 1e-10)
    )
    
    # アンサンブルスコア
    df['ensemble_score'] = (
        weight_binary * df['binary_norm'] +
        weight_ranking * df['ranking_norm'] +
        weight_regression * df['time_norm']
    )
    
    # レースごとの順位
    df['ensemble_rank'] = df.groupby('race_id')['ensemble_score'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    # 統計情報
    print(f"\n[4/4] アンサンブル結果")
    print(f"  - アンサンブルスコアの平均: {df['ensemble_score'].mean():.4f}")
    print(f"  - アンサンブルスコアの最大: {df['ensemble_score'].max():.4f}")
    print(f"  - アンサンブルスコアの最小: {df['ensemble_score'].min():.4f}")
    print(f"  - レース数: {df['race_id'].nunique()}件")
    
    # レースごとのTop3表示（最初の3レースのみ）
    print(f"\n  📊 レースごとのTop3サンプル（最初の3レース）:")
    for idx, (race_id, group) in enumerate(df.groupby('race_id')):
        if idx >= 3:
            break
        top3 = group.nsmallest(3, 'ensemble_rank')[['umaban', 'ensemble_score', 'ensemble_rank']]
        print(f"\n  レース {race_id}:")
        for _, row in top3.iterrows():
            print(f"    {int(row['ensemble_rank'])}位: {int(row['umaban'])}番 (スコア: {row['ensemble_score']:.4f})")
    
    # 保存
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        df.to_csv(output_csv, index=False, encoding='shift-jis')
        print(f"\n✅ アンサンブル結果を保存（Shift-JIS）: {output_csv}")
    except:
        output_csv_utf8 = output_csv.replace('.csv', '_utf8.csv')
        df.to_csv(output_csv_utf8, index=False, encoding='utf-8')
        print(f"\n✅ アンサンブル結果を保存（UTF-8）: {output_csv_utf8}")
    
    print(f"\n{'='*80}")
    print("✅ Phase 12 Step 6 完了")
    print(f"{'='*80}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("使用法: python step6_ensemble.py <binary_csv> <ranking_csv> <regression_csv> <output_csv> [weight_binary] [weight_ranking] [weight_regression]")
        print("\n例: python step6_ensemble.py \\")
        print("      data/phase12_umatan/predictions/binary/船橋_20260422_binary.csv \\")
        print("      data/phase12_umatan/predictions/ranking/船橋_20260422_ranking.csv \\")
        print("      data/phase12_umatan/predictions/regression/船橋_20260422_regression.csv \\")
        print("      data/phase12_umatan/predictions/ensemble/船橋_20260422_ensemble.csv \\")
        print("      0.3 0.5 0.2  # オプション: 重み（デフォルト: 0.3, 0.5, 0.2）")
        sys.exit(1)
    
    try:
        binary_csv = sys.argv[1]
        ranking_csv = sys.argv[2]
        regression_csv = sys.argv[3]
        output_csv = sys.argv[4]
        
        # オプション: 重み
        weight_binary = float(sys.argv[5]) if len(sys.argv) > 5 else 0.3
        weight_ranking = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
        weight_regression = float(sys.argv[7]) if len(sys.argv) > 7 else 0.2
        
        ensemble_predictions(binary_csv, ranking_csv, regression_csv, output_csv,
                           weight_binary, weight_ranking, weight_regression)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
