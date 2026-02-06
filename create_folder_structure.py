"""
E:/anonymous-keiba-ai/ の理想的なフォルダ構造を作成するスクリプト
既存のファイルを自動的に適切な場所に移動
"""
import os
import shutil
from pathlib import Path

def create_folder_structure(root_path):
    """理想的なフォルダ構造を作成"""
    
    root = Path(root_path)
    
    # フォルダ構造定義
    folders = {
        # モデル
        'models/binary': 'Phase 3: Binary classification models',
        'models/ranking': 'Phase 4: Ranking models',
        'models/regression': 'Phase 4: Regression models',
        
        # スクリプト
        'scripts/phase0_data_acquisition': 'Phase 0: Data acquisition scripts',
        'scripts/phase1_feature_engineering': 'Phase 1: Feature engineering scripts',
        'scripts/phase3_binary': 'Phase 3: Binary classification scripts',
        'scripts/phase4_ranking': 'Phase 4: Ranking prediction scripts',
        'scripts/phase4_regression': 'Phase 4: Regression prediction scripts',
        'scripts/phase5_ensemble': 'Phase 5: Ensemble integration scripts',
        'scripts/phase6_betting': 'Phase 6: Betting recommendation scripts',
        'scripts/utils': 'Utility scripts',
        'scripts/batch': 'Batch execution scripts',
        
        # データ
        'data/raw/2026/02': 'Raw data for February 2026',
        'data/raw/archive/2025': 'Archived raw data 2025',
        'data/raw/archive/2024': 'Archived raw data 2024',
        'data/features/2026/02': 'Feature data for February 2026',
        'data/features/archive': 'Archived feature data',
        'data/predictions/phase3': 'Phase 3 predictions',
        'data/predictions/phase4_ranking': 'Phase 4 ranking predictions',
        'data/predictions/phase4_regression': 'Phase 4 regression predictions',
        'data/predictions/phase5_ensemble': 'Phase 5 ensemble predictions',
        'data/payouts/2025': 'Payout data 2025',
        'data/payouts/2024': 'Payout data 2024',
        
        # 出力
        'output/web/2026/02': 'Web output for February 2026',
        'output/web/archive': 'Archived web output',
        'output/reports': 'Reports and summaries',
        'output/logs': 'Execution logs',
        
        # バックテスト
        'backtest/scripts': 'Backtest scripts',
        'backtest/results/2025': 'Backtest results 2025',
        'backtest/results/strategy_tests': 'Strategy test results',
        
        # ドキュメント
        'docs/images': 'Documentation images',
        
        # 設定
        'config': 'Configuration files',
        
        # テスト
        'tests': 'Test scripts',
        
        # アーカイブ
        'archive/old_scripts': 'Old scripts',
        'archive/old_models': 'Old models',
        'archive/old_results': 'Old results',
        
        # サンドボックス
        'sandbox': 'Experimental scripts'
    }
    
    print("="*80)
    print("[CREATE FOLDER STRUCTURE]")
    print("="*80)
    print("Target: {}".format(root_path))
    print("")
    
    # フォルダ作成
    created_count = 0
    exists_count = 0
    
    for folder_path, description in folders.items():
        full_path = root / folder_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print("[CREATE] {}".format(folder_path))
            created_count += 1
        else:
            print("[EXISTS] {}".format(folder_path))
            exists_count += 1
    
    print("")
    print("="*80)
    print("[SUMMARY]")
    print("="*80)
    print("  Created: {} folders".format(created_count))
    print("  Already exists: {} folders".format(exists_count))
    print("  Total: {} folders".format(created_count + exists_count))
    
    return folders

def move_existing_files(root_path, dry_run=True):
    """既存ファイルを適切な場所に移動"""
    
    root = Path(root_path)
    
    print("")
    print("="*80)
    print("[FILE ORGANIZATION]")
    print("="*80)
    if dry_run:
        print("MODE: DRY RUN (no actual moves)")
    else:
        print("MODE: ACTUAL MOVE")
    print("")
    
    # 移動ルール定義
    move_rules = []
    
    # モデルファイル
    for keibajo in ['ooi', 'kawasaki', 'funabashi', 'urawa', 'monbetsu', 
                    'morioka', 'mizusawa', 'kanazawa', 'kasamatsu', 
                    'nagoya', 'sonoda', 'himeji', 'kochi', 'saga']:
        # Binary models
        move_rules.append({
            'pattern': '{}_*_v3_model.txt'.format(keibajo),
            'destination': 'models/binary/',
            'description': 'Binary model for {}'.format(keibajo)
        })
        
        # Ranking models
        move_rules.append({
            'pattern': '{}_*_ranking_model.txt'.format(keibajo),
            'destination': 'models/ranking/',
            'description': 'Ranking model for {}'.format(keibajo)
        })
        
        # Regression models
        move_rules.append({
            'pattern': '{}_*_regression_model.txt'.format(keibajo),
            'destination': 'models/regression/',
            'description': 'Regression model for {}'.format(keibajo)
        })
    
    # データファイル
    move_rules.extend([
        # Payouts
        {'pattern': '*_payouts_*.csv', 'destination': 'data/payouts/2025/', 'description': 'Payout data'},
        
        # Ensemble
        {'pattern': '*_ensemble*.csv', 'destination': 'data/predictions/phase5_ensemble/', 'description': 'Ensemble predictions'},
        
        # Phase 3 predictions
        {'pattern': '*_phase3*.csv', 'destination': 'data/predictions/phase3/', 'description': 'Phase 3 predictions'},
        
        # Phase 4 ranking
        {'pattern': '*_phase4_ranking*.csv', 'destination': 'data/predictions/phase4_ranking/', 'description': 'Phase 4 ranking predictions'},
        
        # Phase 4 regression
        {'pattern': '*_phase4_regression*.csv', 'destination': 'data/predictions/phase4_regression/', 'description': 'Phase 4 regression predictions'},
        
        # Features
        {'pattern': '*_features*.csv', 'destination': 'data/features/2026/02/', 'description': 'Feature data'},
        
        # Raw data
        {'pattern': '*_raw*.csv', 'destination': 'data/raw/2026/02/', 'description': 'Raw data'},
        {'pattern': '*_full*.csv', 'destination': 'data/raw/archive/2025/', 'description': 'Full year data'},
    ])
    
    # スクリプト
    move_rules.extend([
        {'pattern': 'phase0*.py', 'destination': 'scripts/phase0_data_acquisition/', 'description': 'Phase 0 scripts'},
        {'pattern': 'phase1*.py', 'destination': 'scripts/phase1_feature_engineering/', 'description': 'Phase 1 scripts'},
        {'pattern': 'phase3*.py', 'destination': 'scripts/phase3_binary/', 'description': 'Phase 3 scripts'},
        {'pattern': 'phase4_ranking*.py', 'destination': 'scripts/phase4_ranking/', 'description': 'Phase 4 ranking scripts'},
        {'pattern': 'phase4_regression*.py', 'destination': 'scripts/phase4_regression/', 'description': 'Phase 4 regression scripts'},
        {'pattern': 'phase5*.py', 'destination': 'scripts/phase5_ensemble/', 'description': 'Phase 5 scripts'},
        {'pattern': 'phase6*.py', 'destination': 'scripts/phase6_betting/', 'description': 'Phase 6 scripts'},
        {'pattern': 'web_output*.py', 'destination': 'scripts/phase6_betting/', 'description': 'Web output scripts'},
        {'pattern': '*backtest*.py', 'destination': 'backtest/scripts/', 'description': 'Backtest scripts'},
        {'pattern': 'run_*.py', 'destination': 'scripts/batch/', 'description': 'Batch scripts'},
        {'pattern': 'run_*.bat', 'destination': 'scripts/batch/', 'description': 'Batch files'},
    ])
    
    # 結果ファイル
    move_rules.extend([
        {'pattern': '*backtest*.json', 'destination': 'backtest/results/2025/', 'description': 'Backtest results'},
    ])
    
    # ファイル移動
    moved_count = 0
    skipped_count = 0
    
    for rule in move_rules:
        pattern = rule['pattern']
        destination = rule['destination']
        description = rule['description']
        
        # パターンに一致するファイルを検索
        matching_files = list(root.glob(pattern))
        
        for file_path in matching_files:
            if file_path.is_file():
                dest_path = root / destination / file_path.name
                
                # 既に移動先に同名ファイルが存在するかチェック
                if dest_path.exists():
                    print("[SKIP] {} (already exists in destination)".format(file_path.name))
                    skipped_count += 1
                    continue
                
                if dry_run:
                    print("[DRY RUN] {} -> {}".format(file_path.name, destination))
                else:
                    # 実際に移動
                    shutil.move(str(file_path), str(dest_path))
                    print("[MOVE] {} -> {}".format(file_path.name, destination))
                
                moved_count += 1
    
    print("")
    print("="*80)
    print("[SUMMARY]")
    print("="*80)
    if dry_run:
        print("  Files to move: {}".format(moved_count))
    else:
        print("  Files moved: {}".format(moved_count))
    print("  Files skipped: {}".format(skipped_count))
    
    return moved_count

def create_readme_files(root_path):
    """各フォルダにREADME.mdを作成"""
    
    root = Path(root_path)
    
    print("")
    print("="*80)
    print("[CREATE README FILES]")
    print("="*80)
    
    readme_contents = {
        'models/binary/README.md': """# Binary Classification Models

Phase 3の二値分類モデル（入線予測）

## ファイル命名規則
`{keibajo}_{year_range}_v3_model.txt`

例: `ooi_2023-2025_v3_model.txt`

## 使用方法
```python
import lightgbm as lgb
model = lgb.Booster(model_file='ooi_2023-2025_v3_model.txt')
predictions = model.predict(X_test)
```
""",
        
        'models/ranking/README.md': """# Ranking Models

Phase 4のランキング予測モデル

## ファイル命名規則
`{keibajo}_{year_range}_v3_with_race_id_ranking_model.txt`

例: `ooi_2023-2025_v3_with_race_id_ranking_model.txt`
""",
        
        'models/regression/README.md': """# Regression Models

Phase 4の回帰予測モデル（走破時間予測）

## ファイル命名規則
`{keibajo}_{year_range}_v3_time_regression_model.txt`

例: `ooi_2023-2025_v3_time_regression_model.txt`
""",
        
        'scripts/README.md': """# Scripts

競馬AI予測システムの実行スクリプト

## フォルダ構成
- `phase0_data_acquisition/`: データ取得
- `phase1_feature_engineering/`: 特徴量作成
- `phase3_binary/`: 二値分類予測
- `phase4_ranking/`: ランキング予測
- `phase4_regression/`: 回帰予測
- `phase5_ensemble/`: アンサンブル統合
- `phase6_betting/`: 購入推奨生成
- `utils/`: ユーティリティ
- `batch/`: バッチ実行

## クイックスタート
```bash
cd scripts/batch/
run_all.bat
```
""",
        
        'data/README.md': """# Data

## フォルダ構成
- `raw/`: PC-KEIBAから取得した生データ
- `features/`: 特徴量変換後のデータ
- `predictions/`: Phase 3-5の予測結果
- `payouts/`: 払戻金データ（バックテスト用）

## データフロー
raw → features → predictions (phase3/4/5)
"""
    }
    
    created_count = 0
    
    for readme_path, content in readme_contents.items():
        full_path = root / readme_path
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("[CREATE] {}".format(readme_path))
            created_count += 1
        else:
            print("[EXISTS] {}".format(readme_path))
    
    print("")
    print("Created {} README files".format(created_count))

if __name__ == "__main__":
    import sys
    
    root_path = "E:/anonymous-keiba-ai/"
    
    # コマンドライン引数チェック
    execute_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        execute_mode = True
    
    # ディレクトリが存在するか確認
    if not os.path.exists(root_path):
        print("[ERROR] Path not found: {}".format(root_path))
        print("Please check the path")
    else:
        print("="*80)
        print("FOLDER STRUCTURE CREATION SCRIPT")
        print("="*80)
        if execute_mode:
            print("[MODE] EXECUTE - Files will be ACTUALLY moved")
        else:
            print("[MODE] DRY RUN - No files will be moved")
        print("")
        
        # Step 1: フォルダ構造作成
        print("STEP 1: Creating folder structure...")
        create_folder_structure(root_path)
        
        # Step 2: ファイル移動
        if execute_mode:
            print("\nSTEP 2: File organization (EXECUTE MODE)...")
            print("WARNING: Files will be ACTUALLY moved!")
            print("Press Ctrl+C to cancel within 5 seconds...")
            import time
            for i in range(5, 0, -1):
                print("{}...".format(i))
                time.sleep(1)
            print("Starting file move...")
            move_existing_files(root_path, dry_run=False)
        else:
            print("\nSTEP 2: File organization (DRY RUN)...")
            move_existing_files(root_path, dry_run=True)
        
        # Step 3: README作成
        print("\nSTEP 3: Creating README files...")
        create_readme_files(root_path)
        
        print("")
        print("="*80)
        print("[COMPLETED]")
        print("="*80)
        print("")
        if not execute_mode:
            print("NEXT STEPS:")
            print("1. Review the DRY RUN results above")
            print("2. If everything looks good, run with --execute:")
            print("   python create_folder_structure.py --execute")
        else:
            print("Files have been organized!")
            print("Run check_current_status.py to verify the new structure.")
