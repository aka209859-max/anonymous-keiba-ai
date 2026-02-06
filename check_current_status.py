"""
現在のE:/anonymous-keiba-ai/の状態を確認するスクリプト
Windows コマンドプロンプト対応版（絵文字なし、完全ASCII）
"""
import os
import sys
from pathlib import Path
from collections import defaultdict

# Windows環境での出力エンコーディング設定
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def scan_directory(root_path):
    """ディレクトリをスキャンして現状を把握"""
    
    root = Path(root_path)
    
    # ファイル分類
    file_categories = {
        'models': defaultdict(list),
        'data': defaultdict(list),
        'scripts': [],
        'results': [],
        'docs': [],
        'others': []
    }
    
    print("="*80)
    print("[SCAN TARGET] {}".format(root_path))
    print("="*80)
    
    # 全ファイルをスキャン
    for item in root.rglob('*'):
        if item.is_file():
            # モデルファイル
            if 'model.txt' in item.name or '_v3' in item.name:
                if 'ranking' in item.name:
                    file_categories['models']['ranking'].append(item)
                elif 'regression' in item.name or 'time' in item.name:
                    file_categories['models']['regression'].append(item)
                else:
                    file_categories['models']['binary'].append(item)
            
            # データファイル
            elif '.csv' in item.name:
                if 'payouts' in item.name or 'haraimodoshi' in item.name:
                    file_categories['data']['payouts'].append(item)
                elif 'ensemble' in item.name:
                    file_categories['data']['ensemble'].append(item)
                elif 'features' in item.name:
                    file_categories['data']['features'].append(item)
                elif 'phase3' in item.name or 'phase4' in item.name:
                    file_categories['data']['predictions'].append(item)
                else:
                    file_categories['data']['raw'].append(item)
            
            # スクリプト
            elif '.py' in item.name:
                file_categories['scripts'].append(item)
            
            # 結果ファイル
            elif '.json' in item.name:
                file_categories['results'].append(item)
            
            # ドキュメント
            elif '.md' in item.name or '.txt' in item.name:
                file_categories['docs'].append(item)
            
            # その他
            else:
                file_categories['others'].append(item)
    
    # 結果表示
    print("\n" + "="*80)
    print("[CURRENT STATUS REPORT]")
    print("="*80)
    
    # モデルファイル
    print("\n[TRAINED MODELS]")
    for model_type, files in file_categories['models'].items():
        print("\n  {}:".format(model_type.upper()))
        
        # 競馬場別にカウント
        keibajo_count = defaultdict(int)
        for f in files:
            # ファイル名から競馬場を推定
            name = f.stem.lower()
            for keibajo in ['ooi', 'kawasaki', 'funabashi', 'urawa', 'monbetsu', 
                           'morioka', 'mizusawa', 'kanazawa', 'kasamatsu', 
                           'nagoya', 'sonoda', 'himeji', 'kochi', 'saga']:
                if keibajo in name:
                    keibajo_count[keibajo] += 1
                    break
        
        print("    Total: {} files".format(len(files)))
        print("    By Keibajo:")
        for keibajo, count in sorted(keibajo_count.items()):
            print("      - {}: {} file(s)".format(keibajo, count))
        
        # 不足している競馬場を確認
        all_keibajo = ['ooi', 'kawasaki', 'funabashi', 'urawa', 'monbetsu', 
                      'morioka', 'mizusawa', 'kanazawa', 'kasamatsu', 
                      'nagoya', 'sonoda', 'himeji', 'kochi', 'saga']
        missing_keibajo = [k for k in all_keibajo if k not in keibajo_count]
        if missing_keibajo:
            print("    Missing Keibajo: {}".format(', '.join(missing_keibajo)))
    
    # データファイル
    print("\n[DATA FILES]")
    for data_type, files in file_categories['data'].items():
        if files:
            print("\n  {}:".format(data_type.upper()))
            print("    Total: {} files".format(len(files)))
            # サンプルを3つ表示
            print("    Sample:")
            for f in files[:3]:
                size_mb = f.stat().st_size / (1024 * 1024)
                print("      - {} ({:.2f} MB)".format(f.name, size_mb))
            if len(files) > 3:
                print("      ... and {} more files".format(len(files)-3))
    
    # スクリプト
    print("\n[SCRIPTS]")
    print("  Total: {} files".format(len(file_categories['scripts'])))
    
    # Phase別に分類
    phase_scripts = defaultdict(list)
    for script in file_categories['scripts']:
        script_lower = script.name.lower()
        if 'phase' in script_lower:
            # phase番号を抽出
            found = False
            for i in range(10):
                if 'phase{}'.format(i) in script_lower or 'phase_{}'.format(i) in script_lower:
                    phase_scripts['Phase {}'.format(i)].append(script.name)
                    found = True
                    break
            if not found:
                phase_scripts['Phase (other)'].append(script.name)
        elif 'backtest' in script_lower:
            phase_scripts['Backtest'].append(script.name)
        elif 'run' in script_lower or 'batch' in script_lower:
            phase_scripts['Execution'].append(script.name)
        else:
            phase_scripts['Other'].append(script.name)
    
    for phase, scripts in sorted(phase_scripts.items()):
        print("\n  {}:".format(phase))
        for script in sorted(scripts)[:5]:  # 最大5つ表示
            print("    - {}".format(script))
        if len(scripts) > 5:
            print("    ... and {} more files".format(len(scripts)-5))
    
    # 結果ファイル
    print("\n[RESULT FILES (JSON)]")
    print("  Total: {} files".format(len(file_categories['results'])))
    if file_categories['results']:
        print("  Sample:")
        for result in sorted(file_categories['results'], key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            print("    - {}".format(result.name))
    
    # ドキュメント
    print("\n[DOCUMENTS]")
    print("  Total: {} files".format(len(file_categories['docs'])))
    if file_categories['docs']:
        for doc in sorted(file_categories['docs'])[:10]:
            print("    - {}".format(doc.name))
    
    # その他
    if file_categories['others']:
        print("\n[OTHER FILES]")
        print("  Total: {} files".format(len(file_categories['others'])))
        # 拡張子別に集計
        ext_count = defaultdict(int)
        for f in file_categories['others']:
            ext = f.suffix if f.suffix else '(no extension)'
            ext_count[ext] += 1
        print("  By Extension:")
        for ext, count in sorted(ext_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            print("    - {}: {} file(s)".format(ext, count))
    
    # サマリー
    print("\n" + "="*80)
    print("[SUMMARY]")
    print("="*80)
    total_models = sum(len(files) for files in file_categories['models'].values())
    total_data = sum(len(files) for files in file_categories['data'].values())
    
    print("  Trained Models: {} files".format(total_models))
    print("  Data Files: {} files".format(total_data))
    print("  Scripts: {} files".format(len(file_categories['scripts'])))
    print("  Result Files: {} files".format(len(file_categories['results'])))
    print("  Documents: {} files".format(len(file_categories['docs'])))
    print("  Other Files: {} files".format(len(file_categories['others'])))
    
    # 詳細内訳
    print("\n  Model Breakdown:")
    for model_type, files in file_categories['models'].items():
        print("    - {}: {} files".format(model_type, len(files)))
    
    print("\n  Data Breakdown:")
    for data_type, files in file_categories['data'].items():
        if files:
            print("    - {}: {} files".format(data_type, len(files)))
    
    # 不足チェック
    print("\n" + "="*80)
    print("[MISSING OR ATTENTION REQUIRED]")
    print("="*80)
    
    # モデルの不足チェック（14競馬場 × 3種類 = 42ファイル期待）
    expected_models = 14 * 3
    if total_models < expected_models:
        print("  [X] Model files shortage: {}/{} files".format(total_models, expected_models))
        print("      Missing: {} files".format(expected_models - total_models))
        
        # 各モデルタイプの不足を確認
        for model_type in ['binary', 'ranking', 'regression']:
            count = len(file_categories['models'][model_type])
            if count < 14:
                print("      - {}: {}/14 (missing {})".format(model_type, count, 14-count))
    else:
        print("  [OK] Model files: All files may be present ({} files)".format(total_models))
    
    # Phase 0-6のスクリプトチェック
    required_phases = ['Phase 0', 'Phase 1', 'Phase 3', 'Phase 4', 'Phase 5', 'Phase 6']
    missing_phases = [p for p in required_phases if p not in phase_scripts or not phase_scripts[p]]
    
    if missing_phases:
        print("  [X] Missing Phase scripts: {}".format(', '.join(missing_phases)))
    else:
        print("  [OK] All Phase scripts exist")
    
    # バッチファイルチェック
    batch_files = [f for f in file_categories['scripts'] if '.bat' in f.name or '.sh' in f.name]
    if not batch_files:
        print("  [X] Batch execution files (.bat/.sh) not found")
    else:
        print("  [OK] Batch files: {} file(s)".format(len(batch_files)))
        for batch in batch_files:
            print("      - {}".format(batch.name))
    
    # フォルダ構造のチェック
    print("\n  [FOLDER STRUCTURE CHECK]")
    expected_folders = ['models', 'scripts', 'data', 'output', 'backtest', 'docs', 'config']
    existing_folders = set()
    for item in root.iterdir():
        if item.is_dir():
            existing_folders.add(item.name)
    
    missing_folders = [f for f in expected_folders if f not in existing_folders]
    if missing_folders:
        print("  [!] Recommended folders not found: {}".format(', '.join(missing_folders)))
    else:
        print("  [OK] All recommended folders exist")
    
    print("\n  Existing folders:")
    for folder in sorted(existing_folders):
        print("    - {}/".format(folder))
    
    print("\n" + "="*80)
    print("[SCAN COMPLETED]")
    print("="*80)
    
    print("\n[NEXT STEPS]")
    print("  1. Review missing files")
    print("  2. Reorganize folder structure")
    print("  3. Create README.md for documentation")
    print("  4. Download missing model files from sandbox")
    
    return file_categories

if __name__ == "__main__":
    root_path = "E:/anonymous-keiba-ai/"
    
    # ディレクトリが存在するか確認
    if not os.path.exists(root_path):
        print("[ERROR] Path not found: {}".format(root_path))
        print("Please check the path")
    else:
        try:
            scan_directory(root_path)
        except Exception as e:
            print("\n[ERROR] An error occurred during scan:")
            print("  {}: {}".format(type(e).__name__, e))
            import traceback
            traceback.print_exc()
