#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4-2 回帰予測結果の分析スクリプト

予測された走破時間が異常に大きい原因を特定します。
"""

import pandas as pd
import sys

def main():
    if len(sys.argv) < 2:
        print("使用方法: python analyze_prediction_results.py <prediction_csv>")
        print("例: python analyze_prediction_results.py data/predictions/phase4_regression/川崎_20260205_phase4_regression.csv")
        sys.exit(1)
    
    prediction_file = sys.argv[1]
    
    print("=" * 80)
    print("Phase 4-2 回帰予測結果の分析")
    print("=" * 80)
    
    # データ読み込み
    try:
        df = pd.read_csv(prediction_file, encoding='shift-jis')
        print(f"\n✅ ファイル読み込み成功: {prediction_file}")
    except UnicodeDecodeError:
        df = pd.read_csv(prediction_file, encoding='utf-8')
        print(f"\n✅ ファイル読み込み成功 (UTF-8): {prediction_file}")
    
    print(f"   データ件数: {len(df)} 件")
    print(f"   カラム数: {len(df.columns)} 個")
    print(f"   カラム: {list(df.columns)}")
    
    # 予測時間の統計
    print("\n" + "=" * 80)
    print("予測時間 (predicted_time) の統計")
    print("=" * 80)
    
    stats = df['predicted_time'].describe()
    print(f"\n件数 (count)   : {stats['count']:.0f}")
    print(f"平均 (mean)    : {stats['mean']:.2f} 秒 = {stats['mean']/60:.2f} 分")
    print(f"標準偏差 (std) : {stats['std']:.2f} 秒")
    print(f"最小値 (min)   : {stats['min']:.2f} 秒 = {stats['min']/60:.2f} 分")
    print(f"25%点          : {stats['25%']:.2f} 秒")
    print(f"中央値 (50%)   : {stats['50%']:.2f} 秒 = {stats['50%']/60:.2f} 分")
    print(f"75%点          : {stats['75%']:.2f} 秒")
    print(f"最大値 (max)   : {stats['max']:.2f} 秒 = {stats['max']/60:.2f} 分")
    
    # 正常範囲の定義 (55秒〜130秒)
    normal_min = 55
    normal_max = 130
    
    print("\n" + "=" * 80)
    print(f"正常範囲チェック ({normal_min}秒〜{normal_max}秒)")
    print("=" * 80)
    
    normal_count = len(df[(df['predicted_time'] >= normal_min) & (df['predicted_time'] <= normal_max)])
    abnormal_count = len(df) - normal_count
    
    print(f"\n正常範囲内: {normal_count} 件 ({normal_count/len(df)*100:.1f}%)")
    print(f"異常値    : {abnormal_count} 件 ({abnormal_count/len(df)*100:.1f}%)")
    
    # 異常値の詳細
    if abnormal_count > 0:
        print("\n" + "=" * 80)
        print("異常値の詳細")
        print("=" * 80)
        
        abnormal_df = df[(df['predicted_time'] < normal_min) | (df['predicted_time'] > normal_max)]
        print(f"\n異常値のサンプル (最初の10件):")
        print(abnormal_df[['race_id', 'race_bango', 'umaban', 'predicted_time', 'time_rank']].head(10).to_string(index=False))
    
    # 1/10秒単位の仮説検証
    print("\n" + "=" * 80)
    print("仮説検証: 予測値が1/10秒単位である可能性")
    print("=" * 80)
    
    df['predicted_time_divided_10'] = df['predicted_time'] / 10.0
    
    stats_divided = df['predicted_time_divided_10'].describe()
    print(f"\n予測時間 ÷ 10 の統計:")
    print(f"平均 (mean)    : {stats_divided['mean']:.2f} 秒")
    print(f"中央値 (50%)   : {stats_divided['50%']:.2f} 秒")
    print(f"最小値 (min)   : {stats_divided['min']:.2f} 秒")
    print(f"最大値 (max)   : {stats_divided['max']:.2f} 秒")
    
    normal_count_divided = len(df[(df['predicted_time_divided_10'] >= normal_min) & (df['predicted_time_divided_10'] <= normal_max)])
    print(f"\n正常範囲内 ({normal_min}秒〜{normal_max}秒): {normal_count_divided} 件 ({normal_count_divided/len(df)*100:.1f}%)")
    
    # 結論
    print("\n" + "=" * 80)
    print("結論")
    print("=" * 80)
    
    if normal_count_divided > normal_count:
        print("\n✅ 仮説が正しい可能性が高い:")
        print("   予測値は 1/10秒単位 で学習されています。")
        print("   10で割ると正常範囲に収まります。")
        print("\n📋 対策:")
        print("   予測スクリプトを修正して、予測値を 10 で割る処理を追加してください。")
        print("   修正箇所: df['predicted_time'] = predictions / 10.0")
    else:
        print("\n❌ 1/10秒単位の仮説は不正解:")
        print("   別の原因を調査する必要があります。")
        print("\n📋 次のアクション:")
        print("   1. 学習データの target 列を直接確認")
        print("   2. モデル再学習を検討")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
