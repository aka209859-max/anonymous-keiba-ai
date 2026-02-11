#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 7 Binary: Funabashi Binary Feature Selection
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 80)
    print("Phase 7 Binary: Funabashi Feature Selection Test")
    print("=" * 80)
    print()
    
    # Paths
    base_dir = Path(__file__).parent
    input_file = base_dir / "data" / "training" / "funabashi_2020-2026_with_time_PHASE78.csv"
    output_dir = base_dir / "data" / "features" / "selected"
    report_dir = base_dir / "data" / "reports" / "phase7_feature_selection"
    
    # Script path
    script = base_dir / "scripts" / "phase7_feature_selection" / "run_boruta_selection.py"
    
    print(f"Target data: funabashi_2020-2026_with_time_PHASE78.csv")
    print(f"Input file: {input_file}")
    print()
    
    # Verify input file exists
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        print()
        print("Please generate it first:")
        print(f"  python extract_training_data_v2.py --keibajo 43 --start-date 2020 --end-date 2026 --output {input_file}")
        return 1
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    print("✓ Input file exists")
    print(f"✓ Output directory: {output_dir}")
    print(f"✓ Report directory: {report_dir}")
    print()
    
    # Build command
    cmd = [
        sys.executable,
        str(script),
        str(input_file),
        "--max-iter", "100"
    ]
    
    print("Running Phase 7 Binary feature selection...")
    print(f"Command: {' '.join(cmd)}")
    print()
    print("=" * 80)
    print()
    
    # Run the script
    try:
        result = subprocess.run(cmd, check=True)
        print()
        print("=" * 80)
        print("✅ Phase 7 Binary feature selection completed!")
        print()
        print("Output files:")
        print(f"  - Selected features: {output_dir / 'funabashi_selected_features.csv'}")
        print(f"  - Boruta report: {output_dir / 'funabashi_boruta_report.json'}")
        print(f"  - Feature importance: {report_dir / 'funabashi_importance.png'}")
        print(f"  - Analysis report: {report_dir / 'funabashi_report.json'}")
        print()
        print("Next steps:")
        print("  1) Check feature importance graph")
        print("  2) Run Phase 8 Optuna optimization (Binary)")
        print("     Command: python run_phase8_funabashi_binary.py")
        print()
        return 0
        
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 80)
        print(f"❌ Error: Phase 7 Binary failed with exit code {e.returncode}")
        print()
        print("Troubleshooting:")
        print("  1) Verify data file structure")
        print("  2) Install required packages:")
        print("     pip install boruta scikit-learn pandas numpy matplotlib")
        print("  3) Try reducing max-iter (edit --max-iter from 100 to 50)")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
