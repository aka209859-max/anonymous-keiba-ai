# Phase 12: トリプル馬単特化予測モデル

## 📖 目次

1. [概要](#概要)
2. [Phase 11との違い](#phase-11との違い)
3. [システム構成](#システム構成)
4. [モデル設計](#モデル設計)
5. [使用方法](#使用方法)
6. [実装詳細](#実装詳細)

---

## 概要

**Phase 12: トリプル馬単特化予測モデル**は、南関東4場（大井/浦和/船橋/川崎）+ 門別競馬のトリプル馬単に特化した**予測モデル**です。

### 🎯 主な特徴

- ✅ **2着以内特化**: 3着以内ではなく、1着・2着に特化した予測
- ✅ **マルチタスク学習**: 1着確率 + 2着確率 + 馬単ペア確率を同時学習
- ✅ **最終3R重み付け**: 全レースで学習しつつ、最終3Rの重みを増加
- ✅ **競馬場ID埋め込み**: 統合モデルで各競馬場の特性を反映
- ✅ **的中率優先**: Top-K Accuracy で評価

### 🏇 対象競馬場

| 競馬場 | コード | フルゲート | トリプル馬単 |
|--------|--------|------------|--------------|
| 浦和 | 42 | 14頭 | ✅ 対象 |
| 船橋 | 43 | 14頭 | ✅ 対象 |
| 大井 | 44 | 16頭 | ✅ 対象 |
| 川崎 | 45 | 14頭 | ✅ 対象 |
| 門別 | 30 | 16頭 | ✅ 対象 |
| ~~園田~~ | ~~50~~ | ~~14頭~~ | ❌ 対象外 |
| ~~姫路~~ | ~~51~~ | ~~14頭~~ | ❌ 対象外 |

---

## Phase 11との違い

| 項目 | Phase 11 | Phase 12（本Phase） |
|------|----------|---------------------|
| **役割** | 買い目生成 + Kelly基準投資戦略 | **予測モデルの学習・予測** |
| **入力** | 既存の ensemble CSV（Phase 0-5） | 生データ（race.csv, horse.csv等） |
| **出力** | 買い目テキスト・JSON | **1着/2着確率の ensemble CSV** |
| **予測モデル** | 使用しない（既存予測を利用） | **新規モデルを学習** |
| **学習データ** | 不要 | **全レース + 最終3R重み付け** |
| **特化内容** | 3レース連続買い目 | **2着以内特化予測** |

### 連携フロー

```
Phase 12（本Phase）
  ↓ 1着・2着確率予測
  ↓ 出力: 船橋_20260409_phase12_ensemble.csv
Phase 11
  ↓ 買い目生成 + Kelly基準
  ↓ 出力: 船橋_20260409_triple_balanced.txt
```

---

## システム構成

```
scripts/phase12_umatan_model/
├── PHASE12_UMATAN_MODEL_GUIDE.md    # このドキュメント
├── config.py                        # 設定ファイル
├── filter_triple_races.py           # トリプル馬単レース抽出
├── feature_engineering_top2.py      # 2着以内特化特徴量生成
├── train_multitask_model.py         # マルチタスク学習
├── predict_umatan.py                # 予測実行
├── evaluate_model.py                # モデル評価
└── run_phase12_pipeline.py          # 統合実行スクリプト

data/phase12_umatan/
├── raw/              # 生データ（race.csv, horse.csv等）
├── features/         # 特徴量データ
├── models/           # 学習済みモデル
└── predictions/      # 予測結果（ensemble CSV）
```

---

## モデル設計

### 1️⃣ マルチタスク学習アーキテクチャ

```
入力層
  ↓
共有層（Dense x 3）+ 競馬場ID埋め込み
  ↓
  ├─ Task 1: 1着確率（Binary Classification）
  ├─ Task 2: 2着確率（Binary Classification）
  └─ Task 3: 馬単ペア確率（Ranking Loss）
```

### 2️⃣ 特徴量設計（2着以内特化）

#### 新規追加特徴量

| 特徴量 | 説明 | 理由 |
|--------|------|------|
| `recent_1st_rate` | 過去10走の1着率 | 1着実績重視 |
| `recent_2nd_rate` | 過去10走の2着率 | 2着実績重視 |
| `agari_3f_rank` | 上がり3F順位 | 決め手指標 |
| `final_corner_rank` | 最終コーナー通過順位 | ポジション取り |
| `jockey_1st_rate` | 騎手の1着率 | 騎手の勝率 |
| `jockey_2nd_rate` | 騎手の2着率 | 騎手の連対率 |
| `last3_race_weight` | 最終3Rフラグ | 重み付け用 |
| `venue_id_embedding` | 競馬場ID埋め込み | 競馬場特性反映 |

#### 削除/低優先度特徴量

- `top3_finish_rate` → `top2_finish_rate` に変更
- `class_3rd_rate` → 削除（3着情報不要）

### 3️⃣ 損失関数

```python
total_loss = α * loss_1st + β * loss_2nd + γ * loss_pair

where:
  loss_1st  = Binary Cross Entropy (1着 vs それ以外)
  loss_2nd  = Binary Cross Entropy (2着 vs それ以外)
  loss_pair = Pairwise Ranking Loss (1着-2着ペア)
  
  α = 1.0  # 1着の重み
  β = 0.8  # 2着の重み
  γ = 0.5  # ペアの重み
```

### 4️⃣ 最終3R重み付け

```python
sample_weight = np.where(race['is_last_3_race'], 2.0, 1.0)
```

全レースで学習しつつ、最終3レースの重みを2倍にすることで、トリプル馬単特有の傾向を強調学習。

### 5️⃣ 評価指標（的中率優先）

| 指標 | 説明 | 目標値 |
|------|------|--------|
| **Top-1 Accuracy** | 1位予測が1着的中 | > 40% |
| **Top-2 Accuracy** | 2位以内予測が1着的中 | > 60% |
| **Top-3 Accuracy** | 3位以内予測が1着的中 | > 75% |
| **1-2 Hit Rate** | 1-2着両方的中 | > 25% |
| **Exacta Hit Rate** | 馬単的中（1着→2着） | > 15% |

---

## 使用方法

### 🔧 基本的な使い方

#### Step 1: データ準備（トリプル馬単レース抽出）

```bash
cd /home/user/webapp/anonymous-keiba-ai

# 南関東4場 + 門別のトリプル馬単レースを抽出
python scripts/phase12_umatan_model/filter_triple_races.py \
  --input_dir data/raw \
  --output_dir data/phase12_umatan/raw
```

#### Step 2: 特徴量生成（2着以内特化）

```bash
# 2着以内特化の特徴量を生成
python scripts/phase12_umatan_model/feature_engineering_top2.py \
  --input_dir data/phase12_umatan/raw \
  --output_dir data/phase12_umatan/features
```

#### Step 3: モデル学習（マルチタスク学習）

```bash
# 統合モデル + 競馬場ID埋め込み
python scripts/phase12_umatan_model/train_multitask_model.py \
  --features_dir data/phase12_umatan/features \
  --model_output data/phase12_umatan/models/umatan_multitask_model.pkl \
  --venue_ids 30,42,43,44,45 \
  --last3_weight 2.0
```

#### Step 4: 予測実行

```bash
# 船橋競馬の予測
python scripts/phase12_umatan_model/predict_umatan.py \
  --venue_code 43 \
  --date 20260409 \
  --model_path data/phase12_umatan/models/umatan_multitask_model.pkl \
  --output_dir data/phase12_umatan/predictions
```

**出力ファイル**:
- `data/phase12_umatan/predictions/船橋_20260409_phase12_ensemble.csv`

#### Step 5: Phase 11 連携（買い目生成）

```bash
# Phase 12 の予測結果を Phase 11 に入力
python scripts/phase11_triple_umatan/run_triple_umatan.py 43 \
  data/phase12_umatan/predictions/船橋_20260409_phase12_ensemble.csv \
  --strategy balanced
```

### ⚙️ 統合パイプライン実行

```bash
# 全工程を一括実行
python scripts/phase12_umatan_model/run_phase12_pipeline.py \
  --venue_code 43 \
  --date 20260409 \
  --strategy balanced
```

---

## 実装詳細

### 📊 データフロー

```
[1] 生データ（race.csv, horse.csv等）
  ↓ filter_triple_races.py
[2] トリプル馬単レース（南関東4場 + 門別）
  ↓ feature_engineering_top2.py
[3] 2着以内特化特徴量
  ↓ train_multitask_model.py
[4] 学習済みモデル（umatan_multitask_model.pkl）
  ↓ predict_umatan.py
[5] 予測結果（船橋_20260409_phase12_ensemble.csv）
  ↓ Phase 11: run_triple_umatan.py
[6] 買い目テキスト（船橋_20260409_triple_balanced.txt）
```

### 🧪 モデル比較実験

Phase 12 では、以下の3つのモデルを比較検証します：

| モデル | 説明 | 期待性能 |
|--------|------|----------|
| **統合モデル** | 5競馬場統合 + ID埋め込み | 汎化性能高 |
| **競馬場別モデル** | 各競馬場個別学習 | 特化性能高 |
| **アンサンブル** | 統合 + 競馬場別の組み合わせ | 最高性能 |

**推奨**: 統合モデルで開発開始 → 性能不足なら競馬場別追加

---

## 注意事項

### ⚠️ 技術的留意点

1. **クラス不均衡問題**
   - 1着: 約7-10% （14-16頭立て）
   - 2着: 約7-10%
   - 3着以下: 約80-85%
   
   **対策**: 
   - Focal Loss の使用
   - SMOTE（Synthetic Minority Over-sampling）
   - Class Weight の調整

2. **過学習リスク**
   - 最終3R重み付けにより過学習しやすい
   
   **対策**:
   - Early Stopping
   - Dropout（0.3-0.5）
   - L2正則化

3. **データリーク**
   - 未来情報の混入を厳密にチェック
   
   **対策**:
   - 時系列分割（Time Series Split）
   - 特徴量生成時の厳密なフィルタ

### 🛡️ Phase 11 との整合性

- **出力フォーマット**: Phase 11 が期待する CSV カラムと一致させる
- **競馬場コード**: SPAT4 の競馬場コードと統一
- **レース番号**: 最終3レースのみを出力

---

## トラブルシューティング

### Q1: 学習データが少ない（門別）

**A1**: 以下の戦略を検討

```bash
# 戦略1: 統合モデルで補完
python train_multitask_model.py --venue_ids 30,42,43,44,45

# 戦略2: データ拡張（時系列ブートストラップ）
python train_multitask_model.py --augmentation time_bootstrap

# 戦略3: 転移学習（南関東4場で事前学習 → 門別ファインチューニング）
python train_multitask_model.py --pretrain 42,43,44,45 --finetune 30
```

### Q2: 的中率が低い

**A2**: 以下を確認

1. **特徴量の有効性**: SHAP値で重要度分析
2. **最終3R重み**: 過学習していないか検証
3. **競馬場特性**: 競馬場別の性能差を確認
4. **アンサンブル**: 複数モデルの組み合わせ

### Q3: Phase 11 との連携エラー

**A3**: 出力CSVのカラムを確認

```python
# Phase 11 が期待するカラム
required_columns = [
    'race_bango',      # レース番号
    'umaban',          # 馬番
    'ensemble_score',  # 予測スコア（1着確率 + 2着確率）
    'final_rank',      # 最終順位（1,2,3,...）
    'keibajo_code'     # 競馬場コード
]
```

---

## まとめ

Phase 12 は、**トリプル馬単に特化した予測モデル**を新規開発します。

### ✅ 主な特徴

- **2着以内特化**: 1着・2着の確率に特化した予測
- **マルチタスク学習**: 複数のタスクを同時学習
- **最終3R重み付け**: トリプル馬単特有の傾向を強調
- **統合モデル**: 5競馬場を統合し、競馬場IDで特性を反映
- **Phase 11 連携**: 予測結果を Phase 11 に入力し、買い目生成

### 🎯 期待される効果

- **的中率向上**: 2着以内特化により、馬単的中率が向上
- **最終3R最適化**: トリプル馬単の対象レースに最適化
- **競馬場適応**: 各競馬場の特性を反映した予測

---

**Enjoy Responsible Betting with AI! 🏇💰**
