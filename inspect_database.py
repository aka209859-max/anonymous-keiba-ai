#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_database.py
PC-KEIBA Databaseのテーブル構造を調査するスクリプト

使用法:
    python inspect_database.py
"""

import psycopg2
from psycopg2 import sql
import sys

# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}


def connect_db():
    """データベースに接続"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ データベース接続成功\n")
        return conn
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        sys.exit(1)


def get_table_list(conn):
    """テーブル一覧を取得"""
    query = """
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = t.table_schema 
                AND table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    tables = cursor.fetchall()
    cursor.close()
    
    return tables


def get_table_info(conn, table_name):
    """指定したテーブルの詳細情報を取得"""
    # カラム情報
    query = """
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position;
    """
    
    cursor = conn.cursor()
    cursor.execute(query, (table_name,))
    columns = cursor.fetchall()
    
    # レコード数
    try:
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
            sql.Identifier(table_name)
        ))
        count = cursor.fetchone()[0]
    except:
        count = "N/A"
    
    cursor.close()
    
    return columns, count


def get_sample_data(conn, table_name, limit=3):
    """サンプルデータを取得"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql.SQL("SELECT * FROM {} LIMIT %s").format(
            sql.Identifier(table_name)
        ), (limit,))
        
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        cursor.close()
        
        return colnames, rows
    except Exception as e:
        return None, None


def main():
    """メイン処理"""
    print("=" * 80)
    print("PC-KEIBA Database テーブル構造調査")
    print("=" * 80)
    print()
    
    # データベース接続
    conn = connect_db()
    
    try:
        # テーブル一覧取得
        print("[1] テーブル一覧")
        print("-" * 80)
        tables = get_table_list(conn)
        
        for table_name, col_count in tables:
            print(f"  - {table_name:30s} ({col_count:3d} columns)")
        
        print(f"\n合計: {len(tables)} テーブル\n")
        
        # 主要テーブルの詳細情報
        main_tables = ['nvd_ra', 'nvd_se', 'nvd_um', 'nvd_kj', 'nvd_ch']
        
        for table_name in main_tables:
            print("=" * 80)
            print(f"[2] テーブル詳細: {table_name}")
            print("=" * 80)
            
            columns, count = get_table_info(conn, table_name)
            
            if isinstance(count, int):
        print(f"\nレコード数: {count:,}件\n")
    else:
        print(f"\nレコード数: {count}件\n")
            print("カラム情報:")
            print("-" * 80)
            print(f"{'カラム名':40s} {'データ型':20s} {'NULL許可':10s}")
            print("-" * 80)
            
            for col_name, data_type, max_length, is_nullable in columns:
                type_str = data_type
                if max_length:
                    type_str = f"{data_type}({max_length})"
                print(f"{col_name:40s} {type_str:20s} {is_nullable:10s}")
            
            # サンプルデータ
            print(f"\nサンプルデータ（最初の3件）:")
            print("-" * 80)
            colnames, rows = get_sample_data(conn, table_name, limit=3)
            
            if colnames and rows:
                # カラム名を表示
                print("  " + " | ".join([f"{col[:15]:15s}" for col in colnames[:10]]))
                print("  " + "-" * (17 * min(10, len(colnames))))
                
                # データを表示
                for row in rows:
                    values = []
                    for val in row[:10]:
                        if val is None:
                            val_str = "NULL"
                        else:
                            val_str = str(val)[:15]
                        values.append(f"{val_str:15s}")
                    print("  " + " | ".join(values))
            else:
                print("  サンプルデータの取得に失敗しました")
            
            print("\n")
        
        print("=" * 80)
        print("調査完了")
        print("=" * 80)
        
    finally:
        conn.close()
        print("\nデータベース接続を閉じました")


if __name__ == "__main__":
    main()
