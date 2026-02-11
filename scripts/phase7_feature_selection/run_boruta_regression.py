#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_boruta_regression.py
Phase 7-Regression: 回帰モデル用Boruta特徴量選択

走破タイム予測モデルに最適な特徴量を選択します。

目的変数:
    - time（走破タイム、1/10秒単位）

評価指標:
    - RMSE（Root Mean Squared Error）
    - MAE（Mean Absolute Error）

使用法:
    python run_boruta_regression.py <クリーニング済みCSV> [オプション]
    
オプション:
    --alpha ALPHA           有意水準（デフォルト: 0.1）
    --max-iter ITER         最大反復回数（デフォルト: 200）
    --force-keep FEATURES   強制保持する特徴量（カンマ区切り）
    
出力:
    - data/features/selected/{venue}_regression_selected_features.csv
    - data/features/selected/{venue}_regression_importance.png
    - data/features/selected/{venue}_regression_boruta_report.json
"""

import sys
import os
import pandas as pd
import numpy as np
import json
import argparse
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import lightgbm as lgb

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False


class GreedyBorutaRegression:
    """
    回帰モデル専用Greedy Borutaアルゴリズム実装
    
    タイム予測に最適な特徴量を選択
    """
    
    def __init__(self, alpha=0.1, max_iter=200, force_keep=None):
        self.alpha = alpha
        self.max_iter = max_iter
        self.force_keep = force_keep if force_keep is not None else []
        
        self.selected_features = []
        self.feature_importance = {}
        self.history = []
    
    
    def _create_shadow_features(self, X):
        """シャドウ特徴量を生成"""
        shadow_X = X.copy()
        
        for col in shadow_X.columns:
            shadow_X[col] = np.random.permutation(shadow_X[col].values)
        
        shadow_X.columns = ['shadow_' + col for col in shadow_X.columns]
        
        return shadow_X
    
    
    def _train_regression_model(self, X, y):
        """
        回帰モデルを学習（タイム予測）
        
        Args:
            X: 特徴量（シャドウ含む）
            y: 目的変数（走破タイム、1/10秒単位）
        """
        # 訓練・検証分割
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # 回帰パラメータ
        params = {
            'objective': 'regression',  # ← 回帰学習
            'metric': 'rmse',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'num_threads': -1
        }
        
        # LightGBM Dataset作成
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        # 学習
        model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
        )
        
        # 特徴量重要度を取得
        importances = model.feature_importance(importance_type='gain')
        
        return dict(zip(X.columns, importances))
    
    
    def fit(self, X, y):
        """
        Boruta特徴量選択を実行
        
        Args:
            X: 特徴量DataFrame
            y: 目的変数（time: 走破タイム）
        
        Returns:
            list: 選択された特徴量リスト
        """
        print("\n" + "=" * 80)
        print("Greedy Boruta特徴量選択（回帰モデル専用）")
        print("=" * 80)
        print(f"  - 初期特徴量数: {len(X.columns)}個")
        print(f"  - 有意水準: {self.alpha}")
        print(f"  - 最大反復回数: {self.max_iter}")
        print(f"  - 評価指標: RMSE（走破タイム予測）")
        print("=" * 80)
        
        tentative_features = list(X.columns)
        rejected_features = []
        
        for iteration in range(self.max_iter):
            print(f"\n[反復 {iteration + 1}/{self.max_iter}]")
            
            if len(tentative_features) == 0:
                print("  - 全ての特徴量が決定しました")
                break
            
            # 現在の特徴量
            X_current = X[tentative_features].copy()
            
            # シャドウ特徴量を生成
            shadow_X = self._create_shadow_features(X_current)
            
            # 結合
            X_with_shadow = pd.concat([X_current, shadow_X], axis=1)
            
            # 回帰モデルで重要度を計算
            importances = self._train_regression_model(X_with_shadow, y)
            
            # シャドウの最大重要度
            shadow_importances = [imp for feat, imp in importances.items() if feat.startswith('shadow_')]
            shadow_max = max(shadow_importances) if shadow_importances else 0
            
            # 統計的検定
            confirmed = []
            rejected = []
            
            for feature in tentative_features:
                real_importance = importances.get(feature, 0)
                
                # シャドウより明らかに重要
                if real_importance > shadow_max * (1 + self.alpha):
                    confirmed.append(feature)
                # シャドウと同等以下
                elif real_importance < shadow_max * (1 - self.alpha):
                    rejected.append(feature)
            
            # 選択・除外の更新
            self.selected_features.extend(confirmed)
            rejected_features.extend(rejected)
            
            # tentativeから除去
            for feat in confirmed + rejected:
                if feat in tentative_features:
                    tentative_features.remove(feat)
            
            print(f"  - 選択: {len(confirmed)}個")
            print(f"  - 除外: {len(rejected)}個")
            print(f"  - 保留: {len(tentative_features)}個")
            
            # 履歴記録
            self.history.append({
                'iteration': iteration + 1,
                'confirmed': len(confirmed),
                'rejected': len(rejected),
                'tentative': len(tentative_features),
                'shadow_max': float(shadow_max)
            })
            
            # 収束判定
            if len(confirmed) == 0 and len(rejected) == 0:
                print("  - 収束しました（変化なし）")
                break
        
        # 保留されたものは除外
        rejected_features.extend(tentative_features)
        
        # 強制保持
        for feat in self.force_keep:
            if feat in rejected_features:
                rejected_features.remove(feat)
                self.selected_features.append(feat)
        
        # 重複除去
        self.selected_features = list(set(self.selected_features))
        
        print("\n" + "=" * 80)
        print("Boruta選択完了")
        print("=" * 80)
        print(f"  - 選択された特徴量: {len(self.selected_features)}個")
        print(f"  - 除外された特徴量: {len(rejected_features)}個")
        print("=" * 80)
        
        return self.selected_features


def main():
    parser = argparse.ArgumentParser(description='Phase 7-Regression: Boruta特徴量選択')
    parser.add_argument('csv_file', type=str, help='クリーニング済みCSV')
    parser.add_argument('--alpha', type=float, default=0.1, help='有意水準（デフォルト: 0.1）')
    parser.add_argument('--max-iter', type=int, default=200, help='最大反復回数（デフォルト: 200）')
    parser.add_argument('--force-keep', type=str, default='', help='強制保持する特徴量（カンマ区切り）')
    
    args = parser.parse_args()
    
    # パス設定
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ エラー: ファイルが見つかりません - {csv_path}")
        sys.exit(1)
    
    # 競馬場名を抽出
    venue_name = csv_path.stem.split('_')[0]
    
    print("\n" + "=" * 80)
    print("Phase 7-Regression: Boruta特徴量選択")
    print("=" * 80)
    print(f"入力: {csv_path}")
    print(f"競馬場: {venue_name}")
    print("=" * 80)
    
    # データ読み込み
    try:
        df = pd.read_csv(csv_path, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='utf-8')
    
    print(f"  - レコード数: {len(df):,}件")
    print(f"  - カラム数: {len(df.columns)}個")
    
    # 目的変数の確認
    if 'time' not in df.columns:
        print(f"❌ エラー: 'time'カラムが見つかりません")
        print(f"   利用可能なカラム: {df.columns.tolist()}")
        sys.exit(1)
    
    # 特徴量抽出
    exclude_cols = [
        'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
        'ketto_toroku_bango', 'umaban', 'kakutei_chakujun', 'race_result',
        'binary_target', 'rank_target', 'target', 'time'
    ]
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].copy()
    y = df['time'].copy()
    
    # 欠損値・異常値の除去
    valid_idx = (y > 0) & (y < 10000)  # タイムが正常範囲
    X = X[valid_idx].reset_index(drop=True)
    y = y[valid_idx].reset_index(drop=True)
    
    # 欠損値処理
    X.fillna(0, inplace=True)
    
    # カテゴリカル変数を数値化
    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    
    print(f"\n特徴量準備完了:")
    print(f"  - 特徴量数: {len(X.columns)}個")
    print(f"  - サンプル数: {len(X):,}件")
    print(f"  - 目的変数: time（範囲: {y.min():.1f} - {y.max():.1f}）")
    print(f"  - 平均タイム: {y.mean():.1f} (1/10秒)")
    
    # 強制保持する特徴量
    force_keep = args.force_keep.split(',') if args.force_keep else []
    
    # Boruta実行
    boruta = GreedyBorutaRegression(
        alpha=args.alpha,
        max_iter=args.max_iter,
        force_keep=force_keep
    )
    
    selected_features = boruta.fit(X, y)
    
    # 出力ディレクトリ作成
    output_dir = project_root / 'data' / 'features' / 'selected'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 選択された特徴量をCSVで保存
    output_csv = output_dir / f'{venue_name}_regression_selected_features.csv'
    selected_df = pd.DataFrame({'feature': selected_features})
    selected_df.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"\n✅ 選択された特徴量を保存: {output_csv}")
    print(f"   特徴量数: {len(selected_features)}個")
    
    # レポート保存
    report = {
        'venue': venue_name,
        'model_type': 'regression',
        'total_features': len(X.columns),
        'selected_features': len(selected_features),
        'rejected_features': len(X.columns) - len(selected_features),
        'alpha': args.alpha,
        'max_iter': args.max_iter,
        'history': boruta.history
    }
    
    report_path = output_dir / f'{venue_name}_regression_boruta_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ レポート保存: {report_path}")
    
    print("\n" + "=" * 80)
    print("Phase 7-Regression 完了！")
    print("=" * 80)
    print(f"次のステップ: Phase 8-Regressionでハイパーパラメータ最適化")
    print(f"コマンド: python scripts/phase8_auto_tuning/run_optuna_tuning_regression.py \\")
    print(f"          {csv_path} --selected-features {output_csv}")
    print("=" * 80)


if __name__ == '__main__':
    main()
