#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: 二値分類予測スクリプト（距離カテゴリ対応）

学習済みモデルを使って新規データの予測を実行
距離カテゴリ（SHORT/MILE/LONG）ごとのモデルを自動選択
"""

import sys
import os
import pandas as pd
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

def predict_binary(input_csv, model_dir, output_path, keibajo_name=None):
    """
    二値分類予測を実行
    
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
    print(f"Phase 3: 二値分類予測（距離カテゴリ対応）")
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
    
    # 除外列（学習時と同じ）
    exclude_cols = [
        'target', 'rank_target', 'time', 'kakutei_chacujun',
        'waku_bango', 'futan_juryo', 'bataijyu', 'zogensa', 'zogensa_fugo',
        'kaisai_kaime', 'kaisai_nichime', 'race_bangou',
        'grade_code', 'baba_jotai_code',  # 新規追加
        'distance_category'  # 予測用の補助列
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
        model_filename = f"{keibajo_name}_{cat}_binary_model.txt"
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
            y_pred_proba = model.predict(X)
            y_pred_class = (y_pred_proba >= 0.5).astype(int)
            
            # 結果を格納
            cat_data['binary_probability'] = y_pred_proba
            cat_data['predicted_class'] = y_pred_class
            
            predictions.append(cat_data)
            
            # 統計表示
            top3_pred = (y_pred_class == 1).sum()
            top3_rate = top3_pred / len(cat_data) * 100
            avg_prob = y_pred_proba.mean()
            
            print(f"       - TOP3予測: {top3_pred}件 ({top3_rate:.1f}%)")
            print(f"       - 平均確率: {avg_prob:.4f}")
            
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
    
    # race_idの生成
    if 'race_id' not in result_df.columns:
        result_df['race_id'] = (
            result_df['kaisai_nen'].astype(str) + '_' +
            result_df['kaisai_tsukihi'].astype(str) + '_' +
            result_df['keibajo_code'].astype(str).str.zfill(2) + '_' +
            result_df['race_bango'].astype(str).str.zfill(2)
        )
    
    # 出力列の選択
    output_cols = [
        'race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango',
        'umaban', 'ketto_toroku_bango', 'kyori', 'distance_category',
        'binary_probability', 'predicted_class'
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
    total_top3 = (result_df['predicted_class'] == 1).sum()
    total_rate = total_top3 / len(result_df) * 100
    avg_prob = result_df['binary_probability'].mean()
    
    print(f"    - 全体TOP3予測数: {total_top3}件 ({total_rate:.1f}%)")
    print(f"    - 平均確率: {avg_prob:.4f}")
    
    for cat in ['SHORT', 'MILE', 'LONG']:
        cat_data = result_df[result_df['distance_category'] == cat]
        if len(cat_data) > 0:
            cat_top3 = (cat_data['predicted_class'] == 1).sum()
            cat_rate = cat_top3 / len(cat_data) * 100
            cat_prob = cat_data['binary_probability'].mean()
            print(f"    - {cat}: TOP3={cat_top3}/{len(cat_data)}件 ({cat_rate:.1f}%), 平均確率={cat_prob:.4f}")
    
    return result_df

def main():
    parser = argparse.ArgumentParser(
        description='Phase 3: 二値分類予測（距離カテゴリ対応）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python predict_binary_distance.py \\
    --input data/test/urawa_20250207_67features.csv \\
    --models models/binary_distance \\
    --output data/predictions/binary/urawa_20250207_binary.csv \\
    --keibajo urawa
        """
    )
    
    parser.add_argument('--input', required=True, help='予測対象データ（67特徴量変換済みCSV）')
    parser.add_argument('--models', required=True, help='学習済みモデルディレクトリ')
    parser.add_argument('--output', required=True, help='予測結果の出力先CSV')
    parser.add_argument('--keibajo', default=None, help='競馬場名（自動検出する場合は省略可）')
    
    args = parser.parse_args()
    
    try:
        result_df = predict_binary(
            args.input, args.models, args.output, args.keibajo
        )
        
        print("\n" + "="*80)
        print("✅ Phase 3 二値分類予測完了")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
