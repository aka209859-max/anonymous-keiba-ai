#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4-1: ランキング予測スクリプト（距離カテゴリ対応）

学習済みモデルを使って新規データの順位予測を実行
距離カテゴリ（SHORT/MILE/LONG）ごとのモデルを自動選択
"""

import sys
import os
import pandas as pd
import numpy as np
import lightgbm as lgb
import argparse
import warnings
warnings.filterwarnings('ignore')

def get_distance_category(kyori):
    """距離からカテゴリを判定"""
    if kyori <= 1200:
        return 'SHORT'
    elif kyori <= 1700:
        return 'MILE'
    else:
        return 'LONG'

def predict_ranking(input_csv, model_dir, output_path, keibajo_name=None):
    """
    ランキング予測を実行
    
    Parameters
    ----------
    input_csv : str
        予測対象データ（67特徴量変換済み）
    model_dir : str
        学習済みモデルディレクトリ
    output_path : str
        予測結果の出力先
    keibajo_name : str, optional
        競馬場名（自動検出する場合はNone）
    """
    print(f"\n{'='*80}")
    print(f"Phase 4-1: ランキング予測（距離カテゴリ対応）")
    print(f"{'='*80}")
    
    # データ読み込み
    print(f"\n[1/4] データ読み込み: {os.path.basename(input_csv)}")
    try:
        df = pd.read_csv(input_csv, encoding='shift-jis')
    except:
        df = pd.read_csv(input_csv, encoding='utf-8')
    
    print(f"  ✅ レコード数: {len(df)}件")
    print(f"  ✅ カラム数: {len(df.columns)}個")
    
    # 競馬場名の自動検出
    if keibajo_name is None:
        basename = os.path.basename(input_csv)
        keibajo_name = basename.split('_')[0]
    
    print(f"  ✅ 競馬場: {keibajo_name}")
    
    # 距離カテゴリの追加
    if 'kyori' not in df.columns:
        print(f"\n❌ エラー: 'kyori'列が見つかりません")
        sys.exit(1)
    
    df['distance_category'] = df['kyori'].apply(get_distance_category)
    
    print(f"\n  距離カテゴリ別内訳:")
    for cat in ['SHORT', 'MILE', 'LONG']:
        count = len(df[df['distance_category'] == cat])
        if count > 0:
            print(f"    - {cat}: {count}件")
    
    # race_idの生成
    if 'race_id' not in df.columns:
        df['race_id'] = (
            df['kaisai_nen'].astype(str) + '_' +
            df['kaisai_tsukihi'].astype(str) + '_' +
            df['keibajo_code'].astype(str).str.zfill(2) + '_' +
            df['race_bango'].astype(str).str.zfill(2)
        )
    
    # 除外列（学習時と同じ）
    exclude_cols = [
        'target', 'rank_target', 'time', 'kakutei_chacujun', 'race_id',
        'waku_bango', 'futan_juryo', 'bataijyu', 'zogensa', 'zogensa_fugo',
        'kaisai_kaime', 'kaisai_nichime', 'race_bangou',
        'grade_code', 'baba_jotai_code',
        'distance_category'
    ]
    
    # 予測実行
    print(f"\n[2/4] 予測実行（距離カテゴリ別）")
    
    predictions = []
    
    for cat in ['SHORT', 'MILE', 'LONG']:
        cat_data = df[df['distance_category'] == cat].copy()
        
        if len(cat_data) == 0:
            print(f"  ⏭️  {cat}: データなし - スキップ")
            continue
        
        # モデルファイルパス
        model_filename = f"{keibajo_name}_{cat}_ranking_model.txt"
        model_path = os.path.join(model_dir, model_filename)
        
        if not os.path.exists(model_path):
            print(f"  ❌ {cat}: モデルファイルが見つかりません: {model_filename}")
            continue
        
        # モデル読み込み
        try:
            model = lgb.Booster(model_file=model_path)
            print(f"  ✅ {cat}: モデル読み込み成功 ({len(cat_data)}件)")
        except Exception as e:
            print(f"  ❌ {cat}: モデル読み込みエラー: {e}")
            continue
        
        # 特徴量準備
        feature_cols = [col for col in cat_data.columns if col not in exclude_cols]
        X = cat_data[feature_cols].copy()
        
        # 欠損値を0で埋める（学習時と同じ）
        X = X.fillna(0)
        
        # 予測
        try:
            ranking_scores = model.predict(X)
            
            # 結果を格納
            cat_data['ranking_score'] = ranking_scores
            
            # レース内順位を計算
            cat_data['predicted_rank'] = cat_data.groupby('race_id')['ranking_score'].rank(
                ascending=False, method='min'
            ).astype(int)
            
            predictions.append(cat_data)
            
            # 統計表示
            avg_score = ranking_scores.mean()
            top1_count = (cat_data['predicted_rank'] == 1).sum()
            top3_count = (cat_data['predicted_rank'] <= 3).sum()
            
            print(f"       - 平均スコア: {avg_score:.4f}")
            print(f"       - 1位予測: {top1_count}件")
            print(f"       - TOP3予測: {top3_count}件")
            
        except Exception as e:
            print(f"  ❌ {cat}: 予測エラー: {e}")
            continue
    
    # 結果結合
    print(f"\n[3/4] 結果結合")
    
    if len(predictions) == 0:
        print(f"  ❌ エラー: 全ての距離カテゴリで予測に失敗しました")
        sys.exit(1)
    
    result_df = pd.concat(predictions, ignore_index=True)
    
    print(f"  ✅ 結合後レコード数: {len(result_df)}件")
    
    # 出力列の選択
    output_cols = [
        'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
        'umaban', 'ketto_toroku_bango', 'kyori', 'distance_category',
        'ranking_score', 'predicted_rank'
    ]
    
    # 存在するカラムのみ選択
    output_cols = [col for col in output_cols if col in result_df.columns]
    result_df = result_df[output_cols].copy()
    
    # 結果保存
    print(f"\n[4/4] 結果保存")
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        result_df.to_csv(output_path, index=False, encoding='shift-jis')
        print(f"  ✅ 保存完了（Shift-JIS）: {output_path}")
    except:
        output_path_utf8 = output_path.replace('.csv', '_utf8.csv')
        result_df.to_csv(output_path_utf8, index=False, encoding='utf-8')
        print(f"  ✅ 保存完了（UTF-8）: {output_path_utf8}")
        output_path = output_path_utf8
    
    print(f"  - レコード数: {len(result_df):,}件")
    print(f"  - カラム数: {len(result_df.columns)}個")
    
    # サマリー表示
    print(f"\n  【予測サマリー】")
    
    # レースごとの1位予測
    top1_predictions = result_df[result_df['predicted_rank'] == 1].sort_values('race_id')
    print(f"    - 全体レース数: {result_df['race_id'].nunique()}件")
    print(f"    - 1位予測頭数: {len(top1_predictions)}件")
    
    # 距離カテゴリ別統計
    for cat in ['SHORT', 'MILE', 'LONG']:
        cat_data = result_df[result_df['distance_category'] == cat]
        if len(cat_data) > 0:
            cat_races = cat_data['race_id'].nunique()
            cat_avg_score = cat_data['ranking_score'].mean()
            cat_top3 = (cat_data['predicted_rank'] <= 3).sum()
            print(f"    - {cat}: {cat_races}レース, 平均スコア={cat_avg_score:.4f}, TOP3={cat_top3}件")
    
    # レース別TOP3表示（最初の3レースのみ）
    print(f"\n  【レース別TOP3予測（最初の3レース）】")
    for idx, race_id in enumerate(sorted(result_df['race_id'].unique())[:3], 1):
        race_data = result_df[result_df['race_id'] == race_id].sort_values('predicted_rank')
        top3 = race_data.head(3)
        
        print(f"\n  {idx}. レース{race_id}:")
        for _, row in top3.iterrows():
            print(f"      {int(row['predicted_rank'])}位: {int(row['umaban'])}番 "
                  f"({row['distance_category']}) - スコア: {row['ranking_score']:.4f}")
    
    return result_df

def main():
    parser = argparse.ArgumentParser(
        description='Phase 4-1: ランキング予測（距離カテゴリ対応）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python predict_ranking_distance.py \\
    --input data/test/urawa_20250207_67features.csv \\
    --models models/ranking_distance \\
    --output data/predictions/ranking/urawa_20250207_ranking.csv \\
    --keibajo urawa
        """
    )
    
    parser.add_argument('--input', required=True, help='予測対象データ（67特徴量変換済みCSV）')
    parser.add_argument('--models', required=True, help='学習済みモデルディレクトリ')
    parser.add_argument('--output', required=True, help='予測結果の出力先CSV')
    parser.add_argument('--keibajo', default=None, help='競馬場名（自動検出する場合は省略可）')
    
    args = parser.parse_args()
    
    try:
        result_df = predict_ranking(
            args.input, args.models, args.output, args.keibajo
        )
        
        print("\n" + "="*80)
        print("✅ Phase 4-1 ランキング予測完了")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
