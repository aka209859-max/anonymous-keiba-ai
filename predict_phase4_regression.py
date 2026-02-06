#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
predict_phase4_regression.py
Phase 4 回帰モデルで予測を実行
"""

import sys
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def predict_regression(test_csv, model_file, output_csv):
    """
    Phase 4 回帰モデルで予測
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV
    model_file : str
        学習済み回帰モデル
    output_csv : str
        出力CSVファイル
    """
    print("=" * 80)
    print("Phase 4 回帰予測")
    print("=" * 80)
    print()
    
    # モデル読み込み
    print(f"モデル読み込み: {model_file}")
    try:
        model = lgb.Booster(model_file=model_file)
        print("  - モデル読み込み完了\n")
    except Exception as e:
        print(f"エラー: モデル読み込みに失敗しました: {e}")
        sys.exit(1)
    
    # テストデータ読み込み
    print(f"テストデータ読み込み: {test_csv}")
    try:
        df = pd.read_csv(test_csv, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(test_csv, encoding='utf-8')
    
    print(f"  - データ件数: {len(df):,}件\n")
    
    # target列の有無を確認
    has_target = 'target' in df.columns
    if has_target:
        y_true = df['target'].copy()
        X = df.drop('target', axis=1)
    else:
        X = df.copy()
    
    # 非数値カラムを削除
    non_numeric_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols:
        print(f"  警告: 非数値カラムを削除します: {non_numeric_cols}\n")
        X = X.select_dtypes(include=[np.number])
    
    # 欠損値を補完
    if X.isnull().any().any():
        print("  警告: 欠損値を平均値で補完します\n")
        X = X.fillna(X.mean())
    
    # 予測
    print("予測中...")
    try:
        predictions = model.predict(X)
        print("  - 予測完了\n")
    except Exception as e:
        print(f"エラー: 予測に失敗しました: {e}")
        sys.exit(1)
    
    # 予測結果を正規化（0-1）
    # Min-Max正規化: (x - min) / (max - min)
    # 反転して、タイムが速いほどスコアが高くなるようにする
    pred_min = predictions.min()
    pred_max = predictions.max()
    
    if pred_max > pred_min:
        # 反転正規化: 1 - ((x - min) / (max - min))
        normalized_scores = 1.0 - ((predictions - pred_min) / (pred_max - pred_min))
    else:
        normalized_scores = np.ones_like(predictions) * 0.5
    
    # 評価指標（target列がある場合のみ）
    if has_target:
        # 欠損値を除外
        valid_mask = ~y_true.isnull()
        y_true_valid = y_true[valid_mask]
        predictions_valid = predictions[valid_mask]
        
        if len(y_true_valid) > 0:
            rmse = np.sqrt(mean_squared_error(y_true_valid, predictions_valid))
            mae = mean_absolute_error(y_true_valid, predictions_valid)
            r2 = r2_score(y_true_valid, predictions_valid)
            relative_error = (rmse / y_true_valid.mean()) * 100 if y_true_valid.mean() != 0 else 0
            
            print("評価指標（走破タイムが既知のデータ）:")
            print(f"  - 評価可能データ: {len(y_true_valid):,}件")
            print(f"  - RMSE: {rmse:.4f}秒")
            print(f"  - MAE: {mae:.4f}秒")
            print(f"  - R2: {r2:.4f}")
            print(f"  - 相対誤差: {relative_error:.2f}%")
            print(f"  - 目的変数の平均値: {y_true_valid.mean():.2f}秒\n")
    
    # 出力データフレーム作成
    output_df = df.copy()
    output_df['predicted_time'] = predictions
    output_df['regression_score'] = normalized_scores
    
    # 統計情報
    print("予測結果の統計:")
    print(f"  - 予測タイムの平均: {predictions.mean():.2f}秒")
    print(f"  - 予測タイムの最小: {predictions.min():.2f}秒")
    print(f"  - 予測タイムの最大: {predictions.max():.2f}秒")
    print(f"  - regression_scoreの平均: {normalized_scores.mean():.4f}")
    print(f"  - regression_scoreの範囲: [{normalized_scores.min():.4f}, {normalized_scores.max():.4f}]\n")
    
    # 保存
    output_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"出力: {output_csv}")
    print("=" * 80)
    print()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase4_regression.py <test_csv> <model_file> <output_csv>")
        print("\n例:")
        print("  python predict_phase4_regression.py ooi_2025_full_test_with_time.csv ooi_2023-2025_with_time_regression_model.txt ooi_2025_phase4_regression_v3.csv")
        sys.exit(1)
    
    predict_regression(sys.argv[1], sys.argv[2], sys.argv[3])
