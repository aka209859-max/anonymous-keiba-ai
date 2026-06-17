#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Binary Classification Model Training with Distance Categories (67 Features)

Purpose: Train binary classification models for predicting top-3 finishes
Target: target (1 if top-3, 0 otherwise)
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
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import argparse
from pathlib import Path
import json
import sys

def safe_print(text):
    """Safe Japanese text output"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='ignore').decode('utf-8'))

def categorize_distance(kyori):
    """
    Categorize distance into 3 categories
    
    Args:
        kyori: Distance in meters
    
    Returns:
        'SHORT', 'MILE', or 'LONG'
    """
    if kyori <= 1200:
        return 'SHORT'
    elif kyori <= 1700:
        return 'MILE'
    else:
        return 'LONG'

def train_binary_model_with_distance(input_dir: str, output_dir: str):
    """
    Train binary classification models per racecourse × distance category
    
    Args:
        input_dir: Directory containing 67-feature CSV files
        output_dir: Directory for model output
    """
    safe_print("\n" + "="*80)
    safe_print("Phase 3: Binary Classification with Distance Categories (67 Features)")
    safe_print("="*80)
    safe_print("\nDistance Categories:")
    safe_print("  - SHORT: ≤1200m")
    safe_print("  - MILE:  1300-1700m")
    safe_print("  - LONG:  ≥1800m")
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    safe_print(f"\n[INPUT] Directory: {input_dir}")
    csv_files = sorted(input_path.glob("*_67features_FULL.csv"))
    
    if len(csv_files) == 0:
        # Fallback to old naming
        csv_files = sorted(input_path.glob("*_67features.csv"))
    
    safe_print(f"[INFO] Found {len(csv_files)} CSV files")
    
    if len(csv_files) == 0:
        safe_print("[ERROR] No CSV files found!")
        return
    
    # Train models for each racecourse and distance category
    all_results = []
    total_models = 0
    successful_models = 0
    
    for csv_file in csv_files:
        # Extract racecourse name from filename
        # Example: urawa_67features_FULL.csv -> urawa
        keibajo_name = csv_file.stem.replace('_67features_FULL', '').replace('_67features', '')
        
        safe_print(f"\n{'='*80}")
        safe_print(f"[RACECOURSE] {keibajo_name.upper()}")
        safe_print(f"{'='*80}")
        
        try:
            # Load data
            df_all = pd.read_csv(csv_file, encoding='shift-jis')
            safe_print(f"[OK] Data loaded: {len(df_all):,} rows x {len(df_all.columns)} columns")
            
            # Check required columns
            if 'target' not in df_all.columns:
                safe_print("[ERROR] 'target' column not found")
                continue
            
            if 'kyori' not in df_all.columns:
                safe_print("[ERROR] 'kyori' column not found")
                continue
            
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
                    safe_print(f"[SKIP] Insufficient data: {len(df_cat)} samples (minimum: 100)")
                    continue
                
                safe_print(f"[DATA] Samples: {len(df_cat):,}")
                
                # Prepare target variable
                y = df_cat['target']
                
                # Check class balance
                n_positive = y.sum()
                n_negative = len(y) - n_positive
                
                if n_positive < 10 or n_negative < 10:
                    safe_print(f"[SKIP] Imbalanced data: positive={n_positive}, negative={n_negative}")
                    continue
                
                safe_print(f"[TARGET] Distribution:")
                safe_print(f"  - Top-3 (1): {n_positive:,} horses ({y.mean()*100:.1f}%)")
                safe_print(f"  - Others (0): {n_negative:,} horses ({(1-y.mean())*100:.1f}%)")
                
                # Exclude columns
                exclude_cols = [
                    'target', 'rank_target', 'time', 'is_1st', 'is_2nd', 'is_top2', 
                    'finish_position', 'race_id', 'kaisai_tsukihi', 'ketto_toroku_bango',
                    'keibajo_code', 'grade_code', 'distance_category'
                ]
                
                # Select features
                feature_cols = [col for col in df_cat.columns if col not in exclude_cols]
                X = df_cat[feature_cols]
                
                safe_print(f"[FEATURES] Using {len(feature_cols)} features")
                
                # Fill missing values with 0
                X = X.fillna(0)
                
                # Train/Validation split
                try:
                    X_train, X_val, y_train, y_val = train_test_split(
                        X, y, test_size=0.2, random_state=42, stratify=y
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
                    'objective': 'binary',
                    'metric': 'auc',
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
                y_pred_proba = model.predict(X_val, num_iteration=model.best_iteration)
                y_pred = (y_pred_proba >= 0.5).astype(int)
                
                acc = accuracy_score(y_val, y_pred)
                prec = precision_score(y_val, y_pred, zero_division=0)
                rec = recall_score(y_val, y_pred, zero_division=0)
                f1 = f1_score(y_val, y_pred, zero_division=0)
                auc = roc_auc_score(y_val, y_pred_proba)
                
                safe_print(f"[METRICS] Validation Results:")
                safe_print(f"  - Accuracy:  {acc:.4f}")
                safe_print(f"  - Precision: {prec:.4f}")
                safe_print(f"  - Recall:    {rec:.4f}")
                safe_print(f"  - F1-Score:  {f1:.4f}")
                safe_print(f"  - ROC-AUC:   {auc:.4f}")
                
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
                model_filename = f"{keibajo_name}_{distance_cat}_binary_model.txt"
                model_path = output_path / model_filename
                model.save_model(str(model_path))
                safe_print(f"[SAVED] Model: {model_path}")
                
                # Save metadata
                metadata = {
                    'model_type': 'binary',
                    'target': 'target',
                    'keibajo': keibajo_name,
                    'distance_category': distance_cat,
                    'n_samples': len(df_cat),
                    'n_features': len(feature_cols),
                    'features': feature_cols,
                    'best_iteration': model.best_iteration,
                    'metrics': {
                        'accuracy': float(acc),
                        'precision': float(prec),
                        'recall': float(rec),
                        'f1_score': float(f1),
                        'roc_auc': float(auc)
                    },
                    'feature_version': '67features',
                    'distance_range': {
                        'SHORT': '≤1200m',
                        'MILE': '1300-1700m',
                        'LONG': '≥1800m'
                    }[distance_cat]
                }
                
                metadata_filename = f"{keibajo_name}_{distance_cat}_binary_metadata.json"
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
    
    safe_print(f"\n{'Racecourse':<12} {'Category':<8} {'Samples':>8} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'AUC':>10}")
    safe_print("-" * 85)
    for result in all_results:
        m = result['metrics']
        safe_print(f"{result['keibajo']:<12} {result['distance_category']:<8} {result['n_samples']:>8,} "
                  f"{m['accuracy']:>10.4f} {m['precision']:>10.4f} "
                  f"{m['recall']:>10.4f} {m['roc_auc']:>10.4f}")
    
    # Average metrics
    avg_acc = np.mean([r['metrics']['accuracy'] for r in all_results])
    avg_prec = np.mean([r['metrics']['precision'] for r in all_results])
    avg_rec = np.mean([r['metrics']['recall'] for r in all_results])
    avg_auc = np.mean([r['metrics']['roc_auc'] for r in all_results])
    
    safe_print("-" * 85)
    safe_print(f"{'Average':<12} {'':<8} {'':<8} {avg_acc:>10.4f} {avg_prec:>10.4f} "
              f"{avg_rec:>10.4f} {avg_auc:>10.4f}")
    
    safe_print(f"\n[COMPLETE] Successfully trained {successful_models}/{total_models} models")
    safe_print(f"[OUTPUT] Models saved to: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Phase 3 Binary Classification Models with Distance Categories')
    parser.add_argument('--input', type=str, required=True, 
                       help='Input directory containing 67-feature CSV files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for trained models')
    
    args = parser.parse_args()
    
    train_binary_model_with_distance(args.input, args.output)
