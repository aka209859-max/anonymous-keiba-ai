#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
過去走データのカラム名確認スクリプト
"""

import psycopg2

# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

def check_past_race_columns():
    """nvd_seテーブルの過去走関連カラムを確認"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("=" * 80)
        print("nvd_se テーブルの過去走関連カラム確認")
        print("=" * 80)
        
        # nvd_seの前走関連カラムを確認
        query = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'nvd_se'
          AND (
            column_name LIKE 'zensou%'
            OR column_name LIKE '%前走%'
            OR column_name LIKE '%1走%'
          )
        ORDER BY column_name;
        """
        
        cur.execute(query)
        columns = cur.fetchall()
        
        if columns:
            print("\n✅ nvd_se テーブルの前走関連カラム:")
            print("-" * 80)
            for col_name, data_type, max_length in columns:
                length_str = f"({max_length})" if max_length else ""
                print(f"  {col_name:40s} {data_type}{length_str}")
        else:
            print("\n❌ 前走関連カラムが見つかりませんでした")
        
        # nvd_umの過去走関連カラムを確認
        print("\n" + "=" * 80)
        print("nvd_um テーブルの過去走関連カラム確認")
        print("=" * 80)
        
        query = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'nvd_um'
          AND (
            column_name LIKE '%sou%zen%'
            OR column_name LIKE '%走前%'
          )
        ORDER BY column_name;
        """
        
        cur.execute(query)
        columns = cur.fetchall()
        
        if columns:
            print("\n✅ nvd_um テーブルの過去走関連カラム:")
            print("-" * 80)
            for col_name, data_type, max_length in columns:
                length_str = f"({max_length})" if max_length else ""
                print(f"  {col_name:40s} {data_type}{length_str}")
        else:
            print("\n❌ 過去走関連カラムが見つかりませんでした")
        
        # サンプルデータを確認（nvd_se）
        print("\n" + "=" * 80)
        print("nvd_se サンプルデータ（前走関連カラムのみ）")
        print("=" * 80)
        
        query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'nvd_se'
          AND column_name LIKE 'zensou%'
        ORDER BY column_name;
        """
        
        cur.execute(query)
        zensou_columns = [row[0] for row in cur.fetchall()]
        
        if zensou_columns:
            # カラムをカンマ区切りで結合
            columns_str = ', '.join(zensou_columns)
            
            sample_query = f"""
            SELECT {columns_str}
            FROM nvd_se
            WHERE zensou_kyori IS NOT NULL
            LIMIT 5;
            """
            
            cur.execute(sample_query)
            rows = cur.fetchall()
            
            if rows:
                print(f"\n前走関連カラム: {len(zensou_columns)}個")
                print("-" * 80)
                for col_name in zensou_columns:
                    print(f"  {col_name}")
                
                print("\nサンプルデータ（最初の5件）:")
                print("-" * 80)
                for i, row in enumerate(rows, 1):
                    print(f"\nレコード {i}:")
                    for col_name, value in zip(zensou_columns, row):
                        print(f"  {col_name:40s}: {value}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ 確認完了")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_past_race_columns()
