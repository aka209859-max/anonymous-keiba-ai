# 📊 Phase 0-5 作成経緯と *_with_time.csv の真相

## 🔍 調査結果サマリー

**調査日時**: 2026-02-11  
**調査対象**: GitHub コミット履歴 + サンドボックス内スクリプト  
**調査目的**: `*_with_time.csv` の作成方法を特定し、Phase 7/8 に必要なターゲット変数の不足を解決

---

## ✅ 重要な発見

### 1. Phase 2 の真実

**発見**: `scripts/phase2_target_creation/` ディレクトリは**存在しない**

**実際の構造**:
```
Phase 0: データ収集 (extract_race_data.py)
  ↓
Phase 1: 特徴量生成 (prepare_features.py)
  ↓
【Phase 2は独立していない】
  ↓
Phase 3: Binary予測
Phase 4: Ranking/Regression予測
Phase 5: アンサンブル統合
```

---

### 2. `*_with_time.csv` の作成元

**スクリプト**: `extract_training_data_v2.py`

**GitHubコミット**: 
```
commit 9cf4fb0c52c173ee9fde7b4f89689f5b7b748987
Date:   Tue Feb 3 17:39:25 2026 +0000

feat(phase2.5): 過去走データ統合版の抽出スクリプトを実装
```

**機能**:
- PC-KEIBAデータベース (PostgreSQL) から直接抽出
- `nvd_ra` (レーステーブル) + `nvd_se` (出走馬テーブル) を結合
- ROW_NUMBER() で過去5走データを取得
- 50特徴量 + ターゲット変数を生成

---

### 3. 元の出力カラム構成 (修正前)

```python
Columns (50個):
  1. target              # Binary分類用 (3着以内=1)
  2-50. 特徴量           # 49個の特徴量
```

**問題点**:
- ✅ `target` (Binary用) は存在
- ❌ `rank_target` (Ranking用) **が存在しない**
- ❌ `time` (Regression用) **が存在しない**

**SQL内には存在していたデータ**:
- `tr.kakutei_chakujun` (着順) → 出力されていなかった
- `tr.soha_time` (走破タイム) → 取得すらされていなかった

---

## 🔧 実施した修正内容

### コミット情報

**ブランチ**: `phase0_complete_fix_2026_02_07`  
**コミットハッシュ**: `74881e5`  
**コミットメッセージ**: `fix(phase2): add rank_target and time columns for Phase 7/8 Ranking/Regression training`

### 修正内容の詳細

#### 修正1: target_race CTE に soha_time を追加

```sql
-- Before
SELECT 
    se.kakutei_chakujun,
    ...

-- After
SELECT 
    se.kakutei_chakujun,
    se.soha_time,  -- 追加: Regression学習用の走破タイム
    ...
```

#### 修正2: SELECT句に2つの新しいターゲット変数を追加

```sql
-- Binary target (既存)
CASE 
    WHEN tr.kakutei_chakujun ~ '^[0-9]+$' AND tr.kakutei_chakujun::INTEGER <= 3 THEN 1
    ELSE 0
END AS target,

-- Ranking target (新規) ← NEW!
CASE 
    WHEN tr.kakutei_chakujun ~ '^[0-9]+$' THEN tr.kakutei_chakujun::INTEGER
    ELSE NULL
END AS rank_target,

-- Regression target (新規) ← NEW!
CASE 
    WHEN tr.soha_time ~ '^[0-9.]+$' THEN tr.soha_time::NUMERIC
    ELSE NULL
END AS time,
```

#### 修正3: GROUP BY句に soha_time を追加

```sql
GROUP BY 
    tr.kaisai_nen,
    ...
    tr.kakutei_chakujun,
    tr.soha_time,  -- 追加
    ...
```

---

## 📊 修正後の出力構成

```python
Columns (52個):
  1. target         # Binary分類用 (3着以内=1, 圏外=0)
  2. rank_target    # Ranking学習用 (着順 1〜N) ← NEW!
  3. time           # Regression学習用 (走破タイム 秒単位) ← NEW!
  4-52. 特徴量      # 50個の特徴量 (kaisai_nen, kyori, prev1_rank, ...)
```

---

## 🏗️ Phase 0-5 の正確なフロー

### Phase 0: データ収集
- **スクリプト**: `scripts/phase0_data_acquisition/extract_race_data.py`
- **データソース**: PC-KEIBAデータベース (PostgreSQL)
- **出力**: `data/raw/YYYY/MM/{keibajo}_{YYYYMMDD}_raw.csv`

### Phase 1: 特徴量エンジニアリング
- **スクリプト**: `scripts/phase1_feature_engineering/prepare_features.py`
- **処理内容**: 
  - Rawデータから50特徴量を生成
  - 過去走データの集約
  - 欠損値処理
- **出力**: `data/features/YYYY/MM/{keibajo}_{YYYYMMDD}_features.csv`

### Phase 2 (実体): extract_training_data_v2.py
- **実態**: Phase 0 と Phase 1 を統合したスクリプト
- **処理内容**:
  - PostgreSQL から直接データ抽出
  - 特徴量生成とターゲット変数作成を一括実行
  - 過去5走データを ROW_NUMBER() で取得
- **出力**: `{keibajo}_2020-2025_with_time.csv` (学習用データ)

### Phase 3: Binary分類モデル
- **スクリプト**: `scripts/phase3_binary/predict_phase3_binary_inference.py`
- **モデル**: LightGBM Binary Classification
- **ターゲット**: `target` (3着以内=1)
- **出力**: `data/predictions/phase3/{keibajo}_{YYYYMMDD}_phase3_binary.csv`

### Phase 4: Ranking & Regression モデル
- **スクリプト**:
  - Ranking: `scripts/phase4_ranking/predict_phase4_ranking_inference.py`
  - Regression: `scripts/phase4_regression/predict_phase4_regression_inference.py`
- **モデル**: 
  - Ranking: LightGBM LambdaRank
  - Regression: LightGBM Regression
- **出力**:
  - Ranking: `data/predictions/phase4_ranking/{keibajo}_{YYYYMMDD}_phase4_ranking.csv`
  - Regression: `data/predictions/phase4_regression/{keibajo}_{YYYYMMDD}_phase4_regression.csv`

### Phase 5: アンサンブル統合
- **スクリプト**: `scripts/phase5_ensemble/ensemble_predictions.py`
- **処理内容**:
  - Binary (30%) + Ranking (50%) + Regression (20%)
  - レースごとのZ-Score正規化
  - S/A/B/C/Dランク分類
- **出力**: `data/predictions/phase5/{keibajo}_{YYYYMMDD}_ensemble.csv`

---

## 🔄 Phase 7/8/5 の追加フロー

### Phase 7: Boruta特徴量選択
- **目的**: Binary/Ranking/Regressionごとに最適特徴量を選定
- **必要データ**: `{keibajo}_2020-2025_with_time.csv` (52カラム版)
- **出力**:
  - Binary: `data/features/selected/{keibajo}_selected_features.csv`
  - Ranking: `data/features/selected/{keibajo}_ranking_selected_features.csv`
  - Regression: `data/features/selected/{keibajo}_regression_selected_features.csv`

### Phase 8: Optuna最適化
- **目的**: Binary/Ranking/Regressionごとにハイパーパラメータ最適化
- **入力**: Phase 7 で選択された特徴量リスト
- **出力**:
  - Binary: `data/models/tuned/{keibajo}_tuned_model.txt`
  - Ranking: `data/models/tuned/{keibajo}_ranking_tuned_model.txt`
  - Regression: `data/models/tuned/{keibajo}_regression_tuned_model.txt`

### Phase 5拡張: 最適化アンサンブル
- **スクリプト**: `scripts/phase5_ensemble/ensemble_optimized.py`
- **処理内容**: Phase 7/8 最適化モデルを使用してアンサンブル
- **出力**: `data/predictions/phase5_optimized/{keibajo}_{YYYYMMDD}_ensemble_optimized.csv`

---

## 📁 データファイルの位置関係

```
E:\anonymous-keiba-ai\
├── extract_training_data_v2.py  ← 学習データ作成スクリプト (修正済み)
├── data\
│   ├── training\               ← 学習用データ (Phase 2出力)
│   │   ├── funabashi_2020-2025_with_time.csv  (52カラム)
│   │   ├── kawasaki_2020-2025_with_time.csv
│   │   └── ...  (14会場分)
│   │
│   ├── features\               ← Phase 1出力 (日次予測用)
│   │   └── selected\           ← Phase 7出力 (Boruta選択特徴量)
│   │
│   ├── models\
│   │   ├── tuned\              ← Phase 8出力 (最適化モデル)
│   │   ├── binary\
│   │   ├── ranking\
│   │   └── regression\
│   │
│   └── predictions\            ← Phase 3/4/5出力
│       ├── phase3\
│       ├── phase4_ranking\
│       ├── phase4_regression\
│       ├── phase5\
│       └── phase5_optimized\   ← Phase 5拡張出力
```

---

## 🎯 次のアクション (船橋テスト)

### ステップ1: 学習データ再生成
```bash
cd E:\anonymous-keiba-ai

# 修正版スクリプトをダウンロード
# URL: https://github.com/aka209859-max/anonymous-keiba-ai/raw/phase0_complete_fix_2026_02_07/extract_training_data_v2.py

# 船橋データ再生成 (競馬場コード: 43)
python extract_training_data_v2.py \
  --keibajo 43 \
  --start-date 2020 \
  --end-date 2025 \
  --output data\training\funabashi_2020-2025_with_time.csv
```

### ステップ2: データ確認
```bash
# カラム数確認 (52個であることを確認)
python -c "import pandas as pd; df = pd.read_csv('data/training/funabashi_2020-2025_with_time.csv', encoding='shift-jis', nrows=1); print('Total columns:', len(df.columns)); print('Has rank_target:', 'rank_target' in df.columns); print('Has time:', 'time' in df.columns)"
```

**期待される出力**:
```
Total columns: 52
Has rank_target: True
Has time: True
```

### ステップ3: Phase 7 Ranking テスト
```bash
python scripts\phase7_feature_selection\run_boruta_ranking.py \
  data\training\funabashi_2020-2025_with_time.csv \
  --max-iter 100
```

**期待される成功メッセージ**:
```
✅ ターゲット変数検出: rank_target
✅ 特徴量選択完了: 15/50個選択
✅ 出力: data/features/selected/funabashi_ranking_selected_features.csv
```

---

## 📚 関連リンク

- **修正済みスクリプト**: [extract_training_data_v2.py](https://github.com/aka209859-max/anonymous-keiba-ai/blob/phase0_complete_fix_2026_02_07/extract_training_data_v2.py)
- **コミット履歴**: [74881e5](https://github.com/aka209859-max/anonymous-keiba-ai/commit/74881e5)
- **再生成ガイド**: [TRAINING_DATA_REGENERATION_GUIDE.md](./TRAINING_DATA_REGENERATION_GUIDE.md)

---

**作成日**: 2026-02-11  
**調査者**: AI開発アシスタント  
**ステータス**: ✅ 完了
