# 🚀 学習データ再生成 + Phase 7 実行計画

**作成日**: 2026-02-11  
**対象**: 船橋のみでテスト → その後全会場展開  
**目的**: 正しい構造の学習データ生成 → Phase 7 Ranking特徴量選択

---

## ✅ 事前確認チェックリスト

### 1. 環境確認
- [ ] PC-KEIBAデータベースが起動している
- [ ] PostgreSQL (127.0.0.1:5432) に接続可能
- [ ] `extract_training_data_v2.py` が修正版である (rank_target + time 対応)

### 2. ディレクトリ確認
```bash
E:\anonymous-keiba-ai\
├── extract_training_data_v2.py  ← 修正版
├── GENERATE_ALL_TRAINING_DATA.bat  ← 今回作成
├── RUN_PHASE7_FUNABASHI_RANKING.bat  ← 今回作成
└── data\
    ├── training\  ← 学習データ出力先
    ├── features\selected\  ← Phase 7 出力先
    └── reports\phase7_feature_selection\  ← Phase 7 レポート出力先
```

### 3. Python環境確認
```bash
# 必要なパッケージを確認
pip list | findstr "psycopg2 pandas numpy scikit-learn boruta matplotlib"

# 不足している場合はインストール
pip install psycopg2-binary pandas numpy scikit-learn boruta matplotlib
```

---

## 📋 実行手順

### **ステップ1: 修正版スクリプトの確認**

```bash
# E:\anonymous-keiba-ai\ で実行
python -c "with open('extract_training_data_v2.py', 'r', encoding='utf-8') as f: content = f.read(); print('rank_target found:', 'rank_target' in content); print('soha_time found:', 'soha_time' in content)"
```

**期待出力**:
```
rank_target found: True
soha_time found: True
```

もし `False` の場合:
1. GitHubから最新版をダウンロード
   - URL: https://github.com/aka209859-max/anonymous-keiba-ai/raw/phase0_complete_fix_2026_02_07/extract_training_data_v2.py
2. `E:\anonymous-keiba-ai\extract_training_data_v2.py` に上書き保存

---

### **ステップ2: データベース接続テスト**

```bash
# E:\anonymous-keiba-ai\ で実行
python test_db_connection.py
```

**期待出力**:
```
✅ データベース接続成功
船橋のレース件数: 13,596件
出走馬データ件数: 147,743件
```

エラーが出る場合:
- PC-KEIBAを起動
- PostgreSQLサービスを確認 (Windowsサービス)
- `DB_CONFIG` のパスワードを確認

---

### **ステップ3: 残り13会場の学習データ生成**

```bash
# E:\anonymous-keiba-ai\ で実行
GENERATE_ALL_TRAINING_DATA.bat
```

**処理内容**:
- 13会場 × 5〜10分 = 約1〜2時間
- 各会場の `*_2020-2026_with_time_PHASE78.csv` を生成

**出力ファイル**:
```
data\training\
├── monbetsu_2020-2026_with_time_PHASE78.csv
├── obihiro_2020-2026_with_time_PHASE78.csv
├── morioka_2020-2026_with_time_PHASE78.csv
├── mizusawa_2020-2026_with_time_PHASE78.csv
├── urawa_2020-2026_with_time_PHASE78.csv
├── funabashi_2020-2026_with_time_PHASE78.csv  ← 既に完了
├── ooi_2020-2026_with_time_PHASE78.csv
├── kawasaki_2020-2026_with_time_PHASE78.csv
├── kanazawa_2020-2026_with_time_PHASE78.csv
├── kasamatsu_2020-2026_with_time_PHASE78.csv
├── nagoya_2020-2026_with_time_PHASE78.csv
├── sonoda_2020-2026_with_time_PHASE78.csv
├── himeji_2020-2026_with_time_PHASE78.csv
├── kochi_2020-2026_with_time_PHASE78.csv
└── saga_2020-2026_with_time_PHASE78.csv
```

---

### **ステップ4: データ検証 (生成後)**

```bash
# E:\anonymous-keiba-ai\ で実行
python -c "import pandas as pd; df = pd.read_csv('data/training/funabashi_2020-2026_with_time_PHASE78.csv', encoding='shift-jis', nrows=10); print('Total columns:', len(df.columns)); print('Columns:', df.columns[:5].tolist(), '...'); print('Target vars:', [c for c in df.columns if c in ['target', 'rank_target', 'time']])"
```

**期待出力**:
```
Total columns: 52
Columns: ['target', 'rank_target', 'time', 'kaisai_nen', 'kaisai_tsukihi'] ...
Target vars: ['target', 'rank_target', 'time']
```

---

### **ステップ5: 船橋 Phase 7 Ranking 実行**

```bash
# E:\anonymous-keiba-ai\ で実行
RUN_PHASE7_FUNABASHI_RANKING.bat
```

**処理内容**:
- Boruta特徴量選択アルゴリズムで最適特徴量を選定
- 実行時間: 約10〜20分

**出力ファイル**:
```
data\features\selected\
└── funabashi_ranking_selected_features.csv

data\reports\phase7_feature_selection\
├── funabashi_ranking_importance.png
└── funabashi_ranking_report.json
```

---

## 📊 各ステップの推定時間

| ステップ | 内容 | 推定時間 |
|---------|------|---------|
| Step 1 | スクリプト確認 | 1分 |
| Step 2 | DB接続テスト | 1分 |
| Step 3 | 13会場データ生成 | 1〜2時間 |
| Step 4 | データ検証 | 5分 |
| Step 5 | Phase 7 Ranking (船橋) | 10〜20分 |
| **合計** | | **約1.5〜2.5時間** |

---

## 🎯 成功の判定基準

### ✅ ステップ3 (データ生成) の成功判定
- [ ] 全14会場のCSVファイルが生成された
- [ ] 各ファイルが 52カラム (target + rank_target + time + 49特徴量)
- [ ] ログファイルに「完了」と記録されている

### ✅ ステップ5 (Phase 7 Ranking) の成功判定
- [ ] `funabashi_ranking_selected_features.csv` が生成された
- [ ] 特徴量重要度グラフ `importance.png` が表示された
- [ ] JSONレポートに選択された特徴量数が記録されている

---

## 🆘 トラブルシューティング

### 問題1: データベース接続エラー
```
psycopg2.OperationalError: could not connect to server
```

**対処**:
1. PC-KEIBAを起動
2. Windowsサービスで PostgreSQL が起動しているか確認
3. `test_db_connection.py` でパスワードを確認

---

### 問題2: メモリ不足エラー
```
MemoryError: Unable to allocate array
```

**対処**:
1. 会場を分けて実行 (一度に3〜5会場ずつ)
2. `--limit` オプションでテスト実行
```bash
python extract_training_data_v2.py --keibajo 43 --limit 1000 --output test.csv
```

---

### 問題3: Phase 7 特徴量選択エラー
```
ValueError: All features are rejected
```

**対処**:
1. データの欠損値を確認
```python
import pandas as pd
df = pd.read_csv('data/training/funabashi_2020-2026_with_time_PHASE78.csv', encoding='shift-jis')
print(df.isnull().sum())
```

2. `--max-iter` を減らす
```bash
python scripts\phase7_feature_selection\run_boruta_ranking.py data\training\funabashi_2020-2026_with_time_PHASE78.csv --max-iter 50
```

---

## 📚 関連ドキュメント

- [PHASE7_8_EXECUTION_ROADMAP.md](./PHASE7_8_EXECUTION_ROADMAP.md) - 全体ロードマップ
- [PHASE0_5_INVESTIGATION_REPORT.md](./PHASE0_5_INVESTIGATION_REPORT.md) - Phase 0-5 調査報告
- [TRAINING_DATA_REGENERATION_GUIDE.md](./TRAINING_DATA_REGENERATION_GUIDE.md) - データ再生成ガイド

---

## 📞 次のアクション

### 今すぐ実行可能なコマンド

```bash
# ステップ1: スクリプト確認
cd E:\anonymous-keiba-ai
python -c "with open('extract_training_data_v2.py', 'r', encoding='utf-8') as f: content = f.read(); print('rank_target:', 'rank_target' in content); print('soha_time:', 'soha_time' in content)"

# ステップ2: DB接続テスト
python test_db_connection.py

# ステップ3: データ生成開始
GENERATE_ALL_TRAINING_DATA.bat
```

---

**最終更新**: 2026-02-11  
**ステータス**: 実行準備完了  
**次のアクション**: ステップ1から順次実行してください
