#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase5_5_backtest_full.py
Phase 5.5: 全7券種対応の完全バックテスト

全231レースで7券種（単勝・複勝・馬連・ワイド・馬単・三連複・三連単）を評価
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

import pandas as pd
import numpy as np


def parse_haraimodoshi(value) -> int:
    """払戻金を整数に変換"""
    if pd.isna(value) or value == '' or value is None:
        return 0
    try:
        return int(float(str(value).strip()))
    except:
        return 0


def parse_kumiban(kumiban_str: str) -> Tuple:
    """
    組番文字列をタプルに変換
    例: "0102" -> (1, 2), "010203" -> (1, 2, 3), "01-02" -> (1, 2)
    """
    if pd.isna(kumiban_str) or kumiban_str == '' or kumiban_str is None:
        return None
    
    try:
        kumiban_str = str(kumiban_str).strip()
        
        # スペースのみの場合
        if kumiban_str.isspace() or kumiban_str == '':
            return None
        
        # ハイフン区切りの場合
        if '-' in kumiban_str:
            parts = kumiban_str.split('-')
            return tuple(int(p) for p in parts)
        
        # 連続した数字の場合（例: "0102" -> (1, 2), "010203" -> (1, 2, 3)）
        if len(kumiban_str) % 2 == 0:
            parts = [kumiban_str[i:i+2] for i in range(0, len(kumiban_str), 2)]
            return tuple(int(p) for p in parts if p.strip())
        
        return None
    except:
        return None


def load_payouts_csv(csv_path: str) -> pd.DataFrame:
    """払戻金CSVを読み込み"""
    print("\n" + "="*80)
    print("📊 払戻金CSVを読み込み中...")
    print("="*80)
    print(f"📁 ファイル: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path, encoding='shift_jis')
    except:
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except:
            df = pd.read_csv(csv_path, encoding='cp932')
    
    print(f"✅ データ件数: {len(df):,}件")
    
    # race_key を作成
    if 'kaisai_nen' in df.columns:
        df['race_key'] = (df['kaisai_nen'].astype(str) + '_' + 
                         df['kaisai_tsukihi'].astype(str).str.zfill(4) + '_' + 
                         df['keibajo_code'].astype(str).str.zfill(2) + '_' + 
                         df['race_bango'].astype(str).str.zfill(2))
    else:
        df['race_key'] = (df['kaisai_tsukihi'].astype(str).str.zfill(4) + '_' + 
                         df['keibajo_code'].astype(str).str.zfill(2) + '_' + 
                         df['race_bango'].astype(str).str.zfill(2))
    
    return df


def generate_betting_strategy(ensemble_df: pd.DataFrame, 
                              strategy_config: Dict = None) -> Tuple[Dict, Dict]:
    """アンサンブル予測から買い目を生成"""
    print("\n" + "="*80)
    print("🎫 買い目生成中...")
    print("="*80)
    
    if strategy_config is None:
        strategy_config = {
            'tansho_min_rank': 'S',
            'fukusho_min_rank': 'A',
            'umaren_min_rank': 'A',
            'wide_min_rank': 'B',
            'umatan_min_rank': 'A',
            'sanrenpuku_min_rank': 'A',
            'sanrentan_min_rank': 'S',
            'max_horses_tansho': 3,
            'max_horses_fukusho': 5,
            'max_horses_umaren': 4,
            'max_horses_wide': 5,
            'max_horses_umatan': 3,
            'max_horses_sanrenpuku': 4,
            'max_horses_sanrentan': 3,
            'unit_bet': 100
        }
    
    rank_order = {'S': 0, 'A': 1, 'B': 2, 'C': 3, 'D': 4}
    
    bets = {}
    
    for race_key, race_df in ensemble_df.groupby('race_key'):
        race_df = race_df.sort_values('ensemble_score', ascending=False).reset_index(drop=True)
        
        race_bets = {
            'tansho': [],
            'fukusho': [],
            'umaren': [],
            'wide': [],
            'umatan': [],
            'sanrenpuku': [],
            'sanrentan': []
        }
        
        # 単勝: Sランク以上
        tansho_horses = race_df[
            race_df['rank'].map(rank_order) <= rank_order[strategy_config['tansho_min_rank']]
        ]['umaban'].tolist()
        race_bets['tansho'] = tansho_horses[:strategy_config['max_horses_tansho']]
        
        # 複勝: Aランク以上
        fukusho_horses = race_df[
            race_df['rank'].map(rank_order) <= rank_order[strategy_config['fukusho_min_rank']]
        ]['umaban'].tolist()
        race_bets['fukusho'] = fukusho_horses[:strategy_config['max_horses_fukusho']]
        
        # 馬連: Aランク以上
        umaren_horses = race_df[
            race_df['rank'].map(rank_order) <= rank_order[strategy_config['umaren_min_rank']]
        ]['umaban'].tolist()[:strategy_config['max_horses_umaren']]
        
        for i, h1 in enumerate(umaren_horses):
            for h2 in umaren_horses[i+1:]:
                race_bets['umaren'].append(tuple(sorted([h1, h2])))
        
        # ワイド: Bランク以上
        wide_horses = race_df[
            race_df['rank'].map(rank_order) <= rank_order[strategy_config['wide_min_rank']]
        ]['umaban'].tolist()[:strategy_config['max_horses_wide']]
        
        for i, h1 in enumerate(wide_horses):
            for h2 in wide_horses[i+1:]:
                race_bets['wide'].append(tuple(sorted([h1, h2])))
        
        # 馬単: Aランク以上
        umatan_horses = race_df[
            race_df['rank'].map(rank_order) <= rank_order[strategy_config['umatan_min_rank']]
        ]['umaban'].tolist()[:strategy_config['max_horses_umatan']]
        
        for h1 in umatan_horses:
            for h2 in umatan_horses:
                if h1 != h2:
                    race_bets['umatan'].append((h1, h2))
        
        # 三連複: Aランク以上
        sanrenpuku_horses = race_df[
            race_df['rank'].map(rank_order) <= rank_order[strategy_config['sanrenpuku_min_rank']]
        ]['umaban'].tolist()[:strategy_config['max_horses_sanrenpuku']]
        
        for i, h1 in enumerate(sanrenpuku_horses):
            for j, h2 in enumerate(sanrenpuku_horses[i+1:], start=i+1):
                for h3 in sanrenpuku_horses[j+1:]:
                    race_bets['sanrenpuku'].append(tuple(sorted([h1, h2, h3])))
        
        # 三連単: Sランク以上
        sanrentan_horses = race_df[
            race_df['rank'].map(rank_order) <= rank_order[strategy_config['sanrentan_min_rank']]
        ]['umaban'].tolist()[:strategy_config['max_horses_sanrentan']]
        
        for h1 in sanrentan_horses:
            for h2 in sanrentan_horses:
                if h1 != h2:
                    for h3 in sanrentan_horses:
                        if h3 != h1 and h3 != h2:
                            race_bets['sanrentan'].append((h1, h2, h3))
        
        bets[race_key] = race_bets
    
    # 統計表示
    total_bets = {
        'tansho': sum(len(b['tansho']) for b in bets.values()),
        'fukusho': sum(len(b['fukusho']) for b in bets.values()),
        'umaren': sum(len(b['umaren']) for b in bets.values()),
        'wide': sum(len(b['wide']) for b in bets.values()),
        'umatan': sum(len(b['umatan']) for b in bets.values()),
        'sanrenpuku': sum(len(b['sanrenpuku']) for b in bets.values()),
        'sanrentan': sum(len(b['sanrentan']) for b in bets.values())
    }
    
    print(f"✅ レース数: {len(bets)}")
    print(f"📊 券種別買い目数:")
    for ticket_type, count in total_bets.items():
        print(f"   - {ticket_type}: {count:,}点")
    
    return bets, strategy_config


def evaluate_backtest(bets: Dict, payouts_df: pd.DataFrame, 
                     strategy_config: Dict) -> Tuple[Dict, int]:
    """バックテスト評価を実行（全7券種対応）"""
    print("\n" + "="*80)
    print("🔍 バックテスト評価中...")
    print("="*80)
    
    unit_bet = strategy_config['unit_bet']
    
    results = {
        'tansho': {'hit': 0, 'total': 0, 'cost': 0, 'return': 0},
        'fukusho': {'hit': 0, 'total': 0, 'cost': 0, 'return': 0},
        'umaren': {'hit': 0, 'total': 0, 'cost': 0, 'return': 0},
        'wide': {'hit': 0, 'total': 0, 'cost': 0, 'return': 0},
        'umatan': {'hit': 0, 'total': 0, 'cost': 0, 'return': 0},
        'sanrenpuku': {'hit': 0, 'total': 0, 'cost': 0, 'return': 0},
        'sanrentan': {'hit': 0, 'total': 0, 'cost': 0, 'return': 0}
    }
    
    # 払戻金をrace_keyでインデックス化
    payouts_dict = {row['race_key']: row for _, row in payouts_df.iterrows()}
    
    matched_races = 0
    
    for race_key, race_bets in bets.items():
        if race_key not in payouts_dict:
            continue
        
        matched_races += 1
        payout_row = payouts_dict[race_key]
        
        # 単勝
        for umaban in race_bets['tansho']:
            results['tansho']['total'] += 1
            results['tansho']['cost'] += unit_bet
            
            if 'tansho_umaban' in payout_row and payout_row['tansho_umaban'] == umaban:
                results['tansho']['hit'] += 1
                payout = parse_haraimodoshi(payout_row.get('tansho_haraimodoshi', 0))
                results['tansho']['return'] += payout
        
        # 複勝（3着まで）
        fukusho_winners = []
        for i in range(1, 4):  # 複勝は1～3着まで
            uma_col = f'fukusho_{i}_umaban'
            if uma_col in payout_row and not pd.isna(payout_row[uma_col]):
                fukusho_winners.append(int(payout_row[uma_col]))
        
        for umaban in race_bets['fukusho']:
            results['fukusho']['total'] += 1
            results['fukusho']['cost'] += unit_bet
            
            if umaban in fukusho_winners:
                results['fukusho']['hit'] += 1
                for i in range(1, 4):  # 複勝は1～3着まで
                    uma_col = f'fukusho_{i}_umaban'
                    pay_col = f'fukusho_{i}_haraimodoshi'
                    if uma_col in payout_row and payout_row[uma_col] == umaban:
                        payout = parse_haraimodoshi(payout_row.get(pay_col, 0))
                        results['fukusho']['return'] += payout
                        break
        
        # 馬連
        umaren_winner = parse_kumiban(payout_row.get('umaren_kumiban', ''))
        if umaren_winner:
            umaren_winner_sorted = tuple(sorted(umaren_winner))
            for bet in race_bets['umaren']:
                results['umaren']['total'] += 1
                results['umaren']['cost'] += unit_bet
                
                if bet == umaren_winner_sorted:
                    results['umaren']['hit'] += 1
                    payout = parse_haraimodoshi(payout_row.get('umaren_haraimodoshi', 0))
                    results['umaren']['return'] += payout
        
        # ワイド
        wide_winners = []
        for i in range(1, 8):
            kumi = parse_kumiban(payout_row.get(f'wide_{i}_kumiban', ''))
            if kumi:
                wide_winners.append((tuple(sorted(kumi)), 
                                    parse_haraimodoshi(payout_row.get(f'wide_{i}_haraimodoshi', 0))))
        
        for bet in race_bets['wide']:
            results['wide']['total'] += 1
            results['wide']['cost'] += unit_bet
            
            for winner, payout in wide_winners:
                if bet == winner:
                    results['wide']['hit'] += 1
                    results['wide']['return'] += payout
                    break
        
        # 馬単
        umatan_winner = parse_kumiban(payout_row.get('umatan_kumiban', ''))
        if umatan_winner:
            for bet in race_bets['umatan']:
                results['umatan']['total'] += 1
                results['umatan']['cost'] += unit_bet
                
                if bet == umatan_winner:
                    results['umatan']['hit'] += 1
                    payout = parse_haraimodoshi(payout_row.get('umatan_haraimodoshi', 0))
                    results['umatan']['return'] += payout
        
        # 三連複
        sanrenpuku_winner = parse_kumiban(payout_row.get('sanrenpuku_kumiban', ''))
        if sanrenpuku_winner:
            sanrenpuku_winner_sorted = tuple(sorted(sanrenpuku_winner))
            for bet in race_bets['sanrenpuku']:
                results['sanrenpuku']['total'] += 1
                results['sanrenpuku']['cost'] += unit_bet
                
                if bet == sanrenpuku_winner_sorted:
                    results['sanrenpuku']['hit'] += 1
                    payout = parse_haraimodoshi(payout_row.get('sanrenpuku_haraimodoshi', 0))
                    results['sanrenpuku']['return'] += payout
        
        # 三連単
        sanrentan_winner = parse_kumiban(payout_row.get('sanrentan_kumiban', ''))
        if sanrentan_winner:
            for bet in race_bets['sanrentan']:
                results['sanrentan']['total'] += 1
                results['sanrentan']['cost'] += unit_bet
                
                if bet == sanrentan_winner:
                    results['sanrentan']['hit'] += 1
                    payout = parse_haraimodoshi(payout_row.get('sanrentan_haraimodoshi', 0))
                    results['sanrentan']['return'] += payout
    
    print(f"✅ マッチしたレース数: {matched_races}/{len(bets)}")
    
    return results, matched_races


def print_backtest_results(results: Dict, matched_races: int):
    """バックテスト結果を表示"""
    print("\n" + "="*80)
    print("📊 Phase 5.5 実払戻金バックテスト 結果（全7券種対応）")
    print("="*80)
    print(f"📅 実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print(f"🏇 対象レース数: {matched_races}レース")
    print("\n" + "-"*80)
    
    total_cost = 0
    total_return = 0
    total_hit = 0
    total_bets = 0
    
    ticket_types = {
        'tansho': '単勝',
        'fukusho': '複勝',
        'umaren': '馬連',
        'wide': 'ワイド',
        'umatan': '馬単',
        'sanrenpuku': '三連複',
        'sanrentan': '三連単'
    }
    
    print(f"{'券種':<10} {'購入点数':>8} {'的中':>6} {'的中率':>8} {'購入額':>10} {'払戻額':>10} {'回収率':>8} {'収支':>10}")
    print("-"*80)
    
    for ticket_type, name in ticket_types.items():
        stats = results[ticket_type]
        hit_rate = (stats['hit'] / stats['total'] * 100) if stats['total'] > 0 else 0
        recovery_rate = (stats['return'] / stats['cost'] * 100) if stats['cost'] > 0 else 0
        profit = stats['return'] - stats['cost']
        
        print(f"{name:<10} {stats['total']:>8,} {stats['hit']:>6,} "
              f"{hit_rate:>7.2f}% {stats['cost']:>9,}円 {stats['return']:>9,}円 "
              f"{recovery_rate:>7.2f}% {profit:>9,}円")
        
        total_cost += stats['cost']
        total_return += stats['return']
        total_hit += stats['hit']
        total_bets += stats['total']
    
    print("-"*80)
    total_hit_rate = (total_hit / total_bets * 100) if total_bets > 0 else 0
    total_recovery_rate = (total_return / total_cost * 100) if total_cost > 0 else 0
    total_profit = total_return - total_cost
    
    print(f"{'合計':<10} {total_bets:>8,} {total_hit:>6,} "
          f"{total_hit_rate:>7.2f}% {total_cost:>9,}円 {total_return:>9,}円 "
          f"{total_recovery_rate:>7.2f}% {total_profit:>9,}円")
    
    print("\n" + "="*80)
    print("🎯 Phase 5.5 目標達成度")
    print("="*80)
    print(f"目標的中率: 30.0% → 実績: {total_hit_rate:.2f}% "
          f"({'✅ 達成' if total_hit_rate >= 30.0 else '❌ 未達成'})")
    print(f"目標回収率: 80.0% → 実績: {total_recovery_rate:.2f}% "
          f"({'✅ 達成' if total_recovery_rate >= 80.0 else '❌ 未達成'})")
    
    return {
        'total_bets': total_bets,
        'total_hit': total_hit,
        'total_hit_rate': total_hit_rate,
        'total_cost': total_cost,
        'total_return': total_return,
        'total_recovery_rate': total_recovery_rate,
        'total_profit': total_profit,
        'details': results
    }


def main():
    """メイン実行関数"""
    print("\n" + "="*80)
    print("🚀 Phase 5.5: 実払戻金バックテスト（全7券種対応） 実行開始")
    print("="*80)
    
    # ファイルパス設定 - Windows/Sandbox 両対応
    current_dir = Path.cwd()
    
    # Phase 5 アンサンブルファイル
    ensemble_csv = current_dir / "predictions" / "phase5_ooi_2025" / "ooi_2025_phase5_ensemble.csv"
    if not ensemble_csv.exists():
        # サンドボックスパス
        ensemble_csv = Path("/home/user/webapp/predictions/phase5_ooi_2025/ooi_2025_phase5_ensemble.csv")
        if not ensemble_csv.exists():
            # uploaded_files パス
            ensemble_csv = Path("/home/user/uploaded_files/ooi_2025_phase5_ensemble.csv")
    
    # 払戻金CSVファイル
    payouts_csv = current_dir / "ooi_2025_payouts_full.csv"
    if not payouts_csv.exists():
        # サンドボックスパス
        payouts_csv = Path("/home/user/uploaded_files/ooi_2025_payouts_full.csv")
        if not payouts_csv.exists():
            # 元のファイル名も試す
            payouts_csv = Path("/home/user/uploaded_files/data-1770339768417.csv")
    
    output_dir = current_dir / "predictions" / "phase5_5_ooi_2025_backtest_full"
    if not output_dir.exists():
        # サンドボックスパス
        output_dir = Path("/home/user/webapp/predictions/phase5_5_ooi_2025_backtest_full")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル存在確認
    print("\n📋 ファイル存在確認:")
    files_to_check = {
        "Phase 5 アンサンブル": str(ensemble_csv),
        "実払戻金CSV（完全版）": str(payouts_csv)
    }
    
    all_files_exist = True
    for name, path in files_to_check.items():
        exists = Path(path).exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {name}: {path}")
        if not exists:
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ 必要なファイルが見つかりません")
        print("\n📝 次のステップ:")
        print("   1. Windows PC で pgAdmin を起動")
        print("   2. get_full_payouts_ooi_2025.sql を実行")
        print(f"   3. CSV にエクスポート: {payouts_csv}")
        return
    
    # データ読み込み
    print("\n" + "="*80)
    print("📥 データ読み込み中...")
    print("="*80)
    
    ensemble_df = pd.read_csv(ensemble_csv)
    print(f"✅ Phase 5 アンサンブル: {len(ensemble_df):,}件")
    
    payouts_df = load_payouts_csv(payouts_csv)
    
    # 買い目生成
    bets, strategy_config = generate_betting_strategy(ensemble_df)
    
    # バックテスト評価
    results, matched_races = evaluate_backtest(bets, payouts_df, strategy_config)
    
    # 結果表示
    summary = print_backtest_results(results, matched_races)
    
    # 結果をJSON保存
    output_json = output_dir / "backtest_results_full.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': summary,
            'strategy': strategy_config,
            'matched_races': matched_races
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 結果保存: {output_json}")
    print("\n🎉 Phase 5.5 バックテスト（全7券種対応）完了！")


if __name__ == "__main__":
    main()
