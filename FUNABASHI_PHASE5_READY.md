# 🎉 船橋 Phase 5 Ensemble 実行可能確認レポート

**確認日**: 2026-02-11  
**対象**: 船橋（Funabashi）Phase 5 Ensemble アンサンブル統合

---

## ✅ **全ファイル確認完了！**

### **Phase 5 スクリプト ✅**
- ✅ `ensemble_optimized.py` (20.4KB)
  - Phase 7 (Boruta特徴選択) + Phase 8 (Optuna最適化) 結果を統合
  - 3モデル統合: Binary (30%) + Ranking (50%) + Regression (20%)

### **Phase 8 Binary モデル ✅**
- ✅ `funabashi_best_params.csv` (214 bytes)
  ```
  learning_rate: 0.0247
  num_leaves: 66
  max_depth: 12
  min_child_samples: 89
  subsample: 0.671
  colsample_bytree: 0.646
  ```
- ✅ `funabashi_tuned_model.txt` (7.3MB) - LightGBM Binary モデル

### **Phase 8 Ranking モデル ✅**
- ✅ `funabashi_ranking_best_params.csv` (212 bytes)
  ```
  learning_rate: 0.0398
  num_leaves: 167
  max_depth: 6
  min_child_samples: 47
  subsample: 0.710
  colsample_bytree: 0.531
  ```
- ✅ `funabashi_ranking_tuned_model.txt` (2.1MB) - LightGBM Ranking モデル

### **Phase 8 Regression モデル ✅**
- ✅ `funabashi_regression_best_params.csv` (209 bytes)
  ```
  learning_rate: 0.0513
  num_leaves: 97
  max_depth: 15
  min_child_samples: 53
  subsample: 0.538
  colsample_bytree: 0.958
  ```
- ✅ `funabashi_regression_tuned_model.txt` (2.4MB) - LightGBM Regression モデル

---

## 🚀 **Phase 5 Ensemble 実行準備完了**

### **必要なもの**

#### ✅ **揃っているもの**
1. Phase 5 スクリプト: `ensemble_optimized.py`
2. Binary モデル: `funabashi_best_params.csv` + `funabashi_tuned_model.txt`
3. Ranking モデル: `funabashi_ranking_best_params.csv` + `funabashi_ranking_tuned_model.txt`
4. Regression モデル: `funabashi_regression_best_params.csv` + `funabashi_regression_tuned_model.txt`

#### ⚠️ **不足しているもの**
- テストデータ: `test_data\funabashi_20260212.csv`

---

## 📋 **Phase 5 実行方法**

### **方法1: 過去データでテスト実行（動作確認）**

```bash
cd E:\anonymous-keiba-ai

# 1. テストディレクトリ作成
mkdir test_data

# 2. 学習データの最新部分を抽出してテストデータとして使用
python -c "
import pandas as pd

# 船橋の学習データを読み込み
df = pd.read_csv('data/training/funabashi_2020-2026_with_time_PHASE78.csv', encoding='shift-jis')

# 最新100レコードを抽出
test_data = df.tail(100).copy()

# 目的変数を削除（予測対象なので）
cols_to_drop = ['target', 'binary_target', 'rank_target', 'time']
test_data = test_data.drop(columns=[col for col in cols_to_drop if col in test_data.columns])

# テストデータとして保存
test_data.to_csv('test_data/funabashi_test_sample.csv', index=False, encoding='shift-jis')

print('✅ テストデータ生成完了: test_data/funabashi_test_sample.csv')
print(f'レコード数: {len(test_data)}')
print(f'カラム数: {len(test_data.columns)}')
"

# 3. Phase 5 Ensemble 実行
python scripts\phase5_ensemble\ensemble_optimized.py ^
  funabashi ^
  test_data\funabashi_test_sample.csv ^
  --output-dir data\predictions\phase5_optimized
```

**推定時間**: 5分

---

### **方法2: 明日のレースデータで予測（本番）**

**前提**: 明日（2026-02-12）の船橋レースデータを取得済み

```bash
cd E:\anonymous-keiba-ai

# Phase 5 Ensemble 実行
python scripts\phase5_ensemble\ensemble_optimized.py ^
  funabashi ^
  test_data\funabashi_20260212.csv ^
  --output-dir data\predictions\phase5_optimized
```

**出力**:
- `data\predictions\phase5_optimized\funabashi_20260212_ensemble_optimized.csv`
- `data\predictions\phase5_optimized\funabashi_20260212_ensemble_optimized_summary.json`

---

## 🎯 **予測結果の内容**

### **アンサンブル統合スコア**
各馬に対して以下のスコアを計算:
```
ensemble_score = (Binary × 0.3) + (Ranking × 0.5) + (Regression × 0.2)
```

### **出力カラム**
- `umaban`: 馬番
- `binary_score`: Binary分類スコア（複勝圏内確率）
- `ranking_score`: Ranking予測スコア（相対的強さ）
- `regression_score`: Regression予測スコア（走破タイム予測）
- `ensemble_score`: 統合スコア
- `predicted_rank`: 予測着順

---

## 📝 **今すぐ実行可能なコマンド**

```bash
cd E:\anonymous-keiba-ai

# テストデータ生成 + Phase 5 実行
python -c "import pandas as pd; df = pd.read_csv('data/training/funabashi_2020-2026_with_time_PHASE78.csv', encoding='shift-jis'); test = df.tail(100).drop(columns=[c for c in ['target', 'binary_target', 'rank_target', 'time'] if c in df.columns]); import os; os.makedirs('test_data', exist_ok=True); test.to_csv('test_data/funabashi_test_sample.csv', index=False, encoding='shift-jis'); print('✅ テストデータ生成完了')"

# Phase 5 Ensemble 実行
python scripts\phase5_ensemble\ensemble_optimized.py funabashi test_data\funabashi_test_sample.csv --output-dir data\predictions\phase5_optimized
```

---

## 🔍 **確認すべき追加ファイル**

以下のコマンドで、Phase 7 の選択特徴量ファイルも確認してください:

```bash
cd E:\anonymous-keiba-ai

# Phase 7 Binary 選択特徴量
dir data\features\selected\funabashi_selected_features.csv

# Phase 7 Ranking 選択特徴量
dir data\features\selected\funabashi_ranking_selected_features.csv

# Phase 7 Regression 選択特徴量
dir data\features\selected\funabashi_regression_selected_features.csv
```

これらも必要です。もし無い場合は、スクリプトが全特徴量を使用する可能性があります。

---

## ✅ **結論**

**船橋の Phase 5 Ensemble は実行可能です！**

1. ✅ Phase 5 スクリプト存在
2. ✅ Phase 8 モデル（Binary/Ranking/Regression）全て存在
3. ⚠️ テストデータのみ要生成

**次のアクション**: 上記のテストデータ生成コマンドを実行してください！
