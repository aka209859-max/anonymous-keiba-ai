#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 二値分類モデルで予測を実行（予測専用版）

target列がない予測用データに対応
"""

import sys
import os
import pandas as pd
import lightgbm as lgb
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def predict_binary_classification(test_csv, model_path, output_path):
    """
    二値分類モデルで予測を実行（予測専用）
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV（Phase 1の特徴量）
    model_path : str
        学習済みモデルパス
    output_path : str
        予測結果の出力先
    
    Returns
    -------
    dict
        予測結果のサマリー
    """
    print(f"\n{'='*80}")
    print(f"Phase 3 二値分類予測（予測専用モード）")
    print(f"{'='*80}")
    
    # テストデータ読み込み
    print(f"[1/5] テストデータ読み込み: {test_csv}")
    try:
        df = pd.read_csv(test_csv, encoding='shift-jis')
        print("  - エンコーディング: Shift-JIS")
    except:
        df = pd.read_csv(test_csv, encoding='utf-8')
        print("  - エンコーディング: UTF-8")
    
    print(f"  - データ件数: {len(df):,}")
    print(f"  - カラム数: {len(df.columns)}")
    
    # 識別情報を保存
    id_cols = ['race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
               'race_bango', 'ketto_toroku_bango', 'umaban']
    id_data = df[[col for col in id_cols if col in df.columns]].copy()
    
    # モデル読み込み
    print(f"\n[2/5] モデル読み込み: {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"モデルファイルが見つかりません: {model_path}")
    
    model = lgb.Booster(model_file=model_path)
    model_features = model.feature_name()
    print(f"  - モデルの特徴量数: {len(model_features)}")
    
    # 特徴量の準備
    print(f"\n[3/5] 特徴量の準備")
    
    # 除外する列
    exclude_cols = ['target', 'kakutei_chakujun', 'race_id'] + id_cols
    available_features = [col for col in df.columns if col not in exclude_cols]
    
    # モデルが要求する特徴量のみを抽出
    missing_features = [f for f in model_features if f not in available_features]
    if missing_features:
        print(f"  ⚠️  不足している特徴量: {len(missing_features)}個")
        for feat in missing_features[:10]:
            print(f"    - {feat}")
        if len(missing_features) > 10:
            print(f"    ... 他 {len(missing_features) - 10}個")
        
        # 不足特徴量を0で補完
        for feat in missing_features:
            df[feat] = 0
        print(f"  - 不足特徴量を0で補完しました")
    
    # モデルの特徴量順に並べる
    X_test = df[model_features]
    
    # 欠損値を0で補完
    if X_test.isnull().any().any():
        null_counts = X_test.isnull().sum()
        null_features = null_counts[null_counts > 0]
        print(f"  ⚠️  欠損値を検出: {len(null_features)}個の特徴量")
        X_test = X_test.fillna(0)
        print(f"  - 欠損値を0で補完しました")
    
    print(f"  ✅ 特徴量準備完了: {len(model_features)}個")
    
    # 予測
    print(f"\n[4/5] 予測実行中...")
    y_pred_proba = model.predict(X_test, num_iteration=model.best_iteration)
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # 統計情報
    print(f"  - 予測確率の平均: {y_pred_proba.mean():.4f}")
    print(f"  - 予測確率の最大: {y_pred_proba.max():.4f}")
    print(f"  - 予測確率の最小: {y_pred_proba.min():.4f}")
    print(f"  - 入線予測頭数（予測=1）: {y_pred.sum()}頭 / {len(y_pred)}頭")
    
    # 結果をDataFrameに追加
    result_df = id_data.copy()
    result_df['binary_probability'] = y_pred_proba
    result_df['predicted_class'] = y_pred
    
    # 予測結果サマリー
    results = {
        'Data Count': len(df),
        'Average Probability': y_pred_proba.mean(),
        'Predicted Positive Count': y_pred.sum(),
        'Predicted Positive Rate': y_pred.mean()
    }
    
    print(f"\n[5/5] 予測結果サマリー")
    print(f"  - データ件数: {results['Data Count']:,}件")
    print(f"  - 平均入線確率: {results['Average Probability']:.4f}")
    print(f"  - 入線予測頭数: {results['Predicted Positive Count']}頭")
    print(f"  - 入線予測率: {results['Predicted Positive Rate']:.4f}")
    
    # 予測結果をCSVに保存
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        result_df.to_csv(output_path, index=False, encoding='shift-jis')
        print(f"\n✅ 予測結果を保存（Shift-JIS）: {output_path}")
    except:
        output_path_utf8 = output_path.replace('.csv', '_utf8.csv')
        result_df.to_csv(output_path_utf8, index=False, encoding='utf-8')
        print(f"\n✅ 予測結果を保存（UTF-8）: {output_path_utf8}")
        output_path = output_path_utf8
    
    print(f"  - レコード数: {len(result_df):,}件")
    print(f"  - カラム数: {len(result_df.columns)}個")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase3.py <test_csv> <model_path> <output_csv>")
        print("\n例:")
        print("  python predict_phase3.py data/features/2026/02/川崎_20260205_features.csv \\")
        print("                           models/binary/kawasaki_2020-2025_v3_model.txt \\")
        print("                           data/predictions/phase3/川崎_20260205_phase3_binary.csv")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    
    try:
        results = predict_binary_classification(test_csv, model_path, output_path)
        print("\n" + "="*80)
        print("✅ Phase 3 二値分類予測完了")
        print("="*80)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
