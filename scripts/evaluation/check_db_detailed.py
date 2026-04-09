#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_db_detailed.py
PC-KEIBAデータベースの詳細調査
"""

import psycopg2
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

def check_database():
    print("=" * 80)
    print("🔍 PC-KEIBAデータベース 詳細調査")
    print("=" * 80)
    print()
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ データベース接続成功")
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        return
    
    cursor = conn.cursor()
    
    # 1. 2026年データの日付範囲を確認
    print("\n【1】2026年データの日付範囲")
    try:
        query = """
        SELECT 
            MIN(kaisai_tsukihi) as 最小日付,
            MAX(kaisai_tsukihi) as 最大日付,
            COUNT(DISTINCT kaisai_tsukihi) as 異なる日付数
        FROM nvd_se 
        WHERE kaisai_nen = '2026'
        """
        cursor.execute(query)
        row = cursor.fetchone()
        print(f"   最小日付: {row[0]}")
        print(f"   最大日付: {row[1]}")
        print(f"   異なる日付数: {row[2]}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 2. 日付別データ件数（上位20件）
    print("\n【2】日付別データ件数（上位20件）")
    try:
        query = """
        SELECT 
            kaisai_tsukihi,
            COUNT(*) as 件数
        FROM nvd_se 
        WHERE kaisai_nen = '2026'
        GROUP BY kaisai_tsukihi
        ORDER BY kaisai_tsukihi
        LIMIT 20
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"   {'日付':<12} | {'件数':<8}")
        print("   " + "-" * 25)
        for row in rows:
            print(f"   {row[0]:<12} | {row[1]:<8}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 3. 2月のデータを様々な方法で検索
    print("\n【3】2月のデータ検索（複数パターン）")
    
    patterns = [
        ("LIKE '2%'", "2で始まる"),
        ("LIKE '02%'", "02で始まる"),
        ("LIKE '%2%'", "2を含む"),
        (">= '0201' AND kaisai_tsukihi <= '0229'", "0201～0229"),
        (">= '201' AND kaisai_tsukihi <= '229'", "201～229"),
        ("BETWEEN '0201' AND '0231'", "0201～0231"),
        ("BETWEEN '201' AND '231'", "201～231"),
    ]
    
    for pattern, desc in patterns:
        try:
            query = f"""
            SELECT COUNT(*) 
            FROM nvd_se 
            WHERE kaisai_nen = '2026' AND kaisai_tsukihi {pattern}
            """
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"   {desc:<30}: {count:>6} 件")
        except Exception as e:
            print(f"   {desc:<30}: エラー - {e}")
    
    # 4. 予測CSVのrace_idと一致するデータを検索
    print("\n【4】予測CSVのrace_idパターンで検索")
    
    race_patterns = [
        ('2026', '0205', '45', '川崎 2月5日'),
        ('2026', '0213', '43', '船橋 2月13日'),
        ('2026', '0220', '47', '笠松 2月20日'),
        ('2026', '0305', '51', '姫路 3月5日'),
        ('2026', '205', '45', '川崎 2月5日（3桁）'),
        ('2026', '213', '43', '船橋 2月13日（3桁）'),
    ]
    
    for nen, tsukihi, code, desc in race_patterns:
        try:
            query = f"""
            SELECT COUNT(*) 
            FROM nvd_se 
            WHERE kaisai_nen = '{nen}' 
              AND kaisai_tsukihi = '{tsukihi}'
              AND keibajo_code = '{code}'
            """
            cursor.execute(query)
            count = cursor.fetchone()[0]
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {desc:<30}: {count:>6} 件")
        except Exception as e:
            print(f"   ❌ {desc:<30}: エラー")
    
    # 5. 全ての異なるkaisai_tsukihiを表示（最初の50件）
    print("\n【5】全ての異なる kaisai_tsukihi 値（最初の50件）")
    try:
        query = """
        SELECT DISTINCT kaisai_tsukihi
        FROM nvd_se 
        WHERE kaisai_nen = '2026'
        ORDER BY kaisai_tsukihi
        LIMIT 50
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        values = [row[0] for row in rows]
        # 10個ずつ表示
        for i in range(0, len(values), 10):
            chunk = values[i:i+10]
            print(f"   {', '.join(str(v) for v in chunk)}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ 詳細調査完了")
    print("=" * 80)
    print()

if __name__ == '__main__':
    check_database()
