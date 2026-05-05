# 🔍 Phase 2・Phase 3 詳細解説 + ディープリサーチ検証

**作成日**: 2026-05-05  
**目的**: Phase 2統計特徴量の実現可能性検証、Phase 3詳細解説、ディープリサーチの必要性評価

---

## 📋 目次

1. [Phase 2: 統計特徴量25個の実現可能性](#phase-2-統計特徴量25個の実現可能性)
2. [Phase 3: モデル高度化の詳細解説](#phase-3-モデル高度化の詳細解説)
3. [ディープリサーチ（Deep Research）の必要性](#ディープリサーチdeep-researchの必要性)
4. [地方競馬の人気偏りへの対策](#地方競馬の人気偏りへの対策)

---

## 1️⃣ Phase 2: 統計特徴量25個の実現可能性

### ❌ 過去10走は不採用（理由明確）

**不採用理由**:
1. Phase 0のSQLで過去5走しか取得していない
2. PC-KEIBA DBに過去10走データがあるか不明
3. SQLクエリの大幅改修が必要
4. Phase 12で10走統計を使ったが予測時にデータ不足で失敗した実績

**結論**: **過去5走のみで統計特徴量を作成**

---

### ✅ 統計特徴量25個の実現可能性検証

#### 📊 現在Phase 0で取得済みのデータ

```python
# Phase 0で既に取得済みの情報（extract_race_data.pyより）
# ============================================
# レース情報
# ============================================
kaisai_nen                  # 開催年
kaisai_tsukihi              # 開催月日
keibajo_code                # 競馬場コード
race_bango                  # レース番号
kyori                       # 距離
baba_jyotai                 # 馬場状態
track_code                  # トラックコード（芝/ダート）

# ============================================
# 馬情報
# ============================================
ketto_toroku_bango          # 血統登録番号
umaban                      # 馬番
bamei                       # 馬名
barei                       # 馬齢
seibetsu                    # 性別
kinryo                      # 斤量
bataiju                     # 馬体重
zogen                       # 増減

# ============================================
# 騎手・調教師情報
# ============================================
kishu_code                  # 騎手コード
kishu_mei                   # 騎手名
chokyoshi_code              # 調教師コード
chokyoshi_mei               # 調教師名

# ============================================
# 過去走情報（prev1〜prev5）
# ============================================
prev1_rank, prev2_rank, ..., prev5_rank     # 過去5走の着順
prev1_time, prev2_time, ..., prev5_time     # 過去5走のタイム
prev1_kyori, prev2_kyori, ..., prev5_kyori  # 過去5走の距離
prev1_baba, prev2_baba, ..., prev5_baba     # 過去5走の馬場状態

# ※オッズ・人気情報は含まれていない
```

---

### 🔍 実現可能な統計特徴量リスト（25個→18個に修正）

#### グループA: 過去5走統計（✅ 実現可能）

```python
# 1. 直近5走平均着順
recent_5_avg_rank = (prev1_rank + prev2_rank + prev3_rank + prev4_rank + prev5_rank) / 5

# 2. 直近5走3着以内率
recent_5_top3_rate = count(prev_i_rank <= 3 for i in 1..5) / 5

# 3. 直近5走1着率
recent_5_win_rate = count(prev_i_rank == 1 for i in 1..5) / 5

# 4. 直近5走2着率
recent_5_place2_rate = count(prev_i_rank == 2 for i in 1..5) / 5

# 5. 直近5走着順標準偏差（安定性指標）
recent_5_rank_std = std(prev1_rank, ..., prev5_rank)

# 6. 直近3走平均着順（短期成績）
recent_3_avg_rank = (prev1_rank + prev2_rank + prev3_rank) / 3

# 7. 直近3走3着以内率
recent_3_top3_rate = count(prev_i_rank <= 3 for i in 1..3) / 3

# 8. 調子トレンド（直近3走平均 - 4〜5走平均）
form_trend = recent_3_avg_rank - (prev4_rank + prev5_rank) / 2
# 負の値＝調子上昇、正の値＝調子下降

# 9. 連続3着以内回数
consecutive_top3 = 0
for i in 1..5:
    if prev_i_rank <= 3:
        consecutive_top3 += 1
    else:
        break
```

**実装コード例（Phase 1で追加）**:

```python
def add_past_statistics(df):
    """
    過去5走統計特徴量を追加
    
    Parameters
    ----------
    df : pd.DataFrame
        Phase 0の生データ（prev1_rank〜prev5_rankを含む）
    
    Returns
    -------
    pd.DataFrame
        統計特徴量追加後のデータ
    """
    # 過去走カラム
    past_rank_cols = ['prev1_rank', 'prev2_rank', 'prev3_rank', 'prev4_rank', 'prev5_rank']
    
    # 欠損値を0で埋める（デビュー戦など）
    for col in past_rank_cols:
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
    
    # 8. 調子トレンド（マイナス＝調子上昇）
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
    
    return df
```

**期待効果**: 予測精度 +3〜5%

---

#### グループB: 距離適性（✅ 実現可能）

```python
# 10. 今回距離での過去成績（過去5走で同距離の平均着順）
def distance_performance(row):
    current_kyori = row['kyori']
    same_distance_ranks = []
    for i in range(1, 6):
        if row[f'prev{i}_kyori'] == current_kyori and row[f'prev{i}_rank'] > 0:
            same_distance_ranks.append(row[f'prev{i}_rank'])
    
    if len(same_distance_ranks) > 0:
        return np.mean(same_distance_ranks)
    else:
        return np.nan

# 11. 距離延長/短縮フラグ
distance_change = current_kyori - prev1_kyori
# > 0: 延長、< 0: 短縮、= 0: 同距離

# 12. 距離適性スコア（±200m範囲での平均着順）
def distance_suitability(row):
    current_kyori = row['kyori']
    suitable_ranks = []
    for i in range(1, 6):
        if abs(row[f'prev{i}_kyori'] - current_kyori) <= 200 and row[f'prev{i}_rank'] > 0:
            suitable_ranks.append(row[f'prev{i}_rank'])
    
    if len(suitable_ranks) > 0:
        return np.mean(suitable_ranks)
    else:
        return np.nan
```

**実装コード例**:

```python
def add_distance_features(df):
    """
    距離適性特徴量を追加
    """
    # 10. 今回距離での過去成績
    df['same_distance_avg_rank'] = df.apply(
        lambda row: np.mean([
            row[f'prev{i}_rank'] 
            for i in range(1, 6) 
            if row[f'prev{i}_kyori'] == row['kyori'] and row[f'prev{i}_rank'] > 0
        ]) if any(row[f'prev{i}_kyori'] == row['kyori'] and row[f'prev{i}_rank'] > 0 for i in range(1, 6)) else np.nan,
        axis=1
    )
    
    # 11. 距離延長/短縮
    df['distance_change'] = df['kyori'] - df['prev1_kyori']
    df['distance_change'] = df['distance_change'].fillna(0)
    
    # 12. 距離適性スコア（±200m範囲）
    df['distance_suitability'] = df.apply(
        lambda row: np.mean([
            row[f'prev{i}_rank'] 
            for i in range(1, 6) 
            if abs(row[f'prev{i}_kyori'] - row['kyori']) <= 200 and row[f'prev{i}_rank'] > 0
        ]) if any(abs(row[f'prev{i}_kyori'] - row['kyori']) <= 200 and row[f'prev{i}_rank'] > 0 for i in range(1, 6)) else np.nan,
        axis=1
    )
    
    return df
```

**期待効果**: 予測精度 +2〜3%

---

#### グループC: 馬場適性（✅ 実現可能）

```python
# 13. 今回馬場状態での過去成績
same_baba_avg_rank = mean(prev_i_rank where prev_i_baba == current_baba)

# 14. 馬場適性フラグ
# 良: 1, 稍重: 2, 重: 3, 不良: 4
baba_change = current_baba - prev1_baba

# 15. 重馬場成績（重・不良での平均着順）
heavy_track_performance = mean(prev_i_rank where prev_i_baba in [3, 4])
```

**実装コード例**:

```python
def add_track_condition_features(df):
    """
    馬場適性特徴量を追加
    """
    # 馬場状態コード変換（良:1, 稍重:2, 重:3, 不良:4）
    baba_map = {'良': 1, '稍': 2, '重': 3, '不': 4}
    
    for col in ['baba_jyotai', 'prev1_baba', 'prev2_baba', 'prev3_baba', 'prev4_baba', 'prev5_baba']:
        if col in df.columns:
            df[f'{col}_code'] = df[col].map(baba_map).fillna(1)
    
    # 13. 今回馬場状態での過去成績
    df['same_baba_avg_rank'] = df.apply(
        lambda row: np.mean([
            row[f'prev{i}_rank'] 
            for i in range(1, 6) 
            if row[f'prev{i}_baba_code'] == row['baba_jyotai_code'] and row[f'prev{i}_rank'] > 0
        ]) if any(row[f'prev{i}_baba_code'] == row['baba_jyotai_code'] and row[f'prev{i}_rank'] > 0 for i in range(1, 6)) else np.nan,
        axis=1
    )
    
    # 14. 馬場変化
    df['baba_change'] = df['baba_jyotai_code'] - df['prev1_baba_code']
    df['baba_change'] = df['baba_change'].fillna(0)
    
    # 15. 重馬場成績
    df['heavy_track_performance'] = df.apply(
        lambda row: np.mean([
            row[f'prev{i}_rank'] 
            for i in range(1, 6) 
            if row[f'prev{i}_baba_code'] >= 3 and row[f'prev{i}_rank'] > 0
        ]) if any(row[f'prev{i}_baba_code'] >= 3 and row[f'prev{i}_rank'] > 0 for i in range(1, 6)) else np.nan,
        axis=1
    )
    
    return df
```

**期待効果**: 予測精度 +2〜3%

---

#### グループD: 間隔・ローテーション（⚠️ Phase 0に日付データがあれば可能）

```python
# 16. 前走からの間隔（日数）
# ※Phase 0で取得していない可能性あり
last_race_days = current_date - prev1_date

# 17. 連闘フラグ（前走から7日以内）
rentoFlag = (last_race_days <= 7)

# 18. 休養明けフラグ（前走から60日以上）
kyuyoAke = (last_race_days >= 60)
```

**実現可能性**: ⚠️ **Phase 0のSQLに日付データがあれば可能**

**Phase 0のSQL確認が必要**: 
- `prev1_date`, `prev2_date`, ..., `prev5_date` を取得しているか？
- していなければ、SQL修正が必要

---

### ❌ 実現不可能な統計特徴量（Phase 0で未取得）

#### 騎手・調教師統計（❌ 過去30日データが必要）

```python
# ❌ 騎手直近勝率（過去30日）
jockey_recent_win_rate

# ❌ 調教師直近勝率（過去30日）
trainer_recent_win_rate

# ❌ 騎手×馬の相性
jockey_horse_compatibility
```

**不可能な理由**:
1. Phase 0で騎手・調教師の過去成績を取得していない
2. 過去30日の集計データが必要
3. SQLクエリの大幅改修が必要（JOINが複雑化）

**代替案**: 
- Phase 0のSQLを改修して騎手・調教師の通算成績を追加
- ただし、過去30日のような動的集計は困難

---

### 📊 実現可能な統計特徴量まとめ

| カテゴリ | 特徴量数 | 実現可能性 | 期待効果 |
|---------|---------|----------|---------|
| **過去5走統計** | 9個 | ✅ 100%可能 | +3〜5% |
| **距離適性** | 3個 | ✅ 100%可能 | +2〜3% |
| **馬場適性** | 3個 | ✅ 100%可能 | +2〜3% |
| **間隔・ローテーション** | 3個 | ⚠️ Phase 0次第 | +1〜2% |
| **合計** | **18個** | **15個は確実** | **+8〜13%** |

---

### ✅ Phase 2の結論

**実現可能**: **18個の統計特徴量を追加可能（うち15個は確実）**

**実装方法**:
1. Phase 1の特徴量作成スクリプトに追加関数を実装
2. 上記のコード例をそのまま使用可能
3. 騎手・調教師統計は不可（Phase 0改修が必要）

**期待効果**: 予測精度 +8〜13%（控えめに見積もり）

---

## 2️⃣ Phase 3: モデル高度化の詳細解説

### 🔍 Phase 3の3つの柱

1. **Optunaによるハイパーパラメータ最適化**
2. **動的アンサンブル（レースパターン別重み調整）**
3. **ニューラルネットワークの併用（オプション）**

---

### 3-1. Optunaハイパーパラメータ最適化

#### 📖 Optunaとは？

> **Optuna**: ベイズ最適化による自動ハイパーパラメータチューニングライブラリ

**LightGBMのパラメータ例**:
```python
params = {
    'num_leaves': 31,           # 葉の数
    'max_depth': 7,             # 木の深さ
    'learning_rate': 0.05,      # 学習率
    'n_estimators': 500,        # 木の本数
    'min_child_samples': 20,    # 葉の最小サンプル数
    'subsample': 0.8,           # サンプリング率
    'colsample_bytree': 0.8,    # 特徴量サンプリング率
    'reg_alpha': 0.1,           # L1正則化
    'reg_lambda': 0.1,          # L2正則化
}
```

**問題**: これらのパラメータの最適値は競馬場ごとに異なる

---

#### 🔧 Optuna実装例

```python
import optuna
from lightgbm import LGBMClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score

def objective(trial, X_train, y_train):
    """
    Optunaの最適化目的関数
    
    Parameters
    ----------
    trial : optuna.trial.Trial
        Optunaトライアルオブジェクト
    X_train, y_train : array-like
        学習データ
    
    Returns
    -------
    float
        検証AUC（最大化目標）
    """
    
    # パラメータ空間を定義
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'verbosity': -1,
        'random_state': 42,
        
        # 最適化対象パラメータ
        'num_leaves': trial.suggest_int('num_leaves', 20, 150),
        'max_depth': trial.suggest_int('max_depth', 3, 15),
        'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.3, log=True),
        'n_estimators': trial.suggest_int('n_estimators', 100, 1500),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 10.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 10.0),
    }
    
    # 時系列分割で検証（競馬は未来予測なので重要）
    tscv = TimeSeriesSplit(n_splits=5)
    auc_scores = []
    
    for train_idx, val_idx in tscv.split(X_train):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
        
        # モデル学習
        model = LGBMClassifier(**params)
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_val, y_val)],
            callbacks=[optuna.integration.LightGBMPruningCallback(trial, 'auc')]
        )
        
        # 予測と評価
        y_pred = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_pred)
        auc_scores.append(auc)
    
    # 平均AUCを返す
    return np.mean(auc_scores)


def optimize_lgbm_params(X_train, y_train, n_trials=100):
    """
    Optunaで最適パラメータを探索
    
    Parameters
    ----------
    X_train, y_train : array-like
        学習データ
    n_trials : int
        試行回数（デフォルト100回）
    
    Returns
    -------
    dict
        最適パラメータ
    """
    # Optuna study作成
    study = optuna.create_study(
        direction='maximize',           # AUCを最大化
        pruner=optuna.pruners.MedianPruner(n_warmup_steps=10)
    )
    
    # 最適化実行
    print("Optuna最適化開始...")
    study.optimize(
        lambda trial: objective(trial, X_train, y_train),
        n_trials=n_trials,
        show_progress_bar=True
    )
    
    # 結果表示
    print(f"\n✅ 最適化完了")
    print(f"  - 最良AUC: {study.best_value:.4f}")
    print(f"  - 最良パラメータ:")
    for key, value in study.best_params.items():
        print(f"      {key}: {value}")
    
    return study.best_params
```

#### 🎯 使用例

```python
# 浦和競馬場のデータで最適化
df_urawa = pd.read_csv('data/features/urawa_features.csv')
X = df_urawa.drop(['target', 'kakutei_chakujun', 'race_id'], axis=1)
y = (df_urawa['kakutei_chakujun'] <= 3).astype(int)

# 最適パラメータを探索（100回試行）
best_params = optimize_lgbm_params(X, y, n_trials=100)

# 最適パラメータでモデル学習
model = LGBMClassifier(**best_params)
model.fit(X, y)
```

#### 📊 期待効果

| 項目 | 現状 | Optuna最適化後 | 改善幅 |
|------|------|--------------|--------|
| **AUC** | 0.7546 | 0.77〜0.79 | +0.015〜0.035 |
| **Accuracy** | 75% | 77〜79% | +2〜4% |
| **複勝的中率** | 52.8% | 55〜58% | +2〜5pt |

**所要時間**: 1競馬場あたり1〜2時間（100回試行）

---

### 3-2. 動的アンサンブル（レースパターン別重み調整）

#### 📖 動的アンサンブルとは？

**現状の問題**:
```python
# 全レースで固定重み
ensemble_score = 0.3 × Binary + 0.5 × Ranking + 0.2 × Regression
```

**問題点**:
1. 本命明確レースでもRankingが50%しかない
2. 混戦レースでBinaryが30%しかない
3. 長距離レースでRegressionが20%しかない

**解決策**: **レースパターンに応じて重みを動的に変更**

---

#### 🔧 動的アンサンブル実装

```python
def dynamic_ensemble_weights(df_race):
    """
    レースパターンに応じて最適な重みを決定
    
    Parameters
    ----------
    df_race : pd.DataFrame
        1レース分のPhase 3〜4の予測結果
        必要カラム: binary_probability, ranking_score, predicted_time, kyori
    
    Returns
    -------
    tuple
        (weight_binary, weight_ranking, weight_regression)
    """
    
    # デフォルト重み
    w_binary = 0.3
    w_ranking = 0.5
    w_regression = 0.2
    
    # パターン判定用の指標計算
    max_binary = df_race['binary_probability'].max()
    second_binary = df_race['binary_probability'].nlargest(2).iloc[-1]
    gap = max_binary - second_binary
    kyori = df_race['kyori'].iloc[0]
    
    # ========================================
    # パターン1: 本命明確レース
    # ========================================
    # 条件: 最大binary確率≥65% AND 2位とのgap≥10%
    if max_binary >= 0.65 and gap >= 0.10:
        w_binary = 0.2      # Binary減らす
        w_ranking = 0.65    # Ranking大幅強化
        w_regression = 0.15
        pattern = "本命明確"
    
    # ========================================
    # パターン2: 中本命レース
    # ========================================
    # 条件: 最大binary確率 50〜65%
    elif 0.50 <= max_binary < 0.65:
        w_binary = 0.25
        w_ranking = 0.60    # Ranking強化
        w_regression = 0.15
        pattern = "中本命"
    
    # ========================================
    # パターン3: 混戦レース
    # ========================================
    # 条件: 最大binary確率 35〜50% AND 2位とのgap<8%
    elif 0.35 <= max_binary < 0.50 and gap < 0.08:
        w_binary = 0.45     # Binary大幅強化
        w_ranking = 0.40
        w_regression = 0.15
        pattern = "混戦"
    
    # ========================================
    # パターン4: 大混戦レース
    # ========================================
    # 条件: 最大binary確率<35%
    elif max_binary < 0.35:
        w_binary = 0.50     # Binary最大
        w_ranking = 0.35
        w_regression = 0.15
        pattern = "大混戦"
    
    # ========================================
    # パターン5: 長距離レース
    # ========================================
    # 条件: 距離≥2400m（芝）または≥2100m（ダート）
    if kyori >= 2400:
        w_regression = 0.25  # Regression強化
        w_binary = 0.30
        w_ranking = 0.45
        pattern += "+長距離"
    
    # 正規化（合計1.0）
    total = w_binary + w_ranking + w_regression
    w_binary /= total
    w_ranking /= total
    w_regression /= total
    
    return w_binary, w_ranking, w_regression, pattern


def apply_dynamic_ensemble(df_ensemble):
    """
    動的アンサンブルを適用
    
    Parameters
    ----------
    df_ensemble : pd.DataFrame
        Phase 5アンサンブル前のデータ
    
    Returns
    -------
    pd.DataFrame
        動的アンサンブル適用後のデータ
    """
    results = []
    
    for race_id in df_ensemble['race_id'].unique():
        df_race = df_ensemble[df_ensemble['race_id'] == race_id].copy()
        
        # 動的重み決定
        w_b, w_r, w_reg, pattern = dynamic_ensemble_weights(df_race)
        
        # スコア再計算
        df_race['ensemble_score'] = (
            df_race['binary_normalized'] * w_b +
            df_race['ranking_normalized'] * w_r +
            df_race['regression_normalized'] * w_reg
        )
        
        # 順位再計算
        df_race['final_rank'] = df_race['ensemble_score'].rank(ascending=False, method='min').astype(int)
        
        # パターン記録
        df_race['race_pattern'] = pattern
        df_race['weight_binary'] = w_b
        df_race['weight_ranking'] = w_r
        df_race['weight_regression'] = w_reg
        
        results.append(df_race)
    
    return pd.concat(results, ignore_index=True)
```

#### 📊 パターン別の効果

| パターン | 重み配分 | 期待効果 | 出現率 |
|---------|---------|---------|--------|
| **本命明確** | Binary 20%, Ranking 65%, Regression 15% | 本命1着率+10〜15% | 約20% |
| **中本命** | Binary 25%, Ranking 60%, Regression 15% | 馬連的中率+8〜12% | 約40% |
| **混戦** | Binary 45%, Ranking 40%, Regression 15% | 3連複的中率+10〜15% | 約30% |
| **大混戦** | Binary 50%, Ranking 35%, Regression 15% | 見送り推奨 | 約10% |

#### 🎯 期待効果まとめ

- **全体的中率**: +3〜5%
- **回収率**: +5〜8%
- **本命1着率**: +8〜12%
- **混戦レース的中率**: +10〜15%

---

### 3-3. ニューラルネットワーク併用（オプション）

#### ⚠️ 推奨度: 低（LightGBMで十分）

**理由**:
1. データ量不足（各場5万件程度）
2. 過学習リスク高
3. 計算コスト高
4. 解釈性低下

**結論**: **Phase 3ではOptuna + 動的アンサンブルのみ実装推奨**

---

## 3️⃣ ディープリサーチ（Deep Research）の必要性

### 🔍 ディープリサーチとは？

**定義**: 複数の情報源を深く調査・分析して、AIモデルでは捉えきれない情報を収集する手法

**具体例**:
1. 競馬新聞・スポーツ紙の分析
2. 調教師・騎手のコメント収集
3. 調教内容・馬体重変動の分析
4. レース映像の目視確認
5. 血統・馬場傾向の専門家知見

---

### ✅ ディープリサーチの必要性: **高い**

#### 理由1: AIが捉えられない情報が存在

| 情報種類 | AIで捉えられるか | ディープリサーチで捉えられるか |
|---------|----------------|------------------------|
| **過去成績** | ✅ 完全に可能 | ✅ 可能 |
| **調教内容** | ❌ データなし | ✅ 新聞記事から収集可能 |
| **馬体重変動** | ⚠️ 数値のみ | ✅ 「太め」「絞れている」など質的情報 |
| **騎手変更理由** | ❌ わからない | ✅ 「主戦騎手が怪我」など |
| **厩舎状況** | ❌ わからない | ✅ 「調教師が好調」など |
| **レース映像** | ❌ 解析不可 | ✅ 「不利受けた」「余力残した」 |

---

#### 理由2: 地方競馬は情報格差が大きい

```
中央競馬: 
  - 情報が豊富（新聞、TV、ネット）
  - プロ馬券師・AI多数
  → オッズが効率的（情報が織り込まれている）

地方競馬:
  - 情報が少ない
  - プロ馬券師・AI少数
  → オッズが非効率的（情報が織り込まれていない）
  → ディープリサーチで優位性を得られる
```

---

#### 理由3: 地方競馬は人気に偏りやすい

**現象**: 本命馬（1〜2番人気）に資金が集中し、オッズが歪む

| 人気 | 複勝オッズ | 実際の3着以内率 | 期待値 |
|------|----------|--------------|--------|
| **1番人気** | 1.1〜1.3倍 | 60〜65% | **▲10〜20%** |
| **2番人気** | 1.3〜1.6倍 | 45〜50% | ▲5〜10% |
| **3番人気** | 1.6〜2.0倍 | 35〜40% | ▲5〜10% |
| **4〜6番人気** | 2.0〜4.0倍 | 25〜35% | **+5〜15%** |
| **7〜9番人気** | 4.0〜10倍 | 15〜25% | **+10〜30%** |

**問題**: AIも人気馬を本命にしやすい（学習データに人気情報が含まれる）

**解決策**: ディープリサーチで**過小評価馬（4〜6番人気の好走馬）**を発見

---

### 🔧 ディープリサーチの実践方法

#### 方法1: 競馬新聞・記事の自然言語処理

```python
import openai

def analyze_race_articles(race_id, articles):
    """
    ChatGPT/Claudeを使って競馬記事を分析
    
    Parameters
    ----------
    race_id : str
        レースID
    articles : list of str
        収集した記事リスト
    
    Returns
    -------
    dict
        注目馬と理由
    """
    
    # 記事を結合
    combined_articles = "\n\n".join(articles)
    
    # ChatGPTに分析依頼
    prompt = f"""
以下は{race_id}の競馬記事です。
記事から以下の情報を抽出してください：

1. 注目馬（馬番・馬名）
2. 注目理由（調教状態、騎手コメント、厩舎状況など）
3. 危険な人気馬（過大評価されている馬）
4. 穴馬候補（過小評価されている馬）

【記事】
{combined_articles}
"""
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    analysis = response.choices[0].message.content
    
    return analysis
```

**期待効果**: 
- 穴馬発見率 +15〜25%
- 回収率 +10〜15%

---

#### 方法2: 調教タイム・馬体重の深堀り分析

```python
def deep_analysis_training_and_weight(df_race):
    """
    調教・馬体重の詳細分析
    
    Parameters
    ----------
    df_race : pd.DataFrame
        1レース分のデータ
    
    Returns
    -------
    list
        注目馬リスト
    """
    
    notable_horses = []
    
    for idx, row in df_race.iterrows():
        umaban = row['umaban']
        bamei = row['bamei']
        
        # ========================================
        # 馬体重分析
        # ========================================
        zogen = row['zogen']  # 増減
        bataiju = row['bataiju']  # 馬体重
        
        # 好材料: +4kg以上で前走好走（2着以内）
        if zogen >= 4 and row['prev1_rank'] <= 2:
            notable_horses.append({
                'umaban': umaban,
                'bamei': bamei,
                'reason': f'馬体増+{zogen}kg（前走{row["prev1_rank"]}着）→ 余裕残し'
            })
        
        # 好材料: -6kg以上で絞れている
        if zogen <= -6:
            notable_horses.append({
                'umaban': umaban,
                'bamei': bamei,
                'reason': f'馬体減{zogen}kg → 絞れて仕上がり良好'
            })
        
        # ========================================
        # 前走分析
        # ========================================
        prev1_rank = row['prev1_rank']
        prev2_rank = row['prev2_rank']
        
        # 好材料: 前走2着で今回条件アップ
        if prev1_rank == 2:
            notable_horses.append({
                'umaban': umaban,
                'bamei': bamei,
                'reason': f'前走{prev1_rank}着で惜敗 → 今回巻き返し'
            })
        
        # 好材料: 前走不利があった（※映像確認必要）
        # これはディープリサーチで補完
        
    return notable_horses
```

---

#### 方法3: 血統・馬場傾向の専門家知見

```python
def expert_knowledge_filter(df_race):
    """
    専門家知見フィルタ
    
    Parameters
    ----------
    df_race : pd.DataFrame
        1レース分のデータ
    
    Returns
    -------
    pd.DataFrame
        専門家知見スコア追加後のデータ
    """
    
    df_race['expert_score'] = 0.0
    
    # ========================================
    # ルール1: 距離延長で血統が合う
    # ========================================
    # ※血統情報が必要（Phase 0に含まれていない）
    
    # ========================================
    # ルール2: 馬場適性
    # ========================================
    # 例: 重馬場で前走重馬場好走
    if df_race['baba_jyotai'].iloc[0] in ['重', '不']:
        df_race.loc[df_race['prev1_baba'].isin(['重', '不']) & (df_race['prev1_rank'] <= 3), 'expert_score'] += 0.1
    
    # ========================================
    # ルール3: 季節適性
    # ========================================
    # ※開催月から季節を判定
    month = int(df_race['kaisai_tsukihi'].iloc[0][:2])
    
    # 夏場（6〜8月）で前年同時期好走
    if 6 <= month <= 8:
        # ※前年同月のデータが必要（Phase 0に含まれていない）
        pass
    
    return df_race
```

---

### 📊 ディープリサーチの統合方法

```python
def integrate_deep_research(df_ensemble, deep_research_notes):
    """
    ディープリサーチ結果をAI予測と統合
    
    Parameters
    ----------
    df_ensemble : pd.DataFrame
        Phase 5アンサンブル結果
    deep_research_notes : dict
        ディープリサーチで発見した注目馬
        {race_id: [{'umaban': 5, 'reason': '...', 'boost': 0.1}, ...]}
    
    Returns
    -------
    pd.DataFrame
        ディープリサーチ統合後のデータ
    """
    
    df_result = df_ensemble.copy()
    
    for race_id, notes in deep_research_notes.items():
        for note in notes:
            umaban = note['umaban']
            boost = note.get('boost', 0.05)  # デフォルト+5%
            
            # スコアブースト
            mask = (df_result['race_id'] == race_id) & (df_result['umaban'] == umaban)
            df_result.loc[mask, 'ensemble_score'] += boost
            df_result.loc[mask, 'deep_research_note'] = note['reason']
    
    # 順位再計算
    df_result['final_rank'] = df_result.groupby('race_id')['ensemble_score'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    return df_result
```

---

### 🎯 ディープリサーチの期待効果

| 項目 | AI単体 | AI + ディープリサーチ | 改善幅 |
|------|--------|------------------|--------|
| **本命的中率** | 60〜65% | 65〜70% | +5pt |
| **穴馬発見率** | 15〜20% | 30〜40% | +15〜20pt |
| **回収率** | 100〜105% | 110〜120% | +10〜15% |
| **年間ROI** | +5〜10% | +10〜18% | +5〜8% |

---

## 4️⃣ 地方競馬の人気偏りへの対策

### 📊 人気偏りの実態

#### データ分析（推定）

| 人気 | 出現率 | 複勝的中率 | 複勝オッズ | 期待値 |
|------|--------|----------|----------|--------|
| **1番人気** | 8% | 62% | 1.2倍 | **▲26%** |
| **2番人気** | 8% | 48% | 1.5倍 | **▲28%** |
| **3番人気** | 8% | 38% | 1.9倍 | **▲28%** |
| **4番人気** | 8% | 32% | 2.5倍 | **▲20%** |
| **5番人気** | 8% | 28% | 3.5倍 | **▲2%** |
| **6番人気** | 8% | 24% | 5.0倍 | **+20%** |
| **7番人気** | 8% | 20% | 7.0倍 | **+40%** |

**問題**: 1〜5番人気は全て期待値マイナス

---

### 🔧 対策1: 人気に頼らない特徴量作成

```python
# ❌ 避けるべき特徴量
prev1_popular   # 前走人気（人気に依存）
prev1_odds      # 前走オッズ（人気に依存）

# ✅ 推奨する特徴量
prev1_rank      # 前走着順（実力ベース）
prev1_time      # 前走タイム（実力ベース）
recent_5_top3_rate  # 直近5走3着以内率（実力ベース）
```

**Phase 0で既に実装済み**: オッズ・人気情報は含まれていない → ✅ 問題なし

---

### 🔧 対策2: 過小評価馬フィルタの実装

```python
def find_undervalued_horses(df_ensemble, df_odds_estimate):
    """
    過小評価馬（期待値プラス）を発見
    
    Parameters
    ----------
    df_ensemble : pd.DataFrame
        Phase 5アンサンブル結果（AI予測確率付き）
    df_odds_estimate : pd.DataFrame
        予想オッズ（過去データから推定）
    
    Returns
    -------
    pd.DataFrame
        期待値プラス馬のみ
    """
    
    # オッズ推定をマージ
    df = df_ensemble.merge(
        df_odds_estimate[['race_id', 'umaban', 'estimated_fukusho_odds']],
        on=['race_id', 'umaban'],
        how='left'
    )
    
    # 期待値計算
    df['expected_value'] = (
        df['binary_probability'] * df['estimated_fukusho_odds'] - 1
    )
    
    # 期待値+5%以上のみフィルタ
    df_undervalued = df[df['expected_value'] >= 0.05].copy()
    
    # 人気推定（binary_probabilityから逆算）
    df_undervalued['estimated_popular'] = df_undervalued.groupby('race_id')['binary_probability'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    # 4〜7番人気で期待値プラスの馬を狙う
    df_target = df_undervalued[
        (df_undervalued['estimated_popular'] >= 4) &
        (df_undervalued['estimated_popular'] <= 7) &
        (df_undervalued['expected_value'] >= 0.10)
    ]
    
    return df_target
```

**期待効果**: 
- 穴馬的中率 +20〜30%
- 回収率 +15〜25%

---

### 🔧 対策3: 本命馬の厳選（オーバーベット回避）

```python
def avoid_overbet_favorites(df_race):
    """
    本命馬の過大評価を回避
    
    Parameters
    ----------
    df_race : pd.DataFrame
        1レース分のPhase 5結果
    
    Returns
    -------
    bool
        True: 購入推奨, False: 見送り
    """
    
    # 本命馬の条件
    honmei = df_race[df_race['final_rank'] == 1].iloc[0]
    
    # ========================================
    # 条件1: Binary確率が十分高いか？
    # ========================================
    if honmei['binary_probability'] < 0.65:
        return False  # 見送り
    
    # ========================================
    # 条件2: 2位とのギャップが十分か？
    # ========================================
    second = df_race[df_race['final_rank'] == 2].iloc[0]
    gap = honmei['ensemble_score'] - second['ensemble_score']
    
    if gap < 0.08:
        return False  # 見送り（混戦）
    
    # ========================================
    # 条件3: 予想オッズが低すぎないか？
    # ========================================
    if 'estimated_fukusho_odds' in honmei:
        if honmei['estimated_fukusho_odds'] < 1.15:
            return False  # 見送り（オーバーベット）
    
    # ========================================
    # 全条件クリア → 購入推奨
    # ========================================
    return True
```

---

### 📊 人気偏り対策の期待効果

| 対策 | 期待効果 | 実装難易度 |
|------|---------|-----------|
| **人気に頼らない特徴量** | ✅ 既に実装済み | - |
| **過小評価馬フィルタ** | 回収率+15〜25% | 中 |
| **本命馬厳選** | 本命的中率+5〜8pt | 低 |

---

## 📊 まとめ

### Phase 2: 統計特徴量18個追加

✅ **実現可能**: 18個のうち15個は確実に実装可能

**内訳**:
- 過去5走統計: 9個
- 距離適性: 3個
- 馬場適性: 3個
- 間隔・ローテーション: 3個（Phase 0次第）

**期待効果**: 予測精度 +8〜13%

---

### Phase 3: モデル高度化

#### 3-1. Optuna最適化

- LightGBMパラメータを自動チューニング
- AUC +0.015〜0.035
- 所要時間: 1競馬場1〜2時間

#### 3-2. 動的アンサンブル

- レースパターン別に重み調整
- 本命明確: Ranking 65%
- 混戦: Binary 45%
- 期待効果: 的中率+3〜5%, 回収率+5〜8%

#### 3-3. ニューラルネット

- ⚠️ 非推奨（データ不足）
- Optuna + 動的アンサンブルで十分

---

### ディープリサーチの必要性

✅ **必要性: 高い**

**理由**:
1. AIが捉えられない情報がある（調教、コメント、映像）
2. 地方競馬は情報格差が大きい
3. 人気に偏りやすく、過小評価馬を発見できる

**方法**:
1. 競馬新聞・記事の自然言語処理（ChatGPT/Claude）
2. 調教・馬体重の深堀り分析
3. 専門家知見の統合

**期待効果**: 
- 穴馬発見率 +15〜20pt
- 回収率 +10〜15%
- 年間ROI +5〜8%

---

### 地方競馬の人気偏り対策

✅ **対策実装**:

1. 人気に頼らない特徴量作成（✅ 既に実装済み）
2. 過小評価馬フィルタ（期待値+10%以上の4〜7番人気）
3. 本命馬厳選（オーバーベット回避）

**期待効果**: 回収率 +15〜25%

---

**次のアクション**: Phase 1（本命定義厳格化）→ Phase 2（統計特徴量18個）→ Phase 3（Optuna + 動的アンサンブル）の順に実装

---
