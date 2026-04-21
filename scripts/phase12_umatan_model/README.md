# Phase 12: トリプル馬単特化予測モデル

> **Phase 11 との違い**: Phase 11 は買い目生成、Phase 12 は予測モデル本体の学習

## 🎯 概要

南関東4場（大井/浦和/船橋/川崎）+ 門別のトリプル馬単に特化した予測モデル。
**2着以内特化** + **マルチタスク学習** により、馬単的中率を最大化。

## 📊 主な特徴

| 項目 | 内容 |
|------|------|
| **対象競馬場** | 南関東4場 + 門別（園田・姫路除外） |
| **学習データ** | 全レース + 最終3R重み付け（2倍） |
| **モデル構成** | 統合モデル + 競馬場ID埋め込み |
| **予測タスク** | 1着確率 + 2着確率 + 馬単ペア確率 |
| **評価指標** | 的中率優先（Top-K Accuracy） |

## 📁 ディレクトリ構成

```
scripts/phase12_umatan_model/
├── PHASE12_UMATAN_MODEL_GUIDE.md    # 詳細ガイド
├── config.py                        # 設定ファイル
├── filter_triple_races.py           # トリプル馬単レース抽出
├── feature_engineering_top2.py      # 2着以内特化特徴量生成
├── train_multitask_model.py         # マルチタスク学習（未実装）
├── predict_umatan.py                # 予測実行（未実装）
├── evaluate_model.py                # モデル評価（未実装）
└── run_phase12_pipeline.py          # 統合実行（未実装）

data/phase12_umatan/
├── raw/              # トリプル馬単レースデータ
├── features/         # 2着以内特化特徴量
├── models/           # 学習済みモデル
└── predictions/      # 予測結果（ensemble CSV）
```

## 🚀 使用方法

### Step 1: データフィルタリング

```bash
cd /home/user/webapp/anonymous-keiba-ai

python scripts/phase12_umatan_model/filter_triple_races.py \
  --input_dir data/raw \
  --output_dir data/phase12_umatan/raw
```

### Step 2: 特徴量生成

```bash
python scripts/phase12_umatan_model/feature_engineering_top2.py \
  --input_dir data/phase12_umatan/raw \
  --output_dir data/phase12_umatan/features
```

### Step 3: モデル学習（未実装）

```bash
python scripts/phase12_umatan_model/train_multitask_model.py \
  --features_dir data/phase12_umatan/features \
  --model_output data/phase12_umatan/models/umatan_model.pkl
```

### Step 4: 予測実行（未実装）

```bash
python scripts/phase12_umatan_model/predict_umatan.py \
  --venue_code 43 \
  --date 20260409 \
  --model_path data/phase12_umatan/models/umatan_model.pkl
```

### Step 5: Phase 11 連携

```bash
python scripts/phase11_triple_umatan/run_triple_umatan.py 43 \
  data/phase12_umatan/predictions/船橋_20260409_phase12_ensemble.csv \
  --strategy balanced
```

## 📝 新規特徴量（2着以内特化）

| 特徴量 | 説明 |
|--------|------|
| `recent_1st_rate` | 過去10走の1着率 |
| `recent_2nd_rate` | 過去10走の2着率 |
| `agari_3f_rank` | 上がり3F順位 |
| `final_corner_rank` | 最終コーナー通過順位 |
| `jockey_1st_rate` | 騎手の1着率 |
| `jockey_2nd_rate` | 騎手の2着率 |
| `is_last_3_race` | 最終3Rフラグ（重み付け用） |

## 🎯 期待される成果

| 指標 | 目標値 |
|------|--------|
| Top-1 Accuracy | > 40% |
| Top-2 Accuracy | > 60% |
| 馬単的中率 | > 15% |

## 📖 詳細ドキュメント

詳細は [PHASE12_UMATAN_MODEL_GUIDE.md](./PHASE12_UMATAN_MODEL_GUIDE.md) を参照。

---

**Status**: 🚧 開発中（データフィルタ・特徴量生成まで完了）
