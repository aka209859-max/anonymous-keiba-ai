# 🎯 モデルスコア分析と次のアクション（2025年データ評価計画）

**作成日**: 2026-02-11  
**対象期間**: 2025/01/01 〜 2025/12/31  
**目的**: 旧モデルと新モデルの比較、残り13会場への取り組み計画

---

## 📊 **スコアの意味（重要な確認事項）**

### ✅ **結論: スコアは複勝率ではありません**

#### **旧モデル（Phase 3-4-5）**
- **スコア 0.98** = レース内での相対的な評価が最高（1位予測）
- **意味**: Binary (30%) + Ranking (50%) + Regression (20%) の統合スコアをレース内で正規化
- ❌ **複勝率98%ではない**
- ✅ **レース内での総合評価 = 0.98**

#### **新モデル（Phase 7-8-5）**
- **ensemble_score 0.557** = レース内での相対的な評価が最高（1位予測）
- **binary_probability 0.272** = 複勝率27.2%（これが実際の複勝率）
- ✅ **複勝率を見たい場合は `binary_probability` を確認**

---

## 🔍 **旧モデル vs 新モデルの詳細比較**

### **1. アーキテクチャの違い**

| 項目 | 旧モデル | 新モデル |
|------|---------|---------|
| **特徴量選択** | ❌ なし（全特徴量使用） | ✅ Phase 7 Boruta選択<br>- Binary: 31特徴量<br>- Ranking: 25特徴量<br>- Regression: 24特徴量 |
| **ハイパーパラメータ** | ❌ デフォルト値 | ✅ Phase 8 Optuna最適化<br>（100 trials, CV=3） |
| **モデル品質** | 標準 | **最適化済み（高品質）** |

### **2. スコアの計算方法（共通）**

```python
# 両モデル共通のアンサンブル計算
ensemble_score = (
    binary_normalized × 0.3 +      # Binary分類（複勝圏内確率）
    ranking_normalized × 0.5 +     # Ranking予測（相対的強さ）
    regression_normalized × 0.2    # Regression予測（走破タイム）
)

# レース内で0〜1に正規化
final_score = (ensemble_score - min) / (max - min)
```

### **3. 出力フォーマットの違い**

#### **旧モデル出力例**
```
第1R: 7番 タイセイリノ（スコア: 0.98, ランクS）
      3番 アレナメヒコ（スコア: 0.85, ランクS）
      1番 ハイパーファイン（スコア: 0.74, ランクA）
```
- ⚠️ **複勝率が直接わからない**

#### **新モデル出力例**
```csv
race_id,umaban,ensemble_score,final_rank,binary_probability,ranking_score,predicted_time
2020_0107_43_03,8,0.557,1,0.272,−0.117,1380.5
2020_0107_43_03,12,0.500,2,0.798,−1.974,1365.2
2020_0107_43_03,10,0.489,3,0.018,0.970,1376.8
```
- ✅ **`binary_probability` で複勝率が明確**
- ✅ **各モデルの生スコアも確認可能**

---

## 🎯 **新モデルの優位性**

### **1. Phase 7: Boruta特徴量選択の効果**
- **ノイズ削減**: 重要でない特徴量を除外
- **過学習防止**: 本質的な特徴量のみ使用
- **精度向上**: 不要な情報を削減

### **2. Phase 8: Optuna最適化の効果**
- **学習率**: 最適な学習率を自動探索
- **木の深さ**: 最適な複雑度を調整
- **正則化**: 過学習を防ぐパラメータを最適化

### **3. 期待される精度向上**
- ✅ 特徴量選択 → ノイズ削減
- ✅ ハイパーパラメータ最適化 → 精度向上
- ✅ クロスバリデーション → 汎化性能向上

---

## 📊 **2025年データでの評価計画**

### **目的**
- 旧モデルと新モデルの精度を定量的に比較
- 対象期間: **2025/01/01 〜 2025/12/31**

### **Step 1: データ分割**

```python
# 2025年データを学習/テストに分割
# 既存の学習データ: 2020-2026 (Phase 0で生成済み)

# 評価用に2025年データを抽出
train_period = "2020-01-01 to 2024-12-31"  # 学習用
test_period  = "2025-01-01 to 2025-12-31"  # テスト用
```

### **Step 2: 評価指標**

#### **A. 的中率（Hit Rate）**
```python
# 単勝的中率
hit_rate_win = (予測1位が実際に1着だった回数) / (全レース数)

# 複勝的中率
hit_rate_place = (予測1位が実際に1〜3着だった回数) / (全レース数)

# 馬連的中率
hit_rate_quinella = (予測1-2位が実際の1-2着を含む回数) / (全レース数)

# 3連複的中率
hit_rate_trio = (予測1-3位が実際の1-3着を含む回数) / (全レース数)
```

#### **B. 予測精度（Ranking Metrics）**
```python
# NDCG@3 (Normalized Discounted Cumulative Gain)
# 上位3頭の予測精度を評価
from sklearn.metrics import ndcg_score

# 平均着順誤差（MAE）
mean_absolute_error = mean(|predicted_rank - actual_rank|)

# スピアマン順位相関係数
from scipy.stats import spearmanr
correlation = spearmanr(predicted_ranks, actual_ranks)
```

#### **C. 回収率（ROI）**
```python
# 単勝回収率
roi_win = (配当総額) / (購入額) × 100

# 複勝回収率
roi_place = (配当総額) / (購入額) × 100
```

### **Step 3: 評価スクリプトの作成**

```python
# scripts/evaluation/evaluate_2025_performance.py

import pandas as pd
import numpy as np
from sklearn.metrics import ndcg_score
from scipy.stats import spearmanr

def evaluate_model(predictions_csv, actuals_csv):
    """
    モデルの予測精度を評価
    
    Parameters:
    -----------
    predictions_csv : str
        予測結果ファイル（race_id, umaban, final_rank, ensemble_score）
    actuals_csv : str
        実際の結果ファイル（race_id, umaban, actual_rank）
    
    Returns:
    --------
    metrics : dict
        評価指標の辞書
    """
    
    # データ読み込み
    preds = pd.read_csv(predictions_csv, encoding='shift-jis')
    actuals = pd.read_csv(actuals_csv, encoding='shift-jis')
    
    # マージ
    merged = pd.merge(preds, actuals, on=['race_id', 'umaban'])
    
    # 1. 的中率
    hit_rate_win = (merged[merged['final_rank'] == 1]['actual_rank'] == 1).sum() / merged['race_id'].nunique()
    hit_rate_place = (merged[merged['final_rank'] == 1]['actual_rank'] <= 3).sum() / merged['race_id'].nunique()
    
    # 2. NDCG@3
    ndcg_scores = []
    for race_id in merged['race_id'].unique():
        race = merged[merged['race_id'] == race_id].sort_values('umaban')
        # 真のランキング: 着順が小さいほど良い
        y_true = [[1.0 / rank if rank <= 3 else 0 for rank in race['actual_rank']]]
        # 予測スコア: ensemble_scoreが高いほど良い
        y_pred = [race['ensemble_score'].tolist()]
        ndcg_scores.append(ndcg_score(y_true, y_pred, k=3))
    
    ndcg_3 = np.mean(ndcg_scores)
    
    # 3. 平均着順誤差
    mae = np.mean(np.abs(merged['final_rank'] - merged['actual_rank']))
    
    # 4. スピアマン相関
    correlations = []
    for race_id in merged['race_id'].unique():
        race = merged[merged['race_id'] == race_id]
        corr, _ = spearmanr(race['final_rank'], race['actual_rank'])
        correlations.append(corr)
    
    spearman = np.mean(correlations)
    
    return {
        'hit_rate_win': hit_rate_win,
        'hit_rate_place': hit_rate_place,
        'ndcg_3': ndcg_3,
        'mae': mae,
        'spearman': spearman
    }

# 使用例
old_metrics = evaluate_model(
    'data/predictions/old_model/funabashi_2025_predictions.csv',
    'data/actuals/funabashi_2025_actuals.csv'
)

new_metrics = evaluate_model(
    'data/predictions/new_model/funabashi_2025_predictions.csv',
    'data/actuals/funabashi_2025_actuals.csv'
)

# 比較
print("旧モデル vs 新モデル")
print(f"単勝的中率: {old_metrics['hit_rate_win']:.2%} → {new_metrics['hit_rate_win']:.2%}")
print(f"複勝的中率: {old_metrics['hit_rate_place']:.2%} → {new_metrics['hit_rate_place']:.2%}")
print(f"NDCG@3: {old_metrics['ndcg_3']:.3f} → {new_metrics['ndcg_3']:.3f}")
print(f"着順誤差: {old_metrics['mae']:.2f} → {new_metrics['mae']:.2f}")
print(f"相関係数: {old_metrics['spearman']:.3f} → {new_metrics['spearman']:.3f}")
```

---

## 🚀 **残り13会場への取り組み計画**

### **全体方針**
1. **Phase 7 Ranking/Regression**: 残り13会場を一括実行
2. **Phase 8 Ranking/Regression**: 残り13会場を一括実行
3. **Phase 5 Ensemble**: 全14会場でアンサンブル統合
4. **評価**: 2025年データで旧モデルと新モデルを比較

---

### **実行計画（詳細）**

#### **Phase 1: Phase 7 Ranking 一括実行（13会場）**

```powershell
# E:\anonymous-keiba-ai\run_phase7_ranking_all.ps1

$venues = @(
    "monbetsu", "morioka", "mizusawa", "urawa",
    "ooi", "kawasaki", "kanazawa", "kasamatsu",
    "nagoya", "sonoda", "himeji", "kochi", "saga"
)

$total = $venues.Count
$current = 0

foreach ($venue in $venues) {
    $current++
    Write-Host "[$current/$total] Phase 7 Ranking: $venue" -ForegroundColor Green
    
    $input_file = "data\training\${venue}_2020-2026_with_time_PHASE78.csv"
    
    python scripts\phase7_feature_selection\run_boruta_ranking.py `
      $input_file `
      --max-iter 100 `
      --verbose
    
    Write-Host "✅ $venue Phase 7 Ranking 完了" -ForegroundColor Cyan
}

Write-Host "🎉 Phase 7 Ranking 全13会場完了！" -ForegroundColor Green
```

**推定時間**: 2〜4時間

---

#### **Phase 2: Phase 7 Regression 一括実行（13会場）**

```powershell
# E:\anonymous-keiba-ai\run_phase7_regression_all.ps1

$venues = @(
    "monbetsu", "morioka", "mizusawa", "urawa",
    "ooi", "kawasaki", "kanazawa", "kasamatsu",
    "nagoya", "sonoda", "himeji", "kochi", "saga"
)

$total = $venues.Count
$current = 0

foreach ($venue in $venues) {
    $current++
    Write-Host "[$current/$total] Phase 7 Regression: $venue" -ForegroundColor Green
    
    $input_file = "data\training\${venue}_2020-2026_with_time_PHASE78.csv"
    
    python scripts\phase7_feature_selection\run_boruta_regression.py `
      $input_file `
      --max-iter 100 `
      --verbose
    
    Write-Host "✅ $venue Phase 7 Regression 完了" -ForegroundColor Cyan
}

Write-Host "🎉 Phase 7 Regression 全13会場完了！" -ForegroundColor Green
```

**推定時間**: 2〜4時間

---

#### **Phase 3: Phase 8 Ranking 一括実行（13会場）**

```powershell
# E:\anonymous-keiba-ai\run_phase8_ranking_all.ps1

$venues = @(
    "monbetsu", "morioka", "mizusawa", "urawa",
    "ooi", "kawasaki", "kanazawa", "kasamatsu",
    "nagoya", "sonoda", "himeji", "kochi", "saga"
)

$total = $venues.Count
$current = 0

foreach ($venue in $venues) {
    $current++
    Write-Host "[$current/$total] Phase 8 Ranking: $venue" -ForegroundColor Green
    
    $input_file = "data\training\${venue}_2020-2026_with_time_PHASE78.csv"
    $features_file = "data\features\selected\${venue}_ranking_selected_features.csv"
    
    python scripts\phase8_auto_tuning\run_optuna_tuning_ranking.py `
      $input_file `
      --selected-features $features_file `
      --n-trials 100 `
      --timeout 7200 `
      --cv-folds 3 `
      --verbose
    
    Write-Host "✅ $venue Phase 8 Ranking 完了" -ForegroundColor Cyan
}

Write-Host "🎉 Phase 8 Ranking 全13会場完了！" -ForegroundColor Green
```

**推定時間**: 6〜13時間

---

#### **Phase 4: Phase 8 Regression 一括実行（13会場）**

```powershell
# E:\anonymous-keiba-ai\run_phase8_regression_all.ps1

$venues = @(
    "monbetsu", "morioka", "mizusawa", "urawa",
    "ooi", "kawasaki", "kanazawa", "kasamatsu",
    "nagoya", "sonoda", "himeji", "kochi", "saga"
)

$total = $venues.Count
$current = 0

foreach ($venue in $venues) {
    $current++
    Write-Host "[$current/$total] Phase 8 Regression: $venue" -ForegroundColor Green
    
    $input_file = "data\training\${venue}_2020-2026_with_time_PHASE78.csv"
    $features_file = "data\features\selected\${venue}_regression_selected_features.csv"
    
    python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py `
      $input_file `
      --selected-features $features_file `
      --n-trials 100 `
      --timeout 7200 `
      --cv-folds 3 `
      --verbose
    
    Write-Host "✅ $venue Phase 8 Regression 完了" -ForegroundColor Cyan
}

Write-Host "🎉 Phase 8 Regression 全13会場完了！" -ForegroundColor Green
```

**推定時間**: 6〜13時間

---

## 📊 **2025年データでの評価手順**

### **Step 1: 2025年実績データの準備**

```bash
# 2025年のレース結果データを抽出
cd E:\anonymous-keiba-ai

# 各会場の2025年データを抽出
python scripts\evaluation\extract_2025_actuals.py ^
  --input data\training\funabashi_2020-2026_with_time_PHASE78.csv ^
  --output data\actuals\funabashi_2025_actuals.csv ^
  --start-date 2025-01-01 ^
  --end-date 2025-12-31
```

### **Step 2: 旧モデルで2025年を予測**

```bash
# Phase 3-4-5（旧モデル）で予測
python scripts\phase5_ensemble\ensemble_predictions.py ^
  funabashi ^
  data\actuals\funabashi_2025_actuals.csv ^
  --output-dir data\predictions\old_model
```

### **Step 3: 新モデルで2025年を予測**

```bash
# Phase 7-8-5（新モデル）で予測
python scripts\phase5_ensemble\ensemble_optimized.py ^
  funabashi ^
  data\actuals\funabashi_2025_actuals.csv ^
  --output-dir data\predictions\new_model
```

### **Step 4: 精度比較**

```bash
# 評価スクリプトを実行
python scripts\evaluation\evaluate_2025_performance.py ^
  --old-predictions data\predictions\old_model\funabashi_2025_predictions.csv ^
  --new-predictions data\predictions\new_model\funabashi_2025_predictions.csv ^
  --actuals data\actuals\funabashi_2025_actuals.csv ^
  --output-report data\evaluation\funabashi_comparison_report.json
```

---

## 📅 **実行スケジュール（推奨）**

### **短期（今日〜明日）**
- [x] 船橋 Phase 5 Ensemble テスト完了 ✅
- [ ] Phase 7 Ranking 一括実行（2〜4時間）
- [ ] Phase 7 Regression 一括実行（2〜4時間）

### **中期（今週末）**
- [ ] Phase 8 Ranking 一括実行（6〜13時間）
- [ ] Phase 8 Regression 一括実行（6〜13時間）

### **長期（来週）**
- [ ] 2025年データでの評価実施
- [ ] 旧モデルと新モデルの比較レポート作成
- [ ] 本番配信準備

---

## 🎯 **即座に実行すべきアクション**

### **今すぐローカルPCで実行**

```powershell
# Step 1: GitHubから最新版を取得
cd E:\anonymous-keiba-ai
git pull origin phase0_complete_fix_2026_02_07

# Step 2: Phase 7 Ranking 一括実行（2〜4時間）
.\run_phase7_ranking_all.ps1

# （完了後）Step 3: Phase 7 Regression 一括実行（2〜4時間）
.\run_phase7_regression_all.ps1

# （完了後）Step 4: Phase 8 Ranking 一括実行（6〜13時間、週末推奨）
.\run_phase8_ranking_all.ps1

# （完了後）Step 5: Phase 8 Regression 一括実行（6〜13時間、週末推奨）
.\run_phase8_regression_all.ps1
```

---

## 📊 **期待される成果**

### **定量的な改善目標**

| 指標 | 旧モデル（目標） | 新モデル（目標） | 改善率 |
|------|------------------|------------------|--------|
| 単勝的中率 | 25% | **30%+** | +20% |
| 複勝的中率 | 60% | **70%+** | +17% |
| NDCG@3 | 0.65 | **0.75+** | +15% |
| 着順誤差 | 2.5 | **2.0以下** | -20% |
| 相関係数 | 0.55 | **0.65+** | +18% |

### **定性的な改善**
- ✅ 特徴量選択によるノイズ削減
- ✅ ハイパーパラメータ最適化による精度向上
- ✅ `binary_probability` による複勝率の明確化
- ✅ 各モデルの生スコア確認可能

---

## 🎯 **まとめ**

### **スコアの意味（再確認）**
- ❌ **スコア 0.98 ≠ 複勝率98%**
- ✅ **スコア 0.98 = レース内での総合評価が最高（1位予測）**
- ✅ **複勝率は新モデルの `binary_probability` で確認**

### **新モデルの優位性**
1. ✅ Phase 7: Boruta特徴量選択（ノイズ削減）
2. ✅ Phase 8: Optuna最適化（精度向上）
3. ✅ Binary Probability が明確（複勝率がわかる）

### **次のアクション（優先順位順）**
1. **Phase 7 Ranking 実行**（13会場、2〜4時間）
2. **Phase 7 Regression 実行**（13会場、2〜4時間）
3. **Phase 8 Ranking/Regression 実行**（13会場、12〜26時間）
4. **2025年データで評価**（旧モデル vs 新モデル）

---

**最終更新**: 2026-02-11  
**次のアクション**: `.\run_phase7_ranking_all.ps1` を実行してください！ 🚀
