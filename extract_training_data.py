#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_training_data.py
PC-KEIBA Databaseから地方競馬の学習データを抽出してCSVに出力するスクリプト

使用法:
    python extract_training_data.py [オプション]

オプション:
    --keibajo CODE      特定の競馬場のみ抽出（例: 44=大井）
    --start-date YYYY   開始年（デフォルト: 2022）
    --end-date YYYY     終了年（デフォルト: 2024）
    --output FILE       出力CSVファイル名（デフォルト: training_data.csv）
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


def create_base_query(keibajo_code=None, start_year=None, end_year=None, limit=None):
    """基本的なデータ抽出SQLクエリを生成"""
    
    query = """
    SELECT 
        -- 目的変数
        CASE 
            WHEN se.chakujun ~ '^[0-9]+$' AND se.chakujun::INTEGER <= 3 THEN 1
            ELSE 0
        END AS target,
        
        -- 識別情報（学習には使わないが、分析用に保持）
        ra.kaisai_nen,
        ra.kaisai_tsukihi,
        ra.keibajo_code,
        ra.race_bango,
        se.uma_code,
        se.umaban,
        
        -- === レース情報 ===
        ra.kyori,
        ra.track_code,
        ra.baba_jotai_code,
        ra.tenkou_code,
        ra.tosu,
        ra.grade_code,
        
        -- === 出馬情報 ===
        se.wakuban,
        se.seibetsu_code,
        se.barei,
        se.futan_juryo,
        se.kishu_code,
        se.chokyoshi_code,
        se.blinker,
        se.zokusho,
        
        -- === 馬情報 ===
        um.keiro_code,
        um.sire_code,
        um.broodmare_sire_code,
        
        -- === 過去走データ（前走1〜5） ===
        -- 前走1
        se.zensou1_chakujun,
        se.zensou1_time_sa,
        se.zensou1_agari_3f,
        se.zensou1_kyori,
        se.zensou1_keibajo,
        se.zensou1_baba,
        se.zensou1_bataiju,
        
        -- 前走2
        se.zensou2_chakujun,
        se.zensou2_time_sa,
        se.zensou2_agari_3f,
        se.zensou2_kyori,
        se.zensou2_keibajo,
        se.zensou2_baba,
        se.zensou2_bataiju,
        
        -- 前走3
        se.zensou3_chakujun,
        se.zensou3_time_sa,
        se.zensou3_agari_3f,
        se.zensou3_kyori,
        se.zensou3_keibajo,
        se.zensou3_baba,
        se.zensou3_bataiju,
        
        -- 前走4
        se.zensou4_chakujun,
        se.zensou4_time_sa,
        se.zensou4_agari_3f,
        se.zensou4_kyori,
        se.zensou4_keibajo,
        se.zensou4_baba,
        se.zensou4_bataiju,
        
        -- 前走5
        se.zensou5_chakujun,
        se.zensou5_time_sa,
        se.zensou5_agari_3f,
        se.zensou5_kyori,
        se.zensou5_keibajo,
        se.zensou5_baba,
        se.zensou5_bataiju

    FROM 
        nvd_ra ra
        INNER JOIN nvd_se se ON (
            ra.kaisai_nen = se.kaisai_nen 
            AND ra.kaisai_tsukihi = se.kaisai_tsukihi
            AND ra.keibajo_code = se.keibajo_code
            AND ra.race_bango = se.race_bango
        )
        LEFT JOIN nvd_um um ON (
            se.uma_code = um.uma_code
        )

    WHERE 
        -- 着順が確定している（取消・除外を除く）
        se.chakujun IS NOT NULL
        AND se.chakujun NOT IN ('取消', '除外', '中止', '失格')
        AND se.chakujun ~ '^[0-9]+$'
    """
    
    # 地方競馬場フィルタ
    if keibajo_code:
        query += f"\n        AND ra.keibajo_code = '{keibajo_code}'"
    else:
        keibajo_list = "', '".join(LOCAL_KEIBAJO_CODES)
        query += f"\n        AND ra.keibajo_code IN ('{keibajo_list}')"
    
    # 年フィルタ
    if start_year:
        query += f"\n        AND ra.kaisai_nen >= {start_year}"
    if end_year:
        query += f"\n        AND ra.kaisai_nen <= {end_year}"
    
    query += """
    ORDER BY 
        ra.kaisai_nen DESC,
        ra.kaisai_tsukihi DESC,
        ra.keibajo_code,
        ra.race_bango,
        se.umaban
    """
    
    # レコード数制限（テスト用）
    if limit:
        query += f"\n    LIMIT {limit}"
    
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
        df = pd.read_sql_query(query, conn)
        print(f"✅ データ抽出完了: {len(df):,}件")
        return df
    except Exception as e:
        print(f"❌ データ抽出エラー: {e}")
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
    id_columns = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 'uma_code', 'umaban']
    feature_columns = [col for col in df.columns if col not in id_columns + ['target']]
    
    # 特徴量の型変換（可能なものは数値に）
    for col in feature_columns:
        # 数値変換を試みる
        if df[col].dtype == 'object':
            # 数値文字列を数値に変換
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
            print(f"    - {col}: {null_counts[col] / len(df) * 100:.1f}% null")
        if len(high_null_cols) > 5:
            print(f"    ... 他 {len(high_null_cols) - 5}個")
    
    print(f"✅ 前処理完了")
    
    return df


def save_csv(df, output_file):
    """DataFrameをCSVに保存"""
    try:
        print(f"\n⏳ CSV保存中: {output_file}")
        df.to_csv(output_file, index=False, encoding='shift-jis')
        print(f"✅ CSV保存完了: {output_file}")
        print(f"  レコード数: {len(df):,}件")
        print(f"  カラム数: {len(df.columns)}個")
    except Exception as e:
        print(f"❌ CSV保存エラー: {e}")
        print(f"  UTF-8で再試行...")
        try:
            output_file_utf8 = output_file.replace('.csv', '_utf8.csv')
            df.to_csv(output_file_utf8, index=False, encoding='utf-8')
            print(f"✅ UTF-8で保存成功: {output_file_utf8}")
        except Exception as e2:
            print(f"❌ UTF-8保存も失敗: {e2}")
            sys.exit(1)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='PC-KEIBA Databaseから地方競馬の学習データを抽出'
    )
    parser.add_argument('--keibajo', type=str, help='競馬場コード（例: 44=大井）')
    parser.add_argument('--start-date', type=int, default=2022, help='開始年（デフォルト: 2022）')
    parser.add_argument('--end-date', type=int, default=2024, help='終了年（デフォルト: 2024）')
    parser.add_argument('--output', type=str, default='training_data.csv', help='出力ファイル名')
    parser.add_argument('--limit', type=int, help='最大レコード数（テスト用）')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("PC-KEIBA データ抽出ツール")
    print("=" * 80)
    print(f"開始年: {args.start_date}")
    print(f"終了年: {args.end_date}")
    
    if args.keibajo:
        keibajo_name = KEIBAJO_NAMES.get(args.keibajo, '不明')
        print(f"競馬場: {args.keibajo} ({keibajo_name})")
    else:
        print(f"競馬場: 全地方競馬場 ({len(LOCAL_KEIBAJO_CODES)}場)")
    
    print(f"出力ファイル: {args.output}")
    
    if args.limit:
        print(f"レコード制限: {args.limit:,}件（テストモード）")
    
    print()
    
    # データベース接続
    conn = connect_db()
    
    try:
        # SQLクエリ生成
        query = create_base_query(
            keibajo_code=args.keibajo,
            start_year=args.start_date,
            end_year=args.end_date,
            limit=args.limit
        )
        
        # データ抽出
        df = extract_data(conn, query)
        
        if len(df) == 0:
            print("⚠️  抽出データが0件です。条件を確認してください。")
            sys.exit(1)
        
        # データ前処理
        df = preprocess_data(df)
        
        # CSV保存
        save_csv(df, args.output)
        
        print("\n" + "=" * 80)
        print("✅ データ抽出完了")
        print("=" * 80)
        print(f"\n次のステップ:")
        print(f"  python train_development.py {args.output}")
        
    finally:
        conn.close()
        print("\nデータベース接続を閉じました")


if __name__ == "__main__":
    main()
