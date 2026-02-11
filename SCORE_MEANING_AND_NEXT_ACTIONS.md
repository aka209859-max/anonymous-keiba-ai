# 🎯 スコアの意味と次のアクション（完全版）

**作成日**: 2026-02-11  
**GitHub**: https://github.com/aka209859-max/anonymous-keiba-ai/tree/phase0_complete_fix_2026_02_07

---

## ⚠️ **重要な確認事項（必読）**

### **スコア 0.98 ≠ 複勝率98%**

#### **❌ 誤解**
```
第1R: 7番 タイセイリノ（スコア: 0.98）
→ 複勝率98%？ 買えば絶対当たる？
```

#### **✅ 正解**
```
第1R: 7番 タイセイリノ（スコア: 0.98）
→ レース内で最も高い総合評価（1位予測）
→ 複勝率は別途確認が必要
```

---

## 📊 **スコアの意味（詳細解説）**

### **旧モデル（Phase 3-4-5）のスコア**

```python
# アンサンブルスコア計算
ensemble_score = (
    binary_normalized × 0.3 +      # Binary分類（複勝圏内確率）
    ranking_normalized × 0.5 +     # Ranking予測（相対的強さ）
    regression_normalized × 0.2    # Regression予測（走破タイム）
)

# レース内で0〜1に正規化
final_score = (ensemble_score - min) / (max - min)
```

**具体例（第1R）:**
```
7番 タイセイリノ: 0.98 → レース内で最高評価（1位予測）
3番 アレナメヒコ: 0.85 → レース内で2番目の評価（2位予測）
1番 ハイパーファイン: 0.74 → レース内で3番目の評価（3位予測）
```

**⚠️ 注意点:**
- スコア 0.98 は「レース内での相対的な強さ」
- 複勝率98%ではない
- Binary分類の生スコア（複勝率）は別途確認が必要

---

### **新モデル（Phase 7-8-5）のスコア**

```csv
race_id,umaban,ensemble_score,final_rank,binary_probability,ranking_score,predicted_time
2020_0107_43_03,8,0.557,1,0.272,−0.117,1380.5
                  ↑            ↑
           レース内評価      実際の複勝率27.2%
```

**✅ 改善点:**
- `binary_probability` で複勝率が明確にわかる
- 各モデルの生スコアも確認可能

**具体例（レース 2020_0107_43_03）:**

| 馬番 | ensemble_score | final_rank | binary_probability | ranking_score | predicted_time |
|------|----------------|------------|-------------------|---------------|----------------|
| 8    | 0.557          | 1          | 0.272 (27.2%)     | −0.117 (2位)  | 1380.5s (2位)  |
| 12   | 0.500          | 2          | 0.798 (79.8%)     | −1.974 (5位)  | 1365.2s (1位)  |
| 10   | 0.489          | 3          | 0.018 (1.8%)      | 0.970 (1位)   | 1376.8s (3位)  |

**解釈:**
- **馬8**: 総合評価1位、複勝率27.2%
  - Binary: 27.2%（中程度）
  - Ranking: 2位（強い）
  - Time: 2位（速い）
  - → **バランス型で総合1位**

- **馬12**: 総合評価2位、複勝率79.8%
  - Binary: 79.8%（非常に高い）
  - Ranking: 5位（やや弱い）
  - Time: 1位（最速）
  - → **複勝狙いには最適**

- **馬10**: 総合評価3位、複勝率1.8%
  - Binary: 1.8%（非常に低い）
  - Ranking: 1位（最強）
  - Time: 3位（標準）
  - → **穴馬候補**

---

## 🆚 **旧モデル vs 新モデルの比較**

| 項目 | 旧モデル（Phase 3-4-5） | 新モデル（Phase 7-8-5） |
|------|------------------------|------------------------|
| **特徴量選択** | ❌ なし（全特徴量使用） | ✅ Phase 7 Boruta選択<br>- Binary: 31特徴量<br>- Ranking: 25特徴量<br>- Regression: 24特徴量 |
| **ハイパーパラメータ** | ❌ デフォルト値 | ✅ Phase 8 Optuna最適化<br>（100 trials） |
| **複勝率の確認** | ❌ 困難（別ファイル） | ✅ `binary_probability` で明確 |
| **モデル品質** | 標準 | **最適化済み（高品質）** |

---

## 🎯 **新モデルの期待される改善**

### **定量的な目標**

| 指標 | 旧モデル | 新モデル（目標） | 改善率 |
|------|---------|-----------------|--------|
| **単勝的中率** | 25% | **30%+** | +20% |
| **複勝的中率** | 60% | **70%+** | +17% |
| **NDCG@3** | 0.65 | **0.75+** | +15% |
| **着順誤差** | 2.5 | **2.0以下** | -20% |
| **相関係数** | 0.55 | **0.65+** | +18% |

### **定性的な改善**
1. ✅ **特徴量選択**: ノイズ削減 → 精度向上
2. ✅ **ハイパーパラメータ最適化**: 学習率・木の深さ最適化 → 精度向上
3. ✅ **複勝率の明確化**: `binary_probability` で複勝率が直接わかる
4. ✅ **各モデルの生スコア確認**: Binary, Ranking, Regression の個別評価が可能

---

## 📋 **現在の完了状況**

### ✅ **完了済み**
1. **Phase 0**: 全14会場の学習データ生成（199.7MB）
2. **Phase 8 Binary**: 全14会場の最適化完了
3. **Phase 7 Ranking/Regression**: 船橋のみ完了
4. **Phase 8 Ranking/Regression**: 船橋のみ完了
5. **Phase 5 Ensemble**: 船橋でテスト成功 ✅

### ⏳ **未完了（残り13会場）**
1. **Phase 7 Ranking**: 13会場（推定2〜4時間）
2. **Phase 7 Regression**: 13会場（推定2〜4時間）
3. **Phase 8 Ranking**: 13会場（推定6〜13時間）
4. **Phase 8 Regression**: 13会場（推定6〜13時間）

**合計推定時間**: 16〜34時間

---

## 🚀 **次のアクション（即座に実行）**

### **ローカルPCで実行するコマンド**

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

## 📊 **2025年データでの評価計画**

### **目的**
- 旧モデルと新モデルの精度を定量的に比較
- 対象期間: **2025/01/01 〜 2025/12/31**

### **評価指標**
1. **的中率**: 単勝、複勝、馬連、3連複
2. **予測精度**: NDCG@3、平均着順誤差、スピアマン相関
3. **回収率**: 単勝回収率、複勝回収率

### **評価スクリプト**
```bash
# 旧モデルと新モデルを比較
python scripts\evaluation\evaluate_2025_performance.py ^
  --old-predictions data\predictions\old_model\funabashi_2025_predictions.csv ^
  --new-predictions data\predictions\new_model\funabashi_2025_predictions.csv ^
  --actuals data\actuals\funabashi_2025_actuals.csv ^
  --output-report data\evaluation\funabashi_comparison_report.json
```

---

## 🎯 **まとめ**

### **スコアの意味（最終確認）**
- ❌ **スコア 0.98 ≠ 複勝率98%**
- ✅ **スコア 0.98 = レース内での総合評価が最高（1位予測）**
- ✅ **複勝率は新モデルの `binary_probability` で確認**

### **新モデルの優位性**
1. ✅ Phase 7: Boruta特徴量選択（ノイズ削減）
2. ✅ Phase 8: Optuna最適化（精度向上）
3. ✅ Binary Probability が明確（複勝率がわかる）

### **次のアクション（優先順位順）**
1. **Phase 7 Ranking 実行**（13会場、2〜4時間） → **今すぐ**
2. **Phase 7 Regression 実行**（13会場、2〜4時間）
3. **Phase 8 Ranking/Regression 実行**（13会場、12〜26時間） → **週末**
4. **2025年データで評価**（旧モデル vs 新モデル）

---

## 📁 **関連ファイル**

### **GitHub**
- https://github.com/aka209859-max/anonymous-keiba-ai/tree/phase0_complete_fix_2026_02_07

### **新規作成ファイル**
1. `MODEL_SCORE_ANALYSIS_AND_NEXT_STEPS.md`: 詳細分析とアクションプラン
2. `OLD_VS_NEW_MODEL_COMPARISON.md`: 旧モデルと新モデルの比較
3. `scripts/evaluation/evaluate_2025_performance.py`: 評価スクリプト

### **既存のバッチファイル**
1. `run_phase7_ranking_all.ps1`: Phase 7 Ranking 一括実行
2. `run_phase7_regression_all.ps1`: Phase 7 Regression 一括実行
3. `run_phase8_ranking_all.ps1`: Phase 8 Ranking 一括実行
4. `run_phase8_regression_all.ps1`: Phase 8 Regression 一括実行

---

## 🎯 **即座に実行してください！**

```powershell
cd E:\anonymous-keiba-ai
git pull origin phase0_complete_fix_2026_02_07
.\run_phase7_ranking_all.ps1
```

**推定時間**: 2〜4時間  
**対象**: 残り13会場（門別、盛岡、水沢、浦和、大井、川崎、金沢、笠松、名古屋、園田、姫路、高知、佐賀）

---

**最終更新**: 2026-02-11  
**次のアクション**: Phase 7 Ranking を今すぐ実行！ 🚀
