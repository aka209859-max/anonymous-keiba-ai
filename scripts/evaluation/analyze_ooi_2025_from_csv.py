#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_ooi_2025_from_csv.py
大井2025年の予測データと払い戻しデータから複勝率を計算
"""

import pandas as pd
import sys
from pathlib import Path
from collections import defaultdict

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

def load_data():
    """予測データと払い戻しデータを読み込む"""
    
    print("=" * 80)
    print("🏇 大井2025年 複勝率分析（CSV版）")
    print("=" * 80)
    print()
    
    # 予測データ
    prediction_file = Path('predictions/phase5_ooi_2025/ooi_2025_phase5_ensemble.csv')
    if not prediction_file.exists():
        print(f"❌ 予測データが見つかりません: {prediction_file}")
        return None, None
    
    print(f"📄 予測データ読み込み: {prediction_file}")
    try:
        df_pred = pd.read_csv(prediction_file, encoding='shift-jis')
    except:
        try:
            df_pred = pd.read_csv(prediction_file, encoding='utf-8')
        except Exception as e:
            print(f"❌ 読み込みエラー: {e}")
            return None, None
    
    # データ型を統一（整数に統一してゼロ埋めなしに）
    df_pred['kaisai_tsukihi'] = df_pred['kaisai_tsukihi'].astype(str).str.lstrip('0').astype(int)
    df_pred['keibajo_code'] = df_pred['keibajo_code'].astype(int)
    df_pred['race_bango'] = df_pred['race_bango'].astype(int)
    df_pred['umaban'] = df_pred['umaban'].astype(int)
    
    # race_keyを使用（kaisai_nen_kaisai_tsukihi_keibajo_code_race_bango）
    # 全て整数で結合してキーを作成
    if 'race_key' not in df_pred.columns:
        df_pred['race_key'] = (df_pred['kaisai_nen'].astype(str) + '_' + 
                               df_pred['kaisai_tsukihi'].astype(str) + '_' + 
                               df_pred['keibajo_code'].astype(str) + '_' + 
                               df_pred['race_bango'].astype(str))
    
    print(f"   {len(df_pred)} 行, {df_pred['race_key'].nunique()} レース")
    
    # 払い戻しデータ
    payout_file = Path('ooi_2025_payouts.csv')
    if not payout_file.exists():
        print(f"❌ 払い戻しデータが見つかりません: {payout_file}")
        return None, None
    
    print(f"📄 払い戻しデータ読み込み: {payout_file}")
    try:
        df_payout = pd.read_csv(payout_file, encoding='shift-jis')
    except:
        try:
            df_payout = pd.read_csv(payout_file, encoding='utf-8')
        except Exception as e:
            print(f"❌ 読み込みエラー: {e}")
            return None, None
    
    print(f"   {len(df_payout)} 行")
    
    # カラム確認
    print()
    print("🔍 予測データのカラム:")
    print(f"   {', '.join(df_pred.columns[:10])}...")
    
    print()
    print("🔍 払い戻しデータのカラム:")
    print(f"   {', '.join(df_payout.columns[:10])}...")
    
    return df_pred, df_payout

def merge_data(df_pred, df_payout):
    """予測データと払い戻しデータをマージ"""
    
    print()
    print("-" * 80)
    print("🔗 データマージ")
    print("-" * 80)
    
    # 払い戻しデータから3着以内の馬を抽出
    # fukusho_1_umaban, fukusho_2_umaban, fukusho_3_umaban が複勝的中馬
    
    winning_horses = []
    
    for _, row in df_payout.iterrows():
        kaisai_nen = str(row['kaisai_nen'])
        # ゼロ埋めを除去して整数に変換
        kaisai_tsukihi = int(str(row['kaisai_tsukihi']).lstrip('0')) if str(row['kaisai_tsukihi']).strip() != '0' else 0
        keibajo_code = int(str(row['keibajo_code']).lstrip('0'))
        race_bango = int(str(row['race_bango']).lstrip('0'))
        race_key = f"{kaisai_nen}_{kaisai_tsukihi}_{keibajo_code}_{race_bango}"
        
        # 3着以内の馬番を取得（ゼロ埋め文字列を整数に変換）
        for col in ['fukusho_1_umaban', 'fukusho_2_umaban', 'fukusho_3_umaban']:
            if col in row and pd.notna(row[col]):
                try:
                    umaban = int(str(row[col]).strip())
                    if umaban > 0:  # 00は除外
                        winning_horses.append({
                            'race_key': race_key,
                            'umaban': umaban,
                            'actual_top3': 1
                        })
                except (ValueError, TypeError):
                    pass  # 変換失敗は無視
    
    df_winning = pd.DataFrame(winning_horses).drop_duplicates()
    
    print(f"\n✅ 3着以内の馬を抽出: {len(df_winning)} 頭")
    print(f"   ユニーク race_key: {df_winning['race_key'].nunique()} レース")
    if len(df_winning) > 0:
        print(f"   サンプル race_key: {df_winning.iloc[0]['race_key']}")
        print(f"   サンプル umaban: {df_winning.iloc[0]['umaban']}")
    
    # マージ
    df_merged = pd.merge(
        df_pred,
        df_winning,
        on=['race_key', 'umaban'],
        how='left'
    )
    df_merged['actual_top3'] = df_merged['actual_top3'].fillna(0)
    
    print(f"\n✅ マージ完了: {len(df_merged)} 行")
    print(f"   3着以内の馬: {df_merged['actual_top3'].sum():.0f} 頭")
    print(f"   予測データのrace_key数: {df_pred['race_key'].nunique()}")
    if len(df_pred) > 0:
        print(f"   予測データサンプル race_key: {df_pred.iloc[0]['race_key']}")
    
    # デバッグ情報
    total_races = df_merged['race_key'].nunique()
    match_rate = (df_merged['actual_top3'].sum() / (total_races * 3) * 100) if total_races > 0 else 0
    print(f"   マッチ率: {match_rate:.1f}% （期待値: ~100%）")
    
    if match_rate < 80:
        print(f"\n⚠️  警告: マッチ率が低すぎます")
        print(f"   予測データサンプル:")
        sample_pred = df_pred.iloc[0]
        print(f"   race_key: {sample_pred['race_key']}, umaban: {sample_pred['umaban']}")
        print(f"\n   払い戻しデータサンプル:")
        if len(df_winning) > 0:
            sample_win = df_winning.iloc[0]
            print(f"   race_key: {sample_win['race_key']}, umaban: {sample_win['umaban']}")
    
    return df_merged

def analyze_fukusho_rate(df):
    """ランク別複勝率を計算"""
    
    print()
    print("-" * 80)
    print("📊 ランク別複勝率計算")
    print("-" * 80)
    
    # ランク列を追加
    df['rank_label'] = df['ensemble_score'].apply(get_rank_from_score)
    
    # 統計
    stats = {
        '1st_S': {'hits': 0, 'total': 0},
        '1st_A': {'hits': 0, 'total': 0},
        '2nd_S': {'hits': 0, 'total': 0},
        '2nd_A': {'hits': 0, 'total': 0},
        '2nd_B': {'hits': 0, 'total': 0}
    }
    
    race_count = 0
    
    # レースごとに処理
    for race_key, group in df.groupby('race_key'):
        sorted_group = group.sort_values('ensemble_score', ascending=False).reset_index(drop=True)
        
        if len(sorted_group) < 2:
            continue
        
        race_count += 1
        
        # 1位の馬
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
        
        # 2位の馬
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
    
    return stats, race_count

def print_results(stats, race_count):
    """結果を表示"""
    
    print()
    print("=" * 80)
    print("📊 大井2025年 複勝率分析結果")
    print("=" * 80)
    print()
    
    print(f"総レース数: {race_count}")
    print()
    
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
            print(f"【{label}】 {hits}/{total} ({rate:.1f}%)")
        else:
            print(f"【{label}】 -")
    
    print()
    print("=" * 80)

def main():
    # データ読み込み
    df_pred, df_payout = load_data()
    if df_pred is None or df_payout is None:
        sys.exit(1)
    
    # マージ
    df_merged = merge_data(df_pred, df_payout)
    if df_merged is None:
        sys.exit(1)
    
    # 複勝率計算
    stats, race_count = analyze_fukusho_rate(df_merged)
    
    # 結果表示
    print_results(stats, race_count)

if __name__ == '__main__':
    main()
