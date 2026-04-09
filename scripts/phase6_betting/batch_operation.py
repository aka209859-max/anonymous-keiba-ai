# -*- coding: utf-8 -*-
"""
Phase 6 Batch Operation - Python Version
全14競馬場対応の一括処理スクリプト
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def main():
    if len(sys.argv) != 2:
        print("=" * 50)
        print("Keiba AI Batch Processing (Python)")
        print("=" * 50)
        print()
        print("Usage:")
        print("  python batch_operation.py [date]")
        print()
        print("Date Format: YYYY-MM-DD")
        print()
        print("Examples:")
        print("  python batch_operation.py 2026-02-08")
        print("  python batch_operation.py 2026-02-10")
        print()
        print("=" * 50)
        sys.exit(1)
    
    target_date = sys.argv[1]
    date_short = target_date.replace('-', '')
    
    print("=" * 50)
    print("Keiba AI Batch Processing")
    print("=" * 50)
    print()
    print(f"Target Date: {target_date}")
    print()
    print("=" * 50)
    print()
    print("Detecting Phase 5 completed venues...")
    print()
    
    # 競馬場コードとのマッピング
    venue_mapping = {
        30: '門別',
        35: '盛岡',
        36: '水沢',
        42: '浦和',
        43: '船橋',
        44: '大井',
        45: '川崎',
        46: '金沢',
        47: '笠松',
        48: '名古屋',
        50: '園田',
        51: '姫路',
        54: '高知',
        55: '佐賀'
    }
    
    # Phase 5 完了済み競馬場を検出
    detected_venues = []
    for code, name in venue_mapping.items():
        check_file = Path(f"data/predictions/phase5/{name}_{date_short}_ensemble.csv")
        if check_file.exists():
            print(f"[FOUND] {name} - Code {code}")
            detected_venues.append((code, name))
    
    if not detected_venues:
        print()
        print("[ERROR] No Phase 5 data found")
        print()
        print("Please check:")
        print("  - Run Phase 0-5 first")
        print("  - Check data/predictions/phase5/ folder")
        print(f"  - Verify date: {target_date}")
        print()
        sys.exit(1)
    
    print()
    print(f"Detected {len(detected_venues)} venue(s)")
    print()
    print("=" * 50)
    
    success_count = 0
    fail_count = 0
    
    for code, name in detected_venues:
        print()
        print("-" * 50)
        print(f"Processing {name} (Code: {code})...")
        print("-" * 50)
        
        # Phase 6 処理を実行
        ensemble_csv = f"data/predictions/phase5/{name}_{date_short}_ensemble.csv"
        note_txt = f"predictions/{name}_{date_short}_note.txt"
        bookers_txt = f"predictions/{name}_{date_short}_bookers.txt"
        tweet_txt = f"predictions/{name}_{date_short}_tweet.txt"
        
        print(f"Input : {ensemble_csv}")
        print(f"Output: {note_txt}")
        print(f"        {bookers_txt}")
        print(f"        {tweet_txt}")
        print()
        
        try:
            # Note生成
            print("[1/3] Generating Note format...")
            subprocess.run([
                "python", "scripts/phase6_betting/generate_distribution_note.py",
                ensemble_csv, note_txt
            ], check=True)
            print(f"[OK] Note: {note_txt}")
            print()
            
            # Bookers生成
            print("[2/3] Generating Bookers format...")
            subprocess.run([
                "python", "scripts/phase6_betting/generate_distribution_bookers.py",
                ensemble_csv, bookers_txt
            ], check=True)
            print(f"[OK] Bookers: {bookers_txt}")
            print()
            
            # Tweet生成
            print("[3/3] Generating Tweet format...")
            subprocess.run([
                "python", "scripts/phase6_betting/generate_distribution_tweet.py",
                ensemble_csv, tweet_txt
            ], check=True)
            print(f"[OK] Tweet: {tweet_txt}")
            print()
            
            print(f"[OK] {name} complete")
            success_count += 1
            
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] {name} - Error: {e}")
            fail_count += 1
    
    print()
    print("=" * 50)
    print("Processing Summary")
    print("=" * 50)
    print()
    print(f"Success: {success_count} venues")
    print(f"Failed: {fail_count} venues")
    print()
    print("=" * 50)
    
    if fail_count > 0:
        print()
        print("WARNING: Some venues failed")
        print()
    
    if success_count > 0:
        print()
        print("Generated Files:")
        print()
        print("[Note Format]")
        for code, name in detected_venues:
            note_file = Path(f"predictions/{name}_{date_short}_note.txt")
            if note_file.exists():
                print(f"  - {name}_{date_short}_note.txt")
        print()
        print("[Bookers Format]")
        for code, name in detected_venues:
            bookers_file = Path(f"predictions/{name}_{date_short}_bookers.txt")
            if bookers_file.exists():
                print(f"  - {name}_{date_short}_bookers.txt")
        print()
        print("[Tweet Format]")
        for code, name in detected_venues:
            tweet_file = Path(f"predictions/{name}_{date_short}_tweet.txt")
            if tweet_file.exists():
                print(f"  - {name}_{date_short}_tweet.txt")
        print()
        print("Next: Open predictions folder")
        print()
    
    print("=" * 50)


if __name__ == "__main__":
    main()
