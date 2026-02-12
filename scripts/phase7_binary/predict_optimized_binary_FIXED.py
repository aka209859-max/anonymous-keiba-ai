#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 7-8 チューニング済み二値分類モデルで予測を実行（予測専用版・全競馬場対応）

Phase8でチューニングされたモデル（*_tuned_model.txt）を使用
Phase7で選択された特徴量（*_selected_features.csv）を使用
"""

import sys
import os
import pandas as pd
import lightgbm as lgb
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# 親ディレクトリのutilsをインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.keibajo_mapping import extract_keibajo_from_filename, get_keibajo_romaji

def predict_optimized_binary(test_csv, models_dir, output_path, selected_features_path=None):
    """
    チューニング済み二値分類モデルで予測を実行（予測専用・全競馬場対応）
    
    Parameters
    ----------
    test_csv : str
        テストデータCSV（Phase 1の特徴量）
    models_dir : str
        モデルディレクトリ（例: data/models/tuned/）
    output_path : str
        予測結果の出力先
    selected_features_path : str, optional
        選択特徴量CSVパス（Phase7の出力）
    
    Returns
    -------
    dict
        予測結果のサマリー
    """
    print(f"\n{'='*80}")
    print(f"Phase 7-8 二値分類予測（チューニング済みモデル・全競馬場対応）")
    print(f"{'='*80}")
    
    # 競馬場を自動検出
    try:
        keibajo_name = extract_keibajo_from_filename(test_csv)
        keibajo_romaji = get_keibajo_romaji(keibajo_name)
        model_filename = keibajo_romaji + '_tuned_model.txt'
        models_dir = models_dir.rstrip('/\\')
        model_path = os.path.join(models_dir, model_filename)
        print(f"[競馬場検出] {keibajo_name} → {keibajo_romaji} → モデル: {model_filename}")
        print(f"[モデルパス] {model_path}")
    except Exception as e:
        print(f"❌ エラー: 競馬場の自動検出に失敗しました")
        print(f"   {e}")
        sys.exit(1)
    
    # 選択特徴量の読み込み（Phase7の出力）
    if selected_features_path is None:
        # デフォルトパス（ローマ字名を使用）
        selected_features_path = f"data/features/selected/{keibajo_romaji}_selected_features.csv"
    
    print(f"\n[1/6] 選択特徴量読み込み: {selected_features_path}")
    if not os.path.exists(selected_features_path):
        print(f"⚠️  警告: 選択特徴量ファイルが見つかりません")
        print(f"   モデルの全特徴量を使用します")
        selected_features = None
    else:
        try:
            selected_df = pd.read_csv(selected_features_path)
            if 'feature' in selected_df.columns:
                selected_features = selected_df['feature'].tolist()
                print(f"  - 選択特徴量数: {len(selected_features)}")
            else:
                print(f"⚠️  警告: 'feature'列が見つかりません")
                selected_features = None
        except Exception as e:
            print(f"⚠️  警告: 選択特徴量の読み込みに失敗: {e}")
            selected_features = None
    
    # テストデータ読み込み
    print(f"\n[2/6] テストデータ読み込み: {test_csv}")
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
    print(f"\n[3/6] モデル読み込み: {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"モデルファイルが見つかりません: {model_path}")
    
    model = lgb.Booster(model_file=model_path)
    model_features = model.feature_name()
    print(f"  - モデルの特徴量数: {len(model_features)}")
    
    # 特徴量の準備
    print(f"\n[4/6] 特徴量の準備")
    
    # 除外する列
    exclude_cols = ['target', 'kakutei_chakujun', 'race_id'] + id_cols
    available_features = [col for col in df.columns if col not in exclude_cols]
    
    # Phase7で選択された特徴量がある場合はそれを使用
    if selected_features:
        use_features = [f for f in selected_features if f in model_features]
        print(f"  - Phase7選択特徴量を使用: {len(use_features)}個")
    else:
        use_features = model_features
        print(f"  - モデルの全特徴量を使用: {len(use_features)}個")
    
    # モデルが要求する特徴量のみを抽出
    missing_features = [f for f in use_features if f not in available_features]
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
    X_test = df[use_features]
    
    # 欠損値を0で補完
    if X_test.isnull().any().any():
        null_counts = X_test.isnull().sum()
        null_features = null_counts[null_counts > 0]
        print(f"  ⚠️  欠損値を検出: {len(null_features)}個の特徴量")
        X_test = X_test.fillna(0)
        print(f"  - 欠損値を0で補完しました")
    
    # データ型を数値型に変換（object型を排除）
    for col in X_test.columns:
        if X_test[col].dtype == 'object':
            try:
                X_test[col] = pd.to_numeric(X_test[col], errors='coerce').fillna(0)
                print(f"  - {col}: object → numeric に変換")
            except:
                X_test[col] = 0
                print(f"  - {col}: 変換失敗 → 0で補完")
    
    print(f"  ✅ 特徴量準備完了: {len(use_features)}個")
    
    # 予測
    print(f"\n[5/6] 予測実行中...")
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
        'Keibajo': keibajo_name,
        'Data Count': len(df),
        'Average Probability': y_pred_proba.mean(),
        'Predicted Positive Count': y_pred.sum(),
        'Predicted Positive Rate': y_pred.mean()
    }
    
    print(f"\n[6/6] 予測結果サマリー")
    print(f"  - 競馬場: {results['Keibajo']}")
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
    if len(sys.argv) < 4:
        print("使用法: python predict_optimized_binary.py <test_csv> <models_dir> <output_csv> [selected_features_csv]")
        print("\n例:")
        print("  python predict_optimized_binary.py \\")
        print("    data\\features\\2026\\02\\佐賀_20260207_features.csv \\")
        print("    data\\models\\tuned \\")
        print("    data\\predictions\\phase7_binary\\佐賀_20260207_phase7_binary.csv \\")
        print("    data\\features\\selected\\saga_selected_features.csv")
        print("\n注:")
        print("  - 競馬場名は入力CSVファイル名から自動検出されます")
        print("  - 対応競馬場: 門別、盛岡、水沢、浦和、船橋、大井、川崎、金沢、笠松、名古屋、園田、姫路、高知、佐賀")
        print("  - selected_features_csvを省略した場合、デフォルトパスを使用します")
        sys.exit(1)
    
    test_csv = sys.argv[1]
    models_dir = sys.argv[2]
    output_path = sys.argv[3]
    selected_features_path = sys.argv[4] if len(sys.argv) > 4 else None
    
    try:
        results = predict_optimized_binary(test_csv, models_dir, output_path, selected_features_path)
        print("\n" + "="*80)
        print("✅ Phase 7-8 二値分類予測完了")
        print("="*80)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
