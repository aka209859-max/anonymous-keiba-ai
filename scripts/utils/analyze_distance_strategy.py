#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze distance distribution and recommend model strategy
"""

import pandas as pd
from collections import defaultdict

# Raw data from user output
data = {
    'URAWA': {800: 5580, 1300: 428, 1400: 22531, 1500: 11431, 1600: 203, 1900: 10, 2000: 3120},
    'FUNABASHI': {1000: 3062, 1200: 20016, 1500: 10014, 1600: 7054, 1700: 893, 1800: 1717, 2200: 1545, 2400: 75},
    'KAWASAKI': {900: 9127, 1400: 18220, 1500: 13246, 1600: 5575, 2000: 3356, 2100: 616},
    'OOI': {1000: 367, 1200: 16701, 1400: 8251, 1600: 11257, 1650: 605, 1700: 292, 1800: 2147, 2000: 1072, 2400: 63, 2600: 87},
    'MORIOKA': {1000: 5946, 1200: 12521, 1400: 11998, 1600: 10579, 1700: 792, 1800: 704, 2000: 306, 2400: 110, 2500: 10, 2600: 18},
    'MIZUSAWA': {850: 6650, 1300: 9934, 1400: 15452, 1600: 8960, 1800: 128, 1900: 200, 2000: 193, 2500: 27},
    'MONBETSU': {1000: 20498, 1100: 2932, 1200: 21263, 1500: 665, 1600: 2338, 1700: 6403, 1800: 2484, 2000: 393, 2600: 41},
    'KANAZAWA': {900: 638, 1400: 23345, 1500: 24054, 1700: 2463, 1900: 300, 2000: 339, 2100: 147, 2600: 48},
    'KASAMATSU': {800: 1922, 1400: 35778, 1600: 8476, 1800: 346, 1900: 485, 2500: 55},
    'NAGOYA': {800: 27, 900: 215, 920: 4736, 1400: 6382, 1500: 38244, 1600: 495, 1700: 7348, 1800: 92, 1900: 24, 2000: 771, 2100: 222},
    'SONODA': {820: 8445, 1230: 11900, 1400: 67760, 1700: 5265, 1870: 3014, 2400: 90},
    'HIMEJI': {800: 2097, 1400: 12378, 1500: 2605, 1800: 776, 2000: 215},
    'KOCHI': {800: 1052, 1300: 26889, 1400: 34078, 1600: 9100, 1800: 334, 1900: 459, 2400: 72},
    'SAGA': {900: 3806, 1300: 23936, 1400: 41178, 1750: 3632, 1800: 2451, 1860: 269, 2000: 516, 2500: 57}
}

def categorize_3way(kyori):
    """3-category split: SHORT/MILE/LONG"""
    if kyori <= 1200:
        return 'SHORT'
    elif kyori <= 1700:
        return 'MILE'
    else:
        return 'LONG'

def categorize_2way(kyori):
    """2-category split: SHORT/OTHERS"""
    if kyori <= 1200:
        return 'SHORT'
    else:
        return 'OTHERS'

def main():
    print("="*100)
    print("DISTANCE DISTRIBUTION ANALYSIS - 14 RACECOURSES")
    print("="*100)
    print()
    
    # Calculate totals
    total_races = sum(sum(dist.values()) for dist in data.values())
    
    # 3-way categorization
    cat3_totals = defaultdict(int)
    cat3_by_venue = {}
    
    # 2-way categorization
    cat2_totals = defaultdict(int)
    cat2_by_venue = {}
    
    # Analyze each venue
    for venue, distances in data.items():
        venue_total = sum(distances.values())
        
        # 3-way
        cat3 = defaultdict(int)
        for kyori, count in distances.items():
            category = categorize_3way(kyori)
            cat3[category] += count
            cat3_totals[category] += count
        cat3_by_venue[venue] = cat3
        
        # 2-way
        cat2 = defaultdict(int)
        for kyori, count in distances.items():
            category = categorize_2way(kyori)
            cat2[category] += count
            cat2_totals[category] += count
        cat2_by_venue[venue] = cat2
    
    # Print summary table
    print(f"{'Venue':<15} {'Total':<10} {'SHORT%':<10} {'MILE%':<10} {'LONG%':<10} {'Main Distance'}")
    print("-" * 100)
    
    for venue, distances in data.items():
        venue_total = sum(distances.values())
        cat3 = cat3_by_venue[venue]
        
        short_pct = (cat3['SHORT'] / venue_total * 100) if venue_total > 0 else 0
        mile_pct = (cat3['MILE'] / venue_total * 100) if venue_total > 0 else 0
        long_pct = (cat3['LONG'] / venue_total * 100) if venue_total > 0 else 0
        
        # Find main distance
        main_dist = max(distances.items(), key=lambda x: x[1])
        
        print(f"{venue:<15} {venue_total:<10,} {short_pct:<9.1f}% {mile_pct:<9.1f}% {long_pct:<9.1f}% {main_dist[0]}m ({main_dist[1]:,} races)")
    
    print()
    print("="*100)
    print("OVERALL STATISTICS")
    print("="*100)
    print()
    
    print(f"Total races: {total_races:,}")
    print()
    
    print("【3-Category Split】 SHORT (≤1200m) / MILE (1300-1700m) / LONG (1800m+)")
    print(f"  SHORT: {cat3_totals['SHORT']:>8,} races ({cat3_totals['SHORT']/total_races*100:>5.1f}%)")
    print(f"  MILE:  {cat3_totals['MILE']:>8,} races ({cat3_totals['MILE']/total_races*100:>5.1f}%)")
    print(f"  LONG:  {cat3_totals['LONG']:>8,} races ({cat3_totals['LONG']/total_races*100:>5.1f}%)")
    print()
    
    print("【2-Category Split】 SHORT (≤1200m) / OTHERS (1300m+)")
    print(f"  SHORT:  {cat2_totals['SHORT']:>8,} races ({cat2_totals['SHORT']/total_races*100:>5.1f}%)")
    print(f"  OTHERS: {cat2_totals['OTHERS']:>8,} races ({cat2_totals['OTHERS']/total_races*100:>5.1f}%)")
    print()
    
    # Calculate minimum samples per model
    print("="*100)
    print("MODEL STRATEGY ANALYSIS")
    print("="*100)
    print()
    
    # Option 1: Racecourse only (42 models)
    min_samples_option1 = min(sum(dist.values()) for dist in data.values())
    avg_samples_option1 = total_races / 14
    
    print("【Option 1】 Racecourse-only models (current approach)")
    print(f"  Models: 14 racecourses × 3 types = 42 models")
    print(f"  Training time: ~8-12 hours")
    print(f"  Samples per model: {min_samples_option1:,} ~ {int(avg_samples_option1):,} (avg: {int(avg_samples_option1):,})")
    print(f"  Pros: Sufficient data, fast training, distance learned as feature")
    print(f"  Cons: Cannot capture distance-specific patterns explicitly")
    print()
    
    # Option 2: 2-category split (84 models)
    min_samples_option2 = float('inf')
    for venue, cat2 in cat2_by_venue.items():
        for category, count in cat2.items():
            if count > 0:
                min_samples_option2 = min(min_samples_option2, count)
    
    print("【Option 2】 2-Category distance models")
    print(f"  Models: 14 racecourses × 2 categories × 3 types = 84 models")
    print(f"  Training time: ~17-20 hours")
    print(f"  Minimum samples per model: {min_samples_option2:,}")
    print(f"  Pros: Separates short/long distance patterns")
    print(f"  Cons: Longer training, some categories have limited data")
    print()
    
    # Option 3: 3-category split (126 models)
    min_samples_option3 = float('inf')
    problematic_venues = []
    for venue, cat3 in cat3_by_venue.items():
        for category, count in cat3.items():
            if count > 0:
                min_samples_option3 = min(min_samples_option3, count)
                if count < 1000:
                    problematic_venues.append(f"{venue}_{category}={count:,}")
    
    print("【Option 3】 3-Category distance models")
    print(f"  Models: 14 racecourses × 3 categories × 3 types = 126 models")
    print(f"  Training time: ~25-30 hours")
    print(f"  Minimum samples per model: {min_samples_option3:,}")
    print(f"  Pros: Maximum distance-specific modeling")
    print(f"  Cons: Long training, many categories have insufficient data (<1000 samples)")
    if problematic_venues:
        print(f"  ⚠ Categories with <1000 samples: {len(problematic_venues)}")
        for pv in problematic_venues[:10]:  # Show first 10
            print(f"     - {pv}")
        if len(problematic_venues) > 10:
            print(f"     ... and {len(problematic_venues) - 10} more")
    print()
    
    # Recommendation
    print("="*100)
    print("RECOMMENDATION")
    print("="*100)
    print()
    
    short_pct = cat3_totals['SHORT'] / total_races * 100
    long_pct = cat3_totals['LONG'] / total_races * 100
    
    if short_pct > 25 and long_pct > 10 and min_samples_option3 >= 1000:
        print("✅ RECOMMENDED: Option 3 (3-category distance models)")
        print("   Reason: Sufficient data in all categories, clear distance patterns")
    elif short_pct > 20 and min_samples_option2 >= 2000:
        print("✅ RECOMMENDED: Option 2 (2-category distance models)")
        print("   Reason: Short distance is significant, adequate data for split")
    else:
        print("✅ RECOMMENDED: Option 1 (racecourse-only models)")
        print("   Reason: Most balanced approach, sufficient data, reasonable training time")
        print("   Note: LightGBM will learn distance patterns through 'kyori' feature")
    
    print()
    print(f"Key factors:")
    print(f"  - SHORT distance proportion: {short_pct:.1f}%")
    print(f"  - LONG distance proportion: {long_pct:.1f}%")
    print(f"  - Minimum samples (3-cat): {min_samples_option3:,}")
    print(f"  - Minimum samples (2-cat): {min_samples_option2:,}")

if __name__ == "__main__":
    main()
