#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Binary Classification Model Training (67 Features)

Purpose: Train binary classification models for predicting top-3 finishes
Target: target (1 if top-3, 0 otherwise)
Features: 67 features (50 original + 17 statistical)
Training: Per-racecourse models (14 models total)
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

def train_binary_model(input_dir: str, output_dir: str):
    """
    Train binary classification models per racecourse
    
    Args:
        input_dir: Directory containing 67-feature CSV files
        output_dir: Directory for model output
    """
    safe_print("\n" + "="*80)
    safe_print("Phase 3: Binary Classification Model Training (67 Features)")
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
        # Extract racecourse name from filename
        # Example: urawa_67features.csv -> urawa
        keibajo_name = csv_file.stem.replace('_67features', '')
        
        safe_print(f"\n{'='*80}")
        safe_print(f"[RACECOURSE] {keibajo_name}")
        safe_print(f"{'='*80}")
        
        try:
            # Load data
            df_all = pd.read_csv(csv_file, encoding='shift-jis')
            safe_print(f"[OK] Data loaded: {len(df_all):,} rows x {len(df_all.columns)} columns")
            
            # Check if target column exists
            if 'target' not in df_all.columns:
                safe_print("[ERROR] 'target' column not found")
                continue
            
            # Prepare target variable
            y = df_all['target']
            safe_print(f"\n[TARGET] Distribution:")
            safe_print(f"  - Top-3 (1): {y.sum():,} horses ({y.mean()*100:.1f}%)")
            safe_print(f"  - Others (0): {(~y.astype(bool)).sum():,} horses ({(1-y.mean())*100:.1f}%)")
            
            # Exclude columns
            exclude_cols = [
                'target', 'rank_target', 'time', 'is_1st', 'is_2nd', 'is_top2', 
                'finish_position', 'race_id', 'kaisai_tsukihi', 'ketto_toroku_bango',
                'keibajo_code', 'grade_code'
            ]
            
            # Select features
            feature_cols = [col for col in df_all.columns if col not in exclude_cols]
            X = df_all[feature_cols]
            
            safe_print(f"\n[FEATURES] Using {len(feature_cols)} features")
            
            # Fill missing values with 0
            X = X.fillna(0)
            
            # Train/Validation split
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            safe_print(f"\n[SPLIT] Data split:")
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
            y_pred_proba = model.predict(X_val, num_iteration=model.best_iteration)
            y_pred = (y_pred_proba >= 0.5).astype(int)
            
            acc = accuracy_score(y_val, y_pred)
            prec = precision_score(y_val, y_pred, zero_division=0)
            rec = recall_score(y_val, y_pred, zero_division=0)
            f1 = f1_score(y_val, y_pred, zero_division=0)
            auc = roc_auc_score(y_val, y_pred_proba)
            
            safe_print(f"\n[METRICS] Validation Results:")
            safe_print(f"  - Accuracy:  {acc:.4f}")
            safe_print(f"  - Precision: {prec:.4f}")
            safe_print(f"  - Recall:    {rec:.4f}")
            safe_print(f"  - F1-Score:  {f1:.4f}")
            safe_print(f"  - ROC-AUC:   {auc:.4f}")
            
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
            model_path = output_path / f"{keibajo_name}_2020-2025_v3_67features_model.txt"
            model.save_model(str(model_path))
            safe_print(f"\n[SAVED] Model: {model_path}")
            
            # Save metadata
            metadata = {
                'model_type': 'binary',
                'target': 'target',
                'n_samples': len(df_all),
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
                'keibajo': keibajo_name,
                'feature_version': '67features'
            }
            
            metadata_path = output_path / f"{keibajo_name}_2020-2025_v3_67features_metadata.json"
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
            continue
    
    # Summary
    safe_print("\n" + "="*80)
    safe_print("[SUMMARY] All Racecourses Results")
    safe_print("="*80)
    
    if len(all_results) == 0:
        safe_print("[ERROR] No models were trained successfully!")
        return
    
    safe_print(f"\n{'Racecourse':<15} {'Samples':>10} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'AUC':>10}")
    safe_print("-" * 80)
    for result in all_results:
        m = result['metrics']
        safe_print(f"{result['keibajo']:<15} {result['n_samples']:>10,} "
                  f"{m['accuracy']:>10.4f} {m['precision']:>10.4f} "
                  f"{m['recall']:>10.4f} {m['roc_auc']:>10.4f}")
    
    # Average metrics
    avg_acc = np.mean([r['metrics']['accuracy'] for r in all_results])
    avg_prec = np.mean([r['metrics']['precision'] for r in all_results])
    avg_rec = np.mean([r['metrics']['recall'] for r in all_results])
    avg_auc = np.mean([r['metrics']['roc_auc'] for r in all_results])
    
    safe_print("-" * 80)
    safe_print(f"{'Average':<15} {'':<10} {avg_acc:>10.4f} {avg_prec:>10.4f} "
              f"{avg_rec:>10.4f} {avg_auc:>10.4f}")
    
    safe_print(f"\n[SUCCESS] Trained {len(all_results)} models successfully!")
    safe_print(f"[OUTPUT] Models saved to: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Phase 3 Binary Classification Models (67 Features)')
    parser.add_argument('--input', type=str, required=True, 
                       help='Input directory containing 67-feature CSV files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for trained models')
    
    args = parser.parse_args()
    
    train_binary_model(args.input, args.output)
