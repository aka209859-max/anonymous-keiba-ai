# 📐 anonymous競馬AIシステム 技術仕様書（Phase 7-10）

## ドキュメント情報

| 項目 | 内容 |
|------|------|
| **ドキュメント名** | anonymous競馬AIシステム Phase 7-10 技術仕様書 |
| **バージョン** | v1.0 |
| **作成日** | 2026-02-09 |
| **対象読者** | 開発者、データサイエンティスト、システムアーキテクト |
| **前提知識** | Python 3.14、LightGBM、機械学習の基礎、競馬ドメイン知識 |

---

## 目次

1. [Phase 7: Advanced Feature Selection](#phase-7-advanced-feature-selection)
2. [Phase 8: Auto-Optimization](#phase-8-auto-optimization)
3. [Phase 9: Betting Engine](#phase-9-betting-engine)
4. [Phase 10: Simulation & Backtest](#phase-10-simulation--backtest)
5. [統合アーキテクチャ](#統合アーキテクチャ)
6. [実装ガイドライン](#実装ガイドライン)

---

## Phase 7: Advanced Feature Selection

### 概要

**目的**: Greedy Borutaアルゴリズムを用いて、地方競馬データから統計的に有意な特徴量のみを抽出し、過学習を防止する。

**実装場所**: `scripts/phase7_feature_selection/`

### 7.1 Greedy Borutaの実装仕様

#### 7.1.1 アルゴリズムの選択理由

| 項目 | Standard Boruta | Greedy Boruta | 採用判断 |
|------|----------------|---------------|---------|
| **収束速度** | 遅い（max_iter依存） | 高速（O(-log α)保証） | ✅ Greedy |
| **再現率** | 厳格（偽陽性最小化） | 高い（有用特徴を逃さない） | ✅ Greedy |
| **計算コスト** | 高い | 低い（5〜40倍高速） | ✅ Greedy |

#### 7.1.2 実装コード

```python
# scripts/phase7_feature_selection/greedy_boruta_selector.py

import pandas as pd
import numpy as np
from lightgbm import LGBMClassifier
from greedyboruta import GreedyBorutaPy
import warnings
warnings.filterwarnings('ignore')

class GreedyBorutaSelector:
    """
    Greedy Borutaによる特徴量選択クラス
    """
    
    def __init__(self, alpha=0.10, max_iter=200, n_estimators=500):
        """
        Parameters:
        -----------
        alpha : float, default=0.10
            有意水準（地方競馬のノイズに対応するため緩和）
        max_iter : int, default=200
            最大反復回数
        n_estimators : int, default=500
            Base Estimator（LightGBM）の決定木数
        """
        self.alpha = alpha
        self.max_iter = max_iter
        self.n_estimators = n_estimators
        self.selected_features = None
        self.feature_ranking = None
        
    def fit(self, X, y, categorical_features=None):
        """
        特徴量選択を実行
        
        Parameters:
        -----------
        X : pd.DataFrame
            特徴量行列（前処理済み）
        y : pd.Series
            ターゲット変数（0: 圏外, 1: 3着以内）
        categorical_features : list, optional
            カテゴリカル変数のリスト
            
        Returns:
        --------
        self : object
        """
        print(f"[Phase 7] Starting Greedy Boruta Feature Selection...")
        print(f"  Input Features: {X.shape[1]}")
        
        # Base Estimatorの定義
        lgbm = LGBMClassifier(
            n_estimators=self.n_estimators,
            learning_rate=0.05,
            num_leaves=31,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced',
            importance_type='gain',
            verbose=-1
        )
        
        # Greedy Borutaの初期化
        self.feat_selector = GreedyBorutaPy(
            estimator=lgbm,
            n_estimators='auto',
            perc=100,  # シャドウ特徴量の最大値と比較
            alpha=self.alpha,
            max_iter=self.max_iter,
            verbose=2,
            random_state=42
        )
        
        # フィッティング実行
        self.feat_selector.fit(X.values, y.values)
        
        # 結果の抽出
        selected_mask = self.feat_selector.support_
        self.selected_features = X.columns[selected_mask].tolist()
        
        # ランキングの作成
        self.feature_ranking = pd.DataFrame({
            'Feature': X.columns,
            'Rank': self.feat_selector.ranking_,
            'Selected': self.feat_selector.support_
        }).sort_values('Rank')
        
        print(f"  Selected Features: {len(self.selected_features)}")
        print(f"  Reduction Rate: {100 * (1 - len(self.selected_features) / X.shape[1]):.1f}%")
        
        return self
    
    def transform(self, X):
        """
        選択された特徴量のみを返す
        
        Parameters:
        -----------
        X : pd.DataFrame
            特徴量行列
            
        Returns:
        --------
        pd.DataFrame
            選択された特徴量のみのDataFrame
        """
        if self.selected_features is None:
            raise ValueError("fit()を先に実行してください")
        
        return X[self.selected_features]
    
    def get_ranking(self, top_n=20):
        """
        特徴量の重要度ランキングを取得
        
        Parameters:
        -----------
        top_n : int, default=20
            表示する上位特徴量数
            
        Returns:
        --------
        pd.DataFrame
            上位N件の特徴量ランキング
        """
        return self.feature_ranking.head(top_n)
```

### 7.2 ノイズフィルタリング仕様

#### 7.2.1 競走除外データの処理

```python
# scripts/phase7_feature_selection/noise_filter.py

class NoiseFilter:
    """
    地方競馬データのノイズフィルタリングクラス
    """
    
    @staticmethod
    def filter_race_data(df):
        """
        競走中止・失格・降着データを除外
        
        Parameters:
        -----------
        df : pd.DataFrame
            レース結果データ
            
        Returns:
        --------
        pd.DataFrame
            フィルタリング後のデータ
        """
        print("[Phase 7] Filtering Race Data...")
        original_count = len(df)
        
        # 1. 除外対象の着順を削除
        exclude_values = ['取消', '中止', '除外', '失格']
        df = df[~df['order'].isin(exclude_values)]
        
        # 2. 降着処理（確定着順のみを使用）
        # 例: "4(3)" → "4"
        df['order'] = df['order'].astype(str).str.extract(r'(\d+)')[0]
        df['order'] = pd.to_numeric(df['order'], errors='coerce')
        
        # 3. 数値変換できなかった行を削除
        df = df.dropna(subset=['order'])
        
        filtered_count = len(df)
        removed_count = original_count - filtered_count
        
        print(f"  Original Records: {original_count}")
        print(f"  Removed Records: {removed_count} ({100 * removed_count / original_count:.2f}%)")
        print(f"  Filtered Records: {filtered_count}")
        
        return df
    
    @staticmethod
    def handle_missing_values(df, numeric_cols, categorical_cols):
        """
        欠損値の戦略的処理
        
        Parameters:
        -----------
        df : pd.DataFrame
            データフレーム
        numeric_cols : list
            数値カラムのリスト
        categorical_cols : list
            カテゴリカルカラムのリスト
            
        Returns:
        --------
        pd.DataFrame
            欠損値処理後のデータ
        """
        # カテゴリカル変数: "Unknown"で埋める
        for col in categorical_cols:
            df[col] = df[col].fillna('Unknown')
        
        # 数値変数: LightGBMがネイティブに扱えるのでそのまま
        # （use_missing=Trueで欠損自体が情報となる）
        
        return df
```

### 7.3 統合実行スクリプト

```python
# scripts/phase7_feature_selection/run_feature_selection.py

from greedy_boruta_selector import GreedyBorutaSelector
from noise_filter import NoiseFilter
import pandas as pd

def execute_phase7(input_csv, output_csv, target_col='is_top3'):
    """
    Phase 7を実行: ノイズフィルタリング + Greedy Boruta
    
    Parameters:
    -----------
    input_csv : str
        Phase 1で生成された特徴量CSVのパス
    output_csv : str
        選択された特徴量のみのCSV出力パス
    target_col : str
        ターゲット変数のカラム名
    """
    # 1. データ読み込み
    df = pd.read_csv(input_csv, encoding='utf-8')
    
    # 2. ノイズフィルタリング
    noise_filter = NoiseFilter()
    df = noise_filter.filter_race_data(df)
    
    # 3. 特徴量とターゲットの分離
    X = df.drop(columns=[target_col, 'race_id', 'umaban'], errors='ignore')
    y = df[target_col]
    
    # 4. Greedy Boruta実行
    selector = GreedyBorutaSelector(alpha=0.10, max_iter=200)
    selector.fit(X, y)
    
    # 5. 選択された特徴量のみを抽出
    X_selected = selector.transform(X)
    
    # 6. race_id, umabanを結合して保存
    result = pd.concat([
        df[['race_id', 'umaban']],
        X_selected,
        y
    ], axis=1)
    
    result.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\n[Phase 7] Feature Selection Complete!")
    print(f"  Output: {output_csv}")
    
    # 7. ランキングの表示
    print("\nTop 20 Features:")
    print(selector.get_ranking(top_n=20))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python run_feature_selection.py <input_csv> <output_csv>")
        sys.exit(1)
    
    execute_phase7(sys.argv[1], sys.argv[2])
```

---

## Phase 8: Auto-Optimization

### 概要

**目的**: Optuna 3.x系を用いた段階的ハイパーパラメータ最適化により、LightGBMの性能を極限まで引き出す。

**実装場所**: `scripts/phase8_auto_optimization/`

### 8.1 Optuna LightGBM Tunerの実装

```python
# scripts/phase8_auto_optimization/optuna_tuner.py

import optuna.integration.lightgbm as lgb_optuna
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
import json
import pandas as pd

class OptunaHyperparameterTuner:
    """
    Optunaを用いたLightGBMハイパーパラメータ最適化クラス
    """
    
    def __init__(self, time_budget=7200, n_folds=5):
        """
        Parameters:
        -----------
        time_budget : int, default=7200
            最適化の制限時間（秒）
        n_folds : int, default=5
            Cross-Validationの分割数
        """
        self.time_budget = time_budget
        self.n_folds = n_folds
        self.best_params = None
        self.best_score = None
        
    def optimize(self, X, y, categorical_features=None):
        """
        ハイパーパラメータ最適化を実行
        
        Parameters:
        -----------
        X : pd.DataFrame
            特徴量
        y : pd.Series
            ターゲット
        categorical_features : list, optional
            カテゴリカル変数のリスト
            
        Returns:
        --------
        dict
            最適化されたパラメータ
        """
        print("[Phase 8] Starting Optuna Hyperparameter Optimization...")
        print(f"  Time Budget: {self.time_budget}s ({self.time_budget/3600:.1f}h)")
        
        # データセットの作成
        dtrain = lgb.Dataset(
            X, 
            label=y,
            categorical_feature=categorical_features if categorical_features else 'auto'
        )
        
        # クラス不均衡比率の計算
        neg_count = len(y) - y.sum()
        pos_count = y.sum()
        balance_ratio = neg_count / pos_count
        
        print(f"  Class Imbalance Ratio: {balance_ratio:.2f}")
        
        # 固定パラメータ
        fixed_params = {
            'objective': 'binary',
            'metric': 'auc',
            'verbosity': -1,
            'boosting_type': 'gbdt',
            'n_jobs': -1,
            'learning_rate': 0.05,
            'seed': 42,
            # scale_pos_weightの初期値（平方根で過剰補正を防ぐ）
            'scale_pos_weight': balance_ratio ** 0.5
        }
        
        # Cross-Validationの設定
        folds = StratifiedKFold(
            n_splits=self.n_folds,
            shuffle=True,
            random_state=42
        )
        
        # LightGBMTunerCVの初期化
        tuner = lgb_optuna.LightGBMTunerCV(
            fixed_params,
            dtrain,
            verbose_eval=False,
            early_stopping_rounds=100,
            folds=folds,
            time_budget=self.time_budget,
            optuna_seed=42
        )
        
        # 最適化実行
        tuner.run()
        
        self.best_score = tuner.best_score
        self.best_params = tuner.best_params
        
        print(f"\n[Phase 8] Optimization Complete!")
        print(f"  Best AUC Score: {self.best_score:.4f}")
        print("\nBest Parameters:")
        for key, value in self.best_params.items():
            print(f"  {key}: {value}")
        
        return self.best_params
    
    def save_params(self, output_path='best_params.json'):
        """
        最適パラメータをJSONで保存
        """
        if self.best_params is None:
            raise ValueError("optimize()を先に実行してください")
        
        with open(output_path, 'w') as f:
            json.dump(self.best_params, f, indent=4)
        
        print(f"\n[Phase 8] Parameters saved to: {output_path}")
    
    @staticmethod
    def load_params(params_path='best_params.json'):
        """
        保存されたパラメータを読み込み
        """
        with open(params_path, 'r') as f:
            return json.load(f)
```

### 8.2 パラメータ探索範囲の定義

```python
# Phase 8内部で自動的に探索される範囲（LightGBMTunerCVのデフォルト）

PARAM_SEARCH_SPACE = {
    'num_leaves': (31, 127),           # 木の複雑さ
    'min_child_samples': (20, 100),    # 過学習防止
    'lambda_l1': (1e-8, 10.0),         # L1正則化（Log Uniform）
    'lambda_l2': (1e-8, 10.0),         # L2正則化（Log Uniform）
    'feature_fraction': (0.4, 1.0),    # 特徴量サンプリング率
    'bagging_fraction': (0.4, 1.0),    # データサンプリング率
    'bagging_freq': (1, 7),            # バギング頻度
}
```

### 8.3 実行スクリプト

```python
# scripts/phase8_auto_optimization/run_optimization.py

from optuna_tuner import OptunaHyperparameterTuner
import pandas as pd

def execute_phase8(input_csv, output_params='models/best_params.json'):
    """
    Phase 8を実行: Optunaによる自動最適化
    """
    # データ読み込み（Phase 7の出力）
    df = pd.read_csv(input_csv, encoding='utf-8')
    
    # 特徴量とターゲットの分離
    X = df.drop(columns=['is_top3', 'race_id', 'umaban'], errors='ignore')
    y = df['is_top3']
    
    # Optunaチューナーの初期化
    tuner = OptunaHyperparameterTuner(time_budget=7200, n_folds=5)
    
    # 最適化実行
    best_params = tuner.optimize(X, y)
    
    # パラメータ保存
    tuner.save_params(output_params)
    
    print("\n[Phase 8] Auto-Optimization Complete!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_optimization.py <input_csv>")
        sys.exit(1)
    
    execute_phase8(sys.argv[1])
```

---

## Phase 9: Betting Engine

### 概要

**目的**: 予測確率を期待値に変換し、Kelly基準による資金管理を実装する。

**実装場所**: `scripts/phase9_betting_engine/`

### 9.1 Harvilleの公式実装

```python
# scripts/phase9_betting_engine/harville_calculator.py

from itertools import permutations
import pandas as pd

class HarvilleCalculator:
    """
    Harvilleの公式を用いた複合馬券確率計算クラス
    """
    
    @staticmethod
    def calculate_trifecta_probabilities(win_probs):
        """
        3連単（Trifecta）の確率を計算
        
        Parameters:
        -----------
        win_probs : dict
            {馬番: 勝率} の辞書
            
        Returns:
        --------
        dict
            {(1着, 2着, 3着): 確率} の辞書
        """
        trifecta_probs = {}
        horses = list(win_probs.keys())
        
        for h1, h2, h3 in permutations(horses, 3):
            p1 = win_probs[h1]
            p2 = win_probs[h2]
            p3 = win_probs[h3]
            
            # Harville Formula:
            # P(i,j,k) = p_i × (p_j / (1-p_i)) × (p_k / (1-p_i-p_j))
            
            denom2 = 1.0 - p1
            denom3 = 1.0 - p1 - p2
            
            if denom2 <= 1e-9 or denom3 <= 1e-9:
                prob = 0.0
            else:
                prob = p1 * (p2 / denom2) * (p3 / denom3)
            
            trifecta_probs[(h1, h2, h3)] = prob
        
        return trifecta_probs
    
    @staticmethod
    def calculate_trifecta_box_probabilities(win_probs):
        """
        3連複（Trifecta Box）の確率を計算
        """
        from itertools import combinations
        
        trifecta_box_probs = {}
        horses = list(win_probs.keys())
        
        # 3連単確率を先に計算
        trifecta_probs = HarvilleCalculator.calculate_trifecta_probabilities(win_probs)
        
        # 3頭の組み合わせごとに確率を集計
        for h1, h2, h3 in combinations(horses, 3):
            box_key = tuple(sorted([h1, h2, h3]))
            prob_sum = 0.0
            
            # 6通りの順列の確率を合算
            for perm in permutations([h1, h2, h3], 3):
                prob_sum += trifecta_probs.get(perm, 0.0)
            
            trifecta_box_probs[box_key] = prob_sum
        
        return trifecta_box_probs
```

### 9.2 Kelly基準実装

```python
# scripts/phase9_betting_engine/kelly_optimizer.py

import pandas as pd
import numpy as np

class KellyOptimizer:
    """
    Kelly基準による資金配分最適化クラス
    """
    
    def __init__(self, fractional=0.25, max_bet_ratio=0.05):
        """
        Parameters:
        -----------
        fractional : float, default=0.25
            Fractional Kelly（1/4 Kelly推奨）
        max_bet_ratio : float, default=0.05
            1レースあたりの最大ベット比率（資金の5%）
        """
        self.fractional = fractional
        self.max_bet_ratio = max_bet_ratio
    
    def calculate_kelly_stake(self, prob, odds, bankroll):
        """
        Kelly基準でベット額を計算
        
        Parameters:
        -----------
        prob : float
            的中確率
        odds : float
            オッズ
        bankroll : float
            現在の資金
            
        Returns:
        --------
        int
            推奨ベット額
        """
        b = odds - 1.0  # ネットオッズ
        
        if b <= 0:
            return 0
        
        # Kelly Formula: f* = (bp - q) / b = (prob × odds - 1) / b
        f_star = (prob * odds - 1) / b
        
        if f_star <= 0:
            return 0
        
        # Fractional Kellyの適用
        f_adj = f_star * self.fractional
        
        # 最大ベット比率で制限
        f_final = min(f_adj, self.max_bet_ratio)
        
        # ベット額の計算（100円単位に丸める）
        bet_amount = int(bankroll * f_final / 100) * 100
        
        return max(bet_amount, 0)
    
    def optimize_bets(self, bets_df, bankroll):
        """
        複数の買い目を一括で最適化
        
        Parameters:
        -----------
        bets_df : pd.DataFrame
            カラム: race_id, bet_type, prob, odds
        bankroll : float
            現在の資金
            
        Returns:
        --------
        pd.DataFrame
            bet_amountカラムを追加したDataFrame
        """
        results = []
        
        for _, row in bets_df.iterrows():
            bet_amount = self.calculate_kelly_stake(
                row['prob'],
                row['odds'],
                bankroll
            )
            results.append(bet_amount)
        
        bets_df['bet_amount'] = results
        
        # ベット額が0の行を除外
        return bets_df[bets_df['bet_amount'] > 0]
```

### 9.3 期待値フィルタリング

```python
# scripts/phase9_betting_engine/expected_value_filter.py

class ExpectedValueFilter:
    """
    期待値（EV）に基づいて買い目をフィルタリング
    """
    
    @staticmethod
    def calculate_ev(prob, odds):
        """
        期待値を計算
        
        EV = prob × odds - 1
        
        Parameters:
        -----------
        prob : float
            予測的中確率
        odds : float
            オッズ
            
        Returns:
        --------
        float
            期待値
        """
        return prob * odds - 1
    
    @staticmethod
    def filter_positive_ev(bets_df, min_ev=0.0):
        """
        正の期待値を持つ買い目のみを抽出
        
        Parameters:
        -----------
        bets_df : pd.DataFrame
            カラム: prob, odds
        min_ev : float, default=0.0
            最小期待値の閾値
            
        Returns:
        --------
        pd.DataFrame
            期待値でフィルタリングされたDataFrame
        """
        bets_df['ev'] = ExpectedValueFilter.calculate_ev(
            bets_df['prob'],
            bets_df['odds']
        )
        
        positive_ev_bets = bets_df[bets_df['ev'] > min_ev]
        
        print(f"[Phase 9] EV Filtering:")
        print(f"  Total Bets: {len(bets_df)}")
        print(f"  Positive EV Bets: {len(positive_ev_bets)}")
        print(f"  Average EV: {positive_ev_bets['ev'].mean():.4f}")
        
        return positive_ev_bets
```

### 9.4 統合実行スクリプト

```python
# scripts/phase9_betting_engine/run_betting_engine.py

from harville_calculator import HarvilleCalculator
from kelly_optimizer import KellyOptimizer
from expected_value_filter import ExpectedValueFilter
import pandas as pd

def execute_phase9(predictions_csv, odds_csv, bankroll=100000):
    """
    Phase 9を実行: ベッティングエンジン
    
    Parameters:
    -----------
    predictions_csv : str
        Phase 5のアンサンブル予測結果
    odds_csv : str
        オッズデータ
    bankroll : float
        初期資金
    """
    # データ読み込み
    predictions = pd.read_csv(predictions_csv, encoding='utf-8')
    odds_data = pd.read_csv(odds_csv, encoding='utf-8')
    
    # レースごとに処理
    recommended_bets = []
    
    for race_id in predictions['race_id'].unique():
        race_preds = predictions[predictions['race_id'] == race_id]
        race_odds = odds_data[odds_data['race_id'] == race_id]
        
        # 勝率辞書の作成
        win_probs = dict(zip(race_preds['umaban'], race_preds['win_prob']))
        
        # Harvilleの公式で3連複確率を計算
        harville = HarvilleCalculator()
        trifecta_box_probs = harville.calculate_trifecta_box_probabilities(win_probs)
        
        # オッズと照合
        for combo, prob in trifecta_box_probs.items():
            odds_row = race_odds[
                (race_odds['umaban1'] == combo[0]) &
                (race_odds['umaban2'] == combo[1]) &
                (race_odds['umaban3'] == combo[2])
            ]
            
            if not odds_row.empty:
                odds = odds_row['trifecta_box_odds'].iloc[0]
                
                recommended_bets.append({
                    'race_id': race_id,
                    'bet_type': 'trifecta_box',
                    'combo': combo,
                    'prob': prob,
                    'odds': odds
                })
    
    bets_df = pd.DataFrame(recommended_bets)
    
    # 期待値フィルタリング
    ev_filter = ExpectedValueFilter()
    positive_ev_bets = ev_filter.filter_positive_ev(bets_df, min_ev=0.0)
    
    # Kelly基準で資金配分
    kelly = KellyOptimizer(fractional=0.25, max_bet_ratio=0.05)
    final_bets = kelly.optimize_bets(positive_ev_bets, bankroll)
    
    # 結果保存
    output_path = 'data/betting_recommendations.csv'
    final_bets.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"\n[Phase 9] Betting Engine Complete!")
    print(f"  Recommended Bets: {len(final_bets)}")
    print(f"  Total Investment: ¥{final_bets['bet_amount'].sum():,}")
    print(f"  Output: {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python run_betting_engine.py <predictions_csv> <odds_csv>")
        sys.exit(1)
    
    execute_phase9(sys.argv[1], sys.argv[2])
```

---

## Phase 10: Simulation & Backtest

### 概要

**目的**: 過去データを用いてPhase 7-9の統合システムのROIを検証する。

**実装場所**: `scripts/phase10_backtest/`

### 10.1 バックテストエンジン

```python
# scripts/phase10_backtest/backtest_engine.py

import pandas as pd
import numpy as np

class BacktestEngine:
    """
    バックテストエンジン
    """
    
    def __init__(self, initial_bankroll=100000):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.bet_history = []
        self.bankroll_history = [initial_bankroll]
        
    def execute_backtest(self, bets_df, results_df):
        """
        バックテストを実行
        
        Parameters:
        -----------
        bets_df : pd.DataFrame
            推奨ベット（Phase 9の出力）
        results_df : pd.DataFrame
            実際の結果
        """
        for _, bet in bets_df.iterrows():
            race_id = bet['race_id']
            combo = bet['combo']
            bet_amount = bet['bet_amount']
            odds = bet['odds']
            
            # 結果確認
            result = results_df[results_df['race_id'] == race_id]
            
            if not result.empty:
                actual_combo = tuple(result[['1st', '2nd', '3rd']].iloc[0])
                
                if set(combo) == set(actual_combo):
                    # 的中
                    payout = bet_amount * odds
                    profit = payout - bet_amount
                else:
                    # 外れ
                    profit = -bet_amount
                
                self.current_bankroll += profit
                self.bankroll_history.append(self.current_bankroll)
                
                self.bet_history.append({
                    'race_id': race_id,
                    'bet_amount': bet_amount,
                    'odds': odds,
                    'result': 'HIT' if profit > 0 else 'MISS',
                    'profit': profit,
                    'bankroll': self.current_bankroll
                })
        
        return pd.DataFrame(self.bet_history)
    
    def get_performance_metrics(self):
        """
        パフォーマンス指標を計算
        """
        history_df = pd.DataFrame(self.bet_history)
        
        total_bets = len(history_df)
        hit_bets = len(history_df[history_df['result'] == 'HIT'])
        total_investment = history_df['bet_amount'].sum()
        total_return = history_df[history_df['result'] == 'HIT']['bet_amount'].sum() * \
                       history_df[history_df['result'] == 'HIT']['odds'].mean()
        
        metrics = {
            'ROI': (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll,
            'Hit Rate': hit_bets / total_bets if total_bets > 0 else 0,
            'Total Bets': total_bets,
            'Total Investment': total_investment,
            'Final Bankroll': self.current_bankroll,
            'Max Drawdown': self._calculate_max_drawdown()
        }
        
        return metrics
    
    def _calculate_max_drawdown(self):
        """
        最大ドローダウンを計算
        """
        bankroll_array = np.array(self.bankroll_history)
        running_max = np.maximum.accumulate(bankroll_array)
        drawdown = (running_max - bankroll_array) / running_max
        return drawdown.max()
```

### 10.2 実行スクリプト

```python
# scripts/phase10_backtest/run_backtest.py

from backtest_engine import BacktestEngine
import pandas as pd

def execute_phase10(bets_csv, results_csv):
    """
    Phase 10を実行: バックテスト
    """
    # データ読み込み
    bets = pd.read_csv(bets_csv, encoding='utf-8')
    results = pd.read_csv(results_csv, encoding='utf-8')
    
    # バックテスト実行
    engine = BacktestEngine(initial_bankroll=100000)
    history = engine.execute_backtest(bets, results)
    
    # パフォーマンス指標
    metrics = engine.get_performance_metrics()
    
    print("\n[Phase 10] Backtest Results:")
    print(f"  ROI: {metrics['ROI']*100:.2f}%")
    print(f"  Hit Rate: {metrics['Hit Rate']*100:.2f}%")
    print(f"  Total Bets: {metrics['Total Bets']}")
    print(f"  Final Bankroll: ¥{metrics['Final Bankroll']:,}")
    print(f"  Max Drawdown: {metrics['Max Drawdown']*100:.2f}%")
    
    # 履歴保存
    history.to_csv('data/backtest_history.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python run_backtest.py <bets_csv> <results_csv>")
        sys.exit(1)
    
    execute_phase10(sys.argv[1], sys.argv[2])
```

---

## 統合アーキテクチャ

### データフロー

```
Phase 0: データ取得
    ↓
Phase 1: 特徴量作成
    ↓
[Phase 7: 特徴量選択 (NEW)]
    ↓
[Phase 8: 自動最適化 (NEW)]
    ↓
Phase 3: 二値分類予測
    ↓
Phase 4-1: ランキング予測
    ↓
Phase 4-2: 回帰予測
    ↓
Phase 5: アンサンブル統合
    ↓
[Phase 9: ベッティングエンジン (NEW)]
    ↓
Phase 6: 配信用ファイル生成
    ↓
[Phase 10: バックテスト (NEW)]
```

---

## 実装ガイドライン

### 依存ライブラリのインストール

```bash
pip install greedyboruta optuna lightgbm scikit-learn pandas numpy matplotlib
```

### 実行順序

```bash
# Phase 7: 特徴量選択
python scripts/phase7_feature_selection/run_feature_selection.py \
    data/features/input.csv \
    data/features/selected.csv

# Phase 8: 自動最適化
python scripts/phase8_auto_optimization/run_optimization.py \
    data/features/selected.csv

# Phase 3-5: 既存のパイプライン実行
# ...

# Phase 9: ベッティングエンジン
python scripts/phase9_betting_engine/run_betting_engine.py \
    data/predictions/phase5/ensemble.csv \
    data/odds/odds_data.csv

# Phase 10: バックテスト
python scripts/phase10_backtest/run_backtest.py \
    data/betting_recommendations.csv \
    data/actual_results.csv
```

---

## まとめ

本技術仕様書では、anonymous競馬AIシステムをPhase 7-10で拡張し、**76% → 100%の完成度**へ到達させるための詳細な実装方法を定義した。

### 重要なポイント

1. **Greedy Boruta**: 高速かつ高精度な特徴量選択
2. **Optuna**: 段階的ハイパーパラメータ最適化
3. **Harville + Kelly**: 数学的根拠に基づく資金管理
4. **バックテスト**: 継続的な改善サイクル

---

**最高峰の地方競馬AI予想システムの実現へ！** 🚀
