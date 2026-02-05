#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 回帰モデルで予測を実行
"""

import sys
import pandas as pd
import lightgbm as lgb
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

def predict_regression(test_csv, model_path, output_path):
    """
    回帰モデルで予測を実行
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV (target=走破タイム)
    model_path : str
        学習済みモデルパス
    output_path : str
        予測結果の出力先
    
    Returns
    -------
    dict
        評価結果の辞書
    """
    print(f"\n{'='*60}")
    print(f"Phase 4 回帰予測（走破タイム）")
    print(f"{'='*60}")
    
    # テストデータ読み込み
    print(f"テストデータ読み込み: {test_csv}")
    df = pd.read_csv(test_csv)
    print(f"データ件数: {len(df)}")
    
    # target列を確保（正解ラベル: 走破タイム）
    if 'target' not in df.columns:
        raise ValueError("target列が見つかりません")
    
    y_true = df['target']
    
    # 不要列を除外
    exclude_cols = ['target', 'kakutei_chakujun', 'race_id', 'umaban']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X_test = df[feature_cols]
    
    print(f"特徴量数: {len(feature_cols)}")
    
    # モデル読み込み
    print(f"モデル読み込み: {model_path}")
    model = lgb.Booster(model_file=model_path)
    
    # 予測
    print("予測実行中...")
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    
    # 評価
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    # 相対誤差（平均走破タイムに対する割合）
    mean_time = y_true.mean()
    relative_error = (mae / mean_time) * 100
    
    # タイム統計
    time_stats = {
        'Mean Time (True)': mean_time,
        'Mean Time (Predicted)': y_pred.mean(),
        'Min Time (True)': y_true.min(),
        'Max Time (True)': y_true.max()
    }
    
    results = {
        'Data Count': len(df),
        'RMSE': rmse,
        'MAE': mae,
        'R²': r2,
        '相対誤差(%)': relative_error,
        **time_stats
    }
    
    print("\n=== 評価結果 ===")
    for metric, value in results.items():
        if isinstance(value, float):
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")
    
    # 予測結果をCSVに保存
    df['predicted_time'] = y_pred
    df['time_error'] = y_pred - y_true
    df['abs_time_error'] = np.abs(y_pred - y_true)
    
    df.to_csv(output_path, index=False)
    print(f"\n予測結果を保存: {output_path}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase4_regression.py <test_csv> <model_path> <output_csv>")
        print("\n例:")
        print("  python predict_phase4_regression.py csv/ooi_2026_jan_test_time.csv models/ooi_2023-2025_v3_time_regression_model.txt predictions/ooi_2026_jan_regression.csv")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    
    try:
        results = predict_regression(test_csv, model_path, output_path)
        print("\n✅ 予測完了")
    except Exception as e:
        print(f("\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
