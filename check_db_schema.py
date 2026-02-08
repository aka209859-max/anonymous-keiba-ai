#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベーススキーマ確認スクリプト
nvd_se と nvd_ra テーブルのカラム名を確認
"""

import psycopg2

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

def check_table_columns(table_name):
    """テーブルのカラム情報を取得"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    query = """
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = %s
    ORDER BY ordinal_position
    """
    
    cursor.execute(query, (table_name,))
    columns = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return columns

if __name__ == '__main__':
    print("=" * 80)
    print("データベーススキーマ確認")
    print("=" * 80)
    
    # nvd_se テーブル
    print("\n【nvd_se テーブル】")
    print("-" * 80)
    se_columns = check_table_columns('nvd_se')
    
    # 重要なカラムのみ表示
    important_columns = ['seibetsu', 'seibetsu_code', 'barei', 'baba_jotai_code', 
                        'shusso_tosu', 'kishu_code', 'chokyoshi_code', 'futan_juryo',
                        'kakutei_chakujun', 'ketto_toroku_bango']
    
    print("重要カラム:")
    for col_name, data_type in se_columns:
        if any(imp in col_name for imp in important_columns):
            print(f"  {col_name:<30} {data_type}")
    
    # nvd_ra テーブル
    print("\n【nvd_ra テーブル】")
    print("-" * 80)
    ra_columns = check_table_columns('nvd_ra')
    
    important_ra_columns = ['baba', 'babajotai', 'shusso_tosu', 'kyori', 'track_code']
    
    print("重要カラム:")
    for col_name, data_type in ra_columns:
        if any(imp in col_name for imp in important_ra_columns):
            print(f"  {col_name:<30} {data_type}")
    
    print("\n" + "=" * 80)
    print("✅ スキーマ確認完了")
    print("=" * 80)
