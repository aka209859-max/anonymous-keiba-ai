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

### Phase 2: 🔄 進行中
学習データ抽出SQL作成
- `extract_training_data.py` - データ抽出スクリプト
- `inspect_database.py` - DB構造調査ツール
- `docs/sql_design.md` - SQL設計書

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
python extract_training_data.py --start-date 2022 --end-date 2024 --output training_data.csv

# 特定の競馬場のみ（例: 大井=44）
python extract_training_data.py --keibajo 44 --output ooi_data.csv

# テストモード（レコード数制限）
python extract_training_data.py --limit 1000 --output test_data.csv
```

### データベース構造調査
```bash
# PC-KEIBA Databaseのテーブル構造を確認
python inspect_database.py
```

## ライセンス

MIT License
