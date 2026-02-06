# Phase 3: 二値分類予測 ディープサーチ指示文

## 目的
Phase 1で作成した特徴量CSVを使用して、学習済みモデルで入線予測（3着以内に入る確率）を実行する正しい手順を確認する。

## 前提条件
- Phase 1で作成した特徴量CSV: `data/features/2026/02/ooi_20260207_features.csv`
- 学習済みモデル: `models/binary/ooi_2023-2025_v3_model.txt`

## 検証項目

### 1. モデルの特徴量リスト取得
**学習済みモデルが期待する特徴量を確認:**

```python
import lightgbm as lgb

model_path = 'E:/anonymous-keiba-ai/models/binary/ooi_2023-2025_v3_model.txt'
model = lgb.Booster(model_file=model_path)
model_features = model.feature_name()

print(f"モデルが期待する特徴量: {len(model_features)}個")
print(model_features)
```

**検証すべき点:**
- モデルの特徴量数は何個か？
- 特徴量の順序は重要か？
- 14競馬場すべてで特徴量リストは同じか？

### 2. テストデータの読み込みと前処理
**Phase 1の出力CSVを読み込み:**

```python
import pandas as pd

# テストデータ読み込み（エンコーディング注意）
test_df = pd.read_csv('data/features/2026/02/ooi_20260207_features.csv', 
                      encoding='shift_jis')

print(f"テストデータ件数: {len(test_df)}")
print(f"カラム数: {len(test_df.columns)}")
print(test_df.columns.tolist())
```

**検証すべき点:**
- エンコーディングは `shift_jis` か `utf-8` か？
- カラム名はモデルの特徴量名と完全一致しているか？
- 欠損値がある場合の処理方法は？

### 3. 特徴量の整列と補完
**モデルが期待する特徴量に合わせる:**

```python
# モデル特徴量に存在しないカラムがテストデータにある場合
extra_cols = set(test_df.columns) - set(model_features)
print(f"余分なカラム: {extra_cols}")

# モデル特徴量に存在するがテストデータにないカラム
missing_cols = set(model_features) - set(test_df.columns)
print(f"欠損カラム: {missing_cols}")

# 欠損カラムを0で補完
for col in missing_cols:
    test_df[col] = 0

# モデル特徴量の順序で並べ替え
X_test = test_df[model_features]

# 欠損値を平均値で補完（または0埋め）
X_test = X_test.fillna(X_test.mean())
# または
# X_test = X_test.fillna(0)
```

**検証すべき点:**
- 欠損カラムは0埋めか、平均値補完か？
- 既存の `run_phase5_ooi_2025.py` の処理を参考にする
- ID列（kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, ketto_toroku_bango, umaban）は予測時に除外する？

### 4. 予測実行
**LightGBMモデルで予測:**

```python
# 予測実行
predictions = model.predict(X_test)

print(f"予測結果: {len(predictions)}件")
print(f"予測値の範囲: {predictions.min():.4f} ~ {predictions.max():.4f}")
print(f"平均入線確率: {predictions.mean():.4f}")
```

**検証すべき点:**
- 予測値の範囲は 0.0 〜 1.0 か？
- 閾値（例: 0.5）で 0/1 に変換する必要があるか？
- 予測クラス（0 or 1）も出力するか？

### 5. 出力フォーマット
**Phase 3の出力CSV:**

```python
# ID列を追加
id_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
           'race_bango', 'ketto_toroku_bango', 'umaban']

result_df = test_df[id_cols].copy()
result_df['binary_probability'] = predictions
result_df['predicted_class'] = (predictions >= 0.5).astype(int)

# 保存
output_path = 'data/predictions/phase3/ooi_20260207_phase3.csv'
result_df.to_csv(output_path, index=False, encoding='shift_jis')

print(f"Phase 3 予測結果を保存: {output_path}")
print(f"入線予測頭数（predicted_class=1）: {result_df['predicted_class'].sum()}頭")
```

**出力例:**
```csv
kaisai_yen,kaisai_tsukihi,keibajo_code,race_bango,ketto_toroku_bango,umaban,binary_probability,predicted_class
2026,20260207,44,1,2023123456,1,0.7234,1
2026,20260207,44,1,2023123457,2,0.2156,0
...
```

**検証すべき点:**
- カラム名は `binary_probability` か `binary_score` か？
- `predicted_class` は必要か？（Phase 5で使用する？）
- エンコーディングは Phase 1 と同じにする？

### 6. 実行スクリプトの確認
**Phase 3 実行スクリプト（作成すべきもの）:**

```python
# scripts/phase3_binary/predict_phase3.py

import argparse
import pandas as pd
import lightgbm as lgb
from pathlib import Path

def predict_phase3(test_csv, model_path, output_csv):
    """
    Phase 3: 二値分類予測
    
    Args:
        test_csv: 特徴量CSV（Phase 1の出力）
        model_path: 学習済みモデルパス
        output_csv: 予測結果の出力先
    """
    # 1. モデル読み込み
    model = lgb.Booster(model_file=model_path)
    model_features = model.feature_name()
    
    # 2. テストデータ読み込み
    test_df = pd.read_csv(test_csv, encoding='shift_jis')
    
    # 3. 特徴量整列・補完
    # ... (上記の処理)
    
    # 4. 予測実行
    predictions = model.predict(X_test)
    
    # 5. 結果保存
    # ... (上記の処理)
    
    return result_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', required=True, help='テストデータCSV')
    parser.add_argument('--model', required=True, help='モデルパス')
    parser.add_argument('--output', required=True, help='出力先')
    args = parser.parse_args()
    
    predict_phase3(args.test, args.model, args.output)
```

**使用例:**
```bash
python scripts/phase3_binary/predict_phase3.py \
  --test data/features/2026/02/ooi_20260207_features.csv \
  --model models/binary/ooi_2023-2025_v3_model.txt \
  --output data/predictions/phase3/ooi_20260207_phase3.csv
```

### 7. 実行フロー
```
data/features/2026/02/ooi_20260207_features.csv (Phase 1の出力)
    ↓
Phase 3: 二値分類予測
    ↓
data/predictions/phase3/ooi_20260207_phase3.csv
    ↓
Phase 5 アンサンブルへ渡す
```

## 成果物
1. **実行スクリプト**: `scripts/phase3_binary/predict_phase3.py`
2. **実行ガイド**: `docs/phase3_execution_guide.md`

## 次のアクション
Phase 3の実行方法が確認できたら、Phase 4 の指示文を作成する。
