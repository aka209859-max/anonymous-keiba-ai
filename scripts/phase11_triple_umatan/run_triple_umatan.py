#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
トリプル馬単統合実行スクリプト

全機能を統合し、ワンコマンドでトリプル馬単の買い目を生成
"""

import sys
import os
import pandas as pd
import argparse
import logging
from pathlib import Path
import datetime

# 自作モジュールのインポート
sys.path.append(str(Path(__file__).parent))
from scrape_carryover import TripleUmatanCarryoverScraper
from triple_probability_calculator import TripleProbabilityCalculator
from triple_betting_strategy import TripleBettingStrategy
from generate_triple_tickets import TripleTicketGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TripleUmatanSystem:
    """トリプル馬単統合システム"""
    
    def __init__(self, bankroll: int = 100000, risk_factor: float = 0.5):
        """
        初期化
        
        Args:
            bankroll: 総資金（円）
            risk_factor: リスク係数（0〜1）
        """
        self.scraper = TripleUmatanCarryoverScraper()
        self.calculator = TripleProbabilityCalculator()
        self.strategy = TripleBettingStrategy(bankroll, risk_factor)
        self.generator = TripleTicketGenerator()
        
        self.bankroll = bankroll
        self.risk_factor = risk_factor
    
    def run_full_analysis(self, venue_code: int, 
                         ensemble_csv_path: str,
                         strategy_type: str = "balanced") -> dict:
        """
        完全分析を実行
        
        Args:
            venue_code: 競馬場コード
            ensemble_csv_path: ensemble予想CSVのパス
            strategy_type: 投資戦略タイプ
        
        Returns:
            dict: 分析結果
        """
        print("="*80)
        print("トリプル馬単統合分析システム")
        print("="*80)
        
        # 1. キャリーオーバー情報取得
        print("\n[1/5] キャリーオーバー情報取得中...")
        print("-"*80)
        
        carryover_data = self.scraper.fetch_all_carryover()
        
        if venue_code not in carryover_data:
            logging.error(f"❌ 競馬場コード {venue_code} の情報が見つかりません")
            return {}
        
        venue_info = carryover_data[venue_code]
        venue_name = venue_info['venue_name']
        carryover = venue_info['carryover']
        fullgate = venue_info['fullgate']
        
        print(f"競馬場: {venue_name}（コード: {venue_code}）")
        print(f"キャリーオーバー: {carryover:,}円")
        print(f"フルゲート: {fullgate}頭")
        
        if carryover == 0:
            print("\n⚠️ キャリーオーバーがありません。")
            print("トリプル馬単の購入は推奨されません。")
            return {}
        
        # 2. ensemble予想データ読み込み
        print("\n[2/5] AI予想データ読み込み中...")
        print("-"*80)
        
        try:
            ensemble_df = pd.read_csv(ensemble_csv_path, encoding='shift-jis')
        except:
            ensemble_df = pd.read_csv(ensemble_csv_path, encoding='utf-8')
        
        print(f"✅ データ読み込み完了: {len(ensemble_df)}件")
        
        # 最終3レースを抽出
        target_races = self.generator.extract_target_races(ensemble_df)
        race_numbers = sorted(target_races['race_bango'].unique())
        
        if len(race_numbers) != 3:
            logging.error(f"❌ 最終3レースが見つかりません")
            return {}
        
        print(f"対象レース: 第{race_numbers[0]}R - 第{race_numbers[1]}R - 第{race_numbers[2]}R")
        
        # 3. 確率・期待値計算
        print("\n[3/5] 確率・期待値計算中...")
        print("-"*80)
        
        difficulty = self.calculator.analyze_venue_difficulty(fullgate)
        
        print(f"総組み合わせ数: {difficulty['total_combinations']:,}通り")
        print(f"1点的中確率: {difficulty['hit_rate_1point']:.10f}")
        print(f"難易度: {difficulty['difficulty']}")
        
        # 4. 投資戦略分析
        print("\n[4/5] 投資戦略分析中...")
        print("-"*80)
        
        scenarios = self.strategy.generate_investment_scenarios(
            venue_code=venue_code,
            venue_name=venue_name,
            fullgate=fullgate,
            carryover=carryover,
            predictions=target_races
        )
        
        print(f"\n総資金: {self.bankroll:,}円")
        print(f"リスク係数: {self.risk_factor}")
        print("\n投資シナリオ別分析:")
        print("-"*80)
        
        for scenario in scenarios:
            print(f"\n【{scenario['name']}】")
            print(f"  購入点数: {scenario['num_combinations']}点")
            print(f"  投資額: {scenario['total_cost']:,}円")
            print(f"  期待リターン: {scenario['expected_return']:,.0f}円")
            print(f"  ROI: {scenario['roi']:.2%}")
            print(f"  判定: {scenario['decision']}")
        
        # 推奨シナリオを選択
        recommended_scenario = None
        for scenario in scenarios:
            if "✅" in scenario['decision']:
                recommended_scenario = scenario
                break
        
        if not recommended_scenario:
            print("\n⚠️ 投資推奨シナリオが見つかりません")
            print("全シナリオで期待値がマイナスです。購入は見送りを推奨します。")
            return {
                'venue_name': venue_name,
                'carryover': carryover,
                'recommendation': '見送り',
                'scenarios': scenarios
            }
        
        # 5. 買い目生成
        print("\n[5/5] 買い目生成中...")
        print("-"*80)
        
        tickets = self.generator.generate_triple_tickets(target_races, strategy=strategy_type)
        
        if not tickets:
            logging.error("❌ 買い目生成に失敗しました")
            return {}
        
        # 買い目を表示
        formatted = self.generator.format_tickets_for_display(tickets, race_numbers)
        print("\n" + formatted)
        
        # 買い目をファイル保存
        self.generator.save_tickets_to_file(
            tickets=tickets,
            venue_name=venue_name,
            race_numbers=race_numbers,
            strategy=strategy_type
        )
        
        # キャリーオーバー情報も保存
        today = datetime.datetime.now().strftime("%Y%m%d")
        carryover_path = f"data/triple_umatan/carryover/carryover_{today}.json"
        self.scraper.save_to_json(carryover_data, carryover_path)
        
        print("\n" + "="*80)
        print("✅ 統合分析完了")
        print("="*80)
        
        return {
            'venue_name': venue_name,
            'venue_code': venue_code,
            'carryover': carryover,
            'fullgate': fullgate,
            'race_numbers': race_numbers,
            'num_tickets': len(tickets),
            'total_cost': len(tickets) * 50,
            'recommendation': recommended_scenario['name'],
            'expected_return': recommended_scenario['expected_return'],
            'roi': recommended_scenario['roi'],
            'scenarios': scenarios
        }


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='トリプル馬単統合分析システム',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 船橋競馬のトリプル馬単分析
  python run_triple_umatan.py 43 data/predictions/phase5/船橋_20260214_ensemble.csv
  
  # 大井競馬、広範囲型戦略で分析
  python run_triple_umatan.py 44 data/predictions/phase5/大井_20260214_ensemble.csv --strategy aggressive
  
  # 総資金50万円、Full Kelly で分析
  python run_triple_umatan.py 43 data/predictions/phase5/船橋_20260214_ensemble.csv --bankroll 500000 --risk 1.0

戦略タイプ:
  conservative    : 超堅実型（2-2-2）
  balanced        : バランス型（3-3-3）[デフォルト]
  aggressive      : 広範囲型（4-4-4）
  very_aggressive : 超広範囲型（6-6-6）
        """
    )
    
    parser.add_argument('venue_code', type=int, 
                       help='競馬場コード（例: 43=船橋、44=大井）')
    parser.add_argument('ensemble_csv', type=str,
                       help='ensemble予想CSVのパス')
    parser.add_argument('--strategy', type=str, default='balanced',
                       choices=['conservative', 'balanced', 'aggressive', 'very_aggressive'],
                       help='投資戦略タイプ（デフォルト: balanced）')
    parser.add_argument('--bankroll', type=int, default=100000,
                       help='総資金（円）（デフォルト: 100,000円）')
    parser.add_argument('--risk', type=float, default=0.5,
                       help='リスク係数（0〜1、デフォルト: 0.5 = Half Kelly）')
    
    args = parser.parse_args()
    
    # システム初期化
    system = TripleUmatanSystem(bankroll=args.bankroll, risk_factor=args.risk)
    
    # 完全分析実行
    result = system.run_full_analysis(
        venue_code=args.venue_code,
        ensemble_csv_path=args.ensemble_csv,
        strategy_type=args.strategy
    )
    
    if result:
        print("\n📊 分析結果サマリー:")
        print("-"*80)
        print(f"競馬場: {result.get('venue_name', 'N/A')}")
        print(f"キャリーオーバー: {result.get('carryover', 0):,}円")
        print(f"購入点数: {result.get('num_tickets', 0)}点")
        print(f"投資額: {result.get('total_cost', 0):,}円")
        print(f"推奨戦略: {result.get('recommendation', 'N/A')}")
        print(f"期待リターン: {result.get('expected_return', 0):,.0f}円")
        print(f"ROI: {result.get('roi', 0):.2%}")
        print("-"*80)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 引数なしの場合はテスト実行
        print("テストモードで実行します（ダミーデータ使用）")
        print("="*80)
        
        # ダミーCSVを作成
        dummy_csv = "data/predictions/phase5/test_ensemble.csv"
        os.makedirs("data/predictions/phase5", exist_ok=True)
        
        dummy_data = pd.DataFrame({
            'race_id': [10, 10, 10, 11, 11, 11, 12, 12, 12],
            'race_bango': [10, 10, 10, 11, 11, 11, 12, 12, 12],
            'umaban': [1, 2, 3, 4, 5, 6, 7, 8, 9],
            'ensemble_score': [0.95, 0.88, 0.82, 0.90, 0.85, 0.80, 0.92, 0.87, 0.83],
            'keibajo_code': [43] * 9
        })
        dummy_data.to_csv(dummy_csv, index=False, encoding='shift-jis')
        
        system = TripleUmatanSystem(bankroll=100000, risk_factor=0.5)
        result = system.run_full_analysis(
            venue_code=43,
            ensemble_csv_path=dummy_csv,
            strategy_type="balanced"
        )
    else:
        main()
