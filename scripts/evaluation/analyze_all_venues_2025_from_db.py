#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_all_venues_2025_from_db.py
2025年全競馬場の予測データとDB実績から複勝率を計算
"""

import pandas as pd
import psycopg2
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 競馬場コードマッピング
VENUE_NAMES = {
    '30': '盛岡', '35': '門別', '36': '水沢',
    '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
    '46': '金沢', '47': '笠松', '48': '名古屋',
    '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
}

def get_db_connection():
    """PostgreSQLに接続"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='pckeiba',
            user='postgres',
            password='postgres123'
        )
        return conn
    except Exception as e:
        print(f"❌ DB接続エラー: {e}")
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

def load_predictions():
    """全競馬場の予測データを読み込む"""
    
    print("=" * 80)
    print("📂 予測データ読み込み")
    print("=" * 80)
    
    predictions_dir = Path('data/predictions/phase5')
    if not predictions_dir.exists():
        print(f"❌ ディレクトリが存在しません: {predictions_dir}")
        return None
    
    all_predictions = []
    
    # phase5ディレクトリ内の全CSVを読み込む
    csv_files = list(predictions_dir.glob('*.csv'))
    
    if len(csv_files) == 0:
        print(f"❌ 予測CSVが見つかりません: {predictions_dir}")
        return None
    
    print(f"📄 {len(csv_files)} 個のCSVファイルを検出")
    
    for csv_file in csv_files:
        try:
            # Shift-JISで読み込み
            try:
                df = pd.read_csv(csv_file, encoding='shift-jis')
            except:
                df = pd.read_csv(csv_file, encoding='utf-8')
            
            # 必須カラムチェック
            required_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 'umaban', 'ensemble_score']
            if not all(col in df.columns for col in required_cols):
                print(f"⚠️  スキップ（必須カラム不足）: {csv_file.name}")
                continue
            
            # データ型を整数に統一
            df['kaisai_nen'] = df['kaisai_nen'].astype(str)
            df['kaisai_tsukihi'] = df['kaisai_tsukihi'].astype(str).str.lstrip('0').astype(int)
            df['keibajo_code'] = df['keibajo_code'].astype(int)
            df['race_bango'] = df['race_bango'].astype(int)
            df['umaban'] = df['umaban'].astype(int)
            
            # race_keyを作成
            df['race_key'] = (df['kaisai_nen'] + '_' + 
                             df['kaisai_tsukihi'].astype(str) + '_' + 
                             df['keibajo_code'].astype(str) + '_' + 
                             df['race_bango'].astype(str))
            
            all_predictions.append(df)
            print(f"  ✅ {csv_file.name}: {len(df)} 行")
            
        except Exception as e:
            print(f"  ⚠️  エラー {csv_file.name}: {e}")
            continue
    
    if len(all_predictions) == 0:
        print("❌ 読み込めた予測データがありません")
        return None
    
    df_all = pd.concat(all_predictions, ignore_index=True)
    
    print()
    print(f"✅ 予測データ読み込み完了")
    print(f"   総行数: {len(df_all):,}")
    print(f"   総レース数: {df_all['race_key'].nunique():,}")
    print(f"   競馬場数: {df_all['keibajo_code'].nunique()}")
    
    return df_all

def load_actuals_from_db(df_predictions):
    """DBから実績データを取得"""
    
    print()
    print("=" * 80)
    print("💾 実績データ取得（DB）")
    print("=" * 80)
    
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        # 予測データから必要な条件を取得
        year_list = df_predictions['kaisai_nen'].unique().tolist()
        
        # SQLクエリ
        query = """
        SELECT 
            kaisai_nen,
            kaisai_tsukihi,
            keibajo_code,
            race_bango,
            umaban,
            kakutei_chakujun as actual_rank
        FROM nvd_se
        WHERE kaisai_nen = '2025'
          AND kakutei_chakujun IS NOT NULL
          AND kakutei_chakujun != '00'
        """
        
        df_actuals = pd.read_sql(query, conn)
        
        print(f"✅ 実績データ取得完了: {len(df_actuals):,} 行")
        
        # データ型を整数に統一
        df_actuals['kaisai_tsukihi'] = df_actuals['kaisai_tsukihi'].astype(str).str.lstrip('0').astype(int)
        df_actuals['keibajo_code'] = df_actuals['keibajo_code'].astype(int)
        df_actuals['race_bango'] = df_actuals['race_bango'].astype(int)
        df_actuals['umaban'] = df_actuals['umaban'].astype(int)
        df_actuals['actual_rank'] = pd.to_numeric(df_actuals['actual_rank'], errors='coerce')
        
        # 3着以内のみ抽出
        df_actuals = df_actuals[df_actuals['actual_rank'] <= 3].copy()
        
        # race_keyを作成
        df_actuals['race_key'] = (df_actuals['kaisai_nen'].astype(str) + '_' + 
                                   df_actuals['kaisai_tsukihi'].astype(str) + '_' + 
                                   df_actuals['keibajo_code'].astype(str) + '_' + 
                                   df_actuals['race_bango'].astype(str))
        
        print(f"   3着以内の馬: {len(df_actuals):,} 頭")
        print(f"   レース数: {df_actuals['race_key'].nunique():,}")
        
        return df_actuals
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None
    finally:
        conn.close()

def merge_and_analyze(df_pred, df_actuals):
    """予測と実績をマージして分析"""
    
    print()
    print("=" * 80)
    print("🔗 データマージ")
    print("=" * 80)
    
    # マージ
    df_merged = pd.merge(
        df_pred,
        df_actuals[['race_key', 'umaban']],
        on=['race_key', 'umaban'],
        how='left',
        indicator=True
    )
    
    df_merged['actual_top3'] = (df_merged['_merge'] == 'both').astype(int)
    df_merged.drop('_merge', axis=1, inplace=True)
    
    print(f"✅ マージ完了: {len(df_merged):,} 行")
    print(f"   3着以内の馬: {df_merged['actual_top3'].sum():,} 頭")
    
    # ランク列を追加
    df_merged['rank_label'] = df_merged['ensemble_score'].apply(get_rank_from_score)
    
    # 競馬場別・全体の統計
    results = {}
    
    print()
    print("=" * 80)
    print("📊 競馬場別複勝率計算")
    print("=" * 80)
    
    for venue_code in sorted(df_merged['keibajo_code'].unique()):
        venue_name = VENUE_NAMES.get(str(venue_code), f'不明({venue_code})')
        df_venue = df_merged[df_merged['keibajo_code'] == venue_code]
        
        stats = calculate_fukusho_rate(df_venue)
        stats['venue_code'] = venue_code
        stats['venue_name'] = venue_name
        results[venue_code] = stats
        
        print(f"  ✅ {venue_name} ({venue_code}): {stats['race_count']} レース")
    
    # 全体統計
    print()
    print("  ✅ 全体統計を計算中...")
    stats_all = calculate_fukusho_rate(df_merged)
    stats_all['venue_code'] = 'ALL'
    stats_all['venue_name'] = '全体'
    results['ALL'] = stats_all
    
    return results

def calculate_fukusho_rate(df):
    """ランク別複勝率を計算"""
    
    stats = {
        '1st_S': {'hits': 0, 'total': 0},
        '1st_A': {'hits': 0, 'total': 0},
        '2nd_S': {'hits': 0, 'total': 0},
        '2nd_A': {'hits': 0, 'total': 0},
        '2nd_B': {'hits': 0, 'total': 0}
    }
    
    race_count = 0
    
    for race_key, group in df.groupby('race_key'):
        sorted_group = group.sort_values('ensemble_score', ascending=False).reset_index(drop=True)
        
        if len(sorted_group) < 2:
            continue
        
        race_count += 1
        
        # 1位
        first = sorted_group.iloc[0]
        first_rank = first['rank_label']
        first_hit = first['actual_top3'] == 1
        
        if first_rank == 'S':
            stats['1st_S']['total'] += 1
            if first_hit:
                stats['1st_S']['hits'] += 1
        elif first_rank == 'A':
            stats['1st_A']['total'] += 1
            if first_hit:
                stats['1st_A']['hits'] += 1
        
        # 2位
        second = sorted_group.iloc[1]
        second_rank = second['rank_label']
        second_hit = second['actual_top3'] == 1
        
        if second_rank == 'S':
            stats['2nd_S']['total'] += 1
            if second_hit:
                stats['2nd_S']['hits'] += 1
        elif second_rank == 'A':
            stats['2nd_A']['total'] += 1
            if second_hit:
                stats['2nd_A']['hits'] += 1
        elif second_rank == 'B':
            stats['2nd_B']['total'] += 1
            if second_hit:
                stats['2nd_B']['hits'] += 1
    
    # 複勝率計算
    for key in stats:
        if stats[key]['total'] > 0:
            stats[key]['rate'] = stats[key]['hits'] / stats[key]['total'] * 100
        else:
            stats[key]['rate'] = 0.0
    
    stats['race_count'] = race_count
    return stats

def print_results(results, output_file=None):
    """結果を表示・保存"""
    
    output_lines = []
    
    output_lines.append("=" * 80)
    output_lines.append("📊 2025年 全競馬場 複勝率分析結果")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # 競馬場別
    output_lines.append("【競馬場別】")
    output_lines.append("")
    
    for venue_code in sorted([k for k in results.keys() if k != 'ALL']):
        stats = results[venue_code]
        venue_name = stats['venue_name']
        race_count = stats['race_count']
        
        output_lines.append(f"■ {venue_name} ({venue_code}): {race_count} レース")
        
        labels = [
            ('1位Sランク', '1st_S'),
            ('1位Aランク', '1st_A'),
            ('2位Sランク', '2nd_S'),
            ('2位Aランク', '2nd_A'),
            ('2位Bランク', '2nd_B')
        ]
        
        for label, key in labels:
            hits = stats[key]['hits']
            total = stats[key]['total']
            rate = stats[key]['rate']
            
            if total > 0:
                output_lines.append(f"  【{label}】 {hits}/{total} ({rate:.1f}%)")
            else:
                output_lines.append(f"  【{label}】 -")
        
        output_lines.append("")
    
    # 全体
    if 'ALL' in results:
        stats = results['ALL']
        output_lines.append("=" * 80)
        output_lines.append("【全体サマリー】")
        output_lines.append("=" * 80)
        output_lines.append(f"総レース数: {stats['race_count']:,}")
        output_lines.append("")
        
        labels = [
            ('1位Sランク', '1st_S'),
            ('1位Aランク', '1st_A'),
            ('2位Sランク', '2nd_S'),
            ('2位Aランク', '2nd_A'),
            ('2位Bランク', '2nd_B')
        ]
        
        for label, key in labels:
            hits = stats[key]['hits']
            total = stats[key]['total']
            rate = stats[key]['rate']
            
            if total > 0:
                output_lines.append(f"【{label}】 {hits}/{total} ({rate:.1f}%)")
            else:
                output_lines.append(f"【{label}】 -")
    
    output_lines.append("")
    output_lines.append("=" * 80)
    
    # 画面表示
    for line in output_lines:
        print(line)
    
    # ファイル保存
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print()
        print(f"💾 結果を保存しました: {output_file}")

def main():
    # 予測データ読み込み
    df_pred = load_predictions()
    if df_pred is None:
        sys.exit(1)
    
    # 実績データ取得
    df_actuals = load_actuals_from_db(df_pred)
    if df_actuals is None:
        sys.exit(1)
    
    # マージ＆分析
    results = merge_and_analyze(df_pred, df_actuals)
    
    # 結果表示・保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'analysis_results_2025_all_venues_{timestamp}.txt'
    print_results(results, output_file)

if __name__ == '__main__':
    main()
