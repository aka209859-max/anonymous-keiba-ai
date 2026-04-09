#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_db_format.py
PC-KEIBAデータベースのkaisai_tsukihi形式を確認
"""

import psycopg2
import sys

# データベース接続情報
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

def check_database():
    """データベース接続とデータ形式確認"""
    
    print("=" * 80)
    print("🔍 PC-KEIBAデータベース診断ツール")
    print("=" * 80)
    print()
    
    # データベース接続
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ データベース接続成功")
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        print()
        print("💡 確認事項:")
        print("1. PostgreSQLが起動しているか")
        print("2. 接続情報が正しいか（host, port, database, user, password）")
        return
    
    cursor = conn.cursor()
    
    print()
    print("-" * 80)
    print("📊 テーブル nvd_se の確認")
    print("-" * 80)
    
    # 1. 2026年のデータ件数
    print("\n【1】2026年のデータ件数")
    try:
        cursor.execute("SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026'")
        count_2026 = cursor.fetchone()[0]
        print(f"   2026年データ: {count_2026:,} 件")
        
        if count_2026 == 0:
            print()
            print("   ⚠️  警告: 2026年のデータが0件です！")
            print("   原因: PC-KEIBAで2026年のデータを取り込んでいない可能性")
            print()
            print("   💡 解決策:")
            print("   1. PC-KEIBAで2026年のデータを取り込む")
            print("   2. または、2025年のデータで分析:")
            print("      python scripts\\evaluation\\analyze_rank_fukusho_rate_from_db.py --year 2025")
            
            # 2025年のデータ確認
            cursor.execute("SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2025'")
            count_2025 = cursor.fetchone()[0]
            print()
            print(f"   参考: 2025年データ: {count_2025:,} 件")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 2. 2026年2月のデータ
    print("\n【2】2026年2月のデータ")
    try:
        cursor.execute("SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026' AND kaisai_tsukihi LIKE '2%'")
        count_feb = cursor.fetchone()[0]
        print(f"   2月データ: {count_feb:,} 件")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 3. 2026年3月のデータ
    print("\n【3】2026年3月のデータ")
    try:
        cursor.execute("SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen = '2026' AND kaisai_tsukihi LIKE '3%'")
        count_mar = cursor.fetchone()[0]
        print(f"   3月データ: {count_mar:,} 件")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 4. kaisai_tsukihi形式確認（最重要）
    print("\n【4】kaisai_tsukihi の形式確認（★重要）")
    try:
        query = """
        SELECT 
            kaisai_nen,
            kaisai_tsukihi,
            LENGTH(kaisai_tsukihi::text) as 桁数,
            keibajo_code,
            race_bango
        FROM nvd_se 
        WHERE kaisai_nen = '2026' 
        LIMIT 5
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            print("   サンプルデータ:")
            print(f"   {'年':<6} {'月日':<10} {'桁数':<6} {'場':<6} {'R':<6}")
            print("   " + "-" * 40)
            for row in rows:
                print(f"   {row[0]:<6} {row[1]:<10} {row[2]:<6} {row[3]:<6} {row[4]:<6}")
            
            # 桁数判定
            first_tsukihi = str(rows[0][1])
            digit_count = len(first_tsukihi)
            
            print()
            print(f"   📌 kaisai_tsukihi は {digit_count}桁 です")
            print()
            
            if digit_count == 3:
                print("   ⚠️  重要: kaisai_tsukihiが3桁です（先頭ゼロなし）")
                print("   例: '213' = 2月13日")
                print()
                print("   💡 修正が必要:")
                print("   スクリプトは4桁（'0213'）で検索していますが、")
                print("   データベースは3桁（'213'）なのでマッチしません。")
                print()
                print("   修正方法:")
                print("   scripts/evaluation/analyze_rank_fukusho_rate_from_db.py")
                print("   の216行目を以下に変更:")
                print()
                print("   【修正前】")
                print("   df_predictions['kaisai_tsukihi'] = df_predictions['race_id'].astype(str).str[4:8]")
                print()
                print("   【修正後】")
                print("   df_predictions['kaisai_tsukihi'] = df_predictions['race_id'].astype(str).str[4:8].str.lstrip('0')")
                print()
            elif digit_count == 4:
                print("   ✅ kaisai_tsukihiが4桁です（先頭ゼロあり）")
                print("   例: '0213' = 2月13日")
                print()
                print("   これはスクリプトと一致しています。")
                print("   他の原因を調査する必要があります。")
            else:
                print(f"   ⚠️  想定外の桁数: {digit_count}桁")
        else:
            print("   ⚠️  2026年のデータが見つかりません")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 5. 競馬場別データ件数
    print("\n【5】競馬場別データ件数（2026年）")
    try:
        query = """
        SELECT 
            keibajo_code,
            COUNT(*) as 件数
        FROM nvd_se 
        WHERE kaisai_nen = '2026'
        GROUP BY keibajo_code
        ORDER BY keibajo_code
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            venue_names = {
                '30': '門別', '35': '盛岡', '36': '水沢',
                '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
                '46': '金沢', '47': '笠松', '48': '名古屋',
                '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
            }
            
            print("   競馬場コード | 競馬場 | 件数")
            print("   " + "-" * 40)
            for row in rows:
                code = row[0]
                name = venue_names.get(code, '不明')
                count = row[1]
                print(f"   {code:<12} | {name:<6} | {count:>6,} 件")
        else:
            print("   データなし")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # 6. 着順データの有無確認
    print("\n【6】着順データ（kakutei_chakujun）の有無")
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as 全件数,
                COUNT(kakutei_chakujun) as 着順あり,
                COUNT(*) - COUNT(kakutei_chakujun) as 着順なし
            FROM nvd_se 
            WHERE kaisai_nen = '2026'
        """)
        row = cursor.fetchone()
        print(f"   全件数: {row[0]:,} 件")
        print(f"   着順あり: {row[1]:,} 件")
        print(f"   着順なし: {row[2]:,} 件")
        
        if row[2] > 0:
            print()
            print("   ⚠️  着順データが無いレコードがあります")
            print("   原因: レースが未実施、または結果未取り込み")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ 診断完了")
    print("=" * 80)
    print()

if __name__ == '__main__':
    check_database()
