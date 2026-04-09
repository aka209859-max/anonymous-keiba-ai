# Phase 7-10 統合実行ガイド

**最高峰への進化：完全実装版**

---

## 📋 概要

Phase 7-10を順番に実行して、地方競馬AI予想システムを最高峰に進化させます。

### **実装内容**
- **Phase 7**: Boruta特徴量選択（ノイズ除去）
- **Phase 8**: Optuna自動チューニング（精度向上）
- **Phase 9**: 期待値ベース購入戦略（回収率改善）
- **Phase 10**: バックテスト・シミュレーション（安全確認）

### **期待される効果**
| 項目 | 現在 | Phase 7-10後 | 改善率 |
|------|------|--------------|--------|
| 特徴量数 | 50個 | 20-30個 | -40% |
| 予測精度（AUC） | 0.77 | 0.85以上 | +10% |
| 回収率 | 60% | 120%+ | +100% |
| 馬単的中率 | 低い | 大幅改善 | +30% |
| 3連複的中率 | 低い | 大幅改善 | +25% |

---

## 🚀 実行手順

### **前提条件**
1. PC-KEIBAデータベースが起動している
2. PostgreSQL接続が正常
3. 名古屋競馬の学習データ（2022-2025年）が存在

---

### **Phase 7: Boruta特徴量選択**

#### **Step 1: データクリーニング**

```bash
cd /home/user/webapp/anonymous-keiba-ai

python scripts/phase7_feature_selection/clean_training_data.py \
  --venue 名古屋 \
  --start-date 2022-01-01 \
  --end-date 2025-12-31
```

**出力**:
- `data/training/cleaned/名古屋_20220101_20251231_cleaned.csv`
- `data/training/cleaned/名古屋_20220101_20251231_stats.json`

**所要時間**: 約5分

---

#### **Step 2: Boruta特徴量選択**

```bash
python scripts/phase7_feature_selection/run_boruta_selection.py \
  data/training/cleaned/名古屋_20220101_20251231_cleaned.csv \
  --alpha 0.1 \
  --max-iter 200 \
  --force-keep "kishu_code,prev1_rank,prev2_rank"
```

**出力**:
- `data/features/selected/名古屋_selected_features.csv`（選択特徴量リスト）
- `data/features/selected/名古屋_importance.png`（重要度グラフ）
- `data/features/selected/名古屋_boruta_report.json`（詳細レポート）

**所要時間**: 約30分

**期待結果**:
- 50個 → 20-30個に削減
- ノイズ除去で精度5-10%向上

---

### **Phase 8: Optuna自動チューニング**

#### **Step 3: ハイパーパラメータ最適化**

```bash
python scripts/phase8_auto_tuning/run_optuna_tuning.py \
  data/training/cleaned/名古屋_20220101_20251231_cleaned.csv \
  --n-trials 100 \
  --timeout 7200 \
  --cv-folds 5
```

**出力**:
- `data/models/tuned/名古屋_best_params.csv`（最適パラメータ）
- `data/models/tuned/名古屋_tuned_model.txt`（学習済みモデル）
- `data/models/tuned/名古屋_importance.png`（特徴量重要度）
- `data/models/tuned/名古屋_tuning_report.json`（詳細レポート）

**所要時間**: 約2時間（timeout設定）

**期待結果**:
- AUC 0.77 → 0.85以上に向上
- 馬単・3連複の精度が大幅改善

---

### **Phase 9: 期待値ベース購入戦略**

#### **Step 4: 購入戦略テスト（Pythonスクリプト内で使用）**

```python
from scripts.phase9_betting_strategy.betting_strategy_engine import BettingStrategyEngine
import pandas as pd

# サンプルデータ
predictions = pd.DataFrame({
    'umaban': [1, 2, 3, 4, 5, 6, 7, 8],
    'win_prob': [0.25, 0.15, 0.12, 0.10, 0.08, 0.07, 0.05, 0.03],
    'top3_prob': [0.60, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15]
})

odds = pd.DataFrame({
    'umaban': [1, 2, 3, 4, 5, 6, 7, 8],
    'tansho_odds': [4.5, 7.2, 9.8, 12.5, 15.0, 18.0, 25.0, 50.0],
    'fukusho_odds': [1.8, 2.5, 3.2, 4.0, 4.5, 5.0, 6.0, 8.0]
})

# エンジン初期化
engine = BettingStrategyEngine(
    bankroll=100000,
    kelly_fraction=0.25,
    max_bet_pct=0.05,
    min_ev=0.05
)

# 購入推奨生成
recommendations = engine.generate_recommendations(
    predictions,
    odds,
    betting_types=['単勝', '複勝', '馬単', '3連複']
)

print(recommendations)
```

**期待結果**:
- 期待値がプラスの馬券だけを購入
- Kelly基準で賭け金を最適化
- 回収率60% → 120%+に改善

---

### **Phase 10: バックテスト・シミュレーション**

#### **Step 5: 過去データで検証**

```bash
python scripts/phase10_backtest/backtest_simulator.py \
  --venue 名古屋 \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --initial-bankroll 100000 \
  --kelly-fraction 0.25
```

**出力**:
- `data/backtest/名古屋_20240101_20241231_report.json`（詳細レポート）
- `data/backtest/名古屋_20240101_20241231_summary.csv`（サマリー）
- `data/backtest/名古屋_20240101_20241231_performance.png`（パフォーマンスグラフ）

**所要時間**: 約10分

**期待結果**:
- 回収率: 120%以上
- 的中率: 28%以上
- 最大連敗: 15回以下
- 最終資金: 120,000円以上（初期10万円）

---

## 📊 結果の確認

### **Phase 7の確認**

```bash
cat data/features/selected/名古屋_boruta_report.json
```

確認項目:
- `selected_features`: 選択された特徴量数
- `reduction_rate`: 削減率

### **Phase 8の確認**

```bash
cat data/models/tuned/名古屋_tuning_report.json
```

確認項目:
- `best_score`: 最高AUC
- `best_params`: 最適パラメータ

### **Phase 10の確認**

```bash
cat data/backtest/名古屋_20240101_20241231_report.json
```

確認項目:
- `recovery_rate`: 回収率（目標: 1.2以上）
- `hit_rate`: 的中率（目標: 0.28以上）
- `total_profit`: 総利益（目標: +20,000円以上）

---

## 🔧 トラブルシューティング

### **Phase 7でエラー「Number of used features: 0」**

**原因**: alpha値が厳しすぎる

**対処法**:
```bash
python scripts/phase7_feature_selection/run_boruta_selection.py \
  data/training/cleaned/名古屋_20220101_20251231_cleaned.csv \
  --alpha 0.15 \
  --max-iter 300
```

---

### **Phase 8でメモリ不足**

**原因**: データサイズが大きすぎる

**対処法**:
- 試行回数を減らす: `--n-trials 50`
- タイムアウトを短縮: `--timeout 3600`

---

### **Phase 10で「データが見つかりません」**

**原因**: 過去オッズデータが未整備

**対処法**:
1. PC-KEIBAデータベースでオッズテーブルを確認
2. `backtest_simulator.py`の`load_historical_data()`を実データに接続

---

## 🎯 次のステップ

### **本番運用への統合**

Phase 7-10で作成したモデルを、既存のPhase 3-6に統合します：

#### **1. Phase 4-1（ランキング予測）の更新**

```python
# scripts/phase4_ranking/predict_phase4_ranking_inference.py

# 最適パラメータ読み込み
best_params = pd.read_csv('data/models/tuned/名古屋_best_params.csv').iloc[0].to_dict()

# モデル読み込み
model = lgb.Booster(model_file='data/models/tuned/名古屋_tuned_model.txt')

# 予測実行
predictions = model.predict(X)
```

#### **2. Phase 6（配信）に期待値戦略を追加**

```python
# scripts/phase6_betting/generate_distribution.py

from scripts.phase9_betting_strategy.betting_strategy_engine import BettingStrategyEngine

# 購入推奨生成
engine = BettingStrategyEngine(bankroll=100000, kelly_fraction=0.25)
recommendations = engine.generate_recommendations(predictions, odds)

# Note配信用テキスト生成
note_text = format_recommendations(recommendations)
```

---

## 📈 成果物の一覧

```
anonymous-keiba-ai/
├── data/
│   ├── training/
│   │   └── cleaned/
│   │       ├── 名古屋_20220101_20251231_cleaned.csv
│   │       └── 名古屋_20220101_20251231_stats.json
│   ├── features/
│   │   └── selected/
│   │       ├── 名古屋_selected_features.csv
│   │       ├── 名古屋_importance.png
│   │       └── 名古屋_boruta_report.json
│   ├── models/
│   │   └── tuned/
│   │       ├── 名古屋_best_params.csv
│   │       ├── 名古屋_tuned_model.txt
│   │       ├── 名古屋_importance.png
│   │       └── 名古屋_tuning_report.json
│   └── backtest/
│       ├── 名古屋_20240101_20241231_report.json
│       ├── 名古屋_20240101_20241231_summary.csv
│       └── 名古屋_20240101_20241231_performance.png
├── scripts/
│   ├── phase7_feature_selection/
│   │   ├── clean_training_data.py
│   │   └── run_boruta_selection.py
│   ├── phase8_auto_tuning/
│   │   └── run_optuna_tuning.py
│   ├── phase9_betting_strategy/
│   │   └── betting_strategy_engine.py
│   └── phase10_backtest/
│       └── backtest_simulator.py
└── docs/
    ├── ROADMAP_TO_EXCELLENCE.md
    ├── TECHNICAL_SPEC_EXCELLENCE.md
    └── PHASE7_10_INTEGRATION_GUIDE.md（このファイル）
```

---

## ✅ 完成度チェックリスト

- [ ] Phase 7: Boruta特徴量選択完了
  - [ ] データクリーニング実行
  - [ ] 特徴量選択実行
  - [ ] 重要度グラフ確認
  - [ ] 削減率40%以上達成

- [ ] Phase 8: Optuna自動チューニング完了
  - [ ] ハイパーパラメータ最適化実行
  - [ ] best_params.csv保存確認
  - [ ] AUC 0.85以上達成

- [ ] Phase 9: 期待値ベース購入戦略完了
  - [ ] BettingStrategyEngine動作確認
  - [ ] Kelly基準テスト
  - [ ] Harville公式テスト

- [ ] Phase 10: バックテスト完了
  - [ ] 過去1年分の検証実行
  - [ ] 回収率120%以上達成
  - [ ] パフォーマンスグラフ確認

---

## 🎉 おめでとうございます！

Phase 7-10の実装が完了すると、あなたの地方競馬AIシステムは**最高峰の完成度（100%）**に到達します！

次は実戦で検証し、継続的に改善していきましょう！🚀
