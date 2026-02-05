#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtesting_engine.py
Phase 5: バックテスト・回収率評価エンジン

買い目の回収率をシミュレーション評価
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime


class BacktestingEngine:
    """バックテスト・回収率評価エンジン"""
    
    def __init__(
        self,
        unit_bet: int = 100,  # 1点あたりの賭け金
        max_bet_per_race: int = 10  # 1レースあたりの最大購入点数
    ):
        """
        初期化
        
        Args:
            unit_bet: 1点あたりの賭け金
            max_bet_per_race: 1レースあたりの最大購入点数
        """
        self.unit_bet = unit_bet
        self.max_bet_per_race = max_bet_per_race
    
    def load_test_data(self, test_csv_path: str) -> pd.DataFrame:
        """
        テストデータを読み込み（実際の着順付き）
        
        Args:
            test_csv_path: テストデータのパス
        
        Returns:
            テストデータフレーム
        """
        print("\n📂 テストデータの読み込み...")
        df = pd.read_csv(test_csv_path)
        print(f"  ✅ 読み込み完了: {len(df)}件")
        
        # target カラムがあれば実際の着順として使用
        if 'target' in df.columns:
            df['actual_rank'] = df['target']
        elif 'kakutei_chakujun' in df.columns:
            df['actual_rank'] = df['kakutei_chakujun']
        else:
            print("  ⚠️  警告: 実際の着順データが見つかりません")
            df['actual_rank'] = np.nan
        
        return df
    
    def load_bets(self, bets_json_path: str) -> Dict:
        """
        買い目JSONを読み込み
        
        Args:
            bets_json_path: 買い目JSONのパス
        
        Returns:
            買い目データ
        """
        print("\n📂 買い目の読み込み...")
        with open(bets_json_path, 'r', encoding='utf-8') as f:
            bets_data = json.load(f)
        print(f"  ✅ 読み込み完了: {bets_data['total_races']}レース")
        return bets_data
    
    def simulate_tansho(
        self,
        bet: Dict,
        race_df: pd.DataFrame,
        odds: float = 3.0  # 仮の平均オッズ
    ) -> Tuple[int, int, bool]:
        """
        単勝のシミュレーション
        
        Args:
            bet: 単勝の買い目
            race_df: レースのデータフレーム
            odds: オッズ（仮）
        
        Returns:
            (投資額, 払戻額, 的中フラグ)
        """
        umaban = bet['umaban']
        investment = self.unit_bet
        
        # 実際の1着を取得
        winner = race_df[race_df['actual_rank'] == 1]
        if len(winner) == 0:
            return investment, 0, False
        
        winner_umaban = int(winner.iloc[0].get('umaban', -1))
        
        if winner_umaban == umaban:
            payout = int(investment * odds)
            return investment, payout, True
        else:
            return investment, 0, False
    
    def simulate_umaren(
        self,
        bet: Dict,
        race_df: pd.DataFrame,
        odds: float = 10.0  # 仮の平均オッズ
    ) -> Tuple[int, int, bool]:
        """
        馬連のシミュレーション
        
        Args:
            bet: 馬連の買い目
            race_df: レースのデータフレーム
            odds: オッズ（仮）
        
        Returns:
            (投資額, 払戻額, 的中フラグ)
        """
        horses = bet['horses']
        investment = self.unit_bet
        
        # 実際の1-2着を取得
        top2 = race_df[race_df['actual_rank'].isin([1, 2])]
        if len(top2) < 2:
            return investment, 0, False
        
        top2_umaban = set(int(h.get('umaban', -1)) for _, h in top2.iterrows())
        bet_horses = set(horses)
        
        if bet_horses == top2_umaban:
            payout = int(investment * odds)
            return investment, payout, True
        else:
            return investment, 0, False
    
    def simulate_wide(
        self,
        bet: Dict,
        race_df: pd.DataFrame,
        odds: float = 5.0  # 仮の平均オッズ
    ) -> Tuple[int, int, bool]:
        """
        ワイドのシミュレーション
        
        Args:
            bet: ワイドの買い目
            race_df: レースのデータフレーム
            odds: オッズ（仮）
        
        Returns:
            (投資額, 払戻額, 的中フラグ)
        """
        horses = bet['horses']
        investment = self.unit_bet
        
        # 実際の1-3着を取得
        top3 = race_df[race_df['actual_rank'].isin([1, 2, 3])]
        if len(top3) < 3:
            return investment, 0, False
        
        top3_umaban = set(int(h.get('umaban', -1)) for _, h in top3.iterrows())
        bet_horses = set(horses)
        
        # 2頭とも3着以内なら的中
        if bet_horses.issubset(top3_umaban):
            payout = int(investment * odds)
            return investment, payout, True
        else:
            return investment, 0, False
    
    def simulate_sanrenpuku(
        self,
        bet: Dict,
        race_df: pd.DataFrame,
        odds: float = 30.0  # 仮の平均オッズ
    ) -> Tuple[int, int, bool]:
        """
        三連複のシミュレーション
        
        Args:
            bet: 三連複の買い目
            race_df: レースのデータフレーム
            odds: オッズ（仮）
        
        Returns:
            (投資額, 払戻額, 的中フラグ)
        """
        horses = bet['horses']
        investment = self.unit_bet
        
        # 実際の1-3着を取得
        top3 = race_df[race_df['actual_rank'].isin([1, 2, 3])]
        if len(top3) < 3:
            return investment, 0, False
        
        top3_umaban = set(int(h.get('umaban', -1)) for _, h in top3.iterrows())
        bet_horses = set(horses)
        
        if bet_horses == top3_umaban:
            payout = int(investment * odds)
            return investment, payout, True
        else:
            return investment, 0, False
    
    def run_backtest(
        self,
        bets_data: Dict,
        test_df: pd.DataFrame
    ) -> Dict:
        """
        バックテストを実行
        
        Args:
            bets_data: 買い目データ
            test_df: テストデータ
        
        Returns:
            バックテスト結果
        """
        print("\n🔄 バックテスト実行中...")
        
        results = {
            'total_investment': 0,
            'total_payout': 0,
            'total_profit': 0,
            'recovery_rate': 0.0,
            'hit_count': 0,
            'total_bets': 0,
            'hit_rate': 0.0,
            'by_bet_type': {
                'tansho': {'investment': 0, 'payout': 0, 'hits': 0, 'total': 0},
                'umaren': {'investment': 0, 'payout': 0, 'hits': 0, 'total': 0},
                'wide': {'investment': 0, 'payout': 0, 'hits': 0, 'total': 0},
                'sanrenpuku': {'investment': 0, 'payout': 0, 'hits': 0, 'total': 0}
            },
            'race_results': []
        }
        
        for race_bets in bets_data['races']:
            race_id = race_bets['race_id']
            race_info = race_bets['race_info']
            
            # レースデータを取得
            race_df = test_df[
                (test_df['kaisai_nen'] == race_info['kaisai_nen']) &
                (test_df['kaisai_tsukihi'] == race_info['kaisai_tsukihi']) &
                (test_df['keibajo_code'] == race_info['keibajo_code']) &
                (test_df['race_bango'] == race_info['race_bango'])
            ]
            
            if len(race_df) == 0:
                continue
            
            race_result = {
                'race_id': race_id,
                'investment': 0,
                'payout': 0,
                'profit': 0,
                'hits': []
            }
            
            # 単勝
            for bet in race_bets['bets']['tansho']:
                inv, pay, hit = self.simulate_tansho(bet, race_df)
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
                inv, pay, hit = self.simulate_umaren(bet, race_df)
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
                inv, pay, hit = self.simulate_wide(bet, race_df)
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
                inv, pay, hit = self.simulate_sanrenpuku(bet, race_df)
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
        
        # 券種別の回収率計算
        for bet_type in results['by_bet_type']:
            bt = results['by_bet_type'][bet_type]
            if bt['investment'] > 0:
                bt['recovery_rate'] = (bt['payout'] / bt['investment']) * 100
            else:
                bt['recovery_rate'] = 0.0
            if bt['total'] > 0:
                bt['hit_rate'] = (bt['hits'] / bt['total']) * 100
            else:
                bt['hit_rate'] = 0.0
        
        print(f"  ✅ バックテスト完了")
        print(f"     - 総投資額: {results['total_investment']:,}円")
        print(f"     - 総払戻額: {results['total_payout']:,}円")
        print(f"     - 収支: {results['total_profit']:+,}円")
        print(f"     - 回収率: {results['recovery_rate']:.2f}%")
        print(f"     - 的中率: {results['hit_rate']:.2f}%")
        
        return results
    
    def save_results(self, results: Dict, output_path: str):
        """
        バックテスト結果を保存
        
        Args:
            results: バックテスト結果
            output_path: 出力先パス
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
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
        
        print(f"\n💾 バックテスト結果を保存: {output_path}")
    
    def evaluate(
        self,
        bets_json_path: str,
        test_csv_path: str,
        output_path: str
    ) -> Dict:
        """
        バックテスト評価のメイン処理
        
        Args:
            bets_json_path: 買い目JSONのパス
            test_csv_path: テストデータのパス
            output_path: 出力先パス
        
        Returns:
            バックテスト結果
        """
        print("\n" + "="*60)
        print("📊 Phase 5: バックテスト評価開始")
        print("="*60)
        
        # データ読み込み
        bets_data = self.load_bets(bets_json_path)
        test_df = self.load_test_data(test_csv_path)
        
        # バックテスト実行
        results = self.run_backtest(bets_data, test_df)
        
        # 結果保存
        self.save_results(results, output_path)
        
        print("\n✅ Phase 5 バックテスト評価完了！")
        print("="*60)
        
        return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 4:
        print("使用法: python backtesting_engine.py <bets_json> <test_csv> <output>")
        print("例: python backtesting_engine.py predictions/phase5_ooi_test/ooi_test_bets.json csv/test_split/ooi_test.csv predictions/phase5_ooi_test/ooi_test_backtest.json")
        sys.exit(1)
    
    bets_json_path = sys.argv[1]
    test_csv_path = sys.argv[2]
    output_path = sys.argv[3]
    
    # バックテスト評価の実行
    engine = BacktestingEngine(unit_bet=100, max_bet_per_race=10)
    results = engine.evaluate(bets_json_path, test_csv_path, output_path)
