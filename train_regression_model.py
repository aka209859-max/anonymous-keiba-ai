#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_regression_model.py
地方競馬AI 回帰分析プログラム (LightGBM Regressor + Optuna)

使用法:
    python train_regression_model.py <csvファイル名> [特徴量リストファイル]

出力:
    - {csv_file}_regression_model.txt: 学習済み回帰モデル
    - {csv_file}_regression_model.png: 特徴量重要度グラフ (Top 20)
    - {csv_file}_regression_score.txt: 評価指標ログ

注意:
    - 目的変数は 'target' （走破タイム（秒）またはタイム指数）として扱います
    - 特徴量リストファイルを指定すると、二値分類で選定された特徴量のみを使用します
"""

import sys
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import lightgbm as lgb
import optuna.integration.lightgbm as lgb_optuna
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# 日本語フォント設定（環境に応じて調整）
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_feature_list(feature_file):
    """特徴量リストファイルを読み込む"""
    try:
        with open(feature_file, 'r', encoding='utf-8') as f:
            features = [line.strip() for line in f if line.strip()]
        print(f"  - 特徴量リストファイルから {len(features)} 個の特徴量を読み込みました")
        return features
    except Exception as e:
        print(f"  警告: 特徴量リストファイルの読み込みに失敗しました: {e}")
        return None


def main():
    """メイン処理"""
    
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        print("エラー: CSVファイル名が指定されていません")
        print("使用法: python train_regression_model.py <csvファイル名> [特徴量リストファイル]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    feature_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # ファイルの存在確認
    if not os.path.exists(csv_file):
        print(f"エラー: ファイル '{csv_file}' が見つかりません")
        sys.exit(1)
    
    print("=" * 80)
    print("地方競馬AI 回帰分析プログラム (LightGBM Regressor + Optuna)")
    print("=" * 80)
    print(f"CSVファイル: {csv_file}\n")
    
    # データ読み込み
    print("[1/6] データ読み込み中...")
    try:
        df = pd.read_csv(csv_file, encoding='shift-jis')
        print(f"  - データ件数: {len(df):,}件")
        print(f"  - カラム数: {len(df.columns)}個")
    except UnicodeDecodeError:
        print("  警告: Shift-JISでの読み込みに失敗。UTF-8で再試行...")
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"  - データ件数: {len(df):,}件")
        print(f"  - カラム数: {len(df.columns)}個")
    except Exception as e:
        print(f"エラー: CSVファイルの読み込みに失敗しました: {e}")
        sys.exit(1)
    
    # 目的変数の確認
    if 'target' not in df.columns:
        print("エラー: 'target' カラムが見つかりません")
        print("回帰分析では、'target' に走破タイム（秒）またはタイム指数を設定してください")
        sys.exit(1)
    
    # 目的変数と説明変数の分離
    X = df.drop('target', axis=1)
    y = df['target']
    
    print(f"  - 目的変数 'target' の統計:")
    print(f"    最小値: {y.min():.2f}, 最大値: {y.max():.2f}")
    print(f"    平均値: {y.mean():.2f}, 中央値: {y.median():.2f}")
    print(f"    標準偏差: {y.std():.2f}")
    
    # 特徴量リストファイルが指定されている場合
    if feature_file:
        print("\n[2/6] 特徴量リストファイルから特徴量を読み込み中...")
        selected_features = load_feature_list(feature_file)
        if selected_features:
            # 存在する特徴量のみを使用
            available_features = [f for f in selected_features if f in X.columns]
            if len(available_features) == 0:
                print("  警告: リストの特徴量がデータに存在しません。全特徴量を使用します。")
                selected_features = X.columns.tolist()
            else:
                print(f"  - 使用可能な特徴量: {len(available_features)} / {len(selected_features)}")
                selected_features = available_features
                X = X[selected_features]
        else:
            selected_features = X.columns.tolist()
    else:
        print("\n[2/6] 全特徴量を使用...")
        selected_features = X.columns.tolist()
    
    # 非数値カラムのチェックと処理
    non_numeric_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols:
        print(f"  警告: 非数値カラムが検出されました: {non_numeric_cols}")
        print("  これらのカラムを削除します...")
        X = X.select_dtypes(include=[np.number])
        selected_features = X.columns.tolist()
    
    # 欠損値のチェック
    if X.isnull().any().any():
        print("  警告: 欠損値が検出されました。平均値で補完します...")
        X = X.fillna(X.mean())
    
    # 目的変数の欠損値・異常値チェック
    if y.isnull().any():
        print("  警告: 目的変数に欠損値があります。該当行を削除します...")
        valid_indices = ~y.isnull()
        X = X[valid_indices]
        y = y[valid_indices]
    
    print(f"  - 最終的な特徴量数: {len(X.columns)}個")
    print(f"  - 最終的なデータ件数: {len(X):,}件\n")
    
    # データ分割
    print("[3/6] データ分割中...")
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )
    
    print(f"  - 訓練データ: {len(X_train):,}件")
    print(f"  - テストデータ: {len(X_test):,}件\n")
    
    # LightGBM Dataset作成
    print("[4/6] LightGBM Datasetを作成中...")
    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_eval = lgb.Dataset(X_test, y_test, reference=lgb_train)
    print("  - Dataset作成完了\n")
    
    # LightGBM + Optunaによるハイパーパラメータ最適化
    print("[5/6] LightGBM Regressor + Optunaによる学習中...")
    print("  （ハイパーパラメータ自動最適化を実行します）")
    
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'verbosity': -1,
        'boosting_type': 'gbdt',
        'force_col_wise': True
    }
    
    try:
        model = lgb_optuna.train(
            params,
            lgb_train,
            valid_sets=[lgb_eval],
            num_boost_round=1000,
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=100)
            ]
        )
        print("  - 学習完了\n")
    except Exception as e:
        print(f"エラー: モデル学習中にエラーが発生しました: {e}")
        sys.exit(1)
    
    # モデル評価
    print("[6/6] モデル評価中...")
    
    # 予測
    y_pred = model.predict(X_test)
    
    # 評価指標計算
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # 相対誤差の計算（平均値に対する割合）
    mean_target = y_test.mean()
    relative_error = (rmse / mean_target) * 100 if mean_target != 0 else 0
    
    print(f"  - RMSE (二乗平均平方根誤差):  {rmse:.4f}")
    print(f"  - MAE (平均絶対誤差):         {mae:.4f}")
    print(f"  - R² (決定係数):              {r2:.4f}")
    print(f"  - 相対誤差:                   {relative_error:.2f}%")
    print(f"  - 目的変数の平均値:           {mean_target:.2f}\n")
    
    # 出力ファイルの準備
    print("[保存] 結果を保存中...")
    
    base_name = csv_file.replace('.csv', '')
    model_file = f"{base_name}_regression_model.txt"
    image_file = f"{base_name}_regression_model.png"
    score_file = f"{base_name}_regression_score.txt"
    
    # モデルの保存
    try:
        model.save_model(model_file)
        print(f"  - モデル保存: {model_file}")
    except Exception as e:
        print(f"  エラー: モデル保存に失敗しました: {e}")
    
    # 特徴量重要度の可視化
    try:
        importance = model.feature_importance(importance_type='gain')
        feature_importance = pd.DataFrame({
            'feature': selected_features,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        # Top 20を可視化
        top_n = min(20, len(feature_importance))
        plt.figure(figsize=(10, 8))
        plt.barh(
            range(top_n),
            feature_importance['importance'].head(top_n),
            color='steelblue'
        )
        plt.yticks(
            range(top_n),
            feature_importance['feature'].head(top_n),
            fontsize=9
        )
        plt.xlabel('Importance (Gain)', fontsize=11)
        plt.title(f'Feature Importance - Regression Model (Top {top_n})', fontsize=13, fontweight='bold')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(image_file, dpi=150)
        plt.close()
        print(f"  - 重要度グラフ保存: {image_file}")
    except Exception as e:
        print(f"  エラー: グラフ保存に失敗しました: {e}")
    
    # 評価指標の保存
    try:
        with open(score_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("地方競馬AI 回帰分析 結果\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"CSVファイル: {csv_file}\n")
            f.write(f"データ件数: {len(df):,}件\n")
            f.write(f"訓練データ: {len(X_train):,}件\n")
            f.write(f"テストデータ: {len(X_test):,}件\n\n")
            
            f.write("【評価指標】\n")
            f.write(f"RMSE (二乗平均平方根誤差): {rmse:.4f}\n")
            f.write(f"MAE (平均絶対誤差):        {mae:.4f}\n")
            f.write(f"R² (決定係数):             {r2:.4f}\n")
            f.write(f"相対誤差:                  {relative_error:.2f}%\n")
            f.write(f"目的変数の平均値:          {mean_target:.2f}\n\n")
            
            f.write("【目的変数の統計】\n")
            f.write(f"最小値: {y.min():.2f}\n")
            f.write(f"最大値: {y.max():.2f}\n")
            f.write(f"平均値: {y.mean():.2f}\n")
            f.write(f"中央値: {y.median():.2f}\n")
            f.write(f"標準偏差: {y.std():.2f}\n\n")
            
            f.write("【特徴量情報】\n")
            f.write(f"使用特徴量数: {len(selected_features)}\n")
            if feature_file:
                f.write(f"特徴量リストファイル: {feature_file}\n")
            f.write("\n")
            
            f.write("【特徴量重要度 Top 20】\n")
            f.write("-" * 60 + "\n")
            for idx, row in feature_importance.head(20).iterrows():
                f.write(f"{row['feature']:40s} {row['importance']:10.2f}\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        print(f"  - 評価指標保存: {score_file}\n")
    except Exception as e:
        print(f"  エラー: 評価指標保存に失敗しました: {e}")
    
    print("=" * 80)
    print("回帰分析完了！")
    print("=" * 80)
    print(f"\n出力ファイル:")
    print(f"  1. {model_file}")
    print(f"  2. {image_file}")
    print(f"  3. {score_file}\n")


if __name__ == "__main__":
    main()
