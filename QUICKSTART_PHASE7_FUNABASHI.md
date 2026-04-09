# 🚀 クイックスタート: 残り13競馬場データ生成 + 船橋Phase 7テスト

**最終更新**: 2026-02-11  
**所要時間**: 約1.5〜2.5時間  
**前提条件**: PC-KEIBAデータベースが稼働中

---

## 📥 **ステップ0: 最新スクリプトのダウンロード (必要な場合のみ)**

### 修正版 `extract_training_data_v2.py` の確認

```bash
# E:\anonymous-keiba-ai\ で実行
cd E:\anonymous-keiba-ai
python -c "with open('extract_training_data_v2.py', 'r', encoding='utf-8') as f: content = f.read(); print('✅ rank_target:', 'rank_target' in content); print('✅ soha_time:', 'soha_time' in content)"
```

**期待出力**:
```
✅ rank_target: True
✅ soha_time: True
```

もし `False` が表示された場合は、GitHubから最新版をダウンロード:

**ダウンロードURL**:
```
https://github.com/aka209859-max/anonymous-keiba-ai/raw/phase0_complete_fix_2026_02_07/extract_training_data_v2.py
```

**保存先**: `E:\anonymous-keiba-ai\extract_training_data_v2.py` に上書き

---

## 📥 **ステップ0-2: 実行用バッチファイルのダウンロード**

GitHubから以下の3ファイルをダウンロード:

### 1. **GENERATE_ALL_TRAINING_DATA.bat**
```
https://github.com/aka209859-max/anonymous-keiba-ai/raw/phase0_complete_fix_2026_02_07/GENERATE_ALL_TRAINING_DATA.bat
```
**用途**: 残り13競馬場の学習データを一括生成

### 2. **RUN_PHASE7_FUNABASHI_RANKING.bat**
```
https://github.com/aka209859-max/anonymous-keiba-ai/raw/phase0_complete_fix_2026_02_07/RUN_PHASE7_FUNABASHI_RANKING.bat
```
**用途**: 船橋のPhase 7 Ranking特徴量選択を実行

### 3. **EXECUTION_CHECKLIST_FUNABASHI.md**
```
https://github.com/aka209859-max/anonymous-keiba-ai/raw/phase0_complete_fix_2026_02_07/EXECUTION_CHECKLIST_FUNABASHI.md
```
**用途**: 詳細な実行手順とトラブルシューティング

**保存先**: すべて `E:\anonymous-keiba-ai\` に保存

---

## 🚀 **ステップ1: 残り13競馬場の学習データ生成**

### 実行コマンド

```bash
# E:\anonymous-keiba-ai\ で実行
cd E:\anonymous-keiba-ai
GENERATE_ALL_TRAINING_DATA.bat
```

### 処理内容

- **対象**: 13競馬場 (門別、帯広、盛岡、水沢、浦和、大井、川崎、金沢、笠松、名古屋、園田、姫路、高知、佐賀)
- **期間**: 2020-2026年
- **所要時間**: 約1〜2時間
- **出力**: `data\training\*_2020-2026_with_time_PHASE78.csv` (各会場)

### 画面表示例

```
============================================================
🚀 地方競馬AI 学習データ一括生成 (残り13会場)
============================================================

📊 対象競馬場: 13会場 (船橋は完了済み)
⏱️  推定時間: 約1〜2時間

============================================================
[1/13] 門別 (コード: 30) データ生成中...
============================================================
🏇 地方競馬AI 学習データ抽出
============================================================
✅ データベース接続成功
✅ データ抽出完了: 23,456件
✅ クラス分布: 0 -> 16,543件 (70.5%), 1 -> 6,913件 (29.5%)
✅ CSV保存完了: data\training\monbetsu_2020-2026_with_time_PHASE78.csv
✅ カラム数: 52
============================================================

✅ 門別 完了！

[2/13] 帯広 (コード: 33) データ生成中...
...
```

### 生成されるファイル

```
data\training\
├── monbetsu_2020-2026_with_time_PHASE78.csv   (門別)
├── obihiro_2020-2026_with_time_PHASE78.csv    (帯広)
├── morioka_2020-2026_with_time_PHASE78.csv    (盛岡)
├── mizusawa_2020-2026_with_time_PHASE78.csv   (水沢)
├── urawa_2020-2026_with_time_PHASE78.csv      (浦和)
├── funabashi_2020-2026_with_time_PHASE78.csv  (船橋) ← 既に完了
├── ooi_2020-2026_with_time_PHASE78.csv        (大井)
├── kawasaki_2020-2026_with_time_PHASE78.csv   (川崎)
├── kanazawa_2020-2026_with_time_PHASE78.csv   (金沢)
├── kasamatsu_2020-2026_with_time_PHASE78.csv  (笠松)
├── nagoya_2020-2026_with_time_PHASE78.csv     (名古屋)
├── sonoda_2020-2026_with_time_PHASE78.csv     (園田)
├── himeji_2020-2026_with_time_PHASE78.csv     (姫路)
├── kochi_2020-2026_with_time_PHASE78.csv      (高知)
└── saga_2020-2026_with_time_PHASE78.csv       (佐賀)
```

---

## 🧪 **ステップ2: 船橋 Phase 7 Ranking テスト実行**

### 実行コマンド

```bash
# E:\anonymous-keiba-ai\ で実行 (ステップ1完了後)
cd E:\anonymous-keiba-ai
RUN_PHASE7_FUNABASHI_RANKING.bat
```

### 処理内容

- **対象**: 船橋競馬場
- **アルゴリズム**: Boruta特徴量選択
- **所要時間**: 約10〜20分
- **出力**: 選択された特徴量リスト + 重要度グラフ + JSONレポート

### 画面表示例

```
============================================================
🧪 船橋 Phase 7 Ranking 特徴量選択テスト
============================================================

📊 対象データ: funabashi_2020-2026_with_time_PHASE78.csv
🎯 目的: Ranking学習に最適な特徴量を選定
⏱️  推定時間: 約10〜20分

✅ 入力ファイル確認完了

============================================================
Phase 7 Ranking 特徴量選択を開始します...
============================================================

Iteration: 1/100 ...
Iteration: 2/100 ...
...
✅ 特徴量選択完了: 32個の特徴量が選択されました

============================================================
✅ 船橋 Phase 7 Ranking 特徴量選択が完了しました！
============================================================

📁 出力ファイル:
  - data\features\selected\funabashi_ranking_selected_features.csv
  - data\reports\phase7_feature_selection\funabashi_ranking_importance.png
  - data\reports\phase7_feature_selection\funabashi_ranking_report.json
```

### 生成されるファイル

```
data\features\selected\
└── funabashi_ranking_selected_features.csv   (選択された特徴量リスト)

data\reports\phase7_feature_selection\
├── funabashi_ranking_importance.png          (特徴量重要度グラフ)
└── funabashi_ranking_report.json             (詳細レポート)
```

---

## ✅ **成功確認**

### データ生成の確認

```bash
# E:\anonymous-keiba-ai\ で実行
dir data\training\*_PHASE78.csv
```

**期待結果**: 14個のCSVファイルが表示される

### データ構造の確認

```bash
# E:\anonymous-keiba-ai\ で実行
python -c "import pandas as pd; df = pd.read_csv('data/training/funabashi_2020-2026_with_time_PHASE78.csv', encoding='shift-jis', nrows=5); print('Columns:', len(df.columns)); print('Targets:', [c for c in df.columns if c in ['target', 'rank_target', 'time']])"
```

**期待出力**:
```
Columns: 52
Targets: ['target', 'rank_target', 'time']
```

### Phase 7 出力の確認

```bash
# E:\anonymous-keiba-ai\ で実行
type data\features\selected\funabashi_ranking_selected_features.csv
```

**期待出力**: 選択された特徴量のリストが表示される

---

## 🆘 **トラブルシューティング**

### 問題1: データベース接続エラー

**エラーメッセージ**:
```
psycopg2.OperationalError: could not connect to server
```

**解決策**:
1. PC-KEIBAを起動
2. PostgreSQLサービスを確認:
   - Windowsキー + R
   - `services.msc` と入力
   - "PostgreSQL" を探して「開始」

### 問題2: メモリ不足

**エラーメッセージ**:
```
MemoryError: Unable to allocate array
```

**解決策**:
1. 会場を分けて実行 (3〜5会場ずつ)
2. バッチファイルを編集して会場数を減らす

### 問題3: ファイルが見つからない

**エラーメッセージ**:
```
FileNotFoundError: [Errno 2] No such file or directory
```

**解決策**:
1. カレントディレクトリを確認: `cd E:\anonymous-keiba-ai`
2. `data\training` フォルダが存在するか確認
3. 必要に応じて手動作成: `mkdir data\training`

---

## 📊 **次のステップ**

### ステップ3: Phase 7 Regression (船橋)

```bash
# 今後作成予定
RUN_PHASE7_FUNABASHI_REGRESSION.bat
```

### ステップ4: Phase 8 Ranking 最適化 (船橋)

```bash
# 今後作成予定
RUN_PHASE8_FUNABASHI_RANKING.bat
```

### ステップ5: Phase 8 Regression 最適化 (船橋)

```bash
# 今後作成予定
RUN_PHASE8_FUNABASHI_REGRESSION.bat
```

### ステップ6: 全会場展開

船橋でのテストが成功したら、残り13会場でも同じ処理を実行

---

## 📚 **関連ドキュメント**

- **PHASE7_8_EXECUTION_ROADMAP.md**: 全体ロードマップ
- **EXECUTION_CHECKLIST_FUNABASHI.md**: 詳細な実行手順
- **PHASE0_5_INVESTIGATION_REPORT.md**: Phase 0-5 調査報告

---

## 📞 **サポート情報**

### GitHub リポジトリ
```
https://github.com/aka209859-max/anonymous-keiba-ai
```

### ブランチ
```
phase0_complete_fix_2026_02_07  (修正版スクリプト)
```

---

**準備ができたら、ステップ1から順次実行してください！**

**最終更新**: 2026-02-11  
**ステータス**: ✅ 実行準備完了
