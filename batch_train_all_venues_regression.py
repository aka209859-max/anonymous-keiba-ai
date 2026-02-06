#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全14競馬場 Phase 4 回帰モデル再学習バッチスクリプト
"""

import os
import sys
import subprocess

# 全14競馬場の設定
VENUES = [
    {'name': 'funabashi', 'period': '2020-2025'},
    {'name': 'himeji', 'period': '2020-2025'},
    {'name': 'kanazawa', 'period': '2020-2025'},
    {'name': 'kasamatsu', 'period': '2020-2025'},
    {'name': 'kawasaki', 'period': '2020-2025'},
    {'name': 'kochi', 'period': '2020-2025'},
    {'name': 'mizusawa', 'period': '2020-2025'},
    {'name': 'monbetsu', 'period': '2020-2025'},
    {'name': 'morioka', 'period': '2020-2025'},
    {'name': 'nagoya', 'period': '2022-2025'},
    {'name': 'ooi', 'period': '2023-2025'},
    {'name': 'saga', 'period': '2020-2025'},
    {'name': 'sonoda', 'period': '2020-2025'},
    {'name': 'urawa', 'period': '2020-2025'},
]

def main():
    """
    全14競馬場の Phase 4 回帰モデルを一括再学習
    """
    print("=" * 80)
    print("全14競馬場 Phase 4 回帰モデル再学習バッチ処理")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    errors = []
    
    for i, venue in enumerate(VENUES, 1):
        venue_name = venue['name']
        period = venue['period']
        
        # ファイル名
        training_csv = f"{venue_name}_{period}_with_time.csv"
        model_file = f"{venue_name}_{period}_with_time_regression_model.txt"
        
        # ファイル存在確認
        if not os.path.exists(training_csv):
            error_msg = f"❌ {venue_name}: 学習データが見つかりません ({training_csv})"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
            continue
        
        # train_regression_model.py を実行
        print(f"\n{'=' * 80}")
        print(f"🏇 [{i}/{len(VENUES)}] {venue_name} ({period}) - Phase 4 回帰モデル学習中...")
        print(f"{'=' * 80}")
        
        try:
            cmd = [
                'python', 'train_regression_model.py',
                training_csv
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30分タイムアウト
            
            if result.returncode == 0:
                print(result.stdout)
                print(f"✅ {venue_name}: 学習完了 → {model_file}")
                success_count += 1
            else:
                error_msg = f"❌ {venue_name}: エラー発生\n{result.stderr}"
                print(error_msg)
                errors.append(error_msg)
                error_count += 1
        
        except subprocess.TimeoutExpired:
            error_msg = f"❌ {venue_name}: タイムアウト（30分超過）"
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
    print("Phase 4 回帰モデル再学習完了")
    print("=" * 80)
    print(f"成功: {success_count}/{len(VENUES)}競馬場")
    print(f"失敗: {error_count}/{len(VENUES)}競馬場")
    
    if errors:
        print("\n⚠️ エラー詳細:")
        for error in errors:
            print(error)
    else:
        print("\n✅ 全14競馬場の Phase 4 回帰モデル再学習が完了しました！")
        print("\n次のステップ:")
        print("1. 各競馬場のモデルで予測を実行")
        print("2. Phase 5 アンサンブル統合")
        print("3. Phase 5.5 実払戻金バックテスト")

if __name__ == '__main__':
    main()
