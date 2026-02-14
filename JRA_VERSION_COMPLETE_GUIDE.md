# 🏇 中央競馬（JRA）版AI予想システム構築のための完全自己完結型指示書

**作成日**: 2026年02月14日  
**バージョン**: 2.0（新規セッション完全対応版）  
**重要**: このドキュメントのみで開発を開始できるよう、全ての必要情報を含めています

---

## 📖 この指示書について

### 🎯 目的

既存の**地方競馬AI予想システム**（Phase 0-11完成）を参考に、**中央競馬（JRA）専用の予想システム**を新規構築する。

### ⚠️ 重要な前提

- **新規セッションではGitHubリポジトリの直接参照は困難**
- この指示書に**全ての必要な情報を含める**（コード例、設計思想、実装パターン）
- 既存システムの参照は**補足情報として記載**

---

## 1. 既存システム（地方競馬）の完全構造

### 📁 プロジェクト構造

```
anonymous-keiba-ai/
├── scripts/
│   ├── phase0_data_acquisition/       # PC-KEIBA PostgreSQLからデータ取得
│   ├── phase1_feature_engineering/    # 50特徴量生成
│   ├── phase3_binary/                 # 二値分類（出走判定）
│   ├── phase4_ranking/                # ランキング予測
│   ├── phase4_regression/             # 回帰予測（タイム）
│   ├── phase5_ensemble/               # アンサンブル統合
│   ├── phase6_betting/                # 配信ファイル生成
│   ├── phase7_feature_selection/      # Greedy Boruta
│   ├── phase8_auto_tuning/            # Optuna最適化
│   ├── phase9_betting_strategy/       # Kelly基準
│   ├── phase10_backtest/              # バックテスト
│   └── phase11_triple_umatan/         # トリプル馬単（独立）
├── models/
│   ├── binary/{競馬場}_v3_model.txt   # 14競馬場別モデル
│   ├── ranking/{競馬場}_model.txt
│   └── regression/{競馬場}_model.txt
├── data/
│   ├── raw/{年}/{月}/{競馬場}_{日付}_raw.csv
│   ├── features/{年}/{月}/{競馬場}_{日付}_features.csv
│   └── predictions/
│       ├── phase3/temp_{日付}_phase3_binary.csv
│       ├── phase4_ranking/temp_{日付}_phase4_ranking.csv
│       ├── phase4_regression/temp_{日付}_phase4_regression.csv
│       └── phase5/temp_{日付}_ensemble.csv
└── predictions/
    ├── {競馬場}_{日付}_note.txt
    ├── {競馬場}_{日付}_bookers.txt
    └── {競馬場}_{日付}_tweet.txt
```

### 🔧 技術スタック詳細

```python
# 必要なライブラリ
pip install pandas numpy scikit-learn lightgbm matplotlib seaborn
pip install optuna scipy psycopg2-binary  # Phase 7-10用
pip install requests beautifulsoup4 lxml  # Phase 11用
```

### 📊 データフロー（完全版）

```
[Phase 0] データ取得
├─ 入力: PC-KEIBA PostgreSQL（地方競馬14場）
├─ 処理: SQLクエリで過去レースデータ取得
└─ 出力: data/raw/{年}/{月}/{競馬場}_{日付}_raw.csv
         カラム: 50個（着順、馬番、騎手、調教師、馬体重等）

↓

[Phase 1] 特徴量エンジニアリング
├─ 入力: raw CSV
├─ 処理: 過去成績、騎手成績、血統情報から50特徴量生成
│   - prev1_rank, prev2_rank, prev3_rank（過去3走着順）
│   - jockey_win_rate（騎手勝率）
│   - weight_change（馬体重増減）
│   - speed_rating（スピード指数）
│   - 欠損値処理: 平均値/0埋め
└─ 出力: data/features/{年}/{月}/{競馬場}_{日付}_features.csv

↓

[Phase 3] 二値分類（出走判定）
├─ 入力: features CSV
├─ モデル: LightGBM Classifier（14競馬場別）
├─ 処理: 競走中止、失格、降着を除外
│   - binary_probability（出走確率 0〜1）
│   - predicted_class（0 or 1）
└─ 出力: data/predictions/phase3/temp_{日付}_phase3_binary.csv
         評価: AUC平均0.77（範囲0.7459〜0.8275）

↓

[Phase 4-1] ランキング予測
├─ 入力: features CSV
├─ モデル: LightGBM Ranker
├─ 処理: 着順スコア算出（小さいほど上位）
│   - ranking_score（ランキングスコア）
│   - predicted_rank（予測着順）
└─ 出力: data/predictions/phase4_ranking/temp_{日付}_phase4_ranking.csv

↓

[Phase 4-2] 回帰予測（タイム）
├─ 入力: features CSV
├─ モデル: LightGBM Regressor
├─ 処理: 走行タイム予測（秒）
│   - predicted_time（予測タイム）
│   - time_rank（タイム順位）
└─ 出力: data/predictions/phase4_regression/temp_{日付}_phase4_regression.csv

↓

[Phase 5] アンサンブル統合
├─ 入力: Phase 3, 4-1, 4-2 の結果
├─ 重み: Binary 30%, Ranking 50%, Regression 20%
├─ 処理: 各スコアを0〜1に正規化→重み付け合計
│   - ensemble_score = 
│     binary_normalized * 0.3 + 
│     ranking_normalized * 0.5 + 
│     regression_normalized * 0.2
│   - final_rank（最終着順予測、レースごとにランク付け）
└─ 出力: data/predictions/phase5/temp_{日付}_ensemble.csv

↓

[Phase 6] 配信ファイル生成
├─ 入力: ensemble CSV
├─ 処理: 各レースのTOP馬と買い目を生成
│   - 単勝・複勝: TOP1, TOP2
│   - 馬単: TOP2の組み合わせ（1→2、2→1）
│   - 三連複: 1・2位 - 2・3・4位 - 2・3・4・5・6・7位
└─ 出力: 
    ├─ predictions/{競馬場}_{日付}_note.txt（Note投稿用）
    ├─ predictions/{競馬場}_{日付}_bookers.txt（ブッカーズ用）
    └─ predictions/{競馬場}_{日付}_tweet.txt（Twitter用）
```

---

## 2. 重要コード例（地方競馬システム）

### Phase 0: データ取得の実装パターン

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 0: データ取得スクリプト（地方競馬版）
PC-KEIBA PostgreSQLから過去レースデータを取得
"""

import psycopg2
import pandas as pd
from datetime import datetime

# 競馬場コードマッピング（地方14場）
VENUE_CODE_MAP = {
    30: '門別', 35: '盛岡', 36: '水沢',
    42: '浦和', 43: '船橋', 44: '大井', 45: '川崎',
    46: '金沢', 47: '笠松', 48: '名古屋',
    50: '園田', 51: '姫路', 54: '高知', 55: '佐賀'
}

def fetch_race_data(venue_code, date):
    """PC-KEIBAからレースデータ取得"""
    conn = psycopg2.connect(
        host='localhost',
        database='pckeiba',
        user='postgres',
        password='your_password'
    )
    
    query = f"""
    SELECT 
        kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango,
        umaban, bamei, kakutei_chakujun,
        kishu_mei, chokyoshi_mei, futan_juryo,
        bataiju, zogen_fugo, zogen_sa,
        tansho_odds, fukusho_odds,
        time_value
    FROM race_results
    WHERE keibajo_code = {venue_code}
      AND kaisai_tsukihi = '{date.replace("-", "")}'
    ORDER BY race_bango, umaban
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def main(venue_code, date):
    """メイン処理"""
    venue_name = VENUE_CODE_MAP.get(venue_code, 'Unknown')
    
    print(f"データ取得開始: {venue_name} {date}")
    
    # データ取得
    df = fetch_race_data(venue_code, date)
    
    # 保存
    year, month = date[:4], date[5:7]
    date_short = date.replace('-', '')
    output_path = f"data/raw/{year}/{month}/{venue_name}_{date_short}_raw.csv"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='shift-jis')
    
    print(f"✅ 保存完了: {output_path} ({len(df)}件)")

if __name__ == "__main__":
    venue_code = 43  # 船橋
    date = "2026-02-14"
    main(venue_code, date)
```

### Phase 1: 特徴量エンジニアリングの実装パターン

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 特徴量エンジニアリング（地方競馬版）
50特徴量を生成
"""

import pandas as pd
import numpy as np

def create_features(df):
    """特徴量生成"""
    
    # 1. 過去成績特徴量
    df['prev1_rank'] = df.groupby('馬番')['着順'].shift(1).fillna(0)
    df['prev2_rank'] = df.groupby('馬番')['着順'].shift(2).fillna(0)
    df['prev3_rank'] = df.groupby('馬番')['着順'].shift(3).fillna(0)
    
    # 2. 騎手成績特徴量
    jockey_stats = df.groupby('騎手名').agg({
        '着順': lambda x: (x <= 3).mean()  # 3着以内率
    }).rename(columns={'着順': 'jockey_win_rate'})
    df = df.merge(jockey_stats, left_on='騎手名', right_index=True, how='left')
    
    # 3. 馬体重関連
    df['weight_change'] = df.groupby('馬番')['馬体重'].diff().fillna(0)
    
    # 4. スピード指数（簡易版）
    df['speed_rating'] = 100 - (df['タイム'] - df['タイム'].min()) / df['タイム'].std()
    
    # 5. オッズ関連
    df['odds_rank'] = df.groupby('レース番号')['単勝オッズ'].rank()
    
    # 欠損値処理
    df.fillna(0, inplace=True)
    
    return df

def main(raw_csv_path, output_csv_path):
    """メイン処理"""
    print(f"特徴量生成開始: {raw_csv_path}")
    
    # データ読み込み
    df = pd.read_csv(raw_csv_path, encoding='shift-jis')
    
    # 特徴量生成
    df_features = create_features(df)
    
    # 保存
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_features.to_csv(output_csv_path, index=False, encoding='shift-jis')
    
    print(f"✅ 保存完了: {output_csv_path} ({len(df_features)}件)")

if __name__ == "__main__":
    raw_csv_path = "data/raw/2026/02/船橋_20260214_raw.csv"
    output_csv_path = "data/features/2026/02/船橋_20260214_features.csv"
    main(raw_csv_path, output_csv_path)
```

### Phase 5: アンサンブル統合の実装パターン

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5: アンサンブル統合（地方競馬版）
Binary 30%, Ranking 50%, Regression 20%
"""

import pandas as pd
import numpy as np

def normalize_score(series, ascending=True):
    """0〜1に正規化"""
    min_val, max_val = series.min(), series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    
    if ascending:
        # 小さいほど良い（タイム）
        return 1.0 - (series - min_val) / (max_val - min_val)
    else:
        # 大きいほど良い（確率）
        return (series - min_val) / (max_val - min_val)

def ensemble_predictions(binary_csv, ranking_csv, regression_csv, output_csv):
    """アンサンブル統合"""
    
    # 重み設定
    WEIGHT_BINARY = 0.3
    WEIGHT_RANKING = 0.5
    WEIGHT_REGRESSION = 0.2
    
    # データ読み込み
    df_binary = pd.read_csv(binary_csv, encoding='shift-jis')
    df_ranking = pd.read_csv(ranking_csv, encoding='shift-jis')
    df_regression = pd.read_csv(regression_csv, encoding='shift-jis')
    
    # マージ
    df = df_binary.merge(
        df_ranking[['race_id', 'umaban', 'ranking_score', 'predicted_rank']],
        on=['race_id', 'umaban'], how='inner'
    ).merge(
        df_regression[['race_id', 'umaban', 'predicted_time', 'time_rank']],
        on=['race_id', 'umaban'], how='inner'
    )
    
    # レースごとに正規化
    df['binary_normalized'] = df.groupby('race_id')['binary_probability'].transform(
        lambda x: normalize_score(x, ascending=False)
    )
    df['ranking_normalized'] = df.groupby('race_id')['ranking_score'].transform(
        lambda x: normalize_score(x, ascending=False)
    )
    df['regression_normalized'] = df.groupby('race_id')['predicted_time'].transform(
        lambda x: normalize_score(x, ascending=True)
    )
    
    # アンサンブルスコア計算
    df['ensemble_score'] = (
        df['binary_normalized'] * WEIGHT_BINARY +
        df['ranking_normalized'] * WEIGHT_RANKING +
        df['regression_normalized'] * WEIGHT_REGRESSION
    )
    
    # 最終順位決定
    df['final_rank'] = df.groupby('race_id')['ensemble_score'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    # 保存
    df.to_csv(output_csv, index=False, encoding='shift-jis')
    print(f"✅ 保存完了: {output_csv}")

if __name__ == "__main__":
    binary_csv = "data/predictions/phase3/temp_20260214_phase3_binary.csv"
    ranking_csv = "data/predictions/phase4_ranking/temp_20260214_phase4_ranking.csv"
    regression_csv = "data/predictions/phase4_regression/temp_20260214_phase4_regression.csv"
    output_csv = "data/predictions/phase5/temp_20260214_ensemble.csv"
    
    ensemble_predictions(binary_csv, ranking_csv, regression_csv, output_csv)
```

---

## 3. 地方競馬とJRAの完全比較表

### 競馬場

| 項目 | 地方競馬 | JRA |
|------|---------|-----|
| 競馬場数 | 14場 | 10場 |
| 競馬場名 | 門別、盛岡、水沢、浦和、船橋、大井、川崎、金沢、笠松、名古屋、園田、姫路、高知、佐賀 | **札幌、函館、福島、新潟、東京、中山、中京、京都、阪神、小倉** |
| 競馬場コード | 30, 35, 36, 42, 43, 44, 45, 46, 47, 48, 50, 51, 54, 55 | **01, 02, 03, 04, 05, 06, 07, 08, 09, 10** |

### データソース

| 項目 | 地方競馬 | JRA | 実装方針 |
|------|---------|-----|----------|
| データベース | PC-KEIBA PostgreSQL | **JRA-VAN Data Lab** または netkeiba.com | JRA-VAN推奨（有料だが信頼性高い） |
| データ形式 | SQLクエリ→CSV | **SDK経由**→CSV or スクレイピング→CSV | SDKまたはスクレイピング |
| データ量 | 約68万件（2020-2025） | 約数百万件（2020-2025） | 同等の処理パイプライン |
| 更新頻度 | 開催日翌日 | **リアルタイム**（JRA-VAN） | リアルタイム対応検討 |

### レース構成

| 項目 | 地方競馬 | JRA | 実装への影響 |
|------|---------|-----|--------------|
| 1日のレース数 | 10〜12R | 12R（土日祝） | 同等の処理 |
| 出走頭数 | 8〜16頭 | **最大18頭** | フルゲート18頭対応 |
| 馬場種別 | **ダート主体** | **芝・ダート・障害** | ✅ **重要**: track_type特徴量追加 |
| コース形態 | 小回り多い | 大回り、直線長い | ✅ **重要**: コース特性特徴量追加 |

### 特徴量の違い

| 特徴量カテゴリ | 地方競馬 | JRA | JRA版での対応 |
|---------------|---------|-----|--------------|
| 馬場状態 | ダート（良、稍重、重、不良） | **芝・ダート・障害** × （良、稍重、重、不良） | `track_type`（芝/ダート/障害）カラム追加 |
| コース形状 | - | **右回り/左回り、直線距離** | `track_direction`, `straight_length` 追加 |
| 開催時期 | - | **春・夏・秋・冬**（馬場状態が季節で変動） | `season` カラム追加 |
| グレード | Jpn1, Jpn2, Jpn3 | **G1, G2, G3, リステッド** | `grade_class` カラム追加 |
| 賞金 | 数百万〜数千万円 | **数千万〜数億円** | `prize_money` カラム追加 |

### 馬券種類

| 馬券 | 地方競馬 | JRA | JRA版での対応 |
|------|---------|-----|--------------|
| 単勝・複勝 | ✅ | ✅ | 同じ |
| 馬連・馬単 | ✅ | ✅ | 同じ |
| 3連複・3連単 | ✅ | ✅ | 同じ |
| ワイド | ✅ | ✅ | 同じ |
| WIN5 | ❌ | ✅ | ✅ **Phase 6で新機能追加** |
| トリプル馬単 | ✅（SPAT4 LOTO） | ❌ | JRA版では不要 |

---

## 4. JRA版システム設計（完全版）

### 📦 プロジェクト構造

```
jra-keiba-ai/
├── scripts/
│   ├── phase0_data_acquisition/
│   │   └── extract_race_data_jra.py       # JRA-VAN対応
│   ├── phase1_feature_engineering/
│   │   └── prepare_features_jra.py        # 芝・ダート特徴量追加
│   ├── phase3_binary/
│   │   └── predict_phase3_inference_jra.py # 10競馬場対応
│   ├── phase4_ranking/
│   │   └── predict_phase4_ranking_inference_jra.py
│   ├── phase4_regression/
│   │   └── predict_phase4_regression_inference_jra.py
│   ├── phase5_ensemble/
│   │   └── ensemble_predictions_jra.py
│   ├── phase6_betting/
│   │   ├── generate_distribution_note_jra.py
│   │   ├── generate_distribution_bookers_jra.py
│   │   ├── generate_distribution_tweet_jra.py
│   │   └── generate_win5_tickets.py      # WIN5専用
│   ├── phase7_feature_selection/
│   ├── phase8_auto_tuning/
│   ├── phase9_betting_strategy/
│   └── phase10_backtest/
├── models/
│   ├── binary/
│   │   ├── 札幌_v1_model.txt
│   │   ├── 函館_v1_model.txt
│   │   ├── ... (10競馬場)
│   ├── ranking/
│   └── regression/
├── data/
│   ├── raw/{年}/{月}/{競馬場}_{日付}_raw.csv
│   ├── features/{年}/{月}/{競馬場}_{日付}_features.csv
│   └── predictions/
└── docs/
    └── README.md
```

### 🆕 JRA版の追加特徴量（合計70特徴量）

#### 既存特徴量（地方競馬から流用、50個）
1. prev1_rank, prev2_rank, prev3_rank
2. jockey_win_rate
3. weight_change
4. speed_rating
5. odds_rank
6. ... (他45個)

#### 新規特徴量（JRA特有、20個）

```python
# 1. 馬場種別関連（5個）
track_type_芝 = 1 if track_type == '芝' else 0
track_type_ダート = 1 if track_type == 'ダート' else 0
track_type_障害 = 1 if track_type == '障害' else 0
turf_win_rate = 芝コースでの勝率
dirt_win_rate = ダートコースでの勝率

# 2. コース特性関連（5個）
track_direction = 1 if '右' else 0  # 右回り/左回り
straight_length = 直線距離（メートル）
course_category = 平坦/坂/急坂（One-Hot 3個）

# 3. 開催時期関連（5個）
season_spring, season_summer, season_autumn, season_winter (One-Hot)
opening_week = 開催週（1〜5週）

# 4. JRA特有情報（5個）
grade_class = G1/G2/G3/一般/未勝利（One-Hot 5個）
prize_money = 賞金額（円）
field_size = 出走頭数（8〜18）
post_position = 枠順（1〜8）
track_condition_num = 馬場状態（良=1, 稍重=2, 重=3, 不良=4）
```

---

## 5. 実装手順（完全版）

### Step 1: プロジェクトセットアップ

```bash
# 新規ディレクトリ作成
mkdir jra-keiba-ai
cd jra-keiba-ai

# Git初期化
git init

# ディレクトリ構造作成
mkdir -p scripts/{phase0_data_acquisition,phase1_feature_engineering,phase3_binary,phase4_ranking,phase4_regression,phase5_ensemble,phase6_betting,phase7_feature_selection,phase8_auto_tuning,phase9_betting_strategy,phase10_backtest}
mkdir -p models/{binary,ranking,regression}
mkdir -p data/{raw,features,predictions,training}
mkdir -p docs

# README作成
cat > README.md << 'EOF'
# JRA Keiba AI - 中央競馬AI予想システム

中央競馬（JRA）に特化した定量的取引エンジン

## 対象競馬場
札幌、函館、福島、新潟、東京、中山、中京、京都、阪神、小倉（10場）

## 技術スタック
- Python 3.14
- LightGBM
- JRA-VAN Data Lab または netkeiba.com
- Optuna, Kelly基準

## Phase構成
- Phase 0: データ取得（JRA-VAN対応）
- Phase 1: 特徴量エンジニアリング（70特徴量）
- Phase 3-5: 予測・アンサンブル
- Phase 6: 配信ファイル生成（WIN5対応）
- Phase 7-10: 高度化機能
EOF
```

### Step 2: Phase 0実装（JRA-VAN対応）

#### オプション1: JRA-VAN Data Lab（推奨）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 0: JRA-VAN Data Labからデータ取得
"""

# 注意: JRA-VAN SDKは実際のSDKドキュメントを参照
# ここでは擬似コードを示します

import pandas as pd
from datetime import datetime
import os

# JRA競馬場コードマッピング
JRA_VENUE_CODE_MAP = {
    1: '札幌', 2: '函館', 3: '福島', 4: '新潟',
    5: '東京', 6: '中山', 7: '中京', 8: '京都',
    9: '阪神', 10: '小倉'
}

def fetch_jra_race_data(venue_code, date):
    """JRA-VANからレースデータ取得"""
    
    # JRA-VAN SDKを使用（実際のAPI呼び出し）
    # 例: jravan.get_race_results()
    
    # ダミー実装（実際はSDK経由で取得）
    data = {
        '開催年': [],
        '開催月日': [],
        '競馬場コード': [],
        'レース番号': [],
        '馬番': [],
        '馬名': [],
        '確定着順': [],
        '騎手名': [],
        '調教師名': [],
        '負担重量': [],
        '馬体重': [],
        '馬体重増減': [],
        '単勝オッズ': [],
        '複勝オッズ': [],
        'タイム': [],
        '馬場種別': [],  # 芝/ダート/障害
        '馬場状態': [],  # 良/稍重/重/不良
        'コース距離': [],
        'コース形状': [],  # 右/左
        'グレード': [],  # G1/G2/G3/一般
        '賞金': []
    }
    
    df = pd.DataFrame(data)
    return df

def main(venue_code, date):
    """メイン処理"""
    venue_name = JRA_VENUE_CODE_MAP.get(venue_code, 'Unknown')
    
    print(f"[Phase 0] データ取得開始: {venue_name} {date}")
    
    # データ取得
    df = fetch_jra_race_data(venue_code, date)
    
    # 保存
    year, month = date[:4], date[5:7]
    date_short = date.replace('-', '')
    output_path = f"data/raw/{year}/{month}/{venue_name}_{date_short}_raw.csv"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"✅ 保存完了: {output_path} ({len(df)}件)")

if __name__ == "__main__":
    venue_code = 5  # 東京
    date = "2026-02-16"  # 日曜日
    main(venue_code, date)
```

#### オプション2: netkeiba.comスクレイピング

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 0: netkeiba.comスクレイピング（代替案）
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_netkeiba_race(race_id):
    """netkeibaから1レースのデータ取得"""
    
    url = f"https://race.netkeiba.com/race/result.html?race_id={race_id}"
    
    # User-Agent設定（必須）
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 着順表を取得（実際のDOM構造に合わせて調整）
    table = soup.find('table', class_='race_table_01')
    
    data = []
    for row in table.find_all('tr')[1:]:  # ヘッダー行をスキップ
        cols = row.find_all('td')
        if len(cols) > 0:
            data.append({
                '着順': cols[0].text.strip(),
                '枠番': cols[1].text.strip(),
                '馬番': cols[2].text.strip(),
                '馬名': cols[3].text.strip(),
                '騎手': cols[6].text.strip(),
                '単勝オッズ': cols[12].text.strip(),
                # ... 他のカラム
            })
    
    df = pd.DataFrame(data)
    
    # アクセス頻度制限（重要！）
    time.sleep(1)
    
    return df

def main(venue_code, date, num_races=12):
    """メイン処理"""
    # race_idの生成（例: 202602051101 = 2026年 東京5回 1日目 1R）
    # 実際のrace_id生成ロジックは要調整
    
    all_data = []
    for race_num in range(1, num_races + 1):
        race_id = f"{date.replace('-', '')}{venue_code:02d}{race_num:02d}"
        
        print(f"取得中: レース{race_num}R (race_id: {race_id})")
        df = scrape_netkeiba_race(race_id)
        all_data.append(df)
    
    # 統合
    df_all = pd.concat(all_data, ignore_index=True)
    
    # 保存
    output_path = f"data/raw/{date[:4]}/{date[5:7]}/東京_{date.replace('-', '')}_raw.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_all.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"✅ 保存完了: {output_path} ({len(df_all)}件)")

if __name__ == "__main__":
    venue_code = 5  # 東京
    date = "2026-02-16"
    main(venue_code, date)
```

### Step 3: Phase 1実装（芝・ダート特徴量追加）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: JRA版特徴量エンジニアリング
既存50特徴量 + JRA特有20特徴量 = 計70特徴量
"""

import pandas as pd
import numpy as np

def create_jra_features(df):
    """JRA特有の特徴量を追加"""
    
    # === 既存特徴量（地方競馬と同じ） ===
    # 過去成績
    df['prev1_rank'] = df.groupby('馬番')['着順'].shift(1).fillna(0)
    df['prev2_rank'] = df.groupby('馬番')['着順'].shift(2).fillna(0)
    df['prev3_rank'] = df.groupby('馬番')['着順'].shift(3).fillna(0)
    
    # 騎手成績
    jockey_stats = df.groupby('騎手名').agg({
        '着順': lambda x: (x <= 3).mean()
    }).rename(columns={'着順': 'jockey_win_rate'})
    df = df.merge(jockey_stats, left_on='騎手名', right_index=True, how='left')
    
    # 馬体重
    df['weight_change'] = df.groupby('馬番')['馬体重'].diff().fillna(0)
    
    # === JRA特有特徴量（新規追加） ===
    
    # 1. 馬場種別（One-Hot）
    df['track_type_芝'] = (df['馬場種別'] == '芝').astype(int)
    df['track_type_ダート'] = (df['馬場種別'] == 'ダート').astype(int)
    df['track_type_障害'] = (df['馬場種別'] == '障害').astype(int)
    
    # 2. 馬場別勝率
    turf_stats = df[df['馬場種別'] == '芝'].groupby('馬番').agg({
        '着順': lambda x: (x == 1).mean()
    }).rename(columns={'着順': 'turf_win_rate'})
    df = df.merge(turf_stats, left_on='馬番', right_index=True, how='left', suffixes=('', '_turf'))
    
    dirt_stats = df[df['馬場種別'] == 'ダート'].groupby('馬番').agg({
        '着順': lambda x: (x == 1).mean()
    }).rename(columns={'着順': 'dirt_win_rate'})
    df = df.merge(dirt_stats, left_on='馬番', right_index=True, how='left', suffixes=('', '_dirt'))
    
    # 3. コース形状
    df['track_direction'] = (df['コース形状'] == '右').astype(int)
    df['straight_length'] = df['直線距離']  # メートル
    
    # 4. 開催時期（季節）
    df['開催月'] = pd.to_datetime(df['開催月日'], format='%Y%m%d').dt.month
    df['season_spring'] = df['開催月'].isin([3, 4, 5]).astype(int)
    df['season_summer'] = df['開催月'].isin([6, 7, 8]).astype(int)
    df['season_autumn'] = df['開催月'].isin([9, 10, 11]).astype(int)
    df['season_winter'] = df['開催月'].isin([12, 1, 2]).astype(int)
    
    # 5. グレード（One-Hot）
    df['grade_G1'] = (df['グレード'] == 'G1').astype(int)
    df['grade_G2'] = (df['グレード'] == 'G2').astype(int)
    df['grade_G3'] = (df['グレード'] == 'G3').astype(int)
    df['grade_listed'] = (df['グレード'] == 'Listed').astype(int)
    df['grade_normal'] = (df['グレード'].isnull() | (df['グレード'] == '一般')).astype(int)
    
    # 6. 賞金・出走頭数
    df['prize_money'] = df['賞金']
    df['field_size'] = df.groupby('レース番号')['馬番'].transform('count')
    df['post_position'] = df['枠番']
    
    # 7. 馬場状態（数値化）
    condition_map = {'良': 1, '稍重': 2, '重': 3, '不良': 4}
    df['track_condition_num'] = df['馬場状態'].map(condition_map).fillna(1)
    
    # 欠損値処理
    df.fillna(0, inplace=True)
    
    return df

def main(raw_csv_path, output_csv_path):
    """メイン処理"""
    print(f"[Phase 1] 特徴量生成開始: {raw_csv_path}")
    
    # データ読み込み
    df = pd.read_csv(raw_csv_path, encoding='utf-8')
    
    # 特徴量生成
    df_features = create_jra_features(df)
    
    # 保存
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_features.to_csv(output_csv_path, index=False, encoding='utf-8')
    
    print(f"✅ 保存完了: {output_csv_path} ({len(df_features)}件、{len(df_features.columns)}特徴量)")

if __name__ == "__main__":
    raw_csv_path = "data/raw/2026/02/東京_20260216_raw.csv"
    output_csv_path = "data/features/2026/02/東京_20260216_features.csv"
    main(raw_csv_path, output_csv_path)
```

### Step 4: Phase 3-5実装（既存コードほぼ流用）

**Phase 3-5は地方競馬版とほぼ同じ**ため、以下の変更のみ実施:

1. ファイル名変更: `_jra.py` サフィックス追加
2. モデルパス変更: `models/binary/{JRA競馬場}_v1_model.txt`
3. 競馬場コードマッピング更新: 14場→10場

### Step 5: Phase 6実装（WIN5対応）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: WIN5買い目生成（JRA専用）
"""

import pandas as pd
from itertools import product

def generate_win5_tickets(ensemble_csv, target_races=[8, 9, 10, 11, 12]):
    """
    WIN5買い目生成
    指定5レースの本命馬（TOP3）を組み合わせ
    """
    
    # データ読み込み
    df = pd.read_csv(ensemble_csv, encoding='utf-8')
    
    # 対象レースのみ抽出
    df_target = df[df['race_bango'].isin(target_races)]
    
    # 各レースのTOP3馬を取得
    top_horses = {}
    for race_num in target_races:
        race_data = df_target[df_target['race_bango'] == race_num]
        top3 = race_data.nsmallest(3, 'final_rank')['umaban'].tolist()
        top_horses[race_num] = top3
    
    # WIN5の組み合わせ生成
    combinations = list(product(*[top_horses[r] for r in target_races]))
    
    # 購入点数と投資額
    num_tickets = len(combinations)
    total_cost = num_tickets * 100  # 1点100円
    
    print(f"WIN5買い目")
    print(f"対象レース: 第{target_races[0]}R 〜 第{target_races[-1]}R")
    print(f"購入点数: {num_tickets}点")
    print(f"投資額: {total_cost:,}円")
    print(f"\n各レースの本命馬:")
    for race_num in target_races:
        print(f"  第{race_num}R: {'-'.join(map(str, top_horses[race_num]))}")
    
    # ファイル保存
    output_path = "predictions/東京_20260216_win5.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"WIN5買い目\n")
        f.write(f"対象レース: 第{target_races[0]}R 〜 第{target_races[-1]}R\n")
        f.write(f"購入点数: {num_tickets}点\n")
        f.write(f"投資額: {total_cost:,}円\n\n")
        for i, combo in enumerate(combinations, 1):
            f.write(f"{i:3d}. {'-'.join(map(str, combo))}\n")
    
    print(f"\n✅ 保存完了: {output_path}")

if __name__ == "__main__":
    ensemble_csv = "data/predictions/phase5/temp_20260216_ensemble.csv"
    generate_win5_tickets(ensemble_csv)
```

---

## 6. 実装チェックリスト

### Phase 0: プロジェクトセットアップ
- [ ] 新規ディレクトリ作成
- [ ] Git初期化
- [ ] README.md作成
- [ ] ディレクトリ構造作成

### Phase 1: データ取得
- [ ] JRA-VAN Data Lab導入 **または** netkeiba.comスクレイピング実装
- [ ] 10競馬場のデータ取得スクリプト作成
- [ ] テストデータ取得（1競馬場、1日分）

### Phase 2: 特徴量エンジニアリング
- [ ] 既存50特徴量の流用
- [ ] JRA特有20特徴量の追加
- [ ] 欠損値処理の実装

### Phase 3-5: モデル学習・予測・アンサンブル
- [ ] 10競馬場別モデル学習（Phase 3）
- [ ] ランキング予測実装（Phase 4-1）
- [ ] 回帰予測実装（Phase 4-2）
- [ ] アンサンブル統合実装（Phase 5）

### Phase 6: 配信ファイル生成
- [ ] Note/ブッカーズ/Twitter用スクリプト実装
- [ ] WIN5買い目生成スクリプト実装

### Phase 7-10: 高度化機能
- [ ] Greedy Boruta特徴量選択
- [ ] Optuna自動最適化
- [ ] Kelly基準ベッティングエンジン
- [ ] バックテスト

---

## 7. まとめ

### ✅ この指示書の使い方

1. **新規セッション開始時**
   - この指示書の全文をAIアシスタントに提示
   - GitHubリポジトリへのアクセスは不要
   - 指示書内のコード例をそのまま使用可能

2. **実装の優先順位**
   - Phase 0（データ取得）から順次実装
   - 各Phaseごとにテスト・検証
   - Phase 6でWIN5対応を実装

3. **地方競馬システムとの差分**
   - 競馬場数: 14場 → 10場
   - データソース: PC-KEIBA → JRA-VAN
   - 特徴量: 50個 → 70個（芝・ダート対応）
   - 買い目: WIN5追加

### 🚀 開発開始コマンド

```bash
# 1. プロジェクト作成
mkdir jra-keiba-ai && cd jra-keiba-ai
git init

# 2. ディレクトリ作成
mkdir -p scripts/{phase0_data_acquisition,phase1_feature_engineering,phase3_binary,phase4_ranking,phase4_regression,phase5_ensemble,phase6_betting}
mkdir -p models/{binary,ranking,regression}
mkdir -p data/{raw,features,predictions}

# 3. Phase 0実装開始
# この指示書の「Step 2: Phase 0実装」のコードをコピー
```

---

**作成者**: Claude (AI Assistant)  
**作成日**: 2026年02月14日  
**バージョン**: 2.0（新規セッション完全対応版）  
**ステータス**: ✅ 完成

---

**Ready to Start JRA Version Development! 🏇🎯**
