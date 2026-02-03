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

- **Phase 1**: Development Ver. コード作成（Boruta + Optuna）
- **Phase 2**: 学習データ抽出SQL作成
- **Phase 3**: 3つの特化モデル生成（二値分類・ランキング・回帰）
- **Phase 4**: アンサンブル統合

## ライセンス

MIT License
