# Phase 1: データ取得・抽出 ディープサーチ指示文

## 目的
PC-KEIBAまたは地方競馬DATAから予測用の出走情報を取得し、Phase 3-5で使用する特徴量CSVを作成する正しい手順を確認する。

## 前提条件
- PC-KEIBA Database（PostgreSQL）がローカルで稼働中
- または地方競馬DATAのアクセス権がある
- 14競馬場の学習済みモデルが `E:/anonymous-keiba-ai/models/` に存在

## 検証項目

### 1. データソースの確認
**質問:**
- PC-KEIBAのテーブル構造は？
  - `nvd_se`（出馬表）のカラム一覧
  - `nvd_ra`（レース情報）のカラム一覧
  - `nvd_um`（馬情報）のカラム一覧
- 地方競馬DATAの場合、どのファイル形式でデータを取得するか？
  - CSV形式？API？
  - 必要なデータ項目は？

### 2. 必要な特徴量の確認
**学習済みモデルが期待する特徴量リストを抽出:**

```python
import lightgbm as lgb

# 例: 大井競馬場の二値分類モデル
model = lgb.Booster(model_file='E:/anonymous-keiba-ai/models/binary/ooi_2023-2025_v3_model.txt')
feature_names = model.feature_name()
print(f"モデルが期待する特徴量: {len(feature_names)}個")
print(feature_names)
```

**検証すべき点:**
- 各モデル（binary/ranking/regression）で特徴量リストは同じか？
- 14競馬場で特徴量リストは共通か？それとも競馬場ごとに異なるか？
- 特徴量の総数は何個か？（Phase 1完了報告では50個と記載されているが、実際は？）

### 3. データ抽出SQLの確認
**既存の `extract_training_data_v2.py` の処理内容:**

```sql
-- 予測用データ抽出のSQL例（簡略版）
SELECT 
    -- レース情報
    ra.kaisai_nen,
    ra.kaisai_tsukihi,
    ra.keibajo_code,
    ra.race_bango,
    -- 出馬情報
    se.ketto_toroku_bango,
    se.umaban,
    se.wakuban,
    se.seibetsu_code,
    se.barei,
    se.futan_juryo,
    -- ... その他50個の特徴量
FROM nvd_ra ra
INNER JOIN nvd_se se ON ...
WHERE ra.keibajo_code = '44'  -- 大井競馬場
  AND ra.kaisai_nen = '2026'
  AND ra.kaisai_tsukihi = '20260207'  -- 2026年2月7日
```

**検証すべき点:**
- 予測用データ（当日/翌日出走情報）の取得方法は？
- 過去走データ（prev1〜prev5）の取得ロジックは？
  - `ROW_NUMBER()` を使った自己JOIN？
  - または別テーブルから取得？
- 欠損値の扱いは？
  - 前走データがない新馬はどうするか？
  - 欠損特徴量は 0 埋め？平均値埋め？

### 4. 特徴量エンジニアリングの確認
**モデルが期待する特徴量と、PC-KEIBAの生データのマッピング:**

| モデル特徴量 | PC-KEIBAカラム | 変換処理 | 備考 |
|------------|--------------|---------|------|
| `kyori` | `ra.kyori` | そのまま | 距離（m） |
| `track_code` | `ra.track_code` | そのまま | 1=ダート、2=芝 |
| `babajotai_code_dirt` | `ra.babajotai_code` | track_code=1の場合のみ | 1=良、2=稍重、3=重、4=不良 |
| `prev1_rank` | 過去走テーブル | 前走1着順 | ROW_NUMBER()で取得 |
| ... | ... | ... | ... |

**検証すべき点:**
- モデル特徴量50個すべてのマッピングを確認
- 特徴量の型変換は必要か？（文字列→数値など）
- カテゴリ変数のエンコーディングは？（Label Encoding? One-Hot Encoding?）

### 5. 出力フォーマットの確認
**Phase 1の出力CSVフォーマット:**

```csv
kaisai_nen,kaisai_tsukihi,keibajo_code,race_bango,ketto_toroku_bango,umaban,kyori,track_code,...(50個の特徴量)
2026,20260207,44,1,2023123456,1,1200,1,...
2026,20260207,44,1,2023123457,2,1200,1,...
...
```

**検証すべき点:**
- カラム順序は重要か？
- カラム名は完全一致が必要か？
- エンコーディングは Shift-JIS か UTF-8 か？

### 6. 実行スクリプトの確認
**Phase 1 実行スクリプト（作成すべきもの）:**

```python
# scripts/phase1_feature_engineering/prepare_features.py
# 目的: PC-KEIBAから当日/翌日の出走情報を取得し、特徴量CSVを作成

import argparse
import pandas as pd
import psycopg2

def extract_race_features(keibajo_code, race_date):
    """
    PC-KEIBAから指定競馬場・日付の出走情報を取得
    
    Args:
        keibajo_code: 競馬場コード（例: '44'=大井）
        race_date: レース開催日（例: '20260207'）
    
    Returns:
        DataFrame: 特徴量50個を含むCSV形式のデータ
    """
    # SQLクエリでデータ取得
    # 特徴量変換
    # 欠損値補完
    # CSV出力
    pass

if __name__ == "__main__":
    # 使用例
    df = extract_race_features(keibajo_code='44', race_date='20260207')
    df.to_csv('data/features/2026/02/ooi_20260207_features.csv', 
              index=False, encoding='shift_jis')
```

**検証すべき点:**
- 既存の `extract_training_data_v2.py` を予測用に修正すればよいか？
- target カラム（3着以内=1）は予測時には不要だが、含めるべきか？
- race_id カラムは Phase 4 ランキング予測で必要か？

### 7. 実行フロー
```
PC-KEIBA Database
    ↓ SQL抽出（当日/翌日出走情報）
生データ（nvd_ra, nvd_se, 過去走）
    ↓ 特徴量エンジニアリング（50個の特徴量を作成）
data/features/2026/02/ooi_20260207_features.csv
    ↓
Phase 3 へ渡す
```

## 成果物
1. **特徴量対応表**: `scripts/phase1_feature_engineering/feature_mapping.csv`
   - モデル特徴量名 | PC-KEIBAカラム名 | 変換処理 | データ型
2. **実行スクリプト**: `scripts/phase1_feature_engineering/prepare_features.py`
3. **実行ガイド**: `docs/phase1_execution_guide.md`

## 次のアクション
Phase 1の実行方法が確認できたら、Phase 3-6の指示文を作成する。
