# Phase 7-8 完全実行ガイド（訂正版）

**作成日時**: 2026-02-11  
**対象会場**: 船橋（Funabashi）  
**重要**: Phase 8は3つのモデル最適化が必要です

---

## 🔴 重要な訂正

### ❌ 誤り（以前の説明）
```
Phase 8 = Ranking最適化 + Regression最適化
          （2つのモデル）
```

### ✅ 正しい構成
```
Phase 8 = Binary最適化 + Ranking最適化 + Regression最適化
          （3つのモデル）
```

---

## 📊 Phase 7-8の正しい全体像

```
Phase 7: 特徴量選択
  ├── Binary: 3着以内予測用の特徴量選択
  ├── Ranking: 着順予測用の特徴量選択
  └── Regression: タイム予測用の特徴量選択
       ↓
Phase 8: ハイパーパラメータ最適化
  ├── Binary: Binary用の最適パラメータ探索
  ├── Ranking: Ranking用の最適パラメータ探索
  └── Regression: Regression用の最適パラメータ探索
       ↓
Phase 5: アンサンブル統合
  └── 3つのモデルを統合して最終予測
```

---

## 📋 Phase 7の実行状況

### ✅ 完了済み

| タスク | 状態 | 選択特徴量 | 反復回数 |
|--------|------|-----------|---------|
| **Phase 7 Ranking** | ✅ 完了 | 25個 | 3回 |
| **Phase 7 Regression** | ✅ 完了 | 24個 | 3回 |

### ❓ Phase 7 Binary の状態確認が必要

**確認コマンド**:
```bash
cd E:\anonymous-keiba-ai
dir data\features\selected\funabashi_selected_features.csv
```

---

## 🚀 Phase 7-8 完全実行計画

### **ステップ1: Phase 7 Binary（未実行の場合）**

**実行コマンド**:
```bash
cd E:\anonymous-keiba-ai
python run_phase7_funabashi_binary.py
```

**推定時間**: 10〜20分

**期待出力**:
- `data/features/selected/funabashi_selected_features.csv`
- `data/features/selected/funabashi_boruta_report.json`
- `data/reports/phase7_feature_selection/funabashi_importance.png`

---

### **ステップ2: Phase 8 Binary**

**実行コマンド**:
```bash
cd E:\anonymous-keiba-ai
python run_phase8_funabashi_binary.py
```

**推定時間**: 30〜60分

**期待出力**:
- `data/models/tuned/funabashi_best_params.csv`
- `data/models/tuned/funabashi_tuned_model.txt`
- `data/reports/phase8_tuning/funabashi_tuning_history.png`

---

### **ステップ3: Phase 8 Ranking**

**実行コマンド**:
```bash
cd E:\anonymous-keiba-ai
python run_phase8_funabashi_ranking.py
```

**推定時間**: 30〜60分

**期待出力**:
- `data/models/tuned/funabashi_ranking_best_params.csv`
- `data/models/tuned/funabashi_ranking_tuned_model.txt`
- `data/reports/phase8_tuning/funabashi_ranking_optimization_history.png`

---

### **ステップ4: Phase 8 Regression**

**実行コマンド**:
```bash
cd E:\anonymous-keiba-ai
python run_phase8_funabashi_regression.py
```

**推定時間**: 30〜60分

**期待出力**:
- `data/models/tuned/funabashi_regression_best_params.csv`
- `data/models/tuned/funabashi_regression_tuned_model.txt`
- `data/reports/phase8_tuning/funabashi_regression_optimization_history.png`

---

## ⚡ 並行実行で時間短縮

Phase 8の3つのタスクは**並行実行可能**です！

### 3つのコマンドプロンプトを開いて同時実行

**ウィンドウ1（Binary）**:
```bash
cd E:\anonymous-keiba-ai
python run_phase8_funabashi_binary.py
```

**ウィンドウ2（Ranking）**:
```bash
cd E:\anonymous-keiba-ai
python run_phase8_funabashi_ranking.py
```

**ウィンドウ3（Regression）**:
```bash
cd E:\anonymous-keiba-ai
python run_phase8_funabashi_regression.py
```

→ **合計時間: 30〜60分**（並行実行により）

---

## 📊 Phase 8完了後の成果物

### 最終的に9個のファイルが生成される

#### Binary用（3ファイル）
```
data/models/tuned/
├── funabashi_best_params.csv
└── funabashi_tuned_model.txt

data/reports/phase8_tuning/
└── funabashi_tuning_history.png
```

#### Ranking用（3ファイル）
```
data/models/tuned/
├── funabashi_ranking_best_params.csv
└── funabashi_ranking_tuned_model.txt

data/reports/phase8_tuning/
└── funabashi_ranking_optimization_history.png
```

#### Regression用（3ファイル）
```
data/models/tuned/
├── funabashi_regression_best_params.csv
└── funabashi_regression_tuned_model.txt

data/reports/phase8_tuning/
└── funabashi_regression_optimization_history.png
```

---

## 🎯 Phase 5: アンサンブル統合

Phase 8で3つのモデルが最適化されたら、Phase 5で統合します。

```
Phase 5 = Binary + Ranking + Regression の統合予測
```

**実行コマンド**:
```bash
cd E:\anonymous-keiba-ai
python scripts\phase5_ensemble\ensemble_optimized.py ^
  funabashi ^
  test_data\funabashi_20260211.csv ^
  --output-dir data\predictions\phase5_optimized
```

---

## 📋 完全チェックリスト

### Phase 7: 特徴量選択

- [x] Phase 7 Ranking: ✅ 完了（25特徴量）
- [x] Phase 7 Regression: ✅ 完了（24特徴量）
- [ ] Phase 7 Binary: ❓ 確認必要（実行済みか確認）

### Phase 8: ハイパーパラメータ最適化

- [ ] Phase 8 Binary: 未実行
- [ ] Phase 8 Ranking: 未実行
- [ ] Phase 8 Regression: 未実行

### Phase 5: アンサンブル統合

- [ ] Phase 5 Ensemble: Phase 8完了後に実行

---

## 🔍 Phase 7 Binary の確認方法

### 確認コマンド

```bash
cd E:\anonymous-keiba-ai
dir data\features\selected\funabashi_selected_features.csv
```

### 結果の判定

#### ケース1: ファイルが存在する
```
✅ Phase 7 Binary は完了済み
→ Phase 8 Binary から実行開始
```

#### ケース2: ファイルが存在しない
```
❌ Phase 7 Binary が未実行
→ Phase 7 Binary から実行開始
```

---

## 📥 ファイル取得方法

### Git経由で最新ファイルを取得

```bash
cd E:\anonymous-keiba-ai
git pull origin phase0_complete_fix_2026_02_07
```

### 追加された新しいファイル

1. `run_phase7_funabashi_binary.py` ← NEW!
2. `run_phase8_funabashi_binary.py` ← NEW!
3. `run_phase8_funabashi_ranking.py` ← 既存
4. `run_phase8_funabashi_regression.py` ← 既存

---

## 💡 推奨実行順序

### 順序1: Phase 7 Binary確認 → Phase 8 3つ並行実行

```bash
# Step 1: Phase 7 Binary確認
cd E:\anonymous-keiba-ai
dir data\features\selected\funabashi_selected_features.csv

# Step 2-1: Phase 7 Binary（必要な場合のみ）
python run_phase7_funabashi_binary.py

# Step 2-2: Phase 8を3つ並行実行
# ウィンドウ1
python run_phase8_funabashi_binary.py

# ウィンドウ2
python run_phase8_funabashi_ranking.py

# ウィンドウ3
python run_phase8_funabashi_regression.py
```

---

## 🎯 まとめ

### ✅ 正しいPhase 8の構成

```
Phase 8 = 3つのモデル最適化
  1. Binary最適化
  2. Ranking最適化
  3. Regression最適化
```

### 🚀 次のアクション

1. **Phase 7 Binaryの状態確認**
   ```bash
   dir data\features\selected\funabashi_selected_features.csv
   ```

2. **必要に応じてPhase 7 Binary実行**
   ```bash
   python run_phase7_funabashi_binary.py
   ```

3. **Phase 8を3つ並行実行**（最速）
   ```bash
   python run_phase8_funabashi_binary.py
   python run_phase8_funabashi_ranking.py
   python run_phase8_funabashi_regression.py
   ```

---

**ご指摘ありがとうございました！Phase 8は3つのモデル最適化です！** 🎯

---

**作成者**: Claude AI Development System  
**最終更新**: 2026-02-11  
**ドキュメントバージョン**: 2.0（訂正版）
