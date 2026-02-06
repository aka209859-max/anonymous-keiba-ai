#!/usr/bin/env python3
"""
Phase 5.5: Plan C（A+B両方実行）バックテスト

改善内容:
- Plan A: ワイドをSランクのみに厳格化
- Plan B: 三連単の基準を緩和（Zスコア2.0 → 1.5）

実行環境: サンドボックス
対象: 大井競馬場 2025年 Phase 5 アンサンブル（231レース）
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import pandas as pd
import numpy as np


def parse_haraimodoshi(value) -> int:
    """払戻金を整数に変換"""
    if pd.isna(value) or value == '' or value is None:
        return 0
    try:
        return int(float(value))
    except:
        return 0


def parse_kumiban(kumiban_str) -> Optional[Tuple[int, ...]]:
    """
    組番を解析
    例: '0611' → (6, 11)
    例: '050611' → (5, 6, 11)
    """
    if pd.isna(kumiban_str) or str(kumiban_str).strip() == '':
        return None
    
    s = str(kumiban_str).strip()
    
    # ハイフン形式の場合
    if '-' in s:
        try:
            return tuple(int(x) for x in s.split('-'))
        except:
            return None
    
    # 連続数字形式の場合
    try:
        # 2頭立て（4桁）
        if len(s) == 4:
            return (int(s[:2]), int(s[2:4]))
        # 3頭立て（6桁）
        elif len(s) == 6:
            return (int(s[:2]), int(s[2:4]), int(s[4:6]))
        else:
            return None
    except:
        return None


def calculate_z_score(race_df: pd.DataFrame, col: str = 'ensemble_score') -> pd.DataFrame:
    """レース内でZスコアを計算"""
    mean_val = race_df[col].mean()
    std_val = race_df[col].std()
    
    if std_val == 0 or pd.isna(std_val):
        race_df['z_score'] = 0.0
    else:
        race_df['z_score'] = (race_df[col] - mean_val) / std_val
    
    return race_df


def z_score_to_rank(z_score: float) -> str:
    """ZスコアからランクへOmitting変換"""
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


def generate_betting_strategy_plan_c(ensemble_df: pd.DataFrame) -> Tuple[Dict, Dict]:
    """
    Plan C: A+B両方実行
    
    改善内容:
    - Plan A: ワイドをSランクのみに厳格化
    - Plan B: 三連単の基準を緩和（Zスコア2.0 → 1.5）
    """
    print("\n" + "="*80)
    print("🎯 Plan C: A+B両方実行 - 買い目生成中...")
    print("="*80)
    
    strategy_config = {
        'tansho_min_rank': 'S',
        'fukusho_min_rank': 'A',
        'umaren_min_rank': 'B',
        'wide_min_rank': 'S',     # 🔥 Plan A: A → S に厳格化
        'umatan_min_rank': 'A',
        'sanrenpuku_min_z_score': 1.0,
        'sanrentan_min_z_score': 1.5,  # 🔥 Plan B: 2.0 → 1.5 に緩和
        'max_horses_tansho': 3,
        'max_horses_fukusho': 5,
        'max_horses_umaren': 4,
        'max_horses_wide': 2,     # 🔥 Plan A: 4 → 2 に削減（Sランク軸馬+1頭）
        'max_horses_umatan': 2,   # 🔥 Plan C: 3 → 2 に削減（軸馬+1頭）
        'max_horses_sanrenpuku': 4,
        'max_horses_sanrentan': 3,
        'unit_bet': 100,
        'wide_min_odds': 2.5,
        'ev_threshold': 1.05
    }
    
    rank_order = {'S': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5}
    
    bets = {}
    
    for race_key in ensemble_df['race_key'].unique():
        race_df = ensemble_df[ensemble_df['race_key'] == race_key].copy()
        
        # Zスコアを計算
        race_df = calculate_z_score(race_df, 'ensemble_score')
        
        race_bets = {
            'tansho': [],
            'fukusho': [],
            'umaren': [],
            'wide': [],
            'umatan': [],
            'sanrenpuku': [],
            'sanrentan': []
        }
        
        # 単勝: Sランクのみ
        tansho_horses = race_df[race_df['rank'] == strategy_config['tansho_min_rank']]['umaban'].tolist()
        tansho_horses = tansho_horses[:strategy_config['max_horses_tansho']]
        for h in tansho_horses:
            race_bets['tansho'].append({'umaban': h})
        
        # 複勝: Aランク以上
        fukusho_horses = race_df[
            race_df['rank'].apply(lambda r: rank_order.get(r, 99) <= rank_order['A'])
        ]['umaban'].tolist()
        fukusho_horses = fukusho_horses[:strategy_config['max_horses_fukusho']]
        for h in fukusho_horses:
            race_bets['fukusho'].append({'umaban': h})
        
        # 馬連: Bランク以上
        umaren_horses = race_df[
            race_df['rank'].apply(lambda r: rank_order.get(r, 99) <= rank_order['B'])
        ]['umaban'].tolist()
        umaren_horses = umaren_horses[:strategy_config['max_horses_umaren']]
        for i, h1 in enumerate(umaren_horses):
            for h2 in umaren_horses[i+1:]:
                if h1 != h2:
                    race_bets['umaren'].append({'kumiban': (h1, h2)})
        
        # 🔥 Plan A: ワイド - Sランクのみ（軸馬+1頭まで）
        wide_horses = race_df[race_df['rank'] == 'S']['umaban'].tolist()
        wide_horses = wide_horses[:strategy_config['max_horses_wide']]
        for i, h1 in enumerate(wide_horses):
            for h2 in wide_horses[i+1:]:
                if h1 != h2:
                    race_bets['wide'].append({'kumiban': (h1, h2)})
        
        # 🔥 Plan C: 馬単 - Aランク以上（軸馬+1頭まで）
        umatan_horses = race_df[
            race_df['rank'].apply(lambda r: rank_order.get(r, 99) <= rank_order['A'])
        ]['umaban'].tolist()
        umatan_horses = umatan_horses[:strategy_config['max_horses_umatan']]
        for h1 in umatan_horses:
            for h2 in umatan_horses:
                if h1 != h2:
                    race_bets['umatan'].append({'kumiban': (h1, h2)})
        
        # 三連複: Zスコア1.0以上（偏差値60以上）
        sanrenpuku_horses = race_df[
            race_df['z_score'] >= strategy_config['sanrenpuku_min_z_score']
        ]['umaban'].tolist()
        sanrenpuku_horses = sanrenpuku_horses[:strategy_config['max_horses_sanrenpuku']]
        if len(sanrenpuku_horses) >= 3:
            for i, h1 in enumerate(sanrenpuku_horses):
                for j, h2 in enumerate(sanrenpuku_horses[i+1:], start=i+1):
                    for h3 in sanrenpuku_horses[j+1:]:
                        race_bets['sanrenpuku'].append({'kumiban': (h1, h2, h3)})
        
        # 🔥 Plan B: 三連単 - Zスコア1.5以上（偏差値65以上）に緩和
        sanrentan_horses = race_df[
            race_df['z_score'] >= strategy_config['sanrentan_min_z_score']
        ]['umaban'].tolist()
        sanrentan_horses = sanrentan_horses[:strategy_config['max_horses_sanrentan']]
        if len(sanrentan_horses) >= 3:
            for h1 in sanrentan_horses:
                for h2 in sanrentan_horses:
                    if h2 != h1:
                        for h3 in sanrentan_horses:
                            if h3 != h1 and h3 != h2:
                                race_bets['sanrentan'].append({'kumiban': (h1, h2, h3)})
        
        bets[race_key] = race_bets
    
    # 統計情報を出力
    total_races = len(bets)
    total_bets = {
        'tansho': sum(len(b['tansho']) for b in bets.values()),
        'fukusho': sum(len(b['fukusho']) for b in bets.values()),
        'umaren': sum(len(b['umaren']) for b in bets.values()),
        'wide': sum(len(b['wide']) for b in bets.values()),
        'umatan': sum(len(b['umatan']) for b in bets.values()),
        'sanrenpuku': sum(len(b['sanrenpuku']) for b in bets.values()),
        'sanrentan': sum(len(b['sanrentan']) for b in bets.values())
    }
    
    print(f"\n✅ 買い目生成完了:")
    print(f"   📊 対象レース: {total_races}レース")
    print(f"   🎫 券種別買い目数:")
    print(f"      - 単勝: {total_bets['tansho']}点")
    print(f"      - 複勝: {total_bets['fukusho']}点")
    print(f"      - 馬連: {total_bets['umaren']}点")
    print(f"      - ワイド: {total_bets['wide']}点 🔥 Plan A適用")
    print(f"      - 馬単: {total_bets['umatan']}点 🔥 Plan C適用")
    print(f"      - 三連複: {total_bets['sanrenpuku']}点")
    print(f"      - 三連単: {total_bets['sanrentan']}点 🔥 Plan B適用")
    print("\n   🎯 改善内容:")
    print("      - Plan A: ワイドをSランクのみに厳格化（最大2点/レース）")
    print("      - Plan B: 三連単の基準緩和（Zスコア2.0 → 1.5）")
    print("      - Plan C: 馬単を軸馬+1頭に削減（最大2点/レース）")
    
    return bets, strategy_config


def evaluate_backtest(bets: Dict, payouts_df: pd.DataFrame, strategy_config: Dict) -> Dict:
    """バックテスト評価"""
    print("\n" + "="*80)
    print("📈 バックテスト評価中...")
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
    
    # race_keyで辞書化
    payouts_dict = {row['race_key']: row for _, row in payouts_df.iterrows()}
    
    matched_races = 0
    
    for race_key, race_bets in bets.items():
        if race_key not in payouts_dict:
            continue
        
        matched_races += 1
        payout = payouts_dict[race_key]
        
        # 単勝
        tansho_umaban = parse_haraimodoshi(payout.get('tansho_umaban', 0))
        tansho_payout = parse_haraimodoshi(payout.get('tansho_haraimodoshi', 0))
        
        for bet in race_bets['tansho']:
            results['tansho']['total'] += 1
            results['tansho']['cost'] += unit_bet
            if bet['umaban'] == tansho_umaban:
                results['tansho']['hit'] += 1
                results['tansho']['return'] += tansho_payout
        
        # 複勝
        fukusho_winners = []
        for i in range(1, 6):
            umaban = parse_haraimodoshi(payout.get(f'fukusho_{i}_umaban', 0))
            haraimodoshi = parse_haraimodoshi(payout.get(f'fukusho_{i}_haraimodoshi', 0))
            if umaban > 0 and haraimodoshi > 0:
                fukusho_winners.append((umaban, haraimodoshi))
        
        for bet in race_bets['fukusho']:
            results['fukusho']['total'] += 1
            results['fukusho']['cost'] += unit_bet
            for umaban, haraimodoshi in fukusho_winners:
                if bet['umaban'] == umaban:
                    results['fukusho']['hit'] += 1
                    results['fukusho']['return'] += haraimodoshi
                    break
        
        # 馬連
        umaren_kumiban = parse_kumiban(payout.get('umaren_kumiban', ''))
        umaren_payout = parse_haraimodoshi(payout.get('umaren_haraimodoshi', 0))
        
        for bet in race_bets['umaren']:
            results['umaren']['total'] += 1
            results['umaren']['cost'] += unit_bet
            if umaren_kumiban and set(bet['kumiban']) == set(umaren_kumiban):
                results['umaren']['hit'] += 1
                results['umaren']['return'] += umaren_payout
        
        # ワイド
        wide_winners = []
        for i in range(1, 8):
            kumiban = parse_kumiban(payout.get(f'wide_{i}_kumiban', ''))
            haraimodoshi = parse_haraimodoshi(payout.get(f'wide_{i}_haraimodoshi', 0))
            if kumiban and haraimodoshi > 0:
                wide_winners.append((kumiban, haraimodoshi))
        
        for bet in race_bets['wide']:
            results['wide']['total'] += 1
            results['wide']['cost'] += unit_bet
            for kumiban, haraimodoshi in wide_winners:
                if set(bet['kumiban']) == set(kumiban):
                    results['wide']['hit'] += 1
                    results['wide']['return'] += haraimodoshi
                    break
        
        # 馬単
        umatan_kumiban = parse_kumiban(payout.get('umatan_kumiban', ''))
        umatan_payout = parse_haraimodoshi(payout.get('umatan_haraimodoshi', 0))
        
        for bet in race_bets['umatan']:
            results['umatan']['total'] += 1
            results['umatan']['cost'] += unit_bet
            if umatan_kumiban and bet['kumiban'] == umatan_kumiban:
                results['umatan']['hit'] += 1
                results['umatan']['return'] += umatan_payout
        
        # 三連複
        sanrenpuku_kumiban = parse_kumiban(payout.get('sanrenpuku_kumiban', ''))
        sanrenpuku_payout = parse_haraimodoshi(payout.get('sanrenpuku_haraimodoshi', 0))
        
        for bet in race_bets['sanrenpuku']:
            results['sanrenpuku']['total'] += 1
            results['sanrenpuku']['cost'] += unit_bet
            if sanrenpuku_kumiban and set(bet['kumiban']) == set(sanrenpuku_kumiban):
                results['sanrenpuku']['hit'] += 1
                results['sanrenpuku']['return'] += sanrenpuku_payout
        
        # 三連単
        sanrentan_kumiban = parse_kumiban(payout.get('sanrentan_kumiban', ''))
        sanrentan_payout = parse_haraimodoshi(payout.get('sanrentan_haraimodoshi', 0))
        
        for bet in race_bets['sanrentan']:
            results['sanrentan']['total'] += 1
            results['sanrentan']['cost'] += unit_bet
            if sanrentan_kumiban and bet['kumiban'] == sanrentan_kumiban:
                results['sanrentan']['hit'] += 1
                results['sanrentan']['return'] += sanrentan_payout
    
    print(f"\n✅ マッチしたレース: {matched_races}/{len(bets)}")
    
    return results, matched_races


def main():
    """メイン関数"""
    print("\n" + "="*80)
    print("🚀 Phase 5.5: Plan C（A+B両方実行）バックテスト")
    print("="*80)
    print("🎯 改善内容:")
    print("   - Plan A: ワイドをSランクのみに厳格化")
    print("   - Plan B: 三連単の基準緩和（Zスコア2.0 → 1.5）")
    print("   - Plan C: 馬単を軸馬+1頭に削減")
    print("="*80)
    
    # ファイルパス
    ensemble_path = Path('/home/user/webapp/predictions/phase5_ooi_2025/ooi_2025_phase5_ensemble.csv')
    payouts_path = Path('/home/user/uploaded_files/ooi_2025_payouts_full.csv')
    output_dir = Path('/home/user/webapp/predictions/phase5_5_ooi_2025_plan_c')
    
    # 出力ディレクトリ作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # データ確認
    print(f"\n📁 Phase 5 アンサンブル: {ensemble_path}")
    print(f"   存在確認: {'✅' if ensemble_path.exists() else '❌'}")
    print(f"\n📁 実払戻金CSV: {payouts_path}")
    print(f"   存在確認: {'✅' if payouts_path.exists() else '❌'}")
    
    # Phase 5 アンサンブルを読み込み
    print("\n" + "="*80)
    print("📊 Phase 5 アンサンブルを読み込み中...")
    print("="*80)
    ensemble_df = pd.read_csv(ensemble_path)
    print(f"✅ データ件数: {len(ensemble_df):,}件")
    
    # 払戻金CSVを読み込み
    payouts_df = load_payouts_csv(str(payouts_path))
    
    # Plan C: A+B両方実行の買い目生成
    bets, strategy_config = generate_betting_strategy_plan_c(ensemble_df)
    
    # バックテスト評価
    results, matched_races = evaluate_backtest(bets, payouts_df, strategy_config)
    
    # 結果表示
    print("\n" + "="*80)
    print("📊 Phase 5.5: Plan C（A+B両方実行）バックテスト結果")
    print("="*80)
    print(f"🗓️  実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print(f"🎯 対象レース数: {matched_races}")
    print("="*80)
    
    total_cost = 0
    total_return = 0
    total_bets_count = 0
    total_hit_count = 0
    
    for ticket_type, data in results.items():
        total_bets_count += data['total']
        total_hit_count += data['hit']
        total_cost += data['cost']
        total_return += data['return']
        
        hit_rate = (data['hit'] / data['total'] * 100) if data['total'] > 0 else 0
        recovery_rate = (data['return'] / data['cost'] * 100) if data['cost'] > 0 else 0
        profit = data['return'] - data['cost']
        
        type_names = {
            'tansho': '単勝',
            'fukusho': '複勝',
            'umaren': '馬連',
            'wide': 'ワイド',
            'umatan': '馬単',
            'sanrenpuku': '三連複',
            'sanrentan': '三連単'
        }
        
        marker = ''
        if ticket_type == 'wide':
            marker = ' 🔥 Plan A'
        elif ticket_type == 'umatan':
            marker = ' 🔥 Plan C'
        elif ticket_type == 'sanrentan':
            marker = ' 🔥 Plan B'
        
        print(f"\n【{type_names[ticket_type]}】{marker}")
        print(f"  購入点数: {data['total']}点")
        print(f"  的中: {data['hit']}点 ({hit_rate:.2f}%)")
        print(f"  購入額: {data['cost']:,}円")
        print(f"  払戻額: {data['return']:,}円")
        print(f"  回収率: {recovery_rate:.2f}%")
        print(f"  収支: {profit:+,}円")
    
    # 合計
    total_hit_rate = (total_hit_count / total_bets_count * 100) if total_bets_count > 0 else 0
    total_recovery_rate = (total_return / total_cost * 100) if total_cost > 0 else 0
    total_profit = total_return - total_cost
    
    print("\n" + "="*80)
    print("【合計】")
    print("="*80)
    print(f"  総購入点数: {total_bets_count}点")
    print(f"  総的中: {total_hit_count}点 ({total_hit_rate:.2f}%)")
    print(f"  総購入額: {total_cost:,}円")
    print(f"  総払戻額: {total_return:,}円")
    print(f"  総回収率: {total_recovery_rate:.2f}%")
    print(f"  総収支: {total_profit:+,}円")
    
    # 目標達成度
    print("\n" + "="*80)
    print("🎯 目標達成度")
    print("="*80)
    target_hit_rate = 30.0
    target_recovery_rate = 80.0
    print(f"  目標的中率: {target_hit_rate}% → 実績: {total_hit_rate:.2f}% {'✅ 達成' if total_hit_rate >= target_hit_rate else '❌ 未達'}")
    print(f"  目標回収率: {target_recovery_rate}% → 実績: {total_recovery_rate:.2f}% {'✅ 達成' if total_recovery_rate >= target_recovery_rate else '❌ 未達'}")
    
    # JSON保存
    output_json = {
        'summary': {
            'total_bets': total_bets_count,
            'total_hit': total_hit_count,
            'total_hit_rate': total_hit_rate,
            'total_cost': total_cost,
            'total_return': total_return,
            'total_recovery_rate': total_recovery_rate,
            'total_profit': total_profit,
            'details': results
        },
        'strategy': strategy_config,
        'matched_races': matched_races,
        'improvements': {
            'plan_a': 'ワイドをSランクのみに厳格化（最大2点/レース）',
            'plan_b': '三連単の基準緩和（Zスコア2.0 → 1.5）',
            'plan_c': '馬単を軸馬+1頭に削減（最大2点/レース）'
        }
    }
    
    output_file = output_dir / 'backtest_results_plan_c.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 結果を保存しました: {output_file}")
    print("\n" + "="*80)
    print("✅ Phase 5.5: Plan C（A+B両方実行）バックテスト完了！")
    print("="*80)


if __name__ == '__main__':
    main()
