# Phase 7/8/5 完全実装ガイド

## 📋 目次

1. [概要](#概要)
2. [システム構成](#システム構成)
3. [Phase 7: Boruta特徴選択](#phase-7-boruta特徴選択)
4. [Phase 8: Optunaハイパーパラメータ最適化](#phase-8-optunaハイパーパラメータ最適化)
5. [Phase 5: 最適化アンサンブル統合](#phase-5-最適化アンサンブル統合)
6. [実行手順](#実行手順)
7. [トラブルシューティング](#トラブルシューティング)
8. [期待される性能改善](#期待される性能改善)

---

## 概要

本ガイドは、**究極の競馬AIシステム**構築のための完全実装手順を説明します。

### 🎯 目的

従来のPhase 5（AUC ~0.70）から、Phase 7/8の最適化を経て**Phase 5 Optimized（AUC 0.80+目標）**への性能向上を実現します。

### 🔑 キーポイント

- **3つのモデルタイプ**を個別に最適化：Binary分類 / Ranking / Regression
- **Phase 7 Boruta**で各モデル専用の特徴量を選択
- **Phase 8 Optuna**で各モデルのハイパーパラメータを最適化
- **Phase 5 Ensemble**で3つの最適化モデルを統合

### ⚡ 期待される性能

| 項目 | Phase 5（従来） | Phase 5 Optimized（目標） | 改善率 |
|------|----------------|------------------------|--------|
| AUC | ~0.70 | 0.80+ | +14%以上 |
| 複勝的中率 | ~35% | 45%+ | +10%以上 |
| 回収率 | 80-90% | 100-110% | +15-25% |

---

## システム構成

### 📂 ディレクトリ構造

```
E:\anonymous-keiba-ai\
├─ data\
│  ├─ training\                           # 学習データ
│  │  ├─ funabashi_2020-2025_with_time.csv
│  │  ├─ kawasaki_2020-2025_with_time.csv
│  │  └─ ... (全14会場)
│  ├─ features\
│  │  └─ selected\                        # Phase 7出力
│  │     ├─ funabashi_selected_features.csv (Binary用)
│  │     ├─ funabashi_ranking_selected_features.csv (Ranking用)
│  │     ├─ funabashi_regression_selected_features.csv (Regression用)
│  │     └─ ... (全14会場 × 3モデル)
│  ├─ models\
│  │  └─ tuned\                          # Phase 8出力
│  │     ├─ funabashi_tuned_model.txt (Binary用)
│  │     ├─ funabashi_ranking_tuned_model.txt (Ranking用)
│  │     ├─ funabashi_regression_tuned_model.txt (Regression用)
│  │     └─ ... (全14会場 × 3モデル)
│  ├─ predictions\
│  │  └─ phase5_optimized\               # Phase 5出力
│  │     ├─ funabashi_20260210_ensemble_optimized.csv
│  │     └─ ...
│  └─ reports\
│     └─ phase7_feature_selection\       # Phase 7レポート
├─ scripts\
│  ├─ phase7_feature_selection\
│  │  ├─ run_boruta_selection.py         # Binary用
│  │  ├─ run_boruta_ranking.py           # Ranking用
│  │  └─ run_boruta_regression.py        # Regression用
│  ├─ phase8_auto_tuning\
│  │  ├─ run_optuna_tuning.py            # Binary用
│  │  ├─ run_optuna_tuning_ranking.py    # Ranking用
│  │  └─ run_optuna_tuning_regression.py # Regression用
│  └─ phase5_ensemble\
│     └─ ensemble_optimized.py           # 最適化アンサンブル統合
├─ RUN_PHASE7_COMPLETE.bat               # Phase 7一括実行
├─ RUN_PHASE8_COMPLETE.bat               # Phase 8一括実行
├─ RUN_ULTIMATE_FUNABASHI.bat            # 船橋テスト実行
└─ RUN_ULTIMATE_ALL_VENUES.bat           # 全会場展開
```

### 🔄 処理フロー

```
[学習データ]
    ↓
[Phase 7: Boruta特徴選択]
    ├─ Binary用特徴選択
    ├─ Ranking用特徴選択
    └─ Regression用特徴選択
    ↓
[Phase 8: Optunaハイパーパラメータ最適化]
    ├─ Binary分類モデル最適化 (AUC最大化)
    ├─ Rankingモデル最適化 (NDCG@5最大化)
    └─ Regressionモデル最適化 (RMSE最小化)
    ↓
[Phase 5: 最適化アンサンブル統合]
    └─ 3モデル統合予測 (Binary 30% + Ranking 50% + Regression 20%)
    ↓
[最終予測結果]
```

---

## Phase 7: Boruta特徴選択

### 🎯 目的

各モデルタイプに最適な特徴量を自動選択します。

### 📊 3つのモデルタイプ別アプローチ

#### 1. Binary分類用（複勝圏内予測）

**目的**: 複勝圏内（3着以内）に入るかを予測

**目的変数**: `binary_target` (0 or 1)

**評価指標**: AUC (Area Under ROC Curve)

**実行コマンド**:
```bash
python scripts\phase7_feature_selection\run_boruta_selection.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --max-iter 100 ^
    --n-estimators 100
```

**出力**:
- `data/features/selected/funabashi_selected_features.csv`
- `data/reports/phase7_feature_selection/funabashi_boruta_report.txt`
- `data/reports/phase7_feature_selection/funabashi_feature_importance.png`

---

#### 2. Ranking用（相対順位予測）

**目的**: 馬の相対的な強さを順位付け

**目的変数**: `rank_target` (順位スコア、1着=最大値)

**評価指標**: NDCG@5 (上位5頭の順位精度)

**特徴**:
- LambdaRank目的関数
- GroupKFold CV（レース単位でグループ化）

**実行コマンド**:
```bash
python scripts\phase7_feature_selection\run_boruta_ranking.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --max-iter 100 ^
    --n-estimators 100
```

**出力**:
- `data/features/selected/funabashi_ranking_selected_features.csv`
- `data/reports/phase7_feature_selection/funabashi_ranking_boruta_report.txt`
- `data/reports/phase7_feature_selection/funabashi_ranking_feature_importance.png`

---

#### 3. Regression用（走破タイム予測）

**目的**: レース走破タイムを予測

**目的変数**: `time` (走破タイム、1/10秒単位)

**評価指標**: RMSE (Root Mean Squared Error)

**特徴**:
- 回帰目的関数
- 無効タイム（<0 または >10000）は除外

**実行コマンド**:
```bash
python scripts\phase7_feature_selection\run_boruta_regression.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --max-iter 100 ^
    --n-estimators 100
```

**出力**:
- `data/features/selected/funabashi_regression_selected_features.csv`
- `data/reports/phase7_feature_selection/funabashi_regression_boruta_report.txt`
- `data/reports/phase7_feature_selection/funabashi_regression_feature_importance.png`

---

### 🔧 Borutaアルゴリズムの仕組み

1. **シャドウ特徴量生成**: 元の特徴量をシャッフルしたコピーを作成
2. **重要度比較**: 元の特徴量 vs シャドウ特徴量で重要度を比較
3. **統計的検定**: 元の特徴量がシャドウより有意に重要かを判定
4. **繰り返し**: 100イテレーション（`--max-iter 100`）で確実性を高める

### 📈 期待される特徴量数

| モデルタイプ | 元の特徴量数 | 選択後（目安） | 削減率 |
|------------|------------|--------------|--------|
| Binary | 50個 | 20-30個 | 40-50% |
| Ranking | 50個 | 25-35個 | 30-40% |
| Regression | 50個 | 15-25個 | 50-60% |

※ 会場やデータにより変動します

---

## Phase 8: Optunaハイパーパラメータ最適化

### 🎯 目的

Phase 7で選択した特徴量を使い、各モデルのハイパーパラメータを自動最適化します。

### 🔬 最適化戦略

- **探索アルゴリズム**: TPE (Tree-structured Parzen Estimator)
- **試行回数**: 100回（`--n-trials 100`）
- **タイムアウト**: 2時間/モデル（`--timeout 7200`）
- **Cross-Validation**: 3-fold

### 📊 3つのモデルタイプ別最適化

#### 1. Binary分類モデル最適化

**目的関数**: `objective='binary'`

**評価指標**: AUC（最大化）

**CV戦略**: StratifiedKFold（クラスバランスを保持）

**最適化パラメータ**:
- `learning_rate`: 0.01〜0.3（対数スケール）
- `num_leaves`: 20〜200
- `max_depth`: 3〜15
- `min_data_in_leaf`: 10〜100
- `feature_fraction`: 0.5〜1.0
- `bagging_fraction`: 0.5〜1.0
- `lambda_l1`: 0.0〜10.0
- `lambda_l2`: 0.0〜10.0

**実行コマンド**:
```bash
python scripts\phase8_auto_tuning\run_optuna_tuning.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --selected-features data\features\selected\funabashi_selected_features.csv ^
    --n-trials 100 ^
    --timeout 7200 ^
    --cv-folds 3
```

**出力**:
- `data/models/tuned/funabashi_tuned_model.txt`
- `data/models/tuned/funabashi_best_params.csv`
- `data/models/tuned/funabashi_tuning_history.png`
- `data/models/tuned/funabashi_tuning_report.json`

---

#### 2. Rankingモデル最適化

**目的関数**: `objective='lambdarank'`

**評価指標**: NDCG@5（最大化）

**CV戦略**: GroupKFold（レース単位でグループ化）

**特徴**:
- レース単位でグループを保持（同一レースの馬は同じグループ）
- `group`パラメータを使用してレース情報を渡す

**実行コマンド**:
```bash
python scripts\phase8_auto_tuning\run_optuna_tuning_ranking.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --selected-features data\features\selected\funabashi_ranking_selected_features.csv ^
    --n-trials 100 ^
    --timeout 7200 ^
    --cv-folds 3
```

**出力**:
- `data/models/tuned/funabashi_ranking_tuned_model.txt`
- `data/models/tuned/funabashi_ranking_best_params.csv`
- `data/models/tuned/funabashi_ranking_tuning_history.png`
- `data/models/tuned/funabashi_ranking_tuning_report.json`

---

#### 3. Regressionモデル最適化

**目的関数**: `objective='regression'`

**評価指標**: RMSE（最小化）

**CV戦略**: KFold（標準的な分割）

**データフィルタリング**:
- 無効タイム（`time < 0` または `time > 10000`）を除外
- 1/10秒単位のタイムデータを使用

**実行コマンド**:
```bash
python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --selected-features data\features\selected\funabashi_regression_selected_features.csv ^
    --n-trials 100 ^
    --timeout 7200 ^
    --cv-folds 3
```

**出力**:
- `data/models/tuned/funabashi_regression_tuned_model.txt`
- `data/models/tuned/funabashi_regression_best_params.csv`
- `data/models/tuned/funabashi_regression_tuning_history.png`
- `data/models/tuned/funabashi_regression_tuning_report.json`

---

### 📈 期待される性能改善

| モデル | Phase 8前（Phase 3-5標準） | Phase 8後（最適化） | 改善率 |
|--------|-------------------------|------------------|--------|
| Binary (AUC) | 0.68-0.72 | 0.75-0.80 | +5-10% |
| Ranking (NDCG@5) | 0.60-0.65 | 0.70-0.75 | +10-15% |
| Regression (RMSE) | 150-200 | 100-130 | -30-40% |

---

## Phase 5: 最適化アンサンブル統合

### 🎯 目的

Phase 7/8で最適化した3つのモデルを統合し、最終予測を生成します。

### 🔧 統合戦略

#### アンサンブル重み配分

```
最終スコア = Binary (30%) + Ranking (50%) + Regression (20%)
```

**理由**:
- **Ranking (50%)**: 相対的な強さが最も重要
- **Binary (30%)**: 複勝圏内確率も重要な判断材料
- **Regression (20%)**: タイム予測は補助的な情報

#### スコア正規化

各モデルの出力をレース単位で0〜1に正規化します：

```python
# Binary分類: 大きいほど良い（複勝圏内確率）
binary_normalized = (binary_probability - min) / (max - min)

# Ranking: 大きいほど良い（相対順位スコア）
ranking_normalized = (ranking_score - min) / (max - min)

# Regression: 小さいほど良い（走破タイム）
regression_normalized = 1.0 - (predicted_time - min) / (max - min)
```

### 🚀 実行方法

#### 単一会場予測

```bash
python scripts\phase5_ensemble\ensemble_optimized.py ^
    funabashi ^
    test_data\funabashi_20260210.csv ^
    --output-dir data\predictions\phase5_optimized
```

#### 重みカスタマイズ

```bash
python scripts\phase5_ensemble\ensemble_optimized.py ^
    kawasaki ^
    test_data\kawasaki_20260210.csv ^
    --weight-binary 0.4 ^
    --weight-ranking 0.4 ^
    --weight-regression 0.2
```

### 📤 出力ファイル

#### 1. 予測結果CSV

**ファイル名**: `{venue}_{date}_ensemble_optimized.csv`

**カラム**:
- `race_id`: レースID
- `umaban`: 馬番
- `ensemble_score`: 統合スコア（0〜1）
- `final_rank`: 最終予測順位
- `binary_probability`: Binary予測確率
- `binary_rank`: Binary予測順位
- `ranking_score`: Ranking予測スコア
- `ranking_rank`: Ranking予測順位
- `predicted_time`: Regression予測タイム
- `time_rank`: Regression予測順位

#### 2. サマリーJSON

**ファイル名**: `{venue}_{date}_ensemble_optimized_summary.json`

**内容**:
```json
{
  "venue": "funabashi",
  "date": "20260210",
  "total_records": 120,
  "total_races": 12,
  "ensemble_score_stats": {
    "mean": 0.5234,
    "std": 0.2156,
    "min": 0.0823,
    "max": 0.9567
  },
  "binary_probability_stats": {...},
  "ranking_score_stats": {...},
  "predicted_time_stats": {...}
}
```

---

## 実行手順

### 🏁 初回セットアップ

#### 1. 環境確認

```bash
python --version  # Python 3.8以上
pip list | findstr "lightgbm pandas numpy scikit-learn optuna matplotlib"
```

#### 2. ディレクトリ確認

```bash
dir data\training\*_with_time.csv
```

全14会場の学習データ（`*_with_time.csv`）が存在することを確認してください。

---

### 🚀 実行パターン

#### パターンA: 段階的実行（推奨）

**ステップ1**: Phase 7実行（全会場）
```bash
RUN_PHASE7_COMPLETE.bat
```
所要時間: 約2〜4時間

**ステップ2**: Phase 8実行（全会場）
```bash
RUN_PHASE8_COMPLETE.bat
```
所要時間: 約4〜8時間

**ステップ3**: 船橋テスト
```bash
RUN_ULTIMATE_FUNABASHI.bat
```
所要時間: 約1.5〜2時間（Phase 7/8がスキップされるため短縮）

**ステップ4**: 全会場展開（オプション）
```bash
RUN_ULTIMATE_ALL_VENUES.bat
```

---

#### パターンB: 一括実行

```bash
RUN_ULTIMATE_ALL_VENUES.bat
```

Phase 7 → Phase 8 → Phase 5を全会場一括実行します。

所要時間: 約12〜24時間

**注意**: PCのスリープ設定を無効化してください。

---

#### パターンC: 個別会場テスト

**Phase 7実行**:
```bash
python scripts\phase7_feature_selection\run_boruta_selection.py ^
    data\training\funabashi_2020-2025_with_time.csv

python scripts\phase7_feature_selection\run_boruta_ranking.py ^
    data\training\funabashi_2020-2025_with_time.csv

python scripts\phase7_feature_selection\run_boruta_regression.py ^
    data\training\funabashi_2020-2025_with_time.csv
```

**Phase 8実行**:
```bash
python scripts\phase8_auto_tuning\run_optuna_tuning.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --selected-features data\features\selected\funabashi_selected_features.csv

python scripts\phase8_auto_tuning\run_optuna_tuning_ranking.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --selected-features data\features\selected\funabashi_ranking_selected_features.csv

python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --selected-features data\features\selected\funabashi_regression_selected_features.csv
```

**Phase 5実行**:
```bash
python scripts\phase5_ensemble\ensemble_optimized.py ^
    funabashi ^
    test_data\funabashi_test.csv
```

---

## トラブルシューティング

### ❌ よくあるエラーと解決方法

#### 1. "FileNotFoundError: 学習データが見つかりません"

**原因**: 学習データファイルが存在しない

**解決方法**:
```bash
# ファイルの存在確認
dir data\training\*_with_time.csv

# Phase 0-2を実行してデータを生成
python scripts\phase0_data_collection\download_jrdb_data.py
python scripts\phase1_feature_engineering\create_features.py
python scripts\phase2_target_creation\add_targets.py
```

---

#### 2. "ImportError: No module named 'lightgbm'"

**原因**: 必要なライブラリがインストールされていない

**解決方法**:
```bash
pip install lightgbm pandas numpy scikit-learn optuna matplotlib seaborn
```

---

#### 3. "MemoryError: メモリ不足"

**原因**: 大量のデータ処理でメモリ不足

**解決方法**:
- 試行回数を減らす: `--n-trials 50`
- CV foldを減らす: `--cv-folds 2`
- 会場を分割して実行

---

#### 4. "KeyError: 'race_id'"

**原因**: 必須カラムが学習データに存在しない

**解決方法**:
- Phase 2で`race_id`が正しく生成されているか確認
- データファイルを再生成

---

#### 5. Phase 8が途中で停止する

**原因**: タイムアウトまたはメモリ不足

**解決方法**:
```bash
# タイムアウトを延長
--timeout 14400  # 4時間

# 試行回数を減らす
--n-trials 50
```

---

#### 6. "ValueError: グループサイズが一致しません"

**原因**: Rankingモデルで`race_id`のグループ化に失敗

**解決方法**:
- 学習データに`race_id`カラムが存在するか確認
- `race_id`が欠損していないか確認

---

### 🔧 デバッグモード

詳細なログを確認したい場合：

```bash
# Pythonスクリプトを直接実行
python -u scripts\phase8_auto_tuning\run_optuna_tuning.py ^
    data\training\funabashi_2020-2025_with_time.csv ^
    --n-trials 10  # デバッグ用に少ない試行回数

# 出力をファイルに保存
python scripts\phase8_auto_tuning\run_optuna_tuning.py ^
    data\training\funabashi_2020-2025_with_time.csv > log.txt 2>&1
```

---

## 期待される性能改善

### 📊 ベンチマーク比較

| 指標 | Phase 5（従来） | Phase 7/8/5完全版 | 改善率 |
|------|----------------|------------------|--------|
| **AUC** | 0.68-0.72 | 0.78-0.82 | **+10-15%** |
| **複勝的中率** | 32-38% | 42-48% | **+10%以上** |
| **上位3頭的中率** | 25-30% | 35-42% | **+12%以上** |
| **回収率** | 75-85% | 95-110% | **+20-30%** |
| **NDCG@5** | 0.60-0.65 | 0.72-0.78 | **+15-20%** |
| **タイムRMSE** | 150-200 | 95-125 | **-35-45%** |

### 🎯 会場別期待性能（AUC）

| 会場 | Phase 5 | Phase 7/8/5 | 改善 |
|------|---------|------------|------|
| 船橋 | 0.70 | 0.80 | +0.10 |
| 川崎 | 0.72 | 0.81 | +0.09 |
| 大井 | 0.69 | 0.78 | +0.09 |
| 浦和 | 0.68 | 0.77 | +0.09 |
| 盛岡 | 0.65 | 0.75 | +0.10 |
| 水沢 | 0.66 | 0.76 | +0.10 |
| 笠松 | 0.67 | 0.77 | +0.10 |
| 金沢 | 0.64 | 0.74 | +0.10 |
| 園田 | 0.68 | 0.78 | +0.10 |
| 姫路 | 0.66 | 0.76 | +0.10 |
| 高知 | 0.67 | 0.77 | +0.10 |
| 佐賀 | 0.65 | 0.75 | +0.10 |
| 荒尾 | 0.64 | 0.74 | +0.10 |
| **平均** | **0.68** | **0.77** | **+0.09** |

---

## 次のステップ

### ✅ Phase 7/8/5完了後

1. **性能検証**: バックテストで実際の性能を確認
2. **パラメータチューニング**: アンサンブル重み（30/50/20）を調整
3. **運用開始**: リアルタイム予測システムへの統合

### 🚀 さらなる改善

- Phase 9: オンライン学習（データ更新時の自動再学習）
- Phase 10: ディープラーニングモデルの統合
- Phase 11: レース展開予測の追加

---

## まとめ

本ガイドに従って**Phase 7 → 8 → 5**を実行することで、従来のPhase 5（AUC ~0.70）から**Phase 5 Optimized（AUC 0.80+）**への大幅な性能改善が期待できます。

**重要ポイント**:
- ✅ 3つのモデルタイプを個別に最適化
- ✅ Boruta特徴選択で不要な特徴を排除
- ✅ Optunaでハイパーパラメータを自動最適化
- ✅ アンサンブル統合で各モデルの強みを活用

**究極の競馬AIシステム**構築を完了させましょう！🏇✨
