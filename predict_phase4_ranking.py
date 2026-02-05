#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 ランキングモデルで予測を実行
"""

import sys
import pandas as pd
import lightgbm as lgb
import numpy as np
from sklearn.metrics import ndcg_score
import warnings
warnings.filterwarnings('ignore')

def predict_ranking(test_csv, model_path, output_path):
    """
    ランキングモデルで予測を実行
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV (race_id必須)
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
    print(f"Phase 4 ランキング予測")
    print(f"{'='*60}")
    
    # テストデータ読み込み
    print(f"テストデータ読み込み: {test_csv}")
    df = pd.read_csv(test_csv)
    print(f"データ件数: {len(df)}")
    
    # race_idが必須
    if 'race_id' not in df.columns:
        raise ValueError("race_id列が見つかりません")
    
    # target列を確保（正解ラベル: 着順の逆数など）
    if 'target' not in df.columns:
        raise ValueError("target列が見つかりません")
    
    y_true = df['target']
    race_ids = df['race_id']
    
    unique_races = df['race_id'].nunique()
    print(f"レース数: {unique_races}")
    
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
    y_pred_score = model.predict(X_test, num_iteration=model.best_iteration)
    
    # レースごとにNDCGを計算
    unique_race_ids = df['race_id'].unique()
    ndcg_at_k = {k: [] for k in [1, 3, 5, 10]}
    
    print("NDCG計算中...")
    for race_id in unique_race_ids:
        race_mask = df['race_id'] == race_id
        y_true_race = y_true[race_mask].values
        y_pred_race = y_pred_score[race_mask]
        
        # NDCGを計算
        for k in [1, 3, 5, 10]:
            if len(y_true_race) >= k:
                try:
                    ndcg = ndcg_score([y_true_race], [y_pred_race], k=k)
                    ndcg_at_k[k].append(ndcg)
                except:
                    pass
    
    # 平均NDCG
    results = {
        'Data Count': len(df),
        'Race Count': unique_races
    }
    
    for k, values in ndcg_at_k.items():
        if values:
            results[f'NDCG@{k}'] = np.mean(values)
        else:
            results[f'NDCG@{k}'] = 0.0
    
    print("\n=== 評価結果 ===")
    for metric, value in results.items():
        if isinstance(value, float) and 'NDCG' in metric:
            print(f"{metric}: {value:.4f}")
        else:
            print(f"{metric}: {value}")
    
    # 予測結果をCSVに保存
    df['predicted_score'] = y_pred_score
    
    # レース内順位を計算
    df['predicted_rank'] = df.groupby('race_id')['predicted_score'].rank(ascending=False, method='first')
    
    df.to_csv(output_path, index=False)
    print(f"\n予測結果を保存: {output_path}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase4_ranking.py <test_csv> <model_path> <output_csv>")
        print("\n例:")
        print("  python predict_phase4_ranking.py csv/ooi_2026_jan_test_with_race_id.csv models/ooi_2023-2025_v3_with_race_id_ranking_model.txt predictions/ooi_2026_jan_ranking.csv")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    
    try:
        results = predict_ranking(test_csv, model_path, output_path)
        print("\n✅ 予測完了")
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
