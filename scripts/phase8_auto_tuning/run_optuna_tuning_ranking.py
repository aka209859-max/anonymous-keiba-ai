#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_optuna_tuning_ranking.py
Phase 8-Ranking: Optunaハイパーパラメータ自動最適化（ランキング専用）

LambdaRankモデルのハイパーパラメータをOptunaで自動最適化します。

最適化戦略:
    1. LambdaRank目的関数（順位学習）
    2. NDCG@5評価指標
    3. GroupKFold Cross-Validation
    4. Boruta選択済み特徴量を使用

使用法:
    python run_optuna_tuning_ranking.py <クリーニング済みCSV> [オプション]
    
オプション:
    --selected-features PATH  Boruta選択済み特徴量CSV
    --n-trials TRIALS         試行回数（デフォルト: 200）
    --timeout SECONDS         タイムアウト秒数（デフォルト: 7200）
    --cv-folds FOLDS          Cross-Validationのfold数（デフォルト: 5）
    
出力:
    - data/models/tuned/{venue}_ranking_tuned_model.txt（最適化モデル）
    - data/models/tuned/{venue}_ranking_best_params.csv（最適パラメータ）
    - data/models/tuned/{venue}_ranking_tuning_history.png（最適化履歴）
    - data/models/tuned/{venue}_ranking_tuning_report.json（詳細レポート）
"""

import sys
import os
import pandas as pd
import numpy as np
import json
import argparse
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import GroupKFold
from sklearn.metrics import ndcg_score
import lightgbm as lgb
import optuna
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Optunaのログを抑制
optuna.logging.set_verbosity(optuna.logging.WARNING)

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False


def load_training_data(csv_file, selected_features_file):
    """
    学習データとBoruta選択済み特徴量を読み込み
    
    Args:
        csv_file: 学習データCSVファイル
        selected_features_file: Boruta選択済み特徴量CSVファイル
    
    Returns:
        tuple: (X, y, groups)
    """
    print("\n" + "=" * 80)
    print("[1/7] 学習データ読み込み中...")
    print("=" * 80)
    print(f"学習データ: {csv_file}")
    print(f"選択済み特徴量: {selected_features_file}")
    
    # 学習データ読み込み
    if not os.path.exists(csv_file):
        print(f"❌ エラー: ファイルが見つかりません - {csv_file}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(csv_file, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_file, encoding='utf-8')
    
    print(f"✅ 学習データ読み込み完了")
    print(f"  - レコード数: {len(df):,}件")
    
    # Boruta選択済み特徴量読み込み
    if os.path.exists(selected_features_file):
        selected_df = pd.read_csv(selected_features_file, encoding='utf-8')
        selected_features = selected_df['feature'].tolist()
        print(f"✅ Boruta選択済み特徴量読み込み完了")
        print(f"  - 選択特徴量数: {len(selected_features)}個")
    else:
        print(f"⚠️  警告: Boruta選択済み特徴量が見つかりません")
        print(f"  全特徴量を使用します")
        
        # 全特徴量を使用
        exclude_columns = [
            'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
            'ketto_toroku_bango', 'umaban', 'kakutei_chakujun', 'race_result',
            'binary_target', 'rank_target', 'target', 'time'
        ]
        selected_features = [col for col in df.columns if col not in exclude_columns]
    
    # 目的変数とrace_idの確認
    if 'rank_target' not in df.columns:
        print(f"❌ エラー: 'rank_target'カラムが見つかりません")
        sys.exit(1)
    
    if 'race_id' not in df.columns:
        print(f"❌ エラー: 'race_id'カラムが見つかりません（ランキング学習に必須）")
        sys.exit(1)
    
    print(f"✅ 目的変数カラム検出: rank_target")
    print(f"✅ グループカラム検出: race_id")
    
    # 特徴量抽出
    X = df[selected_features].copy()
    y = df['rank_target'].copy()
    groups = df['race_id'].copy()
    
    # 欠損値処理
    X.fillna(0, inplace=True)
    
    # カテゴリカル変数を数値化
    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    
    print(f"\n✅ 前処理完了")
    print(f"  - 特徴量数: {len(X.columns)}個")
    print(f"  - サンプル数: {len(X):,}件")
    print(f"  - レース数: {groups.nunique():,}件")
    print(f"  - ターゲット範囲: {y.min():.1f} - {y.max():.1f}")
    
    return X, y, groups, selected_features


def objective(trial, X, y, groups, n_folds=5):
    """
    Optuna最適化の目的関数（ランキング専用）
    
    Args:
        trial: Optunaのトライアル
        X: 特徴量
        y: 目的変数（rank_target）
        groups: レースID
        n_folds: Cross-Validationのfold数
    
    Returns:
        float: 平均NDCG@5スコア
    """
    # ハイパーパラメータの探索空間
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': [5],
        'num_leaves': trial.suggest_int('num_leaves', 20, 100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 15),
        'min_child_samples': trial.suggest_int('min_child_samples', 20, 100),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-6, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-6, 10.0, log=True),
        'verbose': -1,
        'num_threads': -1
    }
    
    # GroupKFoldでCross-Validation
    gkf = GroupKFold(n_splits=n_folds)
    ndcg_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups), 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        groups_train = groups.iloc[train_idx]
        groups_val = groups.iloc[val_idx]
        
        # グループごとのサイズを計算
        train_group_sizes = groups_train.value_counts().sort_index().values
        val_group_sizes = groups_val.value_counts().sort_index().values
        
        # LightGBM Dataset作成
        train_data = lgb.Dataset(
            X_train, 
            label=y_train,
            group=train_group_sizes
        )
        val_data = lgb.Dataset(
            X_val, 
            label=y_val,
            group=val_group_sizes,
            reference=train_data
        )
        
        # 学習
        model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[val_data],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50, verbose=False),
                lgb.log_evaluation(period=0)
            ]
        )
        
        # 予測
        y_pred = model.predict(X_val)
        
        # NDCG@5を計算（レースごと）
        fold_ndcg_scores = []
        for race_id in groups_val.unique():
            race_mask = (groups_val == race_id)
            y_true_race = y_val[race_mask].values
            y_pred_race = y_pred[race_mask]
            
            # NDCG@5を計算（scikit-learn）
            # 注意: y_trueは大きいほど良い（1着=最大値）
            if len(y_true_race) >= 2:
                ndcg = ndcg_score([y_true_race], [y_pred_race], k=5)
                fold_ndcg_scores.append(ndcg)
        
        if fold_ndcg_scores:
            avg_ndcg = np.mean(fold_ndcg_scores)
            ndcg_scores.append(avg_ndcg)
    
    # 平均NDCG@5を返す
    mean_ndcg = np.mean(ndcg_scores) if ndcg_scores else 0.0
    
    return mean_ndcg


def optimize_hyperparameters(X, y, groups, n_trials=200, timeout=7200, n_folds=5):
    """
    Optunaでハイパーパラメータを最適化
    
    Args:
        X: 特徴量
        y: 目的変数
        groups: レースID
        n_trials: 試行回数
        timeout: タイムアウト秒数
        n_folds: Cross-Validationのfold数
    
    Returns:
        dict: 最適パラメータ
    """
    print("\n" + "=" * 80)
    print("[2/7] Optunaハイパーパラメータ最適化開始")
    print("=" * 80)
    print(f"  - 試行回数: {n_trials}")
    print(f"  - タイムアウト: {timeout}秒")
    print(f"  - Cross-Validation: {n_folds}-fold")
    print(f"  - 評価指標: NDCG@5")
    print("=" * 80)
    
    # Optunaスタディ作成
    study = optuna.create_study(
        direction='maximize',  # NDCG@5を最大化
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    
    # 最適化実行
    study.optimize(
        lambda trial: objective(trial, X, y, groups, n_folds),
        n_trials=n_trials,
        timeout=timeout,
        show_progress_bar=True
    )
    
    print("\n✅ 最適化完了")
    print(f"  - 最良NDCG@5: {study.best_value:.4f}")
    print(f"  - 試行回数: {len(study.trials)}")
    
    return study.best_params, study


def train_final_model(X, y, groups, best_params, selected_features):
    """
    最適パラメータで最終モデルを学習
    
    Args:
        X: 特徴量
        y: 目的変数
        groups: レースID
        best_params: 最適パラメータ
        selected_features: 選択済み特徴量リスト
    
    Returns:
        lgb.Booster: 学習済みモデル
    """
    print("\n" + "=" * 80)
    print("[3/7] 最終モデル学習中...")
    print("=" * 80)
    
    # LambdaRankパラメータを追加
    params = best_params.copy()
    params.update({
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': [5],
        'verbose': -1
    })
    
    # グループごとのサイズを計算
    group_sizes = groups.value_counts().sort_index().values
    
    # LightGBM Dataset作成
    train_data = lgb.Dataset(
        X, 
        label=y,
        group=group_sizes,
        feature_name=selected_features
    )
    
    # 学習
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        callbacks=[lgb.log_evaluation(period=100)]
    )
    
    print(f"✅ 最終モデル学習完了")
    print(f"  - 使用ラウンド数: {model.current_iteration()}")
    
    return model


def save_results(model, best_params, study, venue_name, output_dir):
    """
    結果を保存
    
    Args:
        model: 学習済みモデル
        best_params: 最適パラメータ
        study: Optunaスタディ
        venue_name: 競馬場名
        output_dir: 出力ディレクトリ
    """
    print("\n" + "=" * 80)
    print("[4/7] 結果保存中...")
    print("=" * 80)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # モデル保存
    model_path = output_dir / f'{venue_name}_ranking_tuned_model.txt'
    model.save_model(str(model_path))
    print(f"✅ モデル保存: {model_path}")
    
    # パラメータ保存（CSV）
    params_path = output_dir / f'{venue_name}_ranking_best_params.csv'
    params_df = pd.DataFrame([best_params])
    params_df.to_csv(params_path, index=False, encoding='utf-8')
    print(f"✅ パラメータ保存: {params_path}")
    
    # 最適化履歴グラフ
    fig, ax = plt.subplots(figsize=(10, 6))
    trials_df = study.trials_dataframe()
    ax.plot(trials_df['number'], trials_df['value'], marker='o', linestyle='-', alpha=0.7)
    ax.set_xlabel('Trial Number')
    ax.set_ylabel('NDCG@5')
    ax.set_title(f'Optuna Optimization History - {venue_name} (Ranking)')
    ax.grid(True, alpha=0.3)
    
    history_path = output_dir / f'{venue_name}_ranking_tuning_history.png'
    plt.savefig(history_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 履歴グラフ保存: {history_path}")
    
    # 詳細レポート（JSON）
    report = {
        'venue': venue_name,
        'model_type': 'ranking',
        'objective': 'lambdarank',
        'metric': 'ndcg@5',
        'best_ndcg': float(study.best_value),
        'n_trials': len(study.trials),
        'best_params': best_params,
        'cv_folds': 5
    }
    
    report_path = output_dir / f'{venue_name}_ranking_tuning_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✅ レポート保存: {report_path}")


def main():
    parser = argparse.ArgumentParser(description='Phase 8-Ranking: Optunaチューニング')
    parser.add_argument('csv_file', type=str, help='クリーニング済みCSV')
    parser.add_argument('--selected-features', type=str, default='', help='Boruta選択済み特徴量CSV')
    parser.add_argument('--n-trials', type=int, default=200, help='試行回数（デフォルト: 200）')
    parser.add_argument('--timeout', type=int, default=7200, help='タイムアウト秒数（デフォルト: 7200）')
    parser.add_argument('--cv-folds', type=int, default=5, help='Cross-Validationのfold数（デフォルト: 5）')
    
    args = parser.parse_args()
    
    # パス設定
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ エラー: ファイルが見つかりません - {csv_path}")
        sys.exit(1)
    
    # 競馬場名を抽出
    venue_name = csv_path.stem.split('_')[0]
    
    # 選択済み特徴量パスの自動検出
    if args.selected_features:
        selected_features_file = args.selected_features
    else:
        selected_features_file = project_root / 'data' / 'features' / 'selected' / f'{venue_name}_ranking_selected_features.csv'
    
    print("\n" + "=" * 80)
    print("Phase 8-Ranking: Optunaハイパーパラメータ最適化")
    print("=" * 80)
    print(f"入力: {csv_path}")
    print(f"競馬場: {venue_name}")
    print(f"選択済み特徴量: {selected_features_file}")
    print("=" * 80)
    
    # データ読み込み
    X, y, groups, selected_features = load_training_data(csv_path, selected_features_file)
    
    # ハイパーパラメータ最適化
    best_params, study = optimize_hyperparameters(
        X, y, groups,
        n_trials=args.n_trials,
        timeout=args.timeout,
        n_folds=args.cv_folds
    )
    
    # 最終モデル学習
    model = train_final_model(X, y, groups, best_params, selected_features)
    
    # 結果保存
    output_dir = project_root / 'data' / 'models' / 'tuned'
    save_results(model, best_params, study, venue_name, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ Phase 8-Ranking 完了！")
    print("=" * 80)
    print(f"最良NDCG@5: {study.best_value:.4f}")
    print(f"モデル保存先: {output_dir / f'{venue_name}_ranking_tuned_model.txt'}")
    print("\n次のステップ: Phase 8-Regressionの最適化")
    print(f"コマンド: python scripts/phase8_auto_tuning/run_optuna_tuning_regression.py {csv_path}")
    print("=" * 80)


if __name__ == '__main__':
    main()
