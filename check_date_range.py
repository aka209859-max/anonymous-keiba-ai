#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日付範囲の確認スクリプト
"""
import psycopg2
import pandas as pd

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

def check_date_ranges():
    """各月のデータ件数を確認"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    queries = [
        ("2026年1月全体", "kaisai_tsukihi >= '0101' AND kaisai_tsukihi <= '0131'"),
        ("2026年2月1-3日", "kaisai_tsukihi >= '0201' AND kaisai_tsukihi <= '0203'"),
        ("2026年2月4日", "kaisai_tsukihi = '0204'"),
        ("2026年2月全体", "kaisai_tsukihi >= '0201' AND kaisai_tsukihi <= '0229'"),
    ]
    
    print("=" * 80)
    print("PC-KEIBA Database: 2026年データの日付範囲確認")
    print("=" * 80)
    print()
    
    for label, condition in queries:
        query = f"""
        SELECT COUNT(*) as count
        FROM nvd_se
        WHERE kaisai_nen = '2026'
        AND {condition}
        AND kakutei_chakujun IS NOT NULL
        AND kakutei_chakujun != '0'
        """
        
        try:
            df = pd.read_sql_query(query, conn)
            count = df['count'].iloc[0]
            print(f"📊 {label:20s}: {count:6,d} 件")
        except Exception as e:
            print(f"❌ {label:20s}: エラー - {e}")
    
    print()
    print("=" * 80)
    print("競馬場別データ件数（2026年1月のみ）")
    print("=" * 80)
    
    venue_query = """
    SELECT 
        keibajo_code,
        COUNT(*) as count
    FROM nvd_se
    WHERE kaisai_nen = '2026'
    AND kaisai_tsukihi >= '0101' AND kaisai_tsukihi <= '0131'
    AND kakutei_chakujun IS NOT NULL
    AND kakutei_chakujun != '0'
    GROUP BY keibajo_code
    ORDER BY keibajo_code
    """
    
    venues = {
        '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
        '47': '笠松', '48': '名古屋', '50': '園田', '51': '姫路',
        '54': '高知', '55': '佐賀'
    }
    
    try:
        df = pd.read_sql_query(venue_query, conn)
        for _, row in df.iterrows():
            code = row['keibajo_code']
            count = row['count']
            name = venues.get(code, f'不明({code})')
            print(f"  {name:10s} (コード {code}): {count:6,d} 件")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_date_ranges()
