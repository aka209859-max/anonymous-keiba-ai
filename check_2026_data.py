#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年1-2月のデータ確認スクリプト
PC-KEIBAデータベースに2026-01-01～2026-02-03のデータが存在するかチェックする
"""

import psycopg2
from datetime import datetime

# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

# 競馬場コード（帯広を除く14競馬場）
VENUE_CODES = {
    30: '門別',
    35: '盛岡',
    36: '水沢',
    42: '浦和',
    43: '船橋',
    44: '大井',
    45: '川崎',
    46: '金沢',
    47: '笠松',
    48: '名古屋',
    50: '園田',
    51: '姫路',
    54: '高知',
    55: '佐賀'
}

def check_2026_data():
    """2026年1-2月のデータ件数をチェック"""
    
    try:
        # データベース接続
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("=" * 80)
        print("PC-KEIBA Database: 2026年1-2月データ確認")
        print("=" * 80)
        print(f"確認期間: 2026-01-01 ～ 2026-02-03")
        print(f"対象競馬場: 14競馬場（帯広を除く）")
        print("=" * 80)
        print()
        
        # 全体のデータ件数確認（型を明示的にキャスト）
        query_total = """
        SELECT 
            COUNT(*) as total_count,
            MIN(kaisai_nen || '-' || LPAD(SUBSTRING(kaisai_tsukihi, 1, 2), 2, '0') || '-' || LPAD(SUBSTRING(kaisai_tsukihi, 3, 2), 2, '0')) as min_date,
            MAX(kaisai_nen || '-' || LPAD(SUBSTRING(kaisai_tsukihi, 1, 2), 2, '0') || '-' || LPAD(SUBSTRING(kaisai_tsukihi, 3, 2), 2, '0')) as max_date
        FROM nvd_se
        WHERE kaisai_nen = '2026'
        AND keibajo_code IN ('30', '35', '36', '42', '43', '44', '45', '46', '47', '48', '50', '51', '54', '55')
        AND (
            (kaisai_tsukihi >= '0101' AND kaisai_tsukihi <= '0131') OR  -- 1月
            (kaisai_tsukihi >= '0201' AND kaisai_tsukihi <= '0203')     -- 2月1-3日
        )
        """
        
        cur.execute(query_total)
        result = cur.fetchone()
        total_count = result[0] if result[0] else 0
        min_date = result[1] if result[1] else "N/A"
        max_date = result[2] if result[2] else "N/A"
        
        print(f"【全体サマリー】")
        print(f"  総データ件数: {total_count:,} 件")
        print(f"  最古日付: {min_date}")
        print(f"  最新日付: {max_date}")
        print()
        
        if total_count == 0:
            print("⚠️  2026年1-2月のデータが見つかりませんでした。")
            print()
            print("【確認ポイント】")
            print("  1. PC-KEIBAで最新のデータ更新を実行済みですか？")
            print("  2. kaisai_nen カラムが2026になっていますか？")
            print("  3. kaisai_tsukihi カラムの形式は正しいですか？（例: 101=1月1日）")
            cur.close()
            conn.close()
            return
        
        # 競馬場別のデータ件数
        print("【競馬場別データ件数】")
        print(f"{'競馬場名':<10} {'件数':>10} {'最古日付':<12} {'最新日付':<12}")
        print("-" * 50)
        
        total_venue_count = 0
        for code, name in sorted(VENUE_CODES.items()):
            query_venue = """
            SELECT 
                COUNT(*) as count,
                MIN(kaisai_nen || '-' || LPAD(SUBSTRING(kaisai_tsukihi, 1, 2), 2, '0') || '-' || LPAD(SUBSTRING(kaisai_tsukihi, 3, 2), 2, '0')) as min_date,
                MAX(kaisai_nen || '-' || LPAD(SUBSTRING(kaisai_tsukihi, 1, 2), 2, '0') || '-' || LPAD(SUBSTRING(kaisai_tsukihi, 3, 2), 2, '0')) as max_date
            FROM nvd_se
            WHERE kaisai_nen = '2026'
            AND keibajo_code = %s
            AND (
                (kaisai_tsukihi >= '0101' AND kaisai_tsukihi <= '0131') OR
                (kaisai_tsukihi >= '0201' AND kaisai_tsukihi <= '0203')
            )
            """
            
            cur.execute(query_venue, (str(code),))
            result = cur.fetchone()
            count = result[0] if result[0] else 0
            v_min = result[1] if result[1] else "N/A"
            v_max = result[2] if result[2] else "N/A"
            
            if count > 0:
                total_venue_count += 1
                print(f"{name:<10} {count:>10,} {v_min:<12} {v_max:<12}")
        
        print("-" * 50)
        print(f"データがある競馬場数: {total_venue_count} / 14")
        print()
        
        # 月別集計
        print("【月別データ件数】")
        query_monthly = """
        SELECT 
            CASE 
                WHEN kaisai_tsukihi >= '0101' AND kaisai_tsukihi <= '0131' THEN '2026-01'
                WHEN kaisai_tsukihi >= '0201' AND kaisai_tsukihi <= '0203' THEN '2026-02'
            END as month,
            COUNT(*) as count
        FROM nvd_se
        WHERE kaisai_nen = '2026'
        AND keibajo_code IN ('30', '35', '36', '42', '43', '44', '45', '46', '47', '48', '50', '51', '54', '55')
        AND (
            (kaisai_tsukihi >= '0101' AND kaisai_tsukihi <= '0131') OR
            (kaisai_tsukihi >= '0201' AND kaisai_tsukihi <= '0203')
        )
        GROUP BY month
        ORDER BY month
        """
        
        cur.execute(query_monthly)
        results = cur.fetchall()
        
        for month, count in results:
            print(f"  {month}: {count:,} 件")
        
        print()
        
        # 判定結果
        print("=" * 80)
        if total_count > 0:
            print("✅ 2026年1-2月のデータが確認できました！")
            print()
            print("【次のステップ】")
            print("  1. Phase 3のモデルで予測を実行")
            print("  2. Phase 4のランキング・回帰モデルで予測")
            print("  3. アンサンブルで総合評価")
            print("  4. 的中率・回収率を印別で分析")
        else:
            print("⚠️  データが見つかりませんでした。")
        print("=" * 80)
        
        # クローズ
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print("=" * 80)
        print("❌ データベース接続エラー")
        print("=" * 80)
        print(f"エラー内容: {e}")
        print()
        print("【確認ポイント】")
        print("  1. PostgreSQLサービスが起動していますか？")
        print("  2. PC-KEIBAが正しくインストールされていますか？")
        print("  3. データベース接続情報は正しいですか？")
        print()
        print("【接続情報】")
        for key, value in DB_CONFIG.items():
            if key == 'password':
                print(f"  {key}: {'*' * len(value)}")
            else:
                print(f"  {key}: {value}")
        print("=" * 80)
        
    except Exception as e:
        print("=" * 80)
        print("❌ エラーが発生しました")
        print("=" * 80)
        print(f"エラー内容: {e}")
        print("=" * 80)


if __name__ == '__main__':
    check_2026_data()
