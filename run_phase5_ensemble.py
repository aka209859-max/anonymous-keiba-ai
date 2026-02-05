#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_phase5_ensemble.py
Phase 5: アンサンブル統合の一括実行スクリプト

Phase 3/4/4回帰の予測結果を統合し、買い目を生成、バックテストを実行
"""

import sys
from pathlib import Path
from ensemble_predictor import EnsemblePredictor
from betting_strategy import BettingStrategy
from backtesting_engine import BacktestingEngine


def run_phase5_ensemble(
    binary_pred_path: str,
    ranking_pred_path: str,
    regression_pred_path: str,
    test_csv_path: str,
    output_dir: str = "predictions/phase5_ooi_test"
):
    """
    Phase 5 アンサンブル統合を一括実行
    
    Args:
        binary_pred_path: Phase 3 二値分類予測結果のパス
        ranking_pred_path: Phase 4 ランキング予測結果のパス
        regression_pred_path: Phase 4 回帰予測結果のパス
        test_csv_path: テストデータのパス（実際の着順付き）
        output_dir: 出力ディレクトリ
    """
    print("\n" + "="*80)
    print("🚀 Phase 5: アンサンブル統合システム 一括実行開始")
    print("="*80)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Step 1: アンサンブル予測
    print("\n" + "-"*80)
    print("Step 1: アンサンブル予測")
    print("-"*80)
    
    ensemble_output = output_path / "ensemble_prediction.csv"
    predictor = EnsemblePredictor(
        weight_phase3=0.3,
        weight_phase4_ranking=0.5,
        weight_phase4_regression=0.2
    )
    
    ensemble_df = predictor.predict(
        binary_pred_path,
        ranking_pred_path,
        regression_pred_path,
        str(ensemble_output)
    )
    
    # Step 2: 買い目生成
    print("\n" + "-"*80)
    print("Step 2: 買い目生成")
    print("-"*80)
    
    bets_output = output_path / "betting_recommendations.json"
    strategy = BettingStrategy(
        min_confidence_tansho=0.80,
        min_confidence_umaren=0.65,
        min_confidence_wide=0.50,
        max_bet_horses=5
    )
    
    bets = strategy.generate(str(ensemble_output), str(bets_output))
    
    # Step 3: バックテスト評価
    print("\n" + "-"*80)
    print("Step 3: バックテスト評価")
    print("-"*80)
    
    backtest_output = output_path / "backtest_results.json"
    engine = BacktestingEngine(unit_bet=100, max_bet_per_race=10)
    
    results = engine.evaluate(str(bets_output), test_csv_path, str(backtest_output))
    
    # 最終サマリー
    print("\n" + "="*80)
    print("🎉 Phase 5: アンサンブル統合システム 実行完了")
    print("="*80)
    
    print("\n📊 最終結果サマリー")
    print("-"*80)
    print(f"✅ アンサンブル予測: {len(ensemble_df)}件")
    print(f"   - Sランク: {(ensemble_df['rank'] == 'S').sum()}頭")
    print(f"   - Aランク: {(ensemble_df['rank'] == 'A').sum()}頭")
    print(f"   - Bランク: {(ensemble_df['rank'] == 'B').sum()}頭")
    print(f"   - 平均スコア: {ensemble_df['ensemble_score'].mean():.4f}")
    
    print(f"\n🎫 買い目生成: {len(bets)}レース")
    total_tansho = sum(len(b['bets']['tansho']) for b in bets)
    total_umaren = sum(len(b['bets']['umaren']) for b in bets)
    total_wide = sum(len(b['bets']['wide']) for b in bets)
    total_sanrenpuku = sum(len(b['bets']['sanrenpuku']) for b in bets)
    print(f"   - 単勝: {total_tansho}点")
    print(f"   - 馬連: {total_umaren}点")
    print(f"   - ワイド: {total_wide}点")
    print(f"   - 三連複: {total_sanrenpuku}点")
    
    print(f"\n💰 バックテスト結果")
    print(f"   - 総投資額: {results['total_investment']:,}円")
    print(f"   - 総払戻額: {results['total_payout']:,}円")
    print(f"   - 収支: {results['total_profit']:+,}円")
    print(f"   - 回収率: {results['recovery_rate']:.2f}%")
    print(f"   - 的中率: {results['hit_rate']:.2f}%")
    
    print(f"\n📂 出力ファイル")
    print(f"   - アンサンブル予測: {ensemble_output}")
    print(f"   - 買い目: {bets_output}")
    print(f"   - バックテスト結果: {backtest_output}")
    
    print("\n" + "="*80)
    print("🎊 Phase 5 完全完了！次は Phase 6（Webシステム化）へ")
    print("="*80)
    
    return {
        'ensemble_df': ensemble_df,
        'bets': bets,
        'backtest_results': results
    }


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("使用法: python run_phase5_ensemble.py <binary_pred> <ranking_pred> <regression_pred> <test_csv> [output_dir]")
        print("\n例:")
        print("python run_phase5_ensemble.py \\")
        print("    predictions/phase45_ooi_test/ooi_test_binary_prediction.csv \\")
        print("    predictions/phase45_ooi_test/ooi_test_ranking_prediction.csv \\")
        print("    predictions/phase45_ooi_test/ooi_test_regression_prediction.csv \\")
        print("    csv/test_split/ooi_test.csv \\")
        print("    predictions/phase5_ooi_test")
        sys.exit(1)
    
    binary_pred_path = sys.argv[1]
    ranking_pred_path = sys.argv[2]
    regression_pred_path = sys.argv[3]
    test_csv_path = sys.argv[4]
    output_dir = sys.argv[5] if len(sys.argv) > 5 else "predictions/phase5_ooi_test"
    
    # Phase 5 実行
    results = run_phase5_ensemble(
        binary_pred_path,
        ranking_pred_path,
        regression_pred_path,
        test_csv_path,
        output_dir
    )
