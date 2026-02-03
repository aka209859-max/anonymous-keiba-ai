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

### Phase 3: 予定
3つの特化モデル生成（二値分類・ランキング・回帰）

### Phase 4: 予定
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

## ライセンス

MIT License
