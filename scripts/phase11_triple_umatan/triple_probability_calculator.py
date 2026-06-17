#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
トリプル馬単3レース連続的中確率計算機

フルゲート頭数に基づいて、3レース連続で馬単を的中させる確率を計算
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TripleProbabilityCalculator:
    """トリプル馬単確率計算機"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def calculate_umatan_combinations(self, num_horses: int) -> int:
        """
        馬単の組み合わせ数を計算
        
        Args:
            num_horses: 出走頭数
        
        Returns:
            int: 馬単の組み合わせ数（1着×2着）
        """
        if num_horses < 2:
            return 0
        
        # 馬単 = n × (n-1)
        return num_horses * (num_horses - 1)
    
    def calculate_triple_combinations(self, horses_race1: int, 
                                     horses_race2: int, 
                                     horses_race3: int) -> int:
        """
        3レース連続馬単の組み合わせ数を計算
        
        Args:
            horses_race1: 1レース目の出走頭数
            horses_race2: 2レース目の出走頭数
            horses_race3: 3レース目の出走頭数
        
        Returns:
            int: 3レース連続馬単の総組み合わせ数
        """
        combo1 = self.calculate_umatan_combinations(horses_race1)
        combo2 = self.calculate_umatan_combinations(horses_race2)
        combo3 = self.calculate_umatan_combinations(horses_race3)
        
        return combo1 * combo2 * combo3
    
    def calculate_hit_probability(self, total_combinations: int, 
                                  selected_combinations: int) -> float:
        """
        的中確率を計算
        
        Args:
            total_combinations: 総組み合わせ数
            selected_combinations: 購入した組み合わせ数
        
        Returns:
            float: 的中確率（0〜1）
        """
        if total_combinations == 0:
            return 0.0
        
        return selected_combinations / total_combinations
    
    def calculate_expected_value(self, carryover: int, 
                                total_sales: int,
                                deduction_rate: float = 0.30,
                                hit_probability: float = 0.0001) -> float:
        """
        期待値を計算
        
        Args:
            carryover: キャリーオーバー額（円）
            total_sales: 予想売上高（円）
            deduction_rate: 控除率（デフォルト: 30%）
            hit_probability: 的中確率
        
        Returns:
            float: 期待値（円）
        """
        # 配当原資 = キャリーオーバー + 売上 × (1 - 控除率)
        payout_pool = carryover + (total_sales * (1 - deduction_rate))
        
        # 期待値 = 配当原資 × 的中確率
        expected_value = payout_pool * hit_probability
        
        return expected_value
    
    def analyze_venue_difficulty(self, fullgate: int) -> Dict[str, any]:
        """
        競馬場の難易度分析
        
        Args:
            fullgate: フルゲート頭数
        
        Returns:
            dict: 難易度分析結果
        """
        # 1レースあたりの馬単組み合わせ数
        umatan_per_race = self.calculate_umatan_combinations(fullgate)
        
        # 3レース連続の組み合わせ数（フルゲートの場合）
        total_combinations = umatan_per_race ** 3
        
        # 難易度レベル判定
        if total_combinations > 10_000_000:
            difficulty = "超高難度"
        elif total_combinations > 5_000_000:
            difficulty = "高難度"
        else:
            difficulty = "中難度"
        
        return {
            'fullgate': fullgate,
            'umatan_per_race': umatan_per_race,
            'total_combinations': total_combinations,
            'difficulty': difficulty,
            'hit_rate_1point': 1 / total_combinations if total_combinations > 0 else 0
        }
    
    def generate_probability_table(self, num_horses_list: List[int]) -> pd.DataFrame:
        """
        出走頭数別の確率テーブルを生成
        
        Args:
            num_horses_list: 出走頭数のリスト
        
        Returns:
            pd.DataFrame: 確率テーブル
        """
        data = []
        
        for num_horses in num_horses_list:
            analysis = self.analyze_venue_difficulty(num_horses)
            
            data.append({
                '出走頭数': num_horses,
                '馬単組合せ（1R）': analysis['umatan_per_race'],
                '3R連続組合せ数': analysis['total_combinations'],
                '1点的中確率': f"{analysis['hit_rate_1point']:.10f}",
                '100点的中確率': f"{analysis['hit_rate_1point'] * 100:.8f}",
                '難易度': analysis['difficulty']
            })
        
        return pd.DataFrame(data)
    
    def calculate_investment_scenarios(self, venue_code: int, 
                                      fullgate: int,
                                      carryover: int,
                                      prediction_top3: List[Tuple[int, int, int]]) -> Dict[str, any]:
        """
        投資シナリオを計算
        
        Args:
            venue_code: 競馬場コード
            fullgate: フルゲート頭数
            carryover: キャリーオーバー額
            prediction_top3: 各レースのTOP3予想 [(1着, 2着, 3着), ...]
        
        Returns:
            dict: 投資シナリオ分析結果
        """
        # 総組み合わせ数（フルゲート想定）
        total_combinations = self.calculate_umatan_combinations(fullgate) ** 3
        
        # シナリオ1: 堅実型（各レース上位2頭で1-2、2-1）
        scenario1_points = 2 * 2 * 2  # 8点
        scenario1_cost = scenario1_points * 50  # 400円
        scenario1_prob = scenario1_points / total_combinations
        
        # シナリオ2: バランス型（1着1頭、2着3頭）
        scenario2_points = 3 * 3 * 3  # 27点
        scenario2_cost = scenario2_points * 50  # 1,350円
        scenario2_prob = scenario2_points / total_combinations
        
        # シナリオ3: 広範囲型（1着2頭、2着4頭）
        scenario3_points = 8 * 8 * 8  # 512点
        scenario3_cost = scenario3_points * 50  # 25,600円
        scenario3_prob = scenario3_points / total_combinations
        
        # 期待値計算（予想売上を100万円と仮定）
        estimated_sales = 1_000_000
        
        scenarios = []
        for name, points, cost, prob in [
            ("堅実型（2-2-2）", scenario1_points, scenario1_cost, scenario1_prob),
            ("バランス型（3-3-3）", scenario2_points, scenario2_cost, scenario2_prob),
            ("広範囲型（8-8-8）", scenario3_points, scenario3_cost, scenario3_prob)
        ]:
            expected_val = self.calculate_expected_value(
                carryover, estimated_sales, 0.30, prob
            )
            
            scenarios.append({
                'シナリオ': name,
                '購入点数': points,
                '投資額': cost,
                '的中確率': f"{prob:.10f}",
                '期待値': int(expected_val),
                'ROI': f"{(expected_val / cost - 1) * 100:.2f}%" if cost > 0 else "N/A"
            })
        
        return {
            'venue_code': venue_code,
            'fullgate': fullgate,
            'carryover': carryover,
            'total_combinations': total_combinations,
            'scenarios': scenarios
        }


def main():
    """メイン処理"""
    calculator = TripleProbabilityCalculator()
    
    print("="*80)
    print("トリプル馬単3レース連続的中確率計算")
    print("="*80)
    
    # 出走頭数別の確率テーブル
    print("\n📊 出走頭数別確率テーブル")
    print("-"*80)
    
    prob_table = calculator.generate_probability_table([12, 13, 14, 15, 16])
    print(prob_table.to_string(index=False))
    
    # 投資シナリオ例（船橋競馬、キャリーオーバー2.7億円を想定）
    print("\n" + "="*80)
    print("📈 投資シナリオ分析例")
    print("="*80)
    print("競馬場: 船橋競馬（14頭立て）")
    print("キャリーオーバー: 270,000,000円")
    print("-"*80)
    
    scenario_result = calculator.calculate_investment_scenarios(
        venue_code=43,
        fullgate=14,
        carryover=270_000_000,
        prediction_top3=[(1, 2, 3), (4, 5, 6), (7, 8, 9)]
    )
    
    print(f"\n総組み合わせ数: {scenario_result['total_combinations']:,}通り")
    print(f"1点的中確率: {1/scenario_result['total_combinations']:.10f}")
    print("\n投資シナリオ別分析:")
    print("-"*80)
    
    scenario_df = pd.DataFrame(scenario_result['scenarios'])
    print(scenario_df.to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ 確率計算完了")
    print("="*80)
    
    print("\n💡 推奨戦略:")
    print("- キャリーオーバー1億円未満: 堅実型またはパスを推奨")
    print("- キャリーオーバー1〜5億円: バランス型を推奨")
    print("- キャリーオーバー5億円以上: 広範囲型も選択肢に")
    print("- 控除率30%を考慮し、期待値がマイナスの場合は見送りを推奨")


if __name__ == "__main__":
    main()
