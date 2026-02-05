# Phase 4 完全実行ガイド（クイックスタート）

**最終更新**: 2026-02-04  
**対象**: Windows環境 (`E:\anonymous-keiba-ai`)

---

## 🎯 Phase 4 の目的

**最強の地方競馬予想システムの構築**

- **3つの視点からの多角的予測**
  - 二値分類（Phase 3完了）: 3着以内の確率
  - ランキング学習（Phase 4）: 相対的な強さ（順位）
  - 回帰分析（Phase 4）: 走破タイム予測（能力値）

- **アンサンブル統合**: 3モデルの予測を組み合わせて最終判断

---

## ⚡ クイックスタート（推奨）

### Step 0: 準備
```bash
# 最新版を取得
cd E:\anonymous-keiba-ai
git pull origin phase4_specialized_models
```

### Step 1: 一括実行
```bash
# 全競馬場の学習を一括実行（推奨）
python run_phase4_training.py
```

このスクリプトは以下を自動実行します：
1. race_id カラムの追加（10競馬場）
2. target を走破タイムに変換（10競馬場）
3. ランキングモデル学習（10競馬場）
4. 回帰モデル学習（10競馬場）

### Step 2: 結果確認
```bash
# モデルファイルの確認
dir *_ranking_model.txt
dir *_regression_model.txt

# 評価指標の確認
type ooi_2023-2024_v3_ranking_score.txt
type ooi_2023-2024_v3_regression_score.txt
```

---

## 🔧 手動実行（個別実行）

### 1. データ準備

#### 大井（コード: 44）を例に

```bash
cd E:\anonymous-keiba-ai

# Step 1: race_id を追加
python add_race_id_to_csv.py ooi_2023-2024_v3.csv
# 出力: ooi_2023-2024_v3_with_race_id.csv

# Step 2: target を走破タイムに変換
python convert_target_to_time.py ooi_2023-2024_v3.csv
# 出力: ooi_2023-2024_v3_time.csv
```

### 2. ランキングモデル学習

```bash
# 大井
python train_ranking_model.py ooi_2023-2024_v3_with_race_id.csv
# 出力:
#   - ooi_2023-2024_v3_with_race_id_ranking_model.txt
#   - ooi_2023-2024_v3_with_race_id_ranking_model.png
#   - ooi_2023-2024_v3_with_race_id_ranking_score.txt
```

### 3. 回帰モデル学習

```bash
# 大井
python train_regression_model.py ooi_2023-2024_v3_time.csv
# 出力:
#   - ooi_2023-2024_v3_time_regression_model.txt
#   - ooi_2023-2024_v3_time_regression_model.png
#   - ooi_2023-2024_v3_time_regression_score.txt
```

### 4. 他の競馬場も同様に実行

```bash
# 船橋（コード: 43）
python add_race_id_to_csv.py funabashi_2020-2025_v3.csv
python convert_target_to_time.py funabashi_2020-2025_v3.csv
python train_ranking_model.py funabashi_2020-2025_v3_with_race_id.csv
python train_regression_model.py funabashi_2020-2025_v3_time.csv

# 川崎（コード: 45）
python add_race_id_to_csv.py kawasaki_2020-2025_v3.csv
python convert_target_to_time.py kawasaki_2020-2025_v3.csv
python train_ranking_model.py kawasaki_2020-2025_v3_with_race_id.csv
python train_regression_model.py kawasaki_2020-2025_v3_time.csv

# ... 他7競馬場も同様
```

---

## 📊 期待される成果物

### モデルファイル（各競馬場 × 3種類 = 30モデル）

#### 大井の例
```
ooi_2023-2024_v3_model.txt                       # 二値分類（Phase 3で作成済み）
ooi_2023-2024_v3_with_race_id_ranking_model.txt  # ランキング（Phase 4で作成）
ooi_2023-2024_v3_time_regression_model.txt       # 回帰（Phase 4で作成）
```

### 評価ファイル（各競馬場 × 2種類 = 20ファイル）

```
ooi_2023-2024_v3_with_race_id_ranking_score.txt  # ランキング評価
ooi_2023-2024_v3_time_regression_score.txt       # 回帰評価
```

### 特徴量重要度グラフ（各競馬場 × 2種類 = 20ファイル）

```
ooi_2023-2024_v3_with_race_id_ranking_model.png  # ランキング
ooi_2023-2024_v3_time_regression_model.png       # 回帰
```

---

## 🚀 次のステップ: アンサンブル予測

### アンサンブル予測の実行（例: 大井 2026年1月）

```bash
# 予測対象データの準備
# （simulate_2026_venue_adaptive.py で抽出したデータを使用）

# アンサンブル予測の実行
python ensemble_model.py prediction_data_ooi_2026_01.csv \
    ooi_2023-2024_v3_model.txt \
    ooi_2023-2024_v3_with_race_id_ranking_model.txt \
    ooi_2023-2024_v3_time_regression_model.txt \
    --output ensemble_ooi_2026_01.csv

# 結果確認
type ensemble_ooi_2026_01.csv
```

### アンサンブル予測の出力

```csv
ensemble_score,binary_proba,ranking_score,regression_time,recommendation
0.82,0.75,0.88,85.2,◎ 本命
0.68,0.65,0.70,87.5,○ 対抗
0.55,0.50,0.58,89.1,▲ 単穴
0.42,0.45,0.40,91.3,△ 連下
0.25,0.20,0.28,93.5,× 評価低
0.15,0.10,0.15,95.2,消去
```

---

## 📈 期待される精度

### 推奨度別的中率（目標値）

- **◎本命**: 50-60%以上
- **○対抗**: 35-45%以上
- **▲単穴**: 25-35%以上
- **△連下**: 15-25%以上
- **×評価低**: 5-15%以上
- **消去**: <5%

### 全体的中率

- **Phase 4.5（二値分類のみ）**: 約29%
- **Phase 4（アンサンブル）**: 29%以上を期待

---

## ⚠️ トラブルシューティング

### Q1: race_id カラムが既に存在する
**A**: 既存の race_id を削除してから再実行
```python
df = df.drop('race_id', axis=1)
```

### Q2: time カラムが存在しない
**A**: convert_target_to_time.py は prev1_time を代替使用します
```
警告: 'time' カラムが見つかりません
→ 'prev1_time' カラムを代替使用（応急処置）
```

### Q3: ランキング学習で "group情報が不正" エラー
**A**: race_id が正しく作成されているか確認
```python
print(df['race_id'].head())
print(df['race_id'].nunique())
```

### Q4: 回帰モデルの RMSE が大きい
**A**: target のスケールを確認
```python
print(df['target'].describe())
# 平均値が妥当な範囲（60-120秒）か確認
```

---

## 📚 詳細ドキュメント

- **詳細実行計画書**: [PHASE4_FULL_EXECUTION_PLAN.md](PHASE4_FULL_EXECUTION_PLAN.md)
- **実装ガイド**: [docs/phase4_implementation_guide.md](docs/phase4_implementation_guide.md)
- **完了レポート**: [docs/phase4_completion_report.md](docs/phase4_completion_report.md)

---

## ✅ 成功の基準

### 必須条件
- [x] 全10競馬場でランキングモデル学習が成功
- [x] 全10競馬場で回帰モデル学習が成功
- [x] 各モデルの評価指標が妥当な範囲内
- [x] アンサンブル予測が実行可能

### 推奨条件
- [ ] 推奨度別的中率が目標値を達成
- [ ] 全体的中率が Phase 4.5 を上回る
- [ ] 実戦投入可能なレベル

---

**作成者**: Anonymous Keiba AI Development Team  
**最終更新**: 2026-02-04  
**ステータス**: 実行準備完了 ✅
