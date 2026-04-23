# 🔍 **重大発見：過去走数の違いが乖離の原因！**

## 📊 **結論：Phase 0-6は5走、Phase 12は10走**

---

## 🎯 **過去走数の比較**

| システム | 過去走数 | 使用する情報 | データ量 |
|---------|---------|-------------|---------|
| **Phase 0-6** | **5走** | prev1 ~ prev5 | 少ない |
| **Phase 12** | **10走** | 過去10走のrolling統計 | 多い |

---

## 📋 **Phase 0-6の過去走データ（5走まで）**

### Phase 0のデータ取得

```sql
-- scripts/phase0_data_acquisition/extract_race_data.py

MAX(CASE WHEN pr.race_order = 1 THEN pr.kakutei_chakujun END) AS prev1_rank,
MAX(CASE WHEN pr.race_order = 1 THEN pr.soha_time END) AS prev1_time,
MAX(CASE WHEN pr.race_order = 1 THEN pr.kohan_3f END) AS prev1_last3f,
...
MAX(CASE WHEN pr.race_order = 2 THEN pr.kakutei_chakujun END) AS prev2_rank,
MAX(CASE WHEN pr.race_order = 2 THEN pr.soha_time END) AS prev2_time,
...
MAX(CASE WHEN pr.race_order = 3 THEN pr.kakutei_chakujun END) AS prev3_rank,
MAX(CASE WHEN pr.race_order = 3 THEN pr.soha_time END) AS prev3_time,
...
MAX(CASE WHEN pr.race_order = 4 THEN pr.kakutei_chakujun END) AS prev4_rank,
MAX(CASE WHEN pr.race_order = 4 THEN pr.soha_time END) AS prev4_time,
...
MAX(CASE WHEN pr.race_order = 5 THEN pr.kakutei_chakujun END) AS prev5_rank,
MAX(CASE WHEN pr.race_order = 5 THEN pr.soha_time END) AS prev5_time
```

**特徴**:
- ✅ 前走（prev1）から5走前（prev5）まで
- ✅ 各走の詳細データ（着順・タイム・馬体重・コーナー等）
- ❌ **6走前以降のデータは使用しない**

---

## 📋 **Phase 12の過去走データ（10走の統計）**

### Phase 12の追加特徴量

```python
# scripts/phase12_umatan_model/step1_add_top2_features.py

# 過去10走の1着率
df['recent_1st_rate'] = df.groupby('ketto_toroku_bango')['is_1st'].transform(
    lambda x: x.rolling(window=10, min_periods=1).mean().shift(1).fillna(0)
)

# 過去10走の2着率
df['recent_2nd_rate'] = df.groupby('ketto_toroku_bango')['is_2nd'].transform(
    lambda x: x.rolling(window=10, min_periods=1).mean().shift(1).fillna(0)
)

# 過去10走の2着以内率
df['recent_top2_rate'] = df.groupby('ketto_toroku_bango')['is_top2'].transform(
    lambda x: x.rolling(window=10, min_periods=1).mean().shift(1).fillna(0)
)

# 過去10走の1着回数
df['recent_1st_count'] = df.groupby('ketto_toroku_bango')['is_1st'].transform(
    lambda x: x.rolling(window=10, min_periods=1).sum().shift(1).fillna(0)
)

# 過去10走の2着回数
df['recent_2nd_count'] = df.groupby('ketto_toroku_bango')['is_2nd'].transform(
    lambda x: x.rolling(window=10, min_periods=1).sum().shift(1).fillna(0)
)
```

**特徴**:
- ✅ prev1 ~ prev5（Phase 0-6と同じ）
- ✅ **過去10走の1着率・2着率・2着以内率**（追加）⭐
- ✅ **過去10走の1着回数・2着回数**（追加）⭐
- ✅ **6~10走前の成績も反映される**

---

## 🎯 **なぜ乖離が生じるか**

### 🏇 **ケース1：最近好調・過去低調の馬**

```
A馬の成績:
  過去10走: 6-7-8-8-9-1-1-2-2-1 （最近5走が好調）
  過去5走:  1-1-2-2-1 （最近好調）
  
Phase 0-6の評価:
  → prev1~5のみ → 1-1-2-2-1 → ✅ 高評価
  
Phase 12の評価:
  → 過去10走の1着率 = 40%（4/10）
  → 過去10走の2着以内率 = 50%（5/10）
  → ⚠️ やや低評価（6~10走前の不調が影響）
```

**→ Phase 12は過去の不調が影響、Phase 0-6は最近のみで判断**

---

### 🏇 **ケース2：最近不調・過去好調の馬**

```
B馬の成績:
  過去10走: 1-1-1-2-2-6-7-8-8-9 （最近5走が不調）
  過去5走:  6-7-8-8-9 （最近不調）
  
Phase 0-6の評価:
  → prev1~5のみ → 6-7-8-8-9 → ❌ 低評価
  
Phase 12の評価:
  → 過去10走の1着率 = 30%（3/10）
  → 過去10走の2着以内率 = 50%（5/10）
  → ⚠️ 中評価（6~10走前の好調が影響）
```

**→ Phase 12は過去の好調が残る、Phase 0-6は最近のみで判断**

---

### 🏇 **ケース3：一貫して好調の馬**

```
C馬の成績:
  過去10走: 1-2-1-2-1-2-1-2-1-2 （一貫して好調）
  過去5走:  1-2-1-2-1
  
Phase 0-6の評価:
  → prev1~5 → 1-2-1-2-1 → ✅ 高評価
  
Phase 12の評価:
  → 過去10走の1着率 = 50%（5/10）
  → 過去10走の2着以内率 = 100%（10/10）
  → ✅ 非常に高評価
```

**→ 両システムとも高評価（一致）**

---

## 📊 **過去走数の違いが与える影響**

| 馬のタイプ | Phase 0-6（5走） | Phase 12（10走） | 乖離 |
|-----------|-----------------|-----------------|------|
| **最近好調・過去不調** | 高評価 | 中評価 | ⭐⭐⭐ 大 |
| **最近不調・過去好調** | 低評価 | 中評価 | ⭐⭐⭐ 大 |
| **一貫して好調** | 高評価 | 高評価 | ❌ 一致 |
| **一貫して不調** | 低評価 | 低評価 | ❌ 一致 |
| **波がある馬** | 変動大 | 変動小 | ⭐⭐ 中 |

---

## 🎯 **どちらが正しいか？**

### Phase 0-6（5走）のメリット

- ✅ **最近の調子を重視** → 直近の好不調を反映
- ✅ **データが新鮮** → 6走以上前の古いデータは無視
- ✅ **調子の変化に敏感** → 最近好調な馬を高評価

### Phase 12（10走）のメリット

- ✅ **長期的な実力を反映** → 偶然の好走・不調を平滑化
- ✅ **安定性を評価** → 一貫して強い馬を高評価
- ✅ **サンプル数が多い** → より信頼性の高い統計

---

## ⚠️ **問題点の特定**

### 現在の問題

Phase 12は **予測時に過去10走の統計を使えない**

**理由**:
- Phase 0は **prev1~5のみ** を取得
- Phase 12の特徴量（`recent_1st_rate`等）は **学習時に計算**
- **予測時には過去10走の統計がない** → 0で補完される

### 確認方法

実行ログを見ると：

```
[Step 5-1] Binary予測（2着以内）中...
[3/5] 特徴量の準備
  ⚠️  不足している特徴量: 9個
  - 不足特徴量を0で補完しました
```

**これらの「不足している特徴量」が `recent_*` 系！**

---

## 🔧 **解決策**

### ✅ **提案1：Phase 0で過去10走を取得（推奨）**

Phase 0のSQLを修正して、prev6~prev10を追加：

```sql
MAX(CASE WHEN pr.race_order = 6 THEN pr.kakutei_chakujun END) AS prev6_rank,
MAX(CASE WHEN pr.race_order = 6 THEN pr.soha_time END) AS prev6_time,
...
MAX(CASE WHEN pr.race_order = 10 THEN pr.kakutei_chakujun END) AS prev10_rank,
MAX(CASE WHEN pr.race_order = 10 THEN pr.soha_time END) AS prev10_time
```

Phase 1で `recent_*_rate` を計算：

```python
# Phase 1で追加
df['recent_1st_rate'] = (prev1_rank==1 + prev2_rank==1 + ... + prev10_rank==1) / 10
df['recent_2nd_rate'] = (prev1_rank==2 + prev2_rank==2 + ... + prev10_rank==2) / 10
df['recent_top2_rate'] = (prev1_rank<=2 + prev2_rank<=2 + ... + prev10_rank<=2) / 10
```

### ✅ **提案2：Phase 12の特徴量を5走に統一**

Phase 12の `step1_add_top2_features.py` を修正：

```python
# window=10 → window=5 に変更
df['recent_1st_rate'] = df.groupby('ketto_toroku_bango')['is_1st'].transform(
    lambda x: x.rolling(window=5, min_periods=1).mean().shift(1).fillna(0)
)
```

---

## 📝 **まとめ**

### 🎯 **発見した乖離の原因**

| 項目 | Phase 0-6 | Phase 12 | 影響度 |
|------|-----------|----------|--------|
| **過去走数** | 5走 | 10走（統計） | ⭐⭐⭐ 極大 |
| **最近好調馬** | 高評価 | 中評価 | 乖離大 |
| **過去好調馬** | 低評価 | 中評価 | 乖離大 |
| **予測時の問題** | なし | **特徴量不足（0埋め）** | ⭐⭐⭐ 極大 |

### ⚠️ **最大の問題**

**Phase 12の予測時に `recent_*_rate` が0で補完されている**

→ これが最大の乖離原因！

---

## 🚀 **次のアクション**

1. **Phase 0で過去10走を取得するように修正**（推奨）
2. **Phase 1で `recent_*_rate` を計算**
3. **Phase 12の予測精度を再検証**

---

**過去走数の違いが乖離の主原因です！修正が必要です！** ⚠️
