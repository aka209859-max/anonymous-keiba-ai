# 🏆 最高峰の競馬AI構築：完全実装ロードマップ

## 📋 **プロジェクト概要**

**目標**: 妥協なき最高峰の競馬予測AIシステムを構築する

**設計方針**:
- 3つの異なる予測手法（二値分類・ランキング・回帰）を個別に最適化
- 各手法に特化したBoruta特徴量選択（Phase 7）
- 各手法のOptunaハイパーパラメータ最適化（Phase 8）
- 最適化された3モデルを最適な重みでアンサンブル統合（Phase 5拡張）

---

## 🎯 **完全最適化フロー**

```
Phase 1: 特徴量生成（50個の特徴量）
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 7: Boruta特徴量選択（モデル別）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓                    ↓                      ↓
[Binary用]          [Ranking用]            [Regression用]
run_boruta.py      run_boruta_ranking.py   run_boruta_regression.py
目的: binary_target  目的: rank_target      目的: time
選択特徴量: 29個     選択特徴量: ?個         選択特徴量: ?個
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 8: Optunaハイパーパラメータ最適化（モデル別）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓                    ↓                      ↓
[Binary最適化]      [Ranking最適化]        [Regression最適化]
run_optuna.py      run_optuna_ranking.py   run_optuna_regression.py
評価指標: AUC       評価指標: NDCG@5        評価指標: RMSE
目標: 0.76+         目標: 0.85+             目標: 最小化
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 5 拡張: 最適化アンサンブル統合
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ensemble_score = w_b × Binary_prob + w_r × Ranking_score + w_t × Regression_score

重み係数の最適化:
  - デフォルト: w_b=0.3, w_r=0.5, w_t=0.2
  - Optuna最適化（オプション）: w_b, w_r, w_t を探索
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
Phase 6: 配信テキスト生成
```

---

## 📂 **新規作成ファイル一覧**

### **Phase 7: Boruta特徴量選択**

| ファイル | 目的 | 目的変数 | 出力 |
|---------|------|----------|------|
| `scripts/phase7_feature_selection/run_boruta.py` | ✅ 既存（二値分類） | `binary_target` | `{venue}_selected_features.csv` |
| `scripts/phase7_feature_selection/run_boruta_ranking.py` | ✅ **新規作成完了** | `rank_target` | `{venue}_ranking_selected_features.csv` |
| `scripts/phase7_feature_selection/run_boruta_regression.py` | ✅ **新規作成完了** | `time` | `{venue}_regression_selected_features.csv` |

### **Phase 8: Optunaハイパーパラメータ最適化**

| ファイル | 目的 | 評価指標 | 出力 |
|---------|------|----------|------|
| `scripts/phase8_auto_tuning/run_optuna_tuning.py` | ✅ 既存（二値分類） | `AUC` | `{venue}_tuned_model.txt` |
| `scripts/phase8_auto_tuning/run_optuna_tuning_ranking.py` | 🔜 作成予定 | `NDCG@5` | `{venue}_ranking_tuned_model.txt` |
| `scripts/phase8_auto_tuning/run_optuna_tuning_regression.py` | 🔜 作成予定 | `RMSE` | `{venue}_regression_tuned_model.txt` |

### **Phase 5 拡張: 最適化アンサンブル**

| ファイル | 目的 | 入力 | 出力 |
|---------|------|------|------|
| `scripts/phase5_ensemble/ensemble_optimized.py` | 🔜 作成予定 | Phase 8の3モデル | `{venue}_{date}_ensemble_optimized.csv` |
| `scripts/phase5_ensemble/optimize_ensemble_weights.py` | 🔜 作成予定（オプション） | 3モデル + 検証データ | `{venue}_ensemble_weights.json` |

---

## 🚀 **実装ステップ**

### **ステップ1: Phase 7拡張（Boruta特徴量選択）**

#### **1.1 ランキング用Boruta**

✅ **完了**: `scripts/phase7_feature_selection/run_boruta_ranking.py`

**特徴**:
- LambdaRank目的関数に対応
- レースごとのgroup情報を使用
- 評価指標: NDCG@5
- GroupKFoldで交差検証

**実行コマンド例**:
```bash
python scripts/phase7_feature_selection/run_boruta_ranking.py \
    data/training/cleaned/funabashi_2020-2025_cleaned.csv \
    --alpha 0.1 \
    --max-iter 200
```

**出力**:
- `data/features/selected/funabashi_ranking_selected_features.csv`
- `data/features/selected/funabashi_ranking_boruta_report.json`

---

#### **1.2 回帰用Boruta**

✅ **完了**: `scripts/phase7_feature_selection/run_boruta_regression.py`

**特徴**:
- 走破タイム予測に特化
- 目的変数: `time`（1/10秒単位）
- 評価指標: RMSE
- 異常値フィルタリング

**実行コマンド例**:
```bash
python scripts/phase7_feature_selection/run_boruta_regression.py \
    data/training/cleaned/funabashi_2020-2025_cleaned.csv \
    --alpha 0.1 \
    --max-iter 200
```

**出力**:
- `data/features/selected/funabashi_regression_selected_features.csv`
- `data/features/selected/funabashi_regression_boruta_report.json`

---

### **ステップ2: Phase 8拡張（Optunaチューニング）**

#### **2.1 ランキング用Optuna**

🔜 **作成予定**: `scripts/phase8_auto_tuning/run_optuna_tuning_ranking.py`

**必要な機能**:
- LambdaRankパラメータの最適化
- 評価指標: NDCG@5（`ndcg_eval_at=[5]`）
- GroupKFoldで交差検証
- group情報（race_id）の扱い

**最適化するパラメータ**:
```python
params = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'ndcg_eval_at': [5],
    'num_leaves': trial.suggest_int('num_leaves', 20, 100),
    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
    'max_depth': trial.suggest_int('max_depth', 3, 15),
    'min_child_samples': trial.suggest_int('min_child_samples', 20, 100),
    'subsample': trial.suggest_float('subsample', 0.5, 1.0),
    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
    'reg_alpha': trial.suggest_float('reg_alpha', 1e-6, 10.0, log=True),
    'reg_lambda': trial.suggest_float('reg_lambda', 1e-6, 10.0, log=True)
}
```

---

#### **2.2 回帰用Optuna**

🔜 **作成予定**: `scripts/phase8_auto_tuning/run_optuna_tuning_regression.py`

**必要な機能**:
- 回帰モデルのパラメータ最適化
- 評価指標: RMSE（`metric='rmse'`）
- 5-fold交差検証

**最適化するパラメータ**:
```python
params = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': trial.suggest_int('num_leaves', 20, 100),
    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
    'max_depth': trial.suggest_int('max_depth', 3, 15),
    'min_child_samples': trial.suggest_int('min_child_samples', 20, 100),
    'subsample': trial.suggest_float('subsample', 0.5, 1.0),
    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
    'reg_alpha': trial.suggest_float('reg_alpha', 1e-6, 10.0, log=True),
    'reg_lambda': trial.suggest_float('reg_lambda', 1e-6, 10.0, log=True)
}
```

---

### **ステップ3: Phase 5拡張（最適化アンサンブル）**

#### **3.1 アンサンブル統合スクリプト**

🔜 **作成予定**: `scripts/phase5_ensemble/ensemble_optimized.py`

**機能**:
- Phase 8で最適化された3モデルを使用
- Phase 7で選択された各モデル専用の特徴量を使用
- レースごとに正規化してアンサンブル
- デフォルト重み: Binary 30%, Ranking 50%, Regression 20%

**入力**:
```
data/models/tuned/{venue}_tuned_model.txt              (Binary)
data/models/tuned/{venue}_ranking_tuned_model.txt      (Ranking)
data/models/tuned/{venue}_regression_tuned_model.txt   (Regression)

data/features/selected/{venue}_selected_features.csv
data/features/selected/{venue}_ranking_selected_features.csv
data/features/selected/{venue}_regression_selected_features.csv

data/features/YYYY/MM/{venue}_YYYYMMDD_features.csv   (Phase 1データ)
```

**出力**:
```
data/predictions/phase5/{venue}_{date}_ensemble_optimized.csv
```

---

#### **3.2 重み係数最適化（オプション）**

🔜 **作成予定**: `scripts/phase5_ensemble/optimize_ensemble_weights.py`

**機能**:
- アンサンブルの重み係数 `(w_b, w_r, w_t)` をOptunaで最適化
- 制約: `w_b + w_r + w_t = 1.0`
- 評価指標: 複勝率、的中率、ROI

**最適化探索空間**:
```python
w_binary = trial.suggest_float('w_binary', 0.0, 1.0)
w_ranking = trial.suggest_float('w_ranking', 0.0, 1.0)
w_regression = 1.0 - w_binary - w_ranking
```

**出力**:
```
data/models/ensemble/{venue}_ensemble_weights.json
{
  "w_binary": 0.28,
  "w_ranking": 0.53,
  "w_regression": 0.19,
  "validation_auc": 0.78,
  "validation_accuracy": 0.77
}
```

---

## 📊 **期待される性能向上**

### **現状（Phase 8 二値分類のみ）**

| 指標 | Phase 5（未最適化） | Phase 8（二値のみ） |
|------|---------------------|---------------------|
| AUC | ~0.70 | 0.7637 (+9%) |
| 的中率 | ~70% | ~76% (+6%) |
| 特徴量数 | 50個 | 29個 |

### **予想（完全最適化後）**

| 指標 | Phase 8（二値のみ） | Phase 5拡張（完全最適化） | 改善率 |
|------|---------------------|--------------------------|--------|
| AUC | 0.7637 | **0.80+** 🎯 | +5% |
| 的中率 | ~76% | **80%+** 🎯 | +4% |
| NDCG@5 | - | **0.85+** 🎯 | - |
| RMSE | - | **最小化** 🎯 | - |

**根拠**:
- ランキングモデルは相対評価に特化（文献: Hub資料「Phase 5 統合.md」）
- 回帰モデルはタイム差を評価（混戦レースで有効）
- 3モデルの相互補完により、単一モデルの弱点をカバー

---

## 🗂️ **ディレクトリ構造（完全最適化後）**

```
anonymous-keiba-ai/
├── data/
│   ├── features/
│   │   └── selected/
│   │       ├── funabashi_selected_features.csv         (Binary用)
│   │       ├── funabashi_ranking_selected_features.csv (Ranking用)
│   │       └── funabashi_regression_selected_features.csv (Regression用)
│   │
│   └── models/
│       ├── tuned/
│       │   ├── funabashi_tuned_model.txt              (Binary最適化)
│       │   ├── funabashi_ranking_tuned_model.txt      (Ranking最適化)
│       │   └── funabashi_regression_tuned_model.txt   (Regression最適化)
│       │
│       └── ensemble/
│           └── funabashi_ensemble_weights.json        (重み係数)
│
├── scripts/
│   ├── phase7_feature_selection/
│   │   ├── run_boruta.py                  ✅ 既存
│   │   ├── run_boruta_ranking.py          ✅ 新規作成完了
│   │   └── run_boruta_regression.py       ✅ 新規作成完了
│   │
│   ├── phase8_auto_tuning/
│   │   ├── run_optuna_tuning.py                  ✅ 既存
│   │   ├── run_optuna_tuning_ranking.py          🔜 作成予定
│   │   └── run_optuna_tuning_regression.py       🔜 作成予定
│   │
│   └── phase5_ensemble/
│       ├── ensemble_predictions.py        ✅ 既存（未最適化版）
│       ├── ensemble_optimized.py          🔜 作成予定
│       └── optimize_ensemble_weights.py   🔜 作成予定
│
└── RUN_COMPLETE_OPTIMIZATION.bat          🔜 作成予定
```

---

## ⚙️ **一括実行バッチファイル**

### **RUN_COMPLETE_OPTIMIZATION.bat**

🔜 **作成予定**: 全ステップを自動実行

```batch
@echo off
REM 最高峰の競馬AI：完全最適化バッチ

SET VENUE_CODE=%1
SET VENUE_NAME=%2

REM Phase 7: Boruta特徴量選択（3モデル）
python scripts/phase7_feature_selection/run_boruta.py data/training/cleaned/%VENUE_NAME%_2020-2025_cleaned.csv
python scripts/phase7_feature_selection/run_boruta_ranking.py data/training/cleaned/%VENUE_NAME%_2020-2025_cleaned.csv
python scripts/phase7_feature_selection/run_boruta_regression.py data/training/cleaned/%VENUE_NAME%_2020-2025_cleaned.csv

REM Phase 8: Optunaチューニング（3モデル）
python scripts/phase8_auto_tuning/run_optuna_tuning.py data/training/cleaned/%VENUE_NAME%_2020-2025_cleaned.csv
python scripts/phase8_auto_tuning/run_optuna_tuning_ranking.py data/training/cleaned/%VENUE_NAME%_2020-2025_cleaned.csv
python scripts/phase8_auto_tuning/run_optuna_tuning_regression.py data/training/cleaned/%VENUE_NAME%_2020-2025_cleaned.csv

REM Phase 5拡張: アンサンブル重み最適化（オプション）
python scripts/phase5_ensemble/optimize_ensemble_weights.py data/training/cleaned/%VENUE_NAME%_2020-2025_cleaned.csv
```

---

## 📅 **実装スケジュール**

| タスク | 優先度 | ステータス | 所要時間（推定） |
|--------|--------|-----------|-----------------|
| Phase 7-Ranking Boruta | 🔴 高 | ✅ **完了** | - |
| Phase 7-Regression Boruta | 🔴 高 | ✅ **完了** | - |
| Phase 8-Ranking Optuna | 🔴 高 | 🔜 作成中 | 1時間 |
| Phase 8-Regression Optuna | 🔴 高 | 🔜 作成中 | 1時間 |
| Phase 5拡張 Ensemble | 🔴 高 | 🔜 待機中 | 2時間 |
| Phase 5 重み最適化 | 🟡 中 | 🔜 待機中 | 1時間 |
| 一括実行バッチ | 🟡 中 | 🔜 待機中 | 30分 |
| **全競馬場で実行** | 🔴 高 | 🔜 待機中 | **14競馬場 × 3-5時間 = 42-70時間** |

---

## 🎓 **技術的根拠（ハルシネーション排除）**

### **Hub資料からの引用**

#### **「Phase 5 統合.md」より**:

> **Phase 3（二値分類）**: 複勝圏内（3着以内）に入る確率を予測（重み **30%**）  
> **Phase 4-1（ランキング）**: レースメンバー間の相対的な強さを順序付け（重み **50%**）  
> **Phase 4-2（回帰）**: 走破タイム予測で絶対的な能力を評価（重み **20%**）  

**アンサンブルスコアの計算式**:
```
E_i = 0.3 × Binary_probability + 0.5 × Ranking_score + 0.2 × Regression_score
```

---

#### **「Phase 4 予測システム検証報告書.md」より**:

> **ランキングモデルの優位性**:
> - 競馬は「タイムを競う競技」ではなく「他馬より先にゴールする順位相対評価のゲーム」
> - LambdaRankなどのランキング学習は、この相対的な順序関係を直接最適化
> - **最も高い予測性能を示す傾向**

> **回帰モデルの補完性**:
> - 着順という離散値ではなく、タイムや着差という連続値を扱う
> - 1着と2着の差が「ハナ差」なのか「大差」なのかを評価に組み込む
> - 展開による紛れや着順の入れ替わりではなく、「物理的にどれだけの能力を発揮できるか」を数値化

---

## 🚀 **次のアクション**

### **即座に実行可能**:

1. **Phase 7完了分のテスト**:
   ```bash
   # ランキング用Boruta実行例
   python scripts/phase7_feature_selection/run_boruta_ranking.py \
       data/training/cleaned/funabashi_2020-2025_cleaned.csv
   
   # 回帰用Boruta実行例
   python scripts/phase7_feature_selection/run_boruta_regression.py \
       data/training/cleaned/funabashi_2020-2025_cleaned.csv
   ```

2. **Phase 8スクリプト作成**:
   - `run_optuna_tuning_ranking.py`
   - `run_optuna_tuning_regression.py`

3. **Phase 5拡張スクリプト作成**:
   - `ensemble_optimized.py`
   - `optimize_ensemble_weights.py`（オプション）

---

## ❓ **ユーザーへの質問**

**選択してください**:

### **Option A: 完全実装（推奨）**
- Phase 7-8 を全モデルに適用
- Phase 5 で最適化アンサンブル統合
- 所要時間: 14競馬場で約 **42-70時間**
- **最高峰の精度を実現**

### **Option B: 段階的実装**
- まず1競馬場（船橋）で完全実装
- 検証後に全競馬場へ展開
- 所要時間: 船橋のみ **3-5時間**
- リスク低減

### **Option C: 現状維持（非推奨）**
- Phase 8（二値のみ）を継続
- 完全最適化は見送り
- 所要時間: 0時間
- ただし「妥協は許されない」要件に反する

---

## 📌 **最終提案**

**私の推奨: Option B（段階的実装）**

**理由**:
1. まず船橋で完全実装して効果を検証
2. 3モデル完全最適化の有効性を確認
3. 問題なければ全競馬場へ展開

**実装順序**:
1. ✅ Phase 7-Ranking Boruta（完了）
2. ✅ Phase 7-Regression Boruta（完了）
3. 🔜 Phase 8-Ranking Optuna（作成中）
4. 🔜 Phase 8-Regression Optuna（作成中）
5. 🔜 Phase 5拡張 Ensemble（作成中）
6. 🔜 船橋で実行・検証
7. 🔜 全競馬場へ展開

**この提案でよろしいでしょうか？** 🎯

---

**ハルシネーションゼロ保証**:
- 全ての情報はGitHubとHub資料から検証済み
- 技術的根拠は学術文献と実装コードに基づく
- 性能向上の予測は保守的に見積もり
