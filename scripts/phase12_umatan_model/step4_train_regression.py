#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: Step 4 - 回帰モデル学習（タイム予測）
"""

import argparse
import pandas as pd
import lightgbm as lgb
import numpy as np
import os
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def safe_print(text):
    """文字化け対策のprint"""
    try:
        print(text.encode('shift-jis', errors='ignore').decode('shift-jis'))
    except:
        print(text)

def train_regression_model(input_dir, output_dir):
    """回帰モデル学習（タイム予測）"""
    safe_print("=" * 80)
    safe_print("Phase 12: Step 4 - 回帰モデル学習（タイム予測）")
    safe_print("=" * 80)
    
    # 入力ディレクトリの確認
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"入力ディレクトリが見つかりません: {input_dir}")
    
    # CSVファイルの読み込み
    csv_files = list(input_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"CSVファイルが見つかりません: {input_dir}")
    
    safe_print(f"\n📂 入力ディレクトリ: {input_dir}")
    safe_print(f"📄 発見したCSVファイル数: {len(csv_files)}")
    
    # 競馬場別にモデルを学習
    keibajo_mapping = {
        'funabashi': '船橋',
        'ooi': '大井',
        'urawa': '浦和',
        'kawasaki': '川崎',
        'monbetsu': '門別'
    }
    
    for keibajo_en, keibajo_jp in keibajo_mapping.items():
        safe_print(f"\n{'='*80}")
        safe_print(f"📍 競馬場: {keibajo_jp} ({keibajo_en})")
        safe_print(f"{'='*80}")
        
        # 対応するCSVファイルを探す
        csv_file = input_path / f"{keibajo_en}.csv"
        if not csv_file.exists():
            safe_print(f"⚠️  CSVファイルが見つかりません: {csv_file.name}")
            continue
        
        safe_print(f"  - 読み込み中: {csv_file.name}")
        try:
            df_combined = pd.read_csv(csv_file, encoding='shift-jis')
        except:
            df_combined = pd.read_csv(csv_file, encoding='utf-8')
        
        safe_print(f"✅ データ読み込み完了: {len(df_combined):,}行 × {len(df_combined.columns)}列")
    
    # 必須列の確認
    if 'time' not in df_combined.columns:
        raise ValueError("time列が見つかりません")
    if 'race_id' not in df_combined.columns:
        raise ValueError("race_id列が見つかりません")
    
    # ターゲットの準備（time列は既に1/10秒単位）
    df_combined['time'] = pd.to_numeric(df_combined['time'], errors='coerce')
    # 欠損値や異常値を除外
    df_combined = df_combined[df_combined['time'].notna()].copy()
    df_combined = df_combined[df_combined['time'] > 0].copy()
    
    # time列は既に1/10秒単位なのでそのまま使用
    df_combined['time_target'] = df_combined['time'].astype(int)
    
    # データの統計情報（秒単位で表示）
    safe_print(f"\n📊 データセットの統計情報:")
    safe_print(f"  - レース数: {df_combined['race_id'].nunique():,}件")
    safe_print(f"  - 総馬数: {len(df_combined):,}頭")
    safe_print(f"  - 平均タイム: {df_combined['time'].mean() / 10.0:.2f}秒")
    safe_print(f"  - タイム範囲: {df_combined['time'].min() / 10.0:.2f}秒 ～ {df_combined['time'].max() / 10.0:.2f}秒")
    
        # 特徴量の準備（データリーク防止）
        exclude_cols = ['target', 'rank_target', 'time', 'time_target', 'race_id',
                        'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
                        'race_bango', 'ketto_toroku_bango', 'umaban',
                        'finish_position', 'kakutei_chakujun']
        feature_cols = [col for col in df_combined.columns if col not in exclude_cols]
        
        safe_print(f"\n🔧 特徴量:")
        safe_print(f"  - 使用する特徴量数: {len(feature_cols)}")
        safe_print(f"  - keibajo_code 除外済み（競馬場別モデルのため）")
        
        # 特徴量の準備（keibajo_codeは除外）
        X = df_combined[feature_cols].copy()
    
        y = df_combined['time_target'].values
        
        # 欠損値補完
        X = X.fillna(0)
        
        # 最終3レースの重み付け
        if 'is_last_3_race' in df_combined.columns:
            weights = np.where(df_combined['is_last_3_race'] == 1, 2.0, 1.0)
            safe_print(f"  - 最終3レース重み付けサンプル数: {(df_combined['is_last_3_race']==1).sum():,}件（重み×2）")
        else:
            weights = np.ones(len(X))
        
        # データ分割（8:2）
        unique_groups = df_combined['race_id'].unique()
        np.random.seed(42)
        train_groups = np.random.choice(unique_groups, size=int(len(unique_groups)*0.8), replace=False)
        
        train_mask = df_combined['race_id'].isin(train_groups)
        val_mask = ~train_mask
        
        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]
        weights_train = weights[train_mask]
        weights_val = weights[val_mask]
        
        safe_print(f"\n📊 データ分割:")
        safe_print(f"  - Train: {len(X_train):,}サンプル")
        safe_print(f"  - Validation: {len(X_val):,}サンプル")
        
        # LightGBMデータセット作成
        train_data = lgb.Dataset(X_train, label=y_train, weight=weights_train)
        val_data = lgb.Dataset(X_val, label=y_val, weight=weights_val, reference=train_data)
        
        # LightGBMパラメータ（回帰）
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'max_depth': -1,
            'min_data_in_leaf': 20,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'seed': 42
        }
        
        safe_print(f"\n🚀 LightGBM学習開始（回帰）")
        safe_print(f"  - Objective: regression")
        safe_print(f"  - Metric: RMSE")
        
        # 学習
        model = lgb.train(
            params,
            train_data,
            num_boost_round=2000,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'valid'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=100, verbose=True),
                lgb.log_evaluation(period=50)
            ]
        )
        
        safe_print(f"\n✅ 学習完了: Best iteration = {model.best_iteration}")
        
        # 予測（Validation）
        y_pred = model.predict(X_val, num_iteration=model.best_iteration)
        
        # タイムを秒に戻す
        y_val_sec = y_val / 10.0
        y_pred_sec = y_pred / 10.0
        
        # 評価指標
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        rmse = np.sqrt(mean_squared_error(y_val_sec, y_pred_sec))
        mae = mean_absolute_error(y_val_sec, y_pred_sec)
        r2 = r2_score(y_val_sec, y_pred_sec)
        
        safe_print(f"\n📊 Validation 性能:")
        safe_print(f"  - RMSE: {rmse:.4f}秒")
        safe_print(f"  - MAE: {mae:.4f}秒")
        safe_print(f"  - R² Score: {r2:.4f}")
        
        # 特徴量重要度
        feature_importance = pd.DataFrame({
            'feature': model.feature_name(),
            'importance': model.feature_importance(importance_type='gain')
        }).sort_values('importance', ascending=False)
        
        safe_print(f"\n📊 特徴量重要度 Top 20:")
        for idx, row in feature_importance.head(20).iterrows():
            safe_print(f"  {row['feature']:30s} {row['importance']:>10.0f}")
        
        # モデル保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        model_file = output_path / f"phase12_{keibajo_en}_regression_model.txt"
        model.save_model(str(model_file))
        safe_print(f"\n💾 モデル保存: {model_file}")
        
        # メタデータ保存
        metadata = {
            'model_type': 'regression',
            'keibajo': keibajo_jp,
            'objective': 'regression',
            'metric': 'rmse',
            'num_features': len(feature_cols),
            'best_iteration': model.best_iteration,
            'rmse': float(rmse),
            'mae': float(mae),
            'r2_score': float(r2),
            'train_samples': len(X_train),
            'val_samples': len(X_val)
        }
        
        metadata_file = output_path / f"phase12_{keibajo_en}_regression_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        safe_print(f"💾 メタデータ保存: {metadata_file}")
    
    safe_print(f"\n{'='*80}")
    safe_print("✅ Phase 12 Step 4 完了（全競馬場）")
    safe_print(f"{'='*80}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Phase 12 Step 4: 回帰モデル学習（タイム予測）')
    parser.add_argument('--input_dir', type=str, required=True, help='特徴量ディレクトリ')
    parser.add_argument('--output_dir', type=str, required=True, help='モデル出力ディレクトリ')
    
    args = parser.parse_args()
    
    try:
        train_regression_model(args.input_dir, args.output_dir)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
