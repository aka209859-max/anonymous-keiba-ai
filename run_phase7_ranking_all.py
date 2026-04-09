#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 7 Ranking 一括実行スクリプト
残り13会場のRanking特徴量選択を自動実行
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# 対象会場（船橋を除く13会場）
VENUES = [
    "monbetsu",   # 門別 (30)
    "morioka",    # 盛岡 (35)
    "mizusawa",   # 水沢 (36)
    "urawa",      # 浦和 (42)
    "ooi",        # 大井 (44)
    "kawasaki",   # 川崎 (45)
    "kanazawa",   # 金沢 (46)
    "kasamatsu",  # 笠松 (47)
    "nagoya",     # 名古屋 (48)
    "sonoda",     # 園田 (50)
    "himeji",     # 姫路 (51)
    "kochi",      # 高知 (54)
    "saga"        # 佐賀 (55)
]

def main():
    print("=" * 60)
    print("Phase 7 Ranking 一括実行開始")
    print("=" * 60)
    print()
    
    total = len(VENUES)
    start_time = datetime.now()
    
    for i, venue in enumerate(VENUES, 1):
        print("-" * 60)
        print(f"[{i}/{total}] Phase 7 Ranking: {venue}")
        print("-" * 60)
        
        input_file = f"data/training/{venue}_2020-2026_with_time_PHASE78.csv"
        
        # ファイル存在確認
        if not Path(input_file).exists():
            print(f"❌ ERROR: 入力ファイルが見つかりません: {input_file}")
            continue
        
        # Phase 7 Ranking 実行
        venue_start = datetime.now()
        
        result = subprocess.run([
            sys.executable,
            "scripts/phase7_feature_selection/run_boruta_ranking.py",
            input_file,
            "--max-iter", "100"
        ])
        
        venue_end = datetime.now()
        venue_elapsed = venue_end - venue_start
        
        if result.returncode == 0:
            print(f"✅ {venue} 完了 (所要時間: {venue_elapsed})")
        else:
            print(f"❌ {venue} 失敗 (終了コード: {result.returncode})")
        
        print()
    
    end_time = datetime.now()
    total_elapsed = end_time - start_time
    
    print("=" * 60)
    print("Phase 7 Ranking 一括実行完了")
    print("=" * 60)
    print(f"総実行時間: {total_elapsed}")
    print()
    
    # 完了ファイル確認
    print("出力ファイル確認:")
    selected_dir = Path("data/features/selected")
    if selected_dir.exists():
        for file in sorted(selected_dir.glob("*_ranking_selected_features.csv")):
            print(f"  ✅ {file.name}")
    
    print()
    print("次のステップ: Phase 7 Regression を実行してください")
    print("実行コマンド: python run_phase7_regression_all.py")

if __name__ == "__main__":
    main()
