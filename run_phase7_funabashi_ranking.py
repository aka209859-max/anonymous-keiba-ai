#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Phase 7 Ranking feature selection for Funabashi
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    print("=" * 80)
    print("Phase 7 Ranking Feature Selection - Funabashi Test")
    print("=" * 80)
    print("\nTarget data: funabashi_2020-2026_with_time_PHASE78.csv")
    print("Purpose: Select optimal features for Ranking model")
    print("Estimated time: 10-20 minutes\n")
    
    # Check input file
    input_file = Path("data/training/funabashi_2020-2026_with_time_PHASE78.csv")
    if not input_file.exists():
        print("[ERROR] Input file not found:")
        print(f"  {input_file}")
        print("\nPlease run one of the following first:")
        print("  - GENERATE_ALL_TRAINING_DATA.bat")
        print("  - python generate_all_training_data.py")
        return 1
    
    print(f"[OK] Input file verified: {input_file}")
    
    # Create output directories
    os.makedirs("data/features/selected", exist_ok=True)
    os.makedirs("data/reports/phase7_feature_selection", exist_ok=True)
    
    print("\n" + "=" * 80)
    print("Starting Phase 7 Ranking feature selection...")
    print("=" * 80 + "\n")
    
    # Run Phase 7 Ranking
    cmd = [
        'python',
        'scripts/phase7_feature_selection/run_boruta_ranking.py',
        str(input_file),
        '--max-iter', '100'
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 80)
        print("[OK] Funabashi Phase 7 Ranking feature selection completed!")
        print("=" * 80)
        print("\nOutput files:")
        print("  - data/features/selected/funabashi_ranking_selected_features.csv")
        print("  - data/reports/phase7_feature_selection/funabashi_ranking_importance.png")
        print("  - data/reports/phase7_feature_selection/funabashi_ranking_report.json")
        print("\nNext steps:")
        print("  1. Check feature importance graph")
        print("  2. Run Phase 7 Regression")
        print("  3. Run Phase 8 Optuna optimization")
        print("=" * 80)
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 80)
        print("[ERROR] An error occurred")
        print("=" * 80)
        print("\nTroubleshooting:")
        print("  1. Verify data file structure")
        print("  2. Check if required Python packages are installed:")
        print("     pip install boruta scikit-learn pandas numpy matplotlib")
        print("  3. Try reducing --max-iter:")
        print("     python run_phase7_funabashi_ranking.py --max-iter 50")
        print("=" * 80)
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
