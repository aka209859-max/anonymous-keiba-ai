# Phase 0-6 特徴量・欠損値処理の徹底調査完了レポート

**作成日**: 2026-02-06  
**ステータス**: ✅ 調査完了  
**次のアクション**: Phase 1スクリプト（prepare_features.py）実装

---

## 📋 目次

1. [調査の目的](#調査の目的)
2. [調査方法](#調査方法)
3. [調査結果サマリー](#調査結果サマリー)
4. [特徴量リストの完全版](#特徴量リストの完全版)
5. [欠損値処理の方針](#欠損値処理の方針)
6. [Race ID生成方法](#race-id生成方法)
7. [Phase 0の実装確認](#phase-0の実装確認)
8. [Phase 1の実装仕様](#phase-1の実装仕様)
9. [結論と次のステップ](#結論と次のステップ)

---

## 調査の目的

ユーザーからの指示:
- **Phase 1を今すぐ実装しますか？**: GitHubにどの特徴量を使用しているのか記載してあるはず → 全て確認してくること
- **欠損値の処理方針は以下で良いですか？**: PC-KEIBAマニュアル（https://pc-keiba.com/wp/manual-menu/）で確認すること
- **一切の妥協やハルシネーションは禁止**

調査対象:
1. GitHubリポジトリ内の実際の特徴量リスト
2. PC-KEIBAマニュアルの欠損値に関する情報
3. 既存スクリプト（extract_training_data_v2.py等）の実装内容
4. 調査報告書（Phase 0からPhase 1へ.md等）の技術的詳細

---

## 調査方法

### 1. GitHubリポジトリの調査

#### 実行したコマンド
```bash
# 特徴量関連のコミット履歴検索
git log --all --oneline --grep="特徴量|feature" | head -20

# 特徴量定義が含まれるスクリプト検索
find . -name "*.py" -type f ! -path "*/venv/*" ! -path "*/.git/*" | xargs grep -l "feature|特徴量|カラム|columns" | grep -E "(extract|train|phase)"

# ドキュメント検索
find . -name "*.md" -path "*/docs/*" | xargs grep -l "特徴量|feature list|カラム"
```

#### 発見したファイル
- `extract_training_data_v2.py`: 学習データ抽出スクリプト（過去走データ付き）
- `train_ranking_model.py`: ランキング学習スクリプト
- `docs/phase2_completion_report.md`: Phase 2完了報告
- `docs/Phase 0からPhase 1へ.md`: Phase 0-1の技術報告書

### 2. PC-KEIBAマニュアルの調査

#### 確認したURL
- メインメニュー: https://pc-keiba.com/wp/manual-menu/
- 学習データCSV出力: https://pc-keiba.com/wp/train-csv/

#### 調査結果
❌ **PC-KEIBAマニュアルに欠損値の詳細な説明は見つかりませんでした**

しかし、以下の代替資料から処理方針を確定できました:
- `docs/Phase 0からPhase 1へ.md`（調査報告書）
- `extract_training_data_v2.py`（実装コード）

---

## 調査結果サマリー

### ✅ 確認できた事実

| 項目 | 結果 |
|------|------|
| **特徴量数** | **49個**（識別情報除く） + target（目的変数）= 合計50個 |
| **過去走データ** | 前走1〜5（prev1〜prev5）、前走が新しいほど項目数が多い |
| **欠損値処理** | 過去走: 0埋め、物理量: 平均値補完、行削除: 禁止 |
| **Race ID** | `kaisai_nen || kaisai_tsukihi || keibajo_code || race_bango`（12桁） |
| **Phase 0** | ✅ 実装済み（extract_race_data.py） |
| **Phase 1** | ❌ 未実装（これから実装） |

---

## 特徴量リストの完全版

### SQLクエリから抽出（extract_training_data_v2.py）

```sql
SELECT 
    -- ============================================
    -- 目的変数（Phase 1では除外）
    -- ============================================
    CASE WHEN tr.kakutei_chakujun::INTEGER <= 3 THEN 1 ELSE 0 END AS target,
    
    -- ============================================
    -- 識別情報（6項目）
    -- ============================================
    tr.kaisai_nen,
    tr.kaisai_tsukihi,
    tr.keibajo_code,
    tr.race_bango,
    tr.ketto_toroku_bango,
    tr.umaban,
    
    -- ============================================
    -- レース情報（7項目）
    -- ============================================
    tr.kyori,                    -- 距離
    tr.track_code,               -- トラックコード（芝/ダート）
    tr.babajotai_code_shiba,     -- 馬場状態（芝）
    tr.babajotai_code_dirt,      -- 馬場状態（ダート）
    tr.tenko_code,               -- 天候コード
    tr.shusso_tosu,              -- 出走頭数
    tr.grade_code,               -- グレードコード
    
    -- ============================================
    -- 出馬情報（8項目）
    -- ============================================
    tr.wakuban,                  -- 枠番
    tr.seibetsu_code,            -- 性別コード
    tr.barei,                    -- 馬齢
    tr.futan_juryo,              -- 負担重量
    tr.kishu_code,               -- 騎手コード
    tr.chokyoshi_code,           -- 調教師コード
    tr.blinker_shiyo_kubun,      -- ブリンカー使用区分
    tr.tozai_shozoku_code,       -- 東西所属コード
    
    -- ============================================
    -- 馬情報（1項目）
    -- ============================================
    tr.moshoku_code,             -- 毛色コード
    
    -- ============================================
    -- 前走1（14項目）
    -- ============================================
    MAX(CASE WHEN pr.race_order = 1 THEN pr.kakutei_chakujun END) AS prev1_rank,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.soha_time END) AS prev1_time,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.kohan_3f END) AS prev1_last3f,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.kohan_4f END) AS prev1_last4f,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.corner_1 END) AS prev1_corner1,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.corner_2 END) AS prev1_corner2,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.corner_3 END) AS prev1_corner3,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.corner_4 END) AS prev1_corner4,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.bataiju END) AS prev1_weight,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.past_kyori END) AS prev1_kyori,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.past_keibajo END) AS prev1_keibajo,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.past_track END) AS prev1_track,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.past_baba_shiba END) AS prev1_baba_shiba,
    MAX(CASE WHEN pr.race_order = 1 THEN pr.past_baba_dirt END) AS prev1_baba_dirt,
    
    -- ============================================
    -- 前走2（6項目）
    -- ============================================
    MAX(CASE WHEN pr.race_order = 2 THEN pr.kakutei_chakujun END) AS prev2_rank,
    MAX(CASE WHEN pr.race_order = 2 THEN pr.soha_time END) AS prev2_time,
    MAX(CASE WHEN pr.race_order = 2 THEN pr.kohan_3f END) AS prev2_last3f,
    MAX(CASE WHEN pr.race_order = 2 THEN pr.bataiju END) AS prev2_weight,
    MAX(CASE WHEN pr.race_order = 2 THEN pr.past_kyori END) AS prev2_kyori,
    MAX(CASE WHEN pr.race_order = 2 THEN pr.past_keibajo END) AS prev2_keibajo,
    
    -- ============================================
    -- 前走3（3項目）
    -- ============================================
    MAX(CASE WHEN pr.race_order = 3 THEN pr.kakutei_chakujun END) AS prev3_rank,
    MAX(CASE WHEN pr.race_order = 3 THEN pr.soha_time END) AS prev3_time,
    MAX(CASE WHEN pr.race_order = 3 THEN pr.bataiju END) AS prev3_weight,
    
    -- ============================================
    -- 前走4（2項目）
    -- ============================================
    MAX(CASE WHEN pr.race_order = 4 THEN pr.kakutei_chakujun END) AS prev4_rank,
    MAX(CASE WHEN pr.race_order = 4 THEN pr.soha_time END) AS prev4_time,
    
    -- ============================================
    -- 前走5（2項目）
    -- ============================================
    MAX(CASE WHEN pr.race_order = 5 THEN pr.kakutei_chakujun END) AS prev5_rank,
    MAX(CASE WHEN pr.race_order = 5 THEN pr.soha_time END) AS prev5_time
    
FROM target_race tr
LEFT JOIN past_races pr ON tr.ketto_toroku_bango = pr.ketto_toroku_bango AND pr.race_order <= 5
GROUP BY ... (識別情報)
```

### 特徴量カテゴリ別集計

| カテゴリ | 特徴量名 | 個数 |
|---------|---------|------|
| **目的変数** | target | 1 |
| **識別情報** | kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, ketto_toroku_bango, umaban | 6 |
| **レース情報** | kyori, track_code, babajotai_code_shiba, babajotai_code_dirt, tenko_code, shusso_tosu, grade_code | 7 |
| **出馬情報** | wakuban, seibetsu_code, barei, futan_juryo, kishu_code, chokyoshi_code, blinker_shiyo_kubun, tozai_shozoku_code | 8 |
| **馬情報** | moshoku_code | 1 |
| **前走1** | prev1_rank, prev1_time, prev1_last3f, prev1_last4f, prev1_corner1, prev1_corner2, prev1_corner3, prev1_corner4, prev1_weight, prev1_kyori, prev1_keibajo, prev1_track, prev1_baba_shiba, prev1_baba_dirt | 14 |
| **前走2** | prev2_rank, prev2_time, prev2_last3f, prev2_weight, prev2_kyori, prev2_keibajo | 6 |
| **前走3** | prev3_rank, prev3_time, prev3_weight | 3 |
| **前走4** | prev4_rank, prev4_time | 2 |
| **前走5** | prev5_rank, prev5_time | 2 |
| **合計** | | **50個**（target含む） |
| **Phase 1で使用** | | **49個**（target除く） |

---

## 欠損値処理の方針

### 調査報告書（Phase 0からPhase 1へ.md）より抽出

#### 5.1 欠損値補完の優先順位 (Priority of Imputation)

競馬データにおける「欠損（NULL）」は、単なるデータ不備ではなく、重要な「情報」を含んでいる。

#### ✅ 優先度1：論理的0埋め (Logical Zero-Filling) [推奨]

**対象**: 過去走データ（prev1_rank, prev1_time, prev1_last3f等）

**理由**:
- 「新馬（デビュー戦）」や「長期休養明けで近走履歴がない」場合、過去走データは物理的に存在しない（NULL）
- これを「平均着順」で埋めると、「平均的な馬」として扱われてしまう
- しかし、新馬は「未知数」である
- LightGBMなどの木構造モデルは、値を0（あるいは負の異常値-1）に設定することで、「データがない」という状態自体を分岐条件として学習できる

**適用例**:
```python
df['prev1_rank'].fillna(0, inplace=True)
df['prev1_time'].fillna(0, inplace=True)
df['prev1_last3f'].fillna(0, inplace=True)
df['prev1_last4f'].fillna(0, inplace=True)
# 以下、prev1_*すべて同様
```

#### ✅ 優先度2：平均値/中央値補完 (Mean/Median Imputation)

**対象**: 馬体重（weight）、負担重量（futan_juryo）などの物理量

**理由**:
- 馬体重が0kgであることは物理的にあり得ない
- これらが欠損している（地方競馬のデータ不備など）場合、0を入れると外れ値として計算が狂う可能性がある

**適用例**:
```python
# 馬体重がNULLの場合、その馬の過去平均、あるいは性齢別平均値で補完
df['prev1_weight'].fillna(df['prev1_weight'].mean(), inplace=True)
df['futan_juryo'].fillna(df['futan_juryo'].mean(), inplace=True)
```

#### ❌ 優先度3：削除 (Dropping)

**対象**: Phase 1（予測）段階では原則禁止

**理由**:
- 予測フェーズでは、出走全馬のスコアを算出しなければならない
- 特定の馬のデータが欠損しているからといって行を削除すると、レース全体の予測（ランキングなど）が成立しなくなる

---

### Phase 1での実装コード例

```python
def preprocess_missing_values(df):
    """
    欠損値処理
    
    優先度1: 過去走データ → 0埋め
    優先度2: 物理量 → 平均値補完
    優先度3: 行削除 → 禁止
    """
    
    # ============================================
    # 優先度1: 過去走データ → 0埋め
    # ============================================
    past_race_columns = [
        'prev1_rank', 'prev1_time', 'prev1_last3f', 'prev1_last4f',
        'prev1_corner1', 'prev1_corner2', 'prev1_corner3', 'prev1_corner4',
        'prev1_kyori', 'prev1_keibajo', 'prev1_track', 
        'prev1_baba_shiba', 'prev1_baba_dirt',
        
        'prev2_rank', 'prev2_time', 'prev2_last3f',
        'prev2_kyori', 'prev2_keibajo',
        
        'prev3_rank', 'prev3_time',
        'prev4_rank', 'prev4_time',
        'prev5_rank', 'prev5_time',
    ]
    
    for col in past_race_columns:
        if col in df.columns:
            df[col].fillna(0, inplace=True)
            print(f"  - {col}: 0埋め完了")
    
    # ============================================
    # 優先度2: 物理量（馬体重） → 平均値補完
    # ============================================
    weight_columns = ['prev1_weight', 'prev2_weight', 'prev3_weight']
    
    for col in weight_columns:
        if col in df.columns:
            mean_value = df[col].mean()
            if pd.notna(mean_value):
                df[col].fillna(mean_value, inplace=True)
                print(f"  - {col}: 平均値補完完了（平均値: {mean_value:.2f}）")
            else:
                df[col].fillna(0, inplace=True)
                print(f"  - {col}: 全て欠損のため0埋め")
    
    # ============================================
    # 負担重量 → 平均値補完
    # ============================================
    if 'futan_juryo' in df.columns:
        mean_value = df['futan_juryo'].mean()
        if pd.notna(mean_value):
            df['futan_juryo'].fillna(mean_value, inplace=True)
            print(f"  - futan_juryo: 平均値補完完了（平均値: {mean_value:.2f}）")
    
    # ============================================
    # 優先度3: 行削除 → 実行しない
    # ============================================
    print("\n  ⚠️  行削除は実行しません（全馬の予測が必要）")
    
    return df
```

---

## Race ID生成方法

### 調査報告書（Phase 0からPhase 1へ.md）より抽出

#### Race IDフォーマット（12桁）

```
Race ID = YYYY + MM + DD + JJ + RR

- YYYY: 開催年（4桁）
- MM: 月（2桁）
- DD: 日（2桁）
- JJ: 競馬場コード（2桁）
- RR: レース番号（2桁）
```

#### 例

```
2023年2月4日 小倉競馬場 第12レース
→ ID = 202302041012
```

#### SQLでの生成

```sql
SELECT 
  CAST(kaisai_nen || kaisai_tsukihi || keibajo_code || LPAD(race_bango::TEXT, 2, '0') AS BIGINT) AS race_id
FROM nvd_ra
```

#### Pythonでの生成

```python
def generate_race_id(row):
    """Race IDを生成（12桁）"""
    kaisai_nen = str(row['kaisai_nen'])        # 4桁
    kaisai_tsukihi = str(row['kaisai_tsukihi']) # 4桁（MMDD）
    keibajo_code = str(row['keibajo_code']).zfill(2)  # 2桁
    race_bango = str(row['race_bango']).zfill(2)      # 2桁
    
    race_id = kaisai_nen + kaisai_tsukihi + keibajo_code + race_bango
    return int(race_id)

# 適用
df['race_id'] = df.apply(generate_race_id, axis=1)
```

---

## Phase 0の実装確認

### ✅ Phase 0: データ取得スクリプト（extract_race_data.py）

#### 実装済みファイル
- `scripts/phase0_data_acquisition/extract_race_data.py`

#### テスト実行結果
- **川崎競馬 2026-02-05**: 133レコード（12レース分）取得成功
- **出力先**: `E:/anonymous-keiba-ai/data/raw/2026/02/川崎_20260205_raw.csv`

#### 取得データ項目
- レース情報: 13項目
- 出馬情報: 10項目
- 過去走データ: 前走1〜5（各走で複数項目）

#### 欠損値の状況
- **前走1**: 一部欠損あり（初出走・2走目の馬）
- **前走2〜5**: より多くの欠損（キャリアが浅い馬）

**結論**: Phase 0は正常に動作しており、Phase 1の入力データとして使用可能 ✅

---

## Phase 1の実装仕様

### 目的

Phase 0の生データから、学習済みモデルが要求する49特徴量（識別情報除く）を作成する。

### 入力

- **Phase 0の生データ**: `data/raw/YYYY/MM/{keibajo}_{YYYYMMDD}_raw.csv`
- **例**: `data/raw/2026/02/川崎_20260205_raw.csv`

### 処理

1. **CSV読み込み**（Shift-JIS/UTF-8自動判定）
2. **欠損値処理**:
   - 過去走データ: 0埋め
   - 物理量: 平均値補完
3. **Race ID生成**:
   - `kaisai_nen || kaisai_tsukihi || keibajo_code || race_bango`
4. **特徴量フィルタリング**:
   - 49特徴量のみを抽出（識別情報 + レース情報 + 出馬情報 + 馬情報 + 過去走データ）
5. **データ型変換**:
   - 数値カラムは数値型に変換
   - カテゴリカラムは文字列のまま保持

### 出力

- **Phase 1の特徴量CSV**: `data/features/YYYY/MM/{keibajo}_{YYYYMMDD}_features.csv`
- **例**: `data/features/2026/02/川崎_20260205_features.csv`

### スクリプト構成

```python
# scripts/phase1_feature_engineering/prepare_features.py

import sys
import os
import pandas as pd
import argparse

def load_data(csv_file):
    """Phase 0のCSVを読み込み"""
    pass

def preprocess_missing_values(df):
    """欠損値処理"""
    pass

def generate_race_id(df):
    """Race IDを生成"""
    pass

def filter_features(df):
    """必要な特徴量のみを抽出"""
    pass

def save_features(df, output_file):
    """Phase 1の特徴量CSVを保存"""
    pass

def main():
    """メイン処理"""
    pass

if __name__ == '__main__':
    main()
```

---

## 結論と次のステップ

### ✅ 調査完了事項

1. **特徴量リスト**: GitHubリポジトリから完全に抽出完了（49個 + target）
2. **欠損値処理方針**: 調査報告書から確定（0埋め・平均値補完・行削除禁止）
3. **Race ID生成**: 12桁フォーマット確定
4. **Phase 0**: 実装済み・テスト済み・正常動作確認

### 🚀 次のアクション

**Phase 1スクリプト（prepare_features.py）を実装します！**

#### 実装手順
1. ✅ **このレポート作成** ← 今ここ
2. ⏳ **prepare_features.py実装**
3. ⏳ **川崎 2026-02-05データでテスト実行**
4. ⏳ **Phase 1完了レポート作成**

---

## 📎 参考資料

### GitHubリポジトリ
- `extract_training_data_v2.py`: 学習データ抽出スクリプト（過去走データ付き）
- `train_ranking_model.py`: ランキング学習スクリプト
- `docs/phase2_completion_report.md`: Phase 2完了報告

### 調査報告書
- `docs/Phase 0からPhase 1へ.md`: Phase 0-1の技術報告書（特徴量・欠損値処理の詳細）

### PC-KEIBAマニュアル
- メインメニュー: https://pc-keiba.com/wp/manual-menu/
- 学習データCSV出力: https://pc-keiba.com/wp/train-csv/

---

**作成者**: GenSpark AI Developer  
**最終更新**: 2026-02-06  
**ステータス**: ✅ 調査完了・Phase 1実装準備完了
