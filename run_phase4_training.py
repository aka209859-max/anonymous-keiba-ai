#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_phase4_training.py
Phase 4 の全競馬場学習を一括実行

使用法:
    python run_phase4_training.py
"""
import subprocess
import os
from datetime import datetime


VENUES = [
    {'code': '44', 'name': '大井', 'csv': 'ooi_2023-2024_v3.csv'},
    {'code': '43', 'name': '船橋', 'csv': 'funabashi_2020-2025_v3.csv'},
    {'code': '45', 'name': '川崎', 'csv': 'kawasaki_2020-2025_v3.csv'},
    {'code': '42', 'name': '浦和', 'csv': 'urawa_2020-2025_v3.csv'},
    {'code': '48', 'name': '名古屋', 'csv': 'nagoya_2022-2025_v3.csv'},
    {'code': '50', 'name': '園田', 'csv': 'sonoda_2020-2025_v3.csv'},
    {'code': '47', 'name': '笠松', 'csv': 'kasamatsu_2020-2025_v3.csv'},
    {'code': '55', 'name': '佐賀', 'csv': 'saga_2020-2025_v3.csv'},
    {'code': '54', 'name': '高知', 'csv': 'kochi_2020-2025_v3.csv'},
    {'code': '51', 'name': '姫路', 'csv': 'himeji_2020-2025_v3.csv'},
]


def run_command(cmd, description):
    """コマンドを実行"""
    print(f"\n{'='*80}")
    print(f"🔄 {description}")
    print(f"{'='*80}")
    print(f"コマンド: {' '.join(cmd)}\n")
    
    start_time = datetime.now()
    result = subprocess.run(cmd, capture_output=False)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if result.returncode == 0:
        print(f"\n✅ 成功 ({duration:.1f}秒)")
        return True
    else:
        print(f"\n❌ 失敗 (終了コード: {result.returncode})")
        return False


def main():
    """メイン処理"""
    
    print("="*80)
    print("Phase 4 完全実行スクリプト")
    print("="*80)
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        'race_id': {'success': 0, 'fail': 0, 'skip': 0},
        'time_conversion': {'success': 0, 'fail': 0, 'skip': 0},
        'ranking': {'success': 0, 'fail': 0, 'skip': 0},
        'regression': {'success': 0, 'fail': 0, 'skip': 0}
    }
    
    # Step 1: race_id 追加
    print("\n\n" + "="*80)
    print("【Step 1】race_id カラムの追加")
    print("="*80)
    
    for venue in VENUES:
        csv_file = venue['csv']
        if os.path.exists(csv_file):
            success = run_command(
                ['python', 'add_race_id_to_csv.py', csv_file],
                f"{venue['name']} ({venue['code']}) - race_id追加"
            )
            if success:
                results['race_id']['success'] += 1
            else:
                results['race_id']['fail'] += 1
        else:
            print(f"\n⚠️ スキップ: {csv_file} が見つかりません")
            results['race_id']['skip'] += 1
    
    # Step 2: target変換（走破タイム）
    print("\n\n" + "="*80)
    print("【Step 2】target を走破タイムに変換")
    print("="*80)
    
    for venue in VENUES:
        csv_file = venue['csv']
        if os.path.exists(csv_file):
            success = run_command(
                ['python', 'convert_target_to_time.py', csv_file],
                f"{venue['name']} ({venue['code']}) - target変換"
            )
            if success:
                results['time_conversion']['success'] += 1
            else:
                results['time_conversion']['fail'] += 1
        else:
            print(f"\n⚠️ スキップ: {csv_file} が見つかりません")
            results['time_conversion']['skip'] += 1
    
    # Step 3: ランキングモデル学習
    print("\n\n" + "="*80)
    print("【Step 3】ランキングモデル学習")
    print("="*80)
    
    for venue in VENUES:
        csv_file_with_race_id = venue['csv'].replace('.csv', '_with_race_id.csv')
        if os.path.exists(csv_file_with_race_id):
            success = run_command(
                ['python', 'train_ranking_model.py', csv_file_with_race_id],
                f"{venue['name']} ({venue['code']}) - ランキング学習"
            )
            if success:
                results['ranking']['success'] += 1
            else:
                results['ranking']['fail'] += 1
        else:
            print(f"\n⚠️ スキップ: {csv_file_with_race_id} が見つかりません")
            results['ranking']['skip'] += 1
    
    # Step 4: 回帰モデル学習
    print("\n\n" + "="*80)
    print("【Step 4】回帰モデル学習")
    print("="*80)
    
    for venue in VENUES:
        csv_file_time = venue['csv'].replace('.csv', '_time.csv')
        if os.path.exists(csv_file_time):
            success = run_command(
                ['python', 'train_regression_model.py', csv_file_time],
                f"{venue['name']} ({venue['code']}) - 回帰学習"
            )
            if success:
                results['regression']['success'] += 1
            else:
                results['regression']['fail'] += 1
        else:
            print(f"\n⚠️ スキップ: {csv_file_time} が見つかりません")
            results['regression']['skip'] += 1
    
    # 最終サマリー
    print("\n\n" + "="*80)
    print("Phase 4 学習完了！")
    print("="*80)
    print(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("【実行結果サマリー】\n")
    
    print("Step 1: race_id 追加")
    print(f"  ✅ 成功: {results['race_id']['success']}件")
    print(f"  ❌ 失敗: {results['race_id']['fail']}件")
    print(f"  ⚠️ スキップ: {results['race_id']['skip']}件")
    
    print("\nStep 2: target 変換")
    print(f"  ✅ 成功: {results['time_conversion']['success']}件")
    print(f"  ❌ 失敗: {results['time_conversion']['fail']}件")
    print(f"  ⚠️ スキップ: {results['time_conversion']['skip']}件")
    
    print("\nStep 3: ランキング学習")
    print(f"  ✅ 成功: {results['ranking']['success']}件")
    print(f"  ❌ 失敗: {results['ranking']['fail']}件")
    print(f"  ⚠️ スキップ: {results['ranking']['skip']}件")
    
    print("\nStep 4: 回帰学習")
    print(f"  ✅ 成功: {results['regression']['success']}件")
    print(f"  ❌ 失敗: {results['regression']['fail']}件")
    print(f"  ⚠️ スキップ: {results['regression']['skip']}件")
    
    # 総合判定
    total_success = sum([r['success'] for r in results.values()])
    total_fail = sum([r['fail'] for r in results.values()])
    total_skip = sum([r['skip'] for r in results.values()])
    
    print("\n" + "="*80)
    print(f"【総合結果】")
    print(f"  ✅ 成功: {total_success}件")
    print(f"  ❌ 失敗: {total_fail}件")
    print(f"  ⚠️ スキップ: {total_skip}件")
    print("="*80 + "\n")
    
    if total_fail == 0:
        print("🎉 全ての処理が正常に完了しました！")
        print("次のステップ: アンサンブル予測を実行してください。\n")
    else:
        print("⚠️ 一部の処理が失敗しました。上記のログを確認してください。\n")


if __name__ == "__main__":
    main()
