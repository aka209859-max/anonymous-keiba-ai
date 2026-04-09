#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8 Regression: Funabashi Regression Model Hyperparameter Optimization
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 80)
    print("Phase 8 Regression: Funabashi Hyperparameter Optimization")
    print("=" * 80)
    print()
    
    # Paths
    base_dir = Path(__file__).parent
    input_file = base_dir / "data" / "training" / "funabashi_2020-2026_with_time_PHASE78.csv"
    selected_features = base_dir / "data" / "features" / "selected" / "funabashi_regression_selected_features.csv"
    output_dir = base_dir / "data" / "models" / "tuned"
    report_dir = base_dir / "data" / "reports" / "phase8_tuning"
    
    # Script path
    script = base_dir / "scripts" / "phase8_auto_tuning" / "run_optuna_tuning_regression.py"
    
    print(f"Target data: funabashi_2020-2026_with_time_PHASE78.csv")
    print(f"Input file: {input_file}")
    print(f"Selected features: {selected_features}")
    print()
    
    # Verify input files exist
    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        return 1
    
    if not selected_features.exists():
        print(f"❌ Error: Selected features file not found: {selected_features}")
        print()
        print("Please run Phase 7 Regression first:")
        print("  python run_phase7_funabashi_regression.py")
        return 1
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    print("✓ Input file exists")
    print("✓ Selected features file exists")
    print(f"✓ Output directory: {output_dir}")
    print(f"✓ Report directory: {report_dir}")
    print()
    
    # Build command
    cmd = [
        sys.executable,
        str(script),
        str(input_file),
        "--selected-features", str(selected_features),
        "--n-trials", "100",
        "--timeout", "7200"  # 2 hours
    ]
    
    print("Running Phase 8 Regression hyperparameter optimization...")
    print(f"Command: {' '.join(cmd)}")
    print()
    print("⏱️  Estimated time: 30-60 minutes")
    print("⚙️  Trials: 100")
    print("⏰ Timeout: 2 hours")
    print()
    print("=" * 80)
    print()
    
    # Run the script
    try:
        result = subprocess.run(cmd, check=True)
        print()
        print("=" * 80)
        print("✅ Phase 8 Regression optimization completed!")
        print()
        print("Output files:")
        print(f"  - Best parameters: {output_dir / 'funabashi_regression_best_params.csv'}")
        print(f"  - Tuned model: {output_dir / 'funabashi_regression_tuned_model.txt'}")
        print(f"  - Optimization history: {report_dir / 'funabashi_regression_optimization_history.png'}")
        print(f"  - Tuning report: {report_dir / 'funabashi_regression_tuning_report.json'}")
        print()
        print("Next steps:")
        print("  1) Check optimization history graph")
        print("  2) Run Phase 5 Ensemble integration")
        print("     Command: python run_phase5_funabashi_ensemble.py")
        print()
        return 0
        
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 80)
        print(f"❌ Error: Phase 8 Regression failed with exit code {e.returncode}")
        print()
        print("Troubleshooting:")
        print("  1) Verify data file structure")
        print("  2) Install required packages:")
        print("     pip install optuna lightgbm scikit-learn pandas numpy matplotlib")
        print("  3) Check disk space and memory")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
