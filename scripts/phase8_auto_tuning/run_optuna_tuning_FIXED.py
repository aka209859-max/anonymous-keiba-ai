#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_optuna_tuning.py
Phase 8: Optuna自動チューニング

LightGBM Tunerでハイパーパラメータを自動最適化します。

最適化戦略:
    1. Stepwise Tuning（段階的最適化）
    2. 不均衡データ対策（scale_pos_weight）
    3. Cross-Validation（5-fold）
    4. best_params.csv保存

使用法:
    python run_optuna_tuning.py <選択済み特徴量CSV> [オプション]
    
オプション:
    --n-trials TRIALS      試行回数（デフォルト: 100）
    --timeout SECONDS      タイムアウト秒数（デフォルト: 7200 = 2時間）
    --cv-folds FOLDS       Cross-Validationのfold数（デフォルト: 5）
    
出力:
    - data/models/tuned/{venue}_best_params.csv（最適パラメータ）
    - data/models/tuned/{venue}_tuning_history.png（最適化履歴グラフ）
    - data/models/tuned/{venue}_tuning_report.json（詳細レポート）
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
from sklearn.model_selection import StratifiedKFold
import lightgbm as lgb
import optuna
from optuna.integration import LightGBMTuner

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
        tuple: (X, y)
    """
    print("\n" + "=" * 80)
    print("[1/6] 学習データ読み込み中...")
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
            'binary_target', 'rank_target', 'target'
        ]
        selected_features = [col for col in df.columns if col not in exclude_columns]
    
    # 目的変数カラムを自動検出（'target' または 'binary_target'）
    target_col = None
    if 'target' in df.columns:
        target_col = 'target'
    elif 'binary_target' in df.columns:
        target_col = 'binary_target'
    else:
        print(f"❌ エラー: 目的変数カラムが見つかりません（'target' または 'binary_target' が必要）")
        sys.exit(1)
    
    print(f"✅ 目的変数カラム検出: {target_col}")
    
    # 特徴量抽出
    X = df[selected_features].copy()
    y = df[target_col].copy()
    
    # 欠損値処理
    X.fillna(0, inplace=True)
    
    # カテゴリカル変数を数値化
    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    
    print(f"\n✅ 前処理完了")
    print(f"  - 特徴量数: {len(X.columns)}個")
    print(f"  - サンプル数: {len(X):,}件")
    print(f"  - 正例率: {y.mean() * 100:.2f}%")
    
    return X, y


def calculate_scale_pos_weight(y):
    """
    不均衡データ対策のscale_pos_weightを計算
    
    推奨値: balance_ratioの平方根
    
    Args:
        y: 目的変数
    
    Returns:
        float: scale_pos_weight
    """
    n_pos = (y == 1).sum()
    n_neg = (y == 0).sum()
    
    balance_ratio = n_neg / n_pos
    scale_pos_weight = np.sqrt(balance_ratio)
    
    print(f"\n不均衡データ対策:")
    print(f"  - 正例: {n_pos:,}件 ({n_pos / len(y) * 100:.2f}%)")
    print(f"  - 負例: {n_neg:,}件 ({n_neg / len(y) * 100:.2f}%)")
    print(f"  - balance_ratio: {balance_ratio:.2f}")
    print(f"  - scale_pos_weight: {scale_pos_weight:.2f}")
    
    return scale_pos_weight


def run_optuna_tuning(X, y, n_trials, timeout, cv_folds, scale_pos_weight):
    """
    Optuna + LightGBM Tunerでハイパーパラメータ最適化
    
    Args:
        X: 特徴量DataFrame
        y: 目的変数
        n_trials: 試行回数
        timeout: タイムアウト秒数
        cv_folds: Cross-Validationのfold数
        scale_pos_weight: 不均衡データ対策パラメータ
    
    Returns:
        dict: 最適パラメータ
    """
    print("\n" + "=" * 80)
    print("[2/6] Optuna自動チューニング実行中...")
    print("=" * 80)
    print(f"パラメータ:")
    print(f"  - n_trials: {n_trials}回")
    print(f"  - timeout: {timeout}秒 ({timeout / 60:.1f}分)")
    print(f"  - cv_folds: {cv_folds}fold")
    print(f"  - scale_pos_weight: {scale_pos_weight:.2f}")
    
    # LightGBMデータセット作成
    train_data = lgb.Dataset(X, label=y)
    
    # 固定パラメータ
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'scale_pos_weight': scale_pos_weight,
        'verbose': -1,
        'seed': 42
    }
    
    # Optuna Tuner
    print("\n⏳ 最適化開始...")
    
    tuner = LightGBMTuner(
        params=params,
        train_set=train_data,
        num_boost_round=1000,
        folds=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42),
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
        optuna_seed=42,
        show_progress_bar=True
    )
    
    tuner.run()
    
    # 最適パラメータ取得
    best_params = tuner.best_params
    best_score = tuner.best_score
    
    print(f"\n✅ 最適化完了")
    print(f"  - 最高AUC: {best_score:.4f}")
    print(f"  - 最適パラメータ:")
    for key, value in best_params.items():
        print(f"    - {key}: {value}")
    
    return best_params, best_score


def save_best_params(best_params, best_score, output_csv, output_json):
    """
    最適パラメータを保存
    
    Args:
        best_params: 最適パラメータ
        best_score: 最高スコア
        output_csv: 出力CSVファイル
        output_json: 出力JSONファイル
    """
    print("\n" + "=" * 80)
    print("[3/6] 最適パラメータ保存中...")
    print("=" * 80)
    
    # CSV保存（本番運用で使用）
    params_df = pd.DataFrame([best_params])
    params_df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"✅ CSV保存完了: {output_csv}")
    
    # JSON保存（詳細情報）
    report = {
        'best_params': best_params,
        'best_score': best_score,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON保存完了: {output_json}")


def train_final_model(X, y, best_params, scale_pos_weight):
    """
    最適パラメータで最終モデルを学習
    
    Args:
        X: 特徴量DataFrame
        y: 目的変数
        best_params: 最適パラメータ
        scale_pos_weight: 不均衡データ対策パラメータ
    
    Returns:
        lgb.Booster: 学習済みモデル
    """
    print("\n" + "=" * 80)
    print("[4/6] 最終モデル学習中...")
    print("=" * 80)
    
    # パラメータ統合
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'scale_pos_weight': scale_pos_weight,
        'verbose': -1,
        'seed': 42
    }
    params.update(best_params)
    
    # データセット作成
    train_data = lgb.Dataset(X, label=y)
    
    # 学習
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)]
    )
    
    print(f"✅ 最終モデル学習完了")
    print(f"  - 反復回数: {model.current_iteration()}回")
    print(f"  - 最終AUC: {model.best_score['training']['auc']:.4f}")
    
    return model


def visualize_feature_importance(model, output_file):
    """
    特徴量重要度を可視化
    
    Args:
        model: 学習済みモデル
        output_file: 出力画像ファイル
    """
    print("\n" + "=" * 80)
    print("[5/6] 特徴量重要度可視化中...")
    print("=" * 80)
    
    # 重要度取得
    importance = model.feature_importance(importance_type='gain')
    feature_names = model.feature_name()
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False).head(30)
    
    # グラフ作成
    plt.figure(figsize=(12, 10))
    plt.barh(range(len(importance_df)), importance_df['importance'], color='steelblue')
    plt.yticks(range(len(importance_df)), importance_df['feature'])
    plt.xlabel('Importance (Gain)', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.title('Top 30 Features (Optuna-Tuned Model)', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ グラフ保存完了: {output_file}")
    
    plt.close()


def save_final_model(model, output_file):
    """
    最終モデルを保存
    
    Args:
        model: 学習済みモデル
        output_file: 出力モデルファイル
    """
    print("\n" + "=" * 80)
    print("[6/6] 最終モデル保存中...")
    print("=" * 80)
    
    model.save_model(output_file)
    print(f"✅ モデル保存完了: {output_file}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Phase 8: Optuna自動チューニング',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    # 基本的な使い方
    python run_optuna_tuning.py data/training/cleaned/名古屋_20220101_20251231_cleaned.csv
    
    # 試行回数を増やす
    python run_optuna_tuning.py data/training/cleaned/名古屋_20220101_20251231_cleaned.csv --n-trials 200
    
    # タイムアウトを設定（1時間）
    python run_optuna_tuning.py data/training/cleaned/名古屋_20220101_20251231_cleaned.csv --timeout 3600
        """
    )
    
    parser.add_argument('csv_file', help='学習データCSVファイル')
    parser.add_argument('--n-trials', type=int, default=100, help='試行回数（デフォルト: 100）')
    parser.add_argument('--timeout', type=int, default=7200, help='タイムアウト秒数（デフォルト: 7200秒 = 2時間）')
    parser.add_argument('--cv-folds', type=int, default=5, help='Cross-Validationのfold数（デフォルト: 5）')
    
    args = parser.parse_args()
    
    # パラメータ表示
    print("=" * 80)
    print("Phase 8: Optuna自動チューニング")
    print("=" * 80)
    print(f"学習データ: {args.csv_file}")
    print(f"パラメータ:")
    print(f"  - n_trials: {args.n_trials}回")
    print(f"  - timeout: {args.timeout}秒 ({args.timeout / 60:.1f}分)")
    print(f"  - cv_folds: {args.cv_folds}fold")
    print()
    
    # 出力ファイル名の自動生成
    basename = os.path.basename(args.csv_file)
    venue_name = basename.split('_')[0]
    
    selected_features_file = str(project_root / 'data' / 'features' / 'selected' / f"{venue_name}_selected_features.csv")
    
    output_dir = project_root / 'data' / 'models' / 'tuned'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_params_csv = str(output_dir / f"{venue_name}_best_params.csv")
    output_params_json = str(output_dir / f"{venue_name}_tuning_report.json")
    output_importance_file = str(output_dir / f"{venue_name}_importance.png")
    output_model_file = str(output_dir / f"{venue_name}_tuned_model.txt")
    
    # ============================================
    # Phase 8: Optuna自動チューニング
    # ============================================
    
    # [1/6] データ読み込み
    X, y = load_training_data(args.csv_file, selected_features_file)
    
    # scale_pos_weight計算
    scale_pos_weight = calculate_scale_pos_weight(y)
    
    # [2/6] Optuna最適化
    best_params, best_score = run_optuna_tuning(
        X, y,
        n_trials=args.n_trials,
        timeout=args.timeout,
        cv_folds=args.cv_folds,
        scale_pos_weight=scale_pos_weight
    )
    
    # [3/6] 最適パラメータ保存
    save_best_params(best_params, best_score, output_params_csv, output_params_json)
    
    # [4/6] 最終モデル学習
    model = train_final_model(X, y, best_params, scale_pos_weight)
    
    # [5/6] 特徴量重要度可視化
    visualize_feature_importance(model, output_importance_file)
    
    # [6/6] 最終モデル保存
    save_final_model(model, output_model_file)
    
    # 完了
    print("\n" + "=" * 80)
    print("✅ Phase 8: Optuna自動チューニング完了")
    print("=" * 80)
    print(f"\n最適パラメータ:")
    for key, value in best_params.items():
        print(f"  - {key}: {value}")
    print(f"\n最高AUC: {best_score:.4f}")
    
    print(f"\n次のステップ: Phase 9で期待値ベース購入戦略を実装してください")
    print(f"  python run_betting_strategy.py {output_params_csv}")


if __name__ == '__main__':
    main()
