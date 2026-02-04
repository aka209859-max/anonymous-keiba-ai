#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_training_data_v2.py
PC-KEIBA Databaseから地方競馬の学習データを抽出（過去走データ付き）

ROW_NUMBER()を使用してnvd_seテーブルを自己JOINし、
前走〜5走前のデータを取得します。

使用法:
    python extract_training_data_v2.py [オプション]

オプション:
    --keibajo CODE      特定の競馬場のみ抽出（例: 44=大井）
    --start-date YYYY   開始年（デフォルト: 2020）
    --end-date YYYY     終了年（デフォルト: 2025）
    --output FILE       出力CSVファイル名（デフォルト: training_data_v2.csv）
    --limit N           最大レコード数（テスト用）
"""

import sys
import argparse
import psycopg2
import pandas as pd
from datetime import datetime

# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

# 地方競馬場コード
LOCAL_KEIBAJO_CODES = ['30', '33', '35', '36', '42', '43', '44', '45', '46', '47', '48', '50', '51', '54', '55']

# 競馬場名マッピング
KEIBAJO_NAMES = {
    '30': '門別', '33': '帯広', '35': '盛岡', '36': '水沢',
    '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
    '46': '金沢', '47': '笠松', '48': '名古屋',
    '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
}


def create_query_with_past_races(keibajo_code=None, start_year=None, end_year=None, limit=None):
    """過去走データを含む学習データ抽出SQLクエリを生成
    
    ROW_NUMBER()を使用してnvd_seテーブルを自己JOINし、
    前走〜5走前のデータを取得します。
    """
    
    # 地方競馬場フィルタ
    if keibajo_code:
        keibajo_filter = f"AND ra.keibajo_code = '{keibajo_code}'"
    else:
        keibajo_list = "', '".join(LOCAL_KEIBAJO_CODES)
        keibajo_filter = f"AND ra.keibajo_code IN ('{keibajo_list}')"
    
    # 年フィルタ
    year_filter = ""
    if start_year:
        year_filter += f"\n        AND ra.kaisai_nen >= '{start_year}'"
    if end_year:
        year_filter += f"\n        AND ra.kaisai_nen <= '{end_year}'"
    
    # レコード数制限
    limit_clause = f"\n    LIMIT {limit}" if limit else ""
    
    query = f"""
    WITH target_race AS (
        -- 予測対象レース（学習データのレース）
        SELECT 
            ra.kaisai_nen,
            ra.kaisai_tsukihi,
            ra.keibajo_code,
            ra.race_bango,
            se.ketto_toroku_bango,
            se.umaban,
            se.kakutei_chakujun,
            
            -- レース情報
            ra.kyori,
            ra.track_code,
            ra.babajotai_code_shiba,
            ra.babajotai_code_dirt,
            ra.tenko_code,
            ra.shusso_tosu,
            ra.grade_code,
            
            -- 出馬情報（前日までに確定）
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
            -- 着順が確定している（取消・除外を除く）
            se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun NOT IN ('00', '取消', '除外', '中止', '失格')
            AND se.kakutei_chakujun ~ '^[0-9]+$'
            {keibajo_filter}
            {year_filter}
    ),
    past_races AS (
        -- その馬の過去走を全て取得
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
            
            -- 最新順に番号を付与（1=前走, 2=2走前, ...）
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
            -- 当該レースより前のレースのみ
            (se.kaisai_nen || se.kaisai_tsukihi || LPAD(se.race_bango::TEXT, 2, '0')) 
            < (tr.kaisai_nen || tr.kaisai_tsukihi || LPAD(tr.race_bango::TEXT, 2, '0'))
            -- 着順が確定している
            AND se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun ~ '^[0-9]+$'
    )
    SELECT 
        -- Target variable: 3rd place or better = 1, others = 0
        CASE 
            WHEN tr.kakutei_chakujun ~ '^[0-9]+$' AND tr.kakutei_chakujun::INTEGER <= 3 THEN 1
            ELSE 0
        END AS target,
        
        -- Race identifiers
        tr.kaisai_nen,
        tr.kaisai_tsukihi,
        tr.keibajo_code,
        tr.race_bango,
        tr.ketto_toroku_bango,
        tr.umaban,
        
        -- Race information
        tr.kyori,
        tr.track_code,
        tr.babajotai_code_shiba,
        tr.babajotai_code_dirt,
        tr.tenko_code,
        tr.shusso_tosu,
        tr.grade_code,
        
        -- Entry information
        tr.wakuban,
        tr.seibetsu_code,
        tr.barei,
        tr.futan_juryo,
        tr.kishu_code,
        tr.chokyoshi_code,
        tr.blinker_shiyo_kubun,
        tr.tozai_shozoku_code,
        
        -- Horse information
        tr.moshoku_code,
        
        -- Previous race 1
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
        
        -- Previous race 2
        MAX(CASE WHEN pr.race_order = 2 THEN pr.kakutei_chakujun END) AS prev2_rank,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.soha_time END) AS prev2_time,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.kohan_3f END) AS prev2_last3f,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.bataiju END) AS prev2_weight,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.past_kyori END) AS prev2_kyori,
        MAX(CASE WHEN pr.race_order = 2 THEN pr.past_keibajo END) AS prev2_keibajo,
        
        -- Previous race 3
        MAX(CASE WHEN pr.race_order = 3 THEN pr.kakutei_chakujun END) AS prev3_rank,
        MAX(CASE WHEN pr.race_order = 3 THEN pr.soha_time END) AS prev3_time,
        MAX(CASE WHEN pr.race_order = 3 THEN pr.bataiju END) AS prev3_weight,
        
        -- Previous race 4
        MAX(CASE WHEN pr.race_order = 4 THEN pr.kakutei_chakujun END) AS prev4_rank,
        MAX(CASE WHEN pr.race_order = 4 THEN pr.soha_time END) AS prev4_time,
        
        -- Previous race 5
        MAX(CASE WHEN pr.race_order = 5 THEN pr.kakutei_chakujun END) AS prev5_rank,
        MAX(CASE WHEN pr.race_order = 5 THEN pr.soha_time END) AS prev5_time
        
    FROM target_race tr
    LEFT JOIN past_races pr ON tr.ketto_toroku_bango = pr.ketto_toroku_bango AND pr.race_order <= 5
    GROUP BY 
        tr.kaisai_nen,
        tr.kaisai_tsukihi,
        tr.keibajo_code,
        tr.race_bango,
        tr.ketto_toroku_bango,
        tr.umaban,
        tr.kakutei_chakujun,
        tr.kyori,
        tr.track_code,
        tr.babajotai_code_shiba,
        tr.babajotai_code_dirt,
        tr.tenko_code,
        tr.shusso_tosu,
        tr.grade_code,
        tr.wakuban,
        tr.seibetsu_code,
        tr.barei,
        tr.futan_juryo,
        tr.kishu_code,
        tr.chokyoshi_code,
        tr.blinker_shiyo_kubun,
        tr.tozai_shozoku_code,
        tr.moshoku_code
    ORDER BY 
        tr.kaisai_nen DESC,
        tr.kaisai_tsukihi DESC,
        tr.keibajo_code,
        tr.race_bango,
        tr.umaban
    {limit_clause}
    """
    
    return query


def connect_db():
    """データベースに接続"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ データベース接続成功")
        return conn
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        print("\n接続情報を確認してください:")
        print(f"  ホスト: {DB_CONFIG['host']}")
        print(f"  ポート: {DB_CONFIG['port']}")
        print(f"  DB名: {DB_CONFIG['database']}")
        print(f"  ユーザー: {DB_CONFIG['user']}")
        sys.exit(1)


def extract_data(conn, query):
    """SQLクエリを実行してDataFrameで取得"""
    try:
        print("⏳ データ抽出中...")
        print("  ※ 過去走データを含むため、処理に時間がかかる場合があります")
        df = pd.read_sql_query(query, conn)
        print(f"✅ データ抽出完了: {len(df):,}件")
        return df
    except Exception as e:
        print(f"❌ データ抽出エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def preprocess_data(df):
    """データの前処理"""
    print("\n⏳ データ前処理中...")
    
    original_count = len(df)
    
    # 目的変数の確認
    target_dist = df['target'].value_counts()
    print(f"  目的変数の分布:")
    print(f"    クラス 0: {target_dist.get(0, 0):,}件 ({target_dist.get(0, 0) / len(df) * 100:.1f}%)")
    print(f"    クラス 1: {target_dist.get(1, 0):,}件 ({target_dist.get(1, 0) / len(df) * 100:.1f}%)")
    
    # 識別カラムと目的変数を分離
    id_columns = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 'ketto_toroku_bango', 'umaban']
    
    feature_columns = [col for col in df.columns if col not in id_columns + ['target']]
    
    # 特徴量の型変換（可能なものは数値に）
    for col in feature_columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
    
    # 欠損値の確認
    null_counts = df[feature_columns].isnull().sum()
    high_null_cols = null_counts[null_counts > len(df) * 0.8].index.tolist()
    
    if high_null_cols:
        print(f"  警告: 欠損率80%超のカラム ({len(high_null_cols)}個):")
        for col in high_null_cols[:5]:
            null_pct = null_counts[col] / len(df) * 100
            print(f"    {col}: {null_pct:.1f}%")
        if len(high_null_cols) > 5:
            print(f"    ... 他 {len(high_null_cols) - 5}個")
    
    print(f"✅ 前処理完了")
    print(f"  使用可能な特徴量: {len(feature_columns)}個")
    
    return df


def save_csv(df, output_file):
    """CSVファイルに保存"""
    try:
        df.to_csv(output_file, index=False, encoding='shift-jis')
        print(f"\n✅ CSV保存完了: {output_file}")
        print(f"  レコード数: {len(df):,}件")
        print(f"  カラム数: {len(df.columns)}個")
    except Exception as e:
        print(f"❌ CSV保存エラー（Shift-JIS）: {e}")
        print("  UTF-8で保存を試みます...")
        try:
            output_file_utf8 = output_file.replace('.csv', '_utf8.csv')
            df.to_csv(output_file_utf8, index=False, encoding='utf-8')
            print(f"✅ CSV保存完了（UTF-8）: {output_file_utf8}")
        except Exception as e2:
            print(f"❌ CSV保存失敗: {e2}")
            sys.exit(1)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='PC-KEIBA Databaseから地方競馬の学習データを抽出（過去走データ付き）')
    parser.add_argument('--keibajo', type=str, help='競馬場コード（例: 44=大井）')
    parser.add_argument('--start-date', type=str, default='2020', help='開始年（デフォルト: 2020）')
    parser.add_argument('--end-date', type=str, default='2025', help='終了年（デフォルト: 2025）')
    parser.add_argument('--output', type=str, default='training_data_v2.csv', help='出力CSVファイル名')
    parser.add_argument('--limit', type=int, help='最大レコード数（テスト用）')
    
    args = parser.parse_args()
    
    # パラメータ表示
    print("=" * 80)
    print("PC-KEIBA 地方競馬 学習データ抽出（過去走データ付き）")
    print("=" * 80)
    print(f"開始年: {args.start_date}")
    print(f"終了年: {args.end_date}")
    
    if args.keibajo:
        keibajo_name = KEIBAJO_NAMES.get(args.keibajo, '不明')
        print(f"競馬場: {args.keibajo} ({keibajo_name})")
    else:
        print(f"競馬場: 全地方競馬場 ({len(LOCAL_KEIBAJO_CODES)}競馬場)")
    
    print(f"出力ファイル: {args.output}")
    
    if args.limit:
        print(f"レコード数制限: {args.limit:,}件（テストモード）")
    
    print("\n" + "=" * 80)
    
    # データベース接続
    conn = connect_db()
    
    # SQLクエリ生成
    query = create_query_with_past_races(
        keibajo_code=args.keibajo,
        start_year=args.start_date,
        end_year=args.end_date,
        limit=args.limit
    )
    
    # データ抽出
    df = extract_data(conn, query)
    
    # データベース接続を閉じる
    conn.close()
    print("✅ データベース接続を閉じました")
    
    # 前処理
    df = preprocess_data(df)
    
    # CSV保存
    save_csv(df, args.output)
    
    print("\n" + "=" * 80)
    print("✅ 処理完了")
    print("=" * 80)


if __name__ == '__main__':
    main()
