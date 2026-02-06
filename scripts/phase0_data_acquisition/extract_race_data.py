#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 0: PC-KEIBAから競馬データを取得

使用法:
    python extract_race_data.py --date 2026-02-05 --keibajo 45 --output data/raw/2026/02/kawasaki_20260205_raw.csv
    python extract_race_data.py --date today --keibajo 55  # 今日の佐賀競馬
"""

import sys
import argparse
import psycopg2
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

# 地方競馬場コード
KEIBAJO_CODES = {
    '30': '門別', '33': '帯広', '35': '盛岡', '36': '水沢',
    '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
    '46': '金沢', '47': '笠松', '48': '名古屋',
    '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
}


def parse_date(date_str):
    """日付文字列をパース"""
    if date_str.lower() == 'today':
        return datetime.now()
    elif date_str.lower() == 'tomorrow':
        return datetime.now() + timedelta(days=1)
    else:
        return datetime.strptime(date_str, '%Y-%m-%d')


def create_extraction_query(keibajo_code, kaisai_nen, kaisai_tsukihi):
    """データ抽出SQLクエリを生成
    
    Phase 0で必要な全データを1回のクエリで取得:
    - レース情報（nvd_ra）
    - 出馬情報（nvd_se）
    - 馬情報（nvd_um）
    - 過去走データ（nvd_se の自己JOIN）
    
    調査報告書に基づき、リーク防止のため以下を除外:
    - 当日オッズ（ninki, odds系）
    - 当日馬体重（zogen系）
    - レース結果（kakutei_chakujun, time系）※予測時
    """
    
    query = f"""
    WITH target_race AS (
        -- 予測対象レース
        SELECT 
            ra.kaisai_nen,
            ra.kaisai_tsukihi,
            ra.keibajo_code,
            ra.race_bango,
            se.ketto_toroku_bango,
            se.umaban,
            
            -- レース情報（前日確定）
            ra.kyori,
            ra.track_code,
            ra.babajotai_code_shiba,
            ra.babajotai_code_dirt,
            ra.tenko_code,
            ra.shusso_tosu,
            ra.grade_code,
            
            -- 出馬情報（前日確定）
            se.wakuban,
            se.seibetsu_code,
            se.barei,
            se.futan_juryo,
            se.kishu_code,
            se.chokyoshi_code,
            se.blinker_shiyo_kubun,
            se.tozai_shozoku_code,
            
            -- 馬情報
            um.moshoku_code
            
        FROM 
            nvd_ra ra
            INNER JOIN nvd_se se ON (
                ra.kaisai_nen = se.kaisai_nen 
                AND ra.kaisai_tsukihi = se.kaisai_tsukihi
                AND ra.keibajo_code = se.keibajo_code
                AND ra.race_bango = se.race_bango
            )
            LEFT JOIN nvd_um um ON (
                se.ketto_toroku_bango = um.ketto_toroku_bango
            )
        
        WHERE 
            ra.kaisai_nen = '{kaisai_nen}'
            AND ra.kaisai_tsukihi = '{kaisai_tsukihi}'
            AND ra.keibajo_code = '{keibajo_code}'
    ),
    past_races AS (
        -- その馬の過去走を全て取得（ROW_NUMBER()で順序付け）
        SELECT 
            se.ketto_toroku_bango,
            se.kaisai_nen,
            se.kaisai_tsukihi,
            se.keibajo_code,
            se.race_bango,
            
            -- 過去走の結果データ
            se.kakutei_chakujun,
            se.soha_time,
            se.kohan_3f,
            se.kohan_4f,
            se.corner_1,
            se.corner_2,
            se.corner_3,
            se.corner_4,
            se.bataiju,
            
            -- 過去走のレース情報
            ra.kyori AS past_kyori,
            ra.keibajo_code AS past_keibajo,
            ra.track_code AS past_track,
            ra.babajotai_code_shiba AS past_baba_shiba,
            ra.babajotai_code_dirt AS past_baba_dirt,
            
            -- 過去走の順序（最新=1、2走前=2、...）
            ROW_NUMBER() OVER (
                PARTITION BY se.ketto_toroku_bango
                ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
            ) AS past_rank
            
        FROM 
            nvd_se se
            INNER JOIN nvd_ra ra ON (
                se.kaisai_nen = ra.kaisai_nen
                AND se.kaisai_tsukihi = ra.kaisai_tsukihi
                AND se.keibajo_code = ra.keibajo_code
                AND se.race_bango = ra.race_bango
            )
        
        WHERE 
            se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun NOT IN ('00', '取消', '除外', '中止', '失格')
            AND se.kakutei_chakujun ~ '^[0-9]+$'
            -- 予測対象レースより前のレースのみ
            AND (
                se.kaisai_nen < '{kaisai_nen}'
                OR (
                    se.kaisai_nen = '{kaisai_nen}' 
                    AND se.kaisai_tsukihi < '{kaisai_tsukihi}'
                )
            )
    )
    -- メインクエリ: 予測対象レースと過去走を結合
    SELECT 
        tr.*,
        
        -- 前走1（直近）
        pr1.kakutei_chakujun AS prev1_rank,
        pr1.soha_time AS prev1_time,
        pr1.kohan_3f AS prev1_last3f,
        pr1.kohan_4f AS prev1_last4f,
        pr1.corner_1 AS prev1_corner1,
        pr1.corner_2 AS prev1_corner2,
        pr1.corner_3 AS prev1_corner3,
        pr1.corner_4 AS prev1_corner4,
        pr1.bataiju AS prev1_weight,
        pr1.past_kyori AS prev1_kyori,
        pr1.past_keibajo AS prev1_keibajo,
        pr1.past_track AS prev1_track,
        pr1.past_baba_shiba AS prev1_baba_shiba,
        pr1.past_baba_dirt AS prev1_baba_dirt,
        
        -- 前走2
        pr2.kakutei_chakujun AS prev2_rank,
        pr2.soha_time AS prev2_time,
        pr2.kohan_3f AS prev2_last3f,
        pr2.bataiju AS prev2_weight,
        pr2.past_kyori AS prev2_kyori,
        pr2.past_keibajo AS prev2_keibajo,
        
        -- 前走3
        pr3.kakutei_chakujun AS prev3_rank,
        pr3.soha_time AS prev3_time,
        pr3.bataiju AS prev3_weight,
        
        -- 前走4
        pr4.kakutei_chakujun AS prev4_rank,
        pr4.soha_time AS prev4_time,
        
        -- 前走5
        pr5.kakutei_chakujun AS prev5_rank,
        pr5.soha_time AS prev5_time
        
    FROM 
        target_race tr
        LEFT JOIN past_races pr1 ON (tr.ketto_toroku_bango = pr1.ketto_toroku_bango AND pr1.past_rank = 1)
        LEFT JOIN past_races pr2 ON (tr.ketto_toroku_bango = pr2.ketto_toroku_bango AND pr2.past_rank = 2)
        LEFT JOIN past_races pr3 ON (tr.ketto_toroku_bango = pr3.ketto_toroku_bango AND pr3.past_rank = 3)
        LEFT JOIN past_races pr4 ON (tr.ketto_toroku_bango = pr4.ketto_toroku_bango AND pr4.past_rank = 4)
        LEFT JOIN past_races pr5 ON (tr.ketto_toroku_bango = pr5.ketto_toroku_bango AND pr5.past_rank = 5)
    
    ORDER BY 
        tr.race_bango, tr.umaban;
    """
    
    return query


def extract_race_data(keibajo_code, target_date, output_path=None):
    """PC-KEIBAからレースデータを取得
    
    Parameters
    ----------
    keibajo_code : str
        競馬場コード（例: '45'=川崎、'55'=佐賀）
    target_date : datetime
        対象日付
    output_path : str, optional
        出力先CSVパス（Noneの場合は自動生成）
    
    Returns
    -------
    pd.DataFrame
        取得したデータ
    """
    
    kaisai_yen = target_date.strftime('%Y')
    kaisai_tsukihi = target_date.strftime('%m%d')
    
    keibajo_name = KEIBAJO_CODES.get(keibajo_code, f'競馬場{keibajo_code}')
    
    print("="*80)
    print(f"Phase 0: データ取得")
    print("="*80)
    print(f"対象: {keibajo_name}（コード: {keibajo_code}）")
    print(f"日付: {target_date.strftime('%Y年%m月%d日')} ({kaisai_yen}/{kaisai_tsukihi})")
    print(f"接続: {DB_CONFIG['host']}:{DB_CONFIG['port']} / {DB_CONFIG['database']}")
    print("-"*80)
    
    # データベース接続
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ データベース接続成功")
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        return None
    
    try:
        # SQLクエリ生成
        query = create_extraction_query(keibajo_code, kaisai_yen, kaisai_tsukihi)
        
        # データ取得
        print("\n📥 データ取得中...")
        df = pd.read_sql_query(query, conn)
        
        print(f"✅ データ取得完了: {len(df)}件")
        
        if len(df) == 0:
            print(f"⚠️  {target_date.strftime('%Y-%m-%d')} の{keibajo_name}のデータが見つかりません")
            return None
        
        # データ統計表示
        print("\n📊 データ統計:")
        print(f"  - レース数: {df['race_bango'].nunique()}レース")
        print(f"  - 出走頭数: {len(df)}頭")
        print(f"  - 平均出走頭数: {len(df) / df['race_bango'].nunique():.1f}頭/レース")
        
        # 欠損値チェック
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print("\n⚠️  欠損値:")
            for col in null_counts[null_counts > 0].index:
                print(f"  - {col}: {null_counts[col]}件")
        
        # 出力先決定
        if output_path is None:
            # 自動生成: data/raw/YYYY/MM/keibajo_YYYYMMDD_raw.csv
            output_dir = Path('E:/anonymous-keiba-ai/data/raw') / kaisai_yen / kaisai_tsukihi[:2]
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{keibajo_name}_{target_date.strftime('%Y%m%d')}_raw.csv"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # CSV保存
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n💾 保存完了: {output_path}")
        print(f"   ファイルサイズ: {output_path.stat().st_size / 1024:.1f} KB")
        
        return df
        
    except Exception as e:
        print(f"❌ データ取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        conn.close()
        print("\n✅ データベース接続を閉じました")


def main():
    parser = argparse.ArgumentParser(
        description='PC-KEIBAから競馬データを取得（Phase 0）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 川崎競馬 2026-02-05
  python extract_race_data.py --date 2026-02-05 --keibajo 45
  
  # 今日の佐賀競馬
  python extract_race_data.py --date today --keibajo 55
  
  # 明日の大井競馬
  python extract_race_data.py --date tomorrow --keibajo 44 --output data/raw/ooi_tomorrow.csv
        """
    )
    
    parser.add_argument('--date', required=True, 
                       help='対象日付（YYYY-MM-DD形式、または "today", "tomorrow"）')
    parser.add_argument('--keibajo', required=True, 
                       help='競馬場コード（例: 45=川崎、55=佐賀、44=大井）')
    parser.add_argument('--output', 
                       help='出力先CSVパス（省略時は自動生成）')
    
    args = parser.parse_args()
    
    try:
        target_date = parse_date(args.date)
        df = extract_race_data(args.keibajo, target_date, args.output)
        
        if df is not None:
            print("\n" + "="*80)
            print("🎉 Phase 0 完了！")
            print("="*80)
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
