#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全14競馬場の走破タイムデータを競馬場別に分割
"""

import sys
import pandas as pd

def split_soha_time_by_venue(input_csv: str):
    """
    全競馬場の走破タイムCSVを競馬場別に分割
    
    Args:
        input_csv: 全競馬場の走破タイムCSV
    
    Output:
        <venue_name>_<start_year>-<end_year>_soha_time.csv
    """
    
    print(f"走破タイムデータを読み込み中: {input_csv}")
    df = pd.read_csv(input_csv)
    print(f"総データ件数: {len(df):,}件")
    
    # 競馬場コードと名前のマッピング
    venue_map = {
        '30': 'monbetsu',   # 門別
        '35': 'morioka',    # 盛岡
        '36': 'mizusawa',   # 水沢
        '42': 'urawa',      # 浦和
        '43': 'funabashi',  # 船橋
        '44': 'ooi',        # 大井
        '45': 'kawasaki',   # 川崎
        '46': 'kanazawa',   # 金沢
        '47': 'kasamatsu',  # 笠松
        '48': 'nagoya',     # 名古屋
        '50': 'sonoda',     # 園田
        '51': 'himeji',     # 姫路
        '54': 'kochi',      # 高知
        '55': 'saga'        # 佐賀
    }
    
    # 競馬場別データ期間の定義
    venue_periods = {
        'monbetsu': (2020, 2025),
        'morioka': (2020, 2025),
        'mizusawa': (2020, 2025),
        'urawa': (2020, 2025),
        'funabashi': (2020, 2025),
        'ooi': (2023, 2025),        # 大井は2023-2025
        'kawasaki': (2020, 2025),
        'kanazawa': (2020, 2025),
        'kasamatsu': (2020, 2025),
        'nagoya': (2022, 2025),     # 名古屋は2022-2025
        'sonoda': (2020, 2025),
        'himeji': (2020, 2025),
        'kochi': (2020, 2025),
        'saga': (2020, 2025)
    }
    
    # 競馬場ごとに分割
    for keibajo_code, venue_name in venue_map.items():
        # 該当競馬場のデータを抽出
        df_venue = df[df['keibajo_code'] == keibajo_code].copy()
        
        if len(df_venue) == 0:
            print(f"⚠️  {venue_name} ({keibajo_code}): データなし")
            continue
        
        # データ期間を取得
        start_year, end_year = venue_periods[venue_name]
        
        # 該当期間のデータを抽出
        df_venue = df_venue[
            (df_venue['kaisai_nen'].astype(str).astype(int) >= start_year) &
            (df_venue['kaisai_nen'].astype(str).astype(int) <= end_year)
        ]
        
        # 出力ファイル名
        output_file = f"{venue_name}_{start_year}-{end_year}_soha_time.csv"
        
        # 保存
        df_venue.to_csv(output_file, index=False)
        
        # 統計情報
        min_year = df_venue['kaisai_nen'].astype(str).astype(int).min()
        max_year = df_venue['kaisai_nen'].astype(str).astype(int).max()
        
        print(f"✅ {venue_name} ({keibajo_code}): {len(df_venue):,}件 "
              f"期間: {min_year}-{max_year} → {output_file}")
    
    print("\n✅ 分割完了！")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用法: python split_soha_time_by_venue.py <all_venues_soha_time.csv>")
        print("例: python split_soha_time_by_venue.py all_venues_2020-2025_soha_time.csv")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    split_soha_time_by_venue(input_csv)
