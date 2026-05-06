# Phase 5: アンサンブル統合実装ガイド（距離カテゴリ対応）

## 📋 目次

1. [概要](#概要)
2. [システム構成](#システム構成)
3. [使用方法](#使用方法)
4. [ワークフロー詳細](#ワークフロー詳細)
5. [カスタマイズ](#カスタマイズ)
6. [トラブルシューティング](#トラブルシューティング)
7. [パフォーマンス指標](#パフォーマンス指標)

---

## 概要

Phase 5は、**距離カテゴリ対応の126モデル（Binary 42 + Ranking 42 + Regression 42）** の予測結果を統合し、最終的な馬券購入判断を行うための最終順位を決定します。

### 🎯 目的

- **Binary（二値分類）**: TOP3入線確率を予測
- **Ranking（順位）**: レース内順位をスコアリング
- **Regression（タイム）**: 走破タイムを予測

これら3種類の予測を **重み付けアンサンブル** し、最も信頼性の高い最終順位を決定します。

### 📂 ディレクトリ構成

```
anonymous-keiba-ai/
├── scripts/
│   ├── predict/                           # 予測スクリプト
│   │   ├── predict_binary_distance.py     # Binary予測
│   │   ├── predict_ranking_distance.py    # Ranking予測
│   │   └── predict_regression_distance.py # Regression予測
│   └── phase5_ensemble/                   # アンサンブル統合
│       └── ensemble_distance_category.py  # 統合スクリプト
├── models/                                # 学習済みモデル
│   ├── binary_distance/                   # Binaryモデル（42個）
│   ├── ranking_distance/                  # Rankingモデル（42個）
│   └── regression_distance/               # Regressionモデル（42個）
├── data/
│   ├── test/                              # テストデータ（67特徴量）
│   └── predictions/                       # 予測結果
│       ├── binary/                        # Binary予測結果
│       ├── ranking/                       # Ranking予測結果
│       ├── regression/                    # Regression予測結果
│       └── ensemble/                      # 最終統合結果
└── PREDICT_AND_ENSEMBLE.bat               # 一括実行バッチ
```

---

## システム構成

### 🧩 モデル構成

#### 距離カテゴリ分類

| カテゴリ | 距離範囲 | 特性 |
|---------|---------|-----|
| **SHORT** | ≤1200m | スプリント適性 |
| **MILE** | 1300-1700m | 中距離適性 |
| **LONG** | ≥1800m | 長距離適性 |

#### モデル数

- **14競馬場** × **3距離カテゴリ** × **3タスク** = **126モデル**

### 🔄 予測ワークフロー

```
入力データ（67特徴量CSV）
    ↓
┌───────────────────────────────────────┐
│ 距離判定: kyori列から自動判定          │
│ - SHORT (≤1200m)                      │
│ - MILE (1300-1700m)                  │
│ - LONG (≥1800m)                      │
└───────────────────────────────────────┘
    ↓
┌──────────────────┬──────────────────┬──────────────────┐
│   Phase 3        │   Phase 4-1      │   Phase 4-2      │
│   Binary予測     │   Ranking予測    │   Regression予測 │
│                  │                  │                  │
│ カテゴリ別モデル │ カテゴリ別モデル │ カテゴリ別モデル │
│ - SHORT_model   │ - SHORT_model   │ - SHORT_model   │
│ - MILE_model    │ - MILE_model    │ - MILE_model    │
│ - LONG_model    │ - LONG_model    │ - LONG_model    │
│                  │                  │                  │
│ 出力:            │ 出力:            │ 出力:            │
│ binary_prob     │ ranking_score   │ predicted_time  │
│ predicted_class │ predicted_rank  │ time_rank       │
└──────────────────┴──────────────────┴──────────────────┘
    ↓
┌───────────────────────────────────────┐
│ Phase 5: アンサンブル統合              │
│                                       │
│ 1. race_id + umaban でマージ          │
│ 2. レースごとに0-1正規化              │
│ 3. 重み付き合成                       │
│    ensemble_score =                   │
│      0.3 × binary_normalized +        │
│      0.5 × ranking_normalized +       │
│      0.2 × regression_normalized      │
│ 4. 最終順位決定                       │
│    final_rank = rank(ensemble_score) │
└───────────────────────────────────────┘
    ↓
最終予測結果（ensemble CSV）
```

---

## 使用方法

### 🚀 方法1: 一括実行バッチ（推奨）

**最も簡単な方法です。**

```batch
PREDICT_AND_ENSEMBLE.bat <競馬場名> <日付> <入力CSV> <モデルディレクトリ>
```

#### 使用例

```batch
REM 浦和競馬場、2025年2月7日のデータを予測
PREDICT_AND_ENSEMBLE.bat urawa 20250207 data\test\urawa_20250207_67features.csv models

REM 船橋競馬場、2025年2月8日のデータを予測
PREDICT_AND_ENSEMBLE.bat funabashi 20250208 data\test\funabashi_20250208_67features.csv models
```

#### 出力ファイル

実行後、以下のファイルが自動生成されます：

```
data/predictions/
├── binary/urawa_20250207_binary.csv
├── ranking/urawa_20250207_ranking.csv
├── regression/urawa_20250207_regression.csv
└── ensemble/urawa_20250207_ensemble.csv  ← 最終結果
```

---

### 🛠️ 方法2: 個別実行（詳細制御）

#### Step 1: Binary予測

```batch
python scripts\predict\predict_binary_distance.py ^
    --input data\test\urawa_20250207_67features.csv ^
    --models models\binary_distance ^
    --output data\predictions\binary\urawa_20250207_binary.csv ^
    --keibajo urawa
```

#### Step 2: Ranking予測

```batch
python scripts\predict\predict_ranking_distance.py ^
    --input data\test\urawa_20250207_67features.csv ^
    --models models\ranking_distance ^
    --output data\predictions\ranking\urawa_20250207_ranking.csv ^
    --keibajo urawa
```

#### Step 3: Regression予測

```batch
python scripts\predict\predict_regression_distance.py ^
    --input data\test\urawa_20250207_67features.csv ^
    --models models\regression_distance ^
    --output data\predictions\regression\urawa_20250207_regression.csv ^
    --keibajo urawa
```

#### Step 4: Ensemble統合

```batch
python scripts\phase5_ensemble\ensemble_distance_category.py ^
    --binary data\predictions\binary\urawa_20250207_binary.csv ^
    --ranking data\predictions\ranking\urawa_20250207_ranking.csv ^
    --regression data\predictions\regression\urawa_20250207_regression.csv ^
    --output data\predictions\ensemble\urawa_20250207_ensemble.csv ^
    --weight-binary 0.3 ^
    --weight-ranking 0.5 ^
    --weight-regression 0.2
```

---

## ワークフロー詳細

### 📊 入力データ要件

#### 必須列

| 列名 | 型 | 説明 | 例 |
|-----|---|------|---|
| `kaisai_nen` | int | 開催年 | 2025 |
| `kaisai_tsukihi` | int | 開催月日 | 20250207 |
| `keibajo_code` | int | 競馬場コード | 42 |
| `race_bango` | int | レース番号 | 1 |
| `umaban` | int | 馬番 | 5 |
| `ketto_toroku_bango` | int | 血統登録番号 | 1234567890 |
| `kyori` | int | 距離（メートル） | 1400 |
| **67特徴量** | float | 学習時と同じ特徴量 | - |

#### 自動生成列

- **`race_id`**: `kaisai_nen_kaisai_tsukihi_keibajo_code_race_bango` 形式で自動生成
  - 例: `2025_20250207_42_01`
- **`distance_category`**: `kyori`から自動判定
  - 例: 1400m → `MILE`

---

### 🔢 スコア正規化

#### 正規化方式

各予測スコアをレース内で0〜1に正規化します。

| タイプ | 正規化方向 | 理由 |
|-------|----------|-----|
| **Binary** | 大→小（降順） | 確率が高いほど良い |
| **Ranking** | 大→小（降順） | スコアが高いほど順位が良い |
| **Regression** | 小→大（昇順） | タイムが速いほど良い |

#### 正規化式

**降順（大きいほど良い）:**

```
normalized = (score - min) / (max - min)
```

**昇順（小さいほど良い）:**

```
normalized = 1.0 - (score - min) / (max - min)
```

---

### 🎚️ 重み付けアンサンブル

#### デフォルト重み

| モデル | 重み | 理由 |
|-------|-----|------|
| **Binary** | 30% | TOP3入線の信頼性を反映 |
| **Ranking** | 50% | 最も直接的な順位予測 |
| **Regression** | 20% | タイム差の微妙な差異を補完 |

#### アンサンブルスコア計算式

```
ensemble_score = 
    0.3 × binary_normalized +
    0.5 × ranking_normalized +
    0.2 × regression_normalized
```

#### 最終順位決定

```python
final_rank = rank(ensemble_score, ascending=False, method='min')
```

- レース内でスコアが高い順に順位付け
- 同点の場合は全員に最小順位を付与（`method='min'`）

---

## カスタマイズ

### 🔧 重みのカスタマイズ

重みを変更する場合は、バッチファイルまたはコマンドラインで指定します。

#### 例1: Binary重視（40%）

```batch
python scripts\phase5_ensemble\ensemble_distance_category.py ^
    --binary ... ^
    --ranking ... ^
    --regression ... ^
    --output ... ^
    --weight-binary 0.4 ^
    --weight-ranking 0.4 ^
    --weight-regression 0.2
```

#### 例2: Ranking重視（60%）

```batch
python scripts\phase5_ensemble\ensemble_distance_category.py ^
    --binary ... ^
    --ranking ... ^
    --regression ... ^
    --output ... ^
    --weight-binary 0.2 ^
    --weight-ranking 0.6 ^
    --weight-regression 0.2
```

#### 例3: Regression重視（30%）

```batch
python scripts\phase5_ensemble\ensemble_distance_category.py ^
    --binary ... ^
    --ranking ... ^
    --regression ... ^
    --output ... ^
    --weight-binary 0.3 ^
    --weight-ranking 0.4 ^
    --weight-regression 0.3
```

**注意:** 重みの合計が1.0でない場合、自動正規化されます。

---

### 📁 出力ファイル形式

#### Ensemble統合結果（ensemble CSV）

| 列名 | 型 | 説明 | 例 |
|-----|---|------|---|
| `race_id` | str | レースID | 2025_20250207_42_01 |
| `kaisai_nen` | int | 開催年 | 2025 |
| `kaisai_tsukihi` | int | 開催月日 | 20250207 |
| `keibajo_code` | int | 競馬場コード | 42 |
| `race_bango` | int | レース番号 | 1 |
| `umaban` | int | 馬番 | 5 |
| `ketto_toroku_bango` | int | 血統登録番号 | 1234567890 |
| `kyori` | int | 距離（メートル） | 1400 |
| `distance_category` | str | 距離カテゴリ | MILE |
| `binary_probability` | float | Binary予測確率 | 0.7234 |
| `ranking_score` | float | Ranking予測スコア | 8.456 |
| `predicted_time` | float | Regression予測タイム（秒） | 84.32 |
| `ensemble_score` | float | アンサンブルスコア | 0.6891 |
| `ensemble_score_normalized` | float | 正規化後スコア（0〜1） | 0.8234 |
| **`final_rank`** | int | **最終予測順位** | **1** |

#### 最終順位の使い方

- **`final_rank == 1`**: 1位予測馬（最有力候補）
- **`final_rank <= 3`**: TOP3予測馬（馬券対象候補）
- **`ensemble_score_normalized >= 0.7`**: 高信頼度予測（信頼性70%以上）

---

## トラブルシューティング

### ❌ 問題1: モデルファイルが見つかりません

**エラーメッセージ:**

```
[ERROR] Binaryモデルディレクトリが見つかりません: models\binary_distance
```

**原因:**

- モデルディレクトリが存在しない
- パスが間違っている

**解決方法:**

1. モデルディレクトリの存在を確認：

```batch
dir models\binary_distance
dir models\ranking_distance
dir models\regression_distance
```

2. 各ディレクトリに42個のモデルファイルが存在することを確認：

```batch
dir models\binary_distance\*.txt /b | find /c ".txt"
dir models\ranking_distance\*.txt /b | find /c ".txt"
dir models\regression_distance\*.txt /b | find /c ".txt"
```

**期待結果:** 各ディレクトリに42個の`.txt`ファイル

---

### ❌ 問題2: 'kyori'列が見つかりません

**エラーメッセージ:**

```
エラー: 'kyori'列が見つかりません
```

**原因:**

- 入力CSVファイルに`kyori`列が含まれていない

**解決方法:**

1. 入力CSVファイルの列を確認：

```batch
python -c "import pandas as pd; df = pd.read_csv('data/test/urawa_20250207_67features.csv', encoding='shift-jis'); print(df.columns.tolist())"
```

2. `kyori`列が存在しない場合は、67特徴量変換スクリプトを再実行：

```batch
REM 67特徴量変換を再実行（kyori列が含まれる）
python scripts\utils\add_67features.py ^
    --input data\raw\urawa_2020-2025.csv ^
    --output data\features\67features_FULL\urawa_67features_FULL.csv
```

---

### ❌ 問題3: race_idでマージできません

**エラーメッセージ:**

```
KeyError: 'race_id'
```

**原因:**

- 予測結果CSVに`race_id`列が存在しない

**解決方法:**

- 予測スクリプトは自動的に`race_id`を生成します
- 入力データに`kaisai_nen`, `kaisai_tsukihi`, `keibajo_code`, `race_bango`が必須

---

### ❌ 問題4: 重みの合計が1.0ではありません

**警告メッセージ:**

```
⚠️  警告: 重みの合計が1.0ではありません (1.1)
  - 自動正規化します
```

**原因:**

- カスタム重みの合計が1.0ではない

**解決方法:**

- **自動正規化されるため問題ありません**
- 明示的に1.0にする場合は重みを調整：

```batch
--weight-binary 0.3 --weight-ranking 0.5 --weight-regression 0.2
```

合計: 0.3 + 0.5 + 0.2 = **1.0** ✅

---

## パフォーマンス指標

### 📈 予測精度目標

| モデル | 目標精度 | 現在の平均 |
|-------|---------|-----------|
| **Binary (AUC)** | ≥0.75 | **0.7581** ✅ |
| **Ranking (Top-3 Accuracy)** | ≥15% | **15.51%** ✅ |
| **Regression (R²)** | ≥0.70 | **0.7103** ✅ |
| **Ensemble (Top-1 Accuracy)** | ≥25% | **TBD** 🔄 |

### ⏱️ 実行時間目安

| ステップ | 推定時間 | 備考 |
|---------|---------|------|
| Binary予測 | 1-3分 | カテゴリ別に並列処理 |
| Ranking予測 | 1-3分 | カテゴリ別に並列処理 |
| Regression予測 | 1-3分 | カテゴリ別に並列処理 |
| Ensemble統合 | <1分 | データマージと正規化 |
| **合計** | **3-10分** | 1レース分の全予測 |

---

## 次のステップ

### ✅ Phase 5完了後の推奨アクション

1. **バックテスト実行**
   - 2024-2025年データで精度検証
   - 期待的中率 ≥25%（1位予測）

2. **ROI分析**
   - 信頼度別の回収率計算
   - `ensemble_score_normalized ≥ 0.7` の馬券的中率

3. **リアルタイム予測**
   - レース当日の予測自動化
   - データ取得 → 67特徴量変換 → 予測 → アンサンブル

4. **馬券戦略構築**
   - TOP3予測を使った三連複/三連単
   - 信頼度スコアによる賭け金調整

---

## まとめ

Phase 5アンサンブル統合により、126モデルの予測結果を統一的に扱い、最も信頼性の高い最終順位を決定できます。

**重要ファイル:**

- **一括実行バッチ:** `PREDICT_AND_ENSEMBLE.bat`
- **アンサンブルスクリプト:** `scripts/phase5_ensemble/ensemble_distance_category.py`
- **予測スクリプト:** `scripts/predict/predict_*_distance.py`

**推奨ワークフロー:**

```
入力データ準備 → 一括実行バッチ実行 → 最終結果確認 → 馬券購入判断
```

**質問・問題があれば、本ガイドのトラブルシューティング章を参照してください。**

---

**作成日:** 2026-05-06  
**バージョン:** 1.0  
**更新履歴:**

- 2026-05-06: 初版作成（距離カテゴリ対応126モデル版）
