#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ensemble_model.py
地方競馬AI アンサンブル予測プログラム

3つのモデル（二値分類・ランキング・回帰）の予測結果を統合し、
最終的な買い目候補を決定します。

使用法:
    python ensemble_model.py <csvファイル> <binary_model> <ranking_model> <regression_model> [--output output.csv]

引数:
    csvファイル:       予測対象データ（特徴量を含むCSV）
    binary_model:      二値分類モデルファイル（*_model.txt）
    ranking_model:     ランキングモデルファイル（*_ranking_model.txt）
    regression_model:  回帰モデルファイル（*_regression_model.txt）
    --output:          出力ファイル名（デフォルト: ensemble_predictions.csv）

出力:
    - アンサンブル予測結果CSV（総合スコア、各モデルの予測値、推奨度を含む）
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import lightgbm as lgb


def load_models(binary_path, ranking_path, regression_path):
    """3つのモデルを読み込む"""
    print("\n[1/5] モデル読み込み中...")
    
    try:
        binary_model = lgb.Booster(model_file=binary_path)
        print(f"  ✓ 二値分類モデル: {binary_path}")
    except Exception as e:
        print(f"  ✗ エラー: 二値分類モデルの読み込みに失敗: {e}")
        sys.exit(1)
    
    try:
        ranking_model = lgb.Booster(model_file=ranking_path)
        print(f"  ✓ ランキングモデル: {ranking_path}")
    except Exception as e:
        print(f"  ✗ エラー: ランキングモデルの読み込みに失敗: {e}")
        sys.exit(1)
    
    try:
        regression_model = lgb.Booster(model_file=regression_path)
        print(f"  ✓ 回帰モデル: {regression_path}")
    except Exception as e:
        print(f"  ✗ エラー: 回帰モデルの読み込みに失敗: {e}")
        sys.exit(1)
    
    return binary_model, ranking_model, regression_model


def load_data(csv_path):
    """予測対象データを読み込む"""
    print("\n[2/5] データ読み込み中...")
    
    try:
        df = pd.read_csv(csv_path, encoding='shift-jis')
        print(f"  - データ件数: {len(df):,}件")
    except UnicodeDecodeError:
        print("  警告: Shift-JISでの読み込みに失敗。UTF-8で再試行...")
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f"  - データ件数: {len(df):,}件")
    except Exception as e:
        print(f"  エラー: データ読み込みに失敗: {e}")
        sys.exit(1)
    
    return df


def prepare_features(df, model):
    """モデルに必要な特徴量を準備"""
    # モデルの特徴量名を取得
    model_features = model.feature_name()
    
    # 除外カラム（予測に不要な列）
    exclude_cols = ['target', 'race_id', 'umaban', 'ketto_toroku_bango']
    
    # データフレームから特徴量を抽出
    available_features = [f for f in model_features if f in df.columns]
    missing_features = [f for f in model_features if f not in df.columns]
    
    if missing_features:
        print(f"  警告: 以下の特徴量がデータに存在しません: {missing_features[:5]}...")
    
    # 特徴量データを準備
    X = df[available_features].copy()
    
    # 欠損値を平均値で補完
    if X.isnull().any().any():
        X = X.fillna(X.mean())
    
    return X, available_features


def make_predictions(df, binary_model, ranking_model, regression_model):
    """3つのモデルで予測を実行"""
    print("\n[3/5] 予測実行中...")
    
    # 二値分類モデルの予測
    print("  - 二値分類モデルで予測中...")
    X_binary, binary_features = prepare_features(df, binary_model)
    binary_proba = binary_model.predict(X_binary)
    print(f"    予測完了（使用特徴量: {len(binary_features)}個）")
    
    # ランキングモデルの予測
    print("  - ランキングモデルで予測中...")
    X_ranking, ranking_features = prepare_features(df, ranking_model)
    ranking_score = ranking_model.predict(X_ranking)
    print(f"    予測完了（使用特徴量: {len(ranking_features)}個）")
    
    # 回帰モデルの予測
    print("  - 回帰モデルで予測中...")
    X_regression, regression_features = prepare_features(df, regression_model)
    regression_time = regression_model.predict(X_regression)
    print(f"    予測完了（使用特徴量: {len(regression_features)}個）")
    
    return binary_proba, ranking_score, regression_time


def calculate_ensemble_score(binary_proba, ranking_score, regression_time, 
                             weights={'binary': 0.3, 'ranking': 0.5, 'regression': 0.2}):
    """アンサンブルスコアを計算"""
    print("\n[4/5] アンサンブルスコア計算中...")
    
    # 各予測値を0-1の範囲に正規化
    binary_norm = binary_proba  # 既に0-1の確率値
    
    ranking_norm = (ranking_score - ranking_score.min()) / (ranking_score.max() - ranking_score.min() + 1e-10)
    
    # 回帰（タイム予測）は小さい方が良いので反転
    regression_norm = 1 - ((regression_time - regression_time.min()) / (regression_time.max() - regression_time.min() + 1e-10))
    
    # 加重平均で総合スコアを計算
    ensemble_score = (
        weights['binary'] * binary_norm +
        weights['ranking'] * ranking_norm +
        weights['regression'] * regression_norm
    )
    
    print(f"  - 重み設定: 二値分類={weights['binary']}, ランキング={weights['ranking']}, 回帰={weights['regression']}")
    print(f"  - スコア範囲: {ensemble_score.min():.4f} ~ {ensemble_score.max():.4f}")
    
    return ensemble_score, binary_norm, ranking_norm, regression_norm


def assign_recommendation(ensemble_score, binary_proba, threshold_binary=0.4):
    """推奨度を割り当て"""
    recommendations = []
    
    for score, proba in zip(ensemble_score, binary_proba):
        if proba < threshold_binary:
            # 二値分類の確率が低い場合は除外
            recommendations.append('消去')
        elif score >= 0.7:
            recommendations.append('◎ 本命')
        elif score >= 0.6:
            recommendations.append('○ 対抗')
        elif score >= 0.5:
            recommendations.append('▲ 単穴')
        elif score >= 0.4:
            recommendations.append('△ 連下')
        else:
            recommendations.append('× 評価低')
    
    return recommendations


def save_results(df, predictions, output_path):
    """予測結果を保存"""
    print("\n[5/5] 結果保存中...")
    
    result_df = df.copy()
    
    # 予測結果を追加
    result_df['binary_proba'] = predictions['binary_proba']
    result_df['ranking_score'] = predictions['ranking_score']
    result_df['regression_time'] = predictions['regression_time']
    result_df['binary_norm'] = predictions['binary_norm']
    result_df['ranking_norm'] = predictions['ranking_norm']
    result_df['regression_norm'] = predictions['regression_norm']
    result_df['ensemble_score'] = predictions['ensemble_score']
    result_df['recommendation'] = predictions['recommendation']
    
    # ensemble_scoreでソート
    result_df = result_df.sort_values('ensemble_score', ascending=False)
    
    # 保存
    try:
        result_df.to_csv(output_path, index=False, encoding='shift-jis')
        print(f"  ✓ 保存完了: {output_path}")
        print(f"  - 出力件数: {len(result_df):,}件")
    except Exception as e:
        print(f"  ✗ エラー: 保存に失敗: {e}")
        # UTF-8で再試行
        try:
            result_df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"  ✓ UTF-8で保存完了: {output_path}")
        except Exception as e2:
            print(f"  ✗ エラー: UTF-8での保存も失敗: {e2}")
    
    return result_df


def print_summary(result_df):
    """予測結果のサマリーを表示"""
    print("\n" + "=" * 80)
    print("アンサンブル予測結果サマリー")
    print("=" * 80)
    
    print("\n【推奨度別の分布】")
    recommendation_counts = result_df['recommendation'].value_counts()
    for rec, count in recommendation_counts.items():
        print(f"  {rec}: {count:,}件 ({count/len(result_df)*100:.1f}%)")
    
    print("\n【各モデルの統計】")
    print(f"  二値分類 確率: 平均={result_df['binary_proba'].mean():.4f}, 最大={result_df['binary_proba'].max():.4f}")
    print(f"  ランキング スコア: 平均={result_df['ranking_score'].mean():.2f}, 最大={result_df['ranking_score'].max():.2f}")
    print(f"  回帰 予測値: 平均={result_df['regression_time'].mean():.2f}, 最小={result_df['regression_time'].min():.2f}")
    print(f"  総合スコア: 平均={result_df['ensemble_score'].mean():.4f}, 最大={result_df['ensemble_score'].max():.4f}")
    
    print("\n【Top 10（総合スコア順）】")
    top_cols = ['ensemble_score', 'binary_proba', 'ranking_score', 'regression_time', 'recommendation']
    if 'umaban' in result_df.columns:
        top_cols = ['umaban'] + top_cols
    
    print(result_df[top_cols].head(10).to_string(index=False))
    
    print("\n" + "=" * 80)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='地方競馬AI アンサンブル予測プログラム',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('csv_file', help='予測対象データCSVファイル')
    parser.add_argument('binary_model', help='二値分類モデルファイル')
    parser.add_argument('ranking_model', help='ランキングモデルファイル')
    parser.add_argument('regression_model', help='回帰モデルファイル')
    parser.add_argument('--output', '-o', default='ensemble_predictions.csv', 
                       help='出力ファイル名（デフォルト: ensemble_predictions.csv）')
    parser.add_argument('--binary-weight', type=float, default=0.3,
                       help='二値分類の重み（デフォルト: 0.3）')
    parser.add_argument('--ranking-weight', type=float, default=0.5,
                       help='ランキングの重み（デフォルト: 0.5）')
    parser.add_argument('--regression-weight', type=float, default=0.2,
                       help='回帰の重み（デフォルト: 0.2）')
    parser.add_argument('--threshold', type=float, default=0.4,
                       help='二値分類の閾値（デフォルト: 0.4）')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("地方競馬AI アンサンブル予測プログラム")
    print("=" * 80)
    print(f"\n入力ファイル: {args.csv_file}")
    print(f"二値分類モデル: {args.binary_model}")
    print(f"ランキングモデル: {args.ranking_model}")
    print(f"回帰モデル: {args.regression_model}")
    print(f"出力ファイル: {args.output}")
    
    # モデル読み込み
    binary_model, ranking_model, regression_model = load_models(
        args.binary_model, args.ranking_model, args.regression_model
    )
    
    # データ読み込み
    df = load_data(args.csv_file)
    
    # 予測実行
    binary_proba, ranking_score, regression_time = make_predictions(
        df, binary_model, ranking_model, regression_model
    )
    
    # アンサンブルスコア計算
    weights = {
        'binary': args.binary_weight,
        'ranking': args.ranking_weight,
        'regression': args.regression_weight
    }
    ensemble_score, binary_norm, ranking_norm, regression_norm = calculate_ensemble_score(
        binary_proba, ranking_score, regression_time, weights
    )
    
    # 推奨度を割り当て
    recommendation = assign_recommendation(ensemble_score, binary_proba, args.threshold)
    
    # 予測結果をまとめる
    predictions = {
        'binary_proba': binary_proba,
        'ranking_score': ranking_score,
        'regression_time': regression_time,
        'binary_norm': binary_norm,
        'ranking_norm': ranking_norm,
        'regression_norm': regression_norm,
        'ensemble_score': ensemble_score,
        'recommendation': recommendation
    }
    
    # 結果保存
    result_df = save_results(df, predictions, args.output)
    
    # サマリー表示
    print_summary(result_df)
    
    print("\nアンサンブル予測完了！")


if __name__ == "__main__":
    main()
