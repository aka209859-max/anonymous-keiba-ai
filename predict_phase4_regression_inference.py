#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4-2 回帰分析モデルで予測を実行（予測専用版）

target列がない予測用データに対応
走破時間を予測
"""

import sys
import os
import pandas as pd
import lightgbm as lgb
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def predict_regression(test_csv, model_path, output_path):
    """
    回帰分析モデルで予測を実行（予測専用）
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV（Phase 1の特徴量）
    model_path : str
        学習済み回帰モデルパス
    output_path : str
        予測結果の出力先
    
    Returns
    -------
    dict
        予測結果のサマリー
    """
    print(f"\n{'='*80}")
    print(f"Phase 4-2 回帰予測（予測専用モード）")
    print(f"{'='*80}")
    
    # テストデータ読み込み
    print(f"[1/6] テストデータ読み込み: {test_csv}")
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
    print(f"\n[2/6] モデル読み込み: {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"モデルファイルが見つかりません: {model_path}")
    
    model = lgb.Booster(model_file=model_path)
    model_features = model.feature_name()
    print(f"  - モデルの特徴量数: {len(model_features)}")
    
    # 特徴量の準備
    print(f"\n[3/6] 特徴量の準備")
    
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
    print(f"\n[4/6] 予測実行中...")
    predicted_times_raw = model.predict(X_test, num_iteration=model.best_iteration)
    
    # ⚠️ 重要: 予測値は1/10秒単位なので、秒単位に変換
    predicted_times = predicted_times_raw / 10.0
    print(f"  ℹ️  予測値を1/10秒単位から秒単位に変換 (÷10)")
    
    # 統計情報
    print(f"  - 予測時間の平均: {predicted_times.mean():.2f}秒")
    print(f"  - 予測時間の最大: {predicted_times.max():.2f}秒")
    print(f"  - 予測時間の最小: {predicted_times.min():.2f}秒")
    print(f"  - 予測時間の標準偏差: {predicted_times.std():.2f}秒")
    
    # レース内順位の計算
    print(f"\n[5/6] レース内タイム順位の計算中...")
    result_df = id_data.copy()
    result_df['predicted_time'] = predicted_times
    
    # race_idごとに予測時間で昇順ソートして順位付け（時間が短い方が上位）
    if 'race_id' in result_df.columns:
        result_df['time_rank'] = result_df.groupby('race_id')['predicted_time'].rank(
            ascending=True, method='min'
        ).astype(int)
        
        # レース別サマリー
        race_summary = result_df.groupby('race_id').agg({
            'umaban': 'count',
            'predicted_time': ['mean', 'max', 'min']
        })
        
        print(f"  ✅ レース内タイム順位計算完了")
        print(f"  - レース数: {len(race_summary)}件")
        
        # 各レースの最速予測馬を表示
        print(f"\n  【レース別最速予測馬】")
        for race_id in sorted(result_df['race_id'].unique())[:5]:
            race_data = result_df[result_df['race_id'] == race_id]
            fastest_horse = race_data.nsmallest(1, 'predicted_time').iloc[0]
            race_num = int(str(race_id)[-2:])
            print(f"  - 第{race_num}R: {int(fastest_horse['umaban'])}番 (予測時間: {fastest_horse['predicted_time']:.2f}秒)")
        
        if len(result_df['race_id'].unique()) > 5:
            print(f"  ... 他 {len(result_df['race_id'].unique()) - 5}レース")
    else:
        print(f"  ⚠️  race_id列がないため、レース内順位は計算できません")
        result_df['time_rank'] = 0
    
    # 予測結果サマリー
    results = {
        'Data Count': len(df),
        'Average Predicted Time': predicted_times.mean(),
        'Max Predicted Time': predicted_times.max(),
        'Min Predicted Time': predicted_times.min(),
        'Std Predicted Time': predicted_times.std()
    }
    
    print(f"\n[6/6] 予測結果サマリー")
    print(f"  - データ件数: {results['Data Count']:,}件")
    print(f"  - 平均予測時間: {results['Average Predicted Time']:.2f}秒")
    print(f"  - 最大予測時間: {results['Max Predicted Time']:.2f}秒")
    print(f"  - 最小予測時間: {results['Min Predicted Time']:.2f}秒")
    
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
        print("使用法: python predict_phase4_regression_inference.py <test_csv> <model_path> <output_csv>")
        print("\n例:")
        print("  python predict_phase4_regression_inference.py \\")
        print("         data/features/2026/02/川崎_20260205_features.csv \\")
        print("         models/regression/kawasaki_2020-2025_v3_time_regression_model.txt \\")
        print("         data/predictions/phase4_regression/川崎_20260205_phase4_regression.csv")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    
    try:
        results = predict_regression(test_csv, model_path, output_path)
        print("\n" + "="*80)
        print("✅ Phase 4-2 回帰予測完了")
        print("="*80)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
