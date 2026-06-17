#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_optuna_tuning_regression.py
Phase 8-Regression: Optunaによる回帰モデル自動チューニング

走破タイム予測モデルのハイパーパラメータを最適化します。

最適化戦略:
    1. 回帰目的関数（regression）
    2. 評価指標: RMSE（Root Mean Squared Error）
    3. 5-fold Cross-Validation
    4. 段階的パラメータ探索
    
使用法:
    python run_optuna_tuning_regression.py <学習データCSV> [オプション]
    
オプション:
    --selected-features FILE    Phase 7で選択された特徴量CSV
    --n-trials TRIALS          試行回数（デフォルト: 100）
    --timeout SECONDS          タイムアウト秒数（デフォルト: 7200 = 2時間）
    --cv-folds FOLDS           Cross-Validationのfold数（デフォルト: 5）
    
出力:
    - data/models/tuned/{venue}_regression_tuned_model.txt
    - data/models/tuned/{venue}_regression_best_params.csv
    - data/models/tuned/{venue}_regression_tuning_history.png
    - data/models/tuned/{venue}_regression_tuning_report.json
"""

import sys
import os
import pandas as pd
import numpy as np
import json
import argparse
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
import lightgbm as lgb
import optuna

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Optunaのログを抑制
optuna.logging.set_verbosity(optuna.logging.WARNING)

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False


def load_training_data(csv_file, selected_features_file=None):
    """
    学習データとBoruta選択済み特徴量を読み込み
    
    Args:
        csv_file: 学習データCSVファイル
        selected_features_file: Boruta選択済み特徴量CSVファイル（オプション）
    
    Returns:
        tuple: (X, y)
    """
    print("\n" + "=" * 80)
    print("[1/7] 学習データ読み込み中...")
    print("=" * 80)
    print(f"学習データ: {csv_file}")
    if selected_features_file:
        print(f"選択済み特徴量: {selected_features_file}")
    
    # 学習データ読み込み
    if not os.path.exists(csv_file):
        print(f"❌ エラー: ファイルが見つかりません - {csv_file}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(csv_file, encoding='shift-jis')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
        except:
            df = pd.read_csv(csv_file, encoding='cp932')
    
    print(f"✅ 学習データ読み込み完了")
    print(f"  - レコード数: {len(df):,}件")
    
    # Boruta選択済み特徴量読み込み
    if selected_features_file and os.path.exists(selected_features_file):
        selected_df = pd.read_csv(selected_features_file, encoding='utf-8')
        selected_features = selected_df['feature'].tolist()
        print(f"✅ Boruta選択済み特徴量読み込み完了")
        print(f"  - 選択特徴量数: {len(selected_features)}個")
    else:
        if selected_features_file:
            print(f"⚠️  警告: Boruta選択済み特徴量が見つかりません")
        print(f"  全特徴量を使用します")
        
        # 全特徴量を使用
        exclude_columns = [
            'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
            'ketto_toroku_bango', 'umaban', 'kakutei_chakujun', 'race_result',
            'binary_target', 'rank_target', 'target', 'time'
        ]
        selected_features = [col for col in df.columns if col not in exclude_columns]
    
    # 目的変数の確認
    if 'time' not in df.columns:
        print(f"❌ エラー: 'time'カラムが見つかりません")
        print(f"   利用可能なカラム: {df.columns.tolist()}")
        sys.exit(1)
    
    # 特徴量抽出
    X = df[selected_features].copy()
    y = df['time'].copy()
    
    # 欠損値・異常値の除去
    valid_idx = (y > 0) & (y < 10000)  # タイムが正常範囲（1/10秒単位）
    X = X[valid_idx].reset_index(drop=True)
    y = y[valid_idx].reset_index(drop=True)
    
    # 欠損値処理
    X.fillna(0, inplace=True)
    
    # カテゴリカル変数を数値化
    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    
    print(f"\n✅ 前処理完了")
    print(f"  - 特徴量数: {len(X.columns)}個")
    print(f"  - サンプル数: {len(X):,}件")
    print(f"  - time範囲: {y.min():.1f} - {y.max():.1f} (1/10秒)")
    print(f"  - 平均タイム: {y.mean():.1f} (1/10秒)")
    
    return X, y


def run_optuna_tuning(X, y, n_trials, timeout, cv_folds):
    """
    Optunaでハイパーパラメータ最適化（回帰モデル）
    
    Args:
        X: 特徴量DataFrame
        y: 目的変数（time）
        n_trials: 試行回数
        timeout: タイムアウト秒数
        cv_folds: Cross-Validationのfold数
    
    Returns:
        dict: 最適パラメータ
    """
    print("\n" + "=" * 80)
    print("[2/7] Optuna自動チューニング実行中（回帰モデル）...")
    print("=" * 80)
    print(f"パラメータ:")
    print(f"  - n_trials: {n_trials}回")
    print(f"  - timeout: {timeout}秒 ({timeout / 60:.1f}分)")
    print(f"  - cv_folds: {cv_folds}fold")
    print(f"  - 評価指標: RMSE")
    
    # KFold
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    # Optuna目的関数
    def objective(trial):
        # ハイパーパラメータのサンプリング
        param = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'verbosity': -1,
            'seed': 42,
            'num_threads': -1,
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'num_leaves': trial.suggest_int('num_leaves', 20, 200),
            'max_depth': trial.suggest_int('max_depth', 3, 15),
            'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        }
        
        # Cross-Validation
        rmse_scores = []
        
        for fold_idx, (train_idx, val_idx) in enumerate(kf.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # LightGBM Dataset作成
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            # 学習
            model = lgb.train(
                param,
                train_data,
                num_boost_round=1000,
                valid_sets=[val_data],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=50, verbose=False),
                    lgb.log_evaluation(period=0)
                ]
            )
            
            # RMSEを取得
            rmse = model.best_score['valid_0']['rmse']
            rmse_scores.append(rmse)
        
        # 平均RMSEを返す（最小化）
        mean_rmse = np.mean(rmse_scores)
        return mean_rmse
    
    # Optuna Study作成
    study = optuna.create_study(
        direction='minimize',  # RMSEを最小化
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    
    # 最適化実行
    study.optimize(
        objective,
        n_trials=n_trials,
        timeout=timeout,
        show_progress_bar=True
    )
    
    print("\n✅ Optuna最適化完了")
    print(f"  - 最良RMSE: {study.best_value:.4f}")
    print(f"  - 最良パラメータ:")
    for key, value in study.best_params.items():
        print(f"    - {key}: {value}")
    
    return study.best_params, study


def train_final_model(X, y, best_params):
    """
    最適パラメータで最終モデルを学習
    
    Args:
        X: 特徴量DataFrame
        y: 目的変数（time）
        best_params: Optunaで見つけた最適パラメータ
    
    Returns:
        lgb.Booster: 学習済みモデル
    """
    print("\n" + "=" * 80)
    print("[3/7] 最適パラメータで最終モデル学習中...")
    print("=" * 80)
    
    # パラメータ設定
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'verbosity': -1,
        'seed': 42,
        'num_threads': -1,
    }
    params.update(best_params)
    
    # 訓練・検証分割
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Dataset作成
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    # 学習
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50, verbose=False),
            lgb.log_evaluation(period=100)
        ]
    )
    
    # 予測
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)
    
    # 評価
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
    train_mae = mean_absolute_error(y_train, y_pred_train)
    val_mae = mean_absolute_error(y_val, y_pred_val)
    
    print(f"\n✅ 最終モデル学習完了")
    print(f"  - Best iteration: {model.best_iteration}")
    print(f"  - Train RMSE: {train_rmse:.4f}")
    print(f"  - Valid RMSE: {val_rmse:.4f}")
    print(f"  - Train MAE: {train_mae:.4f}")
    print(f"  - Valid MAE: {val_mae:.4f}")
    
    return model


def save_results(model, best_params, study, venue_name, output_dir):
    """
    結果を保存
    
    Args:
        model: 学習済みモデル
        best_params: 最適パラメータ
        study: Optuna Study
        venue_name: 競馬場名
        output_dir: 出力ディレクトリ
    """
    print("\n" + "=" * 80)
    print("[4/7] 結果保存中...")
    print("=" * 80)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. モデル保存
    model_path = output_dir / f'{venue_name}_regression_tuned_model.txt'
    model.save_model(str(model_path))
    print(f"✅ モデル保存: {model_path}")
    
    # 2. 最適パラメータをCSV保存
    params_df = pd.DataFrame([best_params])
    params_csv = output_dir / f'{venue_name}_regression_best_params.csv'
    params_df.to_csv(params_csv, index=False, encoding='utf-8')
    print(f"✅ パラメータ保存: {params_csv}")
    
    # 3. 最適化履歴をグラフ化
    history_png = output_dir / f'{venue_name}_regression_tuning_history.png'
    
    fig, ax = plt.subplots(figsize=(10, 6))
    trials_df = study.trials_dataframe()
    ax.plot(trials_df['number'], trials_df['value'], marker='o', linestyle='-', alpha=0.7)
    ax.axhline(y=study.best_value, color='r', linestyle='--', label=f'Best RMSE: {study.best_value:.4f}')
    ax.set_xlabel('Trial')
    ax.set_ylabel('RMSE')
    ax.set_title(f'{venue_name.upper()} - Regression Model Optimization')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(history_png, dpi=150)
    plt.close()
    print(f"✅ 最適化履歴グラフ保存: {history_png}")
    
    # 4. 詳細レポート保存
    report = {
        'venue': venue_name,
        'model_type': 'regression',
        'objective': 'regression',
        'metric': 'rmse',
        'best_rmse': float(study.best_value),
        'best_params': best_params,
        'n_trials': len(study.trials),
        'best_iteration': int(model.best_iteration),
        'train_rmse': float(model.best_score['training']['rmse']),
        'valid_rmse': float(model.best_score['valid_1']['rmse'])
    }
    
    report_json = output_dir / f'{venue_name}_regression_tuning_report.json'
    with open(report_json, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✅ レポート保存: {report_json}")


def main():
    parser = argparse.ArgumentParser(description='Phase 8-Regression: Optunaハイパーパラメータ最適化')
    parser.add_argument('csv_file', type=str, help='学習データCSV')
    parser.add_argument('--selected-features', type=str, default=None, 
                       help='Phase 7で選択された特徴量CSV（オプション）')
    parser.add_argument('--n-trials', type=int, default=100, help='試行回数（デフォルト: 100）')
    parser.add_argument('--timeout', type=int, default=7200, help='タイムアウト秒数（デフォルト: 7200）')
    parser.add_argument('--cv-folds', type=int, default=5, help='CV fold数（デフォルト: 5）')
    
    args = parser.parse_args()
    
    # パス設定
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ エラー: ファイルが見つかりません - {csv_path}")
        sys.exit(1)
    
    # 競馬場名を抽出
    venue_name = csv_path.stem.split('_')[0]
    
    print("\n" + "=" * 80)
    print("Phase 8-Regression: Optunaハイパーパラメータ最適化")
    print("=" * 80)
    print(f"入力: {csv_path}")
    print(f"競馬場: {venue_name}")
    print(f"目的: 回帰モデル（タイム予測）の最適化")
    print(f"評価指標: RMSE")
    print("=" * 80)
    
    # [1/7] データ読み込み
    X, y = load_training_data(csv_path, args.selected_features)
    
    # [2/7] Optuna最適化
    best_params, study = run_optuna_tuning(X, y, args.n_trials, args.timeout, args.cv_folds)
    
    # [3/7] 最終モデル学習
    model = train_final_model(X, y, best_params)
    
    # [4/7] 結果保存
    output_dir = project_root / 'data' / 'models' / 'tuned'
    save_results(model, best_params, study, venue_name, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ Phase 8-Regression 完了！")
    print("=" * 80)
    print(f"出力ファイル:")
    print(f"  - {output_dir / f'{venue_name}_regression_tuned_model.txt'}")
    print(f"  - {output_dir / f'{venue_name}_regression_best_params.csv'}")
    print(f"  - {output_dir / f'{venue_name}_regression_tuning_history.png'}")
    print(f"  - {output_dir / f'{venue_name}_regression_tuning_report.json'}")
    print("=" * 80)
    print(f"次のステップ: Phase 5でアンサンブル統合")
    print(f"コマンド: python scripts/phase5_ensemble/ensemble_optimized.py \\")
    print(f"          --venue {venue_name} --date 2026-02-11")
    print("=" * 80)


if __name__ == '__main__':
    main()
