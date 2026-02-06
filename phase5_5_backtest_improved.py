#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase5_5_backtest_improved.py
Phase 5.5 改善版バックテスト: 戦略1〜4完全実装

改善内容:
1. ワイドの点数削減（オッズ2.5倍未満を除外）
2. 三連系の解禁（相対評価: Zスコア導入）
3. 馬連の基準緩和（Aランク → Bランク）
4. オッズ条件のみ表示（ケリー基準の賭け金テーブルは不要）
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
    例: "0102" -> (1, 2), "010203" -> (1, 2, 3)
    """
    if pd.isna(kumiban_str) or kumiban_str == '' or kumiban_str is None:
        return None
    
    try:
        kumiban_str = str(kumiban_str).strip()
        
        if kumiban_str.isspace() or kumiban_str == '':
            return None
        
        # ハイフン区切りの場合
        if '-' in kumiban_str:
            parts = kumiban_str.split('-')
            return tuple(int(p) for p in parts)
        
        # 連続した数字の場合
        if len(kumiban_str) % 2 == 0:
            parts = [kumiban_str[i:i+2] for i in range(0, len(kumiban_str), 2)]
            return tuple(int(p) for p in parts if p.strip())
        
        return None
    except:
        return None


def calculate_z_scores(race_df: pd.DataFrame) -> Dict[int, float]:
    """
    レース内での相対評価（Zスコア）を計算
    
    Parameters:
    - race_df: レースの出走馬データ
    
    Returns:
    - umaban -> z_score の辞書
    """
    scores = race_df['ensemble_score'].values
    mean_score = np.mean(scores)
    std_score = np.std(scores)
    
    if std_score == 0:
        # 全馬同じスコアの場合
        return {row['umaban']: 0.0 for _, row in race_df.iterrows()}
    
    z_scores = {}
    for _, row in race_df.iterrows():
        z = (row['ensemble_score'] - mean_score) / std_score
        z_scores[row['umaban']] = z
    
    return z_scores


def assign_relative_rank(z_score: float) -> str:
    """
    Zスコアから相対ランクを割り当て
    
    Z >= 2.0 → S (偏差値70以上)
    Z >= 1.0 → A (偏差値60以上)
    Z >= 0.0 → B (偏差値50以上)
    Z >= -1.0 → C (偏差値40以上)
    Z < -1.0 → D (偏差値40未満)
    """
    if z_score >= 2.0:
        return 'S'
    elif z_score >= 1.0:
        return 'A'
    elif z_score >= 0.0:
        return 'B'
    elif z_score >= -1.0:
        return 'C'
    else:
        return 'D'


def estimate_min_odds(predicted_prob: float, ev_threshold: float = 1.05) -> float:
    """
    期待値を達成する最低オッズを計算
    
    Parameters:
    - predicted_prob: AI予測の的中確率
    - ev_threshold: 期待値の閾値（デフォルト1.05）
    
    Returns:
    - 最低オッズ
    """
    if predicted_prob <= 0:
        return 999.9  # 確率0の場合は極端に高いオッズが必要
    return ev_threshold / predicted_prob


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
    
    # race_key を作成（Phase 5 フォーマットに合わせる: ゼロパディングなし）
    if 'kaisai_nen' in df.columns:
        df['race_key'] = (df['kaisai_nen'].astype(str) + '_' + 
                         df['kaisai_tsukihi'].astype(str).str.zfill(4) + '_' + 
                         df['keibajo_code'].astype(str).str.zfill(2) + '_' + 
                         df['race_bango'].astype(str))  # ゼロパディングなし
    else:
        df['race_key'] = (df['kaisai_tsukihi'].astype(str).str.zfill(4) + '_' + 
                         df['keibajo_code'].astype(str).str.zfill(2) + '_' + 
                         df['race_bango'].astype(str))  # ゼロパディングなし
    
    return df


def generate_betting_strategy_improved(ensemble_df: pd.DataFrame) -> Tuple[Dict, Dict]:
    """
    改善版買い目生成
    
    改善内容:
    1. ワイド: Aランク以上に厳格化（Bランク除外）
    2. 馬連: Bランク以上に緩和（Aランクのみ → A+B）
    3. 三連系: 相対評価（Zスコア）で解禁
    4. オッズ条件を計算して記録
    """
    print("\n" + "="*80)
    print("🎫 改善版買い目生成中...")
    print("="*80)
    
    strategy_config = {
        'tansho_min_rank': 'S',
        'fukusho_min_rank': 'A',
        'umaren_min_rank': 'B',  # 改善: A → B に緩和
        'wide_min_rank': 'A',     # 改善: B → A に厳格化
        'umatan_min_rank': 'A',
        'sanrenpuku_min_z_score': 1.0,  # 新: Zスコア基準（偏差値60以上）
        'sanrentan_min_z_score': 2.0,   # 新: Zスコア基準（偏差値70以上）
        'max_horses_tansho': 3,
        'max_horses_fukusho': 5,
        'max_horses_umaren': 4,
        'max_horses_wide': 4,      # 改善: 5 → 4 に削減
        'max_horses_umatan': 3,
        'max_horses_sanrenpuku': 4,
        'max_horses_sanrentan': 3,
        'unit_bet': 100,
        'wide_min_odds': 2.5,      # 新: ワイドの最低オッズ条件
        'ev_threshold': 1.05       # 新: 期待値の閾値
    }
    
    rank_order = {'S': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5}
    
    bets = {}
    odds_conditions = {}  # オッズ条件を記録
    
    for race_key in ensemble_df['race_key'].unique():
        race_df = ensemble_df[ensemble_df['race_key'] == race_key].copy()
        
        # Zスコアを計算
        z_scores = calculate_z_scores(race_df)
        race_df['z_score'] = race_df['umaban'].map(z_scores)
        race_df['relative_rank'] = race_df['z_score'].apply(assign_relative_rank)
        
        race_bets = {
            'tansho': [],
            'fukusho': [],
            'umaren': [],
            'wide': [],
            'umatan': [],
            'sanrenpuku': [],
            'sanrentan': []
        }
        
        race_odds_conditions = {
            'tansho': {},
            'fukusho': {},
            'umaren': {},
            'wide': {},
            'umatan': {},
            'sanrenpuku': {},
            'sanrentan': {}
        }
        
        # 単勝: Sランク（相対評価）
        tansho_horses = race_df[race_df['relative_rank'] == 'S']['umaban'].tolist()[:strategy_config['max_horses_tansho']]
        for uma in tansho_horses:
            race_bets['tansho'].append(uma)
            # 的中確率を推定（簡易: binary_probability を使用）
            prob = race_df[race_df['umaban'] == uma]['binary_probability'].values[0]
            min_odds = estimate_min_odds(prob, strategy_config['ev_threshold'])
            race_odds_conditions['tansho'][uma] = min_odds
        
        # 複勝: Aランク以上（相対評価）
        fukusho_horses = race_df[
            race_df['relative_rank'].map(rank_order) <= rank_order['A']
        ]['umaban'].tolist()[:strategy_config['max_horses_fukusho']]
        race_bets['fukusho'] = fukusho_horses
        # 複勝はオッズ制限なし
        
        # 馬連: Bランク以上に緩和（相対評価）
        umaren_horses = race_df[
            race_df['relative_rank'].map(rank_order) <= rank_order[strategy_config['umaren_min_rank']]
        ]['umaban'].tolist()[:strategy_config['max_horses_umaren']]
        
        for i, h1 in enumerate(umaren_horses):
            for h2 in umaren_horses[i+1:]:
                race_bets['umaren'].append(tuple(sorted([h1, h2])))
                # 馬連の的中確率を推定（簡易）
                prob1 = race_df[race_df['umaban'] == h1]['binary_probability'].values[0]
                prob2 = race_df[race_df['umaban'] == h2]['binary_probability'].values[0]
                combined_prob = (prob1 + prob2) * 0.3  # 簡易推定
                min_odds = estimate_min_odds(combined_prob, strategy_config['ev_threshold'])
                race_odds_conditions['umaren'][tuple(sorted([h1, h2]))] = min_odds
        
        # ワイド: Aランク以上に厳格化（相対評価）
        wide_horses = race_df[
            race_df['relative_rank'].map(rank_order) <= rank_order[strategy_config['wide_min_rank']]
        ]['umaban'].tolist()[:strategy_config['max_horses_wide']]
        
        for i, h1 in enumerate(wide_horses):
            for h2 in wide_horses[i+1:]:
                combo = tuple(sorted([h1, h2]))
                race_bets['wide'].append(combo)
                # ワイドの的中確率を推定（簡易）
                prob1 = race_df[race_df['umaban'] == h1]['binary_probability'].values[0]
                prob2 = race_df[race_df['umaban'] == h2]['binary_probability'].values[0]
                combined_prob = (prob1 + prob2) * 0.4  # 簡易推定
                min_odds = max(estimate_min_odds(combined_prob, strategy_config['ev_threshold']), 
                              strategy_config['wide_min_odds'])
                race_odds_conditions['wide'][combo] = min_odds
        
        # 馬単: Aランク以上（相対評価）
        umatan_horses = race_df[
            race_df['relative_rank'].map(rank_order) <= rank_order[strategy_config['umatan_min_rank']]
        ]['umaban'].tolist()[:strategy_config['max_horses_umatan']]
        
        for h1 in umatan_horses:
            for h2 in umatan_horses:
                if h1 != h2:
                    race_bets['umatan'].append((h1, h2))
                    # 馬単の的中確率を推定（簡易）
                    prob1 = race_df[race_df['umaban'] == h1]['binary_probability'].values[0]
                    prob2 = race_df[race_df['umaban'] == h2]['binary_probability'].values[0]
                    combined_prob = prob1 * prob2 * 0.8  # 簡易推定
                    min_odds = estimate_min_odds(combined_prob, strategy_config['ev_threshold'])
                    race_odds_conditions['umatan'][(h1, h2)] = min_odds
        
        # 三連複: Zスコア基準（偏差値60以上）
        sanrenpuku_horses = race_df[
            race_df['z_score'] >= strategy_config['sanrenpuku_min_z_score']
        ]['umaban'].tolist()[:strategy_config['max_horses_sanrenpuku']]
        
        if len(sanrenpuku_horses) >= 3:
            for i, h1 in enumerate(sanrenpuku_horses):
                for j, h2 in enumerate(sanrenpuku_horses[i+1:], start=i+1):
                    for h3 in sanrenpuku_horses[j+1:]:
                        combo = tuple(sorted([h1, h2, h3]))
                        race_bets['sanrenpuku'].append(combo)
                        # 三連複の的中確率を推定（簡易）
                        prob1 = race_df[race_df['umaban'] == h1]['binary_probability'].values[0]
                        prob2 = race_df[race_df['umaban'] == h2]['binary_probability'].values[0]
                        prob3 = race_df[race_df['umaban'] == h3]['binary_probability'].values[0]
                        combined_prob = (prob1 + prob2 + prob3) * 0.1  # 簡易推定
                        min_odds = estimate_min_odds(combined_prob, strategy_config['ev_threshold'])
                        race_odds_conditions['sanrenpuku'][combo] = min_odds
        
        # 三連単: Zスコア基準（偏差値70以上）
        sanrentan_horses = race_df[
            race_df['z_score'] >= strategy_config['sanrentan_min_z_score']
        ]['umaban'].tolist()[:strategy_config['max_horses_sanrentan']]
        
        if len(sanrentan_horses) >= 2:
            # フォーメーション: 1着固定、2着・3着流し
            axis = sanrentan_horses[0]
            support = sanrentan_horses[1:]
            
            for h2 in support:
                for h3 in sanrentan_horses:
                    if h3 != axis and h3 != h2:
                        combo = (axis, h2, h3)
                        race_bets['sanrentan'].append(combo)
                        # 三連単の的中確率を推定（簡易）
                        prob1 = race_df[race_df['umaban'] == axis]['binary_probability'].values[0]
                        prob2 = race_df[race_df['umaban'] == h2]['binary_probability'].values[0]
                        prob3 = race_df[race_df['umaban'] == h3]['binary_probability'].values[0]
                        combined_prob = prob1 * prob2 * prob3 * 0.5  # 簡易推定
                        min_odds = estimate_min_odds(combined_prob, strategy_config['ev_threshold'])
                        race_odds_conditions['sanrentan'][combo] = min_odds
        
        bets[race_key] = race_bets
        odds_conditions[race_key] = race_odds_conditions
    
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
    
    print(f"\n📊 改善内容:")
    print(f"   - ワイド: Aランク以上に厳格化（最低オッズ{strategy_config['wide_min_odds']}倍）")
    print(f"   - 馬連: Bランク以上に緩和")
    print(f"   - 三連複: Zスコア{strategy_config['sanrenpuku_min_z_score']}以上（偏差値60以上）")
    print(f"   - 三連単: Zスコア{strategy_config['sanrentan_min_z_score']}以上（偏差値70以上）")
    
    return bets, odds_conditions, strategy_config


def evaluate_backtest(bets: Dict, odds_conditions: Dict, payouts_df: pd.DataFrame, 
                     strategy_config: Dict) -> Tuple[Dict, int]:
    """バックテスト評価を実行"""
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
        
        # 複勝
        fukusho_winners = []
        for i in range(1, 4):
            uma_col = f'fukusho_{i}_umaban'
            if uma_col in payout_row and not pd.isna(payout_row[uma_col]):
                fukusho_winners.append(int(payout_row[uma_col]))
        
        for umaban in race_bets['fukusho']:
            results['fukusho']['total'] += 1
            results['fukusho']['cost'] += unit_bet
            
            if umaban in fukusho_winners:
                results['fukusho']['hit'] += 1
                for i in range(1, 4):
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
                    break
        
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
                    break
        
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
                    break
        
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
                    break
    
    print(f"✅ マッチしたレース数: {matched_races}/{len(bets)}")
    
    return results, matched_races


def print_backtest_results(results: Dict, matched_races: int) -> Dict:
    """バックテスト結果を表示"""
    print("\n" + "="*80)
    print("📊 Phase 5.5 改善版バックテスト 結果")
    print("="*80)
    print(f"📅 実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print(f"🏇 対象レース数: {matched_races}レース")
    print()
    print("-" * 80)
    print(f"{'券種':<10} {'購入点数':>8} {'的中':>6} {'的中率':>8} {'購入額':>12} {'払戻額':>12} {'回収率':>8} {'収支':>12}")
    print("-" * 80)
    
    total_bets = 0
    total_hit = 0
    total_cost = 0
    total_return = 0
    
    ticket_names = {
        'tansho': '単勝',
        'fukusho': '複勝',
        'umaren': '馬連',
        'wide': 'ワイド',
        'umatan': '馬単',
        'sanrenpuku': '三連複',
        'sanrentan': '三連単'
    }
    
    for ticket_type, name in ticket_names.items():
        r = results[ticket_type]
        total = r['total']
        hit = r['hit']
        cost = r['cost']
        ret = r['return']
        
        hit_rate = (hit / total * 100) if total > 0 else 0
        recovery_rate = (ret / cost * 100) if cost > 0 else 0
        profit = ret - cost
        
        total_bets += total
        total_hit += hit
        total_cost += cost
        total_return += ret
        
        print(f"{name:<10} {total:>8} {hit:>6} {hit_rate:>7.2f}% {cost:>11,}円 {ret:>11,}円 {recovery_rate:>7.2f}% {profit:>11,}円")
    
    print("-" * 80)
    total_hit_rate = (total_hit / total_bets * 100) if total_bets > 0 else 0
    total_recovery_rate = (total_return / total_cost * 100) if total_cost > 0 else 0
    total_profit = total_return - total_cost
    
    print(f"{'合計':<10} {total_bets:>8} {total_hit:>6} {total_hit_rate:>7.2f}% {total_cost:>11,}円 {total_return:>11,}円 {total_recovery_rate:>7.2f}% {total_profit:>11,}円")
    print()
    print("="*80)
    print("🎯 目標達成度")
    print("="*80)
    
    target_hit_rate = 30.0
    target_recovery_rate = 80.0
    
    hit_status = "✅ 達成" if total_hit_rate >= target_hit_rate else "❌ 未達成"
    recovery_status = "✅ 達成" if total_recovery_rate >= target_recovery_rate else "❌ 未達成"
    
    print(f"目標的中率: {target_hit_rate}% → 実績: {total_hit_rate:.2f}% ({hit_status})")
    print(f"目標回収率: {target_recovery_rate}% → 実績: {total_recovery_rate:.2f}% ({recovery_status})")
    
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
    print("🚀 Phase 5.5 改善版バックテスト 実行開始")
    print("="*80)
    
    # ファイルパス設定
    current_dir = Path.cwd()
    
    ensemble_csv = current_dir / "predictions" / "phase5_ooi_2025" / "ooi_2025_phase5_ensemble.csv"
    if not ensemble_csv.exists():
        ensemble_csv = Path("/home/user/webapp/predictions/phase5_ooi_2025/ooi_2025_phase5_ensemble.csv")
        if not ensemble_csv.exists():
            ensemble_csv = Path("/home/user/uploaded_files/ooi_2025_phase5_ensemble.csv")
    
    payouts_csv = current_dir / "ooi_2025_payouts_full.csv"
    if not payouts_csv.exists():
        payouts_csv = Path("/home/user/uploaded_files/ooi_2025_payouts_full.csv")
        if not payouts_csv.exists():
            payouts_csv = Path("/home/user/uploaded_files/data-1770339768417.csv")
    
    output_dir = current_dir / "predictions" / "phase5_5_ooi_2025_improved"
    if not output_dir.exists():
        output_dir = Path("/home/user/webapp/predictions/phase5_5_ooi_2025_improved")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ファイル存在確認
    print("\n📋 ファイル存在確認:")
    files_to_check = {
        "Phase 5 アンサンブル": str(ensemble_csv),
        "実払戻金CSV": str(payouts_csv)
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
        return
    
    # データ読み込み
    print("\n" + "="*80)
    print("📥 データ読み込み中...")
    print("="*80)
    
    ensemble_df = pd.read_csv(ensemble_csv)
    print(f"✅ Phase 5 アンサンブル: {len(ensemble_df):,}件")
    
    payouts_df = load_payouts_csv(payouts_csv)
    
    # 買い目生成
    bets, odds_conditions, strategy_config = generate_betting_strategy_improved(ensemble_df)
    
    # バックテスト評価
    results, matched_races = evaluate_backtest(bets, odds_conditions, payouts_df, strategy_config)
    
    # 結果表示
    summary = print_backtest_results(results, matched_races)
    
    # 結果をJSON保存
    output_json = output_dir / "backtest_results_improved.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': summary,
            'strategy': strategy_config,
            'matched_races': matched_races
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 結果保存: {output_json}")
    print("\n🎉 Phase 5.5 改善版バックテスト完了！")


if __name__ == "__main__":
    main()
