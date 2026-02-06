#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_soha_time.py
テストデータに走破タイムを統合
"""

import pandas as pd
import sys

def parse_soha_time(time_str):
    """
    走破タイムを秒に変換
    
    形式: 4桁 "M秒秒X" (例: "1462" → 1分46.2秒 = 106.2秒)
          ※ 千の位=分, 百十の位=秒, 一の位=0.1秒
    
    Parameters
    ----------
    time_str : str or int
        4桁の走破タイム
    
    Returns
    -------
    float
        走破タイム（秒）
    """
    if pd.isna(time_str) or time_str == '' or time_str == 0:
        return None
    
    try:
        time_int = int(time_str)
        
        # 0は無効データ
        if time_int == 0:
            return None
        
        # 4桁形式: MSSD (M=分, SS=秒, D=0.1秒)
        # 例: 1462 → 1分46.2秒 = 106.2秒
        minutes = time_int // 1000
        seconds = (time_int % 1000) // 10
        deciseconds = time_int % 10
        
        total_seconds = minutes * 60 + seconds + deciseconds / 10.0
        
        return total_seconds
    except:
        return None

def merge_soha_time(test_csv, soha_csv, output_csv):
    """
    テストデータに走破タイムを統合
    
    Parameters
    ----------
    test_csv : str
        元のテストデータCSV
    soha_csv : str
        走破タイムCSV（PC-KEIBAから取得）
    output_csv : str
        出力CSVファイル
    """
    print(f"\n{'='*80}")
    print(f"走破タイム統合")
    print(f"{'='*80}")
    
    # テストデータ読み込み
    print(f"\nテストデータ読み込み: {test_csv}")
    df_test = pd.read_csv(test_csv)
    print(f"  件数: {len(df_test)}")
    
    # 走破タイムデータ読み込み
    print(f"\n走破タイムデータ読み込み: {soha_csv}")
    df_soha = pd.read_csv(soha_csv)
    print(f"  件数: {len(df_soha)}")
    
    # soha_timeを秒に変換
    df_soha['soha_time_seconds'] = df_soha['soha_time'].apply(parse_soha_time)
    
    # 結合キーを生成
    df_test['merge_key'] = (
        df_test['kaisai_nen'].astype(str) +
        df_test['kaisai_tsukihi'].astype(str).str.zfill(4) +
        df_test['keibajo_code'].astype(str).str.zfill(2) +
        df_test['race_bango'].astype(str).str.zfill(2) +
        df_test['ketto_toroku_bango'].astype(str)
    )
    
    df_soha['merge_key'] = (
        df_soha['kaisai_nen'].astype(str) +
        df_soha['kaisai_tsukihi'].astype(str).str.zfill(4) +
        df_soha['keibajo_code'].astype(str).str.zfill(2) +
        df_soha['race_bango'].astype(str).str.zfill(2) +
        df_soha['ketto_toroku_bango'].astype(str)
    )
    
    # 統合
    print(f"\nデータ統合中...")
    df_merged = df_test.merge(
        df_soha[['merge_key', 'soha_time_seconds']],
        on='merge_key',
        how='left'
    )
    
    # target列を走破タイムで置き換え
    df_merged['target'] = df_merged['soha_time_seconds']
    
    # merge_keyとsoha_time_secondsを削除
    df_merged = df_merged.drop(['merge_key', 'soha_time_seconds'], axis=1)
    
    # 統計
    matched = df_merged['target'].notna().sum()
    unmatched = df_merged['target'].isna().sum()
    
    print(f"\n統合結果:")
    print(f"  マッチ: {matched}件 ({matched/len(df_merged)*100:.1f}%)")
    print(f"  未マッチ: {unmatched}件 ({unmatched/len(df_merged)*100:.1f}%)")
    
    if matched > 0:
        print(f"\n走破タイム統計:")
        print(f"  平均: {df_merged['target'].mean():.2f}秒")
        print(f"  最小: {df_merged['target'].min():.2f}秒")
        print(f"  最大: {df_merged['target'].max():.2f}秒")
    
    # 保存
    df_merged.to_csv(output_csv, index=False)
    print(f"\n出力: {output_csv}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("使用法: python merge_soha_time.py <test_csv> <soha_csv> <output_csv>")
        print("\n例:")
        print("  python merge_soha_time.py ooi_2025_full_test.csv ooi_2025_test_soha_time.csv ooi_2025_full_test_with_time.csv")
        sys.exit(1)
    
    merge_soha_time(sys.argv[1], sys.argv[2], sys.argv[3])
