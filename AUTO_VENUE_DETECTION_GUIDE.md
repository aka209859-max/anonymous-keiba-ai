# 🎯 全14競馬場対応・予測スクリプト実行ガイド

**最終更新**: 2026-02-08  
**ブランチ**: `phase0_complete_fix_2026_02_07`  
**コミット**: `3761934`

---

## ✅ 新機能：競馬場自動検出

すべての予測スクリプトが**ファイル名から競馬場を自動検出**し、適切なモデルを選択します。

**対応競馬場（全14場）**:
- 門別(30), 盛岡(35), 水沢(36), 浦和(42), 船橋(43), 大井(44), 川崎(45)
- 金沢(46), 笠松(47), 名古屋(48), 園田(50), 姫路(51), 高知(54), 佐賀(55)

---

## 🚀 実行手順（簡易版）

### Phase 3: 二値分類予測

```bash
python scripts\phase3_binary\predict_phase3_inference.py ^
  data\features\2026\02\佐賀_20260207_features.csv ^
  models\binary ^
  data\predictions\phase3\佐賀_20260207_phase3_binary.csv
```

**変更点**: 
- ❌ 旧: `models\binary\saga_2020-2025_v3_model.txt` （モデルファイルを手動指定）
- ✅ 新: `models\binary` （ディレクトリのみ指定、競馬場は自動検出）

---

### Phase 4-1: ランキング予測

```bash
python scripts\phase4_ranking\predict_phase4_ranking_inference.py ^
  data\features\2026\02\佐賀_20260207_features.csv ^
  models\ranking ^
  data\predictions\phase4_ranking\佐賀_20260207_phase4_ranking.csv
```

---

### Phase 4-2: 回帰予測

```bash
python scripts\phase4_regression\predict_phase4_regression_inference.py ^
  data\features\2026\02\佐賀_20260207_features.csv ^
  models\regression ^
  data\predictions\phase4_regression\佐賀_20260207_phase4_regression.csv
```

---

## 📊 実行例：複数競馬場の一括処理

### 佐賀（2026-02-07）

```bash
# Phase 1: 特徴量作成
python scripts\phase1_feature_engineering\prepare_features.py data\raw\2026\02\佐賀_20260207_raw.csv

# Phase 3-4 予測
python scripts\phase3_binary\predict_phase3_inference.py data\features\2026\02\佐賀_20260207_features.csv models\binary data\predictions\phase3\佐賀_20260207_phase3_binary.csv
python scripts\phase4_ranking\predict_phase4_ranking_inference.py data\features\2026\02\佐賀_20260207_features.csv models\ranking data\predictions\phase4_ranking\佐賀_20260207_phase4_ranking.csv
python scripts\phase4_regression\predict_phase4_regression_inference.py data\features\2026\02\佐賀_20260207_features.csv models\regression data\predictions\phase4_regression\佐賀_20260207_phase4_regression.csv

# Phase 5: アンサンブル
python scripts\phase5_ensemble\ensemble_predictions.py ^
  data\predictions\phase3\佐賀_20260207_phase3_binary.csv ^
  data\predictions\phase4_ranking\佐賀_20260207_phase4_ranking.csv ^
  data\predictions\phase4_regression\佐賀_20260207_phase4_regression.csv ^
  data\predictions\phase5\佐賀_20260207_ensemble.csv

# Phase 6: 配信用テキスト生成
python scripts\phase6_betting\generate_distribution.py ^
  data\predictions\phase5\佐賀_20260207_ensemble.csv ^
  predictions\佐賀_20260207_配信用.txt
```

---

### 川崎（2026-02-05）

```bash
# Phase 0: データ取得
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo 45 --date 20260205

# Phase 1: 特徴量作成
python scripts\phase1_feature_engineering\prepare_features.py data\raw\2026\02\川崎_20260205_raw.csv

# Phase 3-4 予測（自動的に川崎のモデルが選択される）
python scripts\phase3_binary\predict_phase3_inference.py data\features\2026\02\川崎_20260205_features.csv models\binary data\predictions\phase3\川崎_20260205_phase3_binary.csv
python scripts\phase4_ranking\predict_phase4_ranking_inference.py data\features\2026\02\川崎_20260205_features.csv models\ranking data\predictions\phase4_ranking\川崎_20260205_phase4_ranking.csv
python scripts\phase4_regression\predict_phase4_regression_inference.py data\features\2026\02\川崎_20260205_features.csv models\regression data\predictions\phase4_regression\川崎_20260205_phase4_regression.csv
```

---

## 🏗️ ディレクトリ構造

```
E:\anonymous-keiba-ai\
├── scripts\
│   ├── utils\
│   │   ├── __init__.py
│   │   └── keibajo_mapping.py        ← 🆕 競馬場マッピングテーブル
│   ├── phase0_data_acquisition\
│   │   └── extract_race_data.py
│   ├── phase1_feature_engineering\
│   │   └── prepare_features.py
│   ├── phase3_binary\
│   │   └── predict_phase3_inference.py    ← 🔄 自動検出対応
│   ├── phase4_ranking\
│   │   └── predict_phase4_ranking_inference.py    ← 🔄 自動検出対応
│   ├── phase4_regression\
│   │   └── predict_phase4_regression_inference.py ← 🔄 自動検出対応
│   ├── phase5_ensemble\
│   │   └── ensemble_predictions.py
│   └── phase6_betting\
│       └── generate_distribution.py
├── models\
│   ├── binary\
│   │   ├── saga_2020-2025_v3_model.txt
│   │   ├── kawasaki_2020-2025_v3_model.txt
│   │   └── ... (全14競馬場)
│   ├── ranking\
│   │   ├── saga_2020-2025_v3_with_race_id_ranking_model.txt
│   │   └── ... (全14競馬場)
│   └── regression\
│       ├── saga_2020-2025_v3_time_regression_model.txt
│       └── ... (全14競馬場)
├── data\
│   ├── raw\
│   ├── features\
│   └── predictions\
└── predictions\
```

---

## 🔧 技術詳細：自動検出の仕組み

### 1. ファイル名から競馬場名を抽出

```python
# 入力: data\features\2026\02\佐賀_20260207_features.csv
# 出力: '佐賀'

from utils.keibajo_mapping import extract_keibajo_from_filename
keibajo_name = extract_keibajo_from_filename('佐賀_20260207_features.csv')
# → '佐賀'
```

### 2. 競馬場名からモデルファイル名を生成

```python
from utils.keibajo_mapping import get_model_filename

# 二値分類モデル
model_filename = get_model_filename('佐賀', 'binary')
# → 'saga_2020-2025_v3_model.txt'

# ランキングモデル
model_filename = get_model_filename('川崎', 'ranking')
# → 'kawasaki_2020-2025_v3_with_race_id_ranking_model.txt'

# 回帰モデル
model_filename = get_model_filename('大井', 'regression')
# → 'ooi_2023-2025_v3_time_regression_model.txt'
```

### 3. モデルパスの完成

```python
import os

models_dir = 'models/binary'
keibajo_name = '佐賀'
model_filename = get_model_filename(keibajo_name, 'binary')
model_path = os.path.join(models_dir, model_filename)
# → 'models/binary/saga_2020-2025_v3_model.txt'
```

---

## 📋 競馬場コード対応表

| 競馬場 | コード | ローマ字 | 学習期間 |
|--------|--------|----------|----------|
| 門別 | 30 | monbetsu | 2020-2025 |
| 盛岡 | 35 | morioka | 2020-2025 |
| 水沢 | 36 | mizusawa | 2020-2025 |
| 浦和 | 42 | urawa | 2020-2025 |
| 船橋 | 43 | funabashi | 2020-2025 |
| 大井 | 44 | ooi | **2023-2025** |
| 川崎 | 45 | kawasaki | 2020-2025 |
| 金沢 | 46 | kanazawa | 2020-2025 |
| 笠松 | 47 | kasamatsu | 2020-2025 |
| 名古屋 | 48 | nagoya | **2022-2025** |
| 園田 | 50 | sonoda | 2020-2025 |
| 姫路 | 51 | himeji | 2020-2025 |
| 高知 | 54 | kochi | 2020-2025 |
| 佐賀 | 55 | saga | 2020-2025 |

**注意**: 大井と名古屋は学習期間が異なります

---

## ⚠️ エラー対処

### エラー1: モデルファイルが見つかりません

```
FileNotFoundError: モデルファイルが見つかりません: models\binary\saga_2020-2025_v3_model.txt
```

**原因**: モデルファイルが存在しないか、パスが間違っている

**対処**:
```bash
# モデルディレクトリを確認
dir models\binary /b
dir models\ranking /b
dir models\regression /b

# 該当競馬場のモデルが存在するか確認
dir models\binary\*saga*.txt
```

---

### エラー2: 競馬場の自動検出に失敗しました

```
❌ エラー: 競馬場の自動検出に失敗しました
ValueError: ファイル名から競馬場名を抽出できません: test_features.csv
```

**原因**: ファイル名が `{競馬場名}_{日付}_xxx.csv` の形式でない

**対処**: ファイル名を正しい形式に変更
```
❌ test_features.csv
✅ 佐賀_20260207_features.csv
```

---

## 🔄 ローカル環境への反映

```bash
cd E:\anonymous-keiba-ai
git fetch origin
git checkout phase0_complete_fix_2026_02_07
git pull origin phase0_complete_fix_2026_02_07
```

---

## 📊 変更履歴

### コミット: `3761934`
- **タイトル**: `feat(prediction): add auto-venue detection for all 14 racecourses`
- **変更内容**:
  - ✅ `scripts/utils/keibajo_mapping.py` 追加（競馬場マッピングテーブル）
  - ✅ Phase 3 二値分類スクリプトを自動検出対応に更新
  - ✅ Phase 4 ランキングスクリプトを自動検出対応に更新
  - ✅ Phase 4 回帰スクリプトを自動検出対応に更新
  - ✅ 全14競馬場に対応

---

## 🎯 メリット

### ❌ 旧方式（手動指定）

```bash
# 佐賀の場合
python predict_phase3.py data.csv models\binary\saga_2020-2025_v3_model.txt output.csv

# 川崎の場合
python predict_phase3.py data.csv models\binary\kawasaki_2020-2025_v3_model.txt output.csv

# 大井の場合（学習期間が異なる）
python predict_phase3.py data.csv models\binary\ooi_2023-2025_v3_model.txt output.csv
```

**問題点**:
- モデルファイル名を毎回手動で指定
- 学習期間の違いを覚えておく必要がある
- 14競馬場分のコマンドを管理

---

### ✅ 新方式（自動検出）

```bash
# どの競馬場でも同じコマンド
python scripts\phase3_binary\predict_phase3_inference.py ^
  data\features\2026\02\{競馬場}_{日付}_features.csv ^
  models\binary ^
  data\predictions\phase3\{競馬場}_{日付}_phase3_binary.csv
```

**メリット**:
- ファイル名から競馬場を自動検出
- モデルファイル名を自動生成
- 学習期間の違いも自動対応
- **1つのコマンドで全14競馬場に対応**

---

## 📝 まとめ

✅ **全14競馬場対応完了**  
✅ **競馬場自動検出機能実装**  
✅ **コマンド実行が大幅に簡略化**  
✅ **毎日の運用が容易に**

---

**PR #4**: https://github.com/aka209859-max/anonymous-keiba-ai/pull/4

**作成日**: 2026-02-08  
**最終更新**: コミット `3761934`
