# 📊 全14競馬場 学習データ生成完了報告

**報告日**: 2026-02-11  
**対象期間**: 2020-2026年  
**ステータス**: ✅ **13/14会場 生成完了** (帯広のみ未生成)

---

## ✅ 生成成功会場一覧 (13会場)

| No. | 競馬場 | ファイル名 | レコード数 | ファイルサイズ | ステータス |
|-----|--------|-----------|-----------|--------------|----------|
| 1 | 門別 | `monbetsu_2020-2026_with_time_PHASE78.csv` | 57,017件 | 12.39 MB | ✅ 完了 |
| 2 | 盛岡 | `morioka_2020-2026_with_time_PHASE78.csv` | 42,984件 | 9.38 MB | ✅ 完了 |
| 3 | 水沢 | `mizusawa_2020-2026_with_time_PHASE78.csv` | 41,544件 | 9.05 MB | ✅ 完了 |
| 4 | 浦和 | `urawa_2020-2026_with_time_PHASE78.csv` | 43,859件 | 9.58 MB | ✅ 完了 |
| 5 | 船橋 | `funabashi_2020-2026_with_time_PHASE78.csv` | 45,087件 | 9.85 MB | ✅ 完了 |
| 6 | 大井 | `ooi_2020-2026_with_time_PHASE78.csv` | 86,162件 | 19.00 MB | ✅ 完了 |
| 7 | 川崎 | `kawasaki_2020-2026_with_time_PHASE78.csv` | 51,431件 | 11.19 MB | ✅ 完了 |
| 8 | 金沢 | `kanazawa_2020-2026_with_time_PHASE78.csv` | 51,334件 | 11.20 MB | ✅ 完了 |
| 9 | 笠松 | `kasamatsu_2020-2026_with_time_PHASE78.csv` | 48,128件 | 10.45 MB | ✅ 完了 |
| 10 | 名古屋 | `nagoya_2020-2026_with_time_PHASE78.csv` | 86,817件 | 19.03 MB | ✅ 完了 |
| 11 | 園田 | `sonoda_2020-2026_with_time_PHASE78.csv` | 97,383件 | 21.23 MB | ✅ 完了 |
| 12 | 姫路 | `himeji_2020-2026_with_time_PHASE78.csv` | 19,262件 | 4.18 MB | ✅ 完了 |
| 13 | 高知 | `kochi_2020-2026_with_time_PHASE78.csv` | 73,482件 | 16.21 MB | ✅ 完了 |
| 14 | 佐賀 | `saga_2020-2026_with_time_PHASE78.csv` | 77,373件 | 16.99 MB | ✅ 完了 |

---

## ⚠️ 未生成会場 (1会場)

| No. | 競馬場 | コード | ステータス | 対応方法 |
|-----|--------|--------|----------|----------|
| 2 | 帯広 | 33 | ❌ 未生成 | 下記コマンドで生成 |

**帯広データ生成コマンド**:
```bash
python extract_training_data_v2.py --keibajo 33 --start-date 2020 --end-date 2026 --output data\training\obihiro_2020-2026_with_time_PHASE78.csv
```

---

## 📊 総合統計

| 項目 | 数値 |
|------|------|
| **生成成功会場** | 14/14会場 (93.3%) |
| **生成失敗会場** | 1/14会場 (6.7%) |
| **総レコード数** | 821,863件 |
| **総ファイルサイズ** | 179.75 MB |
| **1会場あたり平均** | 58,704件 |
| **データ期間** | 2020年〜2026年 (6年間) |

---

## 📋 データ構造詳細

### カラム構成 (52個)

**ターゲット変数 (3個)**:
1. `target` - Binary分類用 (3着以内=1, 圏外=0)
2. `rank_target` - Ranking学習用 (着順 1〜N位)
3. `time` - Regression学習用 (走破タイム 秒単位)

**特徴量 (49個)**:
- 基本情報: `kaisai_nen`, `kaisai_tsukihi`, `keibajo_code`, `race_bango`, ...
- レース情報: `kyori`, `track_code`, `babajotai_code_shiba`, `babajotai_code_dirt`, ...
- 馬情報: `seibetsu_code`, `barei`, `futan_juryo`, ...
- 過去走データ (1〜5走前): `prev1_rank`, `prev1_time`, `prev2_rank`, ...

### ターゲット変数の分布 (船橋の例)

```
target (Binary):
  - 0 (圏外): 32,112件 (71.2%)
  - 1 (3着以内): 12,975件 (28.8%)

rank_target (Ranking):
  - 最小: 1位
  - 最大: 14位
  - 平均: 5.94位

time (Regression):
  - 最小: 585.0秒
  - 最大: 2,501.0秒
  - 平均: 1,325.7秒
```

### 過去走データ利用率 (船橋の例)

```
prev1 (1走前): 44,673件 (99.1%)
prev2 (2走前): 44,236件 (98.1%)
prev5 (5走前): 43,286件 (96.0%)
```

---

## 🔍 品質検証結果

### ✅ 正常項目

- ✅ 全13会場でカラム数52個を確認
- ✅ ターゲット変数 (target, rank_target, time) が全会場で存在
- ✅ 過去走データ利用率95%以上
- ✅ Binary分布が適切 (約70:30)
- ✅ データ型が全て数値型 (52個)
- ✅ エンコーディング正常 (Shift-JIS)

### ⚠️ 注意事項

- `grade_code`: 全会場で100%欠損 (地方競馬ではグレード情報が少ない)
- `moshoku_code`: 一部会場で15-20%欠損 (毛色情報の記録漏れ)
- `prev5_*`: 2-4%欠損 (新馬やデビュー直後の馬)

---

## 🎯 次のステップ

### ステップ1: 帯広データ生成 (オプション)

```bash
cd E:\anonymous-keiba-ai
python extract_training_data_v2.py --keibajo 33 --start-date 2020 --end-date 2026 --output data\training\obihiro_2020-2026_with_time_PHASE78.csv
```

### ステップ2: Phase 7 Ranking 特徴量選択 (船橋でテスト)

```bash
cd E:\anonymous-keiba-ai
python run_phase7_funabashi_ranking.py
```

**実行時間**: 約10〜20分  
**出力**:
- `data/features/selected/funabashi_ranking_selected_features.csv`
- `data/reports/phase7_feature_selection/funabashi_ranking_importance.png`
- `data/reports/phase7_feature_selection/funabashi_ranking_report.json`

### ステップ3: Phase 7 Regression 特徴量選択 (船橋でテスト)

```bash
cd E:\anonymous-keiba-ai
python run_phase7_funabashi_regression.py
```

**実行時間**: 約10〜20分  
**出力**:
- `data/features/selected/funabashi_regression_selected_features.csv`
- `data/reports/phase7_feature_selection/funabashi_regression_importance.png`
- `data/reports/phase7_feature_selection/funabashi_regression_report.json`

### ステップ4: Phase 8 Optuna最適化 (船橋でテスト)

```bash
# Ranking最適化
python run_phase8_funabashi_ranking.py

# Regression最適化
python run_phase8_funabashi_regression.py
```

**実行時間**: 各30〜60分  
**出力**:
- `data/models/tuned/funabashi_ranking_tuned_model.txt`
- `data/models/tuned/funabashi_regression_tuned_model.txt`

### ステップ5: 全会場展開

船橋でのテストが成功したら、全13会場に展開:

```bash
# Phase 7 全会場実行
RUN_PHASE7_ALL_VENUES.bat

# Phase 8 全会場実行
RUN_PHASE8_ALL_VENUES.bat
```

---

## 📚 関連ドキュメント

| ドキュメント | 用途 |
|-------------|------|
| `SIMPLE_EXECUTION_GUIDE.md` | 簡単実行ガイド |
| `QUICKSTART_PHASE7_FUNABASHI.md` | Phase 7クイックスタート |
| `PHASE7_8_EXECUTION_ROADMAP.md` | 全体ロードマップ |
| `EXECUTION_CHECKLIST_FUNABASHI.md` | チェックリスト |

---

## 🆘 トラブルシューティング

### 問題1: データベース接続エラー

```bash
python test_db_connection.py
```

### 問題2: メモリ不足

会場を分けて実行、または `--limit` オプションを使用

### 問題3: ファイルが見つからない

```bash
cd E:\anonymous-keiba-ai
dir data\training\*_PHASE78.csv
```

---

**最終更新**: 2026-02-11  
**ステータス**: ✅ 13/14会場 生成完了 (92.9%)  
**次のアクション**: Phase 7 Ranking 特徴量選択 (船橋)
