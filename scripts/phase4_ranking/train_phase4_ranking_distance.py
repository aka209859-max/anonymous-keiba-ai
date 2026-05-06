#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4: Ranking Model Training with Distance Categories (67 Features)

Purpose: Train ranking models for predicting finish order
Target: rank_target (1=1st, 2=2nd, 3=3rd, ...)
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

def calc_topk_accuracy(df, k):
    """Calculate Top-K accuracy"""
    total_matches = 0
    total_races = df['race_id'].nunique()
    
    for race_id, group in df.groupby('race_id'):
        top_k_predicted = set(group.nsmallest(k, 'predicted_rank').index)
        top_k_actual = set(group.nsmallest(k, 'actual_rank').index)
        matches = len(top_k_predicted & top_k_actual)
        total_matches += matches
    
    accuracy = total_matches / (total_races * k)
    return accuracy

def train_ranking_model_with_distance(input_dir: str, output_dir: str):
    """Train ranking models per racecourse × distance category"""
    
    safe_print("\n" + "="*80)
    safe_print("Phase 4: Ranking Model with Distance Categories (67 Features)")
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
            if 'rank_target' not in df_all.columns:
                safe_print("[ERROR] 'rank_target' column not found")
                continue
            if 'race_id' not in df_all.columns:
                safe_print("[ERROR] 'race_id' column not found")
                continue
            if 'kyori' not in df_all.columns:
                safe_print("[ERROR] 'kyori' column not found")
                continue
            
            # Prepare target
            df_all['rank_target'] = pd.to_numeric(df_all['rank_target'], errors='coerce')
            df_all = df_all.dropna(subset=['rank_target'])
            
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
                
                # Check if race_id exists
                n_races = df_cat['race_id'].nunique()
                if n_races < 10:
                    safe_print(f"[SKIP] Too few races: {n_races} races")
                    continue
                
                safe_print(f"[DATA] Samples: {len(df_cat):,}, Races: {n_races:,}")
                
                # Create group ID for races
                df_cat['group'] = df_cat.groupby('race_id').ngroup()
                
                safe_print(f"[STATS] Dataset statistics:")
                safe_print(f"  - Races: {n_races:,}")
                safe_print(f"  - Total horses: {len(df_cat):,}")
                safe_print(f"  - Avg horses/race: {df_cat.groupby('race_id').size().mean():.1f}")
                safe_print(f"  - Rank range: {df_cat['rank_target'].min():.0f} - {df_cat['rank_target'].max():.0f}")
                
                # Exclude columns
                exclude_cols = [
                    'target', 'rank_target', 'race_id', 'group',
                    'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code',
                    'race_bango', 'ketto_toroku_bango', 'umaban',
                    'finish_position', 'kakutei_chakujun',
                    'time', 'bamei',
                    'is_top2', 'is_1st', 'is_2nd', 'grade_code',
                    'distance_category'
                ]
                
                # Select features
                feature_cols = [col for col in df_cat.columns if col not in exclude_cols]
                X = df_cat[feature_cols].copy()
                y = df_cat['rank_target'].values
                
                safe_print(f"[FEATURES] Using {len(feature_cols)} features")
                
                # Fill missing values
                X = X.fillna(0)
                
                # Split by race (80/20)
                unique_races = df_cat['race_id'].unique()
                if len(unique_races) < 10:
                    safe_print(f"[SKIP] Too few unique races: {len(unique_races)}")
                    continue
                
                np.random.seed(42)
                n_train = max(int(len(unique_races)*0.8), 1)
                train_races = np.random.choice(unique_races, size=n_train, replace=False)
                
                train_mask = df_cat['race_id'].isin(train_races)
                val_mask = ~train_mask
                
                X_train, y_train = X[train_mask], y[train_mask]
                X_val, y_val = X[val_mask], y[val_mask]
                
                if len(X_val) == 0:
                    safe_print(f"[SKIP] Validation set is empty")
                    continue
                
                safe_print(f"[SPLIT] Data split:")
                safe_print(f"  - Train: {len(X_train):,} samples ({len(df_cat.loc[train_mask, 'race_id'].unique()):,} races)")
                safe_print(f"  - Val:   {len(X_val):,} samples ({len(df_cat.loc[val_mask, 'race_id'].unique()):,} races)")
                
                # Group sizes for LambdaRank
                train_group_sizes = df_cat[train_mask].groupby('group').size().values
                val_group_sizes = df_cat[val_mask].groupby('group').size().values
                
                # Create LightGBM datasets
                train_data = lgb.Dataset(X_train, label=y_train, group=train_group_sizes)
                val_data = lgb.Dataset(X_val, label=y_val, group=val_group_sizes, reference=train_data)
                
                # Hyperparameters
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
                
                safe_print("[TRAINING] Starting LightGBM training (LambdaRank)...")
                
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
                
                safe_print(f"[SUCCESS] Training completed ({model.best_iteration} iterations)")
                
                # Prediction
                y_pred = model.predict(X_val, num_iteration=model.best_iteration)
                
                # Rank by race
                val_df = df_cat[val_mask].copy()
                val_df['predicted_score'] = y_pred
                val_df['predicted_rank'] = val_df.groupby('race_id')['predicted_score'].rank(ascending=False, method='min')
                val_df['actual_rank'] = val_df['rank_target']
                
                # Calculate Top-K accuracy
                top1_acc = calc_topk_accuracy(val_df, 1)
                top3_acc = calc_topk_accuracy(val_df, 3)
                top5_acc = calc_topk_accuracy(val_df, 5)
                
                safe_print(f"[METRICS] Validation Results:")
                safe_print(f"  - Top-1 Accuracy: {top1_acc:.4f}")
                safe_print(f"  - Top-3 Accuracy: {top3_acc:.4f}")
                safe_print(f"  - Top-5 Accuracy: {top5_acc:.4f}")
                
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
                model_filename = f"{keibajo_name}_{distance_cat}_ranking_model.txt"
                model_path = output_path / model_filename
                model.save_model(str(model_path))
                safe_print(f"[SAVED] Model: {model_path}")
                
                # Save metadata
                metadata = {
                    'model_type': 'ranking',
                    'target': 'rank_target',
                    'keibajo': keibajo_name,
                    'distance_category': distance_cat,
                    'n_samples': len(df_cat),
                    'n_features': len(feature_cols),
                    'features': feature_cols,
                    'best_iteration': model.best_iteration,
                    'metrics': {
                        'top1_accuracy': float(top1_acc),
                        'top3_accuracy': float(top3_acc),
                        'top5_accuracy': float(top5_acc)
                    },
                    'feature_version': '67features',
                    'distance_range': {
                        'SHORT': '≤1200m',
                        'MILE': '1300-1700m',
                        'LONG': '≥1800m'
                    }[distance_cat]
                }
                
                metadata_filename = f"{keibajo_name}_{distance_cat}_ranking_metadata.json"
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
    
    safe_print(f"\n{'Racecourse':<12} {'Category':<8} {'Samples':>8} {'Top-1':>10} {'Top-3':>10} {'Top-5':>10}")
    safe_print("-" * 85)
    for result in all_results:
        m = result['metrics']
        safe_print(f"{result['keibajo']:<12} {result['distance_category']:<8} {result['n_samples']:>8,} "
                  f"{m['top1_accuracy']:>10.4f} {m['top3_accuracy']:>10.4f} "
                  f"{m['top5_accuracy']:>10.4f}")
    
    # Average metrics
    avg_top1 = np.mean([r['metrics']['top1_accuracy'] for r in all_results])
    avg_top3 = np.mean([r['metrics']['top3_accuracy'] for r in all_results])
    avg_top5 = np.mean([r['metrics']['top5_accuracy'] for r in all_results])
    
    safe_print("-" * 85)
    safe_print(f"{'Average':<12} {'':<8} {'':<8} {avg_top1:>10.4f} {avg_top3:>10.4f} {avg_top5:>10.4f}")
    
    safe_print(f"\n[COMPLETE] Successfully trained {successful_models}/{total_models} models")
    safe_print(f"[OUTPUT] Models saved to: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Phase 4 Ranking Models with Distance Categories')
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory containing 67-feature CSV files')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory for trained models')
    
    args = parser.parse_args()
    
    train_ranking_model_with_distance(args.input, args.output)
