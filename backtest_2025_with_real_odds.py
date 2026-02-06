#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtest_2025_with_real_odds.py
Phase 5.5: 実オッズを使った正確なバックテスト

PC-KEIBAデータベースから実払戻金を取得し、
Phase 5の買い目と照合して正確な回収率を算出
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

import psycopg2
import pandas as pd
import numpy as np


# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}


def parse_haraimodoshi(haraimodoshi_str: str) -> int:
    """
    払戻金文字列を整数に変換
    
    Args:
        haraimodoshi_str: 払戻金（"000000120"形式）
    
    Returns:
        払戻金（円）
    """
    if not haraimodoshi_str or haraimodoshi_str.strip() == '':
        return 0
    
    try:
        return int(haraimodoshi_str.strip())
    except:
        return 0


def get_real_payouts(keibajo_code: str = '44', year: str = '2025') -> pd.DataFrame:
    """
    PC-KEIBAデータベースから実払戻金を取得
    
    Args:
        keibajo_code: 競馬場コード（デフォルト: 44=大井）
        year: 対象年（デフォルト: 2025）
    
    Returns:
        実払戻金データフレーム
    """
    print("\n" + "="*80)
    print("📊 PC-KEIBAデータベースから実払戻金を取得中...")
    print("="*80)
    
    query = f"""
    -- 実払戻金データ取得SQL
    SELECT 
        -- レース識別情報
        hr.kaisai_nen,
        hr.kaisai_tsukihi,
        hr.keibajo_code,
        hr.race_bango,
        
        -- レースID（8桁）
        hr.kaisai_nen || 
        LPAD(hr.kaisai_tsukihi, 4, '0') || 
        LPAD(hr.keibajo_code, 2, '0') || 
        LPAD(hr.race_bango, 2, '0') AS race_id,
        
        -- 単勝払戻
        hr.haraimodoshi_tansho_1a AS tansho_umaban,
        hr.haraimodoshi_tansho_1b AS tansho_haraimodoshi,
        hr.haraimodoshi_tansho_1c AS tansho_ninkijun,
        
        -- 複勝払戻（1-5着）
        hr.haraimodoshi_fukusho_1a AS fukusho_1_umaban,
        hr.haraimodoshi_fukusho_1b AS fukusho_1_haraimodoshi,
        hr.haraimodoshi_fukusho_2a AS fukusho_2_umaban,
        hr.haraimodoshi_fukusho_2b AS fukusho_2_haraimodoshi,
        hr.haraimodoshi_fukusho_3a AS fukusho_3_umaban,
        hr.haraimodoshi_fukusho_3b AS fukusho_3_haraimodoshi,
        hr.haraimodoshi_fukusho_4a AS fukusho_4_umaban,
        hr.haraimodoshi_fukusho_4b AS fukusho_4_haraimodoshi,
        hr.haraimodoshi_fukusho_5a AS fukusho_5_umaban,
        hr.haraimodoshi_fukusho_5b AS fukusho_5_haraimodoshi,
        
        -- 馬連払戻
        hr.haraimodoshi_umaren_1a AS umaren_kumiban,
        hr.haraimodoshi_umaren_1b AS umaren_haraimodoshi,
        
        -- 馬単払戻
        hr.haraimodoshi_umatan_1a AS umatan_kumiban,
        hr.haraimodoshi_umatan_1b AS umatan_haraimodoshi,
        
        -- ワイド払戻（1-3通り）
        hr.haraimodoshi_wide_1a AS wide_1_kumiban,
        hr.haraimodoshi_wide_1b AS wide_1_haraimodoshi,
        hr.haraimodoshi_wide_2a AS wide_2_kumiban,
        hr.haraimodoshi_wide_2b AS wide_2_haraimodoshi,
        hr.haraimodoshi_wide_3a AS wide_3_kumiban,
        hr.haraimodoshi_wide_3b AS wide_3_haraimodoshi,
        
        -- 三連複払戻
        hr.haraimodoshi_sanrenpuku_1a AS sanrenpuku_kumiban,
        hr.haraimodoshi_sanrenpuku_1b AS sanrenpuku_haraimodoshi,
        
        -- 三連単払戻
        hr.haraimodoshi_sanrentan_1a AS sanrentan_kumiban,
        hr.haraimodoshi_sanrentan_1b AS sanrentan_haraimodoshi
    
    FROM nvd_hr hr
    WHERE hr.kaisai_nen = '{year}'
      AND hr.keibajo_code = '{keibajo_code}'
    ORDER BY hr.kaisai_tsukihi, CAST(hr.race_bango AS INTEGER);
    """
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"  ✅ 取得完了: {len(df)}レース")
        print(f"     - 対象年: {year}")
        print(f"     - 競馬場コード: {keibajo_code}")
        
        # 払戻金を数値に変換
        payout_cols = [col for col in df.columns if 'haraimodoshi' in col]
        for col in payout_cols:
            df[col] = df[col].apply(parse_haraimodoshi)
        
        return df
    
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return pd.DataFrame()


def load_phase5_bets(bets_json_path: str) -> Dict:
    """
    Phase 5の買い目JSONを読み込み
    
    Args:
        bets_json_path: 買い目JSONのパス
    
    Returns:
        買い目データ
    """
    print("\n📂 Phase 5の買い目を読み込み中...")
    
    with open(bets_json_path, 'r', encoding='utf-8') as f:
        bets_data = json.load(f)
    
    print(f"  ✅ 読み込み完了: {bets_data['total_races']}レース")
    print(f"     - 単勝: {bets_data['total_bets']['tansho']}点")
    print(f"     - 馬連: {bets_data['total_bets']['umaren']}点")
    print(f"     - ワイド: {bets_data['total_bets']['wide']}点")
    print(f"     - 三連複: {bets_data['total_bets']['sanrenpuku']}点")
    
    return bets_data


def calculate_tansho_return(bet: Dict, payout_row: pd.Series, unit_bet: int = 100) -> Tuple[int, int, bool]:
    """
    単勝の払戻を計算
    
    Args:
        bet: 単勝の買い目
        payout_row: 払戻金データの行
        unit_bet: 1点あたりの賭け金
    
    Returns:
        (投資額, 払戻額, 的中フラグ)
    """
    umaban = str(bet['umaban']).zfill(2)
    investment = unit_bet
    
    # 実際の単勝払戻を取得
    tansho_umaban = str(payout_row.get('tansho_umaban', '')).zfill(2)
    tansho_haraimodoshi = payout_row.get('tansho_haraimodoshi', 0)
    
    if umaban == tansho_umaban and tansho_haraimodoshi > 0:
        payout = tansho_haraimodoshi
        return investment, payout, True
    else:
        return investment, 0, False


def calculate_umaren_return(bet: Dict, payout_row: pd.Series, unit_bet: int = 100) -> Tuple[int, int, bool]:
    """
    馬連の払戻を計算
    
    Args:
        bet: 馬連の買い目
        payout_row: 払戻金データの行
        unit_bet: 1点あたりの賭け金
    
    Returns:
        (投資額, 払戻額, 的中フラグ)
    """
    horses = sorted([str(h).zfill(2) for h in bet['horses']])
    bet_kumiban = ''.join(horses)
    investment = unit_bet
    
    # 実際の馬連払戻を取得
    umaren_kumiban = str(payout_row.get('umaren_kumiban', '')).zfill(4)
    umaren_haraimodoshi = payout_row.get('umaren_haraimodoshi', 0)
    
    # 組番の正規化（順序を統一）
    if len(umaren_kumiban) == 4:
        umaren_sorted = ''.join(sorted([umaren_kumiban[:2], umaren_kumiban[2:]]))
    else:
        umaren_sorted = ''
    
    if bet_kumiban == umaren_sorted and umaren_haraimodoshi > 0:
        payout = umaren_haraimodoshi
        return investment, payout, True
    else:
        return investment, 0, False


def calculate_wide_return(bet: Dict, payout_row: pd.Series, unit_bet: int = 100) -> Tuple[int, int, bool]:
    """
    ワイドの払戻を計算
    
    Args:
        bet: ワイドの買い目
        payout_row: 払戻金データの行
        unit_bet: 1点あたりの賭け金
    
    Returns:
        (投資額, 払戻額, 的中フラグ)
    """
    horses = sorted([str(h).zfill(2) for h in bet['horses']])
    bet_kumiban = ''.join(horses)
    investment = unit_bet
    
    # 実際のワイド払戻を取得（最大3通り）
    for i in range(1, 4):
        wide_kumiban = str(payout_row.get(f'wide_{i}_kumiban', '')).zfill(4)
        wide_haraimodoshi = payout_row.get(f'wide_{i}_haraimodoshi', 0)
        
        # 組番の正規化
        if len(wide_kumiban) == 4:
            wide_sorted = ''.join(sorted([wide_kumiban[:2], wide_kumiban[2:]]))
        else:
            continue
        
        if bet_kumiban == wide_sorted and wide_haraimodoshi > 0:
            payout = wide_haraimodoshi
            return investment, payout, True
    
    return investment, 0, False


def calculate_sanrenpuku_return(bet: Dict, payout_row: pd.Series, unit_bet: int = 100) -> Tuple[int, int, bool]:
    """
    三連複の払戻を計算
    
    Args:
        bet: 三連複の買い目
        payout_row: 払戻金データの行
        unit_bet: 1点あたりの賭け金
    
    Returns:
        (投資額, 払戻額, 的中フラグ)
    """
    horses = sorted([str(h).zfill(2) for h in bet['horses']])
    bet_kumiban = ''.join(horses)
    investment = unit_bet
    
    # 実際の三連複払戻を取得
    sanrenpuku_kumiban = str(payout_row.get('sanrenpuku_kumiban', '')).zfill(6)
    sanrenpuku_haraimodoshi = payout_row.get('sanrenpuku_haraimodoshi', 0)
    
    # 組番の正規化
    if len(sanrenpuku_kumiban) == 6:
        sanrenpuku_sorted = ''.join(sorted([
            sanrenpuku_kumiban[:2],
            sanrenpuku_kumiban[2:4],
            sanrenpuku_kumiban[4:6]
        ]))
    else:
        sanrenpuku_sorted = ''
    
    if bet_kumiban == sanrenpuku_sorted and sanrenpuku_haraimodoshi > 0:
        payout = sanrenpuku_haraimodoshi
        return investment, payout, True
    else:
        return investment, 0, False


def run_backtest_with_real_odds(
    bets_data: Dict,
    payout_df: pd.DataFrame,
    unit_bet: int = 100
) -> Dict:
    """
    実オッズを使用したバックテストを実行
    
    Args:
        bets_data: Phase 5の買い目データ
        payout_df: 実払戻金データ
        unit_bet: 1点あたりの賭け金
    
    Returns:
        バックテスト結果
    """
    print("\n" + "="*80)
    print("🔄 実オッズを使用したバックテスト実行中...")
    print("="*80)
    
    results = {
        'total_investment': 0,
        'total_payout': 0,
        'total_profit': 0,
        'recovery_rate': 0.0,
        'hit_count': 0,
        'total_bets': 0,
        'hit_rate': 0.0,
        'by_bet_type': {
            'tansho': {'investment': 0, 'payout': 0, 'hits': 0, 'total': 0, 'recovery_rate': 0.0, 'hit_rate': 0.0},
            'umaren': {'investment': 0, 'payout': 0, 'hits': 0, 'total': 0, 'recovery_rate': 0.0, 'hit_rate': 0.0},
            'wide': {'investment': 0, 'payout': 0, 'hits': 0, 'total': 0, 'recovery_rate': 0.0, 'hit_rate': 0.0},
            'sanrenpuku': {'investment': 0, 'payout': 0, 'hits': 0, 'total': 0, 'recovery_rate': 0.0, 'hit_rate': 0.0}
        },
        'race_results': []
    }
    
    # レースIDでインデックス化
    payout_dict = {row['race_id']: row for _, row in payout_df.iterrows()}
    
    matched_races = 0
    unmatched_races = 0
    
    for race_bets in bets_data['races']:
        race_id = race_bets['race_id']
        
        # 実払戻金データを取得
        if race_id not in payout_dict:
            unmatched_races += 1
            continue
        
        matched_races += 1
        payout_row = payout_dict[race_id]
        
        race_result = {
            'race_id': race_id,
            'investment': 0,
            'payout': 0,
            'profit': 0,
            'hits': []
        }
        
        # 単勝
        for bet in race_bets['bets']['tansho']:
            inv, pay, hit = calculate_tansho_return(bet, payout_row, unit_bet)
            results['total_investment'] += inv
            results['total_payout'] += pay
            results['by_bet_type']['tansho']['investment'] += inv
            results['by_bet_type']['tansho']['payout'] += pay
            results['by_bet_type']['tansho']['total'] += 1
            results['total_bets'] += 1
            race_result['investment'] += inv
            race_result['payout'] += pay
            
            if hit:
                results['hit_count'] += 1
                results['by_bet_type']['tansho']['hits'] += 1
                race_result['hits'].append('tansho')
        
        # 馬連
        for bet in race_bets['bets']['umaren']:
            inv, pay, hit = calculate_umaren_return(bet, payout_row, unit_bet)
            results['total_investment'] += inv
            results['total_payout'] += pay
            results['by_bet_type']['umaren']['investment'] += inv
            results['by_bet_type']['umaren']['payout'] += pay
            results['by_bet_type']['umaren']['total'] += 1
            results['total_bets'] += 1
            race_result['investment'] += inv
            race_result['payout'] += pay
            
            if hit:
                results['hit_count'] += 1
                results['by_bet_type']['umaren']['hits'] += 1
                race_result['hits'].append('umaren')
        
        # ワイド
        for bet in race_bets['bets']['wide']:
            inv, pay, hit = calculate_wide_return(bet, payout_row, unit_bet)
            results['total_investment'] += inv
            results['total_payout'] += pay
            results['by_bet_type']['wide']['investment'] += inv
            results['by_bet_type']['wide']['payout'] += pay
            results['by_bet_type']['wide']['total'] += 1
            results['total_bets'] += 1
            race_result['investment'] += inv
            race_result['payout'] += pay
            
            if hit:
                results['hit_count'] += 1
                results['by_bet_type']['wide']['hits'] += 1
                race_result['hits'].append('wide')
        
        # 三連複
        for bet in race_bets['bets']['sanrenpuku']:
            inv, pay, hit = calculate_sanrenpuku_return(bet, payout_row, unit_bet)
            results['total_investment'] += inv
            results['total_payout'] += pay
            results['by_bet_type']['sanrenpuku']['investment'] += inv
            results['by_bet_type']['sanrenpuku']['payout'] += pay
            results['by_bet_type']['sanrenpuku']['total'] += 1
            results['total_bets'] += 1
            race_result['investment'] += inv
            race_result['payout'] += pay
            
            if hit:
                results['hit_count'] += 1
                results['by_bet_type']['sanrenpuku']['hits'] += 1
                race_result['hits'].append('sanrenpuku')
        
        race_result['profit'] = race_result['payout'] - race_result['investment']
        results['race_results'].append(race_result)
    
    # 総合指標の計算
    results['total_profit'] = results['total_payout'] - results['total_investment']
    if results['total_investment'] > 0:
        results['recovery_rate'] = (results['total_payout'] / results['total_investment']) * 100
    if results['total_bets'] > 0:
        results['hit_rate'] = (results['hit_count'] / results['total_bets']) * 100
    
    # 券種別の回収率・的中率計算
    for bet_type in results['by_bet_type']:
        bt = results['by_bet_type'][bet_type]
        if bt['investment'] > 0:
            bt['recovery_rate'] = (bt['payout'] / bt['investment']) * 100
        if bt['total'] > 0:
            bt['hit_rate'] = (bt['hits'] / bt['total']) * 100
    
    print(f"\n  ✅ バックテスト完了")
    print(f"     - マッチしたレース: {matched_races}")
    print(f"     - マッチしなかったレース: {unmatched_races}")
    print(f"     - 総投資額: {results['total_investment']:,}円")
    print(f"     - 総払戻額: {results['total_payout']:,}円")
    print(f"     - 収支: {results['total_profit']:+,}円")
    print(f"     - 回収率: {results['recovery_rate']:.2f}%")
    print(f"     - 的中率: {results['hit_rate']:.2f}%")
    
    return results


def save_results(results: Dict, output_dir: str):
    """
    バックテスト結果を保存
    
    Args:
        results: バックテスト結果
        output_dir: 出力ディレクトリ
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # JSON形式で保存
    output_file = output_path / 'backtest_results_real_odds.json'
    
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_investment': results['total_investment'],
            'total_payout': results['total_payout'],
            'total_profit': results['total_profit'],
            'recovery_rate': results['recovery_rate'],
            'hit_count': results['hit_count'],
            'total_bets': results['total_bets'],
            'hit_rate': results['hit_rate']
        },
        'by_bet_type': results['by_bet_type'],
        'race_results': results['race_results']
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 バックテスト結果を保存: {output_file}")


def print_comparison(results: Dict):
    """
    Phase 5（仮オッズ）との比較を表示
    
    Args:
        results: Phase 5.5のバックテスト結果
    """
    print("\n" + "="*80)
    print("📊 Phase 5（仮オッズ）vs Phase 5.5（実オッズ）比較")
    print("="*80)
    
    phase5_fake = {
        'recovery_rate': 23.86,
        'hit_rate': 4.12,
        'total_investment': 293800,
        'total_payout': 70100,
        'total_profit': -223700
    }
    
    print("\n| 項目 | Phase 5（仮） | Phase 5.5（実） | 改善 |")
    print("|:---|---:|---:|:---|")
    print(f"| 回収率 | {phase5_fake['recovery_rate']:.2f}% | **{results['recovery_rate']:.2f}%** | {results['recovery_rate'] - phase5_fake['recovery_rate']:+.2f}% |")
    print(f"| 的中率 | {phase5_fake['hit_rate']:.2f}% | **{results['hit_rate']:.2f}%** | {results['hit_rate'] - phase5_fake['hit_rate']:+.2f}% |")
    print(f"| 総投資額 | {phase5_fake['total_investment']:,}円 | {results['total_investment']:,}円 | {results['total_investment'] - phase5_fake['total_investment']:+,}円 |")
    print(f"| 総払戻額 | {phase5_fake['total_payout']:,}円 | {results['total_payout']:,}円 | {results['total_payout'] - phase5_fake['total_payout']:+,}円 |")
    print(f"| 損益 | {phase5_fake['total_profit']:+,}円 | **{results['total_profit']:+,}円** | {results['total_profit'] - phase5_fake['total_profit']:+,}円 |")
    
    print("\n📈 券種別回収率:")
    for bet_type, data in results['by_bet_type'].items():
        if data['total'] > 0:
            print(f"   - {bet_type}: {data['recovery_rate']:.2f}% (的中率: {data['hit_rate']:.2f}%)")


def main():
    parser = argparse.ArgumentParser(description='Phase 5.5: 実オッズを使った正確なバックテスト')
    parser.add_argument('--keibajo', default='44', help='競馬場コード（デフォルト: 44=大井）')
    parser.add_argument('--year', default='2025', help='対象年（デフォルト: 2025）')
    parser.add_argument('--bets', default='predictions/phase5_ooi_test/betting_recommendations.json', 
                        help='Phase 5の買い目JSONパス')
    parser.add_argument('--output', default='predictions/phase5.5_ooi_backtest/', 
                        help='出力ディレクトリ')
    parser.add_argument('--unit-bet', type=int, default=100, help='1点あたりの賭け金（デフォルト: 100円）')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🚀 Phase 5.5: 実オッズを使った正確なバックテスト開始")
    print("="*80)
    print(f"  競馬場コード: {args.keibajo}")
    print(f"  対象年: {args.year}")
    print(f"  買い目: {args.bets}")
    print(f"  出力先: {args.output}")
    
    # Step 1: 実払戻金データを取得
    payout_df = get_real_payouts(args.keibajo, args.year)
    
    if payout_df.empty:
        print("\n❌ 実払戻金データの取得に失敗しました")
        return 1
    
    # Step 2: Phase 5の買い目を読み込み
    bets_data = load_phase5_bets(args.bets)
    
    # Step 3: バックテストを実行
    results = run_backtest_with_real_odds(bets_data, payout_df, args.unit_bet)
    
    # Step 4: 結果を保存
    save_results(results, args.output)
    
    # Step 5: Phase 5との比較を表示
    print_comparison(results)
    
    print("\n" + "="*80)
    print("🎉 Phase 5.5 バックテスト完了！")
    print("="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
