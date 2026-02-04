#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_obihiro.py
帯広競馬場（コード: 33）のデータ件数を確認するスクリプト

使用法:
    python check_obihiro.py
"""

import psycopg2
import sys

# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}


def check_obihiro_data():
    """帯広競馬場のデータ件数を確認"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ データベース接続成功\n")
        
        cursor = conn.cursor()
        
        # 帯広競馬場（コード: 33）のレース数を確認
        query_ra = "SELECT COUNT(*) FROM nvd_ra WHERE keibajo_code = '33'"
        cursor.execute(query_ra)
        race_count = cursor.fetchone()[0]
        
        print("=" * 80)
        print("帯広競馬場（コード: 33）のデータ件数確認")
        print("=" * 80)
        print(f"\n📊 レース数（nvd_ra）: {race_count:,}件\n")
        
        if race_count == 0:
            print("🔴 結果: 帯広競馬場のデータは存在しません")
            print("\n【理由】")
            print("  - 帯広競馬場は「ばんえい競馬」で、通常の競馬とは異なる")
            print("  - PC-KEIBAデータベースには含まれていない可能性が高い")
            print("\n【結論】")
            print("  ✅ Phase 3 完了（14競馬場）として次のフェーズへ進む")
        else:
            print(f"✅ 結果: 帯広競馬場のデータが {race_count:,}件 存在します")
            print("\n【次のステップ】")
            print("  1. extract_training_data_v2.py のSQLクエリを確認")
            print("  2. データ抽出を再実行")
            
            # 出走馬数も確認
            query_se = "SELECT COUNT(*) FROM nvd_se WHERE keibajo_code = '33'"
            cursor.execute(query_se)
            horse_count = cursor.fetchone()[0]
            print(f"\n📊 出走馬数（nvd_se）: {horse_count:,}件")
            
            # 期間範囲を確認
            query_period = """
                SELECT 
                    MIN(kaisai_nen || '-' || kaisai_tsukihi) as min_date,
                    MAX(kaisai_nen || '-' || kaisai_tsukihi) as max_date
                FROM nvd_ra 
                WHERE keibajo_code = '33'
            """
            cursor.execute(query_period)
            min_date, max_date = cursor.fetchone()
            print(f"📅 データ期間: {min_date} ～ {max_date}")
        
        print("\n" + "=" * 80)
        
        cursor.close()
        conn.close()
        print("\n✅ データベース接続を閉じました")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_obihiro_data()
