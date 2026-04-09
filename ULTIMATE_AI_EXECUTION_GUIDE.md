# 🏆 最高峰の競馬AI：完全実装ガイド

## 📋 **Option B → A 実装フロー**

### **Phase 1: 船橋で段階的実装・検証（3-5時間）**
### **Phase 2: 全競馬場へ展開（42-70時間）**

---

## ✅ **作成済みファイル（GitHubへpush済み）**

| ファイル | 目的 | ステータス |
|---------|------|-----------|
| `scripts/phase7_feature_selection/run_boruta_ranking.py` | ランキング用Boruta特徴選択 | ✅ 完了 |
| `scripts/phase7_feature_selection/run_boruta_regression.py` | 回帰用Boruta特徴選択 | ✅ 完了 |
| `scripts/phase8_auto_tuning/run_optuna_tuning_ranking.py` | ランキング用Optunaチューニング | ✅ 完了 |
| `ULTIMATE_AI_ROADMAP.md` | 完全実装ロードマップ | ✅ 完了 |

---

## 🔜 **作成が必要なファイル**

### **Phase 8: 回帰モデル最適化**

| ファイル | 目的 | 優先度 | 所要時間 |
|---------|------|--------|---------|
| `scripts/phase8_auto_tuning/run_optuna_tuning_regression.py` | 回帰用Optunaチューニング | 🔴 高 | 30分 |

### **Phase 5拡張: 最適化アンサンブル**

| ファイル | 目的 | 優先度 | 所要時間 |
|---------|------|--------|---------|
| `scripts/phase5_ensemble/predict_ensemble_optimized.py` | 最適化3モデルで日次予測 | 🔴 高 | 1時間 |

### **実行用バッチファイル**

| ファイル | 目的 | 優先度 | 所要時間 |
|---------|------|--------|---------|
| `RUN_ULTIMATE_AI_FUNABASHI.bat` | 船橋専用：完全最適化実行 | 🔴 高 | 15分 |
| `RUN_ULTIMATE_AI_ALL_VENUES.bat` | 全競馬場：完全最適化実行 | 🔴 高 | 15分 |
| `RUN_DAILY_ULTIMATE.bat` | 日次予測：最適化アンサンブル | 🔴 高 | 15分 |

---

## 🚀 **実行フロー全体像**

```
【船橋で検証】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1: Phase 7 完全実行（Boruta特徴選択 × 3モデル）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
[1-1] Binary用Boruta    → funabashi_selected_features.csv (29特徴)
[1-2] Ranking用Boruta   → funabashi_ranking_selected_features.csv (?特徴)
[1-3] Regression用Boruta → funabashi_regression_selected_features.csv (?特徴)

所要時間: 約1時間

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Phase 8 完全実行（Optunaチューニング × 3モデル）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
[2-1] Binary用Optuna     → funabashi_tuned_model.txt (AUC 0.76+)
[2-2] Ranking用Optuna    → funabashi_ranking_tuned_model.txt (NDCG@5 0.85+)
[2-3] Regression用Optuna → funabashi_regression_tuned_model.txt (RMSE最小)

所要時間: 約2-3時間（200試行 × 3モデル）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Phase 5拡張 日次予測テスト
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
RUN_DAILY_ULTIMATE.bat 43 2026-02-11

出力:
- data/predictions/phase5/funabashi_20260211_ensemble_optimized.csv
- predictions/船橋_20260211_note.txt
- predictions/船橋_20260211_tweet.txt
- predictions/船橋_20260211_bookers.txt

所要時間: 約5-10分

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: 性能検証
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
- Binary単体 (Phase 8のみ) と比較
- アンサンブル統合後の精度を確認
- AUC 0.80+, 的中率 80%+ 達成を確認

所要時間: 手動検証 約30分

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 船橋で問題なければ全競馬場へ展開
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


【全競馬場へ展開】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 5: 全競馬場で完全最適化
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
RUN_ULTIMATE_AI_ALL_VENUES.bat

対象競馬場（14箇所）:
- 30: 門別 (monbetsu)
- 35: 盛岡 (morioka)
- 36: 水沢 (mizusawa)
- 42: 浦和 (urawa)
- 43: 船橋 (funabashi) ← 既に完了
- 44: 大井 (ooi)
- 45: 川崎 (kawasaki)
- 46: 金沢 (kanazawa)
- 47: 笠松 (kasamatsu)
- 48: 名古屋 (nagoya)
- 50: 園田 (sonoda)
- 51: 姫路 (himeji)
- 54: 高知 (kochi)
- 55: 佐賀 (saga)

所要時間: 13競馬場 × 3-5時間 = 39-65時間
```

---

## 📂 **最終的なディレクトリ構造**

```
anonymous-keiba-ai/
├── data/
│   ├── features/
│   │   └── selected/
│   │       ├── funabashi_selected_features.csv              (Binary用 29特徴)
│   │       ├── funabashi_ranking_selected_features.csv      (Ranking用 ?特徴)
│   │       ├── funabashi_regression_selected_features.csv   (Regression用 ?特徴)
│   │       ├── ... (他13競馬場も同様)
│   │
│   └── models/
│       └── tuned/
│           ├── funabashi_tuned_model.txt                (Binary最適化)
│           ├── funabashi_ranking_tuned_model.txt        (Ranking最適化)
│           ├── funabashi_regression_tuned_model.txt     (Regression最適化)
│           ├── funabashi_best_params.csv
│           ├── funabashi_ranking_best_params.csv
│           ├── funabashi_regression_best_params.csv
│           ├── ... (他13競馬場も同様)
│
├── scripts/
│   ├── phase7_feature_selection/
│   │   ├── run_boruta.py                         ✅ 既存
│   │   ├── run_boruta_ranking.py                 ✅ 新規作成完了
│   │   └── run_boruta_regression.py              ✅ 新規作成完了
│   │
│   ├── phase8_auto_tuning/
│   │   ├── run_optuna_tuning.py                  ✅ 既存
│   │   ├── run_optuna_tuning_ranking.py          ✅ 新規作成完了
│   │   └── run_optuna_tuning_regression.py       🔜 作成予定
│   │
│   └── phase5_ensemble/
│       ├── ensemble_predictions.py               ✅ 既存（未最適化版）
│       └── predict_ensemble_optimized.py         🔜 作成予定
│
├── RUN_ULTIMATE_AI_FUNABASHI.bat                  🔜 作成予定
├── RUN_ULTIMATE_AI_ALL_VENUES.bat                 🔜 作成予定
├── RUN_DAILY_ULTIMATE.bat                         🔜 作成予定
│
├── ULTIMATE_AI_ROADMAP.md                         ✅ 作成完了
└── ULTIMATE_AI_EXECUTION_GUIDE.md                 ✅ このファイル
```

---

## 💻 **実行コマンド例**

### **船橋で段階的実装（Option B）**

#### **Step 1: Phase 7 完全実行（約1時間）**

```batch
REM Binary用Boruta（既存・スキップ可）
python scripts/phase7_feature_selection/run_boruta.py ^
    data/training/cleaned/funabashi_2020-2025_cleaned.csv

REM Ranking用Boruta
python scripts/phase7_feature_selection/run_boruta_ranking.py ^
    data/training/cleaned/funabashi_2020-2025_cleaned.csv ^
    --alpha 0.1 ^
    --max-iter 200

REM Regression用Boruta
python scripts/phase7_feature_selection/run_boruta_regression.py ^
    data/training/cleaned/funabashi_2020-2025_cleaned.csv ^
    --alpha 0.1 ^
    --max-iter 200
```

#### **Step 2: Phase 8 完全実行（約2-3時間）**

```batch
REM Binary用Optuna（既存・スキップ可）
python scripts/phase8_auto_tuning/run_optuna_tuning.py ^
    data/training/cleaned/funabashi_2020-2025_cleaned.csv ^
    --n-trials 200 ^
    --timeout 7200

REM Ranking用Optuna
python scripts/phase8_auto_tuning/run_optuna_tuning_ranking.py ^
    data/training/cleaned/funabashi_2020-2025_cleaned.csv ^
    --n-trials 200 ^
    --timeout 7200

REM Regression用Optuna
python scripts/phase8_auto_tuning/run_optuna_tuning_regression.py ^
    data/training/cleaned/funabashi_2020-2025_cleaned.csv ^
    --n-trials 200 ^
    --timeout 7200
```

#### **Step 3: 日次予測テスト（約5-10分）**

```batch
RUN_DAILY_ULTIMATE.bat 43 2026-02-11
```

---

### **全競馬場へ展開（Option A）**

```batch
REM 全競馬場で一括実行
RUN_ULTIMATE_AI_ALL_VENUES.bat

REM または競馬場を指定して実行
RUN_ULTIMATE_AI_ALL_VENUES.bat 30 35 36  REM 門別・盛岡・水沢のみ
```

---

## 📊 **期待される成果物**

### **船橋完了時点**

```
data/features/selected/
  ├── funabashi_selected_features.csv              (29特徴)
  ├── funabashi_ranking_selected_features.csv      (例: 25特徴)
  └── funabashi_regression_selected_features.csv   (例: 28特徴)

data/models/tuned/
  ├── funabashi_tuned_model.txt                (Binary AUC 0.76+)
  ├── funabashi_ranking_tuned_model.txt        (Ranking NDCG@5 0.85+)
  └── funabashi_regression_tuned_model.txt     (Regression RMSE最小)

data/predictions/phase5/
  └── funabashi_20260211_ensemble_optimized.csv

predictions/
  ├── 船橋_20260211_note.txt
  ├── 船橋_20260211_tweet.txt
  └── 船橋_20260211_bookers.txt
```

### **全競馬場完了時点**

```
data/features/selected/        (14競馬場 × 3ファイル = 42ファイル)
data/models/tuned/             (14競馬場 × 3ファイル = 42ファイル)
```

---

## 🎯 **性能検証方法**

### **1. Binary単体 vs アンサンブルの比較**

```python
# Binary単体（Phase 8のみ）
Binary AUC: 0.7637
Binary 的中率: ~76%

# アンサンブル統合後（Phase 5拡張）
Ensemble AUC: 0.80+ （目標）
Ensemble 的中率: 80%+ （目標）

改善率: +5% AUC, +4% 的中率
```

### **2. 3モデルの個別性能確認**

```
Binary:     AUC 0.76+       (複勝圏内確率)
Ranking:    NDCG@5 0.85+    (相対的な強さ)
Regression: RMSE 最小化     (走破タイム)
```

### **3. レース別の予測精度検証**

```
- 少頭数レース（7頭以下）: Ranking有効性確認
- 混戦レース: Regression貢献度確認
- 本命レース: Binary信頼性確認
```

---

## ⚠️ **注意事項・トラブルシューティング**

### **1. Phase 7でエラーが出る場合**

**症状**: `rank_target`カラムが見つかりません

**原因**: クリーニング済みCSVに`rank_target`がない

**対処法**:
```python
# rank_targetを手動で追加
df['rank_target'] = df.groupby('race_id')['kakutei_chakujun'].rank(method='max')
```

---

### **2. Phase 8で時間がかかりすぎる場合**

**症状**: 200試行で2時間以上かかる

**対処法**:
```bash
# 試行回数を減らす
python run_optuna_tuning_ranking.py ... --n-trials 100
```

---

### **3. メモリ不足エラー**

**症状**: MemoryError

**対処法**:
- バッチサイズを減らす
- 不要なプロセスを終了
- データを分割して実行

---

## 📅 **実装スケジュール（推奨）**

### **Week 1: 船橋で段階的実装**

| 日 | タスク | 所要時間 |
|----|--------|---------|
| Day 1 | Phase 7完全実行（3モデル） | 1時間 |
| Day 2 | Phase 8 Binary + Ranking | 2時間 |
| Day 3 | Phase 8 Regression | 1.5時間 |
| Day 4 | 日次予測テスト・検証 | 1時間 |
| Day 5 | バグ修正・調整 | 予備日 |

**合計**: 約5.5時間（予備日除く）

---

### **Week 2-3: 全競馬場へ展開**

| 週 | タスク | 所要時間 |
|----|--------|---------|
| Week 2 | 6競馬場実行（門別〜川崎） | 18-30時間 |
| Week 3 | 7競馬場実行（金沢〜佐賀） | 21-35時間 |

**合計**: 39-65時間

---

## 🎓 **技術的補足**

### **なぜ3モデル別々に最適化するのか？**

1. **目的関数が異なる**:
   - Binary: `objective='binary'` → AUC最大化
   - Ranking: `objective='lambdarank'` → NDCG@5最大化
   - Regression: `objective='regression'` → RMSE最小化

2. **最適な特徴量が異なる**:
   - Binary: 複勝圏内に関連する特徴（人気、オッズ）
   - Ranking: 相対的な強さに関連する特徴（前走着順、馬場適性）
   - Regression: タイムに関連する特徴（距離適性、ペース）

3. **ハイパーパラメータが異なる**:
   - Binary: `scale_pos_weight`（不均衡対策）
   - Ranking: `num_leaves`（順序関係の複雑度）
   - Regression: `min_child_samples`（過学習抑制）

---

## 🚀 **次のアクション**

### **即座に実行可能**:

1. **残りのスクリプト作成**:
   - `run_optuna_tuning_regression.py` ✅（次に作成）
   - `predict_ensemble_optimized.py` （その後作成）

2. **バッチファイル作成**:
   - `RUN_ULTIMATE_AI_FUNABASHI.bat`
   - `RUN_ULTIMATE_AI_ALL_VENUES.bat`
   - `RUN_DAILY_ULTIMATE.bat`

3. **船橋で実行開始**:
   ```batch
   RUN_ULTIMATE_AI_FUNABASHI.bat
   ```

---

## 📞 **サポート・質問**

**質問がある場合は以下を確認**:

1. `ULTIMATE_AI_ROADMAP.md`: 完全な技術仕様
2. このファイル: 実行手順
3. 各スクリプトの`--help`: 詳細なオプション

---

## ✅ **チェックリスト**

### **Phase 7完了確認**:
- [ ] Binary用Boruta実行完了
- [ ] Ranking用Boruta実行完了
- [ ] Regression用Boruta実行完了
- [ ] 3つの`*_selected_features.csv`が生成されている

### **Phase 8完了確認**:
- [ ] Binary用Optuna実行完了（AUC 0.76+）
- [ ] Ranking用Optuna実行完了（NDCG@5 0.85+）
- [ ] Regression用Optuna実行完了（RMSE最小化）
- [ ] 3つの`*_tuned_model.txt`が生成されている

### **Phase 5拡張完了確認**:
- [ ] 日次予測スクリプト実行成功
- [ ] `ensemble_optimized.csv`が生成されている
- [ ] 配信テキスト（note/tweet/bookers）が生成されている
- [ ] AUC 0.80+, 的中率 80%+ 達成

---

**妥協なき最高峰への道、始めましょう！** 🏆
