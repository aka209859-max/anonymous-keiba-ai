# 距離カテゴリ別モデル学習ガイド (126モデル)

## 📊 モデル設計 - Option 3: 3カテゴリ（最高精度型）

### 構成
```
14競馬場 × 3距離カテゴリ × 3タスク = 126モデル

【競馬場】14箇所
- 浦和、船橋、川崎、大井
- 盛岡、水沢、門別
- 金沢、笠松、名古屋
- 園田、姫路
- 高知、佐賀

【距離カテゴリ】3種類
- SHORT: ≤1200m  (短距離スプリント)
- MILE:  1300-1700m (マイル～中距離)
- LONG:  ≥1800m  (長距離ステイヤー)

【タスク】3種類
- Binary:     TOP3入線予測 (二値分類)
- Ranking:    着順予測 (ランキング学習)
- Regression: タイム予測 (回帰)
```

---

## 🎯 なぜ距離カテゴリ別が必要か？

### 問題点（旧設計: 競馬場のみ）
❌ 浦和800m（5,580レース）と2000m（3,120レース）を同じモデルで予測  
❌ 短距離スプリンターと長距離馬を同列に扱う  
❌ 距離特性（ペース配分、求められる能力）が異なる  

### 解決策（新設計: 距離カテゴリ別）
✅ 距離帯ごとに専用モデル  
✅ スプリント/マイル/ステイヤーの戦略を分離  
✅ 予測精度の向上  

### データ分布例
| 競馬場 | SHORT | MILE | LONG |
|--------|-------|------|------|
| 浦和   | 5,580 (12.9%) | 34,593 (79.9%) | 3,130 (7.2%) |
| 船橋   | 23,078 (52.0%) | 17,961 (40.5%) | 3,337 (7.5%) |
| 中山   | 78.4% SHORT | ... | ... |

**全体**: SHORT 20.0%, MILE 75.6%, LONG 4.5%

---

## 📥 ダウンロード

### 1. 学習スクリプト（3ファイル）

#### Binary分類用
```
ファイル名: train_phase3_binary_distance.py
URL: https://www.genspark.ai/api/files/s/7nfOIJoC
保存先: E:\anonymous-keiba-ai\scripts\phase3_binary\
```

#### Ranking学習用
```
ファイル名: train_phase4_ranking_distance.py
URL: https://www.genspark.ai/api/files/s/SH7epdz4
保存先: E:\anonymous-keiba-ai\scripts\phase4_ranking\
```

#### Regression学習用
```
ファイル名: train_phase4_regression_distance.py
URL: https://www.genspark.ai/api/files/s/iJihtF48
保存先: E:\anonymous-keiba-ai\scripts\phase4_regression\
```

### 2. 一括実行バッチファイル

```
ファイル名: TRAIN_ALL_126_MODELS.bat
URL: https://www.genspark.ai/api/files/s/yco981vb
保存先: E:\anonymous-keiba-ai\
```

---

## 🚀 実行手順

### Step 1: ファイルをダウンロード

上記4ファイルをそれぞれの保存先にダウンロードしてください。

### Step 2: データ準備確認

以下のディレクトリに67特徴量データが存在することを確認：

```cmd
E:\anonymous-keiba-ai\data\features\67features_FULL\

必要なファイル（14競馬場）:
- urawa_67features_FULL.csv
- funabashi_67features_FULL.csv
- kawasaki_67features_FULL.csv
- ooi_67features_FULL.csv
- morioka_67features_FULL.csv
- mizusawa_67features_FULL.csv
- monbetsu_67features_FULL.csv
- kanazawa_67features_FULL.csv
- kasamatsu_67features_FULL.csv
- nagoya_67features_FULL.csv
- sonoda_67features_FULL.csv
- himeji_67features_FULL.csv
- kochi_67features_FULL.csv
- saga_67features_FULL.csv
```

### Step 3: 実行

#### 🔴 推奨: 一括実行（夜間実行推奨）

```cmd
cd E:\anonymous-keiba-ai
TRAIN_ALL_126_MODELS.bat
```

**推定時間**: 25-30時間

#### 🟡 段階実行（分割実行）

##### Phase 1: Binary分類（8-10時間）
```cmd
cd E:\anonymous-keiba-ai
python scripts\phase3_binary\train_phase3_binary_distance.py ^
    --input data\features\67features_FULL ^
    --output models\binary_distance
```

##### Phase 2: Ranking学習（10-12時間）
```cmd
cd E:\anonymous-keiba-ai
python scripts\phase4_ranking\train_phase4_ranking_distance.py ^
    --input data\features\67features_FULL ^
    --output models\ranking_distance
```

##### Phase 3: Regression学習（7-9時間）
```cmd
cd E:\anonymous-keiba-ai
python scripts\phase4_regression\train_phase4_regression_distance.py ^
    --input data\features\67features_FULL ^
    --output models\regression_distance
```

---

## 📂 出力ファイル

### ディレクトリ構造
```
E:\anonymous-keiba-ai\models\
├── binary_distance\       (42モデル)
│   ├── urawa_SHORT_binary_model.txt
│   ├── urawa_MILE_binary_model.txt
│   ├── urawa_LONG_binary_model.txt
│   ├── funabashi_SHORT_binary_model.txt
│   └── ... (全42モデル)
│
├── ranking_distance\      (42モデル)
│   ├── urawa_SHORT_ranking_model.txt
│   ├── urawa_MILE_ranking_model.txt
│   ├── urawa_LONG_ranking_model.txt
│   └── ... (全42モデル)
│
└── regression_distance\   (42モデル)
    ├── urawa_SHORT_regression_model.txt
    ├── urawa_MILE_regression_model.txt
    ├── urawa_LONG_regression_model.txt
    └── ... (全42モデル)
```

### ファイル命名規則
```
[競馬場名]_[距離カテゴリ]_[タスク]_model.txt
[競馬場名]_[距離カテゴリ]_[タスク]_metadata.json

例:
- urawa_SHORT_binary_model.txt
- funabashi_MILE_ranking_model.txt
- ooi_LONG_regression_model.txt
```

---

## 📊 期待される成果

### Binary分類（TOP3予測）
- **精度向上**: 距離特性を考慮 → 75-80%程度
- **AUC向上**: 0.77 → 0.80以上を期待

### Ranking（着順予測）
- **Top-1精度**: 距離別に最適化 → 20-25%
- **Top-3精度**: 50-60%

### Regression（タイム予測）
- **MAE改善**: 距離ごとのタイム特性を学習
- **R²向上**: 0.6 → 0.7以上を期待

---

## ⚠️ 注意事項

### 1. 実行環境
- **Python 3.7以上**必須
- **LightGBM**インストール済み（`pip install lightgbm`）
- **pandas, numpy, scikit-learn**必須

### 2. 実行時間
- **合計25-30時間**（一括実行の場合）
- **夜間実行推奨**（PCをスリープさせない設定に）

### 3. データ不足カテゴリ
一部の競馬場×距離カテゴリで100サンプル未満の場合、スキップされます：
- 例: 水沢_LONG = 548サンプル（学習可能）
- 例: 金沢_SHORT = 638サンプル（学習可能）

### 4. メモリ使用量
- 最大使用メモリ: 4-8GB程度
- 余裕を持って**8GB以上のRAM**を推奨

---

## 🔧 トラブルシューティング

### エラー: "No CSV files found!"
→ `data\features\67features_FULL\` ディレクトリが存在するか確認

### エラー: "'kyori' column not found"
→ 67features_FULL CSVに距離（kyori）列が存在するか確認

### エラー: "Insufficient data"
→ 該当カテゴリのサンプル数が100未満（正常動作、スキップされる）

### 学習が途中で止まる
→ メモリ不足の可能性。タスクマネージャーでメモリ使用量を確認

---

## 📈 次のステップ

### 1. モデル評価
学習完了後、各モデルの精度を比較：
```
- Binary: Accuracy, AUC
- Ranking: Top-1/3/5 Accuracy
- Regression: MAE, RMSE, R²
```

### 2. 予測実行
新しい距離カテゴリ別モデルを使って予測を実行：
```cmd
python scripts\phase6_betting\predict_with_distance_category.py
```
（※ 予測スクリプトの対応が必要）

### 3. バックテスト
過去データで回収率を検証：
```cmd
python scripts\phase10_backtest\backtest_with_distance_category.py
```
（※ バックテストスクリプトの対応が必要）

---

## 📞 サポート

問題が発生した場合は、以下の情報を提供してください：
1. エラーメッセージ全文
2. 実行コマンド
3. 実行環境（Python version, OS）

---

**作成日**: 2026-05-06  
**バージョン**: 1.0  
**対応モデル数**: 126モデル（14競馬場 × 3カテゴリ × 3タスク）
