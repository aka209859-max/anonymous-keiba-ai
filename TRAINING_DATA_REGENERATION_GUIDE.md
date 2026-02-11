# 🔧 学習データ再生成ガイド (Phase 7/8/5対応版)

## 📋 概要

Phase 7/8の最適化には、以下の3つのターゲット変数が必要です：

- **`target`**: Binary分類用 (3着以内=1, 圏外=0) ✅ 既存
- **`rank_target`**: Ranking学習用 (着順) ❌ 追加が必要
- **`time`**: Regression学習用 (走破タイム) ❌ 追加が必要

---

## 🔍 現状の問題点

現在の `*_with_time.csv` には:
- ✅ `target` (Binary用)
- ✅ `prev1_time`, `prev2_time`, ... (過去走タイム)
- ❌ `rank_target` (当該レースの着順)
- ❌ `time` (当該レースの走破タイム)

**結果**: Phase 7/8 Ranking/Regression の学習ができない

---

## ✅ 解決策: extract_training_data_v2.py を修正済み

### 修正内容 (2026-02-11)

1. **target_race CTE に `se.soha_time` を追加**
   ```sql
   se.soha_time,  -- 追加: Regression学習用の走破タイム
   ```

2. **SELECT句に2つの新しいターゲット変数を追加**
   ```sql
   -- Ranking target: 着順 (Phase 7/8 Ranking用)
   CASE 
       WHEN tr.kakutei_chakujun ~ '^[0-9]+$' THEN tr.kakutei_chakujun::INTEGER
       ELSE NULL
   END AS rank_target,
   
   -- Regression target: 走破タイム (Phase 7/8 Regression用)
   CASE 
       WHEN tr.soha_time ~ '^[0-9.]+$' THEN tr.soha_time::NUMERIC
       ELSE NULL
   END AS time,
   ```

3. **GROUP BY句に `tr.soha_time` を追加**

---

## 🚀 実行手順 (船橋のみテスト)

### ステップ1: PC-KEIBAデータベース接続確認

```bash
# PostgreSQL接続確認
psql -h 127.0.0.1 -p 5432 -U postgres -d pckeiba -c "SELECT COUNT(*) FROM nvd_ra;"
```

**期待される出力**: レース件数が表示される

---

### ステップ2: 船橋の学習データを再生成

```bash
cd E:\anonymous-keiba-ai

# 船橋 (競馬場コード: 43)
python extract_training_data_v2.py \
  --keibajo 43 \
  --start-date 2020 \
  --end-date 2025 \
  --output data\training\funabashi_2020-2025_with_time.csv
```

**実行時間**: 約5〜10分 (データ量による)

---

### ステップ3: データ確認

```bash
# カラム数とターゲット変数を確認
python -c "import pandas as pd; df = pd.read_csv('data/training/funabashi_2020-2025_with_time.csv', encoding='shift-jis', nrows=5); print('Columns:', df.columns.tolist()); print('Total:', len(df.columns)); print('target:', df['target'].unique()); print('rank_target:', df['rank_target'].unique()); print('time sample:', df['time'].head())"
```

**期待される出力**:
```
Columns: ['target', 'rank_target', 'time', 'kaisai_nen', ...]
Total: 52  (50 + 2 新規ターゲット変数)
target: [0 1]
rank_target: [1 2 3 4 5 6 7 8 9 10 ...]
time sample: 0    95.3
             1    97.1
             2    94.8
             ...
```

---

### ステップ4: Phase 7 Ranking 特徴量選択 (テスト)

```bash
cd E:\anonymous-keiba-ai

python scripts\phase7_feature_selection\run_boruta_ranking.py \
  data\training\funabashi_2020-2025_with_time.csv \
  --max-iter 100
```

**期待される出力**:
- ターゲット変数: `rank_target` を検出
- 特徴量選択: 10〜30個程度が選ばれる
- 出力ファイル: `data/features/selected/funabashi_ranking_selected_features.csv`

---

### ステップ5: Phase 7 Regression 特徴量選択 (テスト)

```bash
python scripts\phase7_feature_selection\run_boruta_regression.py \
  data\training\funabashi_2020-2025_with_time.csv \
  --max-iter 100
```

**期待される出力**:
- ターゲット変数: `time` を検出
- 特徴量選択: 10〜30個程度が選ばれる
- 出力ファイル: `data/features/selected/funabashi_regression_selected_features.csv`

---

## 🔄 全14会場一括生成 (Phase 7/8完全実行前)

```bash
# 競馬場コードリスト
# 30=門別, 33=帯広, 35=盛岡, 36=水沢, 42=浦和, 43=船橋, 
# 44=大井, 45=川崎, 46=金沢, 47=笠松, 48=名古屋,
# 50=園田, 51=姫路, 54=高知, 55=佐賀

# 全会場一括生成 (PowerShellスクリプト例)
$venues = @(
  @{code="30"; name="monbetsu"},
  @{code="33"; name="obihiro"},
  @{code="35"; name="morioka"},
  @{code="36"; name="mizusawa"},
  @{code="42"; name="urawa"},
  @{code="43"; name="funabashi"},
  @{code="44"; name="ooi"},
  @{code="45"; name="kawasaki"},
  @{code="46"; name="kanazawa"},
  @{code="47"; name="kasamatsu"},
  @{code="48"; name="nagoya"},
  @{code="50"; name="sonoda"},
  @{code="51"; name="himeji"},
  @{code="54"; name="kochi"},
  @{code="55"; name="saga"}
)

foreach ($v in $venues) {
    Write-Host "Generating $($v.name)..."
    python extract_training_data_v2.py `
      --keibajo $($v.code) `
      --start-date 2020 `
      --end-date 2025 `
      --output "data\training\$($v.name)_2020-2025_with_time.csv"
}
```

**実行時間**: 約1〜2時間 (全14会場)

---

## 📊 期待される成果

修正後の学習データ構成:
```
Columns (52個):
  1. target         - Binary分類用 (3着以内=1)
  2. rank_target    - Ranking学習用 (着順 1〜N) ← NEW!
  3. time           - Regression学習用 (走破タイム 秒単位) ← NEW!
  4-52. 特徴量      - 50個の特徴量 (既存)
```

---

## ⚠️ 注意事項

### データ品質チェック

1. **欠損値の確認**:
   ```python
   import pandas as pd
   df = pd.read_csv('data/training/funabashi_2020-2025_with_time.csv', encoding='shift-jis')
   print(df[['target', 'rank_target', 'time']].isnull().sum())
   ```

2. **異常値の確認**:
   ```python
   # rank_target は 1〜18 程度の範囲
   print(df['rank_target'].describe())
   
   # time は 60〜200秒程度の範囲
   print(df['time'].describe())
   ```

3. **分布の確認**:
   ```python
   # Binary: 30%前後が1 (複勝圏内)
   print(df['target'].value_counts(normalize=True))
   
   # Ranking: 均等分布に近い
   print(df['rank_target'].value_counts().sort_index())
   ```

---

## 🎯 次のステップ

1. ✅ 船橋データ再生成 → Phase 7/8 テスト
2. ⏳ 全14会場データ再生成
3. ⏳ RUN_PHASE7_COMPLETE.bat 実行
4. ⏳ RUN_PHASE8_COMPLETE.bat 実行
5. ⏳ RUN_ULTIMATE_FUNABASHI.bat 実行 (最終テスト)

---

## 📚 関連ドキュメント

- [PHASE7_8_5_COMPLETE_GUIDE.md](./PHASE7_8_5_COMPLETE_GUIDE.md)
- [EXPECTED_OUTPUTS.md](./EXPECTED_OUTPUTS.md)
- [ULTIMATE_AI_PACKAGE_README.md](./ULTIMATE_AI_PACKAGE_README.md)

---

## 🆘 トラブルシューティング

### エラー: `rank_target` がすべて NULL

**原因**: `kakutei_chakujun` が数値以外の文字列を含んでいる

**対策**:
```sql
-- extract_training_data_v2.py の WHERE句を確認
AND se.kakutei_chakujun NOT IN ('00', '取消', '除外', '中止', '失格')
AND se.kakutei_chakujun ~ '^[0-9]+$'
```

### エラー: `time` がすべて NULL

**原因**: `soha_time` が欠損または異常値

**対策**:
```python
# データ確認
df = pd.read_csv('funabashi_2020-2025_with_time.csv', encoding='shift-jis')
print(df[df['time'].isnull()].shape)  # NULL件数
print(df['time'].min(), df['time'].max())  # 範囲確認
```

---

## ✅ 最終確認チェックリスト

- [ ] PC-KEIBAデータベース接続OK
- [ ] `extract_training_data_v2.py` 修正版をダウンロード
- [ ] 船橋データ再生成成功
- [ ] `rank_target` カラム存在確認
- [ ] `time` カラム存在確認
- [ ] Phase 7 Ranking テスト成功
- [ ] Phase 7 Regression テスト成功

---

**作成日**: 2026-02-11  
**最終更新**: 2026-02-11  
**バージョン**: 1.0
