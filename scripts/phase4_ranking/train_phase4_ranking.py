#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Ranking Model Training (67 Features)

Purpose: Train ranking models for predicting finish order
Target: rank_target (1=1st, 2=2nd, 3=3rd, ...)
Features: 67 features (50 original + 17 statistical)
Training: Per-racecourse models (14 models total)
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
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

def calc_topk_accuracy(df, k):
    """
    Calculate Top-K accuracy
    
    Args:
        df: DataFrame with 'race_id', 'predicted_rank', 'actual_rank' columns
        k: Top-K threshold
    
    Returns:
        accuracy: Proportion of correctly predicted top-K horses
    """
    total_matches = 0
    total_races = df['race_id'].nunique()
    
    for race_id, group in df.groupby('race_id'):
        # Top-K predicted (smallest predicted_rank)
        top_k_predicted = set(group.nsmallest(k, 'predicted_rank').index)
        # Top-K actual (smallest actual_rank)
        top_k_actual = set(group.nsmallest(k, 'actual_rank').index)
        # Count matches
        matches = len(top_k_predicted & top_k_actual)
        total_matches += matches
    
    # Accuracy = matched horses / (races × k)
    accuracy = total_matches / (total_races * k)
    return accuracy

def train_ranking_model(input_dir: str, output_dir: str):
    """
    Train ranking models per racecourse
    
    Args:
        input_dir: Directory containing 67-feature CSV files
        output_dir: Directory for model output
    """
    safe_print("\n" + "="*80)
    safe_print("Phase 4: Ranking Model Training (67 Features)")
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
            
            # Check required columns
            if 'rank_target' not in df_all.columns:
                safe_print("[ERROR] 'rank_target' column not found")
                continue
            if 'race_id' not in df_all.columns:
                safe_print("[ERROR] 'race_id' column not found")
                continue
            
            # Prepare target (rank as numeric)
            df_all['rank_target'] = pd.to_numeric(df_all['rank_target'], errors='coerce')
            df_all = df_all.dropna(subset=['rank_target'])
            
            # Create group ID for races
            df_all['group'] = df_all.groupby('race_id').ngroup()
            
            safe_print(f"\n[STATS] Dataset statistics:")
            safe_print(f"  - Races: {df_all['race_id'].nunique():,}")
            safe_print(f"  - Total horses: {len(df_all):,}")
            safe_print(f"  - Avg horses/race: {df_all.groupby('race_id').size().mean():.1f}")
            safe_print(f"  - Rank range: {df_all['rank_target'].min():.0f} - {df_all['rank_target'].max():.0f}")
            
            # Exclude columns
            exclude_cols = [
                'target', 'rank_target', 'race_id', 'group',
                'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code',
                'race_bango', 'ketto_toroku_bango', 'umaban',
                'finish_position', 'kakutei_chakujun',
                'time', 'bamei',
                'is_top2', 'is_1st', 'is_2nd', 'grade_code'
            ]
            
            # Select features
            feature_cols = [col for col in df_all.columns if col not in exclude_cols]
            X = df_all[feature_cols].copy()
            y = df_all['rank_target'].values
            
            safe_print(f"\n[FEATURES] Using {len(feature_cols)} features")
            
            # Fill missing values
            X = X.fillna(0)
            
            # Split by race (80/20)
            unique_races = df_all['race_id'].unique()
            np.random.seed(42)
            train_races = np.random.choice(unique_races, size=int(len(unique_races)*0.8), replace=False)
            
            train_mask = df_all['race_id'].isin(train_races)
            val_mask = ~train_mask
            
            X_train, y_train = X[train_mask], y[train_mask]
            X_val, y_val = X[val_mask], y[val_mask]
            
            safe_print(f"\n[SPLIT] Data split:")
            safe_print(f"  - Train: {len(X_train):,} samples ({len(df_all.loc[train_mask, 'race_id'].unique()):,} races)")
            safe_print(f"  - Val:   {len(X_val):,} samples ({len(df_all.loc[val_mask, 'race_id'].unique()):,} races)")
            
            # Group sizes for LambdaRank
            train_group_sizes = df_all[train_mask].groupby('group').size().values
            val_group_sizes = df_all[val_mask].groupby('group').size().values
            
            # Create LightGBM datasets
            train_data = lgb.Dataset(
                X_train,
                label=y_train,
                group=train_group_sizes
            )
            val_data = lgb.Dataset(
                X_val,
                label=y_val,
                group=val_group_sizes,
                reference=train_data
            )
            
            # Hyperparameters (LambdaRank)
            params = {
                'objective': 'lambdarank',
                'metric': 'ndcg',
                'ndcg_eval_at': [1, 3, 5],
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
            
            safe_print("\n[TRAINING] Starting LightGBM training (LambdaRank)...")
            safe_print("  - Objective: lambdarank")
            safe_print("  - Metric: NDCG@1,3,5")
            
            model = lgb.train(
                params,
                train_data,
                num_boost_round=2000,
                valid_sets=[train_data, val_data],
                valid_names=['train', 'val'],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=100),
                    lgb.log_evaluation(period=100)
                ]
            )
            
            safe_print(f"\n[SUCCESS] Training completed ({model.best_iteration} iterations)")
            
            # Prediction
            y_pred = model.predict(X_val, num_iteration=model.best_iteration)
            
            # Rank by race
            val_df = df_all[val_mask].copy()
            val_df['predicted_score'] = y_pred
            val_df['predicted_rank'] = val_df.groupby('race_id')['predicted_score'].rank(ascending=False, method='min')
            val_df['actual_rank'] = val_df['rank_target']
            
            # Calculate Top-K accuracy
            top1_acc = calc_topk_accuracy(val_df, 1)
            top3_acc = calc_topk_accuracy(val_df, 3)
            top5_acc = calc_topk_accuracy(val_df, 5)
            
            safe_print(f"\n[METRICS] Validation Results:")
            safe_print(f"  - Top-1 Accuracy: {top1_acc:.4f}")
            safe_print(f"  - Top-3 Accuracy: {top3_acc:.4f}")
            safe_print(f"  - Top-5 Accuracy: {top5_acc:.4f}")
            
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
            model_path = output_path / f"{keibajo_name}_2020-2025_v3_67features_ranking_model.txt"
            model.save_model(str(model_path))
            safe_print(f"\n[SAVED] Model: {model_path}")
            
            # Save metadata
            metadata = {
                'model_type': 'ranking',
                'target': 'rank_target',
                'n_samples': len(df_all),
                'n_features': len(feature_cols),
                'features': feature_cols,
                'best_iteration': model.best_iteration,
                'metrics': {
                    'top1_accuracy': float(top1_acc),
                    'top3_accuracy': float(top3_acc),
                    'top5_accuracy': float(top5_acc)
                },
                'keibajo': keibajo_name,
                'feature_version': '67features'
            }
            
            metadata_path = output_path / f"{keibajo_name}_2020-2025_v3_67features_ranking_metadata.json"
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
    
    safe_print(f"\n{'Racecourse':<15} {'Samples':>10} {'Top-1':>10} {'Top-3':>10} {'Top-5':>10}")
    safe_print("-" * 80)
    for result in all_results:
        m = result['metrics']
        safe_print(f"{result['keibajo']:<15} {result['n_samples']:>10,} "
                  f"{m['top1_accuracy']:>10.4f} {m['top3_accuracy']:>10.4f} "
                  f"{m['top5_accuracy']:>10.4f}")
    
    # Average metrics
    avg_top1 = np.mean([r['metrics']['top1_accuracy'] for r in all_results])
    avg_top3 = np.mean([r['metrics']['top3_accuracy'] for r in all_results])
    avg_top5 = np.mean([r['metrics']['top5_accuracy'] for r in all_results])
    
    safe_print("-" * 80)
    safe_print(f"{'Average':<15} {'':<10} {avg_top1:>10.4f} {avg_top3:>10.4f} {avg_top5:>10.4f}")
    
    safe_print(f"\n[SUCCESS] Trained {len(all_results)} models successfully!")
    safe_print(f"[OUTPUT] Models saved to: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Phase 4 Ranking Models (67 Features)')
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory containing 67-feature CSV files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for trained models')
    
    args = parser.parse_args()
    
    train_ranking_model(args.input, args.output)
