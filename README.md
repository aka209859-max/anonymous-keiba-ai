# Anonymous Keiba AI

地方競馬に特化した機械学習予想システム

## プロジェクト概要

PC-KEIBA Database のデータを活用し、LightGBM + Boruta + Optuna による高精度な競馬予想AIを構築します。

## 技術スタック

- **Python**: 3.14
- **機械学習**: LightGBM
- **特徴量選択**: Boruta
- **ハイパーパラメータ最適化**: Optuna
- **データベース**: PostgreSQL (PC-KEIBA)

## プロジェクト構成

\\\
anonymous-keiba-ai/
├── docs/              # ドキュメント
├── data/              # データ（.gitignore対象）
├── src/               # ソースコード
├── models/            # 学習済みモデル（.gitignore対象）
└── scripts/           # SQL・補助スクリプト
\\\

## 開発フェーズ

### Phase 1: ✅ 完了
Development Ver. コード作成（Boruta + Optuna）
- `train_development.py` - 学習プログラム

### Phase 2: ✅ 完了
学習データ抽出SQL作成
- `extract_training_data.py` - データ抽出スクリプト（基本版）
- `extract_training_data_v2.py` - データ抽出スクリプト（過去走データ統合版）
- `inspect_database.py` - DB構造調査ツール
- `docs/sql_design.md` - SQL設計書
- `docs/v2_execution_guide.md` - v2実行ガイド

### Phase 2.5: ✅ 完了
過去走データ統合
- ROW_NUMBER()を使用した過去走データ取得
- 前走〜5走前のデータを取得（着順、タイム、馬体重など）
- 特徴量数: 18個 → 45個 に増加

### Phase 3: ✅ 完了
14競馬場のモデル生成完了
- **完了した競馬場**: 14競馬場（門別、姫路、大井、園田、高知、金沢、佐賀、名古屋、船橋、笠松、浦和、川崎、水沢、盛岡）
- **合計データ件数**: 約68万件
- **平均AUC**: 約0.77（範囲: 0.7459～0.8275）
- **除外**: 帯広（ばんえい競馬、データなし）
- `train_all_venues.py` - 全競馬場一括学習スクリプト
- `docs/train_all_venues_guide.md` - 実行ガイド
- `docs/phase3_completion_report.md` - **Phase 3完了レポート**

### Phase 4: 予定
3つの特化モデル生成（二値分類・ランキング・回帰）

### Phase 5: 予定
アンサンブル統合

## 使用方法

### Phase 1: モデル学習
```bash
# 依存ライブラリのインストール
pip install -r requirements.txt

# CSVから学習
python train_development.py data/sample.csv
```

### Phase 2: データ抽出
```bash
# PC-KEIBA Databaseから学習データを抽出

# === 基本版（過去走データなし）===
python extract_training_data.py --start-date 2022 --end-date 2024 --output training_data.csv

# === v2版（過去走データ統合版）- 推奨 ===
# 特定の競馬場（例: 大井=44）、2023-2024年
python extract_training_data_v2.py --keibajo 44 --start-date 2023 --end-date 2024 --output ooi_2023-2024_v3.csv

# テストモード（1000件制限）
python extract_training_data_v2.py --limit 1000 --output test_data_v2.csv

# 全地方競馬場
python extract_training_data_v2.py --start-date 2023 --end-date 2024 --output all_2023-2024_v3.csv
```

### Phase 3: 全15競馬場の一括学習
```bash
# 全15競馬場を一括学習（完了済みをスキップ）
python train_all_venues.py

# 完了済み競馬場も含めて全て実行
python train_all_venues.py --include-completed

# 特定の競馬場のみ実行（例: 名古屋=48）
python train_all_venues.py --venue 48

# データ抽出のみ実行（学習はスキップ）
python train_all_venues.py --skip-training

# 学習のみ実行（既存CSVを使用）
python train_all_venues.py --skip-extraction
```

詳細は `docs/train_all_venues_guide.md` を参照。

### v2版の特徴
- **過去走データを含む完全版**（前走〜5走前のデータを取得）
- **特徴量数**: 18個 → **45個** に増加
- **期待精度**: AUC 0.60-0.75 → **0.70-0.85**
- **取得データ**: 前走着順、前走タイム、前走馬体重、コーナー順位など27項目

### データベース構造調査
```bash
# PC-KEIBA Databaseのテーブル構造を確認
python inspect_database.py
```

---

## 📊 Phase 3 学習結果（14競馬場完了）

### 上位5競馬場

| 順位 | 競馬場 | データ件数 | AUC | Accuracy | Precision | Recall | F1 |
|------|--------|-----------|-----|----------|-----------|--------|-----|
| 1 | **🥇 門別** | 57,017件 | **0.8275** | 0.7749 | - | 0.5085 | 0.5829 |
| 2 | **🥈 姫路** | 18,071件 | **0.8148** | 0.7751 | - | - | - |
| 3 | **🥉 大井** | 27,219件 | **0.7957** | 0.7906 | 0.6466 | 0.3486 | 0.4530 |
| 4 | **園田** | 96,474件 | 0.7814 | 0.7620 | 0.6728 | 0.4100 | 0.5095 |
| 5 | **高知** | 71,984件 | 0.7803 | 0.7614 | - | - | - |

### 全14競馬場サマリー

| 指標 | 値 |
|------|-----|
| **合計データ件数** | 約68万件 |
| **平均AUC** | 約0.77 |
| **最高AUC** | 0.8275（門別） |
| **最低AUC** | 0.7459（水沢） |

**共通の特徴量重要度Top5:**
1. 騎手コード (kishu_code) - **圧倒的に重要**
2. 前走着順 (prev1_rank) - 過去走データの効果大
3. 2走前着順 (prev2_rank)
4. 開催月日 (kaisai_tsukihi) - 季節性
5. 出走頭数 (shusso_tosu)

**詳細**: `docs/phase3_completion_report.md` を参照

---

## ライセンス

MIT License
