#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
モデルファイルの情報確認スクリプト

使用方法:
    python check_model_target.py <model_file>

例:
    python check_model_target.py models/regression/kawasaki_2020-2025_v3_time_regression_model.txt
"""

import lightgbm as lgb
import sys

def main():
    if len(sys.argv) < 2:
        print("使用方法: python check_model_target.py <model_file>")
        print("例: python check_model_target.py models/regression/kawasaki_2020-2025_v3_time_regression_model.txt")
        sys.exit(1)

    model_path = sys.argv[1]

    try:
        # モデル読み込み
        print(f"モデル読み込み中: {model_path}")
        model = lgb.Booster(model_file=model_path)
        
        print("\n" + "=" * 80)
        print("モデル情報")
        print("=" * 80)
        
        # 特徴量名
        feature_names = model.feature_name()
        print(f"\n✅ 特徴量数: {len(feature_names)}")
        print(f"\n特徴量リスト (最初の20個):")
        for i, name in enumerate(feature_names[:20], 1):
            print(f"  {i:2d}. {name}")
        
        if len(feature_names) > 20:
            print(f"  ... (残り {len(feature_names) - 20} 個)")
        
        # 特徴量の重要度 (Gain)
        print(f"\n✅ 特徴量重要度 (Gain) Top 10:")
        importance_dict = model.feature_importance(importance_type='gain')
        feature_importance = [(name, importance_dict[i]) for i, name in enumerate(feature_names)]
        feature_importance_sorted = sorted(feature_importance, key=lambda x: x[1], reverse=True)
        
        for i, (name, importance) in enumerate(feature_importance_sorted[:10], 1):
            print(f"  {i:2d}. {name:30s} : {importance:12.2f}")
        
        # モデルのパラメータ
        params = model.params
        print(f"\n✅ モデルパラメータ:")
        important_params = ['objective', 'metric', 'num_leaves', 'learning_rate', 'feature_fraction', 'bagging_fraction']
        for key in important_params:
            if key in params:
                print(f"  {key:20s}: {params[key]}")
        
        # 木の数
        print(f"\n✅ ブースティングラウンド数: {model.num_trees()}")
        
        print("\n" + "=" * 80)
        print("⚠️  重要な注意")
        print("=" * 80)
        print("target列の統計量 (平均値、最小値、最大値) はモデルファイルに保存されていません。")
        print("学習時のCSVファイルまたは学習ログファイルを確認する必要があります。")
        print("\n以下のファイルを探してください:")
        print("  1. 学習ログ: models/regression/kawasaki_2020-2025_v3_time_regression_score.txt")
        print("  2. 学習データCSV: csv/川崎_2020-2025_v3_training_data.csv")
        print("=" * 80)
        
    except FileNotFoundError:
        print(f"❌ エラー: ファイルが見つかりません: {model_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
