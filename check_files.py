#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_files.py
Phase 5.5 実行前のファイル確認スクリプト
"""

import os
from pathlib import Path

def check_files():
    """必要なファイルの存在を確認"""
    print("\n" + "="*80)
    print("📋 Phase 5.5 実行前のファイル確認")
    print("="*80)
    
    # 現在のディレクトリ
    current_dir = Path.cwd()
    print(f"\n📁 現在のディレクトリ: {current_dir}")
    
    # 必要なファイル
    files_to_check = {
        "Phase 5 アンサンブル": current_dir / "predictions" / "phase5_ooi_2025" / "ooi_2025_phase5_ensemble.csv",
        "実払戻金CSV": current_dir / "ooi_2025_payouts.csv",
        "バックテストスクリプト": current_dir / "phase5_5_backtest_with_csv.py"
    }
    
    print("\n📊 ファイル存在確認:")
    all_exist = True
    
    for name, path in files_to_check.items():
        exists = path.exists()
        status = "✅" if exists else "❌"
        size = f"({path.stat().st_size:,} bytes)" if exists else "(ファイルなし)"
        print(f"   {status} {name}: {path} {size}")
        
        if not exists:
            all_exist = False
    
    print("\n" + "="*80)
    
    if all_exist:
        print("✅ すべてのファイルが揃っています！")
        print("\n🚀 次のコマンドで実行できます:")
        print("   python phase5_5_backtest_with_csv.py")
    else:
        print("❌ 一部のファイルが不足しています")
        print("\n📥 不足しているファイルをダウンロードしてください:")
        
        for name, path in files_to_check.items():
            if not path.exists():
                print(f"\n   {name}:")
                print(f"   → 保存先: {path}")
                
                # ディレクトリが存在しない場合の作成コマンドを提案
                parent_dir = path.parent
                if not parent_dir.exists():
                    print(f"   → ディレクトリ作成: mkdir {parent_dir}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    check_files()
