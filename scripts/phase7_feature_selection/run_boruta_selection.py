#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_boruta_selection.py
Phase 7-2: Boruta特徴量選択

Greedy Borutaアルゴリズムで重要な特徴量のみを選択し、
ノイズを除去して過学習を抑制します。

アルゴリズム:
    1. シャドウ特徴量生成（各特徴量をランダムシャッフル）
    2. LightGBMで重要度計算
    3. Binomial分布で統計的検定
    4. 有意な特徴量のみを採用

使用法:
    python run_boruta_selection.py <クリーニング済みCSV> [オプション]
    
オプション:
    --alpha ALPHA           有意水準（デフォルト: 0.1）
    --max-iter ITER         最大反復回数（デフォルト: 200）
    --two-step              2段階選択を有効化
    --force-keep FEATURES   強制保持する特徴量（カンマ区切り）
    
出力:
    - data/features/selected/{venue}_selected_features.csv（選択された特徴量リスト）
    - data/features/selected/{venue}_importance.png（特徴量重要度グラフ）
    - data/features/selected/{venue}_boruta_report.json（詳細レポート）
"""

import sys
import os
import pandas as pd
import numpy as np
import json
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.model_selection import train_test_split
import lightgbm as lgb

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False


class GreedyBoruta:
    """
    Greedy Borutaアルゴリズム実装
    
    参考: PC-KEIBA標準仕様書
    """
    
    def __init__(self, alpha=0.1, max_iter=200, two_step=False, force_keep=None):
        """
        Args:
            alpha: 有意水準（小さいほど厳しい選択）
            max_iter: 最大反復回数
            two_step: 2段階選択の有効化
            force_keep: 強制保持する特徴量リスト
        """
        self.alpha = alpha
        self.max_iter = max_iter
        self.two_step = two_step
        self.force_keep = force_keep if force_keep is not None else []
        
        self.selected_features = []
        self.feature_importance = {}
        self.shadow_importance = {}
        self.history = []
    
    
    def _create_shadow_features(self, X):
        """
        シャドウ特徴量を生成
        
        各特徴量をランダムシャッフルして、ノイズの重要度を測定
        
        Args:
            X: 特徴量DataFrame
        
        Returns:
            pd.DataFrame: シャドウ特徴量
        """
        shadow_X = X.copy()
        
        # 各カラムをランダムシャッフル
        for col in shadow_X.columns:
            shadow_X[col] = np.random.permutation(shadow_X[col].values)
        
        # カラム名に "shadow_" プレフィックスを追加
        shadow_X.columns = ['shadow_' + col for col in shadow_X.columns]
        
        return shadow_X
    
    
    def _fit_lightgbm(self, X, y):
        """
        LightGBMで特徴量重要度を計算
        
        Args:
            X: 特徴量DataFrame
            y: 目的変数
        
        Returns:
            dict: 特徴量重要度
        """
        # LightGBMデータセット作成
        train_data = lgb.Dataset(X, label=y)
        
        # パラメータ
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'seed': 42
        }
        
        # 学習
        model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[train_data],
            callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
        )
        
        # 特徴量重要度取得
        importance = dict(zip(X.columns, model.feature_importance(importance_type='gain')))
        
        return importance
    
    
    def _binomial_test(self, real_importance, shadow_max):
        """
        Binomial分布で統計的検定
        
        実際の特徴量重要度がシャドウの最大値より有意に高いか判定
        
        Args:
            real_importance: 実際の特徴量重要度
            shadow_max: シャドウ特徴量の最大重要度
        
        Returns:
            bool: 有意かどうか
        """
        from scipy.stats import binom
        
        # シャドウより高い回数をカウント
        n_trials = len(self.history)
        n_success = sum(1 for h in self.history if h.get('importance', 0) > shadow_max)
        
        # Binomial検定
        p_value = 1 - binom.cdf(n_success - 1, n_trials, 0.5)
        
        return p_value < self.alpha
    
    
    def fit(self, X, y):
        """
        Boruta特徴量選択を実行
        
        Args:
            X: 特徴量DataFrame
            y: 目的変数
        
        Returns:
            list: 選択された特徴量リスト
        """
        print("\n" + "=" * 80)
        print("Greedy Boruta特徴量選択")
        print("=" * 80)
        print(f"パラメータ:")
        print(f"  - alpha: {self.alpha}")
        print(f"  - max_iter: {self.max_iter}")
        print(f"  - two_step: {self.two_step}")
        print(f"  - force_keep: {len(self.force_keep)}個")
        print(f"\n開始特徴量数: {len(X.columns)}個")
        
        # 強制保持の確認
        for feature in self.force_keep:
            if feature not in X.columns:
                print(f"⚠️  警告: 強制保持特徴量が見つかりません - {feature}")
        
        # 反復処理
        for iteration in range(1, self.max_iter + 1):
            print(f"\n[反復 {iteration}/{self.max_iter}]")
            
            # シャドウ特徴量生成
            shadow_X = self._create_shadow_features(X)
            
            # 結合
            X_combined = pd.concat([X, shadow_X], axis=1)
            
            # LightGBMで重要度計算
            importance = self._fit_lightgbm(X_combined, y)
            
            # 実特徴量とシャドウを分離
            real_features = {k: v for k, v in importance.items() if not k.startswith('shadow_')}
            shadow_features = {k: v for k, v in importance.items() if k.startswith('shadow_')}
            
            # シャドウの最大重要度
            shadow_max = max(shadow_features.values()) if shadow_features else 0
            
            # 統計情報記録
            self.history.append({
                'iteration': iteration,
                'shadow_max': shadow_max,
                'real_mean': np.mean(list(real_features.values())),
                'selected_count': len(self.selected_features)
            })
            
            # 有意な特徴量を選択
            newly_selected = []
            for feature, imp in real_features.items():
                if feature in self.force_keep:
                    # 強制保持
                    if feature not in self.selected_features:
                        self.selected_features.append(feature)
                        newly_selected.append(feature)
                elif imp > shadow_max:
                    if feature not in self.selected_features:
                        self.selected_features.append(feature)
                        self.feature_importance[feature] = imp
                        newly_selected.append(feature)
            
            print(f"  - シャドウ最大重要度: {shadow_max:.2f}")
            print(f"  - 新規選択: {len(newly_selected)}個")
            print(f"  - 累計選択: {len(self.selected_features)}個")
            
            # 収束判定
            if iteration > 10 and len(newly_selected) == 0:
                print(f"\n✅ 収束しました（反復 {iteration}回）")
                break
        
        print(f"\n" + "=" * 80)
        print(f"✅ Boruta特徴量選択完了")
        print(f"=" * 80)
        print(f"最終選択特徴量数: {len(self.selected_features)} / {len(X.columns)}個")
        print(f"削減率: {(1 - len(self.selected_features) / len(X.columns)) * 100:.1f}%")
        
        return self.selected_features
    
    
    def get_importance_dataframe(self):
        """
        特徴量重要度をDataFrameで取得
        
        Returns:
            pd.DataFrame: 特徴量重要度
        """
        importance_df = pd.DataFrame([
            {'feature': feature, 'importance': importance}
            for feature, importance in self.feature_importance.items()
        ])
        
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        return importance_df


def load_training_data(csv_file):
    """
    クリーニング済み学習データを読み込み
    
    Args:
        csv_file: CSVファイルパス
    
    Returns:
        tuple: (X, y, df)
    """
    print("\n" + "=" * 80)
    print("[1/5] クリーニング済みデータ読み込み中...")
    print("=" * 80)
    print(f"ファイル: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"❌ エラー: ファイルが見つかりません - {csv_file}")
        sys.exit(1)
    
    # CSV読み込み
    try:
        df = pd.read_csv(csv_file, encoding='shift-jis')
        print("✅ エンコーディング: Shift-JIS")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_file, encoding='utf-8')
        print("✅ エンコーディング: UTF-8")
    
    print(f"✅ データ読み込み完了")
    print(f"  - レコード数: {len(df):,}件")
    print(f"  - カラム数: {len(df.columns)}個")
    
    # 特徴量と目的変数を分離
    exclude_columns = [
        'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
        'ketto_toroku_bango', 'umaban', 'kakutei_chakujun', 'race_result',
        'binary_target', 'rank_target'
    ]
    
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    
    X = df[feature_columns].copy()
    y = df['binary_target'].copy()
    
    # 欠損値を0で埋める
    X.fillna(0, inplace=True)
    
    # カテゴリカル変数を数値化
    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    
    print(f"\n✅ 前処理完了")
    print(f"  - 特徴量数: {len(X.columns)}個")
    print(f"  - サンプル数: {len(X):,}件")
    print(f"  - 正例率: {y.mean() * 100:.2f}%")
    
    return X, y, df


def run_boruta(X, y, alpha, max_iter, two_step, force_keep):
    """
    Boruta特徴量選択を実行
    
    Args:
        X: 特徴量DataFrame
        y: 目的変数
        alpha: 有意水準
        max_iter: 最大反復回数
        two_step: 2段階選択
        force_keep: 強制保持特徴量
    
    Returns:
        GreedyBoruta: 選択器
    """
    print("\n" + "=" * 80)
    print("[2/5] Boruta特徴量選択実行中...")
    print("=" * 80)
    
    # Borutaインスタンス作成
    boruta = GreedyBoruta(
        alpha=alpha,
        max_iter=max_iter,
        two_step=two_step,
        force_keep=force_keep
    )
    
    # 特徴量選択実行
    selected_features = boruta.fit(X, y)
    
    return boruta


def visualize_importance(boruta, output_file):
    """
    特徴量重要度を可視化
    
    Args:
        boruta: GreedyBorutaインスタンス
        output_file: 出力画像ファイル
    """
    print("\n" + "=" * 80)
    print("[3/5] 特徴量重要度可視化中...")
    print("=" * 80)
    
    # 重要度DataFrame取得
    importance_df = boruta.get_importance_dataframe()
    
    # 上位30個のみ表示
    top_features = importance_df.head(30)
    
    # グラフ作成
    plt.figure(figsize=(12, 10))
    
    # 横棒グラフ
    plt.barh(range(len(top_features)), top_features['importance'], color='steelblue')
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importance (Gain)', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.title(f'Top {len(top_features)} Selected Features (Boruta)', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    
    # 保存
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ グラフ保存完了: {output_file}")
    
    plt.close()


def save_results(boruta, output_features_file, output_report_file):
    """
    結果を保存
    
    Args:
        boruta: GreedyBorutaインスタンス
        output_features_file: 選択特徴量CSVファイル
        output_report_file: 詳細レポートJSONファイル
    """
    print("\n" + "=" * 80)
    print("[4/5] 結果保存中...")
    print("=" * 80)
    
    # 選択特徴量CSV
    selected_df = boruta.get_importance_dataframe()
    selected_df.to_csv(output_features_file, index=False, encoding='utf-8')
    print(f"✅ 選択特徴量保存完了: {output_features_file}")
    
    # 詳細レポートJSON
    report = {
        'selected_features': boruta.selected_features,
        'feature_importance': boruta.feature_importance,
        'parameters': {
            'alpha': boruta.alpha,
            'max_iter': boruta.max_iter,
            'two_step': boruta.two_step,
            'force_keep': boruta.force_keep
        },
        'statistics': {
            'total_features': len(boruta.feature_importance) + len(boruta.force_keep),
            'selected_features': len(boruta.selected_features),
            'reduction_rate': 1 - len(boruta.selected_features) / (len(boruta.feature_importance) + len(boruta.force_keep))
        }
    }
    
    with open(output_report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✅ レポート保存完了: {output_report_file}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Phase 7-2: Boruta特徴量選択',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    # 基本的な使い方
    python run_boruta_selection.py data/training/cleaned/名古屋_20220101_20251231_cleaned.csv
    
    # パラメータ調整
    python run_boruta_selection.py data/training/cleaned/名古屋_20220101_20251231_cleaned.csv --alpha 0.15 --max-iter 300
    
    # 強制保持特徴量を指定
    python run_boruta_selection.py data/training/cleaned/名古屋_20220101_20251231_cleaned.csv --force-keep "kishu_code,prev1_rank,prev2_rank"
        """
    )
    
    parser.add_argument('csv_file', help='クリーニング済みCSVファイル')
    parser.add_argument('--alpha', type=float, default=0.1, help='有意水準（デフォルト: 0.1）')
    parser.add_argument('--max-iter', type=int, default=200, help='最大反復回数（デフォルト: 200）')
    parser.add_argument('--two-step', action='store_true', help='2段階選択を有効化')
    parser.add_argument('--force-keep', type=str, default='', help='強制保持特徴量（カンマ区切り）')
    
    args = parser.parse_args()
    
    # 強制保持特徴量をリスト化
    force_keep = [f.strip() for f in args.force_keep.split(',') if f.strip()]
    
    # パラメータ表示
    print("=" * 80)
    print("Phase 7-2: Boruta特徴量選択")
    print("=" * 80)
    print(f"入力ファイル: {args.csv_file}")
    print(f"パラメータ:")
    print(f"  - alpha: {args.alpha}")
    print(f"  - max_iter: {args.max_iter}")
    print(f"  - two_step: {args.two_step}")
    print(f"  - force_keep: {len(force_keep)}個")
    print()
    
    # 出力ファイル名の自動生成
    basename = os.path.basename(args.csv_file)
    venue_name = basename.split('_')[0]
    
    output_dir = project_root / 'data' / 'features' / 'selected'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_features_file = str(output_dir / f"{venue_name}_selected_features.csv")
    output_importance_file = str(output_dir / f"{venue_name}_importance.png")
    output_report_file = str(output_dir / f"{venue_name}_boruta_report.json")
    
    # ============================================
    # Phase 7-2: Boruta特徴量選択
    # ============================================
    
    # [1/5] データ読み込み
    X, y, df = load_training_data(args.csv_file)
    
    # [2/5] Boruta実行
    boruta = run_boruta(X, y, args.alpha, args.max_iter, args.two_step, force_keep)
    
    # [3/5] 可視化
    visualize_importance(boruta, output_importance_file)
    
    # [4/5] 結果保存
    save_results(boruta, output_features_file, output_report_file)
    
    # [5/5] サマリー表示
    print("\n" + "=" * 80)
    print("✅ Phase 7-2: Boruta特徴量選択完了")
    print("=" * 80)
    print(f"\n選択された特徴量トップ10:")
    importance_df = boruta.get_importance_dataframe()
    for i, row in importance_df.head(10).iterrows():
        print(f"  {i+1}. {row['feature']}: {row['importance']:.2f}")
    
    print(f"\n次のステップ: Phase 8でOptuna自動チューニングを実行してください")
    print(f"  python run_optuna_tuning.py {output_features_file}")


if __name__ == '__main__':
    main()
