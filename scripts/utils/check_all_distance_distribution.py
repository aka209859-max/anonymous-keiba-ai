#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check distance distribution for all 14 racecourses
"""

import pandas as pd
from pathlib import Path
import sys
import json

def check_distance_distribution(csv_path):
    """Check distance distribution for a single racecourse"""
    try:
        df = pd.read_csv(csv_path, encoding='shift-jis')
        if 'kyori' not in df.columns:
            return None
        
        dist_counts = df['kyori'].value_counts().sort_index()
        total = len(df)
        
        result = {
            'total': total,
            'distances': {}
        }
        
        for kyori, count in dist_counts.items():
            result['distances'][int(kyori)] = {
                'count': int(count),
                'percentage': round(count / total * 100, 1)
            }
        
        return result
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None

def categorize_distance(kyori):
    """Categorize distance into short/mile/long"""
    if kyori <= 1200:
        return 'SHORT'
    elif kyori <= 1600:
        return 'MILE'
    else:
        return 'LONG'

def main():
    # Find all CSV files
    data_dir = Path('.')
    output_file = None
    
    # Parse arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--input' and i + 1 < len(sys.argv):
            data_dir = Path(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            data_dir = Path(sys.argv[i])
            i += 1
    
    csv_files = sorted(data_dir.glob('*_2020-2025_v3.csv')) + sorted(data_dir.glob('*_2023-2025_v3.csv')) + sorted(data_dir.glob('*_2022-2025_v3.csv'))
    
    if not csv_files:
        print("ERROR: No CSV files found!")
        print(f"Searched in: {data_dir.absolute()}")
        return
    
    print("="*80)
    print("Distance Distribution Analysis for All Racecourses")
    print("="*80)
    print()
    
    all_results = {}
    
    for csv_file in csv_files:
        # Extract racecourse name
        keibajo_name = csv_file.stem.split('_')[0]
        
        print(f"{'='*80}")
        print(f"Racecourse: {keibajo_name.upper()}")
        print(f"{'='*80}")
        
        result = check_distance_distribution(csv_file)
        
        if result is None:
            print("  [ERROR] Failed to read file")
            continue
        
        all_results[keibajo_name] = result
        
        print(f"Total races: {result['total']:,}")
        print()
        print(f"{'Distance':<10} {'Count':<10} {'Percentage':<12} {'Category':<10}")
        print("-" * 50)
        
        # Categorize distances
        categories = {'SHORT': 0, 'MILE': 0, 'LONG': 0}
        
        for kyori, data in sorted(result['distances'].items()):
            category = categorize_distance(kyori)
            categories[category] += data['count']
            print(f"{kyori:<10} {data['count']:<10,} {data['percentage']:<11.1f}% {category:<10}")
        
        print("-" * 50)
        print()
        print("Category Summary:")
        total = result['total']
        print(f"  SHORT (~1200m):  {categories['SHORT']:>7,} ({categories['SHORT']/total*100:>5.1f}%)")
        print(f"  MILE (1300-1600): {categories['MILE']:>7,} ({categories['MILE']/total*100:>5.1f}%)")
        print(f"  LONG (1700m+):   {categories['LONG']:>7,} ({categories['LONG']/total*100:>5.1f}%)")
        print()
    
    # Overall summary
    print("="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print()
    print(f"{'Racecourse':<15} {'Total':<10} {'SHORT%':<10} {'MILE%':<10} {'LONG%':<10}")
    print("-" * 80)
    
    for keibajo_name, result in all_results.items():
        categories = {'SHORT': 0, 'MILE': 0, 'LONG': 0}
        total = result['total']
        
        for kyori, data in result['distances'].items():
            category = categorize_distance(kyori)
            categories[category] += data['count']
        
        short_pct = categories['SHORT'] / total * 100
        mile_pct = categories['MILE'] / total * 100
        long_pct = categories['LONG'] / total * 100
        
        print(f"{keibajo_name:<15} {total:<10,} {short_pct:<9.1f}% {mile_pct:<9.1f}% {long_pct:<9.1f}%")
    
    print()
    print("="*80)
    print("RECOMMENDATION")
    print("="*80)
    print()
    
    # Calculate average category distribution
    total_races = sum(r['total'] for r in all_results.values())
    total_short = sum(sum(data['count'] for k, data in r['distances'].items() if categorize_distance(k) == 'SHORT') for r in all_results.values())
    total_mile = sum(sum(data['count'] for k, data in r['distances'].items() if categorize_distance(k) == 'MILE') for r in all_results.values())
    total_long = sum(sum(data['count'] for k, data in r['distances'].items() if categorize_distance(k) == 'LONG') for r in all_results.values())
    
    print(f"Total races across all racecourses: {total_races:,}")
    print(f"  SHORT (~1200m):  {total_short:>7,} ({total_short/total_races*100:>5.1f}%)")
    print(f"  MILE (1300-1600): {total_mile:>7,} ({total_mile/total_races*100:>5.1f}%)")
    print(f"  LONG (1700m+):   {total_long:>7,} ({total_long/total_races*100:>5.1f}%)")
    print()
    
    if total_short / total_races > 0.10 and total_long / total_races > 0.05:
        print("RECOMMENDATION: Use 3 distance categories (SHORT/MILE/LONG)")
        print("  - Models: 14 racecourses x 3 distances x 3 types = 126 models")
        print("  - Training time: ~25-30 hours")
    elif total_short / total_races > 0.10:
        print("RECOMMENDATION: Use 2 distance categories (SHORT/OTHERS)")
        print("  - Models: 14 racecourses x 2 distances x 3 types = 84 models")
        print("  - Training time: ~17-20 hours")
    else:
        print("RECOMMENDATION: Use racecourse-only models")
        print("  - Models: 14 racecourses x 3 types = 42 models")
        print("  - Training time: ~8-12 hours")
        print("  - Note: Distance will be learned as a feature")
    
    # Save to JSON if output file specified
    if output_file:
        output_data = {
            'racecourses': all_results,
            'summary': {
                'total_races': total_races,
                'category_distribution': {
                    'SHORT': {'count': total_short, 'percentage': round(total_short/total_races*100, 1)},
                    'MILE': {'count': total_mile, 'percentage': round(total_mile/total_races*100, 1)},
                    'LONG': {'count': total_long, 'percentage': round(total_long/total_races*100, 1)}
                }
            }
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print()
        print(f"Results saved to: {output_path.absolute()}")

if __name__ == "__main__":
    main()
