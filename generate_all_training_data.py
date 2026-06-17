#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate training data for all 13 remaining venues (excluding Funabashi)
"""

import subprocess
import sys
from datetime import datetime

# Venue configuration
VENUES = [
    {'code': '30', 'name': 'monbetsu', 'jp_name': '門別'},
    {'code': '33', 'name': 'obihiro', 'jp_name': '帯広'},
    {'code': '35', 'name': 'morioka', 'jp_name': '盛岡'},
    {'code': '36', 'name': 'mizusawa', 'jp_name': '水沢'},
    {'code': '42', 'name': 'urawa', 'jp_name': '浦和'},
    # 43=funabashi already completed
    {'code': '44', 'name': 'ooi', 'jp_name': '大井'},
    {'code': '45', 'name': 'kawasaki', 'jp_name': '川崎'},
    {'code': '46', 'name': 'kanazawa', 'jp_name': '金沢'},
    {'code': '47', 'name': 'kasamatsu', 'jp_name': '笠松'},
    {'code': '48', 'name': 'nagoya', 'jp_name': '名古屋'},
    {'code': '50', 'name': 'sonoda', 'jp_name': '園田'},
    {'code': '51', 'name': 'himeji', 'jp_name': '姫路'},
    {'code': '54', 'name': 'kochi', 'jp_name': '高知'},
    {'code': '55', 'name': 'saga', 'jp_name': '佐賀'},
]


def main():
    print("=" * 80)
    print("Training Data Generation for 13 Venues")
    print("=" * 80)
    print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {len(VENUES)} venues (Funabashi already completed)")
    print(f"Estimated time: 1-2 hours\n")
    
    success_count = 0
    failed_venues = []
    
    for idx, venue in enumerate(VENUES, 1):
        print("=" * 80)
        print(f"[{idx}/{len(VENUES)}] {venue['jp_name']} (Code: {venue['code']}) - Generating...")
        print("=" * 80)
        
        cmd = [
            'python',
            'extract_training_data_v2.py',
            '--keibajo', venue['code'],
            '--start-date', '2020',
            '--end-date', '2026',
            '--output', f"data/training/{venue['name']}_2020-2026_with_time_PHASE78.csv"
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=False, text=True)
            print(f"\n[OK] {venue['jp_name']} completed!\n")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] {venue['jp_name']} failed!\n")
            failed_venues.append(venue['jp_name'])
        except Exception as e:
            print(f"\n[ERROR] {venue['jp_name']} - Unexpected error: {e}\n")
            failed_venues.append(venue['jp_name'])
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Completed: {success_count}/{len(VENUES)} venues")
    print(f"Failed: {len(failed_venues)} venues")
    
    if failed_venues:
        print("\nFailed venues:")
        for venue in failed_venues:
            print(f"  - {venue}")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nOutput directory: data/training/")
    print("\nNext steps:")
    print("  1. Verify generated CSV files")
    print("  2. Run Phase 7 Ranking feature selection")
    print("  3. Run Phase 7 Regression feature selection")
    print("=" * 80)
    
    return 0 if len(failed_venues) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
