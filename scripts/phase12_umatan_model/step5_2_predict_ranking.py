#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: Step 5-2 - ランキング予測
"""

import sys
import os
import pandas as pd
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

def predict_ranking(test_csv, model_path, output_csv):
    """Phase 12 ランキング予測"""
    print(f"\n{'='*80}")
    print(f"Phase 12: Step 5-2 - ランキング予測")
    print(f"{'='*80}")
    
    # データ読み込み
    print(f"\n[1/4] テストデータ読み込み: {test_csv}")
    try:
        df = pd.read_csv(test_csv, encoding='shift-jis')
        print("  - エンコーディング: Shift-JIS")
    except:
        df = pd.read_csv(test_csv, encoding='utf-8')
        print("  - エンコーディング: UTF-8")
    
    print(f"  - データ件数: {len(df):,}")
    print(f"  - カラム数: {len(df.columns)}")
    
    # race_idの確認
    if 'race_id' not in df.columns:
        raise ValueError("race_id列が見つかりません")
    
    # 識別情報を保存
    id_cols = ['race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code',
               'race_bango', 'ketto_toroku_bango', 'umaban']
    id_data = df[[col for col in id_cols if col in df.columns]].copy()
    
    # モデル読み込み
    print(f"\n[2/4] モデル読み込み: {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"モデルファイルが見つかりません: {model_path}")
    
    model = lgb.Booster(model_file=model_path)
    model_features = model.feature_name()
    print(f"  - モデルの特徴量数: {len(model_features)}")
    
    # 特徴量の準備
    print(f"\n[3/4] 特徴量の準備")
    exclude_cols = ['target', 'rank_target', 'time', 'race_id',
                    'finish_position', 'kakutei_chakujun'] + id_cols
    available_features = [col for col in df.columns if col not in exclude_cols]
    
    missing_features = [f for f in model_features if f not in available_features]
    if missing_features:
        print(f"  ⚠️  不足している特徴量: {len(missing_features)}個")
        for feat in missing_features:
            df[feat] = 0
        print(f"  - 不足特徴量を0で補完しました")
    
    X_test = df[model_features].fillna(0)
    
    # データ型変換
    for col in X_test.columns:
        if X_test[col].dtype == 'object':
            X_test[col] = pd.to_numeric(X_test[col], errors='coerce').fillna(0)
    
    print(f"  ✅ 特徴量準備完了: {len(model_features)}個")
    
    # 予測
    print(f"\n[4/4] 予測実行中...")
    ranking_score = model.predict(X_test, num_iteration=model.best_iteration)
    
    # レースごとに順位付け
    result_df = id_data.copy()
    result_df['ranking_score'] = ranking_score
    result_df['ranking_rank'] = result_df.groupby('race_id')['ranking_score'].rank(ascending=False, method='min').astype(int)
    
    # 統計情報
    print(f"  - ランキングスコアの平均: {ranking_score.mean():.4f}")
    print(f"  - ランキングスコアの最大: {ranking_score.max():.4f}")
    print(f"  - ランキングスコアの最小: {ranking_score.min():.4f}")
    print(f"  - レース数: {result_df['race_id'].nunique()}件")
    
    # 保存
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        result_df.to_csv(output_csv, index=False, encoding='shift-jis')
        print(f"\n✅ 予測結果を保存（Shift-JIS）: {output_csv}")
    except:
        output_csv_utf8 = output_csv.replace('.csv', '_utf8.csv')
        result_df.to_csv(output_csv_utf8, index=False, encoding='utf-8')
        print(f"\n✅ 予測結果を保存（UTF-8）: {output_csv_utf8}")
    
    print(f"\n{'='*80}")
    print("✅ Phase 12 Step 5-2 完了")
    print(f"{'='*80}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python step5_2_predict_ranking.py <test_csv> <model_path> <output_csv>")
        print("\n例: python step5_2_predict_ranking.py \\")
        print("      data/features/2026/04/船橋_20260422_features.csv \\")
        print("      data/phase12_umatan/models/ranking/phase12_ranking_model.txt \\")
        print("      data/phase12_umatan/predictions/ranking/船橋_20260422_ranking.csv")
        sys.exit(1)
    
    try:
        predict_ranking(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
