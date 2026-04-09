# 🏇 地方競馬AI予想システム - 毎日運用ガイド

## 📋 目次

1. [概要](#概要)
2. [前提条件](#前提条件)
3. [基本的な使い方](#基本的な使い方)
4. [実行例](#実行例)
5. [トラブルシューティング](#トラブルシューティング)
6. [ファイル構成](#ファイル構成)
7. [カスタマイズ](#カスタマイズ)

---

## 概要

毎日の競馬予想を **Note** と **ブッカーズ** 用に自動生成するためのスクリプトです。

### ワークフロー

```
1. Phase 0-5 の実行（データ取得→予測まで）
   ↓
2. DAILY_OPERATION の実行（配信用テキスト生成）
   ↓
3. Note / ブッカーズへコピー＆ペースト投稿
```

### 出力形式の違い

| 項目 | Note版 | ブッカーズ版 |
|------|--------|-------------|
| **見出し** | Markdown形式（#/##/###） | 絵文字で視認性重視 |
| **推奨馬** | 順位番号で表示 | 印（◎○▲△）で表示 |
| **買い目** | 箇条書き | セクション分け |
| **表示件数** | 全頭表示 | トップ5のみ |
| **ハッシュタグ** | なし | 自動生成 |

---

## 前提条件

### 必須ソフトウェア

- Python 3.8 以上
- pandas ライブラリ
- Phase 5 まで完了していること

### 必須ファイル

- `data/predictions/phase5/{競馬場名}_{YYYYMMDD}_ensemble.csv`
  - Phase 5 で生成されたアンサンブル予測ファイル
- `data/raw/{YYYY}/{MM}/{競馬場名}_{YYYYMMDD}_raw.csv`
  - Phase 0 で取得した生データ（馬名取得用）

---

## 基本的な使い方

### Windows の場合

```batch
cd E:\anonymous-keiba-ai
scripts\phase6_betting\DAILY_OPERATION.bat [競馬場コード] [対象日付]
```

### Linux / Mac の場合

```bash
cd /path/to/anonymous-keiba-ai
./scripts/phase6_betting/daily_operation.sh [競馬場コード] [対象日付]
```

### 競馬場コード一覧

| コード | 競馬場 | コード | 競馬場 | コード | 競馬場 |
|--------|--------|--------|--------|--------|--------|
| 30 | 門別 | 35 | 盛岡 | 36 | 水沢 |
| 42 | 浦和 | 43 | 船橋 | 44 | 大井 |
| 45 | 川崎 | 46 | 金沢 | 47 | 笠松 |
| 48 | 名古屋 | 50 | 園田 | 51 | 姫路 |
| 54 | 高知 | 55 | 佐賀 | | |

### 日付フォーマット

- `YYYY-MM-DD` 形式（例: `2026-02-08`）

---

## 実行例

### 例1: 佐賀競馬 2026年2月8日

```batch
REM Windows
scripts\phase6_betting\DAILY_OPERATION.bat 55 2026-02-08
```

```bash
# Linux / Mac
./scripts/phase6_betting/daily_operation.sh 55 2026-02-08
```

**出力ファイル:**
- `predictions/佐賀_20260208_note.txt`
- `predictions/佐賀_20260208_bookers.txt`

---

### 例2: 大井競馬 2026年2月10日

```batch
REM Windows
scripts\phase6_betting\DAILY_OPERATION.bat 44 2026-02-10
```

```bash
# Linux / Mac
./scripts/phase6_betting/daily_operation.sh 44 2026-02-10
```

**出力ファイル:**
- `predictions/大井_20260210_note.txt`
- `predictions/大井_20260210_bookers.txt`

---

### 例3: 川崎競馬 2026年2月10日

```batch
REM Windows
scripts\phase6_betting\DAILY_OPERATION.bat 45 2026-02-10
```

```bash
# Linux / Mac
./scripts/phase6_betting/daily_operation.sh 45 2026-02-10
```

**出力ファイル:**
- `predictions/川崎_20260210_note.txt`
- `predictions/川崎_20260210_bookers.txt`

---

## トラブルシューティング

### エラー: 入力ファイルが見つかりません

**原因:**
- Phase 5 までの処理が完了していない
- ファイル名が間違っている

**解決方法:**
```batch
REM 1. Phase 5 まで実行されているか確認
dir data\predictions\phase5\

REM 2. ensemble.csv ファイルが存在するか確認
dir data\predictions\phase5\佐賀_20260208_ensemble.csv
```

---

### エラー: 馬名が「未登録」と表示される

**原因:**
- raw CSV ファイルが見つからない
- raw CSV に必要なカラムが不足している

**解決方法:**
```batch
REM 1. raw CSV ファイルが存在するか確認
dir data\raw\2026\02\佐賀_20260208_raw.csv

REM 2. raw CSV の内容を確認
type data\raw\2026\02\佐賀_20260208_raw.csv | more
```

必須カラム:
- `kaisai_nen` (開催年)
- `kaisai_tsukihi` (開催月日)
- `race_bango` (レース番号)
- `umaban` (馬番)
- `bamei` (馬名)

---

### エラー: Python が見つかりません

**Windows の場合:**
```batch
REM Python がインストールされているか確認
python --version

REM パスが通っているか確認
where python
```

**Linux / Mac の場合:**
```bash
# Python がインストールされているか確認
python3 --version

# パスが通っているか確認
which python3
```

---

## ファイル構成

```
anonymous-keiba-ai/
├── scripts/
│   └── phase6_betting/
│       ├── DAILY_OPERATION.bat          # Windows用実行バッチ
│       ├── daily_operation.sh           # Linux/Mac用実行スクリプト
│       ├── generate_distribution_note.py    # Note用生成スクリプト
│       ├── generate_distribution_bookers.py # ブッカーズ用生成スクリプト
│       └── README_DAILY_OPERATION.md    # このファイル
├── data/
│   ├── raw/                             # Phase 0 生データ
│   └── predictions/
│       └── phase5/                      # Phase 5 予測結果（入力）
└── predictions/                         # 配信用テキスト（出力）
```

---

## カスタマイズ

### 出力先ディレクトリを変更したい

**DAILY_OPERATION.bat を編集:**

```batch
REM 変更前
set NOTE_TXT=predictions\%KEIBA_NAME%_%DATE_SHORT%_note.txt

REM 変更後（例: output フォルダに出力）
set NOTE_TXT=output\%KEIBA_NAME%_%DATE_SHORT%_note.txt
```

**daily_operation.sh を編集:**

```bash
# 変更前
NOTE_TXT="predictions/${KEIBA_NAME}_${DATE_SHORT}_note.txt"

# 変更後（例: output フォルダに出力）
NOTE_TXT="output/${KEIBA_NAME}_${DATE_SHORT}_note.txt"
```

---

### ランク評価基準を変更したい

**generate_distribution_note.py と generate_distribution_bookers.py を編集:**

```python
def assign_rank_label(score):
    """スコアに基づいてランクラベルを付与"""
    if score >= 0.80:
        return 'S'
    elif score >= 0.70:
        return 'A'
    elif score >= 0.60:
        return 'B'
    elif score >= 0.50:
        return 'C'
    else:
        return 'D'
```

閾値を変更することで、ランク付けをカスタマイズできます。

---

### 複数競馬場の一括処理

**バッチ処理スクリプトの例（Windows）:**

```batch
@echo off
REM 2026年2月10日の複数競馬場を一括処理

call scripts\phase6_betting\DAILY_OPERATION.bat 44 2026-02-10
call scripts\phase6_betting\DAILY_OPERATION.bat 45 2026-02-10
call scripts\phase6_betting\DAILY_OPERATION.bat 43 2026-02-10

echo すべての競馬場の処理が完了しました！
```

**または、BATCH_OPERATION.bat を使用（推奨）:**

```batch
REM 自動的に開催中の競馬場を検出して処理
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-10 wed
```

**出力される各競馬場別のファイル:**
- `predictions/大井_20260210_note.txt` + `predictions/大井_20260210_bookers.txt`
- `predictions/川崎_20260210_note.txt` + `predictions/川崎_20260210_bookers.txt`
- `predictions/船橋_20260210_note.txt` + `predictions/船橋_20260210_bookers.txt`

**バッチ処理スクリプトの例（Linux/Mac）:**

```bash
#!/bin/bash
# 2026年2月10日の複数競馬場を一括処理

./scripts/phase6_betting/daily_operation.sh 44 2026-02-10
./scripts/phase6_betting/daily_operation.sh 45 2026-02-10
./scripts/phase6_betting/daily_operation.sh 43 2026-02-10

echo "すべての競馬場の処理が完了しました！"
```

---

## よくある質問（FAQ）

### Q1. 毎日何時に実行すればいいですか？

**A:** レース当日の朝（開催前）に実行することをおすすめします。  
前日夜に翌日分を実行することも可能です。

---

### Q2. 同じ日に複数の競馬場がある場合は？

**A:** 競馬場コードを変えて複数回実行してください。

```batch
REM 例: 2026年2月10日は大井・川崎・船橋が開催
scripts\phase6_betting\DAILY_OPERATION.bat 44 2026-02-10
scripts\phase6_betting\DAILY_OPERATION.bat 45 2026-02-10
scripts\phase6_betting\DAILY_OPERATION.bat 43 2026-02-10
```

---

### Q3. 生成されたテキストを修正してもいいですか？

**A:** はい、問題ありません。  
コピー＆ペーストする前に手動で調整してください。

---

### Q4. Note と ブッカーズ、どちらも投稿する必要がありますか？

**A:** 用途に応じて選択してください。
- **Note**: 記事形式で詳細に説明したい場合
- **ブッカーズ**: 簡潔に買い目を提示したい場合

両方投稿することも可能です。

---

## サポート

問題が発生した場合は、以下を確認してください:

1. **ログファイル:** 実行時のエラーメッセージを確認
2. **GitHub Issues:** 既知の問題があるか確認
3. **開発レポート:** `DEVELOPMENT_REPORT_2026_02_08.md` を参照

---

## ライセンス

本プロジェクトは内部利用を前提としています。  
外部への配布や商用利用は禁止されています。

---

## 更新履歴

- **2026-02-08**: 初版作成
  - Note用フォーマット対応
  - ブッカーズ用フォーマット対応
  - Windows/Linux 両対応の実行スクリプト追加

---

## 関連ドキュメント

- [開発レポート](../../DEVELOPMENT_REPORT_2026_02_08.md)
- [Phase 3-5 実装ガイド](../../docs/)
- [Note投稿用フォーマット仕様](./地方競馬AI予想におけるNoteプラットフォームへの投稿フォーマット最.md)

---

**🏇 Happy Betting! 🎯**
