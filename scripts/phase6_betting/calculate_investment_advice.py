#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: 投資判断アドバイス計算スクリプト
投資競馬最適化版 - 改良案B（Binary強化型）対応

目的:
    アンサンブル結果（Phase 5）から投資判断を行い、
    期待値・損益分岐オッズ・推奨購入額を計算

入力:
    ensemble_csv: Phase 5アンサンブル結果CSV
    bankroll: 投資可能資金（デフォルト: 100,000円）

出力:
    投資判断アドバイス付きCSV
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class InvestmentAdvisor:
    """投資判断アドバイザー"""
    
    def __init__(self, bankroll=100000):
        """
        Args:
            bankroll: 投資可能資金（円）
        """
        self.bankroll = bankroll
        self.max_race_pct = 0.10  # 1レース最大投資率10%
        self.max_daily_pct = 0.50  # 1日最大投資率50%
        
        # 馬券種別の推奨投資率
        self.bet_pcts = {
            '複勝': 0.05,    # 5%
            '馬連': 0.02,    # 2%
            'ワイド': 0.015,  # 1.5%
            '三連複': 0.01   # 1%（1点あたり）
        }
    
    def calculate_breakeven_odds(self, win_prob):
        """
        損益分岐オッズ計算
        
        Args:
            win_prob: 的中確率
        
        Returns:
            float: 損益分岐オッズ
        """
        if win_prob <= 0:
            return 999.0
        return 1.0 / win_prob
    
    def calculate_expected_value(self, win_prob, odds):
        """
        期待値計算
        
        Args:
            win_prob: 的中確率
            odds: オッズ
        
        Returns:
            float: 期待値
        """
        return (win_prob * odds) - 1.0
    
    def select_fukusho_candidates(self, df_race):
        """
        複勝候補を選択
        
        条件:
            - ensemble_score >= 0.50
            - binary_probability >= 0.50
            - final_rank <= 5
        
        Args:
            df_race: レースデータ（1レース分）
        
        Returns:
            pd.DataFrame: 複勝候補
        """
        candidates = df_race[
            (df_race['ensemble_score'] >= 0.50) &
            (df_race['binary_probability'] >= 0.50) &
            (df_race['final_rank'] <= 5)
        ].copy()
        
        return candidates.sort_values('ensemble_score', ascending=False)
    
    def select_umaren_wide_candidates(self, df_race):
        """
        馬連・ワイド候補を選択
        
        条件:
            - ensemble_score >= 0.50
            - final_rank <= 5
        
        Args:
            df_race: レースデータ（1レース分）
        
        Returns:
            list: 候補馬番リスト（上位2頭）
        """
        candidates = df_race[
            (df_race['ensemble_score'] >= 0.50) &
            (df_race['final_rank'] <= 5)
        ].sort_values('ensemble_score', ascending=False)
        
        if len(candidates) >= 2:
            return candidates.head(2)['umaban'].tolist()
        return []
    
    def select_sanrenpuku_candidates(self, df_race):
        """
        三連複候補を選択
        
        条件:
            - ensemble_score >= 0.50
            - final_rank <= 7
        
        Args:
            df_race: レースデータ（1レース分）
        
        Returns:
            list: 候補馬番リスト（上位3-6頭）
        """
        candidates = df_race[
            (df_race['ensemble_score'] >= 0.50) &
            (df_race['final_rank'] <= 7)
        ].sort_values('ensemble_score', ascending=False)
        
        if len(candidates) >= 3:
            # 3-6頭を返す（最大6頭まで）
            return candidates.head(6)['umaban'].tolist()
        return []
    
    def calculate_fukusho_advice(self, df_race):
        """
        複勝推奨を計算
        
        Args:
            df_race: レースデータ（1レース分）
        
        Returns:
            dict: 複勝推奨アドバイス
        """
        candidates = self.select_fukusho_candidates(df_race)
        
        if len(candidates) == 0:
            return None
        
        # 本命（スコア最高）
        honmei = candidates.iloc[0]
        
        # 的中確率 = binary_probability（3着以内確率）
        win_prob = honmei['binary_probability']
        
        # 損益分岐オッズ
        breakeven_odds = self.calculate_breakeven_odds(win_prob)
        
        # 推奨購入額
        bet_amount = int(self.bankroll * self.bet_pcts['複勝'])
        
        advice = {
            'betting_type': '複勝',
            'umaban': int(honmei['umaban']),
            'ensemble_score': honmei['ensemble_score'],
            'binary_probability': win_prob,
            'breakeven_odds': breakeven_odds,
            'bet_amount': bet_amount,
            'bet_pct': self.bet_pcts['複勝'] * 100
        }
        
        return advice
    
    def calculate_umaren_advice(self, df_race):
        """
        馬連推奨を計算
        
        Args:
            df_race: レースデータ（1レース分）
        
        Returns:
            dict: 馬連推奨アドバイス
        """
        horses = self.select_umaren_wide_candidates(df_race)
        
        if len(horses) < 2:
            return None
        
        # 馬連的中確率（簡易計算）
        # P(1着 or 2着) × P(もう1頭が1着 or 2着)
        top2 = df_race[df_race['umaban'].isin(horses)].sort_values('ensemble_score', ascending=False)
        prob1 = top2.iloc[0]['binary_probability']
        prob2 = top2.iloc[1]['binary_probability']
        
        # 馬連的中確率 ≈ prob1 × prob2
        win_prob = prob1 * prob2
        
        # 損益分岐オッズ
        breakeven_odds = self.calculate_breakeven_odds(win_prob)
        
        # 推奨購入額
        bet_amount = int(self.bankroll * self.bet_pcts['馬連'])
        
        advice = {
            'betting_type': '馬連',
            'horses': f"{horses[0]}-{horses[1]}",
            'win_probability': win_prob,
            'breakeven_odds': breakeven_odds,
            'bet_amount': bet_amount,
            'bet_pct': self.bet_pcts['馬連'] * 100
        }
        
        return advice
    
    def calculate_wide_advice(self, df_race):
        """
        ワイド推奨を計算
        
        Args:
            df_race: レースデータ（1レース分）
        
        Returns:
            dict: ワイド推奨アドバイス
        """
        horses = self.select_umaren_wide_candidates(df_race)
        
        if len(horses) < 2:
            return None
        
        # ワイド的中確率（3着以内2頭が含まれる確率）
        top2 = df_race[df_race['umaban'].isin(horses)].sort_values('ensemble_score', ascending=False)
        prob1 = top2.iloc[0]['binary_probability']
        prob2 = top2.iloc[1]['binary_probability']
        
        # ワイド的中確率 ≈ prob1 × prob2 × 1.2（補正係数）
        win_prob = min(prob1 * prob2 * 1.2, 0.95)
        
        # 損益分岐オッズ
        breakeven_odds = self.calculate_breakeven_odds(win_prob)
        
        # 推奨購入額
        bet_amount = int(self.bankroll * self.bet_pcts['ワイド'])
        
        advice = {
            'betting_type': 'ワイド',
            'horses': f"{horses[0]}-{horses[1]}",
            'win_probability': win_prob,
            'breakeven_odds': breakeven_odds,
            'bet_amount': bet_amount,
            'bet_pct': self.bet_pcts['ワイド'] * 100
        }
        
        return advice
    
    def calculate_sanrenpuku_advice(self, df_race):
        """
        三連複推奨を計算
        
        Args:
            df_race: レースデータ（1レース分）
        
        Returns:
            list: 三連複推奨アドバイスリスト
        """
        horses = self.select_sanrenpuku_candidates(df_race)
        
        if len(horses) < 3:
            return []
        
        from itertools import combinations
        
        # 3頭組み合わせを生成
        combos = list(combinations(horses, 3))
        
        # 最大5点まで
        combos = combos[:5]
        
        advices = []
        
        for combo in combos:
            # 三連複的中確率（簡易計算）
            top3 = df_race[df_race['umaban'].isin(combo)].sort_values('ensemble_score', ascending=False)
            
            if len(top3) < 3:
                continue
            
            prob1 = top3.iloc[0]['binary_probability']
            prob2 = top3.iloc[1]['binary_probability']
            prob3 = top3.iloc[2]['binary_probability']
            
            # 三連複的中確率 ≈ (prob1 × prob2 × prob3) ^ (1/3)
            win_prob = (prob1 * prob2 * prob3) ** (1.0 / 3.0)
            
            # 損益分岐オッズ
            breakeven_odds = self.calculate_breakeven_odds(win_prob)
            
            # 推奨購入額（1点あたり）
            bet_amount = int(self.bankroll * self.bet_pcts['三連複'])
            
            advice = {
                'betting_type': '三連複',
                'horses': f"{combo[0]}-{combo[1]}-{combo[2]}",
                'win_probability': win_prob,
                'breakeven_odds': breakeven_odds,
                'bet_amount': bet_amount,
                'bet_pct': self.bet_pcts['三連複'] * 100,
                'combo_index': len(advices) + 1,
                'total_combos': len(combos)
            }
            
            advices.append(advice)
        
        return advices
    
    def generate_advice_for_race(self, df_race):
        """
        レースごとの投資判断アドバイスを生成
        
        Args:
            df_race: レースデータ（1レース分）
        
        Returns:
            list: アドバイスリスト
        """
        advices = []
        
        # 複勝
        fukusho = self.calculate_fukusho_advice(df_race)
        if fukusho:
            advices.append(fukusho)
        
        # 馬連
        umaren = self.calculate_umaren_advice(df_race)
        if umaren:
            advices.append(umaren)
        
        # ワイド
        wide = self.calculate_wide_advice(df_race)
        if wide:
            advices.append(wide)
        
        # 三連複
        sanrenpuku_list = self.calculate_sanrenpuku_advice(df_race)
        advices.extend(sanrenpuku_list)
        
        return advices
    
    def process_ensemble_csv(self, ensemble_csv):
        """
        アンサンブルCSVを処理して投資判断を生成
        
        Args:
            ensemble_csv: Phase 5アンサンブル結果CSV
        
        Returns:
            pd.DataFrame: 投資判断付きDataFrame
        """
        # CSV読み込み
        try:
            df = pd.read_csv(ensemble_csv, encoding='shift-jis')
        except:
            df = pd.read_csv(ensemble_csv, encoding='utf-8')
        
        print(f"\n{'='*80}")
        print(f"Phase 6: 投資判断アドバイス計算")
        print(f"{'='*80}")
        print(f"投資可能資金: {self.bankroll:,}円")
        print(f"レース数: {df['race_id'].nunique()}件")
        print(f"")
        
        all_advices = []
        
        # レースごとに処理
        for race_id in sorted(df['race_id'].unique()):
            df_race = df[df['race_id'] == race_id].copy()
            
            advices = self.generate_advice_for_race(df_race)
            
            for advice in advices:
                advice['race_id'] = race_id
                advice['keibajo_code'] = df_race.iloc[0]['keibajo_code']
                advice['race_bango'] = df_race.iloc[0]['race_bango']
                advice['kaisai_nen'] = df_race.iloc[0]['kaisai_nen']
                advice['kaisai_tsukihi'] = df_race.iloc[0]['kaisai_tsukihi']
                all_advices.append(advice)
        
        df_advices = pd.DataFrame(all_advices)
        
        print(f"✅ 投資判断アドバイス生成完了")
        print(f"  - 推奨購入数: {len(df_advices)}点")
        print(f"  - 合計投資額: {df_advices['bet_amount'].sum():,}円")
        print(f"")
        
        return df_advices


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用法: python calculate_investment_advice.py <ensemble_csv> [<bankroll>]")
        print("")
        print("例:")
        print("  python calculate_investment_advice.py \\")
        print("         data/predictions/phase5/浦和_20260423_ensemble.csv 100000")
        sys.exit(1)
    
    ensemble_csv = sys.argv[1]
    bankroll = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
    
    # 入力ファイルの存在確認
    if not Path(ensemble_csv).exists():
        print(f"❌ エラー: 入力ファイルが見つかりません: {ensemble_csv}")
        sys.exit(1)
    
    # アドバイザー初期化
    advisor = InvestmentAdvisor(bankroll=bankroll)
    
    # 投資判断生成
    df_advices = advisor.process_ensemble_csv(ensemble_csv)
    
    # 出力ファイル名
    output_csv = ensemble_csv.replace('_ensemble.csv', '_investment_advice.csv')
    
    # 保存
    output_dir = os.path.dirname(output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        df_advices.to_csv(output_csv, index=False, encoding='shift-jis')
        print(f"✅ 投資判断アドバイス保存完了（Shift-JIS）: {output_csv}")
    except:
        output_csv_utf8 = output_csv.replace('.csv', '_utf8.csv')
        df_advices.to_csv(output_csv_utf8, index=False, encoding='utf-8')
        print(f"✅ 投資判断アドバイス保存完了（UTF-8）: {output_csv_utf8}")


if __name__ == "__main__":
    main()
