#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtest_simulator.py
Phase 10: バックテスト・シミュレーター

過去データで購入戦略を検証し、回収率・的中率を算出します。

検証項目:
    1. 回収率（回収額 / 投資額）
    2. 的中率（的中回数 / 総レース数）
    3. 最大連敗・最大利益・最大損失
    4. 馬券種別の成績
    5. 月別・競馬場別の成績

使用法:
    python backtest_simulator.py --start-date 2024-01-01 --end-date 2024-12-31 --venue 名古屋
    
オプション:
    --venue VENUE             競馬場名
    --start-date DATE         開始日（YYYY-MM-DD）
    --end-date DATE           終了日（YYYY-MM-DD）
    --initial-bankroll MONEY  初期資金（円）
    --kelly-fraction FRAC     Kelly比率（デフォルト: 0.25）
    
出力:
    - data/backtest/{venue}_{start}_{end}_report.json（詳細レポート）
    - data/backtest/{venue}_{start}_{end}_performance.png（パフォーマンスグラフ）
    - data/backtest/{venue}_{start}_{end}_summary.csv（サマリー）
"""

import sys
import os
import pandas as pd
import numpy as np
import json
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.phase9_betting_strategy.betting_strategy_engine import BettingStrategyEngine

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False


class BacktestSimulator:
    """
    バックテスト・シミュレーター
    
    過去データで購入戦略を検証します。
    """
    
    def __init__(self, initial_bankroll=100000, kelly_fraction=0.25):
        """
        Args:
            initial_bankroll: 初期資金（円）
            kelly_fraction: Kelly比率
        """
        self.initial_bankroll = initial_bankroll
        self.kelly_fraction = kelly_fraction
        
        self.bankroll = initial_bankroll
        self.total_investment = 0
        self.total_return = 0
        self.total_profit = 0
        
        self.race_results = []
        self.betting_history = []
        
        print(f"✅ BacktestSimulator初期化完了")
        print(f"  - 初期資金: {initial_bankroll:,}円")
        print(f"  - Kelly比率: {kelly_fraction}")
    
    
    def load_historical_data(self, venue, start_date, end_date):
        """
        過去データを読み込み
        
        Args:
            venue: 競馬場名
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            pd.DataFrame: 過去データ
        """
        print("\n" + "=" * 80)
        print("[1/5] 過去データ読み込み中...")
        print("=" * 80)
        print(f"競馬場: {venue}")
        print(f"期間: {start_date} ～ {end_date}")
        
        # TODO: PC-KEIBAデータベースから過去レース結果とオッズを取得
        # 仮のデータ構造
        # df = pd.read_sql_query(sql, conn)
        
        # サンプルデータ（実装時は実データに置き換え）
        df = pd.DataFrame({
            'race_id': [20240101431] * 8,
            'kaisai_date': ['2024-01-01'] * 8,
            'race_bango': [1] * 8,
            'umaban': list(range(1, 9)),
            'kakutei_chakujun': [1, 2, 3, 4, 5, 6, 7, 8],
            'tansho_odds': [4.5, 7.2, 9.8, 12.5, 15.0, 18.0, 25.0, 50.0],
            'fukusho_odds': [1.8, 2.5, 3.2, 4.0, 4.5, 5.0, 6.0, 8.0],
            'predicted_win_prob': [0.25, 0.15, 0.12, 0.10, 0.08, 0.07, 0.05, 0.03],
            'predicted_top3_prob': [0.60, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15]
        })
        
        print(f"✅ データ読み込み完了")
        print(f"  - レース数: {df['race_id'].nunique():,}件")
        print(f"  - 総出走馬数: {len(df):,}頭")
        
        return df
    
    
    def simulate_race(self, race_df):
        """
        1レースのシミュレーション
        
        Args:
            race_df: 1レース分のデータ
        
        Returns:
            dict: レース結果
        """
        race_id = race_df['race_id'].iloc[0]
        
        # 予測データ準備
        predictions = pd.DataFrame({
            'umaban': race_df['umaban'],
            'win_prob': race_df['predicted_win_prob'],
            'top3_prob': race_df['predicted_top3_prob']
        })
        
        # オッズデータ準備
        odds = pd.DataFrame({
            'umaban': race_df['umaban'],
            'tansho_odds': race_df['tansho_odds'],
            'fukusho_odds': race_df['fukusho_odds']
        })
        
        # BettingStrategyEngine初期化
        engine = BettingStrategyEngine(
            bankroll=self.bankroll,
            kelly_fraction=self.kelly_fraction,
            max_bet_pct=0.05,
            min_ev=0.05
        )
        
        # 購入推奨生成
        recommendations = engine.generate_recommendations(
            predictions,
            odds,
            betting_types=['単勝', '複勝']
        )
        
        # 購入なしの場合
        if len(recommendations) == 0:
            return {
                'race_id': race_id,
                'investment': 0,
                'return': 0,
                'profit': 0,
                'hit': False,
                'betting_count': 0
            }
        
        # 購入実行
        total_investment = recommendations['bet_amount'].sum()
        total_return = 0
        hit = False
        
        for _, bet in recommendations.iterrows():
            betting_type = bet['betting_type']
            horses = bet['horses']
            bet_amount = bet['bet_amount']
            odds_value = bet['odds']
            
            # 的中判定
            if betting_type == '単勝':
                umaban = int(horses)
                winner = race_df[race_df['kakutei_chakujun'] == 1]['umaban'].values[0]
                if umaban == winner:
                    total_return += bet_amount * odds_value
                    hit = True
            
            elif betting_type == '複勝':
                umaban = int(horses)
                top3 = race_df[race_df['kakutei_chakujun'] <= 3]['umaban'].values
                if umaban in top3:
                    total_return += bet_amount * odds_value
                    hit = True
        
        # 資金更新
        profit = total_return - total_investment
        self.bankroll += profit
        
        self.total_investment += total_investment
        self.total_return += total_return
        self.total_profit += profit
        
        # 履歴記録
        race_result = {
            'race_id': race_id,
            'investment': total_investment,
            'return': total_return,
            'profit': profit,
            'hit': hit,
            'betting_count': len(recommendations),
            'bankroll': self.bankroll
        }
        
        self.race_results.append(race_result)
        self.betting_history.extend(recommendations.to_dict('records'))
        
        return race_result
    
    
    def run_backtest(self, historical_data):
        """
        バックテスト実行
        
        Args:
            historical_data: 過去データ
        
        Returns:
            dict: バックテスト結果
        """
        print("\n" + "=" * 80)
        print("[2/5] バックテスト実行中...")
        print("=" * 80)
        
        # レースごとにシミュレーション
        race_ids = historical_data['race_id'].unique()
        
        for i, race_id in enumerate(race_ids, 1):
            race_df = historical_data[historical_data['race_id'] == race_id]
            result = self.simulate_race(race_df)
            
            if i % 100 == 0:
                print(f"  - {i}/{len(race_ids)}レース完了 | 資金: {self.bankroll:,.0f}円 | 回収率: {self.total_return / self.total_investment * 100:.1f}%")
        
        print(f"\n✅ バックテスト完了")
        print(f"  - 総レース数: {len(race_ids)}レース")
        print(f"  - 総投資額: {self.total_investment:,.0f}円")
        print(f"  - 総回収額: {self.total_return:,.0f}円")
        print(f"  - 総利益: {self.total_profit:,.0f}円")
        print(f"  - 回収率: {self.total_return / self.total_investment * 100:.1f}%")
        
        return {
            'total_races': len(race_ids),
            'total_investment': self.total_investment,
            'total_return': self.total_return,
            'total_profit': self.total_profit,
            'recovery_rate': self.total_return / self.total_investment if self.total_investment > 0 else 0,
            'final_bankroll': self.bankroll
        }
    
    
    def calculate_statistics(self):
        """
        詳細統計を計算
        
        Returns:
            dict: 統計情報
        """
        print("\n" + "=" * 80)
        print("[3/5] 統計情報計算中...")
        print("=" * 80)
        
        results_df = pd.DataFrame(self.race_results)
        
        # 的中率
        hit_rate = results_df['hit'].mean() if len(results_df) > 0 else 0
        
        # 最大連勝・最大連敗
        max_win_streak = 0
        max_lose_streak = 0
        current_win_streak = 0
        current_lose_streak = 0
        
        for hit in results_df['hit']:
            if hit:
                current_win_streak += 1
                current_lose_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_lose_streak += 1
                current_win_streak = 0
                max_lose_streak = max(max_lose_streak, current_lose_streak)
        
        # 最大利益・最大損失
        max_profit = results_df['profit'].max() if len(results_df) > 0 else 0
        max_loss = results_df['profit'].min() if len(results_df) > 0 else 0
        
        # 平均利益・平均損失
        avg_profit = results_df['profit'].mean() if len(results_df) > 0 else 0
        
        stats = {
            'hit_rate': hit_rate,
            'max_win_streak': max_win_streak,
            'max_lose_streak': max_lose_streak,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'avg_profit_per_race': avg_profit
        }
        
        print(f"✅ 統計情報計算完了")
        print(f"  - 的中率: {hit_rate * 100:.1f}%")
        print(f"  - 最大連勝: {max_win_streak}回")
        print(f"  - 最大連敗: {max_lose_streak}回")
        print(f"  - 最大利益: {max_profit:,.0f}円")
        print(f"  - 最大損失: {max_loss:,.0f}円")
        
        return stats
    
    
    def visualize_performance(self, output_file):
        """
        パフォーマンスグラフを作成
        
        Args:
            output_file: 出力画像ファイル
        """
        print("\n" + "=" * 80)
        print("[4/5] パフォーマンスグラフ作成中...")
        print("=" * 80)
        
        results_df = pd.DataFrame(self.race_results)
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 資金推移
        axes[0, 0].plot(range(len(results_df)), results_df['bankroll'], color='steelblue', linewidth=2)
        axes[0, 0].axhline(y=self.initial_bankroll, color='red', linestyle='--', label='初期資金')
        axes[0, 0].set_xlabel('Race Number', fontsize=12)
        axes[0, 0].set_ylabel('Bankroll (Yen)', fontsize=12)
        axes[0, 0].set_title('Bankroll Trend', fontsize=14, fontweight='bold')
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        
        # 累積利益
        results_df['cumulative_profit'] = results_df['profit'].cumsum()
        axes[0, 1].plot(range(len(results_df)), results_df['cumulative_profit'], color='green', linewidth=2)
        axes[0, 1].axhline(y=0, color='black', linestyle='-', linewidth=1)
        axes[0, 1].set_xlabel('Race Number', fontsize=12)
        axes[0, 1].set_ylabel('Cumulative Profit (Yen)', fontsize=12)
        axes[0, 1].set_title('Cumulative Profit', fontsize=14, fontweight='bold')
        axes[0, 1].grid(alpha=0.3)
        
        # 利益分布
        axes[1, 0].hist(results_df['profit'], bins=50, color='steelblue', edgecolor='black', alpha=0.7)
        axes[1, 0].axvline(x=0, color='red', linestyle='--', linewidth=2)
        axes[1, 0].set_xlabel('Profit per Race (Yen)', fontsize=12)
        axes[1, 0].set_ylabel('Frequency', fontsize=12)
        axes[1, 0].set_title('Profit Distribution', fontsize=14, fontweight='bold')
        axes[1, 0].grid(alpha=0.3)
        
        # 的中率推移（移動平均）
        results_df['hit_ma'] = results_df['hit'].rolling(window=20, min_periods=1).mean()
        axes[1, 1].plot(range(len(results_df)), results_df['hit_ma'], color='orange', linewidth=2)
        axes[1, 1].set_xlabel('Race Number', fontsize=12)
        axes[1, 1].set_ylabel('Hit Rate (20-race MA)', fontsize=12)
        axes[1, 1].set_title('Hit Rate Trend', fontsize=14, fontweight='bold')
        axes[1, 1].grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ グラフ保存完了: {output_file}")
        
        plt.close()
    
    
    def save_report(self, backtest_result, statistics, output_json, output_csv):
        """
        レポート保存
        
        Args:
            backtest_result: バックテスト結果
            statistics: 統計情報
            output_json: 出力JSONファイル
            output_csv: 出力CSVファイル
        """
        print("\n" + "=" * 80)
        print("[5/5] レポート保存中...")
        print("=" * 80)
        
        # JSON保存
        report = {
            'backtest_result': backtest_result,
            'statistics': statistics,
            'parameters': {
                'initial_bankroll': self.initial_bankroll,
                'kelly_fraction': self.kelly_fraction
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON保存完了: {output_json}")
        
        # CSV保存
        results_df = pd.DataFrame(self.race_results)
        results_df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"✅ CSV保存完了: {output_csv}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Phase 10: バックテスト・シミュレーター',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--venue', type=str, default='名古屋', help='競馬場名')
    parser.add_argument('--start-date', type=str, default='2024-01-01', help='開始日（YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str, default='2024-12-31', help='終了日（YYYY-MM-DD）')
    parser.add_argument('--initial-bankroll', type=int, default=100000, help='初期資金（円）')
    parser.add_argument('--kelly-fraction', type=float, default=0.25, help='Kelly比率')
    
    args = parser.parse_args()
    
    # パラメータ表示
    print("=" * 80)
    print("Phase 10: バックテスト・シミュレーター")
    print("=" * 80)
    print(f"競馬場: {args.venue}")
    print(f"期間: {args.start_date} ～ {args.end_date}")
    print(f"初期資金: {args.initial_bankroll:,}円")
    print(f"Kelly比率: {args.kelly_fraction}")
    
    # 出力ファイル名
    start_fmt = args.start_date.replace('-', '')
    end_fmt = args.end_date.replace('-', '')
    
    output_dir = project_root / 'data' / 'backtest'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_json = str(output_dir / f"{args.venue}_{start_fmt}_{end_fmt}_report.json")
    output_csv = str(output_dir / f"{args.venue}_{start_fmt}_{end_fmt}_summary.csv")
    output_png = str(output_dir / f"{args.venue}_{start_fmt}_{end_fmt}_performance.png")
    
    # ============================================
    # Phase 10: バックテスト実行
    # ============================================
    
    # シミュレーター初期化
    simulator = BacktestSimulator(
        initial_bankroll=args.initial_bankroll,
        kelly_fraction=args.kelly_fraction
    )
    
    # [1/5] 過去データ読み込み
    historical_data = simulator.load_historical_data(args.venue, args.start_date, args.end_date)
    
    # [2/5] バックテスト実行
    backtest_result = simulator.run_backtest(historical_data)
    
    # [3/5] 統計情報計算
    statistics = simulator.calculate_statistics()
    
    # [4/5] パフォーマンスグラフ作成
    simulator.visualize_performance(output_png)
    
    # [5/5] レポート保存
    simulator.save_report(backtest_result, statistics, output_json, output_csv)
    
    # 完了
    print("\n" + "=" * 80)
    print("✅ Phase 10: バックテスト完了")
    print("=" * 80)
    print(f"\n総合成績:")
    print(f"  - 回収率: {backtest_result['recovery_rate'] * 100:.1f}%")
    print(f"  - 的中率: {statistics['hit_rate'] * 100:.1f}%")
    print(f"  - 総利益: {backtest_result['total_profit']:,.0f}円")
    print(f"  - 最終資金: {backtest_result['final_bankroll']:,.0f}円")


if __name__ == '__main__':
    main()
