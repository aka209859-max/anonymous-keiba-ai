#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
トリプル馬単投資戦略エンジン（Kelly基準）

Kelly基準を用いた最適投資額算出と、リスク管理機能を実装
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
import json
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TripleBettingStrategy:
    """トリプル馬単投資戦略エンジン"""
    
    def __init__(self, bankroll: int = 100000, risk_factor: float = 0.5):
        """
        初期化
        
        Args:
            bankroll: 総資金（円）
            risk_factor: リスク係数（0〜1、デフォルト: 0.5 = Half Kelly）
        """
        self.bankroll = bankroll
        self.risk_factor = risk_factor
        self.deduction_rate = 0.30  # トリプル馬単の控除率
        
        logging.info(f"💰 総資金: {bankroll:,}円")
        logging.info(f"📊 リスク係数: {risk_factor} (Full Kelly=1.0)")
    
    def calculate_kelly_criterion(self, win_probability: float, 
                                  odds: float) -> float:
        """
        Kelly基準による最適投資比率を計算
        
        Kelly公式: f* = (bp - q) / b
        where:
            f* = 最適投資比率
            b = オッズ（配当倍率 - 1）
            p = 勝率
            q = 負率 (1 - p)
        
        Args:
            win_probability: 勝率（0〜1）
            odds: オッズ（倍率）
        
        Returns:
            float: 最適投資比率（0〜1）
        """
        if win_probability <= 0 or odds <= 1:
            return 0.0
        
        b = odds - 1  # 純利益倍率
        p = win_probability
        q = 1 - p
        
        # Kelly公式
        kelly_fraction = (b * p - q) / b
        
        # 負の値の場合は投資しない
        if kelly_fraction < 0:
            return 0.0
        
        # リスク係数を適用（Full Kelly は激しすぎるため、Half Kelly等を推奨）
        adjusted_kelly = kelly_fraction * self.risk_factor
        
        # 最大投資比率を25%に制限（破産リスク軽減）
        return min(adjusted_kelly, 0.25)
    
    def estimate_expected_odds(self, carryover: int, 
                              estimated_sales: int,
                              num_winners: int = 1) -> float:
        """
        期待オッズを推定
        
        Args:
            carryover: キャリーオーバー額（円）
            estimated_sales: 予想売上高（円）
            num_winners: 予想的中者数（デフォルト: 1）
        
        Returns:
            float: 期待オッズ（倍率）
        """
        # 配当原資 = キャリーオーバー + 売上 × (1 - 控除率)
        payout_pool = carryover + (estimated_sales * (1 - self.deduction_rate))
        
        # 1口50円あたりの期待配当
        expected_payout_per_ticket = payout_pool / num_winners if num_winners > 0 else 0
        
        # オッズ = 配当 / 投資額
        odds = expected_payout_per_ticket / 50 if expected_payout_per_ticket > 0 else 0
        
        return odds
    
    def calculate_investment_amount(self, carryover: int,
                                   estimated_sales: int,
                                   win_probability: float,
                                   num_combinations: int) -> Dict[str, any]:
        """
        投資額を計算
        
        Args:
            carryover: キャリーオーバー額（円）
            estimated_sales: 予想売上高（円）
            win_probability: 勝率（0〜1）
            num_combinations: 購入する組み合わせ数
        
        Returns:
            dict: 投資分析結果
        """
        # 期待オッズを推定
        expected_odds = self.estimate_expected_odds(carryover, estimated_sales, 1)
        
        # Kelly基準による最適投資比率
        kelly_fraction = self.calculate_kelly_criterion(win_probability, expected_odds)
        
        # 最適投資額
        optimal_investment = self.bankroll * kelly_fraction
        
        # 実際の購入額（50円単位、購入点数を考慮）
        cost_per_combination = 50
        total_cost = num_combinations * cost_per_combination
        
        # 期待値計算
        payout_pool = carryover + (estimated_sales * (1 - self.deduction_rate))
        expected_return = payout_pool * win_probability
        expected_profit = expected_return - total_cost
        
        # ROI（投資収益率）
        roi = (expected_return / total_cost - 1) if total_cost > 0 else 0
        
        # 投資判定
        if kelly_fraction <= 0:
            decision = "❌ 見送り推奨（期待値マイナス）"
        elif total_cost > optimal_investment:
            decision = "⚠️ 投資額過大（Kelly基準超過）"
        elif roi < 0:
            decision = "⚠️ 期待値マイナス（投資非推奨）"
        elif roi < 0.5:
            decision = "△ 低期待値（慎重に判断）"
        else:
            decision = "✅ 投資推奨"
        
        return {
            'carryover': carryover,
            'estimated_sales': estimated_sales,
            'expected_odds': expected_odds,
            'win_probability': win_probability,
            'kelly_fraction': kelly_fraction,
            'optimal_investment': optimal_investment,
            'num_combinations': num_combinations,
            'total_cost': total_cost,
            'expected_return': expected_return,
            'expected_profit': expected_profit,
            'roi': roi,
            'decision': decision
        }
    
    def generate_investment_scenarios(self, venue_code: int,
                                     venue_name: str,
                                     fullgate: int,
                                     carryover: int,
                                     predictions: pd.DataFrame) -> List[Dict[str, any]]:
        """
        複数の投資シナリオを生成
        
        Args:
            venue_code: 競馬場コード
            venue_name: 競馬場名
            fullgate: フルゲート頭数
            carryover: キャリーオーバー額
            predictions: AI予想データ（ensemble CSV）
        
        Returns:
            list: 投資シナリオリスト
        """
        # 最終3レースを抽出
        target_races = predictions['race_bango'].max() - 2
        last_3_races = predictions[predictions['race_bango'] >= target_races]
        
        # 総組み合わせ数
        umatan_per_race = fullgate * (fullgate - 1)
        total_combinations = umatan_per_race ** 3
        
        # 売上高推定（キャリーオーバー額に応じて変動）
        if carryover > 500_000_000:
            estimated_sales = 5_000_000  # 5億円超: 500万円
        elif carryover > 100_000_000:
            estimated_sales = 2_000_000  # 1億円超: 200万円
        else:
            estimated_sales = 1_000_000  # 1億円未満: 100万円
        
        scenarios = []
        
        # シナリオ1: 超堅実型（TOP2のみ、各2点）
        scenario1 = self.calculate_investment_amount(
            carryover=carryover,
            estimated_sales=estimated_sales,
            win_probability=8 / total_combinations,
            num_combinations=8
        )
        scenario1['name'] = "超堅実型（2-2-2）"
        scenario1['description'] = "各レースTOP2の馬単2点買い"
        scenarios.append(scenario1)
        
        # シナリオ2: バランス型（1着1頭、2着3頭）
        scenario2 = self.calculate_investment_amount(
            carryover=carryover,
            estimated_sales=estimated_sales,
            win_probability=27 / total_combinations,
            num_combinations=27
        )
        scenario2['name'] = "バランス型（3-3-3）"
        scenario2['description'] = "1着本命1頭、2着候補3頭"
        scenarios.append(scenario2)
        
        # シナリオ3: 広範囲型（1着2頭、2着4頭）
        scenario3 = self.calculate_investment_amount(
            carryover=carryover,
            estimated_sales=estimated_sales,
            win_probability=64 / total_combinations,
            num_combinations=64
        )
        scenario3['name'] = "広範囲型（4-4-4）"
        scenario3['description'] = "1着候補2頭、2着候補4頭"
        scenarios.append(scenario3)
        
        # シナリオ4: 超広範囲型（キャリーオーバー5億円以上専用）
        if carryover >= 500_000_000:
            scenario4 = self.calculate_investment_amount(
                carryover=carryover,
                estimated_sales=estimated_sales,
                win_probability=216 / total_combinations,
                num_combinations=216
            )
            scenario4['name'] = "超広範囲型（6-6-6）"
            scenario4['description'] = "1着候補3頭、2着候補6頭"
            scenarios.append(scenario4)
        
        return scenarios
    
    def save_strategy_report(self, scenarios: List[Dict], output_path: str):
        """
        投資戦略レポートを保存
        
        Args:
            scenarios: 投資シナリオリスト
            output_path: 出力先パス
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(scenarios, f, ensure_ascii=False, indent=2)
        
        logging.info(f"💾 投資戦略レポート保存: {output_file}")


def main():
    """メイン処理"""
    strategy = TripleBettingStrategy(bankroll=100000, risk_factor=0.5)
    
    print("="*80)
    print("トリプル馬単投資戦略エンジン（Kelly基準）")
    print("="*80)
    
    # テストケース: 船橋競馬、キャリーオーバー2.7億円
    print("\n📊 投資シナリオ分析")
    print("-"*80)
    print("競馬場: 船橋競馬（14頭立て）")
    print("キャリーオーバー: 270,000,000円")
    print("総資金: 100,000円")
    print("リスク係数: 0.5 (Half Kelly)")
    print("-"*80)
    
    # ダミーの予想データ作成
    dummy_predictions = pd.DataFrame({
        'race_bango': [10, 10, 11, 11, 12, 12],
        'umaban': [1, 2, 3, 4, 5, 6],
        'ensemble_score': [0.9, 0.8, 0.85, 0.75, 0.88, 0.78]
    })
    
    scenarios = strategy.generate_investment_scenarios(
        venue_code=43,
        venue_name="船橋",
        fullgate=14,
        carryover=270_000_000,
        predictions=dummy_predictions
    )
    
    print("\n投資シナリオ別分析:")
    print("="*80)
    
    for scenario in scenarios:
        print(f"\n【{scenario['name']}】")
        print(f"説明: {scenario['description']}")
        print(f"購入点数: {scenario['num_combinations']}点")
        print(f"投資額: {scenario['total_cost']:,}円")
        print(f"期待オッズ: {scenario['expected_odds']:.1f}倍")
        print(f"勝率: {scenario['win_probability']:.10f}")
        print(f"Kelly最適投資額: {scenario['optimal_investment']:,.0f}円")
        print(f"期待リターン: {scenario['expected_return']:,.0f}円")
        print(f"期待利益: {scenario['expected_profit']:,.0f}円")
        print(f"ROI: {scenario['roi']:.2%}")
        print(f"判定: {scenario['decision']}")
        print("-"*80)
    
    print("\n✅ 投資戦略分析完了")
    print("="*80)
    
    print("\n💡 Kelly基準の解説:")
    print("- Full Kelly (1.0): 最大成長率だが変動大")
    print("- Half Kelly (0.5): 推奨設定、リスクとリターンのバランス")
    print("- Quarter Kelly (0.25): 保守的、低リスク")
    print("- 総資金の25%を超える投資は避けるべき")


if __name__ == "__main__":
    main()
