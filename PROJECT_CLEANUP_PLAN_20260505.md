# プロジェクト整理計画 2026-05-05

**目的**: Phase 2高性能化（67特徴量版）の実装前に、不要ファイル・旧モデルを整理し、プロジェクトを見通し良くする。

---

## 📊 現状分析

### プロジェクト規模
- **合計ファイル数**: 20,953行（project_analysis_20260505.txt）
- **主要フォルダ**: 14個（docs, venv, models, data, scripts等）
- **ルート直下のファイル**: 約400個（大量のPNG, TXT, CSV, MD, BAT）

### 問題点
1. **ルート直下が散乱**: 学習結果PNG/TXT、旧バッチファイル、旧CSVが混在
2. **旧スクリプトが混在**: Phase 1-12の複数バージョンが並存
3. **旧モデル（34特徴量版）**: 使わないモデルが残存
4. **ドキュメント過多**: 100個以上のMDファイル

---

## 🎯 整理方針

### 1. `old/` フォルダ構造

```
E:\anonymous-keiba-ai\
├── old\
│   ├── models_34features\          # 旧モデル（34特徴量版）
│   │   ├── binary\
│   │   ├── ranking\
│   │   └── regression\
│   ├── scripts\                    # 旧スクリプト
│   │   ├── phase1\                 # prepare_features.py, v2.py
│   │   ├── phase7-8\               # Phase7-8関連
│   │   ├── phase11\                # 三連複実装
│   │   └── phase12\                # 馬単モデル
│   ├── data\                       # 旧データ
│   │   ├── training_csv\           # ルート直下の学習データCSV
│   │   └── features_old\           # 古い特徴量CSV
│   ├── docs_archive\               # 古いドキュメント
│   │   ├── completion_reports\     # 完了報告書
│   │   ├── quickstart_guides\      # クイックスタート
│   │   └── phase_specific\         # Phase別ドキュメント
│   ├── results\                    # 学習結果（PNG/TXT）
│   │   ├── binary_results\         # *_model.png, *_score.txt
│   │   ├── ranking_results\
│   │   └── regression_results\
│   └── batch_scripts\              # 旧バッチファイル
│       ├── run_all_variants\       # run_all_*.bat の大量バリエーション
│       ├── phase7-8\
│       └── phase10-12\
├── models\                         # 新モデル（67特徴量版）
│   ├── binary\
│   ├── ranking\
│   └── regression\
├── scripts\                        # 最新スクリプトのみ
│   ├── phase0_data_acquisition\
│   ├── phase1_feature_engineering\ # prepare_features_v3.py のみ
│   ├── phase3_binary\
│   ├── phase4_ranking\
│   ├── phase4_regression\
│   ├── phase5_ensemble\
│   └── phase6_betting\             # 新規実装予定
├── data\
│   ├── raw\
│   │   ├── 2026\                   # 最新データ
│   │   └── archive\
│   └── features\                   # 67特徴量版のみ
├── docs\                           # 最新ドキュメントのみ
│   ├── PHASE2_HIGHPERFORMANCE_PROGRESS.md
│   ├── ULTIMATE_IMPROVEMENT_PLAN.md
│   └── README.md
└── (必要な最新ファイルのみ)
```

---

## 📋 移動対象リスト

### A. ルート直下のファイル → `old/`

#### 1. 学習結果（PNG/TXT）→ `old/results/`
- `*_2020-2025_v3_model.png` → `old/results/binary_results/`
- `*_2020-2025_v3_score.txt` → `old/results/binary_results/`
- `*_ranking_model.png` → `old/results/ranking_results/`
- `*_ranking_score.txt` → `old/results/ranking_results/`
- `*_time_regression_model.png` → `old/results/regression_results/`
- `*_time_regression_score.txt` → `old/results/regression_results/`
- **対象**: 約140ファイル（14競馬場 × 3モデル × 2ファイル + バリエーション）

#### 2. 学習データCSV → `old/data/training_csv/`
- `*_2020-2025_v3.csv`
- `*_2020-2025_v3_with_race_id.csv`
- `*_2020-2025_v3_time.csv`
- `*_2020-2025_with_time.csv`
- `*_2020-2025_soha_time.csv`
- `training_data_v2.csv`
- `test_data.csv`, `test_data_v2.csv`
- **対象**: 約80ファイル

#### 3. 旧バッチファイル → `old/batch_scripts/`
- `run_all_*.bat`（20個以上のバリエーション）
- `RUN_PHASE7_*.bat`, `RUN_PHASE8_*.bat`, `RUN_PHASE10_*.bat`
- `EXTRACT_ALL_TRAINING_DATA.bat`, `GENERATE_ALL_TRAINING_DATA.bat`
- **対象**: 約40ファイル

#### 4. 古いドキュメント → `old/docs_archive/`
- `PHASE*_COMPLETION_REPORT.md`（30個以上）
- `QUICKSTART*.md`（10個以上）
- `*_GUIDE.md`（20個以上）
- `COMPLETE_*.md`, `FINAL_*.md`, `EXECUTION_*.md`
- **対象**: 約100ファイル

#### 5. その他 → `old/data/` or `old/misc/`
- `*_2025_payouts_official.csv` → `old/data/payouts/`
- `.zip`, `.tar.gz` アーカイブ → `old/archives/`
- 古いPythonスクリプト（ルート直下） → `old/scripts/misc/`

### B. models/ → `old/models_34features/`

#### 旧モデル（34特徴量版）を全移動
```bash
models/binary/*.txt       → old/models_34features/binary/
models/ranking/*.txt      → old/models_34features/ranking/
models/regression/*.txt   → old/models_34features/regression/
```
- **対象**: 約42モデル（14競馬場 × 3モデル）

**理由**: 67特徴量版の新モデルを作成するため、34特徴量版は不要

### C. scripts/ → `old/scripts/`

#### 1. Phase 1旧バージョン → `old/scripts/phase1/`
- `prepare_features.py`（49特徴量版）
- `prepare_features_v2.py`（61特徴量版）
- `prepare_features_safe.py`

**残すもの**: `prepare_features_v3.py`（67特徴量版・最新）

#### 2. Phase7-8 → `old/scripts/phase7-8/`
- `scripts/phase7_binary/`
- `scripts/phase7_feature_selection/`
- `scripts/phase8_auto_tuning/`
- `scripts/phase8_prediction/`
- `scripts/phase8_ranking/`
- `scripts/phase8_regression/`

**理由**: Phase 3-5の推論スクリプトに統合済み

#### 3. Phase11-12 → `old/scripts/phase11-12/`
- `scripts/phase11_triple_umatan/`
- `scripts/phase12_umatan_model/`

**理由**: Phase 6で再実装予定（67特徴量版対応）

### D. docs/ → `old/docs_archive/`

#### 古いドキュメント（100個以上）
- Phase別完了報告書
- クイックスタートガイド
- 実装ガイド

**残すもの**:
- `PHASE2_HIGHPERFORMANCE_PROGRESS.md`（最新進捗）
- `ULTIMATE_IMPROVEMENT_PLAN.md`（最終計画）
- `IMPLEMENTATION_PLAN_20260505.md`（実装計画）
- `README.md`（プロジェクト概要）

---

## 🚀 実行コマンド

### 準備
```cmd
cd E:\anonymous-keiba-ai
mkdir old
mkdir old\models_34features
mkdir old\models_34features\binary
mkdir old\models_34features\ranking
mkdir old\models_34features\regression
mkdir old\scripts
mkdir old\scripts\phase1
mkdir old\scripts\phase7-8
mkdir old\scripts\phase11-12
mkdir old\data
mkdir old\data\training_csv
mkdir old\data\payouts
mkdir old\data\features_old
mkdir old\docs_archive
mkdir old\docs_archive\completion_reports
mkdir old\docs_archive\quickstart_guides
mkdir old\docs_archive\phase_specific
mkdir old\results
mkdir old\results\binary_results
mkdir old\results\ranking_results
mkdir old\results\regression_results
mkdir old\batch_scripts
mkdir old\batch_scripts\run_all_variants
mkdir old\batch_scripts\phase7-8
mkdir old\batch_scripts\phase10-12
mkdir old\archives
mkdir old\misc
```

### A. 学習結果の移動
```cmd
move *_model.png old\results\binary_results\
move *_score.txt old\results\binary_results\
move *_ranking_model.png old\results\ranking_results\
move *_ranking_score.txt old\results\ranking_results\
move *_time_regression_model.png old\results\regression_results\
move *_time_regression_score.txt old\results\regression_results\
```

### B. 学習データCSVの移動
```cmd
move *_2020-2025_v3.csv old\data\training_csv\
move *_2020-2025_v3_with_race_id.csv old\data\training_csv\
move *_2020-2025_v3_time.csv old\data\training_csv\
move *_2020-2025_with_time.csv old\data\training_csv\
move *_2020-2025_soha_time.csv old\data\training_csv\
move training_data_v2.csv old\data\training_csv\
move test_data.csv old\data\training_csv\
move test_data_v2.csv old\data\training_csv\
```

### C. 旧バッチファイルの移動
```cmd
move run_all_*.bat old\batch_scripts\run_all_variants\
move RUN_PHASE7_*.bat old\batch_scripts\phase7-8\
move RUN_PHASE8_*.bat old\batch_scripts\phase7-8\
move RUN_PHASE10_*.bat old\batch_scripts\phase10-12\
move EXTRACT_ALL_TRAINING_DATA.bat old\batch_scripts\
move GENERATE_ALL_TRAINING_DATA.bat old\batch_scripts\
```

### D. payoutsファイルの移動
```cmd
move *_payouts_official.csv old\data\payouts\
move *_payouts.csv old\data\payouts\
```

### E. アーカイブファイルの移動
```cmd
move *.zip old\archives\
move *.tar.gz old\archives\
```

### F. 旧モデルの移動
```cmd
xcopy /s models\binary\*.txt old\models_34features\binary\
xcopy /s models\ranking\*.txt old\models_34features\ranking\
xcopy /s models\regression\*.txt old\models_34features\regression\
rmdir /s /q models\binary
rmdir /s /q models\ranking
rmdir /s /q models\regression
mkdir models\binary
mkdir models\ranking
mkdir models\regression
```

### G. 旧スクリプトの移動
```cmd
move scripts\phase1_feature_engineering\prepare_features.py old\scripts\phase1\
move scripts\phase1_feature_engineering\prepare_features_v2.py old\scripts\phase1\
move scripts\phase1_feature_engineering\prepare_features_safe.py old\scripts\phase1\

xcopy /s /i scripts\phase7_binary old\scripts\phase7-8\phase7_binary
xcopy /s /i scripts\phase7_feature_selection old\scripts\phase7-8\phase7_feature_selection
xcopy /s /i scripts\phase8_auto_tuning old\scripts\phase7-8\phase8_auto_tuning
xcopy /s /i scripts\phase8_prediction old\scripts\phase7-8\phase8_prediction
xcopy /s /i scripts\phase8_ranking old\scripts\phase7-8\phase8_ranking
xcopy /s /i scripts\phase8_regression old\scripts\phase7-8\phase8_regression

xcopy /s /i scripts\phase11_triple_umatan old\scripts\phase11-12\phase11_triple_umatan
xcopy /s /i scripts\phase12_umatan_model old\scripts\phase11-12\phase12_umatan_model

rmdir /s /q scripts\phase7_binary
rmdir /s /q scripts\phase7_feature_selection
rmdir /s /q scripts\phase8_auto_tuning
rmdir /s /q scripts\phase8_prediction
rmdir /s /q scripts\phase8_ranking
rmdir /s /q scripts\phase8_regression
rmdir /s /q scripts\phase11_triple_umatan
rmdir /s /q scripts\phase12_umatan_model
```

### H. 古いドキュメントの移動
```cmd
move *COMPLETION_REPORT*.md old\docs_archive\completion_reports\
move *QUICKSTART*.md old\docs_archive\quickstart_guides\
move *GUIDE*.md old\docs_archive\phase_specific\
move PHASE*_*.md old\docs_archive\phase_specific\
move COMPLETE_*.md old\docs_archive\
move FINAL_*.md old\docs_archive\
move EXECUTION_*.md old\docs_archive\
```

---

## ✅ 残すファイル（最新版のみ）

### ルート直下
- `requirements.txt`
- `.gitignore`
- `README.md`
- `PHASE2_HIGHPERFORMANCE_PROGRESS.md`（進捗レポート）
- `ULTIMATE_IMPROVEMENT_PLAN.md`（最終計画）
- `IMPLEMENTATION_PLAN_20260505.md`（実装計画）
- `project_analysis_20260505.txt`（今回の分析結果）

### scripts/
- `phase0_data_acquisition/`
- `phase1_feature_engineering/prepare_features_v3.py`（67特徴量版のみ）
- `phase3_binary/predict_phase3_inference.py`
- `phase4_ranking/predict_phase4_ranking_inference.py`
- `phase4_regression/predict_phase4_regression_inference.py`
- `phase5_ensemble/ensemble_predictions.py`
- `phase6_betting/`（新規作成予定）
- `utils/`
- `phase9_betting_strategy/`
- `phase10_backtest/`
- `phase10_daily_prediction/`
- `evaluation/`

### models/
- （空フォルダ：67特徴量版の新モデルを作成予定）

### data/
- `raw/2026/`（最新データ）
- `raw/archive/2025/`（大井2025年）
- `features/`（67特徴量版のみ）

### docs/
- （最新ドキュメントのみ）

---

## ⚠️ 注意事項

1. **バックアップ**: 実行前に`E:\anonymous-keiba-ai`全体をバックアップ
2. **段階実行**: セクションごとに実行し、都度確認
3. **コミット**: 整理完了後にGitコミット
4. **old/フォルダ**: 必要に応じて後日削除可能（当面は保持）

---

## 📊 期待効果

### 削減見込み
- **ルート直下のファイル**: 約400個 → 約10個（-97.5%）
- **models/**: 42モデル → 0モデル（新モデル作成前）
- **scripts/**: 14フォルダ → 9フォルダ（-36%）
- **docs/**: 100個以上 → 5個程度（-95%）

### メリット
- ✅ プロジェクト全体が見通しやすくなる
- ✅ 最新ファイルがすぐ見つかる
- ✅ 67特徴量版の実装に集中できる
- ✅ 誤って旧スクリプトを実行するリスク減

---

**次のステップ**: この計画を確認後、実行コマンドをバッチファイル化して実行します。

**作成日**: 2026-05-05
