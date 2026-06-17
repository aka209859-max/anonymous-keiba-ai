#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース状態確認スクリプト
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

def check_database():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        safe_print('=' * 70)
        safe_print('データベース状態確認')
        safe_print('=' * 70)
        safe_print('')
        
        # 1. 最新のデータを確認
        safe_print('[1] 最新のデータ（上位10件）')
        safe_print('-' * 70)
        query_latest = '''
        SELECT DISTINCT 
            kaisai_nen,
            kaisai_tsukihi,
            COUNT(DISTINCT keibajo_code) as venue_count,
            COUNT(DISTINCT race_bango) as race_count,
            COUNT(*) as horse_count
        FROM nvd_se
        GROUP BY kaisai_nen, kaisai_tsukihi
        ORDER BY kaisai_nen DESC, kaisai_tsukihi DESC
        LIMIT 10
        '''
        
        cur.execute(query_latest)
        latest = cur.fetchall()
        
        if latest:
            for row in latest:
                year, date, venues, races, horses = row
                date_str = f'{date[:4]}-{date[4:6]}-{date[6:8]}'
                safe_print(f'{year}年 {date_str}: {venues}競馬場, {races}R, {horses}頭')
        else:
            safe_print('データが見つかりません')
        
        safe_print('')
        
        # 2. 2026年のデータ範囲を確認
        safe_print('[2] 2026年のデータ範囲')
        safe_print('-' * 70)
        query_2026_range = '''
        SELECT 
            MIN(kaisai_tsukihi) as min_date,
            MAX(kaisai_tsukihi) as max_date,
            COUNT(DISTINCT kaisai_tsukihi) as date_count,
            COUNT(DISTINCT keibajo_code) as venue_count,
            COUNT(*) as total_records
        FROM nvd_se
        WHERE kaisai_nen = '2026'
        '''
        
        cur.execute(query_2026_range)
        result = cur.fetchone()
        
        if result and result[0]:
            min_date, max_date, date_count, venue_count, total_records = result
            min_str = f'{min_date[:4]}-{min_date[4:6]}-{min_date[6:8]}'
            max_str = f'{max_date[:4]}-{max_date[4:6]}-{max_date[6:8]}'
            safe_print(f'期間: {min_str} ～ {max_str}')
            safe_print(f'開催日数: {date_count}日')
            safe_print(f'競馬場数: {venue_count}場')
            safe_print(f'総レコード数: {total_records:,}件')
        else:
            safe_print('2026年のデータが存在しません')
        
        safe_print('')
        
        # 3. 2026年2月の詳細データ
        safe_print('[3] 2026年2月のデータ（全日程）')
        safe_print('-' * 70)
        query_feb = '''
        SELECT 
            kaisai_tsukihi,
            COUNT(DISTINCT keibajo_code) as venue_count,
            COUNT(DISTINCT race_bango) as race_count,
            COUNT(*) as horse_count
        FROM nvd_se
        WHERE kaisai_nen = '2026'
          AND kaisai_tsukihi >= '20260201'
          AND kaisai_tsukihi <= '20260228'
        GROUP BY kaisai_tsukihi
        ORDER BY kaisai_tsukihi
        '''
        
        cur.execute(query_feb)
        feb_data = cur.fetchall()
        
        if feb_data:
            for row in feb_data:
                date, venues, races, horses = row
                date_str = f'{date[:4]}-{date[4:6]}-{date[6:8]}'
                safe_print(f'{date_str}: {venues}競馬場, {races}R, {horses}頭')
        else:
            safe_print('2026年2月のデータが存在しません')
        
        safe_print('')
        
        # 4. 直近3ヶ月のデータサマリー
        safe_print('[4] 直近3ヶ月のデータサマリー')
        safe_print('-' * 70)
        query_recent_months = '''
        SELECT 
            kaisai_nen,
            SUBSTRING(kaisai_tsukihi, 5, 2) as month,
            COUNT(DISTINCT kaisai_tsukihi) as days,
            COUNT(DISTINCT keibajo_code) as venues,
            COUNT(*) as total_records
        FROM nvd_se
        WHERE kaisai_nen >= '2025'
        GROUP BY kaisai_nen, SUBSTRING(kaisai_tsukihi, 5, 2)
        ORDER BY kaisai_nen DESC, month DESC
        LIMIT 3
        '''
        
        cur.execute(query_recent_months)
        months = cur.fetchall()
        
        if months:
            for row in months:
                year, month, days, venues, records = row
                safe_print(f'{year}年{month}月: {days}日開催, {venues}競馬場, {records:,}件')
        else:
            safe_print('直近データなし')
        
        safe_print('')
        safe_print('=' * 70)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        safe_print(f'[ERROR] {e}')

if __name__ == '__main__':
    check_database()
