#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年2月9日の出走データ確認スクリプト
"""

import sys
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

def safe_print(msg):
    """安全な出力"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('cp932', errors='ignore').decode('cp932'))

def check_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 2026-02-09のデータを確認（複数パターン対応）
        target_patterns = ['20260209', '0209']
        
        query = '''
        SELECT 
            keibajo_code,
            COUNT(DISTINCT race_bango) as race_count,
            COUNT(*) as horse_count
        FROM nvd_se
        WHERE kaisai_nen = '2026'
          AND (kaisai_tsukihi = %s OR kaisai_tsukihi LIKE %s)
        GROUP BY keibajo_code
        ORDER BY keibajo_code
        '''
        
        cur.execute(query, ('20260209', '0209%'))
        results = cur.fetchall()
        
        if results:
            safe_print('=' * 60)
            safe_print('2026年2月9日（日）の出走データ')
            safe_print('=' * 60)
            
            keibajo_map = {
                '30': '門別', '35': '盛岡', '36': '水沢', '42': '浦和',
                '43': '船橋', '44': '大井', '45': '川崎', '46': '金沢',
                '47': '笠松', '48': '名古屋', '50': '園田', '51': '姫路',
                '54': '高知', '55': '佐賀'
            }
            
            total_races = 0
            total_horses = 0
            
            for row in results:
                code, races, horses = row
                name = keibajo_map.get(code, f'競馬場{code}')
                safe_print(f'{name:6s} (Code {code}): {races:2d}R, {horses:3d}頭')
                total_races += races
                total_horses += horses
            
            safe_print('=' * 60)
            safe_print(f'合計: {len(results)}競馬場, {total_races}R, {total_horses}頭')
            safe_print('=' * 60)
        else:
            safe_print('=' * 60)
            safe_print('[WARNING] 2026年2月9日のデータが見つかりません')
            safe_print('=' * 60)
            safe_print('')
            safe_print('直近のデータを確認します...')
            safe_print('')
            
            # 直近のデータを確認
            query_recent = '''
            SELECT DISTINCT 
                kaisai_nen,
                kaisai_tsukihi,
                COUNT(DISTINCT keibajo_code) as venue_count,
                COUNT(DISTINCT race_bango) as race_count,
                COUNT(*) as horse_count
            FROM nvd_se
            WHERE kaisai_nen = '2026'
              AND (kaisai_tsukihi >= '20260201' OR kaisai_tsukihi LIKE '02%')
            GROUP BY kaisai_nen, kaisai_tsukihi
            ORDER BY kaisai_tsukihi DESC
            LIMIT 10
            '''
            
            cur.execute(query_recent)
            recent = cur.fetchall()
            
            if recent:
                safe_print('2026年2月の直近データ:')
                safe_print('-' * 60)
                for row in recent:
                    year, date, venues, races, horses = row
                    date_str = f'{date[:4]}-{date[4:6]}-{date[6:8]}'
                    safe_print(f'{date_str}: {venues}競馬場, {races}R, {horses}頭')
                safe_print('-' * 60)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        safe_print(f'[ERROR] データベース接続エラー: {e}')
        safe_print('')
        safe_print('データベース設定を確認してください:')
        safe_print('  - ホスト: localhost')
        safe_print('  - ポート: 5432')
        safe_print('  - データベース: pckeiba')
        safe_print('  - ユーザー: postgres')

if __name__ == '__main__':
    check_data()
