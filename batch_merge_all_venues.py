#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全14競馬場の走破タイム統合バッチスクリプト
"""

import os
import sys
import subprocess

# 全14競馬場の設定
VENUES = [
    {'name': 'funabashi', 'period': '2020-2025', 'code': '43'},
    {'name': 'himeji', 'period': '2020-2025', 'code': '51'},
    {'name': 'kanazawa', 'period': '2020-2025', 'code': '46'},
    {'name': 'kasamatsu', 'period': '2020-2025', 'code': '47'},
    {'name': 'kawasaki', 'period': '2020-2025', 'code': '45'},
    {'name': 'kochi', 'period': '2020-2025', 'code': '54'},
    {'name': 'mizusawa', 'period': '2020-2025', 'code': '36'},
    {'name': 'monbetsu', 'period': '2020-2025', 'code': '30'},
    {'name': 'morioka', 'period': '2020-2025', 'code': '35'},
    {'name': 'nagoya', 'period': '2022-2025', 'code': '48'},
    {'name': 'ooi', 'period': '2023-2025', 'code': '44'},
    {'name': 'saga', 'period': '2020-2025', 'code': '55'},
    {'name': 'sonoda', 'period': '2020-2025', 'code': '50'},
    {'name': 'urawa', 'period': '2020-2025', 'code': '42'},
]

def main():
    """
    全14競馬場の走破タイム統合を一括実行
    """
    print("=" * 80)
    print("全14競馬場 走破タイム統合バッチ処理")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    errors = []
    
    for venue in VENUES:
        venue_name = venue['name']
        period = venue['period']
        
        # ファイル名
        training_csv = f"{venue_name}_{period}_v3.csv"
        soha_time_csv = f"{venue_name}_{period}_soha_time.csv"
        output_csv = f"{venue_name}_{period}_with_time.csv"
        
        # ファイル存在確認
        if not os.path.exists(training_csv):
            error_msg = f"❌ {venue_name}: 学習データが見つかりません ({training_csv})"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
            continue
        
        if not os.path.exists(soha_time_csv):
            error_msg = f"❌ {venue_name}: 走破タイムデータが見つかりません ({soha_time_csv})"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
            continue
        
        # merge_soha_time.py を実行
        print(f"\n{'=' * 80}")
        print(f"🏇 {venue_name} ({period}) - 走破タイム統合中...")
        print(f"{'=' * 80}")
        
        try:
            cmd = [
                'python', 'merge_soha_time.py',
                training_csv,
                soha_time_csv,
                output_csv
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
                print(f"✅ {venue_name}: 統合完了 → {output_csv}")
                success_count += 1
            else:
                error_msg = f"❌ {venue_name}: エラー発生\n{result.stderr}"
                print(error_msg)
                errors.append(error_msg)
                error_count += 1
        
        except Exception as e:
            error_msg = f"❌ {venue_name}: 例外発生 - {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
    
    # 最終サマリー
    print("\n" + "=" * 80)
    print("統合処理完了")
    print("=" * 80)
    print(f"成功: {success_count}/{len(VENUES)}競馬場")
    print(f"失敗: {error_count}/{len(VENUES)}競馬場")
    
    if errors:
        print("\n⚠️ エラー詳細:")
        for error in errors:
            print(error)
    else:
        print("\n✅ 全14競馬場の走破タイム統合が完了しました！")
        print("\n次のステップ:")
        print("1. python batch_train_all_venues_regression.py")
        print("   → 全14競馬場の Phase 4 回帰モデルを再学習")

if __name__ == '__main__':
    main()
