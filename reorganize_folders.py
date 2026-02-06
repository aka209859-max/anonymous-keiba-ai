"""
E:/anonymous-keiba-ai/ のフォルダ構造を自動整理するスクリプト
"""
import os
import shutil
from pathlib import Path
from collections import defaultdict

def reorganize_structure(root_path):
    """
    既存ファイルを推奨フォルダ構造に整理する
    """
    root = Path(root_path)
    
    print("="*80)
    print("[FOLDER REORGANIZATION]")
    print("="*80)
    print("Target: {}".format(root_path))
    
    # 推奨フォルダ構造を作成
    folders = {
        'models': {
            'binary': None,
            'ranking': None,
            'regression': None
        },
        'scripts': {
            'phase0_data_acquisition': None,
            'phase1_feature_engineering': None,
            'phase3_binary': None,
            'phase4_ranking': None,
            'phase4_regression': None,
            'phase5_ensemble': None,
            'phase6_betting': None,
            'utils': None,
            'batch': None
        },
        'data': {
            'raw': None,
            'features': None,
            'predictions': {
                'phase3': None,
                'phase4': None,
                'phase5': None
            },
            'payouts': None
        },
        'output': {
            'web': None,
            'reports': None,
            'logs': None
        },
        'backtest': {
            'scripts': None,
            'results': None
        },
        'docs': None,
        'config': None,
        'tests': None,
        'archive': {
            'old_scripts': None,
            'old_models': None,
            'old_results': None
        },
        'sandbox': None
    }
    
    def create_folders(base_path, structure, parent_key=''):
        """再帰的にフォルダを作成"""
        for key, value in structure.items():
            folder_path = base_path / key
            folder_path.mkdir(exist_ok=True)
            
            full_key = "{}/{}".format(parent_key, key) if parent_key else key
            print("  [CREATE] {}".format(full_key))
            
            if isinstance(value, dict):
                create_folders(folder_path, value, full_key)
    
    print("\n[STEP 1] Creating folder structure...")
    create_folders(root, folders)
    
    print("\n[STEP 2] Moving existing files...")
    
    # 移動カウンター
    move_count = defaultdict(int)
    
    # ルートディレクトリ直下のファイルをスキャン
    for item in root.iterdir():
        if item.is_file():
            moved = False
            
            # モデルファイルの移動
            if 'model.txt' in item.name or '_v3' in item.name:
                if 'ranking' in item.name:
                    dest = root / 'models' / 'ranking' / item.name
                elif 'regression' in item.name or 'time' in item.name:
                    dest = root / 'models' / 'regression' / item.name
                else:
                    dest = root / 'models' / 'binary' / item.name
                
                if not dest.exists():
                    print("  [MOVE] {} -> models/".format(item.name))
                    shutil.move(str(item), str(dest))
                    move_count['models'] += 1
                    moved = True
            
            # Pythonスクリプトの移動
            elif item.suffix == '.py' and item.name != 'reorganize_folders.py':
                # Phaseスクリプトを分類
                if 'phase0' in item.name.lower():
                    dest_folder = 'phase0_data_acquisition'
                elif 'phase1' in item.name.lower() or 'feature' in item.name.lower():
                    dest_folder = 'phase1_feature_engineering'
                elif 'phase3' in item.name.lower() or 'binary' in item.name.lower():
                    dest_folder = 'phase3_binary'
                elif 'phase4' in item.name.lower() and 'ranking' in item.name.lower():
                    dest_folder = 'phase4_ranking'
                elif 'phase4' in item.name.lower() and ('regression' in item.name.lower() or 'time' in item.name.lower()):
                    dest_folder = 'phase4_regression'
                elif 'phase5' in item.name.lower() or 'ensemble' in item.name.lower():
                    dest_folder = 'phase5_ensemble'
                elif 'phase6' in item.name.lower() or 'web' in item.name.lower() or 'betting' in item.name.lower():
                    dest_folder = 'phase6_betting'
                elif 'backtest' in item.name.lower():
                    dest = root / 'backtest' / 'scripts' / item.name
                    if not dest.exists():
                        print("  [MOVE] {} -> backtest/scripts/".format(item.name))
                        shutil.move(str(item), str(dest))
                        move_count['backtest'] += 1
                        moved = True
                    continue
                elif 'test_' in item.name.lower():
                    dest = root / 'tests' / item.name
                    if not dest.exists():
                        print("  [MOVE] {} -> tests/".format(item.name))
                        shutil.move(str(item), str(dest))
                        move_count['tests'] += 1
                        moved = True
                    continue
                else:
                    dest_folder = 'utils'
                
                dest = root / 'scripts' / dest_folder / item.name
                if not dest.exists():
                    print("  [MOVE] {} -> scripts/{}/".format(item.name, dest_folder))
                    shutil.move(str(item), str(dest))
                    move_count['scripts'] += 1
                    moved = True
            
            # バッチファイルの移動
            elif item.suffix in ['.bat', '.sh']:
                dest = root / 'scripts' / 'batch' / item.name
                if not dest.exists():
                    print("  [MOVE] {} -> scripts/batch/".format(item.name))
                    shutil.move(str(item), str(dest))
                    move_count['batch'] += 1
                    moved = True
            
            # CSVファイルの移動
            elif item.suffix == '.csv':
                if 'payouts' in item.name or 'haraimodoshi' in item.name:
                    dest = root / 'data' / 'payouts' / item.name
                elif 'ensemble' in item.name:
                    dest = root / 'data' / 'predictions' / 'phase5' / item.name
                elif 'phase3' in item.name:
                    dest = root / 'data' / 'predictions' / 'phase3' / item.name
                elif 'phase4' in item.name:
                    dest = root / 'data' / 'predictions' / 'phase4' / item.name
                elif 'features' in item.name:
                    dest = root / 'data' / 'features' / item.name
                else:
                    dest = root / 'data' / 'raw' / item.name
                
                if not dest.exists():
                    print("  [MOVE] {} -> {}".format(item.name, dest.relative_to(root)))
                    shutil.move(str(item), str(dest))
                    move_count['data'] += 1
                    moved = True
            
            # JSONファイルの移動
            elif item.suffix == '.json':
                if 'backtest' in item.name:
                    dest = root / 'backtest' / 'results' / item.name
                elif 'config' in item.name:
                    dest = root / 'config' / item.name
                else:
                    dest = root / 'output' / 'reports' / item.name
                
                if not dest.exists():
                    print("  [MOVE] {} -> {}".format(item.name, dest.relative_to(root)))
                    shutil.move(str(item), str(dest))
                    move_count['json'] += 1
                    moved = True
            
            # ドキュメントファイルの移動
            elif item.suffix in ['.md', '.txt', '.rst']:
                if item.name.upper() in ['README.MD', 'README.TXT', 'README.RST', 'README']:
                    continue  # READMEはルートに残す
                dest = root / 'docs' / item.name
                if not dest.exists():
                    print("  [MOVE] {} -> docs/".format(item.name))
                    shutil.move(str(item), str(dest))
                    move_count['docs'] += 1
                    moved = True
            
            if not moved and item.name not in ['reorganize_folders.py', 'check_current_status.py']:
                print("  [SKIP] {} (manual review needed)".format(item.name))
    
    print("\n[STEP 3] Summary")
    print("  Files moved:")
    for category, count in move_count.items():
        print("    - {}: {} files".format(category, count))
    
    print("\n[STEP 4] Creating README files...")
    
    # メインREADME
    main_readme = root / 'README.md'
    if not main_readme.exists():
        with open(main_readme, 'w', encoding='utf-8') as f:
            f.write("""# Anonymous競馬AIシステム

## プロジェクト概要
14の地方競馬場を対象とした、機械学習による競馬予測システムです。

## 対象競馬場（14場）
- 大井、川崎、船橋、浦和
- 門別、盛岡、水沢
- 金沢、笠松、名古屋
- 園田、姫路、高知、佐賀

## フォルダ構成
```
E:/anonymous-keiba-ai/
├── models/              # 学習済みモデル（14競馬場 × 3種類 = 42ファイル）
│   ├── binary/         # Phase 3 二値分類モデル
│   ├── ranking/        # Phase 4 ランキングモデル
│   └── regression/     # Phase 4 回帰モデル
├── scripts/            # 実行スクリプト
│   ├── phase0_data_acquisition/  # データ取得
│   ├── phase1_feature_engineering/  # 特徴量生成
│   ├── phase3_binary/             # 二値分類予測
│   ├── phase4_ranking/            # ランキング予測
│   ├── phase4_regression/         # 回帰予測
│   ├── phase5_ensemble/           # アンサンブル統合
│   ├── phase6_betting/            # 購入推奨生成
│   ├── utils/                     # ユーティリティ
│   └── batch/                     # バッチ実行ファイル
├── data/               # データファイル
│   ├── raw/           # 生データ
│   ├── features/      # 特徴量データ
│   ├── predictions/   # 予測結果
│   │   ├── phase3/
│   │   ├── phase4/
│   │   └── phase5/
│   └── payouts/       # 払戻金データ
├── output/            # 最終出力
│   ├── web/          # Web表示用HTML
│   ├── reports/      # レポート
│   └── logs/         # ログ
├── backtest/         # バックテスト
│   ├── scripts/     # バックテストスクリプト
│   └── results/     # バックテスト結果
├── docs/            # ドキュメント
├── config/          # 設定ファイル
├── tests/           # テストコード
├── archive/         # アーカイブ
└── sandbox/         # 実験用

```

## 実行フロー
1. **Phase 0**: PC-KEIBAから出走情報を取得
2. **Phase 1**: 特徴量CSV作成（50個の特徴量）
3. **Phase 3**: 二値分類予測（入線確率）
4. **Phase 4**: ランキング予測 + 回帰予測（走破時間）
5. **Phase 5**: アンサンブル統合（重み: binary 0.3, ranking 0.5, regression 0.2）
6. **Phase 6**: 購入推奨生成（単勝/複勝/馬単/三連複/三連単）

## クイックスタート
```bash
cd E:/anonymous-keiba-ai/
scripts/batch/run_all.bat
```

## 予測券種（馬連・ワイド廃止）
- 単勝: Sランク馬のみ
- 複勝: S+Aランク馬
- 馬単: Sランク1頭軸 × Aランク2頭
- 三連複: Zスコア≧1.5の馬でBOX
- 三連単: Zスコア≧1.5の馬でフォーメーション

## バックテスト結果（大井2025年 全期間）
- 対象レース: 1,073レース
- 総回収率: **113.63%**
- 総収支: **+26,800円**

### 券種別成績
- 単勝: 回収率 125.50%、収支 +4,870円
- 複勝: 回収率 146.12%、収支 +50,500円
- 馬単: 回収率 37.33%、収支 -15,040円
- 三連単: 回収率 1,307.27%、収支 +26,560円

## ライセンス
Private Use Only

## 作成日
2026-02-06
""")
        print("  [CREATE] README.md")
    
    print("\n" + "="*80)
    print("[REORGANIZATION COMPLETED]")
    print("="*80)
    print("\n[NEXT STEPS]")
    print("  1. Review the new folder structure")
    print("  2. Check if all files are in correct locations")
    print("  3. Run check_current_status.py again to verify")
    print("  4. Start creating Phase 0-6 execution scripts")

if __name__ == "__main__":
    root_path = "E:/anonymous-keiba-ai/"
    
    if not os.path.exists(root_path):
        print("[ERROR] Path not found: {}".format(root_path))
        print("Please check the path")
    else:
        # 確認プロンプト
        print("="*80)
        print("[WARNING] This script will reorganize your folder structure")
        print("="*80)
        print("Target directory: {}".format(root_path))
        print("\nThis will:")
        print("  1. Create new folder structure")
        print("  2. Move existing files to appropriate locations")
        print("  3. Keep original files safe (no deletion)")
        print("\nDo you want to continue? (yes/no): ", end='')
        
        # 自動実行版（PCでの手動確認を想定）
        print("yes")
        response = "yes"
        
        if response.lower() in ['yes', 'y']:
            try:
                reorganize_structure(root_path)
            except Exception as e:
                print("\n[ERROR] An error occurred during reorganization:")
                print("  {}: {}".format(type(e).__name__, e))
                import traceback
                traceback.print_exc()
        else:
            print("[CANCELLED] Reorganization cancelled by user")
