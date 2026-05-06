#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Regression Model Training (67 Features)

Purpose: Train regression models for predicting race time
Target: time (race finish time in seconds)
Features: 67 features (50 original + 17 statistical)
Training: Per-racecourse models (14 models total)
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import argparse
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

def safe_print(text):
    """Safe Japanese text output"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='ignore').decode('utf-8'))

def train_regression_model(input_dir: str, output_dir: str):
    """
    Train regression models per racecourse
    
    Args:
        input_dir: Directory containing 67-feature CSV files
        output_dir: Directory for model output
    """
    safe_print("\n" + "="*80)
    safe_print("Phase 4: Regression Model Training (67 Features)")
    safe_print("="*80)
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    safe_print(f"\n[INPUT] Directory: {input_dir}")
    csv_files = sorted(input_path.glob("*_67features.csv"))
    safe_print(f"[INFO] Found {len(csv_files)} CSV files")
    
    if len(csv_files) == 0:
        safe_print("[ERROR] No CSV files found!")
        return
    
    # Train model for each racecourse
    all_results = []
    for csv_file in csv_files:
        # Extract racecourse name
        keibajo_name = csv_file.stem.replace('_67features', '')
        
        safe_print(f"\n{'='*80}")
        safe_print(f"[RACECOURSE] {keibajo_name}")
        safe_print(f"{'='*80}")
        
        try:
            # Load data
            df_all = pd.read_csv(csv_file, encoding='shift-jis')
            safe_print(f"[OK] Data loaded: {len(df_all):,} rows x {len(df_all.columns)} columns")
            
            # Check required column
            if 'time' not in df_all.columns:
                safe_print("[ERROR] 'time' column not found")
                continue
            
            # Prepare target (time in seconds)
            df_all['time'] = pd.to_numeric(df_all['time'], errors='coerce')
            # Remove invalid times (0 or negative)
            df_all = df_all[(df_all['time'] > 0) & (df_all['time'].notna())]
            
            y = df_all['time']
            safe_print(f"\n[TARGET] Time statistics:")
            safe_print(f"  - Count: {len(y):,}")
            safe_print(f"  - Mean:  {y.mean():.2f} sec")
            safe_print(f"  - Std:   {y.std():.2f} sec")
            safe_print(f"  - Min:   {y.min():.2f} sec")
            safe_print(f"  - Max:   {y.max():.2f} sec")
            
            # Exclude columns
            exclude_cols = [
                'target', 'rank_target', 'time', 'is_1st', 'is_2nd', 'is_top2',
                'finish_position', 'race_id', 'kaisai_tsukihi', 'ketto_toroku_bango',
                'keibajo_code', 'kaisai_nen', 'race_bango', 'umaban',
                'kakutei_chakujun', 'bamei'
            ]
            
            # Select features
            feature_cols = [col for col in df_all.columns if col not in exclude_cols]
            X = df_all[feature_cols]
            
            safe_print(f"\n[FEATURES] Using {len(feature_cols)} features")
            
            # Fill missing values with 0
            X = X.fillna(0)
            
            # Train/Validation split
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            safe_print(f"\n[SPLIT] Data split:")
            safe_print(f"  - Train: {len(X_train):,} samples")
            safe_print(f"  - Val:   {len(X_val):,} samples")
            
            # Create LightGBM datasets
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            # Hyperparameters
            params = {
                'objective': 'regression',
                'metric': 'rmse',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.8,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1,
                'seed': 42
            }
            
            safe_print("\n[TRAINING] Starting LightGBM training...")
            model = lgb.train(
                params,
                train_data,
                num_boost_round=1000,
                valid_sets=[train_data, val_data],
                valid_names=['train', 'val'],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=50),
                    lgb.log_evaluation(period=100)
                ]
            )
            
            safe_print(f"\n[SUCCESS] Training completed ({model.best_iteration} iterations)")
            
            # Evaluation
            y_pred = model.predict(X_val, num_iteration=model.best_iteration)
            
            mae = mean_absolute_error(y_val, y_pred)
            rmse = np.sqrt(mean_squared_error(y_val, y_pred))
            r2 = r2_score(y_val, y_pred)
            mape = np.mean(np.abs((y_val - y_pred) / y_val)) * 100
            
            safe_print(f"\n[METRICS] Validation Results:")
            safe_print(f"  - MAE (Mean Absolute Error): {mae:.4f} sec")
            safe_print(f"  - RMSE (Root Mean Squared Error): {rmse:.4f} sec")
            safe_print(f"  - R² Score: {r2:.4f}")
            safe_print(f"  - MAPE (Mean Absolute Percentage Error): {mape:.2f}%")
            
            # Feature importance (Top 20)
            importance = model.feature_importance(importance_type='gain')
            feature_importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': importance
            }).sort_values('importance', ascending=False)
            
            safe_print(f"\n[IMPORTANCE] Top 20 Features:")
            for idx, row in feature_importance.head(20).iterrows():
                safe_print(f"  {row['feature']:30s}: {row['importance']:10.0f}")
            
            # Save model
            model_path = output_path / f"{keibajo_name}_2020-2025_v3_67features_time_regression_model.txt"
            model.save_model(str(model_path))
            safe_print(f"\n[SAVED] Model: {model_path}")
            
            # Save metadata
            metadata = {
                'model_type': 'regression',
                'target': 'time',
                'n_samples': len(df_all),
                'n_features': len(feature_cols),
                'features': feature_cols,
                'best_iteration': model.best_iteration,
                'metrics': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'r2_score': float(r2),
                    'mape': float(mape)
                },
                'keibajo': keibajo_name,
                'feature_version': '67features'
            }
            
            metadata_path = output_path / f"{keibajo_name}_2020-2025_v3_67features_time_regression_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            safe_print(f"[SAVED] Metadata: {metadata_path}")
            
            # Store results
            all_results.append({
                'keibajo': keibajo_name,
                'n_samples': len(df_all),
                'metrics': metadata['metrics']
            })
            
        except Exception as e:
            safe_print(f"[ERROR] Failed to process {keibajo_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    safe_print("\n" + "="*80)
    safe_print("[SUMMARY] All Racecourses Results")
    safe_print("="*80)
    
    if len(all_results) == 0:
        safe_print("[ERROR] No models were trained successfully!")
        return
    
    safe_print(f"\n{'Racecourse':<15} {'Samples':>10} {'MAE':>10} {'RMSE':>10} {'R²':>10} {'MAPE':>10}")
    safe_print("-" * 80)
    for result in all_results:
        m = result['metrics']
        safe_print(f"{result['keibajo']:<15} {result['n_samples']:>10,} "
                  f"{m['mae']:>10.4f} {m['rmse']:>10.4f} "
                  f"{m['r2_score']:>10.4f} {m['mape']:>9.2f}%")
    
    # Average metrics
    avg_mae = np.mean([r['metrics']['mae'] for r in all_results])
    avg_rmse = np.mean([r['metrics']['rmse'] for r in all_results])
    avg_r2 = np.mean([r['metrics']['r2_score'] for r in all_results])
    avg_mape = np.mean([r['metrics']['mape'] for r in all_results])
    
    safe_print("-" * 80)
    safe_print(f"{'Average':<15} {'':<10} {avg_mae:>10.4f} {avg_rmse:>10.4f} "
              f"{avg_r2:>10.4f} {avg_mape:>9.2f}%")
    
    safe_print(f"\n[SUCCESS] Trained {len(all_results)} models successfully!")
    safe_print(f"[OUTPUT] Models saved to: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Phase 4 Regression Models (67 Features)')
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory containing 67-feature CSV files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for trained models')
    
    args = parser.parse_args()
    
    train_regression_model(args.input, args.output)
