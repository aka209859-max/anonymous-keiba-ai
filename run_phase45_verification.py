#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4.5 検証: 全14競馬場・3モデルで2026年1月データを予測

このスクリプトは2026年1月データの予測を一括実行します。
"""

import os
import subprocess
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# 競馬場リスト
VENUES = {
    'funabashi': '船橋',
    'himeji': '姫路',
    'kanazawa': '金沢',
    'kasamatsu': '笠松',
    'kawasaki': '川崎',
    'kochi': '高知',
    'mizusawa': '水沢',
    'monbetsu': '門別',
    'morioka': '盛岡',
    'nagoya': '名古屋',
    'ooi': '大井',
    'saga': '佐賀',
    'sonoda': '園田',
    'urawa': '浦和'
}

# モデルタイプ設定
MODEL_TYPES = {
    'binary': {
        'script': 'predict_phase3.py',
        'test_suffix': '_2026_jan_test.csv',
        'model_suffix': '_v3_model.txt',
        'output_suffix': '_2026_jan_binary_prediction.csv'
    },
    'ranking': {
        'script': 'predict_phase4_ranking.py',
        'test_suffix': '_2026_jan_test_with_race_id.csv',
        'model_suffix': '_v3_with_race_id_ranking_model.txt',
        'output_suffix': '_2026_jan_ranking_prediction.csv'
    },
    'regression': {
        'script': 'predict_phase4_regression.py',
        'test_suffix': '_2026_jan_test_time.csv',
        'model_suffix': '_v3_time_regression_model.txt',
        'output_suffix': '_2026_jan_regression_prediction.csv'
    }
}

def find_file_with_variations(directory, venue, suffix):
    """
    ファイル名の表記揺れに対応してファイルを探す
    
    Parameters
    ----------
    directory : str
        検索ディレクトリ
    venue : str
        競馬場名
    suffix : str
        ファイル名のサフィックス
    
    Returns
    -------
    str or None
        見つかったファイルパス、またはNone
    """
    # 標準の競馬場名
    variations = [venue]
    
    # 表記揺れ対応
    if venue == 'monbetsu':
        variations.append('mombetsu')
    elif venue == 'mombetsu':
        variations.append('monbetsu')
    
    # 期間の揺れも考慮（2020-2025, 2022-2025, 2023-2025など）
    for var in variations:
        # 完全一致を試す
        exact_path = os.path.join(directory, f"{var}{suffix}")
        if os.path.exists(exact_path):
            return exact_path
        
        # パターンマッチングで探す
        for file in Path(directory).glob(f"{var}*{suffix}"):
            return str(file)
    
    return None

def run_prediction(venue, venue_jp, model_type, test_csv_dir, model_dir, output_dir):
    """
    指定された競馬場・モデルタイプで予測を実行
    
    Parameters
    ----------
    venue : str
        競馬場名（例: ooi, funabashi）
    venue_jp : str
        競馬場名（日本語）
    model_type : str
        モデルタイプ（binary, ranking, regression）
    test_csv_dir : str
        テストデータCSVのディレクトリ
    model_dir : str
        学習済みモデルのディレクトリ
    output_dir : str
        予測結果の出力先ディレクトリ
    
    Returns
    -------
    dict
        実行結果
    """
    config = MODEL_TYPES[model_type]
    script = config['script']
    test_suffix = config['test_suffix']
    model_suffix = config['model_suffix']
    output_suffix = config['output_suffix']
    
    # テストCSVを探す
    test_csv = find_file_with_variations(test_csv_dir, venue, test_suffix)
    
    if not test_csv:
        return {
            'venue': venue,
            'venue_jp': venue_jp,
            'model_type': model_type,
            'status': 'skipped',
            'reason': 'テストCSVが見つかりません'
        }
    
    # モデルパスを探す
    model_path = find_file_with_variations(model_dir, venue, model_suffix)
    
    if not model_path:
        return {
            'venue': venue,
            'venue_jp': venue_jp,
            'model_type': model_type,
            'status': 'skipped',
            'reason': 'モデルファイルが見つかりません'
        }
    
    # 出力パス
    output_path = os.path.join(output_dir, f"{venue}{output_suffix}")
    
    # 予測実行
    print(f"\n{'='*70}")
    print(f"🏇 競馬場: {venue_jp} ({venue}) | モデル: {model_type}")
    print(f"{'='*70}")
    print(f"テストCSV: {test_csv}")
    print(f"モデル: {model_path}")
    print(f"出力先: {output_path}")
    
    try:
        result = subprocess.run(
            ['python', script, test_csv, model_path, output_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        
        return {
            'venue': venue,
            'venue_jp': venue_jp,
            'model_type': model_type,
            'status': 'success',
            'test_csv': test_csv,
            'model_path': model_path,
            'output_path': output_path
        }
    except subprocess.CalledProcessError as e:
        print(f"❌ エラー発生:")
        print(e.stderr)
        
        return {
            'venue': venue,
            'venue_jp': venue_jp,
            'model_type': model_type,
            'status': 'failed',
            'error': str(e),
            'stderr': e.stderr
        }

def main():
    """
    Phase 4.5 検証を一括実行
    """
    # ディレクトリ設定
    test_csv_dir = 'csv/2026_jan_test'
    model_dir = 'models'
    output_dir = 'predictions/2026_jan'
    
    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("Phase 4.5 実データ検証 - 2026年1月")
    print("=" * 70)
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"競馬場数: {len(VENUES)}")
    print(f"モデルタイプ: {len(MODEL_TYPES)}")
    print(f"総予測数: {len(VENUES) * len(MODEL_TYPES)}")
    print("=" * 70)
    
    results = []
    
    # 全競馬場・全モデルで予測実行
    for venue, venue_jp in VENUES.items():
        for model_type in MODEL_TYPES.keys():
            result = run_prediction(
                venue, venue_jp, model_type, 
                test_csv_dir, model_dir, output_dir
            )
            results.append(result)
    
    # 結果サマリー
    print("\n" + "=" * 70)
    print("Phase 4.5 検証完了")
    print("=" * 70)
    print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    skipped_count = sum(1 for r in results if r['status'] == 'skipped')
    
    print(f"\n✅ 成功: {success_count}/{len(results)}")
    print(f"❌ 失敗: {failed_count}/{len(results)}")
    print(f"⏭️  スキップ: {skipped_count}/{len(results)}")
    
    # スキップされた予測を表示
    if skipped_count > 0:
        print("\n⏭️  スキップされた予測:")
        for r in results:
            if r['status'] == 'skipped':
                print(f"  - {r['venue_jp']} ({r['venue']}) - {r['model_type']}: {r['reason']}")
    
    # 失敗した予測を表示
    if failed_count > 0:
        print("\n❌ 失敗した予測:")
        for r in results:
            if r['status'] == 'failed':
                print(f"  - {r['venue_jp']} ({r['venue']}) - {r['model_type']}")
    
    # 結果をJSONに保存
    results_json_path = os.path.join(output_dir, 'verification_summary.json')
    with open(results_json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n検証結果を保存: {results_json_path}")
    
    # 結果をCSVに保存
    results_csv_path = os.path.join(output_dir, 'verification_summary.csv')
    results_df = pd.DataFrame(results)
    results_df.to_csv(results_csv_path, index=False, encoding='utf-8-sig')
    print(f"検証結果を保存: {results_csv_path}")
    
    print("\n" + "=" * 70)
    if failed_count == 0 and skipped_count == 0:
        print("🎉 全ての予測が成功しました！")
    elif success_count > 0:
        print("⚠️  一部の予測が完了しました。")
    else:
        print("❌ 予測を実行できませんでした。")
    print("=" * 70)

if __name__ == "__main__":
    main()
