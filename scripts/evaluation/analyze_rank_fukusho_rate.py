#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_rank_fukusho_rate.py
競馬場別・ランク別の複勝率を計算

【計算対象】
- 1位のSランク複勝率
- 1位のAランク複勝率
- 2位のSランク複勝率
- 2位のAランク複勝率
- 2位のBランク複勝率

使用法:
    python analyze_rank_fukusho_rate.py
    python analyze_rank_fukusho_rate.py --venue kawasaki
    python analyze_rank_fukusho_rate.py --input-dir data/predictions/phase5
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

# 競馬場コード→名前のマッピング
VENUE_CODE_TO_NAME = {
    '30': 'monbetsu', '35': 'morioka', '36': 'mizusawa',
    '42': 'urawa', '43': 'funabashi', '44': 'ooi', '45': 'kawasaki',
    '46': 'kanazawa', '47': 'kasamatsu', '48': 'nagoya',
    '50': 'sonoda', '51': 'himeji', '54': 'kochi', '55': 'saga'
}

VENUE_NAME_TO_JP = {
    'monbetsu': '門別', 'morioka': '盛岡', 'mizusawa': '水沢',
    'urawa': '浦和', 'funabashi': '船橋', 'ooi': '大井', 'kawasaki': '川崎',
    'kanazawa': '金沢', 'kasamatsu': '笠松', 'nagoya': '名古屋',
    'sonoda': '園田', 'himeji': '姫路', 'kochi': '高知', 'saga': '佐賀'
}

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


def analyze_single_file(csv_path):
    """
    1つのアンサンブル予測CSVファイルを分析
    
    Returns:
        dict: {
            'venue': 競馬場名,
            'total_races': レース数,
            '1st_S': {hits: X, total: Y, rate: Z},
            '1st_A': {hits: X, total: Y, rate: Z},
            '2nd_S': {hits: X, total: Y, rate: Z},
            '2nd_A': {hits: X, total: Y, rate: Z},
            '2nd_B': {hits: X, total: Y, rate: Z}
        }
    """
    
    # CSVファイル読み込み
    try:
        df = pd.read_csv(csv_path, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='utf-8')
    
    # 必要なカラムの確認
    required_cols = ['race_id', 'horse_no', 'ensemble_score', 'actual_rank']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"⚠️  欠損カラム: {missing_cols} - スキップ: {csv_path}")
        return None
    
    # ランク列を追加
    df['rank_label'] = df['ensemble_score'].apply(get_rank_from_score)
    
    # レースごとにグループ化
    results = {
        '1st_S': {'hits': 0, 'total': 0},
        '1st_A': {'hits': 0, 'total': 0},
        '2nd_S': {'hits': 0, 'total': 0},
        '2nd_A': {'hits': 0, 'total': 0},
        '2nd_B': {'hits': 0, 'total': 0}
    }
    
    total_races = 0
    
    for race_id, group in df.groupby('race_id'):
        total_races += 1
        
        # スコアでソート（降順）
        sorted_group = group.sort_values('ensemble_score', ascending=False).reset_index(drop=True)
        
        if len(sorted_group) < 2:
            continue
        
        # 1位の馬
        first_horse = sorted_group.iloc[0]
        first_rank = first_horse['rank_label']
        first_actual = first_horse['actual_rank']
        
        # 1位がSランク
        if first_rank == 'S':
            results['1st_S']['total'] += 1
            if pd.notna(first_actual) and first_actual <= 3:
                results['1st_S']['hits'] += 1
        
        # 1位がAランク
        if first_rank == 'A':
            results['1st_A']['total'] += 1
            if pd.notna(first_actual) and first_actual <= 3:
                results['1st_A']['hits'] += 1
        
        # 2位の馬
        second_horse = sorted_group.iloc[1]
        second_rank = second_horse['rank_label']
        second_actual = second_horse['actual_rank']
        
        # 2位がSランク
        if second_rank == 'S':
            results['2nd_S']['total'] += 1
            if pd.notna(second_actual) and second_actual <= 3:
                results['2nd_S']['hits'] += 1
        
        # 2位がAランク
        if second_rank == 'A':
            results['2nd_A']['total'] += 1
            if pd.notna(second_actual) and second_actual <= 3:
                results['2nd_A']['hits'] += 1
        
        # 2位がBランク
        if second_rank == 'B':
            results['2nd_B']['total'] += 1
            if pd.notna(second_actual) and second_actual <= 3:
                results['2nd_B']['hits'] += 1
    
    # 複勝率を計算
    for key in results:
        if results[key]['total'] > 0:
            results[key]['rate'] = results[key]['hits'] / results[key]['total'] * 100
        else:
            results[key]['rate'] = 0.0
    
    # 競馬場名を抽出
    filename = Path(csv_path).name
    venue = None
    for v_name in VENUE_NAME_TO_JP.values():
        if v_name in filename:
            venue = v_name
            break
    
    results['venue'] = venue
    results['total_races'] = total_races
    
    return results


def analyze_all_venues(input_dir):
    """
    指定ディレクトリ内の全アンサンブルCSVを分析
    """
    
    input_path = Path(input_dir)
    csv_files = list(input_path.glob('*ensemble*.csv'))
    
    if not csv_files:
        print(f"❌ アンサンブルCSVが見つかりません: {input_dir}")
        return None
    
    print(f"📂 対象ファイル数: {len(csv_files)}")
    print()
    
    # 競馬場別に集計
    venue_stats = defaultdict(lambda: {
        'total_races': 0,
        '1st_S': {'hits': 0, 'total': 0},
        '1st_A': {'hits': 0, 'total': 0},
        '2nd_S': {'hits': 0, 'total': 0},
        '2nd_A': {'hits': 0, 'total': 0},
        '2nd_B': {'hits': 0, 'total': 0}
    })
    
    for csv_file in csv_files:
        print(f"📄 処理中: {csv_file.name}")
        result = analyze_single_file(csv_file)
        
        if result is None:
            continue
        
        venue = result['venue']
        if venue is None:
            venue = '不明'
        
        # 集計
        venue_stats[venue]['total_races'] += result['total_races']
        for key in ['1st_S', '1st_A', '2nd_S', '2nd_A', '2nd_B']:
            venue_stats[venue][key]['hits'] += result[key]['hits']
            venue_stats[venue][key]['total'] += result[key]['total']
    
    print()
    
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


def print_results(venue_stats):
    """
    結果を表形式で出力
    """
    
    print("=" * 120)
    print("📊 競馬場別・ランク別 複勝率分析結果")
    print("=" * 120)
    print()
    
    # ヘッダー
    header = f"{'競馬場':<10} {'レース数':>8} | {'1位S複勝':>12} | {'1位A複勝':>12} | {'2位S複勝':>12} | {'2位A複勝':>12} | {'2位B複勝':>12}"
    print(header)
    print("-" * 120)
    
    # 各競馬場の結果
    for venue in sorted(venue_stats.keys()):
        stats = venue_stats[venue]
        
        total_races = stats['total_races']
        
        # 1位Sランク
        s1_hits = stats['1st_S']['hits']
        s1_total = stats['1st_S']['total']
        s1_rate = stats['1st_S']['rate']
        s1_str = f"{s1_hits}/{s1_total} ({s1_rate:5.1f}%)" if s1_total > 0 else "-"
        
        # 1位Aランク
        a1_hits = stats['1st_A']['hits']
        a1_total = stats['1st_A']['total']
        a1_rate = stats['1st_A']['rate']
        a1_str = f"{a1_hits}/{a1_total} ({a1_rate:5.1f}%)" if a1_total > 0 else "-"
        
        # 2位Sランク
        s2_hits = stats['2nd_S']['hits']
        s2_total = stats['2nd_S']['total']
        s2_rate = stats['2nd_S']['rate']
        s2_str = f"{s2_hits}/{s2_total} ({s2_rate:5.1f}%)" if s2_total > 0 else "-"
        
        # 2位Aランク
        a2_hits = stats['2nd_A']['hits']
        a2_total = stats['2nd_A']['total']
        a2_rate = stats['2nd_A']['rate']
        a2_str = f"{a2_hits}/{a2_total} ({a2_rate:5.1f}%)" if a2_total > 0 else "-"
        
        # 2位Bランク
        b2_hits = stats['2nd_B']['hits']
        b2_total = stats['2nd_B']['total']
        b2_rate = stats['2nd_B']['rate']
        b2_str = f"{b2_hits}/{b2_total} ({b2_rate:5.1f}%)" if b2_total > 0 else "-"
        
        row = f"{venue:<10} {total_races:>8} | {s1_str:>12} | {a1_str:>12} | {s2_str:>12} | {a2_str:>12} | {b2_str:>12}"
        print(row)
    
    print("=" * 120)
    print()
    
    # 全体サマリー
    print("📈 全体サマリー")
    print("-" * 120)
    
    total_races = sum(v['total_races'] for v in venue_stats.values())
    
    # 1位Sランク合計
    s1_total_hits = sum(v['1st_S']['hits'] for v in venue_stats.values())
    s1_total_total = sum(v['1st_S']['total'] for v in venue_stats.values())
    s1_total_rate = (s1_total_hits / s1_total_total * 100) if s1_total_total > 0 else 0
    
    # 1位Aランク合計
    a1_total_hits = sum(v['1st_A']['hits'] for v in venue_stats.values())
    a1_total_total = sum(v['1st_A']['total'] for v in venue_stats.values())
    a1_total_rate = (a1_total_hits / a1_total_total * 100) if a1_total_total > 0 else 0
    
    # 2位Sランク合計
    s2_total_hits = sum(v['2nd_S']['hits'] for v in venue_stats.values())
    s2_total_total = sum(v['2nd_S']['total'] for v in venue_stats.values())
    s2_total_rate = (s2_total_hits / s2_total_total * 100) if s2_total_total > 0 else 0
    
    # 2位Aランク合計
    a2_total_hits = sum(v['2nd_A']['hits'] for v in venue_stats.values())
    a2_total_total = sum(v['2nd_A']['total'] for v in venue_stats.values())
    a2_total_rate = (a2_total_hits / a2_total_total * 100) if a2_total_total > 0 else 0
    
    # 2位Bランク合計
    b2_total_hits = sum(v['2nd_B']['hits'] for v in venue_stats.values())
    b2_total_total = sum(v['2nd_B']['total'] for v in venue_stats.values())
    b2_total_rate = (b2_total_hits / b2_total_total * 100) if b2_total_total > 0 else 0
    
    print(f"総レース数: {total_races}")
    print()
    print(f"【1位Sランク】 {s1_total_hits}/{s1_total_total} ({s1_total_rate:.1f}%)")
    print(f"【1位Aランク】 {a1_total_hits}/{a1_total_total} ({a1_total_rate:.1f}%)")
    print(f"【2位Sランク】 {s2_total_hits}/{s2_total_total} ({s2_total_rate:.1f}%)")
    print(f"【2位Aランク】 {a2_total_hits}/{a2_total_total} ({a2_total_rate:.1f}%)")
    print(f"【2位Bランク】 {b2_total_hits}/{b2_total_total} ({b2_total_rate:.1f}%)")
    print()


def main():
    parser = argparse.ArgumentParser(description='競馬場別・ランク別の複勝率を計算')
    parser.add_argument('--input-dir', default='data/predictions/phase5',
                        help='アンサンブル予測CSVのディレクトリ（デフォルト: data/predictions/phase5）')
    parser.add_argument('--venue', help='特定の競馬場のみ分析（例: kawasaki）')
    
    args = parser.parse_args()
    
    print("=" * 120)
    print("🏇 競馬場別・ランク別 複勝率分析ツール")
    print("=" * 120)
    print()
    
    # 分析実行
    venue_stats = analyze_all_venues(args.input_dir)
    
    if venue_stats is None:
        sys.exit(1)
    
    # 特定競馬場のみ
    if args.venue:
        venue_jp = VENUE_NAME_TO_JP.get(args.venue)
        if venue_jp and venue_jp in venue_stats:
            venue_stats = {venue_jp: venue_stats[venue_jp]}
        else:
            print(f"❌ 競馬場が見つかりません: {args.venue}")
            sys.exit(1)
    
    # 結果出力
    print_results(venue_stats)
    
    print("✅ 分析完了")


if __name__ == '__main__':
    main()
