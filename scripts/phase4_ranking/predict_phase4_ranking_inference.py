#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4-1 ランキングモデルで予測を実行（予測専用版・全競馬場対応）
"""

import sys
import os
import pandas as pd
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

# 親ディレクトリのutilsをインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.keibajo_mapping import extract_keibajo_from_filename, get_model_filename

def predict_ranking(test_csv, models_dir, output_path):
    """ランキングモデルで予測（全競馬場対応）"""
    print(f"\n{'='*80}")
    print(f"Phase 4-1 ランキング予測（予測専用モード・全競馬場対応）")
    print(f"{'='*80}")
    
    # 競馬場を自動検出
    try:
        keibajo_name = extract_keibajo_from_filename(test_csv)
        model_filename = get_model_filename(keibajo_name, 'ranking')
        # models_dir の末尾の区切り文字を削除
        models_dir = models_dir.rstrip('/\\')
        model_path = os.path.join(models_dir, model_filename)
        print(f"[競馬場検出] {keibajo_name} → モデル: {model_filename}")
        print(f"[モデルパス] {model_path}")
    except Exception as e:
        print(f"❌ エラー: 競馬場の自動検出に失敗しました: {e}")
        sys.exit(1)
    
    # データ読み込み
    print(f"\n[1/5] テストデータ読み込み: {test_csv}")
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
    print(f"\n[2/5] モデル読み込み: {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"モデルファイルが見つかりません: {model_path}")
    
    model = lgb.Booster(model_file=model_path)
    model_features = model.feature_name()
    print(f"  - モデルの特徴量数: {len(model_features)}")
    
    # 特徴量の準備
    print(f"\n[3/5] 特徴量の準備")
    exclude_cols = ['target', 'kakutei_chakujun', 'race_id'] + id_cols
    available_features = [col for col in df.columns if col not in exclude_cols]
    
    missing_features = [f for f in model_features if f not in available_features]
    if missing_features:
        print(f"  ⚠️  不足している特徴量: {len(missing_features)}個")
        for feat in missing_features:
            df[feat] = 0
        print(f"  - 不足特徴量を0で補完しました")
    
    X_test = df[model_features].fillna(0)
    print(f"  ✅ 特徴量準備完了: {len(model_features)}個")
    
    # 予測
    print(f"\n[4/5] 予測実行中...")
    ranking_scores = model.predict(X_test, num_iteration=model.best_iteration)
    
    # レースごとの順位付け
    result_df = id_data.copy()
    result_df['ranking_score'] = ranking_scores
    result_df['predicted_rank'] = result_df.groupby('race_id')['ranking_score'].rank(ascending=False, method='min').astype(int)
    
    # 統計情報
    print(f"  - ランキングスコアの平均: {ranking_scores.mean():.4f}")
    print(f"  - ランキングスコアの最大: {ranking_scores.max():.4f}")
    print(f"  - ランキングスコアの最小: {ranking_scores.min():.4f}")
    
    # レースごとのTOP3表示
    print(f"\n[5/5] 予測結果サマリー")
    print(f"  - 競馬場: {keibajo_name}")
    print(f"  - データ件数: {len(result_df):,}件")
    print(f"  - レース数: {result_df['race_id'].nunique()}件")
    
    # 保存
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
    
    return {'Keibajo': keibajo_name, 'Data Count': len(result_df), 'Race Count': result_df['race_id'].nunique()}

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python predict_phase4_ranking_inference.py <test_csv> <models_dir> <output_csv>")
        print("\n例: python predict_phase4_ranking_inference.py \\")
        print("      data\\features\\2026\\02\\佐賀_20260207_features.csv \\")
        print("      models\\ranking \\")
        print("      data\\predictions\\phase4_ranking\\佐賀_20260207_phase4_ranking.csv")
        sys.exit(1)
    
    try:
        results = predict_ranking(sys.argv[1], sys.argv[2], sys.argv[3])
        print("\n" + "="*80)
        print("✅ Phase 4-1 ランキング予測完了")
        print("="*80)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
