#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Regression Model Training with Distance Categories (67 Features)

Purpose: Train regression models for predicting race time
Target: time (race finish time in seconds)
Features: 67 features (50 original + 17 statistical)
Training: Per-racecourse × distance category models (14 × 3 = 42 models total)

Distance Categories:
  - SHORT: ≤1200m
  - MILE:  1300-1700m
  - LONG:  ≥1800m
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

def categorize_distance(kyori):
    """Categorize distance into 3 categories"""
    if kyori <= 1200:
        return 'SHORT'
    elif kyori <= 1700:
        return 'MILE'
    else:
        return 'LONG'

def train_regression_model_with_distance(input_dir: str, output_dir: str):
    """Train regression models per racecourse × distance category"""
    
    safe_print("\n" + "="*80)
    safe_print("Phase 4: Regression Model with Distance Categories (67 Features)")
    safe_print("="*80)
    safe_print("\nDistance Categories:")
    safe_print("  - SHORT: ≤1200m")
    safe_print("  - MILE:  1300-1700m")
    safe_print("  - LONG:  ≥1800m")
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find CSV files
    safe_print(f"\n[INPUT] Directory: {input_dir}")
    csv_files = sorted(input_path.glob("*_67features_FULL.csv"))
    
    if len(csv_files) == 0:
        csv_files = sorted(input_path.glob("*_67features.csv"))
    
    safe_print(f"[INFO] Found {len(csv_files)} CSV files")
    
    if len(csv_files) == 0:
        safe_print("[ERROR] No CSV files found!")
        return
    
    all_results = []
    total_models = 0
    successful_models = 0
    
    for csv_file in csv_files:
        keibajo_name = csv_file.stem.replace('_67features_FULL', '').replace('_67features', '')
        
        safe_print(f"\n{'='*80}")
        safe_print(f"[RACECOURSE] {keibajo_name.upper()}")
        safe_print(f"{'='*80}")
        
        try:
            # Load data
            df_all = pd.read_csv(csv_file, encoding='shift-jis')
            safe_print(f"[OK] Data loaded: {len(df_all):,} rows x {len(df_all.columns)} columns")
            
            # Check required columns
            if 'time' not in df_all.columns:
                safe_print("[ERROR] 'time' column not found")
                continue
            if 'kyori' not in df_all.columns:
                safe_print("[ERROR] 'kyori' column not found")
                continue
            
            # Prepare target (time in seconds)
            df_all['time'] = pd.to_numeric(df_all['time'], errors='coerce')
            df_all = df_all[(df_all['time'] > 0) & (df_all['time'].notna())]
            
            # Add distance category
            df_all['distance_category'] = df_all['kyori'].apply(categorize_distance)
            
            # Show distance distribution
            safe_print(f"\n[DISTANCE] Distribution:")
            for cat in ['SHORT', 'MILE', 'LONG']:
                count = (df_all['distance_category'] == cat).sum()
                pct = count / len(df_all) * 100
                safe_print(f"  - {cat:5s}: {count:6,} races ({pct:5.1f}%)")
            
            # Train model for each distance category
            for distance_cat in ['SHORT', 'MILE', 'LONG']:
                safe_print(f"\n{'-'*80}")
                safe_print(f"[CATEGORY] {keibajo_name.upper()} × {distance_cat}")
                safe_print(f"{'-'*80}")
                
                total_models += 1
                
                # Filter by distance category
                df_cat = df_all[df_all['distance_category'] == distance_cat].copy()
                
                if len(df_cat) < 100:
                    safe_print(f"[SKIP] Insufficient data: {len(df_cat)} samples")
                    continue
                
                safe_print(f"[DATA] Samples: {len(df_cat):,}")
                
                # Prepare target
                y = df_cat['time']
                
                safe_print(f"[TARGET] Time statistics:")
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
                    'kakutei_chakujun', 'bamei', 'grade_code', 'distance_category'
                ]
                
                # Select features
                feature_cols = [col for col in df_cat.columns if col not in exclude_cols]
                X = df_cat[feature_cols]
                
                safe_print(f"[FEATURES] Using {len(feature_cols)} features")
                
                # Fill missing values
                X = X.fillna(0)
                
                # Train/Validation split
                try:
                    X_train, X_val, y_train, y_val = train_test_split(
                        X, y, test_size=0.2, random_state=42
                    )
                except ValueError as e:
                    safe_print(f"[ERROR] Split failed: {e}")
                    continue
                
                safe_print(f"[SPLIT] Data split:")
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
                
                safe_print("[TRAINING] Starting LightGBM training...")
                
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
                
                safe_print(f"[SUCCESS] Training completed ({model.best_iteration} iterations)")
                
                # Evaluation
                y_pred = model.predict(X_val, num_iteration=model.best_iteration)
                
                mae = mean_absolute_error(y_val, y_pred)
                rmse = np.sqrt(mean_squared_error(y_val, y_pred))
                r2 = r2_score(y_val, y_pred)
                
                safe_print(f"[METRICS] Validation Results:")
                safe_print(f"  - MAE:  {mae:.4f} sec")
                safe_print(f"  - RMSE: {rmse:.4f} sec")
                safe_print(f"  - R²:   {r2:.4f}")
                
                # Feature importance (Top 15)
                importance = model.feature_importance(importance_type='gain')
                feature_importance = pd.DataFrame({
                    'feature': feature_cols,
                    'importance': importance
                }).sort_values('importance', ascending=False)
                
                safe_print(f"[IMPORTANCE] Top 15 Features:")
                for idx, row in feature_importance.head(15).iterrows():
                    safe_print(f"  {row['feature']:30s}: {row['importance']:10.0f}")
                
                # Save model
                model_filename = f"{keibajo_name}_{distance_cat}_regression_model.txt"
                model_path = output_path / model_filename
                model.save_model(str(model_path))
                safe_print(f"[SAVED] Model: {model_path}")
                
                # Save metadata
                metadata = {
                    'model_type': 'regression',
                    'target': 'time',
                    'keibajo': keibajo_name,
                    'distance_category': distance_cat,
                    'n_samples': len(df_cat),
                    'n_features': len(feature_cols),
                    'features': feature_cols,
                    'best_iteration': model.best_iteration,
                    'metrics': {
                        'mae': float(mae),
                        'rmse': float(rmse),
                        'r2_score': float(r2)
                    },
                    'feature_version': '67features',
                    'distance_range': {
                        'SHORT': '≤1200m',
                        'MILE': '1300-1700m',
                        'LONG': '≥1800m'
                    }[distance_cat]
                }
                
                metadata_filename = f"{keibajo_name}_{distance_cat}_regression_metadata.json"
                metadata_path = output_path / metadata_filename
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                safe_print(f"[SAVED] Metadata: {metadata_path}")
                
                # Store results
                all_results.append({
                    'keibajo': keibajo_name,
                    'distance_category': distance_cat,
                    'n_samples': len(df_cat),
                    'metrics': metadata['metrics']
                })
                
                successful_models += 1
                
        except Exception as e:
            safe_print(f"[ERROR] Failed to process {keibajo_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    safe_print("\n" + "="*80)
    safe_print("[SUMMARY] All Models Results")
    safe_print("="*80)
    
    if len(all_results) == 0:
        safe_print("[ERROR] No models were trained successfully!")
        return
    
    safe_print(f"\n{'Racecourse':<12} {'Category':<8} {'Samples':>8} {'MAE':>10} {'RMSE':>10} {'R²':>10}")
    safe_print("-" * 85)
    for result in all_results:
        m = result['metrics']
        safe_print(f"{result['keibajo']:<12} {result['distance_category']:<8} {result['n_samples']:>8,} "
                  f"{m['mae']:>10.4f} {m['rmse']:>10.4f} {m['r2_score']:>10.4f}")
    
    # Average metrics
    avg_mae = np.mean([r['metrics']['mae'] for r in all_results])
    avg_rmse = np.mean([r['metrics']['rmse'] for r in all_results])
    avg_r2 = np.mean([r['metrics']['r2_score'] for r in all_results])
    
    safe_print("-" * 85)
    safe_print(f"{'Average':<12} {'':<8} {'':<8} {avg_mae:>10.4f} {avg_rmse:>10.4f} {avg_r2:>10.4f}")
    
    safe_print(f"\n[COMPLETE] Successfully trained {successful_models}/{total_models} models")
    safe_print(f"[OUTPUT] Models saved to: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Phase 4 Regression Models with Distance Categories')
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory containing 67-feature CSV files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for trained models')
    
    args = parser.parse_args()
    
    train_regression_model_with_distance(args.input, args.output)
