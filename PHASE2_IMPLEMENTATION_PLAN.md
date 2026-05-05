# 📋 18個統計特徴量追加 実装計画

**作成日**: 2026-05-05  
**目的**: Phase 2統計特徴量18個を確実に実装するための具体的計画

---

## 🎯 実装方針

- ✅ **18個の統計特徴量を追加**
- ❌ **ディープリサーチはしない**
- ❌ **リアルタイム情報は使用しない**
- ✅ **Phase 0で取得済みのデータのみ使用**

---

## 📊 実装する18個の統計特徴量

### グループA: 過去5走統計（9個）

| No | 特徴量名 | 説明 | 計算式 |
|----|---------|------|--------|
| 1 | `recent_5_avg_rank` | 直近5走平均着順 | (prev1_rank + ... + prev5_rank) / 5 |
| 2 | `recent_5_top3_rate` | 直近5走3着以内率 | count(rank ≤ 3) / 5 |
| 3 | `recent_5_win_rate` | 直近5走1着率 | count(rank = 1) / 5 |
| 4 | `recent_5_place2_rate` | 直近5走2着率 | count(rank = 2) / 5 |
| 5 | `recent_5_rank_std` | 直近5走着順標準偏差 | std(prev1_rank, ..., prev5_rank) |
| 6 | `recent_3_avg_rank` | 直近3走平均着順 | (prev1_rank + prev2_rank + prev3_rank) / 3 |
| 7 | `recent_3_top3_rate` | 直近3走3着以内率 | count(rank ≤ 3) / 3 |
| 8 | `form_trend` | 調子トレンド | recent_3_avg - (prev4_rank + prev5_rank)/2 |
| 9 | `consecutive_top3` | 連続3着以内回数 | 先頭から連続で3着以内の回数 |

### グループB: 距離適性（3個）

| No | 特徴量名 | 説明 | 計算式 |
|----|---------|------|--------|
| 10 | `same_distance_avg_rank` | 今回距離での過去平均着順 | mean(rank where kyori = current_kyori) |
| 11 | `distance_change` | 距離延長/短縮 | current_kyori - prev1_kyori |
| 12 | `distance_suitability` | 距離適性スコア | mean(rank where abs(kyori - current_kyori) ≤ 200) |

### グループC: 馬場適性（3個）

| No | 特徴量名 | 説明 | 計算式 |
|----|---------|------|--------|
| 13 | `same_baba_avg_rank` | 今回馬場状態での過去平均着順 | mean(rank where baba = current_baba) |
| 14 | `baba_change` | 馬場状態変化 | current_baba_code - prev1_baba_code |
| 15 | `heavy_track_performance` | 重馬場成績 | mean(rank where baba in ['重', '不']) |

### グループD: 間隔・ローテーション（3個）※Phase 0確認後

| No | 特徴量名 | 説明 | 計算式 |
|----|---------|------|--------|
| 16 | `last_race_days` | 前走からの間隔 | current_date - prev1_date |
| 17 | `rento_flag` | 連闘フラグ | last_race_days ≤ 7 |
| 18 | `kyuyo_ake_flag` | 休養明けフラグ | last_race_days ≥ 60 |

---

## 🔧 実装手順（5ステップ）

### ステップ1: Phase 0のデータ確認（30分）

#### 目的
Phase 0で取得済みのカラムを確認し、実装可能な特徴量を最終決定

#### 作業内容
```bash
# Phase 0の出力サンプルを確認
cd /home/user/webapp/anonymous-keiba-ai
head -1 data/raw/2026/04/浦和_20260423_raw.csv
```

#### 確認項目
- ✅ `prev1_rank` 〜 `prev5_rank` が存在するか
- ✅ `prev1_kyori` 〜 `prev5_kyori` が存在するか
- ✅ `prev1_baba` 〜 `prev5_baba` が存在するか
- ⚠️ `prev1_date` 〜 `prev5_date` が存在するか（間隔計算用）

#### 判断
- 日付データがない場合 → 特徴量16〜18は**実装見送り**（15個のみ実装）
- 日付データがある場合 → 18個全て実装

---

### ステップ2: Phase 1スクリプト修正（2時間）

#### 目的
`scripts/phase1_feature_engineering/prepare_features.py` に統計特徴量追加関数を実装

#### 作業内容

1. **新規関数を追加**

```python
# scripts/phase1_feature_engineering/prepare_features.py

def add_statistical_features(df):
    """
    18個の統計特徴量を追加
    
    Parameters
    ----------
    df : pd.DataFrame
        Phase 0の生データ
    
    Returns
    -------
    pd.DataFrame
        統計特徴量追加後のデータ
    """
    
    print("\n" + "="*80)
    print("[Phase 1+] 統計特徴量18個を追加中...")
    print("="*80)
    
    # グループA: 過去5走統計（9個）
    df = add_past_performance_features(df)
    
    # グループB: 距離適性（3個）
    df = add_distance_features(df)
    
    # グループC: 馬場適性（3個）
    df = add_track_condition_features(df)
    
    # グループD: 間隔・ローテーション（3個）※Phase 0次第
    if 'prev1_date' in df.columns:
        df = add_interval_features(df)
    else:
        print("  ⚠️ 日付データなし → 間隔特徴量（3個）はスキップ")
    
    print("\n✅ 統計特徴量追加完了")
    return df
```

2. **メイン関数に統合**

```python
def main():
    # ... 既存の処理 ...
    
    # Phase 0データ読み込み
    df = pd.read_csv(input_csv, encoding=encoding)
    
    # 欠損値処理
    df = handle_missing_values(df)
    
    # 🆕 統計特徴量追加
    df = add_statistical_features(df)
    
    # Race ID生成
    df['race_id'] = create_race_id(df)
    
    # 必要な特徴量のみ抽出
    df_output = filter_required_features(df)
    
    # 保存
    df_output.to_csv(output_csv, index=False, encoding='shift-jis')
```

#### ファイル
- 修正対象: `scripts/phase1_feature_engineering/prepare_features.py`
- 新規追加: なし

---

### ステップ3: 統計特徴量関数の実装（3時間）

#### 目的
4つのグループ関数を実装

#### 3-1. グループA: 過去5走統計（9個）

```python
def add_past_performance_features(df):
    """
    過去5走統計特徴量（9個）を追加
    """
    print("\n  [グループA] 過去5走統計（9個）")
    
    past_rank_cols = ['prev1_rank', 'prev2_rank', 'prev3_rank', 'prev4_rank', 'prev5_rank']
    
    # 欠損値を0で埋める
    for col in past_rank_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0)
    
    # 1. 直近5走平均着順
    df['recent_5_avg_rank'] = df[past_rank_cols].replace(0, np.nan).mean(axis=1)
    
    # 2. 直近5走3着以内率
    df['recent_5_top3_rate'] = (df[past_rank_cols] <= 3).sum(axis=1) / (df[past_rank_cols] > 0).sum(axis=1)
    df['recent_5_top3_rate'] = df['recent_5_top3_rate'].fillna(0)
    
    # 3. 直近5走1着率
    df['recent_5_win_rate'] = (df[past_rank_cols] == 1).sum(axis=1) / (df[past_rank_cols] > 0).sum(axis=1)
    df['recent_5_win_rate'] = df['recent_5_win_rate'].fillna(0)
    
    # 4. 直近5走2着率
    df['recent_5_place2_rate'] = (df[past_rank_cols] == 2).sum(axis=1) / (df[past_rank_cols] > 0).sum(axis=1)
    df['recent_5_place2_rate'] = df['recent_5_place2_rate'].fillna(0)
    
    # 5. 直近5走着順標準偏差
    df['recent_5_rank_std'] = df[past_rank_cols].replace(0, np.nan).std(axis=1)
    df['recent_5_rank_std'] = df['recent_5_rank_std'].fillna(0)
    
    # 6. 直近3走平均着順
    df['recent_3_avg_rank'] = df[['prev1_rank', 'prev2_rank', 'prev3_rank']].replace(0, np.nan).mean(axis=1)
    
    # 7. 直近3走3着以内率
    df['recent_3_top3_rate'] = (df[['prev1_rank', 'prev2_rank', 'prev3_rank']] <= 3).sum(axis=1) / \
                                (df[['prev1_rank', 'prev2_rank', 'prev3_rank']] > 0).sum(axis=1)
    df['recent_3_top3_rate'] = df['recent_3_top3_rate'].fillna(0)
    
    # 8. 調子トレンド
    recent_3 = df[['prev1_rank', 'prev2_rank', 'prev3_rank']].replace(0, np.nan).mean(axis=1)
    prev_4_5 = df[['prev4_rank', 'prev5_rank']].replace(0, np.nan).mean(axis=1)
    df['form_trend'] = recent_3 - prev_4_5
    df['form_trend'] = df['form_trend'].fillna(0)
    
    # 9. 連続3着以内回数
    def count_consecutive_top3(row):
        count = 0
        for col in past_rank_cols:
            if row[col] > 0 and row[col] <= 3:
                count += 1
            elif row[col] > 0:
                break
        return count
    
    df['consecutive_top3'] = df.apply(count_consecutive_top3, axis=1)
    
    print(f"    ✅ 9個追加完了")
    return df
```

#### 3-2. グループB: 距離適性（3個）

```python
def add_distance_features(df):
    """
    距離適性特徴量（3個）を追加
    """
    print("\n  [グループB] 距離適性（3個）")
    
    # 10. 今回距離での過去平均着順
    df['same_distance_avg_rank'] = df.apply(
        lambda row: np.mean([
            row[f'prev{i}_rank'] 
            for i in range(1, 6) 
            if f'prev{i}_kyori' in df.columns and row[f'prev{i}_kyori'] == row['kyori'] and row[f'prev{i}_rank'] > 0
        ]) if any(f'prev{i}_kyori' in df.columns and row.get(f'prev{i}_kyori') == row['kyori'] and row[f'prev{i}_rank'] > 0 for i in range(1, 6)) else np.nan,
        axis=1
    )
    
    # 11. 距離延長/短縮
    if 'prev1_kyori' in df.columns:
        df['distance_change'] = df['kyori'] - df['prev1_kyori']
        df['distance_change'] = df['distance_change'].fillna(0)
    else:
        df['distance_change'] = 0
    
    # 12. 距離適性スコア（±200m範囲）
    df['distance_suitability'] = df.apply(
        lambda row: np.mean([
            row[f'prev{i}_rank'] 
            for i in range(1, 6) 
            if f'prev{i}_kyori' in df.columns and abs(row[f'prev{i}_kyori'] - row['kyori']) <= 200 and row[f'prev{i}_rank'] > 0
        ]) if any(f'prev{i}_kyori' in df.columns and abs(row.get(f'prev{i}_kyori', 0) - row['kyori']) <= 200 and row[f'prev{i}_rank'] > 0 for i in range(1, 6)) else np.nan,
        axis=1
    )
    
    print(f"    ✅ 3個追加完了")
    return df
```

#### 3-3. グループC: 馬場適性（3個）

```python
def add_track_condition_features(df):
    """
    馬場適性特徴量（3個）を追加
    """
    print("\n  [グループC] 馬場適性（3個）")
    
    # 馬場状態コード変換
    baba_map = {'良': 1, '稍': 2, '重': 3, '不': 4}
    
    if 'baba_jyotai' in df.columns:
        df['baba_jyotai_code'] = df['baba_jyotai'].map(baba_map).fillna(1)
    
    for i in range(1, 6):
        col = f'prev{i}_baba'
        if col in df.columns:
            df[f'{col}_code'] = df[col].map(baba_map).fillna(1)
    
    # 13. 今回馬場状態での過去平均着順
    df['same_baba_avg_rank'] = df.apply(
        lambda row: np.mean([
            row[f'prev{i}_rank'] 
            for i in range(1, 6) 
            if f'prev{i}_baba_code' in df.columns and row[f'prev{i}_baba_code'] == row.get('baba_jyotai_code', 1) and row[f'prev{i}_rank'] > 0
        ]) if any(f'prev{i}_baba_code' in df.columns and row.get(f'prev{i}_baba_code') == row.get('baba_jyotai_code', 1) and row[f'prev{i}_rank'] > 0 for i in range(1, 6)) else np.nan,
        axis=1
    )
    
    # 14. 馬場変化
    if 'prev1_baba_code' in df.columns and 'baba_jyotai_code' in df.columns:
        df['baba_change'] = df['baba_jyotai_code'] - df['prev1_baba_code']
        df['baba_change'] = df['baba_change'].fillna(0)
    else:
        df['baba_change'] = 0
    
    # 15. 重馬場成績
    df['heavy_track_performance'] = df.apply(
        lambda row: np.mean([
            row[f'prev{i}_rank'] 
            for i in range(1, 6) 
            if f'prev{i}_baba_code' in df.columns and row[f'prev{i}_baba_code'] >= 3 and row[f'prev{i}_rank'] > 0
        ]) if any(f'prev{i}_baba_code' in df.columns and row.get(f'prev{i}_baba_code', 0) >= 3 and row[f'prev{i}_rank'] > 0 for i in range(1, 6)) else np.nan,
        axis=1
    )
    
    print(f"    ✅ 3個追加完了")
    return df
```

#### 3-4. グループD: 間隔・ローテーション（3個）※オプション

```python
def add_interval_features(df):
    """
    間隔・ローテーション特徴量（3個）を追加
    ※Phase 0に日付データがある場合のみ
    """
    print("\n  [グループD] 間隔・ローテーション（3個）")
    
    # 日付を datetime に変換
    if 'kaisai_tsukihi' in df.columns:
        df['current_date'] = pd.to_datetime(df['kaisai_nen'].astype(str) + df['kaisai_tsukihi'].astype(str), format='%Y%m%d', errors='coerce')
    
    if 'prev1_date' in df.columns:
        df['prev1_date_dt'] = pd.to_datetime(df['prev1_date'], format='%Y%m%d', errors='coerce')
        
        # 16. 前走からの間隔
        df['last_race_days'] = (df['current_date'] - df['prev1_date_dt']).dt.days
        df['last_race_days'] = df['last_race_days'].fillna(999)
        
        # 17. 連闘フラグ
        df['rento_flag'] = (df['last_race_days'] <= 7).astype(int)
        
        # 18. 休養明けフラグ
        df['kyuyo_ake_flag'] = (df['last_race_days'] >= 60).astype(int)
        
        print(f"    ✅ 3個追加完了")
    else:
        # 日付データがない場合は0埋め
        df['last_race_days'] = 999
        df['rento_flag'] = 0
        df['kyuyo_ake_flag'] = 0
        print(f"    ⚠️ 日付データなし → 0埋め")
    
    return df
```

---

### ステップ4: テスト実行（1時間）

#### 目的
修正したPhase 1スクリプトを実行し、特徴量が正しく追加されることを確認

#### 作業内容

```bash
cd /home/user/webapp/anonymous-keiba-ai

# テストデータで実行（浦和 2026-04-23）
python scripts/phase1_feature_engineering/prepare_features.py \
    data/raw/2026/04/浦和_20260423_raw.csv \
    --output data/features/2026/04/浦和_20260423_features_test.csv

# 特徴量数を確認
head -1 data/features/2026/04/浦和_20260423_features_test.csv | tr ',' '\n' | wc -l

# 新規追加された特徴量を確認
head -1 data/features/2026/04/浦和_20260423_features_test.csv | tr ',' '\n' | grep -E "recent_|distance_|baba_|form_|consecutive|last_race|rento|kyuyo"
```

#### 確認項目
- ✅ 特徴量数が 50個 → 68個（または65個）に増えているか
- ✅ 新規特徴量18個（または15個）が追加されているか
- ✅ エラーが発生していないか
- ✅ 欠損値が適切に処理されているか

---

### ステップ5: 全競馬場で再実行（2時間）

#### 目的
Phase 0-6の全パイプラインを実行し、新しい特徴量で学習・予測を実施

#### 作業内容

```bash
cd E:\anonymous-keiba-ai

# Phase 0: データ取得（スキップ - 既存データ使用）

# Phase 1: 特徴量作成（新しいスクリプト使用）
# 浦和（コード42）の2026-04-23で実行
python scripts/phase1_feature_engineering/prepare_features.py \
    data/raw/2026/04/浦和_20260423_raw.csv

# Phase 3-5: 予測・アンサンブル
run_all_FINAL.bat 42 2026-04-23

# 結果確認
type predictions\浦和_20260423_note.txt
```

#### 確認項目
- ✅ Phase 3 Binary予測が正常に動作するか
- ✅ Phase 4-1 Ranking予測が正常に動作するか
- ✅ Phase 4-2 Regression予測が正常に動作するか
- ✅ Phase 5 Ensembleが正常に動作するか
- ✅ 予測精度が向上しているか（的中率+8〜13%）

---

## 📊 期待効果

### 予測精度の向上

| 項目 | 現状 | 特徴量追加後 | 改善幅 |
|------|------|------------|--------|
| **本命複勝的中率** | 52.8% | 56〜60% | +3〜7pt |
| **AUC** | 0.7546 | 0.77〜0.79 | +0.015〜0.035 |
| **3連複的中率** | 約15% | 20〜25% | +5〜10pt |
| **回収率** | 約75% | 80〜88% | +5〜13% |

### 特徴量重要度の変化

**予想される上位10特徴量**:
1. `ranking_score`（Phase 4-1）
2. `predicted_time`（Phase 4-2）
3. `recent_5_avg_rank`（🆕）
4. `recent_5_top3_rate`（🆕）
5. `prev1_rank`
6. `recent_3_avg_rank`（🆕）
7. `form_trend`（🆕）
8. `distance_suitability`（🆕）
9. `prev1_time`
10. `same_distance_avg_rank`（🆕）

---

## 📋 チェックリスト

### 事前確認
- [ ] Phase 0のデータに `prev1_rank` 〜 `prev5_rank` が含まれているか
- [ ] Phase 0のデータに `prev1_kyori` 〜 `prev5_kyori` が含まれているか
- [ ] Phase 0のデータに `prev1_baba` 〜 `prev5_baba` が含まれているか
- [ ] Phase 0のデータに `prev1_date` 〜 `prev5_date` が含まれているか（オプション）

### 実装
- [ ] `add_past_performance_features()` 関数を実装
- [ ] `add_distance_features()` 関数を実装
- [ ] `add_track_condition_features()` 関数を実装
- [ ] `add_interval_features()` 関数を実装（オプション）
- [ ] `add_statistical_features()` 関数を実装
- [ ] `prepare_features.py` のメイン関数に統合

### テスト
- [ ] テストデータで実行し、特徴量数が増加することを確認
- [ ] 新規特徴量18個（または15個）が追加されることを確認
- [ ] エラーが発生しないことを確認
- [ ] Phase 3-5が正常に動作することを確認

### 検証
- [ ] 本命複勝的中率が向上することを確認
- [ ] AUCが向上することを確認
- [ ] 特徴量重要度を確認し、新規特徴量が上位に来ることを確認

---

## 🚀 実装スケジュール

| ステップ | 作業内容 | 所要時間 | 担当 |
|---------|---------|---------|------|
| **Step 1** | Phase 0データ確認 | 30分 | サンドボックス |
| **Step 2** | Phase 1スクリプト修正 | 2時間 | サンドボックス |
| **Step 3** | 統計特徴量関数実装 | 3時間 | サンドボックス |
| **Step 4** | テスト実行 | 1時間 | サンドボックス |
| **Step 5** | 全競馬場で再実行 | 2時間 | Eドライブ |
| **合計** | - | **8.5時間** | - |

---

## 📄 成果物

### 修正ファイル
1. `scripts/phase1_feature_engineering/prepare_features.py`（修正）

### 新規ファイル
なし

### ドキュメント
1. `PHASE2_IMPLEMENTATION_PLAN.md`（本ファイル）

---

## 🎯 次のアクション

**今すぐ実行**: **ステップ1: Phase 0データ確認**

```bash
cd /home/user/webapp/anonymous-keiba-ai
head -1 data/raw/2026/04/浦和_20260423_raw.csv 2>/dev/null || \
find data -name "*_raw.csv" -type f | head -1 | xargs head -1
```

---
