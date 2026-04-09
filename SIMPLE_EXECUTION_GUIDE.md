# 🚀 簡単実行ガイド (文字化け対策版)

**最終更新**: 2026-02-11  
**問題**: batファイルの文字化け  
**解決策**: Pythonスクリプトを使用

---

## ✅ 事前確認

```bash
cd E:\anonymous-keiba-ai

# 1. スクリプトの確認
python -c "with open('extract_training_data_v2.py', 'r', encoding='utf-8') as f: content = f.read(); print('rank_target:', 'rank_target' in content); print('soha_time:', 'soha_time' in content)"

# 期待出力: rank_target: True, soha_time: True

# 2. DB接続確認
python test_db_connection.py

# 期待: データベース接続成功
```

---

## 🎯 実行方法 (2つの選択肢)

### **方法A: Pythonスクリプト (推奨)**

文字化けの問題がないため、こちらを推奨します。

#### **ステップ1: 残り13競馬場のデータ生成**

```bash
cd E:\anonymous-keiba-ai
python generate_all_training_data.py
```

**所要時間**: 約1〜2時間

#### **ステップ2: 船橋 Phase 7 Ranking**

```bash
cd E:\anonymous-keiba-ai
python run_phase7_funabashi_ranking.py
```

**所要時間**: 約10〜20分

---

### **方法B: batファイル (文字化け修正済み)**

英語表示に変更しましたが、文字化けが続く場合は方法Aを使用してください。

#### **ステップ1: 残り13競馬場のデータ生成**

```bash
cd E:\anonymous-keiba-ai
GENERATE_ALL_TRAINING_DATA.bat
```

#### **ステップ2: 船橋 Phase 7 Ranking**

```bash
cd E:\anonymous-keiba-ai
RUN_PHASE7_FUNABASHI_RANKING.bat
```

---

## 📊 期待される出力

### ステップ1完了後

```
data\training\
├── monbetsu_2020-2026_with_time_PHASE78.csv    (New)
├── obihiro_2020-2026_with_time_PHASE78.csv     (New)
├── morioka_2020-2026_with_time_PHASE78.csv     (New)
├── mizusawa_2020-2026_with_time_PHASE78.csv    (New)
├── urawa_2020-2026_with_time_PHASE78.csv       (New)
├── funabashi_2020-2026_with_time_PHASE78.csv   (Already completed)
├── ooi_2020-2026_with_time_PHASE78.csv         (New)
├── kawasaki_2020-2026_with_time_PHASE78.csv    (New)
├── kanazawa_2020-2026_with_time_PHASE78.csv    (New)
├── kasamatsu_2020-2026_with_time_PHASE78.csv   (New)
├── nagoya_2020-2026_with_time_PHASE78.csv      (New)
├── sonoda_2020-2026_with_time_PHASE78.csv      (New)
├── himeji_2020-2026_with_time_PHASE78.csv      (New)
├── kochi_2020-2026_with_time_PHASE78.csv       (New)
└── saga_2020-2026_with_time_PHASE78.csv        (New)
```

**各ファイルの構造**: 52カラム (target + rank_target + time + 49特徴量)

### ステップ2完了後

```
data\features\selected\
└── funabashi_ranking_selected_features.csv

data\reports\phase7_feature_selection\
├── funabashi_ranking_importance.png
└── funabashi_ranking_report.json
```

---

## 🆘 トラブルシューティング

### 問題1: データベース接続エラー

```
psycopg2.OperationalError: could not connect to server
```

**解決策**:
1. PC-KEIBAを起動
2. PostgreSQLサービスを確認
3. パスワードを確認

---

### 問題2: ファイルが見つからない

```
FileNotFoundError: [Errno 2] No such file or directory
```

**解決策**:
```bash
cd E:\anonymous-keiba-ai
mkdir data\training
mkdir data\features\selected
mkdir data\reports\phase7_feature_selection
```

---

### 問題3: メモリ不足

```
MemoryError: Unable to allocate array
```

**解決策**: 会場を分けて実行

```python
# generate_all_training_data.py の VENUES リストを編集して
# 3〜5会場ずつ実行
```

---

## 📁 ファイルダウンロード (必要な場合)

GitHubから最新版をダウンロード:

```
https://github.com/aka209859-max/anonymous-keiba-ai/tree/phase0_complete_fix_2026_02_07
```

**必要なファイル**:
1. `extract_training_data_v2.py` (修正版)
2. `generate_all_training_data.py` (Pythonスクリプト)
3. `run_phase7_funabashi_ranking.py` (Pythonスクリプト)

---

## ✅ 成功確認

```bash
# データ生成の確認
dir data\training\*_PHASE78.csv

# 14個のファイルが表示されればOK

# データ構造の確認
python -c "import pandas as pd; df = pd.read_csv('data/training/funabashi_2020-2026_with_time_PHASE78.csv', encoding='shift-jis', nrows=5); print('Columns:', len(df.columns)); print('Targets:', [c for c in df.columns if c in ['target', 'rank_target', 'time']])"

# 期待出力: Columns: 52, Targets: ['target', 'rank_target', 'time']
```

---

## 🎯 次のステップ (船橋テスト成功後)

1. Phase 7 Regression (船橋)
2. Phase 8 Ranking 最適化 (船橋)
3. Phase 8 Regression 最適化 (船橋)
4. 全会場展開

---

**準備ができたら、方法Aまたは方法Bを選択して実行してください！**
