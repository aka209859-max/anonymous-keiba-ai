#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_race_id.py
テストデータにrace_idカラムを追加
"""

import pandas as pd
import sys

def add_race_id(input_csv, output_csv):
    """
    race_idカラムを追加
    
    Parameters
    ----------
    input_csv : str
        入力CSVファイル
    output_csv : str
        出力CSVファイル
    """
    print(f"\nrace_id追加中...")
    print(f"入力: {input_csv}")
    
    df = pd.read_csv(input_csv)
    print(f"データ件数: {len(df)}")
    
    # race_idを生成
    df['race_id'] = (
        df['kaisai_nen'].astype(str) +
        df['kaisai_tsukihi'].astype(str).str.zfill(4) +
        df['keibajo_code'].astype(str).str.zfill(2) +
        df['race_bango'].astype(str).str.zfill(2)
    )
    
    print(f"race_id生成完了: {df['race_id'].nunique()}レース")
    
    # 保存
    df.to_csv(output_csv, index=False)
    print(f"出力: {output_csv}")
    print("✅ 完了\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用法: python add_race_id.py <input_csv> <output_csv>")
        print("\n例:")
        print("  python add_race_id.py ooi_2025_full_test.csv ooi_2025_full_test_with_race_id.csv")
        sys.exit(1)
    
    add_race_id(sys.argv[1], sys.argv[2])
