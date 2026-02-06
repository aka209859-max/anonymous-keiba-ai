#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
川崎競馬 2026-02-05 全レース予想結果サマリー表示

Phase 5アンサンブル結果をレース別に整形表示
"""

import pandas as pd
import sys

def display_race_predictions(csv_path):
    """
    アンサンブル予測結果を見やすく表示
    
    Parameters
    ----------
    csv_path : str
        Phase 5アンサンブル結果CSV
    """
    # データ読み込み
    try:
        df = pd.read_csv(csv_path, encoding='shift-jis')
    except:
        df = pd.read_csv(csv_path, encoding='utf-8')
    
    print("=" * 100)
    print("川崎競馬 2026-02-05 全レース予想結果")
    print("=" * 100)
    print(f"\n総データ件数: {len(df)}件")
    print(f"レース数: {df['race_id'].nunique()}レース")
    print()
    
    # レースごとに表示
    for race_id in sorted(df['race_id'].unique()):
        race_data = df[df['race_id'] == race_id].sort_values('final_rank')
        race_num = int(str(race_id)[-2:])
        horse_count = len(race_data)
        
        print("=" * 100)
        print(f"第{race_num}R ({horse_count}頭立)")
        print("=" * 100)
        print(f"{'順位':>4} {'馬番':>4} {'総合スコア':>12} {'入線確率':>10} {'予測ランク':>10} {'予測タイム':>10}")
        print("-" * 100)
        
        for idx, row in race_data.iterrows():
            print(f"{int(row['final_rank']):4d} "
                  f"{int(row['umaban']):4d}番 "
                  f"{row['ensemble_score']:11.4f}  "
                  f"{row['binary_probability']:9.3f}  "
                  f"{int(row['predicted_rank']):9d}位  "
                  f"{row['predicted_time']:9.2f}秒")
        
        # トップ3の詳細
        top3 = race_data.head(3)
        print()
        print("【本命】")
        for idx, row in top3.iterrows():
            rank = int(row['final_rank'])
            if rank == 1:
                label = "◎本命"
            elif rank == 2:
                label = "○対抗"
            elif rank == 3:
                label = "▲単穴"
            
            print(f"  {label}: {int(row['umaban'])}番 "
                  f"(スコア {row['ensemble_score']:.4f}, "
                  f"入線確率 {row['binary_probability']:.1%}, "
                  f"予測タイム {row['predicted_time']:.2f}秒)")
        print()
    
    print("=" * 100)
    print("予想完了")
    print("=" * 100)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python display_predictions.py <ensemble_csv>")
        print("\n例:")
        print("  python display_predictions.py data/predictions/phase5/川崎_20260205_ensemble.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    display_race_predictions(csv_path)
