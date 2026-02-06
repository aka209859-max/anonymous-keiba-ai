#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
debug_merge_key.py
merge_key のデバッグ用スクリプト
"""

import pandas as pd
import sys

def debug_merge_keys(csv1, csv2):
    """両方のCSVの merge_key を比較"""
    
    print(f"\n{'='*80}")
    print(f"merge_key デバッグ")
    print(f"{'='*80}")
    
    # ファイル1読み込み
    print(f"\nファイル1: {csv1}")
    df1 = pd.read_csv(csv1)
    print(f"  件数: {len(df1)}")
    print(f"  カラム: {list(df1.columns[:10])}")
    
    # ファイル2読み込み
    print(f"\nファイル2: {csv2}")
    df2 = pd.read_csv(csv2)
    print(f"  件数: {len(df2)}")
    print(f"  カラム: {list(df2.columns[:10])}")
    
    # merge_key 生成（ファイル1）
    df1['merge_key'] = (
        df1['kaisai_nen'].astype(str) +
        df1['kaisai_tsukihi'].astype(str).str.zfill(4) +
        df1['keibajo_code'].astype(str).str.zfill(2) +
        df1['race_bango'].astype(str).str.zfill(2) +
        df1['ketto_toroku_bango'].astype(str)
    )
    
    # merge_key 生成（ファイル2）
    df2['merge_key'] = (
        df2['kaisai_nen'].astype(str) +
        df2['kaisai_tsukihi'].astype(str).str.zfill(4) +
        df2['keibajo_code'].astype(str).str.zfill(2) +
        df2['race_bango'].astype(str).str.zfill(2) +
        df2['ketto_toroku_bango'].astype(str)
    )
    
    # サンプル表示
    print(f"\n【ファイル1のサンプル merge_key】")
    for i in range(min(5, len(df1))):
        row = df1.iloc[i]
        print(f"  {row['kaisai_nen']}-{row['kaisai_tsukihi']}-{row['keibajo_code']}-{row['race_bango']}-{row['ketto_toroku_bango']} → {row['merge_key']}")
    
    print(f"\n【ファイル2のサンプル merge_key】")
    for i in range(min(5, len(df2))):
        row = df2.iloc[i]
        print(f"  {row['kaisai_nen']}-{row['kaisai_tsukihi']}-{row['keibajo_code']}-{row['race_bango']}-{row['ketto_toroku_bango']} → {row['merge_key']}")
    
    # 共通キーの確認
    common_keys = set(df1['merge_key']) & set(df2['merge_key'])
    print(f"\n【マッチング結果】")
    print(f"  ファイル1のユニークキー数: {df1['merge_key'].nunique()}")
    print(f"  ファイル2のユニークキー数: {df2['merge_key'].nunique()}")
    print(f"  共通キー数: {len(common_keys)}")
    
    if len(common_keys) > 0:
        print(f"\n【共通キーのサンプル（最初の5件）】")
        for i, key in enumerate(list(common_keys)[:5]):
            print(f"  {key}")
    else:
        print(f"\n❌ 共通キーが見つかりません！")
        print(f"\nファイル1の最初のキー: {df1['merge_key'].iloc[0]}")
        print(f"ファイル2の最初のキー: {df2['merge_key'].iloc[0]}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用法: python debug_merge_key.py <csv1> <csv2>")
        sys.exit(1)
    
    debug_merge_keys(sys.argv[1], sys.argv[2])
