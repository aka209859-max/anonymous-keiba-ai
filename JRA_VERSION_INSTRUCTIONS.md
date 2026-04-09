# 🏇 中央競馬（JRA）版AI予想システム構築のための完全指示書

**作成日**: 2026年02月14日  
**対象**: 新規セッションでのJRA版システム開発  
**既存システム**: 地方競馬AI予想システム（Phase 0-11完成）

---

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [既存システムアーキテクチャ分析](#既存システムアーキテクチャ分析)
3. [地方競馬とJRAの違い](#地方競馬とjraの違い)
4. [JRA版システム設計方針](#jra版システム設計方針)
5. [実装手順](#実装手順)
6. [技術的課題と解決策](#技術的課題と解決策)
7. [GitHubリポジトリ情報](#githubリポジトリ情報)

---

## 1. プロジェクト概要

### 🎯 目的

既存の**地方競馬AI予想システム**の実装経験を活用し、**中央競馬（JRA）専用の予想システム**を新規構築する。

### ✅ 既存システムの状態

- **リポジトリ**: https://github.com/aka209859-max/anonymous-keiba-ai
- **ブランチ**: `phase0_complete_fix_2026_02_07`
- **完成度**: Phase 0-11（100%完成）
- **最新コミット**: `aa4bb50` - Phase 11 トリプル馬単システム実装完了

### 🆕 新規開発目標

- **プロジェクト名**: JRA-Keiba-AI（仮称）
- **対象**: 中央競馬（JRA）10競馬場
- **ベース**: 地方競馬システムのアーキテクチャを流用
- **独立性**: 完全に独立したリポジトリ/プロジェクトとして構築

---

## 2. 既存システムアーキテクチャ分析

### 📁 プロジェクト構造

```
anonymous-keiba-ai/
├── scripts/
│   ├── phase0_data_acquisition/       # データ取得（PC-KEIBA PostgreSQL）
│   ├── phase1_feature_engineering/    # 特徴量エンジニアリング
│   ├── phase3_binary/                 # 二値分類（出走・非出走判定）
│   ├── phase4_ranking/                # ランキング予測（着順予想）
│   ├── phase4_regression/             # 回帰予測（走行タイム予想）
│   ├── phase5_ensemble/               # アンサンブル統合（重み付け統合）
│   ├── phase6_betting/                # 配信用ファイル生成（Note、ブッカーズ、Twitter）
│   ├── phase7_feature_selection/      # Greedy Boruta特徴量選択
│   ├── phase8_auto_tuning/            # Optuna自動最適化
│   ├── phase9_betting_strategy/       # Kelly基準ベッティングエンジン
│   ├── phase10_backtest/              # バックテスト・ROI検証
│   └── phase11_triple_umatan/         # トリプル馬単システム（独立）
├── models/
│   ├── binary/                        # 14競馬場別モデル
│   ├── ranking/
│   ├── regression/
│   └── best_params.csv                # Optuna最適パラメータ
├── data/
│   ├── raw/                           # 生データ（PC-KEIBA）
│   ├── features/                      # 特徴量データ
│   ├── predictions/                   # 予測結果
│   └── training/                      # 学習用データ
└── docs/                              # ドキュメント
```

### 🔧 技術スタック

| カテゴリ | 技術 | 用途 |
|---------|------|------|
| 言語 | Python 3.14 | メイン開発言語 |
| データベース | PostgreSQL | PC-KEIBAデータ格納 |
| 機械学習 | LightGBM | 予測モデル |
| 特徴量選択 | Greedy Boruta | ノイズ除去 |
| 最適化 | Optuna 3.x | ハイパーパラメータ最適化 |
| 資金管理 | Kelly基準 | 賭け金最適化 |
| 確率計算 | Harvilleの公式 | 3連単理論値 |
| スクレイピング | BeautifulSoup, Requests | キャリーオーバー取得 |

### 📊 データフロー

```
[Phase 0] データ取得
  ↓ PC-KEIBA PostgreSQL → raw CSV
[Phase 1] 特徴量エンジニアリング
  ↓ 50カラム生成 → features CSV
[Phase 3] 二値分類予測
  ↓ 出走確率 → binary CSV
[Phase 4-1] ランキング予測
  ↓ 着順スコア → ranking CSV
[Phase 4-2] 回帰予測
  ↓ 走行タイム → regression CSV
[Phase 5] アンサンブル統合
  ↓ 重み付け統合（Binary 30%, Ranking 50%, Regression 20%） → ensemble CSV
[Phase 6] 配信ファイル生成
  ↓ Note/ブッカーズ/Twitter用テキスト → txt files
```

### 🎯 主要機能

#### Phase 0: データ取得
- **ファイル**: `extract_race_data.py`
- **機能**: PC-KEIBA PostgreSQLから過去レースデータを取得
- **対応競馬場**: 14場（門別、盛岡、水沢、浦和、船橋、大井、川崎、金沢、笠松、名古屋、園田、姫路、高知、佐賀）
- **出力**: `data/raw/{年}/{月}/{競馬場}_{日付}_raw.csv`

#### Phase 1: 特徴量エンジニアリング
- **ファイル**: `prepare_features_safe.py`
- **機能**: 過去成績、騎手成績、血統情報などから50特徴量を生成
- **特徴量例**:
  - `prev1_rank`, `prev2_rank`, `prev3_rank` - 過去3走の着順
  - `jockey_win_rate` - 騎手勝率
  - `weight_change` - 馬体重増減
  - `speed_rating` - スピード指数
- **欠損値処理**: 平均値/中央値/0埋め

#### Phase 3: 二値分類
- **ファイル**: `predict_phase3_inference.py`
- **機能**: 出走するか否か（競走中止、失格、降着除外）
- **モデル**: LightGBM（14競馬場別）
- **評価指標**: AUC 平均0.77（範囲: 0.7459〜0.8275）

#### Phase 4-1: ランキング予測
- **ファイル**: `predict_phase4_ranking_inference.py`
- **機能**: 着順スコアを予測（小さいほど上位）
- **モデル**: LightGBM Ranker

#### Phase 4-2: 回帰予測
- **ファイル**: `predict_phase4_regression_inference.py`
- **機能**: 走行タイムを予測
- **モデル**: LightGBM Regressor

#### Phase 5: アンサンブル統合
- **ファイル**: `ensemble_predictions.py`
- **重み**: Binary 30%, Ranking 50%, Regression 20%
- **最終スコア**: 0〜1に正規化（1が最高評価）

#### Phase 6: 配信ファイル生成
- **ファイル**:
  - `generate_distribution_note.py` - Note投稿用
  - `generate_distribution_bookers.py` - ブッカーズ投稿用
  - `generate_distribution_tweet.py` - Twitter投稿用
- **機能**: 各レースのTOP馬と買い目を生成

#### Phase 7: 特徴量選択（Greedy Boruta）
- **ファイル**: `run_boruta_selection.py`
- **機能**: 重要でない特徴量を除外（50個→20-30個）
- **効果**: AUC +0.01〜0.03、計算効率向上

#### Phase 8: 自動最適化（Optuna）
- **ファイル**: `run_optuna_tuning.py`
- **機能**: LightGBMのハイパーパラメータ最適化
- **期待効果**: AUC 0.77→0.85以上

#### Phase 9: ベッティングエンジン（Kelly基準）
- **ファイル**: `betting_strategy_engine.py`
- **機能**: Kelly基準による最適賭け金算出
- **期待効果**: 回収率60%→120%+

#### Phase 10: バックテスト
- **ファイル**: `backtest_simulator.py`
- **機能**: 過去1年分のシミュレーション

#### Phase 11: トリプル馬単（独立システム）
- **ディレクトリ**: `scripts/phase11_triple_umatan/`
- **機能**: キャリーオーバー取得、Kelly基準投資戦略、買い目生成
- **対象**: 南関東4場、門別、園田、姫路
- **特徴**: 完全独立システム（Phase 0-10と分離）

---

## 3. 地方競馬とJRAの違い

### 🏇 対象競馬場

| 地方競馬 | JRA（中央競馬） |
|---------|----------------|
| 14競馬場 | 10競馬場 |
| 門別、盛岡、水沢、浦和、船橋、大井、川崎、金沢、笠松、名古屋、園田、姫路、高知、佐賀 | 札幌、函館、福島、新潟、東京、中山、中京、京都、阪神、小倉 |

### 📊 データソース

| 項目 | 地方競馬 | JRA |
|------|---------|-----|
| データベース | PC-KEIBA PostgreSQL | **JRA-VAN Data Lab** または netkeiba.com スクレイピング |
| データ形式 | SQL直接クエリ | **Data Lab SDK**（推奨） or HTML解析 |
| データ量 | 約68万件（2020-2025） | 約数百万件（2020-2025） |
| 更新頻度 | 開催日翌日 | リアルタイム（JRA-VAN） |

### 🎲 レース構成

| 項目 | 地方競馬 | JRA |
|------|---------|-----|
| 1日のレース数 | 10〜12R | 12R（土日祝） |
| 出走頭数 | 8〜16頭（競馬場により異なる） | 最大18頭（フルゲート） |
| グレード | 地方重賞（Jpn1, Jpn2, Jpn3） | G1, G2, G3, リステッド |
| 賞金規模 | 数百万〜数千万円 | 数千万〜数億円 |

### 💰 馬券種類

| 馬券 | 地方競馬 | JRA |
|------|---------|-----|
| 単勝・複勝 | ✅ | ✅ |
| 馬連・馬単 | ✅ | ✅ |
| 3連複・3連単 | ✅ | ✅ |
| ワイド | ✅ | ✅ |
| **WIN5** | ❌ | ✅ |
| **トリプル馬単** | ✅（SPAT4 LOTO） | ❌ |

### 🔍 特徴量の違い

| 特徴量 | 地方競馬 | JRA | 対応方法 |
|--------|---------|-----|----------|
| 馬場状態 | ダート主体 | 芝・ダート・障害 | **馬場種別カラム追加** |
| コース形態 | 小回り多い | 大回り・直線長い | **コース特性カラム追加** |
| 騎手ランク | 地方騎手 | 中央騎手 | **騎手データベース分離** |
| 調教師ランク | 地方調教師 | 中央調教師 | **調教師データベース分離** |
| 血統情報 | 地方産馬多い | サラブレッド主体 | **血統辞書更新** |

---

## 4. JRA版システム設計方針

### 🎯 基本方針

1. **既存アーキテクチャの流用**
   - Phase 0-10 の構造をそのまま活用
   - ファイル名、関数名、データフロー を統一

2. **データソースの変更**
   - PC-KEIBA → **JRA-VAN Data Lab**（推奨）
   - または netkeiba.com スクレイピング

3. **競馬場数の変更**
   - 14場 → **10場**（札幌、函館、福島、新潟、東京、中山、中京、京都、阪神、小倉）

4. **特徴量の拡張**
   - 芝・ダート・障害の区別
   - コース形状（右回り・左回り・直線距離）
   - 開催時期（春・夏・秋・冬）

5. **独立プロジェクト化**
   - 新規GitHubリポジトリ作成: `jra-keiba-ai`
   - 地方競馬システムとは完全分離

### 📦 プロジェクト名・ディレクトリ構造

```
jra-keiba-ai/
├── scripts/
│   ├── phase0_data_acquisition/       # JRA-VAN Data Lab対応
│   ├── phase1_feature_engineering/    # 芝・ダート特徴量追加
│   ├── phase3_binary/                 # 10競馬場モデル
│   ├── phase4_ranking/
│   ├── phase4_regression/
│   ├── phase5_ensemble/
│   ├── phase6_betting/
│   ├── phase7_feature_selection/
│   ├── phase8_auto_tuning/
│   ├── phase9_betting_strategy/
│   └── phase10_backtest/
├── models/
│   ├── binary/                        # 10競馬場別モデル
│   ├── ranking/
│   └── regression/
├── data/
│   ├── raw/                           # JRA-VANデータ
│   ├── features/
│   └── predictions/
└── docs/
```

---

## 5. 実装手順

### 🚀 Phase 0: プロジェクトセットアップ

#### Step 1: 新規GitHubリポジトリ作成

```bash
# ローカル環境で新規プロジェクト作成
mkdir jra-keiba-ai
cd jra-keiba-ai
git init
git remote add origin https://github.com/YOUR_USERNAME/jra-keiba-ai.git
```

#### Step 2: 基本ディレクトリ構造作成

```bash
mkdir -p scripts/{phase0_data_acquisition,phase1_feature_engineering,phase3_binary,phase4_ranking,phase4_regression,phase5_ensemble,phase6_betting,phase7_feature_selection,phase8_auto_tuning,phase9_betting_strategy,phase10_backtest}
mkdir -p models/{binary,ranking,regression}
mkdir -p data/{raw,features,predictions,training}
mkdir -p docs
```

#### Step 3: README.md作成

```markdown
# JRA Keiba AI - 中央競馬AI予想システム

中央競馬（JRA）に特化した定量的取引エンジン

## 対象競馬場
- 札幌、函館、福島、新潟、東京、中山、中京、京都、阪神、小倉

## 技術スタック
- Python 3.14
- LightGBM
- JRA-VAN Data Lab
- Optuna, Kelly基準
```

---

### 📊 Phase 1: データ取得（JRA-VAN対応）

#### データソースの選択

##### オプション1: JRA-VAN Data Lab（推奨）

**メリット**:
- ✅ 公式データ、高信頼性
- ✅ リアルタイム更新
- ✅ SDK提供（Python対応）
- ✅ 過去データ完備

**デメリット**:
- ❌ 有料（月額数千円）
- ❌ API学習コスト

**実装方法**:
```python
# JRA-VAN Data Lab SDKのインストール
pip install jravan-sdk

# データ取得スクリプト
import jravan

# JRA-VANから過去レースデータを取得
data = jravan.get_race_results(
    start_date='2020-01-01',
    end_date='2025-12-31',
    venue_codes=['05', '06', '08', '09', '10', '11', '12', '13', '14', '15']
)
```

##### オプション2: netkeiba.com スクレイピング

**メリット**:
- ✅ 無料
- ✅ データ豊富

**デメリット**:
- ❌ 利用規約確認必須
- ❌ robots.txt遵守
- ❌ アクセス頻度制限
- ❌ DOM構造変更リスク

**実装方法**:
```python
import requests
from bs4 import BeautifulSoup

# netkeibaからスクレイピング
url = f"https://race.netkeiba.com/race/result.html?race_id=202105050411"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
# 着順、馬名、騎手名などを抽出
```

#### 実装ファイル: `scripts/phase0_data_acquisition/extract_race_data_jra.py`

**変更点**:
- データソース: PC-KEIBA PostgreSQL → JRA-VAN Data Lab
- 競馬場コード: 地方14場 → JRA10場
- カラム追加: `track_type`（芝/ダート/障害）、`track_condition`（良/稍重/重/不良）

---

### 🔧 Phase 2: 特徴量エンジニアリング

#### 実装ファイル: `scripts/phase1_feature_engineering/prepare_features_jra.py`

**追加特徴量**:

1. **馬場種別関連**
   - `track_type_芝`, `track_type_ダート`, `track_type_障害` (One-Hot)
   - `turf_win_rate` - 芝コース勝率
   - `dirt_win_rate` - ダートコース勝率

2. **コース特性関連**
   - `track_direction` - 右回り/左回り
   - `straight_length` - 直線距離（m）
   - `course_category` - 平坦/坂/急坂

3. **開催時期関連**
   - `season_spring`, `season_summer`, `season_autumn`, `season_winter` (One-Hot)
   - `opening_week` - 開催週（1〜5週）

4. **JRA特有情報**
   - `gradeclass` - G1/G2/G3/一般/未勝利
   - `prize_money` - 賞金額
   - `field_size` - 出走頭数

**既存特徴量**（流用可能）:
- `prev1_rank`, `prev2_rank`, `prev3_rank`
- `jockey_win_rate`
- `weight_change`
- `speed_rating`

---

### 🤖 Phase 3-5: モデル学習・予測・アンサンブル

#### 既存コードの流用

**Phase 3: 二値分類**
- ファイル名変更: `predict_phase3_inference.py` → `predict_phase3_inference_jra.py`
- モデルパス変更: `models/binary/{地方競馬場}` → `models/binary/{JRA競馬場}`
- 学習データ: JRA過去5年分（2020-2025）

**Phase 4-1: ランキング予測**
- ほぼそのまま流用可能
- LightGBM Ranker は変更不要

**Phase 4-2: 回帰予測**
- ほぼそのまま流用可能
- 目的変数: 走行タイム（秒）

**Phase 5: アンサンブル統合**
- そのまま流用可能
- 重み: Binary 30%, Ranking 50%, Regression 20%

---

### 📝 Phase 6: 配信ファイル生成

#### 変更点

**買い目フォーマット**:
- 地方競馬: 三連複（1・2位 - 2・3・4位 - 2・3・4・5・6・7位）
- JRA: **WIN5対応** or 3連単フルカバー

**実装ファイル**:
- `generate_distribution_note_jra.py`
- `generate_distribution_bookers_jra.py`
- `generate_distribution_tweet_jra.py`

**新機能**:
- **WIN5買い目生成**: 指定5レースの本命馬を組み合わせ
- **馬場状態別分析**: 芝・ダート別の推奨馬

---

### 🎯 Phase 7-10: 高度化機能

**Phase 7: Greedy Boruta特徴量選択**
- そのまま流用可能
- JRA特有特徴量（芝/ダート）の重要度確認

**Phase 8: Optuna自動最適化**
- そのまま流用可能
- JRAデータで再チューニング

**Phase 9: Kelly基準ベッティングエンジン**
- そのまま流用可能
- JRAオッズデータ対応

**Phase 10: バックテスト**
- そのまま流用可能
- JRA過去1年分でシミュレーション

---

## 6. 技術的課題と解決策

### 🔴 課題1: JRA-VAN Data Lab のAPI学習コスト

**解決策**:
- 公式ドキュメント参照: https://www.jra-van.jp/
- サンプルコード活用
- 初期はnetkeibaスクレイピングで代替も検討

### 🔴 課題2: 芝・ダートの特徴量設計

**解決策**:
- `track_type` カラムでOne-Hot化
- 芝専用モデル、ダート専用モデルを別々に学習
- または統合モデルで `track_type` を特徴量に含める

### 🔴 課題3: 18頭立てフルゲート対応

**解決策**:
- 出走頭数を特徴量に追加: `field_size`
- 馬番（枠順）の重要性を考慮: `post_position`
- 内枠・外枠の有利不利を分析

### 🔴 課題4: WIN5の買い目生成

**解決策**:
- Phase 6 で専用スクリプト作成: `generate_win5_tickets.py`
- 指定5レースのTOP3馬を組み合わせ
- 購入点数: 3^5 = 243点 → 1点100円 = 24,300円

### 🔴 課題5: リアルタイム予測

**解決策**:
- Phase 0 でJRA-VANからリアルタイムデータ取得
- Phase 1-5 を高速化（数秒以内に完了）
- Phase 6 で即座に買い目生成

---

## 7. GitHubリポジトリ情報

### 📌 既存リポジトリ（地方競馬）

- **URL**: https://github.com/aka209859-max/anonymous-keiba-ai
- **ブランチ**: `phase0_complete_fix_2026_02_07`
- **最新コミット**: `aa4bb50`
- **参照方法**:

```bash
# 既存リポジトリをクローン
git clone https://github.com/aka209859-max/anonymous-keiba-ai.git
cd anonymous-keiba-ai
git checkout phase0_complete_fix_2026_02_07

# Phase 0-11 のコードを確認
ls -la scripts/
```

### 🆕 新規リポジトリ（JRA版）

- **リポジトリ名**: `jra-keiba-ai`
- **作成手順**:

```bash
# 新規ディレクトリ作成
mkdir jra-keiba-ai
cd jra-keiba-ai
git init

# GitHubで新規リポジトリ作成後
git remote add origin https://github.com/YOUR_USERNAME/jra-keiba-ai.git

# 初回コミット
git add .
git commit -m "Initial commit: JRA Keiba AI system"
git push -u origin main
```

---

## 8. 実装チェックリスト

### ✅ Phase 0: プロジェクトセットアップ

- [ ] 新規GitHubリポジトリ作成
- [ ] ディレクトリ構造作成
- [ ] README.md作成
- [ ] `.gitignore`作成

### ✅ Phase 1: データ取得

- [ ] JRA-VAN Data Lab SDK導入 or netkeibaスクレイピング実装
- [ ] 10競馬場のデータ取得スクリプト作成
- [ ] データ形式統一（CSV）

### ✅ Phase 2: 特徴量エンジニアリング

- [ ] 芝・ダート特徴量追加
- [ ] コース特性特徴量追加
- [ ] 既存特徴量の流用確認

### ✅ Phase 3-5: モデル学習・予測・アンサンブル

- [ ] 10競馬場別モデル学習
- [ ] Phase 3 二値分類実装
- [ ] Phase 4-1 ランキング予測実装
- [ ] Phase 4-2 回帰予測実装
- [ ] Phase 5 アンサンブル統合実装

### ✅ Phase 6: 配信ファイル生成

- [ ] Note/ブッカーズ/Twitter用スクリプト実装
- [ ] WIN5買い目生成スクリプト実装

### ✅ Phase 7-10: 高度化機能

- [ ] Greedy Boruta特徴量選択実装
- [ ] Optuna自動最適化実装
- [ ] Kelly基準ベッティングエンジン実装
- [ ] バックテスト実装

---

## 9. 新規セッション開始時の指示文

### 📋 指示文テンプレート

```
こんにちは！新規セッションで中央競馬（JRA）版AI予想システムを構築します。

【前提情報】
- 既存の地方競馬AI予想システムが完成しています（Phase 0-11）
- GitHubリポジトリ: https://github.com/aka209859-max/anonymous-keiba-ai
- ブランチ: phase0_complete_fix_2026_02_07
- 最新コミット: aa4bb50

【新規開発目標】
- プロジェクト名: jra-keiba-ai
- 対象: 中央競馬（JRA）10競馬場（札幌、函館、福島、新潟、東京、中山、中京、京都、阪神、小倉）
- ベース: 地方競馬システムのアーキテクチャを流用
- データソース: JRA-VAN Data Lab または netkeiba.com

【実装手順】
1. 既存リポジトリ（anonymous-keiba-ai）を確認
2. Phase 0-11 のコード構造を分析
3. JRA版の設計方針を決定
4. 新規リポジトリ（jra-keiba-ai）を作成
5. Phase 0（データ取得）から順次実装

【重要な変更点】
- 競馬場数: 14場 → 10場
- データソース: PC-KEIBA PostgreSQL → JRA-VAN Data Lab
- 特徴量追加: 芝/ダート、コース形状、開催時期
- 買い目: WIN5対応

【質問】
まず、既存リポジトリのPhase 0-11を確認し、JRA版の実装計画を立てていただけますか？
特に以下の点を重点的にお願いします:
1. Phase 0（データ取得）のJRA-VAN対応方針
2. Phase 1（特徴量エンジニアリング）の芝・ダート特徴量設計
3. Phase 6（配信ファイル生成）のWIN5買い目生成方法

参考ドキュメント: /home/user/webapp/anonymous-keiba-ai/JRA_VERSION_INSTRUCTIONS.md
```

---

## 10. まとめ

### ✅ 準備完了事項

1. ✅ 地方競馬AI予想システム（Phase 0-11）完成
2. ✅ GitHubにプッシュ完了（コミット: aa4bb50）
3. ✅ トリプル馬単システム（Phase 11）完成（保留中）
4. ✅ JRA版システム構築指示書作成完了

### 🚀 次のステップ

1. **新規セッション開始**
2. **既存リポジトリ確認**: `git clone https://github.com/aka209859-max/anonymous-keiba-ai.git`
3. **JRA版設計方針決定**: データソース選択、特徴量設計
4. **Phase 0実装開始**: JRA-VAN Data Lab対応

### 📚 参考資料

- **地方競馬システムREADME**: `/home/user/webapp/anonymous-keiba-ai/README.md`
- **Phase 11実装完了報告**: `/home/user/webapp/anonymous-keiba-ai/PHASE11_IMPLEMENTATION_COMPLETE.md`
- **Phase 7-10統合ガイド**: `/home/user/webapp/anonymous-keiba-ai/docs/PHASE7_10_INTEGRATION_GUIDE.md`

---

**作成者**: Claude (AI Assistant)  
**作成日**: 2026年02月14日  
**バージョン**: 1.0  
**ステータス**: ✅ 完成

---

**Good Luck with JRA Version Development! 🏇🎯**
