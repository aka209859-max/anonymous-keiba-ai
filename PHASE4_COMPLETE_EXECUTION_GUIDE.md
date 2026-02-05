# Phase 4 完全実行ガイド（全14競馬場対応）

## 🚨 重要な修正：水沢・盛岡・門別・金沢の追加

Phase 4 の実行で **4競馬場が欠落** していました。以下の手順で **全14競馬場** の学習を完了させます。

---

## 📊 **対象競馬場一覧（全14場）**

### ✅ **既に実行済み（10競馬場）**
- 大井（44）※2023-2024のみ → 2020-2025に修正が必要
- 船橋（43）
- 川崎（45）
- 浦和（42）
- 名古屋（48）
- 園田（50）
- 笠松（47）
- 佐賀（55）
- 高知（54）
- 姫路（51）

### ❌ **欠落している（4競馬場）**
- 門別（36）← 北海道（4月〜11月開催）
- 盛岡（35）← 岩手県（4月〜12月開催）
- 水沢（37）← 岩手県（1月〜3月開催）
- 金沢（46）← 石川県（通年開催）

---

## 🛠️ **完全実行手順**

### **Step 1: 欠落している4競馬場のデータ抽出**

```bash
cd E:\anonymous-keiba-ai

# 門別（30）※コード修正済み
python extract_training_data_v2.py --keibajo 30 --start-date 2020 --end-date 2025 --output mombetsu_2020-2025_v3.csv

# 盛岡（35）
python extract_training_data_v2.py --keibajo 35 --start-date 2020 --end-date 2025 --output morioka_2020-2025_v3.csv

# 水沢（36）※コード修正済み
python extract_training_data_v2.py --keibajo 36 --start-date 2020 --end-date 2025 --output mizusawa_2020-2025_v3.csv

# 金沢（46）
python extract_training_data_v2.py --keibajo 46 --start-date 2020 --end-date 2025 --output kanazawa_2020-2025_v3.csv

# 大井（44）を2020-2025に修正
python extract_training_data_v2.py --keibajo 44 --start-date 2020 --end-date 2025 --output ooi_2020-2025_v3.csv
```

---

### **Step 2: 全14競馬場のPhase 4学習を一括実行**

#### **方法1: 完全版スクリプトで一括実行（推奨）**

```bash
cd E:\anonymous-keiba-ai
python run_phase4_training_complete.py
```

**特徴**:
- 全14競馬場を自動処理
- タイムアウト: 10分/競馬場（ランキング・回帰学習）
- 既存ファイルはスキップ（重複実行を回避）
- 詳細な進捗表示

**実行時間**: 約2〜3時間（全14競馬場）

---

#### **方法2: 欠落している4競馬場のみ手動実行**

既に10競馬場は処理済みなので、欠落している4競馬場のみ実行：

```bash
cd E:\anonymous-keiba-ai

# 門別
python add_race_id_to_csv.py monbetsu_2020-2025_v3.csv
python convert_target_to_time.py monbetsu_2020-2025_v3.csv
python train_ranking_model.py monbetsu_2020-2025_v3_with_race_id.csv
python train_regression_model.py monbetsu_2020-2025_v3_time.csv

# 盛岡
python add_race_id_to_csv.py morioka_2020-2025_v3.csv
python convert_target_to_time.py morioka_2020-2025_v3.csv
python train_ranking_model.py morioka_2020-2025_v3_with_race_id.csv
python train_regression_model.py morioka_2020-2025_v3_time.csv

# 水沢
python add_race_id_to_csv.py mizusawa_2020-2025_v3.csv
python convert_target_to_time.py mizusawa_2020-2025_v3.csv
python train_ranking_model.py mizusawa_2020-2025_v3_with_race_id.csv
python train_regression_model.py mizusawa_2020-2025_v3_time.csv

# 金沢
python add_race_id_to_csv.py kanazawa_2020-2025_v3.csv
python convert_target_to_time.py kanazawa_2020-2025_v3.csv
python train_ranking_model.py kanazawa_2020-2025_v3_with_race_id.csv
python train_regression_model.py kanazawa_2020-2025_v3_time.csv

# 大井（2020-2025に修正）
python add_race_id_to_csv.py ooi_2020-2025_v3.csv
python convert_target_to_time.py ooi_2020-2025_v3.csv
python train_ranking_model.py ooi_2020-2025_v3_with_race_id.csv
python train_regression_model.py ooi_2020-2025_v3_time.csv
```

---

#### **方法3: 既存10競馬場のランキング学習のみ再実行**

ランキングモデルが生成されていない場合：

```bash
cd E:\anonymous-keiba-ai

# 既存10競馬場のランキング学習を再実行
python train_ranking_model.py himeji_2020-2025_v3_with_race_id.csv
python train_ranking_model.py kochi_2020-2025_v3_with_race_id.csv
python train_ranking_model.py saga_2020-2025_v3_with_race_id.csv
python train_ranking_model.py kasamatsu_2020-2025_v3_with_race_id.csv
python train_ranking_model.py sonoda_2020-2025_v3_with_race_id.csv
python train_ranking_model.py nagoya_2022-2025_v3_with_race_id.csv
python train_ranking_model.py urawa_2020-2025_v3_with_race_id.csv
python train_ranking_model.py kawasaki_2020-2025_v3_with_race_id.csv
python train_ranking_model.py funabashi_2020-2025_v3_with_race_id.csv
python train_ranking_model.py ooi_2023-2024_v3_with_race_id.csv
```

**実行時間**: 約5〜10分/競馬場

---

## 📂 **期待される成果物（全14競馬場 × 6ファイル = 84ファイル）**

各競馬場ごとに以下の6ファイルが生成されます：

### **データファイル（2個）**
- `{競馬場}_v3_with_race_id.csv` ← ランキング学習用
- `{競馬場}_v3_time.csv` ← 回帰学習用

### **ランキングモデル（2個）**
- `{競馬場}_v3_with_race_id_ranking_model.txt` ← モデルファイル
- `{競馬場}_v3_with_race_id_ranking_score.txt` ← 評価ファイル

### **回帰モデル（2個）**
- `{競馬場}_v3_time_regression_model.txt` ← モデルファイル
- `{競馬場}_v3_time_regression_score.txt` ← 評価ファイル

---

## 🎯 **Phase 4 完了確認**

### **確認コマンド**

```bash
cd E:\anonymous-keiba-ai

# ランキングモデルの確認（14ファイル）
dir *_ranking_model.txt

# 回帰モデルの確認（14ファイル）
dir *_regression_model.txt

# 評価ファイルの確認（28ファイル）
dir *_ranking_score.txt
dir *_regression_score.txt
```

**期待される結果**:
- ランキングモデル: 14ファイル
- 回帰モデル: 14ファイル
- 評価ファイル: 28ファイル（ランキング14 + 回帰14）

---

## 📊 **Phase 4 の全体像（修正版）**

| 競馬場 | データ期間 | ランキング | 回帰 | 二値分類 |
|--------|-----------|-----------|------|---------|
| 大井 | 2020-2025 | ⚠️ 要実行 | ⚠️ 要実行 | ✅ 完了 |
| 船橋 | 2020-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |
| 川崎 | 2020-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |
| 浦和 | 2020-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |
| 門別 | 2020-2025 | ❌ 未実行 | ❌ 未実行 | ✅ 完了 |
| 盛岡 | 2020-2025 | ❌ 未実行 | ❌ 未実行 | ✅ 完了 |
| 水沢 | 2020-2025 | ❌ 未実行 | ❌ 未実行 | ✅ 完了 |
| 金沢 | 2020-2025 | ❌ 未実行 | ❌ 未実行 | ✅ 完了 |
| 名古屋 | 2022-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |
| 園田 | 2020-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |
| 笠松 | 2020-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |
| 佐賀 | 2020-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |
| 高知 | 2020-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |
| 姫路 | 2020-2025 | ⚠️ 要実行 | ✅ 完了 | ✅ 完了 |

---

## ⚠️ **トラブルシューティング**

### **Q1: ランキング学習がタイムアウトする**
**A**: `run_phase4_training_complete.py` ではタイムアウトを10分に設定済み。手動実行の場合は放置してください（5〜10分で完了）。

### **Q2: データ抽出でエラーが出る**
**A**: PostgreSQL への接続を確認してください。以下のコマンドで接続テスト：
```bash
python extract_training_data_v2.py --keibajo 36 --start-date 2020 --end-date 2025 --output monbetsu_2020-2025_v3.csv
```

### **Q3: 既存のモデルを上書きしたい**
**A**: モデルファイルを削除してから再実行：
```bash
del *_ranking_model.txt
del *_regression_model.txt
python run_phase4_training_complete.py
```

---

## 🚀 **次のステップ**

### **Step 1: 欠落している4競馬場のデータ抽出**
```bash
python extract_training_data_v2.py --keibajo 36 --start-date 2020 --end-date 2025 --output monbetsu_2020-2025_v3.csv
python extract_training_data_v2.py --keibajo 35 --start-date 2020 --end-date 2025 --output morioka_2020-2025_v3.csv
python extract_training_data_v2.py --keibajo 37 --start-date 2020 --end-date 2025 --output mizusawa_2020-2025_v3.csv
python extract_training_data_v2.py --keibajo 46 --start-date 2020 --end-date 2025 --output kanazawa_2020-2025_v3.csv
python extract_training_data_v2.py --keibajo 44 --start-date 2020 --end-date 2025 --output ooi_2020-2025_v3.csv
```

### **Step 2: 一括実行**
```bash
python run_phase4_training_complete.py
```

### **Step 3: 完了確認**
```bash
dir *_ranking_model.txt
dir *_regression_model.txt
```

### **Step 4: 評価ファイルのアップロード**
全14競馬場の `*_ranking_score.txt` と `*_regression_score.txt` をアップロードして、Phase 4 完了報告を作成します。

---

## 📝 **まとめ**

- **欠落**: 門別・盛岡・水沢・金沢の4競馬場
- **修正**: 大井を2020-2025に修正
- **実行**: `run_phase4_training_complete.py` で一括処理
- **期待**: 全14競馬場 × 3モデル = 42モデル

---

**作成日**: 2026-02-04  
**対象**: Phase 4 完全実行（全14競馬場対応）  
**作成者**: Anonymous Keiba AI Development Team
