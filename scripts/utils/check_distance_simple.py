#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple distance distribution check for all 14 racecourses
Output format matches: kyori + count (like value_counts().sort_index())
"""

import pandas as pd
from pathlib import Path
import sys

def main():
    # Racecourse list
    racecourses = [
        'urawa', 'funabashi', 'kawasaki', 'ooi',
        'morioka', 'mizusawa', 'monbetsu',
        'kanazawa', 'kasamatsu', 'nagoya',
        'sonoda', 'himeji', 'kochi', 'saga'
    ]
    
    # Get input directory
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    else:
        data_dir = Path('old/data/training_csv')
    
    if not data_dir.exists():
        print(f"ERROR: Directory not found: {data_dir}")
        return
    
    print("="*80)
    print("Distance Distribution for All 14 Racecourses")
    print("="*80)
    print()
    
    for keibajo in racecourses:
        # Try different year ranges
        csv_patterns = [
            f"{keibajo}_2020-2025_v3.csv",
            f"{keibajo}_2023-2025_v3.csv",
            f"{keibajo}_2022-2025_v3.csv"
        ]
        
        csv_file = None
        for pattern in csv_patterns:
            candidate = data_dir / pattern
            if candidate.exists():
                csv_file = candidate
                break
        
        if csv_file is None:
            print(f"【{keibajo.upper()}】")
            print("  File not found")
            print()
            continue
        
        try:
            # Read CSV
            df = pd.read_csv(csv_file, encoding='shift-jis')
            
            if 'kyori' not in df.columns:
                print(f"【{keibajo.upper()}】")
                print("  'kyori' column not found")
                print()
                continue
            
            # Get distance distribution
            dist_counts = df['kyori'].value_counts().sort_index()
            
            # Print result
            print(f"【{keibajo.upper()}】 (Total: {len(df):,} races)")
            print("kyori")
            for kyori, count in dist_counts.items():
                print(f"{int(kyori):<8} {count}")
            print()
            
        except Exception as e:
            print(f"【{keibajo.upper()}】")
            print(f"  ERROR: {e}")
            print()

if __name__ == "__main__":
    main()
