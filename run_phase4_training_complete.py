#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_phase4_training_complete.py
Phase 4 の全14競馬場学習を一括実行（完全版）

使用法:
    python run_phase4_training_complete.py
"""
import subprocess
import os
from datetime import datetime


# 全14競馬場の定義
VENUES = [
    # 南関東4場
    {'code': '44', 'name': '大井', 'csv': 'ooi_2020-2025_v3.csv'},
    {'code': '43', 'name': '船橋', 'csv': 'funabashi_2020-2025_v3.csv'},
    {'code': '45', 'name': '川崎', 'csv': 'kawasaki_2020-2025_v3.csv'},
    {'code': '42', 'name': '浦和', 'csv': 'urawa_2020-2025_v3.csv'},
    
    # 北海道・東北
    {'code': '30', 'name': '門別', 'csv': 'mombetsu_2020-2025_v3.csv'},
    {'code': '35', 'name': '盛岡', 'csv': 'morioka_2020-2025_v3.csv'},
    {'code': '36', 'name': '水沢', 'csv': 'mizusawa_2020-2025_v3.csv'},
    
    # 中部
    {'code': '46', 'name': '金沢', 'csv': 'kanazawa_2020-2025_v3.csv'},
    {'code': '48', 'name': '名古屋', 'csv': 'nagoya_2022-2025_v3.csv'},
    {'code': '47', 'name': '笠松', 'csv': 'kasamatsu_2020-2025_v3.csv'},
    
    # 近畿
    {'code': '50', 'name': '園田', 'csv': 'sonoda_2020-2025_v3.csv'},
    {'code': '51', 'name': '姫路', 'csv': 'himeji_2020-2025_v3.csv'},
    
    # 四国・九州
    {'code': '54', 'name': '高知', 'csv': 'kochi_2020-2025_v3.csv'},
    {'code': '55', 'name': '佐賀', 'csv': 'saga_2020-2025_v3.csv'},
]


def run_command(cmd, description, timeout=600):
    """コマンドを実行（タイムアウト10分）"""
    print(f"\n{'='*80}")
    print(f"🔄 {description}")
    print(f"{'='*80}")
    print(f"コマンド: {' '.join(cmd)}\n")
    
    start_time = datetime.now()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result.returncode == 0:
            print(f"\n✅ 成功 ({duration:.1f}秒)")
            return True
        else:
            print(f"\n❌ 失敗 (終了コード: {result.returncode})")
            print(f"STDERR: {result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"\n⚠️ タイムアウト（{timeout}秒超過）")
        return False


def main():
    """メイン処理"""
    print("=" * 80)
    print("Phase 4 全14競馬場 学習スクリプト（完全版）")
    print("=" * 80)
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象競馬場数: {len(VENUES)}場\n")
    
    results = {
        'step1_race_id': {'success': [], 'failed': [], 'skipped': []},
        'step2_convert': {'success': [], 'failed': [], 'skipped': []},
        'step3_ranking': {'success': [], 'failed': [], 'skipped': []},
        'step4_regression': {'success': [], 'failed': [], 'skipped': []},
    }
    
    for venue in VENUES:
        name = venue['name']
        csv_file = venue['csv']
        
        print("\n" + "=" * 80)
        print(f"📍 {name}競馬場 の学習を開始")
        print("=" * 80)
        
        # ファイルの存在確認
        if not os.path.exists(csv_file):
            print(f"⚠️ ファイルが見つかりません: {csv_file}")
            print(f"   以下のコマンドでデータを抽出してください:")
            print(f"   python extract_training_data_v2.py --keibajo {venue['code']} --start-date 2020 --end-date 2025 --output {csv_file}")
            results['step1_race_id']['skipped'].append(name)
            results['step2_convert']['skipped'].append(name)
            results['step3_ranking']['skipped'].append(name)
            results['step4_regression']['skipped'].append(name)
            continue
        
        # Step 1: race_id 追加
        csv_with_race_id = csv_file.replace('.csv', '_with_race_id.csv')
        if not os.path.exists(csv_with_race_id):
            success = run_command(
                ['python', 'add_race_id_to_csv.py', csv_file],
                f"{name}: Step 1 - race_id 追加"
            )
            if success:
                results['step1_race_id']['success'].append(name)
            else:
                results['step1_race_id']['failed'].append(name)
                continue
        else:
            print(f"✅ {csv_with_race_id} は既に存在します（スキップ）")
            results['step1_race_id']['skipped'].append(name)
        
        # Step 2: target 変換（走破タイム）
        csv_time = csv_file.replace('.csv', '_time.csv')
        if not os.path.exists(csv_time):
            success = run_command(
                ['python', 'convert_target_to_time.py', csv_file],
                f"{name}: Step 2 - target 変換（走破タイム）"
            )
            if success:
                results['step2_convert']['success'].append(name)
            else:
                results['step2_convert']['failed'].append(name)
                continue
        else:
            print(f"✅ {csv_time} は既に存在します（スキップ）")
            results['step2_convert']['skipped'].append(name)
        
        # Step 3: ランキング学習（タイムアウト10分）
        ranking_model = csv_with_race_id.replace('.csv', '_ranking_model.txt')
        if not os.path.exists(ranking_model):
            success = run_command(
                ['python', 'train_ranking_model.py', csv_with_race_id],
                f"{name}: Step 3 - ランキング学習",
                timeout=600  # 10分
            )
            if success:
                results['step3_ranking']['success'].append(name)
            else:
                results['step3_ranking']['failed'].append(name)
        else:
            print(f"✅ {ranking_model} は既に存在します（スキップ）")
            results['step3_ranking']['skipped'].append(name)
        
        # Step 4: 回帰学習（タイムアウト10分）
        regression_model = csv_time.replace('.csv', '_regression_model.txt')
        if not os.path.exists(regression_model):
            success = run_command(
                ['python', 'train_regression_model.py', csv_time],
                f"{name}: Step 4 - 回帰学習",
                timeout=600  # 10分
            )
            if success:
                results['step4_regression']['success'].append(name)
            else:
                results['step4_regression']['failed'].append(name)
        else:
            print(f"✅ {regression_model} は既に存在します（スキップ）")
            results['step4_regression']['skipped'].append(name)
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("Phase 4 学習完了！")
    print("=" * 80)
    print(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n【実行結果サマリー】\n")
    
    for step_name, step_label in [
        ('step1_race_id', 'Step 1: race_id 追加'),
        ('step2_convert', 'Step 2: target 変換'),
        ('step3_ranking', 'Step 3: ランキング学習'),
        ('step4_regression', 'Step 4: 回帰学習'),
    ]:
        step_result = results[step_name]
        print(f"{step_label}")
        print(f"  ✅ 成功: {len(step_result['success'])}件")
        print(f"  ❌ 失敗: {len(step_result['failed'])}件")
        print(f"  ⚠️ スキップ: {len(step_result['skipped'])}件")
        print()
    
    # 総合結果
    total_success = sum(len(results[step]['success']) for step in results)
    total_failed = sum(len(results[step]['failed']) for step in results)
    total_skipped = sum(len(results[step]['skipped']) for step in results)
    
    print("=" * 80)
    print("【総合結果】")
    print(f"  ✅ 成功: {total_success}件")
    print(f"  ❌ 失敗: {total_failed}件")
    print(f"  ⚠️ スキップ: {total_skipped}件")
    print("=" * 80)
    
    if total_failed > 0:
        print("\n⚠️ 一部の処理が失敗しました。上記のログを確認してください。")
        return 1
    else:
        print("\n🎉 すべての処理が正常に完了しました！")
        return 0


if __name__ == '__main__':
    exit(main())
