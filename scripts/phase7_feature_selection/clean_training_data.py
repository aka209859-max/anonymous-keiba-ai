#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_training_data.py
Phase 7-1: 学習データクリーニング

PC-KEIBAデータベースから不正なレース結果を除外し、
Boruta特徴量選択用の高品質な学習データを作成します。

除外対象:
    - 取消 (race_result = '取消')
    - 中止 (race_result = '中止')
    - 除外 (race_result = '除外')
    - 失格 (race_result = '失格')

降着データの処理:
    - 「3(5)」のような括弧付き着順 → 3（確定着順）を採用

使用法:
    python clean_training_data.py --venue 名古屋 --start-date 2022-01-01 --end-date 2025-12-31
    
出力:
    - data/training/cleaned/{venue}_{start}_{end}_cleaned.csv
    - data/training/cleaned/{venue}_{start}_{end}_stats.json（統計情報）
"""

import sys
import os
import pandas as pd
import numpy as np
import json
import argparse
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def connect_to_pckeiba():
    """
    PC-KEIBAデータベースに接続
    
    Returns:
        psycopg2.connection: データベース接続
    """
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="keiba",
            user="postgres",
            password=""  # 環境変数から取得推奨
        )
        
        print("✅ PC-KEIBAデータベース接続成功")
        return conn
        
    except Exception as e:
        print(f"❌ エラー: データベース接続に失敗しました - {e}")
        print("\n対処法:")
        print("  1. PostgreSQLが起動しているか確認")
        print("  2. データベース名・ユーザー名・パスワードを確認")
        print("  3. PC-KEIBAがインストールされているか確認")
        sys.exit(1)


def extract_training_data(conn, venue, start_date, end_date):
    """
    PC-KEIBAから学習データを抽出
    
    Args:
        conn: データベース接続
        venue: 競馬場名（例: '名古屋', '船橋'）
        start_date: 開始日（YYYY-MM-DD）
        end_date: 終了日（YYYY-MM-DD）
    
    Returns:
        pd.DataFrame: 学習データ
    """
    print("\n" + "=" * 80)
    print("[1/4] PC-KEIBAからデータ抽出中...")
    print("=" * 80)
    print(f"競馬場: {venue}")
    print(f"期間: {start_date} ～ {end_date}")
    
    # 競馬場コード取得（例: 名古屋 → 43）
    venue_code_map = {
        '門別': 30, '盛岡': 35, '水沢': 36, '浦和': 42,
        '船橋': 43, '大井': 44, '川崎': 45, '金沢': 46,
        '笠松': 47, '名古屋': 48, '園田': 50, '姫路': 51,
        '高知': 54, '佐賀': 55, '帯広': 65
    }
    
    venue_code = venue_code_map.get(venue)
    
    if venue_code is None:
        print(f"❌ エラー: 未対応の競馬場 - {venue}")
        sys.exit(1)
    
    # SQL: レース結果と特徴量を抽出
    sql = """
    SELECT
        -- レース識別情報
        r.kaisai_nen,
        r.kaisai_tsukihi,
        r.keibajo_code,
        r.race_bango,
        
        -- 出走馬情報
        r.ketto_toroku_bango,
        r.umaban,
        r.wakuban,
        
        -- レース結果（目的変数）
        r.kakutei_chakujun,
        r.race_result,
        
        -- レース条件
        r.kyori,
        r.track_code,
        r.babajotai_code_shiba,
        r.babajotai_code_dirt,
        r.tenko_code,
        r.shusso_tosu,
        r.grade_code,
        
        -- 出馬情報
        r.seibetsu_code,
        r.barei,
        r.futan_juryo,
        r.kishu_code,
        r.chokyoshi_code,
        r.blinker_shiyo_kubun,
        r.tozai_shozoku_code,
        
        -- 馬基本情報
        h.moshoku_code,
        
        -- 前走1
        p1.kakutei_chakujun AS prev1_rank,
        p1.time AS prev1_time,
        p1.last3f AS prev1_last3f,
        p1.last4f AS prev1_last4f,
        p1.corner1 AS prev1_corner1,
        p1.corner2 AS prev1_corner2,
        p1.corner3 AS prev1_corner3,
        p1.corner4 AS prev1_corner4,
        p1.bataiju AS prev1_weight,
        p1.kyori AS prev1_kyori,
        p1.keibajo_code AS prev1_keibajo,
        p1.track_code AS prev1_track,
        p1.babajotai_code_shiba AS prev1_baba_shiba,
        p1.babajotai_code_dirt AS prev1_baba_dirt,
        
        -- 前走2
        p2.kakutei_chakujun AS prev2_rank,
        p2.time AS prev2_time,
        p2.last3f AS prev2_last3f,
        p2.bataiju AS prev2_weight,
        p2.kyori AS prev2_kyori,
        p2.keibajo_code AS prev2_keibajo,
        
        -- 前走3
        p3.kakutei_chakujun AS prev3_rank,
        p3.time AS prev3_time,
        p3.bataiju AS prev3_weight,
        
        -- 前走4
        p4.kakutei_chakujun AS prev4_rank,
        p4.time AS prev4_time,
        
        -- 前走5
        p5.kakutei_chakujun AS prev5_rank,
        p5.time AS prev5_time
        
    FROM
        race_results r
        LEFT JOIN horses h ON r.ketto_toroku_bango = h.ketto_toroku_bango
        LEFT JOIN race_results p1 ON r.prev1_race_id = p1.race_id AND r.ketto_toroku_bango = p1.ketto_toroku_bango
        LEFT JOIN race_results p2 ON r.prev2_race_id = p2.race_id AND r.ketto_toroku_bango = p2.ketto_toroku_bango
        LEFT JOIN race_results p3 ON r.prev3_race_id = p3.race_id AND r.ketto_toroku_bango = p3.ketto_toroku_bango
        LEFT JOIN race_results p4 ON r.prev4_race_id = p4.race_id AND r.ketto_toroku_bango = p4.ketto_toroku_bango
        LEFT JOIN race_results p5 ON r.prev5_race_id = p5.race_id AND r.ketto_toroku_bango = p5.ketto_toroku_bango
    WHERE
        r.keibajo_code = %s
        AND r.kaisai_nen::text || LPAD(r.kaisai_tsukihi::text, 4, '0') BETWEEN %s AND %s
    ORDER BY
        r.kaisai_nen, r.kaisai_tsukihi, r.race_bango, r.umaban
    """
    
    # 日付フォーマット変換（YYYY-MM-DD → YYYYMMDD）
    start_date_fmt = start_date.replace('-', '')
    end_date_fmt = end_date.replace('-', '')
    
    try:
        df = pd.read_sql_query(sql, conn, params=(venue_code, start_date_fmt, end_date_fmt))
        
        print(f"✅ データ抽出完了")
        print(f"  - レコード数: {len(df):,}件")
        print(f"  - カラム数: {len(df.columns)}個")
        print(f"  - レース数: {df.groupby(['kaisai_nen', 'kaisai_tsukihi', 'race_bango']).ngroups:,}件")
        
        return df
        
    except Exception as e:
        print(f"❌ エラー: データ抽出に失敗しました - {e}")
        sys.exit(1)


def clean_race_results(df):
    """
    不正なレース結果を除外
    
    除外対象:
        - 取消
        - 中止
        - 除外
        - 失格
    
    Args:
        df: DataFrame
    
    Returns:
        pd.DataFrame: クリーニング後のデータ
        dict: 統計情報
    """
    print("\n" + "=" * 80)
    print("[2/4] 不正なレース結果を除外中...")
    print("=" * 80)
    
    # 元のレコード数
    original_count = len(df)
    
    # 除外対象のレース結果
    invalid_results = ['取消', '中止', '除外', '失格']
    
    # 統計情報
    stats = {
        'original_count': original_count,
        'removed_records': {},
        'cleaned_count': 0,
        'removed_total': 0
    }
    
    # 除外対象をカウント
    for result in invalid_results:
        count = len(df[df['race_result'] == result])
        if count > 0:
            stats['removed_records'][result] = count
            print(f"  - {result}: {count:,}件")
    
    # 除外実行
    df_cleaned = df[~df['race_result'].isin(invalid_results)].copy()
    
    # 統計更新
    stats['cleaned_count'] = len(df_cleaned)
    stats['removed_total'] = original_count - stats['cleaned_count']
    
    print(f"\n✅ クリーニング完了")
    print(f"  - 除外レコード数: {stats['removed_total']:,}件 ({stats['removed_total'] / original_count * 100:.2f}%)")
    print(f"  - 残存レコード数: {stats['cleaned_count']:,}件 ({stats['cleaned_count'] / original_count * 100:.2f}%)")
    
    return df_cleaned, stats


def normalize_kakutei_chakujun(df):
    """
    確定着順を正規化
    
    降着データの処理:
        - 「3(5)」のような括弧付き着順 → 3（確定着順）を採用
        - 数値以外 → NaN
    
    Args:
        df: DataFrame
    
    Returns:
        pd.DataFrame: 正規化後のデータ
    """
    print("\n" + "=" * 80)
    print("[3/4] 確定着順を正規化中...")
    print("=" * 80)
    
    def parse_chakujun(value):
        """
        確定着順をパース
        
        例:
            '3(5)' → 3
            '10' → 10
            '中止' → NaN
        """
        if pd.isna(value):
            return np.nan
        
        value_str = str(value).strip()
        
        # 括弧付き着順の処理（例: '3(5)' → '3'）
        if '(' in value_str:
            value_str = value_str.split('(')[0]
        
        # 数値変換
        try:
            return int(value_str)
        except ValueError:
            return np.nan
    
    # 確定着順を正規化
    df['kakutei_chakujun'] = df['kakutei_chakujun'].apply(parse_chakujun)
    
    # 統計情報
    valid_count = df['kakutei_chakujun'].notna().sum()
    invalid_count = df['kakutei_chakujun'].isna().sum()
    
    print(f"✅ 正規化完了")
    print(f"  - 有効な着順: {valid_count:,}件")
    print(f"  - 無効な着順: {invalid_count:,}件")
    
    return df


def create_target_variables(df):
    """
    目的変数を作成
    
    - binary_target: 3着以内 = 1, 4着以下 = 0
    - rank_target: 着順（1～最大頭数）
    
    Args:
        df: DataFrame
    
    Returns:
        pd.DataFrame: 目的変数追加後のデータ
    """
    print("\n" + "=" * 80)
    print("[4/4] 目的変数を作成中...")
    print("=" * 80)
    
    # 二値分類用（3着以内 = 1）
    df['binary_target'] = (df['kakutei_chakujun'] <= 3).astype(int)
    
    # ランキング用（着順そのまま）
    df['rank_target'] = df['kakutei_chakujun']
    
    # 統計情報
    top3_count = (df['binary_target'] == 1).sum()
    total_count = len(df)
    
    print(f"✅ 目的変数作成完了")
    print(f"  - 3着以内: {top3_count:,}件 ({top3_count / total_count * 100:.2f}%)")
    print(f"  - 4着以下: {total_count - top3_count:,}件 ({(total_count - top3_count) / total_count * 100:.2f}%)")
    
    return df


def save_cleaned_data(df, stats, output_file, stats_file):
    """
    クリーニング済みデータを保存
    
    Args:
        df: DataFrame
        stats: 統計情報
        output_file: 出力CSVファイルパス
        stats_file: 統計JSONファイルパス
    """
    print("\n" + "=" * 80)
    print("保存中...")
    print("=" * 80)
    
    # 出力ディレクトリ作成
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ ディレクトリ作成: {output_dir}")
    
    # CSV保存
    df.to_csv(output_file, index=False, encoding='shift-jis')
    print(f"✅ CSV保存完了: {output_file}")
    print(f"  - レコード数: {len(df):,}件")
    print(f"  - カラム数: {len(df.columns)}個")
    
    # 統計情報保存
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"✅ 統計情報保存完了: {stats_file}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Phase 7-1: 学習データクリーニング',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    # 名古屋競馬の2022-2025年データをクリーニング
    python clean_training_data.py --venue 名古屋 --start-date 2022-01-01 --end-date 2025-12-31
    
    # 船橋競馬の2023年データをクリーニング
    python clean_training_data.py --venue 船橋 --start-date 2023-01-01 --end-date 2023-12-31
        """
    )
    
    parser.add_argument('--venue', type=str, required=True, help='競馬場名（例: 名古屋, 船橋）')
    parser.add_argument('--start-date', type=str, required=True, help='開始日（YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str, required=True, help='終了日（YYYY-MM-DD）')
    parser.add_argument('--output', type=str, help='出力CSVファイル（デフォルト: 自動生成）')
    
    args = parser.parse_args()
    
    # パラメータ表示
    print("=" * 80)
    print("Phase 7-1: 学習データクリーニング")
    print("=" * 80)
    print(f"競馬場: {args.venue}")
    print(f"期間: {args.start_date} ～ {args.end_date}")
    
    # 出力ファイル名の自動生成
    if args.output is None:
        start_fmt = args.start_date.replace('-', '')
        end_fmt = args.end_date.replace('-', '')
        output_basename = f"{args.venue}_{start_fmt}_{end_fmt}_cleaned.csv"
        stats_basename = f"{args.venue}_{start_fmt}_{end_fmt}_stats.json"
        
        output_dir = project_root / 'data' / 'training' / 'cleaned'
        args.output = str(output_dir / output_basename)
        stats_file = str(output_dir / stats_basename)
    else:
        stats_file = args.output.replace('.csv', '_stats.json')
    
    print(f"出力ファイル: {args.output}")
    print(f"統計ファイル: {stats_file}")
    print()
    
    # ============================================
    # Phase 7-1: データクリーニング
    # ============================================
    
    # [0/4] データベース接続
    conn = connect_to_pckeiba()
    
    # [1/4] データ抽出
    df = extract_training_data(conn, args.venue, args.start_date, args.end_date)
    
    # [2/4] 不正レース結果除外
    df, stats = clean_race_results(df)
    
    # [3/4] 確定着順正規化
    df = normalize_kakutei_chakujun(df)
    
    # [4/4] 目的変数作成
    df = create_target_variables(df)
    
    # 保存
    save_cleaned_data(df, stats, args.output, stats_file)
    
    # データベース接続終了
    conn.close()
    
    # 完了
    print("\n" + "=" * 80)
    print("✅ Phase 7-1: データクリーニング完了")
    print("=" * 80)
    print(f"\n次のステップ: Phase 7-2でBoruta特徴量選択を実行してください")
    print(f"  python run_boruta_selection.py {args.output}")


if __name__ == '__main__':
    main()
