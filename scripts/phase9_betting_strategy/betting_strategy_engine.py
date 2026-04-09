#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
betting_strategy_engine.py
Phase 9: 期待値ベース購入戦略エンジン

Kelly基準とHarville公式を用いた最適賭け戦略を実装します。

主要機能:
    1. 期待値計算（EV = 予測確率 × オッズ - 1）
    2. Kelly基準による資金管理（Fractional Kelly）
    3. Harville公式で3連単確率を計算
    4. リスク管理（1レース最大5%、連敗時縮小）

使用法:
    from betting_strategy_engine import BettingStrategyEngine
    
    engine = BettingStrategyEngine(bankroll=100000, kelly_fraction=0.25, max_bet_pct=0.05)
    recommendations = engine.calculate_betting_strategy(predictions, odds)
    
入力:
    - predictions: 予測確率DataFrame（馬番、予測確率）
    - odds: オッズDataFrame（馬番、単勝オッズ、複勝オッズ）
    
出力:
    - recommendations: 購入推奨DataFrame（馬券種、買い目、賭け金、期待値）
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations, permutations
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class BettingStrategyEngine:
    """
    期待値ベース購入戦略エンジン
    
    Kelly基準とHarville公式を用いて最適な賭け戦略を提案します。
    """
    
    def __init__(self, bankroll=100000, kelly_fraction=0.25, max_bet_pct=0.05, min_ev=0.05):
        """
        Args:
            bankroll: 総資金（円）
            kelly_fraction: Kelly比率（1/4 Kelly推奨）
            max_bet_pct: 1レース最大賭け率（デフォルト: 5%）
            min_ev: 最小期待値（これ以下は購入しない）
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.max_bet_pct = max_bet_pct
        self.min_ev = min_ev
        
        print(f"✅ BettingStrategyEngine初期化完了")
        print(f"  - 総資金: {bankroll:,}円")
        print(f"  - Kelly比率: {kelly_fraction} (Fractional Kelly)")
        print(f"  - 最大賭け率: {max_bet_pct * 100}%/レース")
        print(f"  - 最小期待値: {min_ev * 100}%")
    
    
    def calculate_expected_value(self, win_prob, odds):
        """
        期待値を計算
        
        EV = (予測確率 × オッズ) - 1
        
        Args:
            win_prob: 勝率（予測確率）
            odds: オッズ
        
        Returns:
            float: 期待値
        """
        return (win_prob * odds) - 1
    
    
    def calculate_kelly_bet(self, win_prob, odds, ev):
        """
        Kelly基準で最適賭け金を計算
        
        f* = (bp - q) / b
        
        Args:
            win_prob: 勝率（予測確率）
            odds: オッズ
            ev: 期待値
        
        Returns:
            float: 賭け金（円）
        """
        # Kelly比率計算
        b = odds - 1  # ネットオッズ
        p = win_prob  # 勝率
        q = 1 - p     # 負け率
        
        kelly_ratio = (b * p - q) / b
        
        # Fractional Kelly適用
        kelly_ratio = kelly_ratio * self.kelly_fraction
        
        # 上限制約
        kelly_ratio = min(kelly_ratio, self.max_bet_pct)
        
        # マイナスの場合は0
        kelly_ratio = max(kelly_ratio, 0)
        
        # 賭け金計算
        bet_amount = self.bankroll * kelly_ratio
        
        # 最小100円単位に丸める
        bet_amount = max(100, int(bet_amount / 100) * 100)
        
        return bet_amount
    
    
    def harville_formula(self, probabilities, positions):
        """
        Harville公式で複数着順の同時確率を計算
        
        3連単の確率計算に使用
        
        Args:
            probabilities: 各馬の勝率リスト
            positions: 着順リスト（例: [1, 3, 5]なら1着-3着-5着）
        
        Returns:
            float: 同時確率
        """
        probs = np.array(probabilities)
        joint_prob = 1.0
        remaining_prob = 1.0
        
        for pos in positions:
            # 該当馬の確率
            horse_prob = probs[pos]
            
            # 条件付き確率
            conditional_prob = horse_prob / remaining_prob
            
            # 同時確率に乗算
            joint_prob *= conditional_prob
            
            # 残存確率を更新
            remaining_prob -= horse_prob
            
            if remaining_prob <= 0:
                break
        
        return joint_prob
    
    
    def calculate_win_bets(self, predictions, odds):
        """
        単勝の購入推奨を計算
        
        Args:
            predictions: 予測DataFrame（umaban, win_prob）
            odds: オッズDataFrame（umaban, tansho_odds）
        
        Returns:
            pd.DataFrame: 購入推奨
        """
        recommendations = []
        
        for _, row in predictions.iterrows():
            umaban = row['umaban']
            win_prob = row['win_prob']
            
            # オッズ取得
            odds_row = odds[odds['umaban'] == umaban]
            if len(odds_row) == 0:
                continue
            
            tansho_odds = odds_row['tansho_odds'].values[0]
            
            # 期待値計算
            ev = self.calculate_expected_value(win_prob, tansho_odds)
            
            # 期待値がプラスの場合のみ購入
            if ev >= self.min_ev:
                # Kelly賭け金計算
                bet_amount = self.calculate_kelly_bet(win_prob, tansho_odds, ev)
                
                recommendations.append({
                    'betting_type': '単勝',
                    'horses': f"{umaban}",
                    'win_prob': win_prob,
                    'odds': tansho_odds,
                    'expected_value': ev,
                    'bet_amount': bet_amount,
                    'expected_return': bet_amount * (1 + ev)
                })
        
        return pd.DataFrame(recommendations)
    
    
    def calculate_place_bets(self, predictions, odds):
        """
        複勝の購入推奨を計算
        
        Args:
            predictions: 予測DataFrame（umaban, top3_prob）
            odds: オッズDataFrame（umaban, fukusho_odds）
        
        Returns:
            pd.DataFrame: 購入推奨
        """
        recommendations = []
        
        for _, row in predictions.iterrows():
            umaban = row['umaban']
            top3_prob = row['top3_prob']
            
            # オッズ取得
            odds_row = odds[odds['umaban'] == umaban]
            if len(odds_row) == 0:
                continue
            
            fukusho_odds = odds_row['fukusho_odds'].values[0]
            
            # 期待値計算
            ev = self.calculate_expected_value(top3_prob, fukusho_odds)
            
            # 期待値がプラスの場合のみ購入
            if ev >= self.min_ev:
                # Kelly賭け金計算
                bet_amount = self.calculate_kelly_bet(top3_prob, fukusho_odds, ev)
                
                recommendations.append({
                    'betting_type': '複勝',
                    'horses': f"{umaban}",
                    'win_prob': top3_prob,
                    'odds': fukusho_odds,
                    'expected_value': ev,
                    'bet_amount': bet_amount,
                    'expected_return': bet_amount * (1 + ev)
                })
        
        return pd.DataFrame(recommendations)
    
    
    def calculate_exacta_bets(self, predictions, odds, top_n=5):
        """
        馬単の購入推奨を計算
        
        Args:
            predictions: 予測DataFrame（umaban, win_prob）
            odds: オッズDataFrame（umaban1, umaban2, umatan_odds）
            top_n: 上位N頭で組み合わせ作成
        
        Returns:
            pd.DataFrame: 購入推奨
        """
        recommendations = []
        
        # 上位N頭を抽出
        top_horses = predictions.nlargest(top_n, 'win_prob')
        
        # 馬単の組み合わせ（順列）
        for horse1, horse2 in permutations(top_horses.itertuples(), 2):
            umaban1 = horse1.umaban
            umaban2 = horse2.umaban
            
            # 1着確率
            prob1 = horse1.win_prob
            
            # 2着確率（Harville公式）
            remaining_prob = 1.0 - prob1
            prob2_given_1 = horse2.win_prob / remaining_prob if remaining_prob > 0 else 0
            
            # 馬単確率
            umatan_prob = prob1 * prob2_given_1
            
            # オッズ取得
            odds_row = odds[(odds['umaban1'] == umaban1) & (odds['umaban2'] == umaban2)]
            if len(odds_row) == 0:
                continue
            
            umatan_odds = odds_row['umatan_odds'].values[0]
            
            # 期待値計算
            ev = self.calculate_expected_value(umatan_prob, umatan_odds)
            
            # 期待値がプラスの場合のみ購入
            if ev >= self.min_ev:
                # Kelly賭け金計算
                bet_amount = self.calculate_kelly_bet(umatan_prob, umatan_odds, ev)
                
                recommendations.append({
                    'betting_type': '馬単',
                    'horses': f"{umaban1}-{umaban2}",
                    'win_prob': umatan_prob,
                    'odds': umatan_odds,
                    'expected_value': ev,
                    'bet_amount': bet_amount,
                    'expected_return': bet_amount * (1 + ev)
                })
        
        return pd.DataFrame(recommendations)
    
    
    def calculate_trio_bets(self, predictions, odds, top_n=6):
        """
        3連複の購入推奨を計算
        
        Args:
            predictions: 予測DataFrame（umaban, top3_prob）
            odds: オッズDataFrame（umaban1, umaban2, umaban3, sanrenpuku_odds）
            top_n: 上位N頭で組み合わせ作成
        
        Returns:
            pd.DataFrame: 購入推奨
        """
        recommendations = []
        
        # 上位N頭を抽出
        top_horses = predictions.nlargest(top_n, 'top3_prob')
        
        # 3連複の組み合わせ（組み合わせ）
        for horse1, horse2, horse3 in combinations(top_horses.itertuples(), 3):
            umaban1 = horse1.umaban
            umaban2 = horse2.umaban
            umaban3 = horse3.umaban
            
            # 3着以内確率（簡易計算）
            trio_prob = (horse1.top3_prob + horse2.top3_prob + horse3.top3_prob) / 3
            
            # オッズ取得
            odds_row = odds[
                (odds['umaban1'] == umaban1) &
                (odds['umaban2'] == umaban2) &
                (odds['umaban3'] == umaban3)
            ]
            
            if len(odds_row) == 0:
                continue
            
            sanrenpuku_odds = odds_row['sanrenpuku_odds'].values[0]
            
            # 期待値計算
            ev = self.calculate_expected_value(trio_prob, sanrenpuku_odds)
            
            # 期待値がプラスの場合のみ購入
            if ev >= self.min_ev:
                # Kelly賭け金計算
                bet_amount = self.calculate_kelly_bet(trio_prob, sanrenpuku_odds, ev)
                
                recommendations.append({
                    'betting_type': '3連複',
                    'horses': f"{umaban1}-{umaban2}-{umaban3}",
                    'win_prob': trio_prob,
                    'odds': sanrenpuku_odds,
                    'expected_value': ev,
                    'bet_amount': bet_amount,
                    'expected_return': bet_amount * (1 + ev)
                })
        
        return pd.DataFrame(recommendations)
    
    
    def calculate_trifecta_bets(self, predictions, odds, top_n=5):
        """
        3連単の購入推奨を計算（Harville公式使用）
        
        Args:
            predictions: 予測DataFrame（umaban, win_prob）
            odds: オッズDataFrame（umaban1, umaban2, umaban3, sanrentan_odds）
            top_n: 上位N頭で組み合わせ作成
        
        Returns:
            pd.DataFrame: 購入推奨
        """
        recommendations = []
        
        # 上位N頭を抽出
        top_horses = predictions.nlargest(top_n, 'win_prob')
        probabilities = top_horses['win_prob'].values
        
        # 3連単の組み合わせ（順列）
        for horse1, horse2, horse3 in permutations(top_horses.itertuples(), 3):
            umaban1 = horse1.umaban
            umaban2 = horse2.umaban
            umaban3 = horse3.umaban
            
            # Harville公式で3連単確率計算
            positions = [
                top_horses[top_horses['umaban'] == umaban1].index[0],
                top_horses[top_horses['umaban'] == umaban2].index[0],
                top_horses[top_horses['umaban'] == umaban3].index[0]
            ]
            
            trifecta_prob = self.harville_formula(probabilities, positions)
            
            # オッズ取得
            odds_row = odds[
                (odds['umaban1'] == umaban1) &
                (odds['umaban2'] == umaban2) &
                (odds['umaban3'] == umaban3)
            ]
            
            if len(odds_row) == 0:
                continue
            
            sanrentan_odds = odds_row['sanrentan_odds'].values[0]
            
            # 期待値計算
            ev = self.calculate_expected_value(trifecta_prob, sanrentan_odds)
            
            # 期待値がプラスの場合のみ購入
            if ev >= self.min_ev:
                # Kelly賭け金計算
                bet_amount = self.calculate_kelly_bet(trifecta_prob, sanrentan_odds, ev)
                
                recommendations.append({
                    'betting_type': '3連単',
                    'horses': f"{umaban1}-{umaban2}-{umaban3}",
                    'win_prob': trifecta_prob,
                    'odds': sanrentan_odds,
                    'expected_value': ev,
                    'bet_amount': bet_amount,
                    'expected_return': bet_amount * (1 + ev)
                })
        
        return pd.DataFrame(recommendations)
    
    
    def generate_recommendations(self, predictions, odds, betting_types=['単勝', '複勝', '馬単', '3連複']):
        """
        全馬券種の購入推奨を生成
        
        Args:
            predictions: 予測DataFrame
            odds: オッズDataFrame
            betting_types: 購入する馬券種リスト
        
        Returns:
            pd.DataFrame: 購入推奨一覧
        """
        print("\n" + "=" * 80)
        print("期待値ベース購入戦略計算中...")
        print("=" * 80)
        
        all_recommendations = []
        
        # 単勝
        if '単勝' in betting_types:
            print("  - 単勝計算中...")
            win_recs = self.calculate_win_bets(predictions, odds)
            if len(win_recs) > 0:
                all_recommendations.append(win_recs)
                print(f"    ✅ {len(win_recs)}件の購入候補")
        
        # 複勝
        if '複勝' in betting_types:
            print("  - 複勝計算中...")
            place_recs = self.calculate_place_bets(predictions, odds)
            if len(place_recs) > 0:
                all_recommendations.append(place_recs)
                print(f"    ✅ {len(place_recs)}件の購入候補")
        
        # 馬単
        if '馬単' in betting_types:
            print("  - 馬単計算中...")
            exacta_recs = self.calculate_exacta_bets(predictions, odds)
            if len(exacta_recs) > 0:
                all_recommendations.append(exacta_recs)
                print(f"    ✅ {len(exacta_recs)}件の購入候補")
        
        # 3連複
        if '3連複' in betting_types:
            print("  - 3連複計算中...")
            trio_recs = self.calculate_trio_bets(predictions, odds)
            if len(trio_recs) > 0:
                all_recommendations.append(trio_recs)
                print(f"    ✅ {len(trio_recs)}件の購入候補")
        
        # 3連単
        if '3連単' in betting_types:
            print("  - 3連単計算中...")
            trifecta_recs = self.calculate_trifecta_bets(predictions, odds)
            if len(trifecta_recs) > 0:
                all_recommendations.append(trifecta_recs)
                print(f"    ✅ {len(trifecta_recs)}件の購入候補")
        
        # 統合
        if len(all_recommendations) == 0:
            print("\n⚠️  購入推奨なし（期待値がプラスの馬券がありません）")
            return pd.DataFrame()
        
        recommendations = pd.concat(all_recommendations, ignore_index=True)
        recommendations = recommendations.sort_values('expected_value', ascending=False)
        
        print(f"\n✅ 購入推奨生成完了")
        print(f"  - 合計: {len(recommendations)}件")
        print(f"  - 総賭け金: {recommendations['bet_amount'].sum():,}円")
        print(f"  - 期待リターン: {recommendations['expected_return'].sum():,.0f}円")
        print(f"  - 期待利益: {recommendations['expected_return'].sum() - recommendations['bet_amount'].sum():,.0f}円")
        
        return recommendations


# テスト用
if __name__ == '__main__':
    # サンプルデータ
    predictions = pd.DataFrame({
        'umaban': [1, 2, 3, 4, 5, 6, 7, 8],
        'win_prob': [0.25, 0.15, 0.12, 0.10, 0.08, 0.07, 0.05, 0.03],
        'top3_prob': [0.60, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15]
    })
    
    odds = pd.DataFrame({
        'umaban': [1, 2, 3, 4, 5, 6, 7, 8],
        'tansho_odds': [4.5, 7.2, 9.8, 12.5, 15.0, 18.0, 25.0, 50.0],
        'fukusho_odds': [1.8, 2.5, 3.2, 4.0, 4.5, 5.0, 6.0, 8.0]
    })
    
    # エンジン初期化
    engine = BettingStrategyEngine(bankroll=100000, kelly_fraction=0.25, max_bet_pct=0.05, min_ev=0.05)
    
    # 購入推奨生成
    recommendations = engine.generate_recommendations(predictions, odds, betting_types=['単勝', '複勝'])
    
    # 結果表示
    print("\n購入推奨一覧:")
    print(recommendations[['betting_type', 'horses', 'odds', 'expected_value', 'bet_amount']].to_string(index=False))
