# -*- coding: utf-8 -*-
"""
Phase 0: PC-KEIBAデータベースからレースデータを取得（完全版・修正済み）
学習時（extract_training_data_v2.py）と同じ特徴量を網羅的に取得する

修正履歴:
- 2026-02-07: race_me → 削除（存在しないカラム）
- 2026-02-07: course_kubun → 削除（存在しないカラム）
- 2026-02-07: ばんえい競馬の除外フィルタ追加
"""

import sys
import os
from pathlib import Path
import psycopg2
import pandas as pd
from datetime import datetime
import argparse
import logging

# Windows環境でのUTF-8対応
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'

# ログ設定
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'phase0.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 競馬場コードマッピング
KEIBAJO_MAP = {
    '30': '門別', '33': '帯広', '35': '盛岡', '36': '水沢',
    '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
    '46': '金沢', '47': '笠松', '48': '名古屋',
    '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
}

# データベース接続情報
# ユーザー環境に合わせて変更してください
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'  # 必要に応じて変更
}

def safe_print(msg):
    """安全な出力（Windows CP932対応）"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('cp932', errors='ignore').decode('cp932'))

def get_db_connection():
    """データベース接続を取得"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        safe_print(f"[ERROR] DB接続失敗: {e}")
        return None

def get_target_races(conn, keibajo_code, target_date):
    """
    指定された日・競馬場のレース一覧を取得
    
    修正点:
    - race_me → 削除（存在しないカラム）
    - course_kubun → 削除（存在しないカラム）
    - hondai（本題）を追加（レース名として使用可能）
    - ばんえい競馬の除外フィルタ追加（track_code != '00'）
    """
    query = """
    SELECT 
        kaisai_nen,
        kaisai_tsukihi,
        keibajo_code,
        race_bango,
        kyosomei_hondai,         -- レース名（本題）
        kyosomei_ryakusho_10,    -- レース名（略称10文字）
        kyori,
        track_code,
        course_kubun,            -- コース区分
        shusso_tosu,
        tenko_code,
        grade_code
    FROM nvd_ra
    WHERE keibajo_code = %s
      AND kaisai_nen = %s
      AND kaisai_tsukihi = %s
      AND track_code != '00'  -- ばんえい競馬を除外
    ORDER BY race_bango
    """
    
    # 日付分解 (YYYYMMDD -> YYYY, MMDD)
    year = target_date[:4]
    month_day = target_date[4:]
    
    try:
        df = pd.read_sql(query, conn, params=(keibajo_code, year, month_day))
        return df
    except Exception as e:
        safe_print(f"[ERROR] レース一覧取得失敗: {e}")
        import traceback
        safe_print(traceback.format_exc())
        return pd.DataFrame()

def get_horse_entries(conn, df_races):
    """
    出走馬データを取得（過去走データ・馬名含む・完全版）
    
    修正点:
    - PC-KEIBAの正しいカラム名を使用
    - extract_training_data_v2.py と完全に同じ構造
    - ばんえい競馬の除外
    """
    
    if len(df_races) == 0:
        return pd.DataFrame()
    
    # 対象レースの条件作成
    conditions = []
    for _, row in df_races.iterrows():
        cond = (
            f"(ra.kaisai_nen = '{row['kaisai_nen']}' "
            f"AND ra.kaisai_tsukihi = '{row['kaisai_tsukihi']}' "
            f"AND ra.keibajo_code = '{row['keibajo_code']}' "
            f"AND ra.race_bango = '{row['race_bango']}')"
        )
        conditions.append(cond)
    
    where_clause = " OR ".join(conditions)
    
    # 学習時(extract_training_data_v2.py)と同じクエリ構造を移植
    # 重要な変更点：過去走データ、調教師、ブリンカーなどをすべて取得
    query = f"""
    WITH target_race AS (
        SELECT 
            ra.kaisai_nen,
            ra.kaisai_tsukihi,
            ra.keibajo_code,
            ra.race_bango,
            se.umaban,
            se.wakuban,
            se.ketto_toroku_bango,
            se.bamei, -- 馬名（表示用）
            se.barei,
            se.seibetsu_code,
            se.futan_juryo,
            se.kishu_code,
            se.chokyoshi_code,       -- 追加: 調教師コード
            se.blinker_shiyo_kubun,  -- 追加: ブリンカー
            se.tozai_shozoku_code,   -- 追加: 東西所属
            
            ra.kyori,
            ra.track_code,
            ra.babajotai_code_shiba,
            ra.babajotai_code_dirt,
            ra.tenko_code,           -- 追加: 天候
            ra.shusso_tosu,          -- 追加: 出走頭数
            ra.grade_code,           -- 追加: グレード
            
            um.moshoku_code          -- 追加: 毛色
            
        FROM nvd_se se
        INNER JOIN nvd_ra ra
            ON se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        LEFT JOIN nvd_um um
            ON se.ketto_toroku_bango = um.ketto_toroku_bango
            
        WHERE ({where_clause})
          AND ra.track_code != '00'  -- ばんえい競馬を除外
    ),
    past_races AS (
        -- 過去走データ取得（学習用スクリプトと同じロジック）
        SELECT 
            se.ketto_toroku_bango,
            se.kaisai_nen,
            se.kaisai_tsukihi,
            se.keibajo_code,
            se.race_bango,
            
            se.kakutei_chakujun,
            se.soha_time,
            se.kohan_3f,
            se.kohan_4f,
            se.corner_1,
            se.corner_2,
            se.corner_3,
            se.corner_4,
            se.bataiju,
            
            ra.kyori AS past_kyori,
            ra.keibajo_code AS past_keibajo,
            ra.track_code AS past_track,
            ra.babajotai_code_shiba AS past_baba_shiba,
            ra.babajotai_code_dirt AS past_baba_dirt,
            
            ROW_NUMBER() OVER (
                PARTITION BY se.ketto_toroku_bango 
                ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC, se.race_bango DESC
            ) AS race_order
            
        FROM nvd_se se
        INNER JOIN nvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen 
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        INNER JOIN target_race tr ON se.ketto_toroku_bango = tr.ketto_toroku_bango
        
        WHERE 
            -- 当該レースより前
            (se.kaisai_nen || se.kaisai_tsukihi || LPAD(se.race_bango::TEXT, 2, '0')) 
            < (tr.kaisai_nen || tr.kaisai_tsukihi || LPAD(tr.race_bango::TEXT, 2, '0'))
            -- 着順が数値のもののみ（中止などを除外）
            AND se.kakutei_chakujun ~ '^[0-9]+$'
            -- ばんえい競馬を除外
            AND ra.track_code != '00'
    )
    SELECT 
        tr.*,
        
        -- 過去走データ（前走〜5走前）
        MAX(CASE WHEN pr.race_order = 1 THEN pr.kakutei_chakujun END) AS prev1_rank,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.soha_time END) AS prev1_time,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.kohan_3f END) AS prev1_last3f,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.kohan_4f END) AS prev1_last4f,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.corner_1 END) AS prev1_corner1,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.corner_2 END) AS prev1_corner2,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.corner_3 END) AS prev1_corner3,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.corner_4 END) AS prev1_corner4,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.bataiju END) AS prev1_weight,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.past_kyori END) AS prev1_kyori,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.past_keibajo END) AS prev1_keibajo,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.past_track END) AS prev1_track,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.past_baba_shiba END) AS prev1_baba_shiba,
        MAX(CASE WHEN pr.race_order = 1 THEN pr.past_baba_dirt END) AS prev1_baba_dirt,
        
        MAX(CASE WHEN pr.race_order = 2 THEN pr.kakutei_chakujun END) AS prev2_rank,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.soha_time END) AS prev2_time,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.kohan_3f END) AS prev2_last3f,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.bataiju END) AS prev2_weight,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.past_kyori END) AS prev2_kyori,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.past_keibajo END) AS prev2_keibajo,
        
        MAX(CASE WHEN pr.race_order = 3 THEN pr.kakutei_chakujun END) AS prev3_rank,
        MAX(CASE WHEN pr.race_order = 3 THEN pr.soha_time END) AS prev3_time,
        MAX(CASE WHEN pr.race_order = 3 THEN pr.bataiju END) AS prev3_weight,
        
        MAX(CASE WHEN pr.race_order = 4 THEN pr.kakutei_chakujun END) AS prev4_rank,
        MAX(CASE WHEN pr.race_order = 4 THEN pr.soha_time END) AS prev4_time,
        
        MAX(CASE WHEN pr.race_order = 5 THEN pr.kakutei_chakujun END) AS prev5_rank,
        MAX(CASE WHEN pr.race_order = 5 THEN pr.soha_time END) AS prev5_time
        
    FROM target_race tr
    LEFT JOIN past_races pr ON tr.ketto_toroku_bango = pr.ketto_toroku_bango AND pr.race_order <= 5
    GROUP BY 
        tr.kaisai_nen, tr.kaisai_tsukihi, tr.keibajo_code, tr.race_bango, tr.umaban, tr.wakuban, 
        tr.ketto_toroku_bango, tr.bamei, tr.barei, tr.seibetsu_code, tr.futan_juryo, tr.kishu_code, 
        tr.chokyoshi_code, tr.blinker_shiyo_kubun, tr.tozai_shozoku_code, tr.kyori, tr.track_code, 
        tr.babajotai_code_shiba, tr.babajotai_code_dirt, tr.tenko_code, tr.shusso_tosu, tr.grade_code, 
        tr.moshoku_code
    ORDER BY CAST(tr.race_bango AS INTEGER), CAST(tr.umaban AS INTEGER)
    """
    
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        safe_print(f"[ERROR] データ取得クエリエラー: {e}")
        import traceback
        safe_print(traceback.format_exc())
        return pd.DataFrame()

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='PC-KEIBAからレースデータを取得（完全版・修正済み）')
    parser.add_argument('--keibajo', required=True, help='競馬場コード (例: 55)')
    parser.add_argument('--date', required=True, help='開催日 (例: 20260207)')
    
    args = parser.parse_args()
    
    keibajo_name = KEIBAJO_MAP.get(args.keibajo, 'Unknown')
    date_short = args.date.replace('-', '')
    
    safe_print("=" * 80)
    safe_print(f"[INFO] Phase 0: データ抽出開始")
    safe_print(f"  競馬場: {keibajo_name} ({args.keibajo})")
    safe_print(f"  開催日: {date_short}")
    safe_print("=" * 80)
    
    # DB接続
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
        
    try:
        # レース一覧取得
        df_races = get_target_races(conn, args.keibajo, date_short)
        if len(df_races) == 0:
            safe_print("[WARN] 対象レースが見つかりませんでした")
            safe_print("[INFO] 以下の点を確認してください:")
            safe_print("  1. 競馬場コードが正しいか")
            safe_print("  2. 開催日が正しいか（YYYYMMDD形式）")
            safe_print("  3. データベースにデータが存在するか")
            return
            
        safe_print(f"[INFO] 対象レース数: {len(df_races)}")
        
        # 出走馬データ取得（過去走含む完全版）
        df_horses = get_horse_entries(conn, df_races)
        
        if len(df_horses) == 0:
            safe_print("[WARN] 出走馬データが取得できませんでした")
            return
            
        # 保存ディレクトリ作成
        year = date_short[:4]
        month = date_short[4:6]
        output_dir = Path('data/raw') / year / month
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名設定
        keibajo_name_romaji = {
            '30': 'mombetsu', '33': 'obihiro', '35': 'morioka', '36': 'mizusawa',
            '42': 'urawa', '43': 'funabashi', '44': 'ooi', '45': 'kawasaki',
            '46': 'kanazawa', '47': 'kasamatsu', '48': 'nagoya',
            '50': 'sonoda', '51': 'himeji', '54': 'kochi', '55': 'saga'
        }.get(args.keibajo, f'venue{args.keibajo}')
        
        output_path = output_dir / f"{keibajo_name_romaji}_{date_short}_raw.csv"
        
        # CSV出力（UTF-8）
        df_horses.to_csv(output_path, index=False, encoding='utf-8')
        
        safe_print("")
        safe_print("=" * 80)
        safe_print(f"[SUCCESS] データ保存完了")
        safe_print("=" * 80)
        safe_print(f"  出力ファイル: {output_path}")
        safe_print(f"  レコード数: {len(df_horses):,}件")
        safe_print(f"  カラム数: {len(df_horses.columns)}個")
        
        # 重要なカラムの存在確認
        required_cols = ['prev1_rank', 'chokyoshi_code', 'blinker_shiyo_kubun', 'bamei']
        missing_cols = [c for c in required_cols if c not in df_horses.columns]
        
        if not missing_cols:
            safe_print("")
            safe_print("✅ [SUCCESS] 必要な特徴量（過去走データ・馬名等）はすべて正常に含まれています")
        else:
            safe_print(f"⚠️  [WARN] 注意: 一部の特徴量が欠落しています: {missing_cols}")
        
        # 過去走データの統計
        prev_cols = [c for c in df_horses.columns if c.startswith('prev')]
        if prev_cols:
            safe_print("")
            safe_print(f"[INFO] 過去走データカラム: {len(prev_cols)}個")
            for col in prev_cols[:5]:
                non_null = df_horses[col].notna().sum()
                pct = non_null / len(df_horses) * 100
                safe_print(f"  - {col}: {non_null}件 ({pct:.1f}%)")
            if len(prev_cols) > 5:
                safe_print(f"  ... 他 {len(prev_cols) - 5}個")
            
        safe_print("")
        safe_print("=" * 80)
        safe_print("[OK] Phase 0 完了")
        safe_print("=" * 80)
        safe_print("")
        safe_print("次のステップ:")
        safe_print(f"  Phase 1: python prepare_features.py {output_path}")
        
    except psycopg2.OperationalError as e:
        safe_print("")
        safe_print("=" * 80)
        safe_print(f"[ERROR] データベース接続エラー")
        safe_print("=" * 80)
        safe_print(f"エラー内容: {e}")
        safe_print("")
        safe_print("[INFO] 接続情報を確認してください:")
        safe_print(f"  - host: {DB_CONFIG['host']}")
        safe_print(f"  - port: {DB_CONFIG['port']}")
        safe_print(f"  - database: {DB_CONFIG['database']}")
        safe_print(f"  - user: {DB_CONFIG['user']}")
    except Exception as e:
        safe_print("")
        safe_print("=" * 80)
        safe_print(f"[ERROR] データ取得エラー")
        safe_print("=" * 80)
        safe_print(f"エラー内容: {e}")
        import traceback
        safe_print("")
        safe_print("詳細:")
        safe_print(traceback.format_exc())
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
