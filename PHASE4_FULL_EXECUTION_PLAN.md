# Phase 4 完全実行計画書

**作成日**: 2026-02-04  
**目的**: 最強の地方競馬予想システムの構築 - Phase 4（ランキング学習・回帰分析・アンサンブル統合）の完全実行

---

## 📊 現状確認

### ✅ 完了済み
- Phase 1-3: 二値分類モデルの学習（10競馬場）
- Phase 4.5: 2026年1月シミュレーション実行（的中率検証）
- スクリプト実装: `train_ranking_model.py`, `train_regression_model.py`, `ensemble_model.py`

### ⚠️ 未実施
- ランキング学習モデルの学習（10競馬場）
- 回帰分析モデルの学習（10競馬場）
- アンサンブル予測の実行（3モデル統合）

---

## 🎯 Phase 4 完全実行の目標

### 最終成果物
1. **ランキングモデル**: 各競馬場で相対順位を学習（10競馬場 × 1モデル = 10モデル）
2. **回帰モデル**: 各競馬場で走破タイムを予測（10競馬場 × 1モデル = 10モデル）
3. **アンサンブル予測**: 2026年1月データで3モデル統合予測を実行
4. **評価レポート**: 的中率・推奨度別分析（◎本命/○対抗/▲単穴/△連下/×評価低/消去）

### 期待効果
- **多角的予測**: 二値分類（確率）+ ランキング（順位）+ 回帰（タイム）の3つの視点
- **精度向上**: 各モデルの強みを組み合わせて弱点を補完
- **実戦投入可能**: 買い目の優先順位を明確化（◎○▲△×）

---

## 📋 実行ステップ（全体フロー）

### Step 0: 前提確認
- Windows環境: `E:\anonymous-keiba-ai`
- データベース: PostgreSQL (localhost:5432, database: pckeiba)
- 既存モデル: 二値分類モデル（Phase 3で学習済み）
  - `ooi_2023-2024_v3_model.txt` (大井 32特徴量)
  - `funabashi_2020-2025_v3_model.txt` (船橋 34特徴量)
  - 他8競馬場のモデル

### Step 1: データ準備（ランキング学習用）
**目的**: `race_id` カラムを追加したデータセットを作成

#### 1-1. 既存データの修正（推奨方法）
既存のCSVファイルに `race_id` を追加する：

```python
# add_race_id_to_csv.py (新規作成)
import pandas as pd
import sys

csv_file = sys.argv[1]  # 例: ooi_2023-2024_v3.csv
df = pd.read_csv(csv_file, encoding='shift-jis')

# race_idを作成
df['race_id'] = (
    df['kaisai_nen'].astype(str) + 
    df['kaisai_tsukihi'].astype(str).str.zfill(4) + 
    df['keibajo_code'].astype(str) + 
    df['race_bango'].astype(str).str.zfill(2)
)

# 保存
output_file = csv_file.replace('.csv', '_with_race_id.csv')
df.to_csv(output_file, index=False, encoding='shift-jis')
print(f"✓ 保存完了: {output_file}")
print(f"  - レース数: {df['race_id'].nunique():,}件")
print(f"  - データ件数: {len(df):,}件")
```

**実行コマンド**:
```bash
cd E:\anonymous-keiba-ai
python add_race_id_to_csv.py ooi_2023-2024_v3.csv
python add_race_id_to_csv.py funabashi_2020-2025_v3.csv
# ... 他8競馬場も同様
```

#### 1-2. SQLから再抽出（代替方法）
`extract_training_data_v2.py` を修正して race_id を追加：

```python
# extract_training_data_v2.py の修正箇所
def create_query_with_past_races(...):
    query = f"""
    WITH target_race AS (
        SELECT 
            -- race_idを追加
            CONCAT(r.kaisai_nen, LPAD(r.kaisai_tsukihi::text, 4, '0'), r.keibajo_code, LPAD(r.race_bango::text, 2, '0')) AS race_id,
            
            -- 既存のカラム
            CASE WHEN s.kakutei_chakujun::int <= 3 THEN 1 ELSE 0 END AS target,
            r.kaisai_nen,
            ...
```

### Step 2: データ準備（回帰分析用）
**目的**: `target` を走破タイム（秒）に変更したデータセットを作成

#### 2-1. 既存データの修正（推奨方法）
既存のCSVファイルの target を走破タイムに変更：

```python
# convert_target_to_time.py (新規作成)
import pandas as pd
import sys

csv_file = sys.argv[1]  # 例: ooi_2023-2024_v3.csv
df = pd.read_csv(csv_file, encoding='shift-jis')

# targetを走破タイムに変更（time カラムが存在すると仮定）
if 'time' in df.columns:
    # timeは1/10秒単位 → 秒に変換
    df['target'] = df['time'] / 10.0
elif 'prev1_time' in df.columns:
    # 前走タイムを使用（応急処置）
    df['target'] = df['prev1_time']
else:
    print("エラー: タイムカラムが見つかりません")
    sys.exit(1)

# 欠損値を除去
df = df[df['target'].notna()]
df = df[df['target'] > 0]

# 保存
output_file = csv_file.replace('.csv', '_time.csv')
df.to_csv(output_file, index=False, encoding='shift-jis')
print(f"✓ 保存完了: {output_file}")
print(f"  - データ件数: {len(df):,}件")
print(f"  - タイム範囲: {df['target'].min():.2f}秒 ~ {df['target'].max():.2f}秒")
```

**実行コマンド**:
```bash
cd E:\anonymous-keiba-ai
python convert_target_to_time.py ooi_2023-2024_v3.csv
python convert_target_to_time.py funabashi_2020-2025_v3.csv
# ... 他8競馬場も同様
```

#### 2-2. SQLから再抽出（代替方法）
`extract_training_data_v2.py` を修正して time を target に：

```python
# target を走破タイムに変更
query = f"""
WITH target_race AS (
    SELECT 
        s.time / 10.0 AS target,  -- 走破タイム（秒）
        r.kaisai_nen,
        ...
```

### Step 3: ランキングモデル学習（10競馬場）
**実行コマンド**:

```bash
cd E:\anonymous-keiba-ai

# 大井（コード: 44）
python train_ranking_model.py ooi_2023-2024_v3_with_race_id.csv

# 船橋（コード: 43）
python train_ranking_model.py funabashi_2020-2025_v3_with_race_id.csv

# 川崎（コード: 45）
python train_ranking_model.py kawasaki_2020-2025_v3_with_race_id.csv

# 浦和（コード: 42）
python train_ranking_model.py urawa_2020-2025_v3_with_race_id.csv

# 名古屋（コード: 48）
python train_ranking_model.py nagoya_2022-2025_v3_with_race_id.csv

# 園田（コード: 50）
python train_ranking_model.py sonoda_2020-2025_v3_with_race_id.csv

# 笠松（コード: 47）
python train_ranking_model.py kasamatsu_2020-2025_v3_with_race_id.csv

# 佐賀（コード: 55）
python train_ranking_model.py saga_2020-2025_v3_with_race_id.csv

# 高知（コード: 54）
python train_ranking_model.py kochi_2020-2025_v3_with_race_id.csv

# 姫路（コード: 51）
python train_ranking_model.py himeji_2020-2025_v3_with_race_id.csv
```

**期待される出力（各競馬場）**:
- `{venue}_ranking_model.txt`: ランキングモデル
- `{venue}_ranking_model.png`: 特徴量重要度グラフ
- `{venue}_ranking_score.txt`: 評価指標（NDCG@1, @3, @5, @10）

### Step 4: 回帰モデル学習（10競馬場）
**実行コマンド**:

```bash
cd E:\anonymous-keiba-ai

# 大井（コード: 44）
python train_regression_model.py ooi_2023-2024_v3_time.csv

# 船橋（コード: 43）
python train_regression_model.py funabashi_2020-2025_v3_time.csv

# ... 他8競馬場も同様
```

**期待される出力（各競馬場）**:
- `{venue}_regression_model.txt`: 回帰モデル
- `{venue}_regression_model.png`: 特徴量重要度グラフ
- `{venue}_regression_score.txt`: 評価指標（RMSE, MAE, R²）

### Step 5: アンサンブル予測（2026年1月データ）
**目的**: 3モデル統合で最終予測を実行

#### 5-1. 予測対象データの準備
2026年1月データを抽出（既存の `simulate_2026_venue_adaptive.py` を活用）：

```bash
# 既存のシミュレーションスクリプトを実行してデータを取得
python simulate_2026_venue_adaptive.py
```

または、新規に予測用データを作成：

```python
# extract_2026_prediction_data.py (新規作成)
# 2026年1月のデータを抽出（targetは不要）
```

#### 5-2. アンサンブル予測の実行

```bash
cd E:\anonymous-keiba-ai

# 大井（コード: 44）
python ensemble_model.py prediction_data_ooi_2026_01.csv \
    ooi_2023-2024_v3_model.txt \
    ooi_2023-2024_v3_ranking_model.txt \
    ooi_2023-2024_v3_regression_model.txt \
    --output ensemble_ooi_2026_01.csv

# 船橋（コード: 43）
python ensemble_model.py prediction_data_funabashi_2026_01.csv \
    funabashi_2020-2025_v3_model.txt \
    funabashi_2020-2025_v3_ranking_model.txt \
    funabashi_2020-2025_v3_regression_model.txt \
    --output ensemble_funabashi_2026_01.csv

# ... 他8競馬場も同様
```

**期待される出力（各競馬場）**:
- `ensemble_{venue}_2026_01.csv`: アンサンブル予測結果
  - 各モデルの予測値（binary_proba, ranking_score, regression_time）
  - 正規化スコア（binary_norm, ranking_norm, regression_norm）
  - 総合スコア（ensemble_score）
  - 推奨度（recommendation: ◎本命/○対抗/▲単穴/△連下/×評価低/消去）

### Step 6: 評価レポート作成
**目的**: 的中率・推奨度別分析

#### 6-1. 推奨度別の的中率集計

```python
# analyze_ensemble_results.py (新規作成)
import pandas as pd
import glob

# 全競馬場のアンサンブル結果を読み込み
ensemble_files = glob.glob('ensemble_*_2026_01.csv')

results = []
for file in ensemble_files:
    df = pd.read_csv(file, encoding='shift-jis')
    
    # 推奨度別の集計
    summary = df.groupby('recommendation').agg({
        'kakutei_chakujun': [
            'count',
            lambda x: (x <= 3).sum()  # 3着以内の件数
        ]
    })
    
    summary.columns = ['件数', '3着以内件数']
    summary['的中率'] = (summary['3着以内件数'] / summary['件数'] * 100).round(2)
    
    results.append({
        'venue': file.replace('ensemble_', '').replace('_2026_01.csv', ''),
        'summary': summary
    })

# 全体集計
print("=" * 80)
print("Phase 4 アンサンブル予測 - 推奨度別的中率")
print("=" * 80)

for result in results:
    print(f"\n【{result['venue']}】")
    print(result['summary'].to_string())
```

#### 6-2. 期待される分析項目
1. **推奨度別的中率**
   - ◎本命: XX% (期待: 50-60%)
   - ○対抗: XX% (期待: 35-45%)
   - ▲単穴: XX% (期待: 25-35%)
   - △連下: XX% (期待: 15-25%)
   - ×評価低: XX% (期待: 5-15%)
   - 消去: XX% (期待: <5%)

2. **モデル別の寄与度分析**
   - 二値分類モデルの影響度
   - ランキングモデルの影響度
   - 回帰モデルの影響度

3. **競馬場別の最適重み**
   - 各競馬場で最適なアンサンブル重みを探索

---

## 🔧 実装サポートツール

### Tool 1: `add_race_id_to_csv.py`
**目的**: 既存CSVに race_id カラムを追加

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_race_id_to_csv.py
既存のCSVファイルに race_id カラムを追加
"""
import pandas as pd
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("使用法: python add_race_id_to_csv.py <csvファイル名>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"エラー: ファイル '{csv_file}' が見つかりません")
        sys.exit(1)
    
    print(f"処理中: {csv_file}")
    
    # データ読み込み
    try:
        df = pd.read_csv(csv_file, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_file, encoding='utf-8')
    
    print(f"  - 読み込み完了: {len(df):,}件")
    
    # race_idを作成
    df['race_id'] = (
        df['kaisai_nen'].astype(str) + 
        df['kaisai_tsukihi'].astype(str).str.zfill(4) + 
        df['keibajo_code'].astype(str) + 
        df['race_bango'].astype(str).str.zfill(2)
    )
    
    print(f"  - race_id作成完了: {df['race_id'].nunique():,}レース")
    
    # 保存
    output_file = csv_file.replace('.csv', '_with_race_id.csv')
    df.to_csv(output_file, index=False, encoding='shift-jis')
    
    print(f"✓ 保存完了: {output_file}")
    print(f"  - レース数: {df['race_id'].nunique():,}件")
    print(f"  - データ件数: {len(df):,}件")

if __name__ == "__main__":
    main()
```

### Tool 2: `convert_target_to_time.py`
**目的**: targetを走破タイムに変更

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_target_to_time.py
CSVファイルのtargetカラムを走破タイムに変更
"""
import pandas as pd
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("使用法: python convert_target_to_time.py <csvファイル名>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"エラー: ファイル '{csv_file}' が見つかりません")
        sys.exit(1)
    
    print(f"処理中: {csv_file}")
    
    # データ読み込み
    try:
        df = pd.read_csv(csv_file, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_file, encoding='utf-8')
    
    print(f"  - 読み込み完了: {len(df):,}件")
    
    # timeカラムが存在するか確認
    if 'time' in df.columns:
        # timeは1/10秒単位 → 秒に変換
        df['target'] = df['time'] / 10.0
        print("  - time カラムから target を作成")
    elif 'prev1_time' in df.columns:
        # 前走タイムを使用（応急処置）
        df['target'] = df['prev1_time']
        print("  - prev1_time カラムから target を作成（応急処置）")
    else:
        print("エラー: タイムカラム（time または prev1_time）が見つかりません")
        print(f"利用可能なカラム: {df.columns.tolist()}")
        sys.exit(1)
    
    # 欠損値を除去
    original_count = len(df)
    df = df[df['target'].notna()]
    df = df[df['target'] > 0]
    removed_count = original_count - len(df)
    
    if removed_count > 0:
        print(f"  - 欠損値・異常値を除去: {removed_count}件")
    
    # 保存
    output_file = csv_file.replace('.csv', '_time.csv')
    df.to_csv(output_file, index=False, encoding='shift-jis')
    
    print(f"✓ 保存完了: {output_file}")
    print(f"  - データ件数: {len(df):,}件")
    print(f"  - タイム範囲: {df['target'].min():.2f}秒 ~ {df['target'].max():.2f}秒")
    print(f"  - タイム平均: {df['target'].mean():.2f}秒")

if __name__ == "__main__":
    main()
```

### Tool 3: `run_phase4_training.py`
**目的**: 全競馬場の学習を一括実行

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_phase4_training.py
Phase 4 の全競馬場学習を一括実行
"""
import subprocess
import os
from datetime import datetime

VENUES = [
    {'code': '44', 'name': '大井', 'csv': 'ooi_2023-2024_v3.csv'},
    {'code': '43', 'name': '船橋', 'csv': 'funabashi_2020-2025_v3.csv'},
    {'code': '45', 'name': '川崎', 'csv': 'kawasaki_2020-2025_v3.csv'},
    {'code': '42', 'name': '浦和', 'csv': 'urawa_2020-2025_v3.csv'},
    {'code': '48', 'name': '名古屋', 'csv': 'nagoya_2022-2025_v3.csv'},
    {'code': '50', 'name': '園田', 'csv': 'sonoda_2020-2025_v3.csv'},
    {'code': '47', 'name': '笠松', 'csv': 'kasamatsu_2020-2025_v3.csv'},
    {'code': '55', 'name': '佐賀', 'csv': 'saga_2020-2025_v3.csv'},
    {'code': '54', 'name': '高知', 'csv': 'kochi_2020-2025_v3.csv'},
    {'code': '51', 'name': '姫路', 'csv': 'himeji_2020-2025_v3.csv'},
]

def run_command(cmd, description):
    """コマンドを実行"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}")
    print(f"コマンド: {' '.join(cmd)}")
    
    start_time = datetime.now()
    result = subprocess.run(cmd, capture_output=False)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if result.returncode == 0:
        print(f"✓ 成功 ({duration:.1f}秒)")
        return True
    else:
        print(f"✗ 失敗 (終了コード: {result.returncode})")
        return False

def main():
    print("="*80)
    print("Phase 4 完全実行スクリプト")
    print("="*80)
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: race_id 追加
    print("\n\n【Step 1】race_id カラムの追加")
    for venue in VENUES:
        csv_file = venue['csv']
        if os.path.exists(csv_file):
            run_command(
                ['python', 'add_race_id_to_csv.py', csv_file],
                f"{venue['name']} ({venue['code']}) - race_id追加"
            )
        else:
            print(f"⚠️ スキップ: {csv_file} が見つかりません")
    
    # Step 2: target変換（走破タイム）
    print("\n\n【Step 2】target を走破タイムに変換")
    for venue in VENUES:
        csv_file = venue['csv']
        if os.path.exists(csv_file):
            run_command(
                ['python', 'convert_target_to_time.py', csv_file],
                f"{venue['name']} ({venue['code']}) - target変換"
            )
        else:
            print(f"⚠️ スキップ: {csv_file} が見つかりません")
    
    # Step 3: ランキングモデル学習
    print("\n\n【Step 3】ランキングモデル学習")
    for venue in VENUES:
        csv_file_with_race_id = venue['csv'].replace('.csv', '_with_race_id.csv')
        if os.path.exists(csv_file_with_race_id):
            run_command(
                ['python', 'train_ranking_model.py', csv_file_with_race_id],
                f"{venue['name']} ({venue['code']}) - ランキング学習"
            )
        else:
            print(f"⚠️ スキップ: {csv_file_with_race_id} が見つかりません")
    
    # Step 4: 回帰モデル学習
    print("\n\n【Step 4】回帰モデル学習")
    for venue in VENUES:
        csv_file_time = venue['csv'].replace('.csv', '_time.csv')
        if os.path.exists(csv_file_time):
            run_command(
                ['python', 'train_regression_model.py', csv_file_time],
                f"{venue['name']} ({venue['code']}) - 回帰学習"
            )
        else:
            print(f"⚠️ スキップ: {csv_file_time} が見つかりません")
    
    print("\n\n" + "="*80)
    print("Phase 4 学習完了！")
    print("="*80)
    print(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
```

---

## 📊 期待される最終成果物

### モデルファイル（各競馬場 × 3種類 = 30モデル）
```
ooi_2023-2024_v3_model.txt                  # 二値分類（Phase 3で作成済み）
ooi_2023-2024_v3_ranking_model.txt          # ランキング（Phase 4で作成）
ooi_2023-2024_v3_regression_model.txt       # 回帰（Phase 4で作成）

funabashi_2020-2025_v3_model.txt
funabashi_2020-2025_v3_ranking_model.txt
funabashi_2020-2025_v3_regression_model.txt

... (他8競馬場も同様)
```

### 評価ファイル（各競馬場 × 3種類 = 30ファイル）
```
ooi_2023-2024_v3_ranking_score.txt
ooi_2023-2024_v3_regression_score.txt
... (他9競馬場も同様)
```

### アンサンブル予測結果（各競馬場 = 10ファイル）
```
ensemble_ooi_2026_01.csv
ensemble_funabashi_2026_01.csv
... (他8競馬場も同様)
```

---

## ⚙️ 実行手順（Windows環境）

### 準備
```bash
cd E:\anonymous-keiba-ai
git pull origin phase4_specialized_models
```

### サポートツールの作成
```bash
# Tool 1: race_id追加ツール
# add_race_id_to_csv.py を作成（上記コード参照）

# Tool 2: target変換ツール
# convert_target_to_time.py を作成（上記コード参照）

# Tool 3: 一括実行ツール
# run_phase4_training.py を作成（上記コード参照）
```

### 実行
```bash
# 方法1: 一括実行（推奨）
python run_phase4_training.py

# 方法2: 手動実行
python add_race_id_to_csv.py ooi_2023-2024_v3.csv
python convert_target_to_time.py ooi_2023-2024_v3.csv
python train_ranking_model.py ooi_2023-2024_v3_with_race_id.csv
python train_regression_model.py ooi_2023-2024_v3_time.csv
# ... 他9競馬場も同様
```

---

## 🎯 成功の基準

### 必須条件
- ✅ 全10競馬場でランキングモデル学習が成功
- ✅ 全10競馬場で回帰モデル学習が成功
- ✅ アンサンブル予測が実行可能
- ✅ 推奨度別の的中率が明確化

### 期待される精度
- ◎本命の的中率: 50-60%以上
- ○対抗の的中率: 35-45%以上
- ▲単穴の的中率: 25-35%以上
- 全体の的中率: Phase 4.5（約29%）を上回る

---

## 🚨 注意事項

### データ準備時の注意
1. **race_id の形式**: `YYYYMMDDCCRRR` （年月日 + 競馬場コード + レース番号）
2. **走破タイムの単位**: 秒単位（time / 10.0）
3. **欠損値の処理**: target が欠損・異常値の行は削除

### 学習時の注意
1. **Boruta の使用**: ランキング・回帰モデルでは Boruta を使用しない
2. **特徴量の統一**: 二値分類で選定した特徴量を使用
3. **ハイパーパラメータ**: Optuna による自動最適化を実行

### アンサンブル時の注意
1. **モデルファイルの整合性**: 3つのモデルが同じ特徴量を使用していること
2. **重みの調整**: 初期重み（二値0.3/ランキング0.5/回帰0.2）から開始
3. **閾値の調整**: 二値分類の閾値（デフォルト0.4）を調整可能

---

## 📝 次のステップ（Phase 5）

Phase 4 完了後の展望：

1. **実戦投入**: 当日レースでの予測実行
2. **回収率分析**: 払戻金データを活用
3. **重みの最適化**: 競馬場ごとの最適重みを探索
4. **システム化**: Web UI の構築
5. **自動化**: 予測の自動実行システム

---

**作成者**: Anonymous Keiba AI Development Team  
**最終更新**: 2026-02-04  
**ステータス**: 実行準備完了
