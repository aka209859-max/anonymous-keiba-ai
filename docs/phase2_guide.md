# フェーズ2: データ抽出ガイド

## 概要
PC-KEIBA Databaseから地方競馬の学習データを抽出し、CSVファイルを生成します。

## 前提条件

### 1. PC-KEIBAのインストール
- PC-KEIBA Database（PostgreSQL）が動作していること
- データベース接続情報:
  - ホスト: 127.0.0.1
  - ポート: 5432
  - DB名: pckeiba
  - ユーザー: postgres
  - パスワード: postgres123

### 2. Pythonライブラリ
```bash
pip install -r requirements.txt
```

## データ抽出の手順

### ステップ1: データベース構造の確認
```bash
python inspect_database.py
```

このスクリプトは以下を出力します:
- テーブル一覧
- 主要テーブル（nvd_ra, nvd_se, nvd_um, nvd_kj, nvd_ch）の詳細
- カラム名とデータ型
- サンプルデータ

**重要**: 実際のカラム名がドキュメントと異なる場合、`extract_training_data.py` のSQLクエリを修正する必要があります。

### ステップ2: テストデータの抽出
まず小規模データでテストします:

```bash
# 1000件のみ抽出（テスト）
python extract_training_data.py --limit 1000 --output test_data.csv
```

出力を確認:
```bash
# CSVの先頭を表示
head -20 test_data.csv

# レコード数を確認
wc -l test_data.csv
```

### ステップ3: 特定競馬場のデータ抽出
特定の競馬場に絞ってデータを抽出:

```bash
# 大井競馬場（コード: 44）のデータ
python extract_training_data.py --keibajo 44 --start-date 2022 --end-date 2024 --output ooi_2022-2024.csv

# 門別競馬場（コード: 30）のデータ
python extract_training_data.py --keibajo 30 --start-date 2023 --end-date 2024 --output monbetsu_2023-2024.csv
```

### ステップ4: 全地方競馬場のデータ抽出
```bash
# 全地方競馬場、2022-2024年のデータ
python extract_training_data.py --start-date 2022 --end-date 2024 --output training_data_all.csv
```

**注意**: 全競馬場のデータは非常に大きくなる可能性があります（数十万〜数百万レコード）。

## 競馬場コード一覧

| コード | 競馬場名 | 地域 |
|--------|----------|------|
| 30 | 門別 | 北海道 |
| 33 | 帯広 | 北海道（ばんえい） |
| 35 | 盛岡 | 岩手 |
| 36 | 水沢 | 岩手 |
| 42 | 浦和 | 埼玉（南関東） |
| 43 | 船橋 | 千葉（南関東） |
| 44 | 大井 | 東京（南関東） |
| 45 | 川崎 | 神奈川（南関東） |
| 46 | 金沢 | 石川 |
| 47 | 笠松 | 岐阜 |
| 48 | 名古屋 | 愛知 |
| 50 | 園田 | 兵庫 |
| 51 | 姫路 | 兵庫 |
| 54 | 高知 | 高知 |
| 55 | 佐賀 | 佐賀 |

## 抽出されるデータ

### 目的変数
- **target**: 3着以内なら `1`、それ以外は `0`

### 識別情報
- kaisai_nen: 開催年
- kaisai_tsukihi: 開催月日
- keibajo_code: 競馬場コード
- race_bango: レース番号
- uma_code: 馬コード
- umaban: 馬番

### レース情報
- kyori: 距離
- track_code: トラックコード
- baba_jotai_code: 馬場状態コード
- tenkou_code: 天候コード
- tosu: 頭数
- grade_code: グレードコード

### 出馬情報
- wakuban: 枠番
- seibetsu_code: 性別コード
- barei: 馬齢
- futan_juryo: 負担重量
- kishu_code: 騎手コード
- chokyoshi_code: 調教師コード
- blinker: ブリンカー
- zokusho: 所属

### 馬情報
- keiro_code: 毛色コード
- sire_code: 種牡馬コード
- broodmare_sire_code: 母父馬コード

### 過去走データ（前走1〜5）
各前走について以下の情報:
- chakujun: 着順
- time_sa: タイム差
- agari_3f: 上がり3F
- kyori: 距離
- keibajo: 競馬場
- baba: 馬場状態
- bataiju: 馬体重

## トラブルシューティング

### エラー: データベース接続失敗
```
❌ データベース接続エラー: could not connect to server
```

**対処法**:
1. PC-KEIBAが起動しているか確認
2. PostgreSQLが起動しているか確認
3. データベース接続情報が正しいか確認（extract_training_data.py の DB_CONFIG）

### エラー: カラムが見つからない
```
❌ データ抽出エラー: column "zensou1_chakujun" does not exist
```

**対処法**:
1. `inspect_database.py` で実際のカラム名を確認
2. `extract_training_data.py` のSQLクエリを修正

### 警告: 欠損率が高い
```
警告: 欠損率80%超のカラム
```

**対処法**:
- これは正常な動作です（過去走データは馬によって存在しない場合がある）
- Borutaが自動的に不要なカラムを削除します

### CSVがShift-JISで保存できない
```
❌ CSV保存エラー: 'shift_jis' codec can't encode character
```

**対処法**:
- スクリプトが自動的にUTF-8で保存します
- 学習時は `encoding='shift-jis'` の代わりに `encoding='utf-8'` を使用してください

## 次のステップ

データ抽出が完了したら、フェーズ1の学習プログラムで学習を実行します:

```bash
# 学習実行
python train_development.py training_data_all.csv

# 出力ファイル
# - training_data_all_model.txt: 学習済みモデル
# - training_data_all_model.png: 特徴量重要度グラフ
# - training_data_all_score.txt: 評価指標
```

## 推奨される学習戦略

### 1. 競馬場別モデル
競馬場ごとに特性が異なるため、競馬場別にモデルを作成することを推奨:

```bash
# 南関東4場（浦和・船橋・大井・川崎）
for code in 42 43 44 45; do
    python extract_training_data.py --keibajo $code --output keibajo_${code}.csv
    python train_development.py keibajo_${code}.csv
done
```

### 2. 地域別モデル
複数の競馬場をまとめて学習:

```bash
# 南関東モデル（42,43,44,45）
# SQLで WHERE ra.keibajo_code IN ('42','43','44','45') を指定

# 北海道モデル（30,33）
# 東海モデル（47,48）
```

### 3. 全体モデル
全競馬場を統合したモデル（計算時間が長い）:

```bash
python extract_training_data.py --start-date 2023 --end-date 2024 --output all_2023-2024.csv
python train_development.py all_2023-2024.csv
```

**注意**: Borutaの処理時間は数時間〜数日かかる可能性があります。
