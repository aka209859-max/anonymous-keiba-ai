# 📊 学習データ再生成 + Phase 7 実行計画 - サマリーレポート

**作成日**: 2026-02-11  
**ステータス**: ✅ 実行準備完了  
**対象**: 残り13競馬場データ生成 → 船橋Phase 7テスト

---

## 🎯 **実行計画の全体像**

```
┌─────────────────────────────────────────────────────────┐
│ ステップ1: 残り13競馬場の学習データ生成 (1〜2時間)    │
├─────────────────────────────────────────────────────────┤
│  GENERATE_ALL_TRAINING_DATA.bat を実行                 │
│  ↓                                                      │
│  13会場 × *_2020-2026_with_time_PHASE78.csv 生成       │
│  (52カラム: target + rank_target + time + 49特徴量)    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ ステップ2: 船橋 Phase 7 Ranking テスト (10〜20分)     │
├─────────────────────────────────────────────────────────┤
│  RUN_PHASE7_FUNABASHI_RANKING.bat を実行               │
│  ↓                                                      │
│  Boruta特徴量選択 → 最適特徴量リスト生成               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ ステップ3: 結果確認 → 全会場展開の判断                │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 **作成したファイル一覧**

### 1. **実行用バッチファイル**

| ファイル名 | 用途 | 所要時間 |
|-----------|------|---------|
| `GENERATE_ALL_TRAINING_DATA.bat` | 残り13競馬場の学習データ一括生成 | 1〜2時間 |
| `RUN_PHASE7_FUNABASHI_RANKING.bat` | 船橋Phase 7 Ranking特徴量選択 | 10〜20分 |

### 2. **ドキュメント**

| ファイル名 | 内容 |
|-----------|------|
| `QUICKSTART_PHASE7_FUNABASHI.md` | クイックスタートガイド |
| `EXECUTION_CHECKLIST_FUNABASHI.md` | 詳細な実行手順とチェックリスト |
| `PHASE7_8_EXECUTION_ROADMAP.md` | 全体ロードマップ (既存) |
| `PHASE0_5_INVESTIGATION_REPORT.md` | Phase 0-5 調査報告 (既存) |

### 3. **修正版スクリプト**

| ファイル名 | 修正内容 | ブランチ |
|-----------|---------|---------|
| `extract_training_data_v2.py` | rank_target + time カラム追加 | phase0_complete_fix_2026_02_07 |

---

## 🚀 **即座に実行できるコマンド**

### Windows環境 (E:\anonymous-keiba-ai)

```bash
# 1. カレントディレクトリへ移動
cd E:\anonymous-keiba-ai

# 2. スクリプト確認
python -c "with open('extract_training_data_v2.py', 'r', encoding='utf-8') as f: content = f.read(); print('rank_target:', 'rank_target' in content); print('soha_time:', 'soha_time' in content)"

# 3. データベース接続テスト
python test_db_connection.py

# 4. 残り13競馬場のデータ生成 (1〜2時間)
GENERATE_ALL_TRAINING_DATA.bat

# 5. 船橋 Phase 7 Ranking テスト (10〜20分)
RUN_PHASE7_FUNABASHI_RANKING.bat
```

---

## 📊 **出力ファイルの構造**

### 学習データ (ステップ1の出力)

```
data\training\
├── monbetsu_2020-2026_with_time_PHASE78.csv    (門別)
├── obihiro_2020-2026_with_time_PHASE78.csv     (帯広)
├── morioka_2020-2026_with_time_PHASE78.csv     (盛岡)
├── mizusawa_2020-2026_with_time_PHASE78.csv    (水沢)
├── urawa_2020-2026_with_time_PHASE78.csv       (浦和)
├── funabashi_2020-2026_with_time_PHASE78.csv   (船橋) ✅ 完了済み
├── ooi_2020-2026_with_time_PHASE78.csv         (大井)
├── kawasaki_2020-2026_with_time_PHASE78.csv    (川崎)
├── kanazawa_2020-2026_with_time_PHASE78.csv    (金沢)
├── kasamatsu_2020-2026_with_time_PHASE78.csv   (笠松)
├── nagoya_2020-2026_with_time_PHASE78.csv      (名古屋)
├── sonoda_2020-2026_with_time_PHASE78.csv      (園田)
├── himeji_2020-2026_with_time_PHASE78.csv      (姫路)
├── kochi_2020-2026_with_time_PHASE78.csv       (高知)
└── saga_2020-2026_with_time_PHASE78.csv        (佐賀)
```

**各ファイルの構造** (52カラム):
```
1. target         # Binary分類用 (3着以内=1, 圏外=0)
2. rank_target    # Ranking学習用 (着順 1〜N)
3. time           # Regression学習用 (走破タイム 秒)
4-52. 特徴量      # 49個の特徴量
```

### Phase 7 出力 (ステップ2の出力)

```
data\features\selected\
└── funabashi_ranking_selected_features.csv  (選択された特徴量リスト)

data\reports\phase7_feature_selection\
├── funabashi_ranking_importance.png         (特徴量重要度グラフ)
└── funabashi_ranking_report.json            (詳細レポート)
```

---

## ✅ **成功の判定基準**

### ステップ1: データ生成

- [x] 船橋 (43) - 既に完了
- [ ] 門別 (30)
- [ ] 帯広 (33)
- [ ] 盛岡 (35)
- [ ] 水沢 (36)
- [ ] 浦和 (42)
- [ ] 大井 (44)
- [ ] 川崎 (45)
- [ ] 金沢 (46)
- [ ] 笠松 (47)
- [ ] 名古屋 (48)
- [ ] 園田 (50)
- [ ] 姫路 (51)
- [ ] 高知 (54)
- [ ] 佐賀 (55)

**成功条件**:
- ✅ 全14会場のCSVファイルが生成された
- ✅ 各ファイルが52カラム
- ✅ target, rank_target, time カラムが存在する

### ステップ2: Phase 7 Ranking

- [ ] 船橋 (43)

**成功条件**:
- ✅ `funabashi_ranking_selected_features.csv` が生成された
- ✅ 特徴量重要度グラフが生成された
- ✅ JSONレポートが生成された
- ✅ 選択された特徴量数が10個以上

---

## 🆘 **よくあるエラーと対処法**

### エラー1: データベース接続失敗

```
psycopg2.OperationalError: could not connect to server
```

**対処法**:
1. PC-KEIBAを起動
2. PostgreSQLサービスを起動 (services.msc)
3. `test_db_connection.py` で接続確認

---

### エラー2: ファイルが見つからない

```
FileNotFoundError: [Errno 2] No such file or directory: 'data\\training\\...'
```

**対処法**:
1. `cd E:\anonymous-keiba-ai` で移動
2. `mkdir data\training` でディレクトリ作成

---

### エラー3: メモリ不足

```
MemoryError: Unable to allocate array
```

**対処法**:
1. 会場を分けて実行 (3〜5会場ずつ)
2. `--limit 10000` でデータ量を制限してテスト

---

## 📈 **進捗トラッキング**

### 実行状況の確認

```bash
# 生成されたファイルを確認
dir data\training\*_PHASE78.csv

# 各ファイルの行数を確認
python -c "import pandas as pd; import glob; files = glob.glob('data/training/*_PHASE78.csv'); [print(f'{f}: {len(pd.read_csv(f, encoding=\"shift-jis\"))} records') for f in files]"
```

### ログの確認

```bash
# 生成ログを確認
type data\training\generation_log_*.txt
```

---

## 🎯 **次のステップ (船橋テスト成功後)**

### 1. Phase 7 Regression (船橋)
```bash
RUN_PHASE7_FUNABASHI_REGRESSION.bat  # 今後作成
```

### 2. Phase 8 Ranking 最適化 (船橋)
```bash
RUN_PHASE8_FUNABASHI_RANKING.bat  # 今後作成
```

### 3. Phase 8 Regression 最適化 (船橋)
```bash
RUN_PHASE8_FUNABASHI_REGRESSION.bat  # 今後作成
```

### 4. 全会場展開
```bash
RUN_PHASE7_ALL_VENUES.bat  # 全14会場
RUN_PHASE8_ALL_VENUES.bat  # 全14会場
```

---

## 📚 **ドキュメント参照**

| ドキュメント | 用途 |
|-------------|------|
| `QUICKSTART_PHASE7_FUNABASHI.md` | 今すぐ実行したい場合 |
| `EXECUTION_CHECKLIST_FUNABASHI.md` | 詳細な手順を確認したい場合 |
| `PHASE7_8_EXECUTION_ROADMAP.md` | 全体計画を確認したい場合 |
| `PHASE0_5_INVESTIGATION_REPORT.md` | 背景を理解したい場合 |

---

## 🔗 **GitHub リポジトリ**

```
https://github.com/aka209859-max/anonymous-keiba-ai
ブランチ: phase0_complete_fix_2026_02_07
```

**最新ファイルのダウンロード**:
- extract_training_data_v2.py
- GENERATE_ALL_TRAINING_DATA.bat
- RUN_PHASE7_FUNABASHI_RANKING.bat
- QUICKSTART_PHASE7_FUNABASHI.md
- EXECUTION_CHECKLIST_FUNABASHI.md

---

## 💡 **推奨実行スケジュール**

### 平日夜間
```
19:00 - データ生成開始 (GENERATE_ALL_TRAINING_DATA.bat)
21:00 - データ生成完了 (推定)
21:00 - Phase 7 Ranking開始 (RUN_PHASE7_FUNABASHI_RANKING.bat)
21:20 - Phase 7 Ranking完了 (推定)
```

### 週末
```
午前: データ生成 (1〜2時間)
午後: Phase 7 Ranking + Phase 7 Regression (各10〜20分)
夜間: Phase 8 最適化 (各30〜60分)
```

---

**最終更新**: 2026-02-11  
**ステータス**: ✅ 実行準備完了  
**次のアクション**: `QUICKSTART_PHASE7_FUNABASHI.md` を参照して実行開始
