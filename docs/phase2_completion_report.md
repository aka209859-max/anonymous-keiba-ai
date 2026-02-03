# フェーズ2完了報告

## 📋 概要
PC-KEIBA Databaseから地方競馬の学習データを抽出するスクリプトとSQLクエリを実装しました。

## ✅ 完了項目

### 1. データ抽出スクリプト
- **extract_training_data.py** (310行)
  - PC-KEIBA Databaseからデータを抽出してCSVに出力
  - 柔軟なオプション（競馬場、期間、レコード数制限）
  - データ前処理機能（型変換、欠損値確認）
  - Shift-JIS/UTF-8両対応

- **inspect_database.py** (159行)
  - データベース構造調査ツール
  - テーブル一覧とカラム情報の表示
  - サンプルデータの確認

### 2. SQL設計書
- **docs/sql_design.md** (244行)
  - データ抽出の基本方針
  - SQLクエリテンプレート
  - 除外項目と使用項目の明確化
  - 拡張版（統計量）の設計

### 3. ドキュメント
- **docs/phase2_guide.md** (214行)
  - データ抽出の手順
  - 競馬場コード一覧
  - トラブルシューティング
  - 推奨される学習戦略

## 📊 実装内容

### データ抽出の基本方針
1. **地方競馬のみ**: 15競馬場（門別、帯広、盛岡、水沢、浦和、船橋、大井、川崎、金沢、笠松、名古屋、園田、姫路、高知、佐賀）
2. **平地レースのみ**: 障害レースは除外
3. **前日確定データのみ**: 
   - ❌ 除外: 当日オッズ、当日馬体重、当日人気
   - ✅ 使用: 過去走、血統、騎手、調教師、コース情報

### 抽出データ項目
- **目的変数**: 3着以内=1、それ以外=0
- **レース情報**: 距離、トラック、馬場状態、天候、頭数、グレード
- **出馬情報**: 枠番、性別、馬齢、負担重量、騎手、調教師、ブリンカー
- **馬情報**: 毛色、種牡馬、母父馬
- **過去走データ**: 前走1〜5の着順、タイム差、上がり3F、距離、競馬場、馬場状態、馬体重

## 🚀 使用方法

### 基本的な使い方
```bash
# 全地方競馬場、2022-2024年
python extract_training_data.py --start-date 2022 --end-date 2024 --output training_data.csv

# 特定の競馬場（大井=44）
python extract_training_data.py --keibajo 44 --output ooi_data.csv

# テストモード（1000件のみ）
python extract_training_data.py --limit 1000 --output test_data.csv
```

### データベース構造の確認
```bash
python inspect_database.py
```

### 学習の実行
```bash
# データ抽出
python extract_training_data.py --keibajo 44 --output ooi_data.csv

# 学習実行
python train_development.py ooi_data.csv
```

## 🎯 推奨される学習戦略

### 1. 競馬場別モデル
競馬場ごとに特性が大きく異なるため、個別にモデルを作成することを推奨:
```bash
# 大井競馬場
python extract_training_data.py --keibajo 44 --output ooi.csv
python train_development.py ooi.csv
```

### 2. 地域別モデル
複数の競馬場を統合:
- **南関東モデル** (浦和・船橋・大井・川崎)
- **北海道モデル** (門別・帯広)
- **東海モデル** (笠松・名古屋)

### 3. 全体モデル
全競馬場を統合（計算時間が長い）:
```bash
python extract_training_data.py --start-date 2023 --end-date 2024 --output all_2023-2024.csv
python train_development.py all_2023-2024.csv
```

## ⚠️ 注意事項

### 1. Borutaの処理時間
全ファクター（数百カラム）を入れると、Borutaの計算に数時間〜数日かかる可能性があります。最初は小規模データ（1競馬場、1年分、1000件）でテストすることを推奨します。

### 2. データベース接続
このスクリプトはローカルのPC-KEIBA Database（PostgreSQL）への接続が必要です。接続情報:
- ホスト: 127.0.0.1
- ポート: 5432
- DB名: pckeiba
- ユーザー: postgres
- パスワード: postgres123

### 3. カラム名の確認
PC-KEIBAの実際のテーブル定義を確認してから実行してください:
```bash
python inspect_database.py
```

実際のカラム名がドキュメントと異なる場合、`extract_training_data.py` のSQLクエリを修正する必要があります。

## 📝 技術的な詳細

### SQLクエリの構造
```sql
SELECT 
    CASE WHEN se.chakujun::INTEGER <= 3 THEN 1 ELSE 0 END AS target,
    -- レース情報
    ra.kyori, ra.track_code, ra.baba_jotai_code, ...
    -- 出馬情報
    se.wakuban, se.barei, se.futan_juryo, ...
    -- 馬情報
    um.sire_code, um.broodmare_sire_code, ...
    -- 過去走データ
    se.zensou1_chakujun, se.zensou1_time_sa, ...
FROM nvd_ra ra
INNER JOIN nvd_se se ON (...)
LEFT JOIN nvd_um um ON (...)
WHERE ra.keibajo_code IN ('30', '33', ..., '55')
  AND se.chakujun IS NOT NULL
  AND se.chakujun NOT IN ('取消', '除外', '中止', '失格')
ORDER BY ra.kaisai_nen DESC, ...
```

### データ前処理
1. 目的変数の分布確認
2. 識別カラムと特徴量カラムの分離
3. 数値変換（可能なものは自動変換）
4. 欠損値の確認と警告

## 🔗 関連リンク
- **Pull Request**: https://github.com/aka209859-max/anonymous-keiba-ai/pull/1
- **PR Comment**: https://github.com/aka209859-max/anonymous-keiba-ai/pull/1#issuecomment-3842425328

## 📅 次のフェーズ: フェーズ3

フェーズ3では、以下の3つの特化モデルを作成します:

### 1. 二値分類モデル（Binary）
- 目的: 3着以内に入る確率を予測
- 既存の `train_development.py` をそのまま使用

### 2. ランキング学習モデル（LambdaRank）
- 目的: レース内の相対順位を学習
- `train_development.py` を元に `lambdarank_train.py` を作成

### 3. 回帰分析モデル（Regression）
- 目的: 走破タイムを予測
- `train_development.py` を元に `regression_train.py` を作成

### アンサンブル統合（フェーズ4）
3つのモデルの予測結果を統合し、最強の買い目を決定します。

---

**作成日**: 2026-02-03  
**ステータス**: ✅ 完了  
**次のアクション**: フェーズ3の実装開始
