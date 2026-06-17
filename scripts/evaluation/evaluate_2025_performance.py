#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 7-8モデルの評価スクリプト

旧モデル（Phase 3-4-5）と新モデル（Phase 7-8-5）の精度を比較

使用例:
    python scripts/evaluation/evaluate_2025_performance.py \
        --old-predictions data/predictions/old_model/funabashi_2025_predictions.csv \
        --new-predictions data/predictions/new_model/funabashi_2025_predictions.csv \
        --actuals data/actuals/funabashi_2025_actuals.csv \
        --output-report data/evaluation/funabashi_comparison_report.json
"""

import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
from sklearn.metrics import ndcg_score
from scipy.stats import spearmanr


def load_data(predictions_csv, actuals_csv):
    """
    予測データと実績データを読み込み
    
    Parameters:
    -----------
    predictions_csv : str
        予測結果ファイルパス
    actuals_csv : str
        実績結果ファイルパス
    
    Returns:
    --------
    merged : pd.DataFrame
        マージされたデータ
    """
    # エンコーディングを試行
    encodings = ['shift-jis', 'utf-8', 'cp932']
    
    for enc in encodings:
        try:
            preds = pd.read_csv(predictions_csv, encoding=enc)
            print(f"✅ 予測データ読み込み成功: {predictions_csv} ({enc})")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"❌ 予測データの読み込みに失敗: {predictions_csv}")
    
    for enc in encodings:
        try:
            actuals = pd.read_csv(actuals_csv, encoding=enc)
            print(f"✅ 実績データ読み込み成功: {actuals_csv} ({enc})")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"❌ 実績データの読み込みに失敗: {actuals_csv}")
    
    # マージ
    merged = pd.merge(preds, actuals, on=['race_id', 'umaban'], how='inner', suffixes=('_pred', '_actual'))
    
    print(f"📊 マージ結果: {len(merged)} レコード, {merged['race_id'].nunique()} レース")
    
    return merged


def calculate_hit_rates(merged):
    """
    的中率を計算
    
    Parameters:
    -----------
    merged : pd.DataFrame
        マージされたデータ（final_rank, actual_rank を含む）
    
    Returns:
    --------
    hit_rates : dict
        各種的中率
    """
    total_races = merged['race_id'].nunique()
    
    # 単勝的中率: 予測1位が実際に1着
    win_hits = 0
    for race_id in merged['race_id'].unique():
        race = merged[merged['race_id'] == race_id]
        predicted_1st = race[race['final_rank'] == 1]['umaban'].values
        actual_1st = race[race['actual_rank'] == 1]['umaban'].values
        
        if len(predicted_1st) > 0 and len(actual_1st) > 0:
            if predicted_1st[0] == actual_1st[0]:
                win_hits += 1
    
    hit_rate_win = win_hits / total_races if total_races > 0 else 0
    
    # 複勝的中率: 予測1位が実際に1〜3着
    place_hits = 0
    for race_id in merged['race_id'].unique():
        race = merged[merged['race_id'] == race_id]
        predicted_1st = race[race['final_rank'] == 1]['umaban'].values
        actual_top3 = race[race['actual_rank'] <= 3]['umaban'].values
        
        if len(predicted_1st) > 0:
            if predicted_1st[0] in actual_top3:
                place_hits += 1
    
    hit_rate_place = place_hits / total_races if total_races > 0 else 0
    
    # 馬連的中率: 予測1-2位が実際の1-2着を含む
    quinella_hits = 0
    for race_id in merged['race_id'].unique():
        race = merged[merged['race_id'] == race_id]
        predicted_top2 = set(race[race['final_rank'] <= 2]['umaban'].values)
        actual_top2 = set(race[race['actual_rank'] <= 2]['umaban'].values)
        
        if len(predicted_top2) == 2 and len(actual_top2) == 2:
            if predicted_top2 == actual_top2:
                quinella_hits += 1
    
    hit_rate_quinella = quinella_hits / total_races if total_races > 0 else 0
    
    # 3連複的中率: 予測1-3位が実際の1-3着を含む
    trio_hits = 0
    for race_id in merged['race_id'].unique():
        race = merged[merged['race_id'] == race_id]
        predicted_top3 = set(race[race['final_rank'] <= 3]['umaban'].values)
        actual_top3 = set(race[race['actual_rank'] <= 3]['umaban'].values)
        
        if len(predicted_top3) == 3 and len(actual_top3) == 3:
            if predicted_top3 == actual_top3:
                trio_hits += 1
    
    hit_rate_trio = trio_hits / total_races if total_races > 0 else 0
    
    return {
        'hit_rate_win': hit_rate_win,
        'hit_rate_place': hit_rate_place,
        'hit_rate_quinella': hit_rate_quinella,
        'hit_rate_trio': hit_rate_trio,
        'total_races': total_races
    }


def calculate_ranking_metrics(merged):
    """
    予測精度指標を計算
    
    Parameters:
    -----------
    merged : pd.DataFrame
        マージされたデータ
    
    Returns:
    --------
    metrics : dict
        NDCG@3, MAE, Spearman相関
    """
    ndcg_scores = []
    mae_list = []
    spearman_list = []
    
    for race_id in merged['race_id'].unique():
        race = merged[merged['race_id'] == race_id].copy()
        
        # NDCG@3 計算
        # 真のランキング: 着順が小さいほど良い → relevance scoreに変換
        y_true = []
        for rank in race['actual_rank']:
            if rank <= 3:
                # 1着=3点, 2着=2点, 3着=1点
                y_true.append(4 - rank)
            else:
                y_true.append(0)
        
        y_true = [y_true]  # ndcg_scoreは2D配列を要求
        
        # 予測スコア: ensemble_scoreが高いほど良い
        if 'ensemble_score' in race.columns:
            y_pred = [race['ensemble_score'].tolist()]
        else:
            # ensemble_scoreがない場合はfinal_rankから逆算
            y_pred = [[1.0 / (r + 1) for r in race['final_rank']]]
        
        try:
            ndcg = ndcg_score(y_true, y_pred, k=3)
            ndcg_scores.append(ndcg)
        except:
            pass
        
        # MAE（平均着順誤差）
        mae = np.mean(np.abs(race['final_rank'] - race['actual_rank']))
        mae_list.append(mae)
        
        # スピアマン相関
        try:
            corr, _ = spearmanr(race['final_rank'], race['actual_rank'])
            if not np.isnan(corr):
                spearman_list.append(corr)
        except:
            pass
    
    return {
        'ndcg_3': np.mean(ndcg_scores) if ndcg_scores else 0,
        'mae': np.mean(mae_list) if mae_list else 0,
        'spearman': np.mean(spearman_list) if spearman_list else 0
    }


def evaluate_model(predictions_csv, actuals_csv):
    """
    モデルの予測精度を評価
    
    Parameters:
    -----------
    predictions_csv : str
        予測結果ファイル
    actuals_csv : str
        実績結果ファイル
    
    Returns:
    --------
    metrics : dict
        評価指標の辞書
    """
    # データ読み込み
    merged = load_data(predictions_csv, actuals_csv)
    
    # 的中率
    hit_rates = calculate_hit_rates(merged)
    
    # 予測精度
    ranking_metrics = calculate_ranking_metrics(merged)
    
    # 統合
    metrics = {**hit_rates, **ranking_metrics}
    
    return metrics


def compare_models(old_predictions, new_predictions, actuals, output_report):
    """
    旧モデルと新モデルを比較
    
    Parameters:
    -----------
    old_predictions : str
        旧モデルの予測結果
    new_predictions : str
        新モデルの予測結果
    actuals : str
        実績結果
    output_report : str
        出力レポートパス
    """
    print("=" * 60)
    print("🔍 旧モデル（Phase 3-4-5）の評価")
    print("=" * 60)
    old_metrics = evaluate_model(old_predictions, actuals)
    
    print("\n" + "=" * 60)
    print("🚀 新モデル（Phase 7-8-5）の評価")
    print("=" * 60)
    new_metrics = evaluate_model(new_predictions, actuals)
    
    # 比較レポート
    print("\n" + "=" * 60)
    print("📊 旧モデル vs 新モデル 比較結果")
    print("=" * 60)
    
    comparison = {}
    
    for key in old_metrics:
        if key == 'total_races':
            continue
        
        old_val = old_metrics[key]
        new_val = new_metrics[key]
        
        if old_val > 0:
            improvement = ((new_val - old_val) / old_val) * 100
        else:
            improvement = 0
        
        comparison[key] = {
            'old_model': old_val,
            'new_model': new_val,
            'improvement_pct': improvement
        }
        
        if key.startswith('hit_rate'):
            print(f"{key:20s}: {old_val:6.2%} → {new_val:6.2%} ({improvement:+6.2f}%)")
        else:
            print(f"{key:20s}: {old_val:6.3f} → {new_val:6.3f} ({improvement:+6.2f}%)")
    
    # JSON出力
    output_data = {
        'old_model': old_metrics,
        'new_model': new_metrics,
        'comparison': comparison
    }
    
    output_path = Path(output_report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ レポート保存: {output_report}")


def main():
    parser = argparse.ArgumentParser(description='Phase 7-8モデルの評価')
    parser.add_argument('--old-predictions', required=True, help='旧モデルの予測結果CSV')
    parser.add_argument('--new-predictions', required=True, help='新モデルの予測結果CSV')
    parser.add_argument('--actuals', required=True, help='実績結果CSV')
    parser.add_argument('--output-report', required=True, help='出力レポートJSON')
    
    args = parser.parse_args()
    
    compare_models(
        args.old_predictions,
        args.new_predictions,
        args.actuals,
        args.output_report
    )


if __name__ == '__main__':
    main()
