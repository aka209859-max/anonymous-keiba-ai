#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Statistical Features to Existing 50-feature CSV
Purpose: Upgrade 50-feature CSV to 67-feature CSV by adding 17 statistical features
Author: AI Assistant
Date: 2026-05-05
"""

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

def add_statistical_features(input_csv, output_csv, encoding='shift-jis'):
    """
    Add 17 statistical features to existing 50-feature CSV
    
    Args:
        input_csv: Path to input CSV (50 features)
        output_csv: Path to output CSV (67 features)
        encoding: CSV encoding (default: shift-jis)
    """
    
    print(f"Loading CSV: {input_csv}")
    
    # Try Shift-JIS first, fallback to UTF-8
    try:
        df = pd.read_csv(input_csv, encoding='shift-jis')
        print(f"[OK] Loaded with Shift-JIS encoding")
    except:
        try:
            df = pd.read_csv(input_csv, encoding='utf-8')
            print(f"[OK] Loaded with UTF-8 encoding")
        except Exception as e:
            print(f"[ERROR] Error loading CSV: {e}")
            sys.exit(1)
    
    print(f"Records: {len(df)}, Columns: {len(df.columns)}")
    
    # ========================================
    # Calculate Statistical Features
    # ========================================
    
    print("\n" + "="*50)
    print("Calculating Statistical Features...")
    print("="*50)
    
    # --- Simple Average Features (11) ---
    
    # 1. recent5_avg_rank - Average rank of last 5 races
    print("1. recent5_avg_rank - Average rank of last 5 races")
    rank_cols = ['prev1_rank', 'prev2_rank', 'prev3_rank', 'prev4_rank', 'prev5_rank']
    df['recent5_avg_rank'] = df[rank_cols].replace(0, np.nan).mean(axis=1)
    
    # 2. recent5_top3_rate - Top 3 finish rate in last 5 races
    print("2. recent5_top3_rate - Top 3 finish rate in last 5 races")
    top3_mask = df[rank_cols].replace(0, np.nan).apply(lambda x: (x <= 3).sum() / x.notna().sum(), axis=1)
    df['recent5_top3_rate'] = top3_mask
    
    # 3. recent5_win_rate - Win rate in last 5 races
    print("3. recent5_win_rate - Win rate in last 5 races")
    win_mask = df[rank_cols].replace(0, np.nan).apply(lambda x: (x == 1).sum() / x.notna().sum(), axis=1)
    df['recent5_win_rate'] = win_mask
    
    # 4. recent5_avg_time - Average time of last 5 races
    print("4. recent5_avg_time - Average time of last 5 races")
    time_cols = ['prev1_time', 'prev2_time', 'prev3_time', 'prev4_time', 'prev5_time']
    df['recent5_avg_time'] = df[time_cols].replace(0, np.nan).mean(axis=1)
    
    # 5. recent5_time_std - Time standard deviation of last 5 races
    print("5. recent5_time_std - Time standard deviation of last 5 races")
    df['recent5_time_std'] = df[time_cols].replace(0, np.nan).std(axis=1)
    
    # 6-8. Popularity/Prize features (not available in current CSV, set to 0)
    print("6-8. recent5_avg_popularity, recent5_favorites_rate, recent5_avg_prize (not available, set to 0)")
    df['recent5_avg_popularity'] = 0
    df['recent5_favorites_rate'] = 0
    df['recent5_avg_prize'] = 0
    
    # 9. trend_rank_change - Rank trend (prev1 - prev5)
    print("9. trend_rank_change - Rank trend (prev1 - prev5)")
    df['trend_rank_change'] = df['prev1_rank'].replace(0, np.nan) - df['prev5_rank'].replace(0, np.nan)
    
    # 10. distance_change - Distance change from previous race
    print("10. distance_change - Distance change from previous race")
    df['distance_change'] = df['kyori'] - df['prev1_kyori'].replace(0, np.nan)
    
    # 11. track_change - Track change rate (1 if different, 0 if same)
    print("11. track_change - Track change rate")
    df['track_change'] = (df['track_code'] != df['prev1_track'].replace(0, np.nan)).astype(float)
    
    # --- Weighted Average Features (6) ---
    
    # Weights: [5, 4, 3, 2, 1] for [prev1, prev2, prev3, prev4, prev5]
    weights = np.array([5, 4, 3, 2, 1])
    
    # 12. recent5_weighted_avg_rank - Weighted average rank
    print("12. recent5_weighted_avg_rank - Weighted average rank")
    rank_values = df[rank_cols].replace(0, np.nan).values
    rank_weights = np.where(np.isnan(rank_values), 0, weights)
    weighted_rank_sum = np.nansum(rank_values * rank_weights, axis=1)
    weight_sum = np.sum(rank_weights, axis=1)
    df['recent5_weighted_avg_rank'] = np.where(weight_sum > 0, weighted_rank_sum / weight_sum, np.nan)
    
    # 13. recent5_weighted_avg_time - Weighted average time
    print("13. recent5_weighted_avg_time - Weighted average time")
    time_values = df[time_cols].replace(0, np.nan).values
    time_weights = np.where(np.isnan(time_values), 0, weights)
    weighted_time_sum = np.nansum(time_values * time_weights, axis=1)
    weight_sum = np.sum(time_weights, axis=1)
    df['recent5_weighted_avg_time'] = np.where(weight_sum > 0, weighted_time_sum / weight_sum, np.nan)
    
    # 14. recent3_avg_rank - Average rank of last 3 races
    print("14. recent3_avg_rank - Average rank of last 3 races")
    recent3_rank_cols = ['prev1_rank', 'prev2_rank', 'prev3_rank']
    df['recent3_avg_rank'] = df[recent3_rank_cols].replace(0, np.nan).mean(axis=1)
    
    # 15. recent3_top3_rate - Top 3 finish rate in last 3 races
    print("15. recent3_top3_rate - Top 3 finish rate in last 3 races")
    recent3_top3 = df[recent3_rank_cols].replace(0, np.nan).apply(lambda x: (x <= 3).sum() / x.notna().sum(), axis=1)
    df['recent3_top3_rate'] = recent3_top3
    
    # 16. form_trend - Form trend (weighted_avg_rank - avg_rank)
    print("16. form_trend - Form trend (weighted_avg_rank - avg_rank)")
    df['form_trend'] = df['recent5_weighted_avg_rank'] - df['recent5_avg_rank']
    
    # 17. consistency_score - Consistency score (1 / (time_std + 1))
    print("17. consistency_score - Consistency score")
    df['consistency_score'] = 1 / (df['recent5_time_std'].fillna(0) + 1)
    
    # Fill NaN with 0 for statistical features
    stat_feature_cols = [
        'recent5_avg_rank', 'recent5_top3_rate', 'recent5_win_rate',
        'recent5_avg_time', 'recent5_time_std', 'recent5_avg_popularity',
        'recent5_favorites_rate', 'recent5_avg_prize', 'trend_rank_change',
        'distance_change', 'track_change', 'recent5_weighted_avg_rank',
        'recent5_weighted_avg_time', 'recent3_avg_rank', 'recent3_top3_rate',
        'form_trend', 'consistency_score'
    ]
    
    print("\nFilling NaN values with 0 for statistical features...")
    df[stat_feature_cols] = df[stat_feature_cols].fillna(0)
    
    # ========================================
    # Summary Statistics
    # ========================================
    
    print("\n" + "="*50)
    print("Summary Statistics")
    print("="*50)
    
    print(f"\nSample statistics (non-zero values):")
    for col in stat_feature_cols[:5]:  # Show first 5 features
        non_zero = df[col][df[col] != 0]
        if len(non_zero) > 0:
            print(f"{col:30s}: mean={non_zero.mean():.2f}, min={non_zero.min():.2f}, max={non_zero.max():.2f}")
        else:
            print(f"{col:30s}: all zeros")
    
    # ========================================
    # Save Output CSV
    # ========================================
    
    print(f"\n{'='*50}")
    print(f"Saving CSV: {output_csv}")
    print(f"{'='*50}")
    
    # Create output directory if needed
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created directory: {output_dir}")
    
    # Save with encoding
    try:
        df.to_csv(output_csv, index=False, encoding='shift-jis')
        print(f"[OK] Saved with Shift-JIS encoding")
    except:
        df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"[OK] Saved with UTF-8 encoding")
    
    print(f"\nFinal dataset:")
    print(f"  Records: {len(df)}")
    print(f"  Columns: {len(df.columns)} (50 original + 17 statistical = 67 total)")
    print(f"  Output: {output_csv}")
    
    print("\n" + "="*50)
    print("[SUCCESS] Statistical Features Added Successfully!")
    print("="*50)
    
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_statistical_features.py <input_csv> [output_csv]")
        print("\nExample:")
        print("  python add_statistical_features.py urawa_2020-2025_v3.csv urawa_2020-2025_v4_67features.csv")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    
    # Default output path
    if len(sys.argv) >= 3:
        output_csv = sys.argv[2]
    else:
        # Auto-generate output filename
        base_name = os.path.basename(input_csv)
        output_csv = base_name.replace('.csv', '_67features.csv')
    
    # Execute
    add_statistical_features(input_csv, output_csv)
