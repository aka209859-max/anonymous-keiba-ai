#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 二値分類モデルで予測を実行
"""

import sys
import pandas as pd
import lightgbm as lgb
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

def predict_binary_classification(test_csv, model_path, output_path):
    """
    二値分類モデルで予測を実行
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV
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
    print(f"Phase 3 二値分類予測")
    print(f"{'='*60}")
    
    # テストデータ読み込み
    print(f"テストデータ読み込み: {test_csv}")
    df = pd.read_csv(test_csv)
    print(f"データ件数: {len(df)}")
    
    # target列を確保（正解ラベル）
    if 'target' not in df.columns:
        raise ValueError("target列が見つかりません")
    
    y_true = df['target']
    
    # 不要列を除外（umaban はモデルの特徴量なので除外しない）
    exclude_cols = ['target', 'kakutei_chakujun', 'race_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X_test = df[feature_cols]
    
    print(f"特徴量数: {len(feature_cols)}")
    
    # モデル読み込み
    print(f"モデル読み込み: {model_path}")
    model = lgb.Booster(model_file=model_path)
    
    # 予測
    print("予測実行中...")
    y_pred_proba = model.predict(X_test, num_iteration=model.best_iteration)
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # 評価
    auc = roc_auc_score(y_true, y_pred_proba)
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # 結果を出力
    results = {
        'AUC': auc,
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1,
        'Data Count': len(df),
        'Positive Rate': y_true.mean(),
        'Predicted Positive Rate': y_pred.mean()
    }
    
    print("\n=== 評価結果 ===")
    for metric, value in results.items():
        if isinstance(value, (int, float)) and metric != 'Data Count':
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")
    
    # 予測結果をCSVに保存
    df['predicted_proba'] = y_pred_proba
    df['predicted'] = y_pred
    df.to_csv(output_path, index=False)
    print(f"\n予測結果を保存: {output_path}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase3.py <test_csv> <model_path> <output_csv>")
        print("\n例:")
        print("  python predict_phase3.py csv/ooi_2026_jan_test.csv models/ooi_2023-2025_v3_model.txt predictions/ooi_2026_jan_binary.csv")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    
    try:
        results = predict_binary_classification(test_csv, model_path, output_path)
        print("\n✅ 予測完了")
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
