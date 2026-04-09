#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_rank_fukusho_rate_from_db.py
PC-KEIBAデータベースから過去データを取得し、競馬場別・ランク別の複勝率を計算

【データソース】
- PC-KEIBA PostgreSQLデータベース
- nvd_ra: レース情報
- nvd_se: 出馬表・結果

【計算対象】
- 1位のSランク複勝率
- 1位のAランク複勝率
- 2位のSランク複勝率
- 2位のAランク複勝率
- 2位のBランク複勝率

使用法:
    python analyze_rank_fukusho_rate_from_db.py --year 2025
    python analyze_rank_fukusho_rate_from_db.py --year 2025 --venue kawasaki
    python analyze_rank_fukusho_rate_from_db.py --year 2025 --month 01-06
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import psycopg2
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# データベース接続情報
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

# 競馬場コード→名前のマッピング
VENUE_CODE_TO_NAME = {
    '30': '門別', '35': '盛岡', '36': '水沢',
    '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
    '46': '金沢', '47': '笠松', '48': '名古屋',
    '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
}

VENUE_NAME_TO_CODE = {v: k for k, v in VENUE_CODE_TO_NAME.items()}

def get_db_connection():
    """データベース接続を取得"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ DB接続失敗: {e}")
        return None


def get_rank_from_score(score):
    """スコアからランクを判定"""
    if score >= 0.80:
        return 'S'
    elif score >= 0.70:
        return 'A'
    elif score >= 0.60:
        return 'B'
    elif score >= 0.50:
        return 'C'
    else:
        return 'D'


def load_predictions_and_actuals(conn, year, venue_code=None, month_range=None):
    """
    予測結果CSVと実際の結果をPC-KEIBAから取得・マージ
    
    Parameters:
    -----------
    conn : psycopg2.connection
        データベース接続
    year : str
        対象年（例: '2025'）
    venue_code : str, optional
        競馬場コード（例: '45'=川崎）
    month_range : str, optional
        月範囲（例: '01-06'）
    
    Returns:
    --------
    pd.DataFrame
        race_id, horse_no, ensemble_score, actual_rank を含むDataFrame
    """
    
    # 予測結果CSVファイルを検索（複数のディレクトリを試行）
    possible_dirs = [
        Path('data/predictions/phase5'),  # メインディレクトリ（優先）
        Path('data/predictions/phase5_ensemble'),
        Path('predictions/phase5_ooi_2025'),
        Path('predictions'),
        Path('results'),
        Path('data/results'),
        Path('.'),  # カレントディレクトリ
    ]
    
    predictions_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            csv_files = list(dir_path.glob('*.csv'))
            if csv_files:
                predictions_dir = dir_path
                print(f"✅ 予測ディレクトリ発見: {predictions_dir} ({len(csv_files)} 個のCSV)")
                break
            else:
                print(f"⚠️  ディレクトリ発見（CSVなし）: {dir_path}")
    
    if predictions_dir is None:
        print(f"❌ 予測CSVが見つかりません")
        print(f"\n検索したディレクトリ:")
        for dir_path in possible_dirs:
            status = "存在" if dir_path.exists() else "存在しない"
            print(f"  - {dir_path}: {status}")
        print(f"\n💡 解決方法:")
        print(f"  1. run_all_FINAL.bat でPhase 5まで実行")
        print(f"  2. または、CSVファイルの場所を確認:")
        print(f"     dir /s /b *.csv | findstr /i ensemble")
        return pd.DataFrame()
    
    # 月範囲フィルタ
    if month_range:
        start_month, end_month = month_range.split('-')
        month_filter = lambda m: start_month <= m <= end_month
    else:
        month_filter = lambda m: True
    
    # 競馬場フィルタ
    if venue_code:
        venue_name = VENUE_CODE_TO_NAME.get(venue_code)
        if not venue_name:
            print(f"❌ 不明な競馬場コード: {venue_code}")
            return pd.DataFrame()
        venue_filter = [venue_name]
    else:
        venue_filter = list(VENUE_CODE_TO_NAME.values())
    
    # 全予測CSVを読み込み
    all_predictions = []
    
    for csv_file in predictions_dir.glob(f'*{year}*.csv'):
        # CSV読み込み（ファイル名フィルタ前に読み込んで、keibajo_codeで判定）
        try:
            df = pd.read_csv(csv_file, encoding='shift-jis')
        except:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
            except Exception as e:
                print(f"⚠️  読み込みエラー: {csv_file.name} - {e}")
                continue
        
        # 必要なカラムを確認
        if 'race_id' not in df.columns or 'ensemble_score' not in df.columns:
            print(f"⚠️  必要なカラムがありません: {csv_file.name}")
            continue
        
        # keibajo_codeカラムがあればそれを使用、無ければrace_idから抽出
        if 'keibajo_code' in df.columns:
            df['keibajo_code_str'] = df['keibajo_code'].astype(str).str.zfill(2)
        else:
            # race_idから競馬場コードを抽出（8～9桁目）
            df['keibajo_code_str'] = df['race_id'].astype(str).str[8:10]
        
        # 競馬場フィルタ適用
        if venue_code:
            # 特定競馬場のみ
            df = df[df['keibajo_code_str'] == venue_code].copy()
            if df.empty:
                continue
        else:
            # 全競馬場（登録されている14場のみ）
            valid_codes = list(VENUE_CODE_TO_NAME.keys())
            df = df[df['keibajo_code_str'].isin(valid_codes)].copy()
            if df.empty:
                continue
        
        # 月フィルタ適用
        if month_range:
            # race_idから月を抽出（5～6桁目）
            df['month_str'] = df['race_id'].astype(str).str[4:6]
            df = df[df['month_str'].apply(month_filter)].copy()
            if df.empty:
                continue
        
        # 競馬場名をマッピング
        df['venue'] = df['keibajo_code_str'].map(VENUE_CODE_TO_NAME)
        
        all_predictions.append(df)
        print(f"📄 読み込み: {csv_file.name} ({len(df)} 行)")
    
    if not all_predictions:
        print("❌ 予測CSVが見つかりませんでした")
        return pd.DataFrame()
    
    df_predictions = pd.concat(all_predictions, ignore_index=True)
    print(f"\n✅ 予測データ読み込み完了: {len(df_predictions)} 行, {df_predictions['race_id'].nunique()} レース")
    
    # PC-KEIBAから実際の結果を取得
    print("\n📊 PC-KEIBAから実際の結果を取得中...")
    
    # race_idから年・月日・競馬場・レース番号を抽出
    # race_id例: 202502034501 → 2025, 0203, 45, 01
    df_predictions['kaisai_nen'] = df_predictions['race_id'].astype(str).str[:4]
    df_predictions['kaisai_tsukihi'] = df_predictions['race_id'].astype(str).str[4:8]
    df_predictions['keibajo_code'] = df_predictions['race_id'].astype(str).str[8:10]
    df_predictions['race_bango'] = df_predictions['race_id'].astype(str).str[10:12]
    
    # umaban列の確認（horse_noがある場合は使用）
    if 'horse_no' in df_predictions.columns:
        df_predictions['umaban'] = df_predictions['horse_no']
    elif 'umaban' not in df_predictions.columns:
        print("❌ horse_no または umaban カラムが見つかりません")
        return pd.DataFrame()
    
    # 数値型に統一してから文字列に変換
    df_predictions['umaban'] = pd.to_numeric(df_predictions['umaban'], errors='coerce').astype('Int64').astype(str).str.zfill(2)
    
    # PC-KEIBAから着順を取得
    race_conditions = []
    for _, row in df_predictions[['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango']].drop_duplicates().iterrows():
        cond = f"(kaisai_nen = '{row['kaisai_nen']}' AND kaisai_tsukihi = '{row['kaisai_tsukihi']}' AND keibajo_code = '{row['keibajo_code']}' AND race_bango = '{row['race_bango']}')"
        race_conditions.append(cond)
    
    where_clause = " OR ".join(race_conditions)
    
    query = f"""
    SELECT 
        kaisai_nen,
        kaisai_tsukihi,
        keibajo_code,
        race_bango,
        umaban,
        kakutei_chakujun as actual_rank
    FROM nvd_se
    WHERE ({where_clause})
      AND kakutei_chakujun IS NOT NULL
      AND kakutei_chakujun != '00'
    """
    
    try:
        df_actuals = pd.read_sql(query, conn)
        print(f"✅ 実績データ取得完了: {len(df_actuals)} 行")
        
        # デバッグ: 実績データのサンプルを表示
        if len(df_actuals) > 0:
            print(f"\n🔍 実績データサンプル:")
            print(f"   kaisai_nen例: {df_actuals['kaisai_nen'].iloc[0]}")
            print(f"   kaisai_tsukihi例: {df_actuals['kaisai_tsukihi'].iloc[0]} (桁数: {len(str(df_actuals['kaisai_tsukihi'].iloc[0]))})")
            print(f"   keibajo_code例: {df_actuals['keibajo_code'].iloc[0]}")
            print(f"   race_bango例: {df_actuals['race_bango'].iloc[0]}")
            print(f"   umaban例: {df_actuals['umaban'].iloc[0]}")
        else:
            print(f"\n⚠️  実績データが0件です！")
            print(f"   予測データの条件例:")
            sample = df_predictions.iloc[0]
            print(f"   kaisai_nen: {sample['kaisai_nen']}")
            print(f"   kaisai_tsukihi: {sample['kaisai_tsukihi']}")
            print(f"   keibajo_code: {sample['keibajo_code']}")
            print(f"   race_bango: {sample['race_bango']}")
    except Exception as e:
        print(f"❌ 実績データ取得失敗: {e}")
        return pd.DataFrame()
    
    # データ型を統一（文字列に変換）
    # 実績データ側
    df_actuals['umaban'] = pd.to_numeric(df_actuals['umaban'], errors='coerce').astype('Int64').astype(str).str.zfill(2)
    df_actuals['actual_rank'] = pd.to_numeric(df_actuals['actual_rank'], errors='coerce')
    df_actuals['kaisai_nen'] = df_actuals['kaisai_nen'].astype(str)
    df_actuals['kaisai_tsukihi'] = df_actuals['kaisai_tsukihi'].astype(str).str.zfill(4)
    df_actuals['keibajo_code'] = df_actuals['keibajo_code'].astype(str).str.zfill(2)
    df_actuals['race_bango'] = df_actuals['race_bango'].astype(str).str.zfill(2)
    
    # 予測データ側
    df_predictions['kaisai_nen'] = df_predictions['kaisai_nen'].astype(str)
    df_predictions['kaisai_tsukihi'] = df_predictions['kaisai_tsukihi'].astype(str).str.zfill(4)
    df_predictions['keibajo_code'] = df_predictions['keibajo_code'].astype(str).str.zfill(2)
    df_predictions['race_bango'] = df_predictions['race_bango'].astype(str).str.zfill(2)
    
    # マージ
    df_merged = pd.merge(
        df_predictions,
        df_actuals[['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 'umaban', 'actual_rank']],
        on=['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 'umaban'],
        how='inner'
    )
    
    print(f"✅ マージ完了: {len(df_merged)} 行, {df_merged['race_id'].nunique()} レース")
    
    # デバッグ: マージ前後のレコード数を比較
    pred_records = len(df_predictions)
    actual_records = len(df_actuals)
    merged_records = len(df_merged)
    match_rate = (merged_records / pred_records * 100) if pred_records > 0 else 0
    
    print(f"\n🔍 マージ統計:")
    print(f"   予測データ: {pred_records} 行")
    print(f"   実績データ: {actual_records} 行")
    print(f"   マージ後: {merged_records} 行 ({match_rate:.1f}%)")
    
    if match_rate < 80:
        print(f"\n⚠️  警告: マッチ率が低い ({match_rate:.1f}%)です")
        print(f"   原因候補:")
        print(f"   1. PC-KEIBAに2026年データが無い")
        print(f"   2. kaisai_tsukihiのフォーマット不一致")
        print(f"   3. レースがまだ実施されていない（未来のレース）")
        
        # サンプル比較
        if len(df_predictions) > 0 and len(df_actuals) > 0:
            print(f"\n   予測データ例:")
            sample_pred = df_predictions.iloc[0]
            print(f"   {sample_pred['kaisai_nen']}-{sample_pred['kaisai_tsukihi']}-{sample_pred['keibajo_code']}-{sample_pred['race_bango']}")
            print(f"\n   実績データ例:")
            sample_act = df_actuals.iloc[0]
            print(f"   {sample_act['kaisai_nen']}-{sample_act['kaisai_tsukihi']}-{sample_act['keibajo_code']}-{sample_act['race_bango']}")
    
    return df_merged


def analyze_fukusho_rate(df):
    """
    ランク別複勝率を計算
    
    Parameters:
    -----------
    df : pd.DataFrame
        race_id, ensemble_score, actual_rank を含むDataFrame
    
    Returns:
    --------
    dict
        競馬場別の複勝率統計
    """
    
    # ランク列を追加
    df['rank_label'] = df['ensemble_score'].apply(get_rank_from_score)
    
    # 競馬場別に集計
    venue_stats = defaultdict(lambda: {
        'total_races': 0,
        '1st_S': {'hits': 0, 'total': 0},
        '1st_A': {'hits': 0, 'total': 0},
        '2nd_S': {'hits': 0, 'total': 0},
        '2nd_A': {'hits': 0, 'total': 0},
        '2nd_B': {'hits': 0, 'total': 0}
    })
    
    # レースごとに処理
    for race_id, group in df.groupby('race_id'):
        # スコアでソート（降順）
        sorted_group = group.sort_values('ensemble_score', ascending=False).reset_index(drop=True)
        
        if len(sorted_group) < 2:
            continue
        
        venue = sorted_group.iloc[0]['venue']
        venue_stats[venue]['total_races'] += 1
        
        # 1位の馬
        first_horse = sorted_group.iloc[0]
        first_rank = first_horse['rank_label']
        first_actual = first_horse['actual_rank']
        
        # 1位がSランク
        if first_rank == 'S':
            venue_stats[venue]['1st_S']['total'] += 1
            if pd.notna(first_actual) and first_actual <= 3:
                venue_stats[venue]['1st_S']['hits'] += 1
        
        # 1位がAランク
        if first_rank == 'A':
            venue_stats[venue]['1st_A']['total'] += 1
            if pd.notna(first_actual) and first_actual <= 3:
                venue_stats[venue]['1st_A']['hits'] += 1
        
        # 2位の馬
        second_horse = sorted_group.iloc[1]
        second_rank = second_horse['rank_label']
        second_actual = second_horse['actual_rank']
        
        # 2位がSランク
        if second_rank == 'S':
            venue_stats[venue]['2nd_S']['total'] += 1
            if pd.notna(second_actual) and second_actual <= 3:
                venue_stats[venue]['2nd_S']['hits'] += 1
        
        # 2位がAランク
        if second_rank == 'A':
            venue_stats[venue]['2nd_A']['total'] += 1
            if pd.notna(second_actual) and second_actual <= 3:
                venue_stats[venue]['2nd_A']['hits'] += 1
        
        # 2位がBランク
        if second_rank == 'B':
            venue_stats[venue]['2nd_B']['total'] += 1
            if pd.notna(second_actual) and second_actual <= 3:
                venue_stats[venue]['2nd_B']['hits'] += 1
    
    # 複勝率を計算
    for venue in venue_stats:
        for key in ['1st_S', '1st_A', '2nd_S', '2nd_A', '2nd_B']:
            total = venue_stats[venue][key]['total']
            if total > 0:
                hits = venue_stats[venue][key]['hits']
                venue_stats[venue][key]['rate'] = hits / total * 100
            else:
                venue_stats[venue][key]['rate'] = 0.0
    
    return dict(venue_stats)


def print_results(venue_stats, output_file=None):
    """結果を表形式で出力
    
    Parameters:
    -----------
    venue_stats : dict
        競馬場別の統計データ
    output_file : str, optional
        出力ファイルパス（指定時はTXTファイルに保存）
    """
    
    # 出力内容を文字列として構築
    lines = []
    lines.append("\n" + "=" * 120)
    lines.append("📊 競馬場別・ランク別 複勝率分析結果（PC-KEIBAデータベース）")
    lines.append("=" * 120)
    lines.append("")
    
    # ヘッダー
    header = f"{'競馬場':<10} {'レース数':>8} | {'1位S複勝':>12} | {'1位A複勝':>12} | {'2位S複勝':>12} | {'2位A複勝':>12} | {'2位B複勝':>12}"
    lines.append(header)
    lines.append("-" * 120)
    
    # 各競馬場の結果
    for venue in sorted(venue_stats.keys()):
        stats = venue_stats[venue]
        
        total_races = stats['total_races']
        
        # 各ランクの文字列生成
        def format_stat(key):
            hits = stats[key]['hits']
            total = stats[key]['total']
            rate = stats[key]['rate']
            return f"{hits}/{total} ({rate:5.1f}%)" if total > 0 else "-"
        
        row = f"{venue:<10} {total_races:>8} | {format_stat('1st_S'):>12} | {format_stat('1st_A'):>12} | {format_stat('2nd_S'):>12} | {format_stat('2nd_A'):>12} | {format_stat('2nd_B'):>12}"
        lines.append(row)
    
    lines.append("=" * 120)
    lines.append("")
    
    # 全体サマリー
    lines.append("📈 全体サマリー")
    lines.append("-" * 120)
    
    total_races = sum(v['total_races'] for v in venue_stats.values())
    
    def calc_total(key):
        total_hits = sum(v[key]['hits'] for v in venue_stats.values())
        total_total = sum(v[key]['total'] for v in venue_stats.values())
        total_rate = (total_hits / total_total * 100) if total_total > 0 else 0
        return total_hits, total_total, total_rate
    
    lines.append(f"総レース数: {total_races}")
    lines.append("")
    
    for label, key in [('1位Sランク', '1st_S'), ('1位Aランク', '1st_A'), 
                       ('2位Sランク', '2nd_S'), ('2位Aランク', '2nd_A'), ('2位Bランク', '2nd_B')]:
        hits, total, rate = calc_total(key)
        lines.append(f"【{label}】 {hits}/{total} ({rate:.1f}%)")
    
    lines.append("")
    
    # 画面出力
    output_text = "\n".join(lines)
    print(output_text)
    
    # ファイル出力（指定時）
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"\n💾 結果を保存しました: {output_file}")
        except Exception as e:
            print(f"\n⚠️  ファイル保存エラー: {e}")


def main():
    parser = argparse.ArgumentParser(description='PC-KEIBAから競馬場別・ランク別の複勝率を計算')
    parser.add_argument('--year', required=True, help='対象年（例: 2025）')
    parser.add_argument('--venue', help='競馬場コード（例: 45=川崎）')
    parser.add_argument('--month', help='月範囲（例: 01-06）')
    parser.add_argument('--output', help='出力ファイルパス（例: results_2026.txt）', default=None)
    
    args = parser.parse_args()
    
    print("=" * 120)
    print("🏇 競馬場別・ランク別 複勝率分析ツール（PC-KEIBAデータベース版）")
    print("=" * 120)
    print()
    
    # DB接続
    conn = get_db_connection()
    if conn is None:
        sys.exit(1)
    
    try:
        # データ取得・分析
        df = load_predictions_and_actuals(conn, args.year, args.venue, args.month)
        
        if df.empty:
            print("❌ データが見つかりませんでした")
            sys.exit(1)
        
        # 複勝率計算
        venue_stats = analyze_fukusho_rate(df)
        
        # 結果出力（TXTファイル対応）
        if args.output:
            output_file = args.output
        else:
            # デフォルトファイル名生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            venue_suffix = f"_venue{args.venue}" if args.venue else "_all"
            month_suffix = f"_month{args.month.replace('-', '')}" if args.month else ""
            output_file = f"analysis_results_{args.year}{venue_suffix}{month_suffix}_{timestamp}.txt"
        
        print_results(venue_stats, output_file)
        
        print("✅ 分析完了")
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
