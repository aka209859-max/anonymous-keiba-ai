#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8 Regression 一括実行スクリプト
残り13会場のRegression最適化を自動実行
注意: Phase 7 Regression 完了後に実行してください
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
    print("Phase 8 Regression 一括実行開始")
    print("=" * 60)
    print()
    
    total = len(VENUES)
    start_time = datetime.now()
    
    for i, venue in enumerate(VENUES, 1):
        print("-" * 60)
        print(f"[{i}/{total}] Phase 8 Regression: {venue}")
        print("-" * 60)
        
        input_file = f"data/training/{venue}_2020-2026_with_time_PHASE78.csv"
        selected_features = f"data/features/selected/{venue}_regression_selected_features.csv"
        
        # ファイル存在確認
        if not Path(input_file).exists():
            print(f"❌ ERROR: 入力ファイルが見つかりません: {input_file}")
            continue
        
        if not Path(selected_features).exists():
            print(f"❌ ERROR: 選択特徴量ファイルが見つかりません: {selected_features}")
            print("Phase 7 Regression を先に実行してください")
            continue
        
        # Phase 8 Regression 実行
        venue_start = datetime.now()
        
        result = subprocess.run([
            sys.executable,
            "scripts/phase8_auto_tuning/run_optuna_tuning_regression.py",
            input_file,
            "--selected-features", selected_features,
            "--n-trials", "100",
            "--timeout", "7200",
            "--cv-folds", "3"
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
    print("Phase 8 Regression 一括実行完了")
    print("=" * 60)
    print(f"総実行時間: {total_elapsed}")
    print()
    
    # 完了ファイル確認
    print("出力ファイル確認:")
    tuned_dir = Path("data/models/tuned")
    if tuned_dir.exists():
        for file in sorted(tuned_dir.glob("*_regression_best_params.csv")):
            print(f"  ✅ {file.name}")
    
    print()
    print("🎉 全Phase完了！")
    print("次のステップ: Phase 5 Ensemble 統合テストを実行してください")

if __name__ == "__main__":
    main()
