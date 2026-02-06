#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_phase5_ooi_2025.py
大井2025年 Phase 5 アンサンブル統合の完全実行スクリプト

このスクリプトは以下を実行します:
1. Phase 3 二値分類予測
2. Phase 4 ランキング予測  
3. Phase 4 回帰予測（既に完了済み）
4. Phase 5 アンサンブル統合
5. 買い目生成
6. バックテスト実行
"""

import sys
import os
from pathlib import Path
import pandas as pd
import lightgbm as lgb
import numpy as np
from datetime import datetime


def predict_phase3_binary(test_csv: str, model_path: str, output_csv: str):
    """Phase 3 二値分類予測"""
    print("\n" + "="*80)
    print("Step 1/6: Phase 3 二値分類予測")
    print("="*80)
    
    # モデル読み込み
    print(f"📥 モデル読み込み中: {model_path}")
    model = lgb.Booster(model_file=model_path)
    
    # モデルの特徴量を取得
    model_features = model.feature_name()
    print(f"🔑 モデル特徴量数: {len(model_features)}")
    
    # テストデータ読み込み
    print(f"📥 テストデータ読み込み中: {test_csv}")
    try:
        df = pd.read_csv(test_csv, encoding='shift_jis')
    except:
        df = pd.read_csv(test_csv, encoding='utf-8')
    
    print(f"✅ データ件数: {len(df):,}件")
    
    # 特徴量準備
    id_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 
               'ketto_toroku_bango', 'umaban']
    
    # モデルの特徴量に合わせる
    missing_features = []
    for feat in model_features:
        if feat not in df.columns:
            missing_features.append(feat)
            df[feat] = 0  # 欠損している特徴量は0で補完
    
    if missing_features:
        print(f"⚠️  欠損特徴量を0で補完: {len(missing_features)}個")
    
    # モデルの特徴量順で並び替え
    X = df[model_features].copy()
    
    # 欠損値補完
    X = X.fillna(X.mean())
    
    # 予測実行
    print(f"🔮 予測実行中... (特徴量数: {len(model_features)})")
    predictions = model.predict(X)
    
    # 結果保存
    result_df = df[id_cols].copy()
    result_df['binary_probability'] = predictions
    result_df['predicted_class'] = (predictions >= 0.5).astype(int)
    
    result_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"✅ 予測結果保存: {output_csv}")
    print(f"   - 入線確率 平均: {predictions.mean():.4f}")
    print(f"   - 入線予測数: {result_df['predicted_class'].sum()}頭")
    
    return result_df


def predict_phase4_ranking(test_csv: str, model_path: str, output_csv: str):
    """Phase 4 ランキング予測"""
    print("\n" + "="*80)
    print("Step 2/6: Phase 4 ランキング予測")
    print("="*80)
    
    # モデル読み込み
    print(f"📥 モデル読み込み中: {model_path}")
    model = lgb.Booster(model_file=model_path)
    
    # モデルの特徴量を取得
    model_features = model.feature_name()
    print(f"🔑 モデル特徴量数: {len(model_features)}")
    
    # テストデータ読み込み
    print(f"📥 テストデータ読み込み中: {test_csv}")
    try:
        df = pd.read_csv(test_csv, encoding='shift_jis')
    except:
        df = pd.read_csv(test_csv, encoding='utf-8')
    
    print(f"✅ データ件数: {len(df):,}件")
    
    # 特徴量準備
    id_cols = ['kaisai_yen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 
               'ketto_toroku_bango', 'umaban', 'race_id']
    
    # 実際に存在するID列のみ使用
    existing_id_cols = [col for col in id_cols if col in df.columns]
    
    # モデルの特徴量に合わせる
    missing_features = []
    for feat in model_features:
        if feat not in df.columns:
            missing_features.append(feat)
            df[feat] = 0  # 欠損している特徴量は0で補完
    
    if missing_features:
        print(f"⚠️  欠損特徴量を0で補完: {len(missing_features)}個")
    
    # モデルの特徴量順で並び替え
    X = df[model_features].copy()
    
    # 欠損値補完
    X = X.fillna(X.mean())
    
    # 予測実行
    print(f"🔮 予測実行中... (特徴量数: {len(model_features)})")
    predictions = model.predict(X)
    
    # Min-Max正規化 (0-1範囲に変換)
    predictions_min = predictions.min()
    predictions_max = predictions.max()
    ranking_score = (predictions - predictions_min) / (predictions_max - predictions_min + 1e-10)
    
    # 結果保存
    result_df = df[existing_id_cols].copy()
    result_df['ranking_prediction'] = predictions
    result_df['ranking_score'] = ranking_score
    
    result_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"✅ 予測結果保存: {output_csv}")
    print(f"   - ランキングスコア 平均: {ranking_score.mean():.4f}")
    print(f"   - 最小値: {ranking_score.min():.4f}, 最大値: {ranking_score.max():.4f}")
    
    return result_df


def ensemble_integration(binary_csv: str, ranking_csv: str, regression_csv: str, 
                        output_csv: str, weights: dict = None):
    """Phase 5 アンサンブル統合"""
    print("\n" + "="*80)
    print("Step 3/6: Phase 5 アンサンブル統合")
    print("="*80)
    
    # デフォルトウェイト
    if weights is None:
        weights = {'binary': 0.3, 'ranking': 0.5, 'regression': 0.2}
    
    print(f"📊 ウェイト設定:")
    print(f"   - 二値分類: {weights['binary']:.1%}")
    print(f"   - ランキング: {weights['ranking']:.1%}")
    print(f"   - 回帰予測: {weights['regression']:.1%}")
    
    # データ読み込み
    print("\n📥 予測結果読み込み中...")
    df_binary = pd.read_csv(binary_csv)
    df_ranking = pd.read_csv(ranking_csv)
    df_regression = pd.read_csv(regression_csv)
    
    print(f"   - 二値分類: {len(df_binary):,}件")
    print(f"   - ランキング: {len(df_ranking):,}件")
    print(f"   - 回帰予測: {len(df_regression):,}件")
    
    # マージキー作成 (kaisai_nenがない場合に対応)
    if 'kaisai_nen' in df_binary.columns and 'kaisai_nen' in df_ranking.columns and 'kaisai_nen' in df_regression.columns:
        merge_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 
                      'ketto_toroku_bango', 'umaban']
    else:
        merge_cols = ['kaisai_tsukihi', 'keibajo_code', 'race_bango', 
                      'ketto_toroku_bango', 'umaban']
    
    print(f"🔑 マージキー: {merge_cols}")
    
    # データ統合
    print("\n🔗 データ統合中...")
    df = df_binary.copy()
    
    # ランキングをマージ
    df = df.merge(df_ranking[merge_cols + ['ranking_score']], 
                  on=merge_cols, how='left')
    
    # 回帰をマージ
    df = df.merge(df_regression[merge_cols + ['regression_score']], 
                  on=merge_cols, how='left')
    
    # 欠損値を0で補完
    df['ranking_score'] = df['ranking_score'].fillna(0)
    df['regression_score'] = df['regression_score'].fillna(0)
    
    # アンサンブルスコア計算
    print("\n🧮 アンサンブルスコア計算中...")
    df['ensemble_score'] = (
        weights['binary'] * df['binary_probability'] +
        weights['ranking'] * df['ranking_score'] +
        weights['regression'] * df['regression_score']
    )
    
    # ランク付け (レース内での順位)
    print("\n🏆 ランク付け実行中...")
    if 'kaisai_nen' in df.columns:
        df['race_key'] = (df['kaisai_nen'].astype(str) + '_' + 
                          df['kaisai_tsukihi'].astype(str) + '_' + 
                          df['keibajo_code'].astype(str) + '_' + 
                          df['race_bango'].astype(str))
    else:
        df['race_key'] = (df['kaisai_tsukihi'].astype(str) + '_' + 
                          df['keibajo_code'].astype(str) + '_' + 
                          df['race_bango'].astype(str))
    
    # レース内順位を計算
    df['race_rank'] = df.groupby('race_key')['ensemble_score'].rank(ascending=False, method='first')
    
    # S/A/B/C/Dランクを付与
    def assign_rank(score):
        if score >= 0.80:
            return 'S'
        elif score >= 0.65:
            return 'A'
        elif score >= 0.50:
            return 'B'
        elif score >= 0.35:
            return 'C'
        else:
            return 'D'
    
    df['rank'] = df['ensemble_score'].apply(assign_rank)
    
    # 結果保存
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✅ アンサンブル結果保存: {output_csv}")
    print(f"\n📊 アンサンブル統計:")
    print(f"   - データ件数: {len(df):,}件")
    print(f"   - 平均スコア: {df['ensemble_score'].mean():.4f}")
    print(f"   - Sランク: {(df['rank'] == 'S').sum()}頭 ({(df['rank'] == 'S').sum() / len(df) * 100:.2f}%)")
    print(f"   - Aランク: {(df['rank'] == 'A').sum()}頭 ({(df['rank'] == 'A').sum() / len(df) * 100:.2f}%)")
    print(f"   - Bランク: {(df['rank'] == 'B').sum()}頭 ({(df['rank'] == 'B').sum() / len(df) * 100:.2f}%)")
    print(f"   - Cランク: {(df['rank'] == 'C').sum()}頭 ({(df['rank'] == 'C').sum() / len(df) * 100:.2f}%)")
    print(f"   - Dランク: {(df['rank'] == 'D').sum()}頭 ({(df['rank'] == 'D').sum() / len(df) * 100:.2f}%)")
    
    return df


def main():
    """メイン実行関数"""
    print("\n" + "="*80)
    print("🚀 大井2025年 Phase 5 アンサンブル統合 実行開始")
    print("="*80)
    print(f"📅 実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    
    # ファイルパス設定
    base_dir = Path("/home/user/uploaded_files")
    output_dir = Path("/home/user/webapp/predictions/phase5_ooi_2025")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 入力ファイル
    test_csv = str(base_dir / "ooi_2025_full_test_with_time.csv")
    test_csv_with_race_id = str(base_dir / "ooi_2025_full_test_with_race_id.csv")
    
    # モデルファイル
    phase3_model = str(base_dir / "ooi_2023-2025_v3_model.txt")
    phase4_ranking_model = str(base_dir / "ooi_2023-2025_v3_with_race_id_ranking_model.txt")
    
    # 出力ファイル
    phase3_output = str(output_dir / "ooi_2025_phase3_binary_predictions.csv")
    phase4_ranking_output = str(output_dir / "ooi_2025_phase4_ranking_predictions.csv")
    phase4_regression_input = str(base_dir / "ooi_2025_phase4_regression_v3_fixed.csv")
    ensemble_output = str(output_dir / "ooi_2025_phase5_ensemble.csv")
    
    # ファイル存在確認
    print("\n📋 ファイル存在確認:")
    files_to_check = {
        "テストデータ": test_csv,
        "テストデータ(race_id付き)": test_csv_with_race_id,
        "Phase 3 モデル": phase3_model,
        "Phase 4 ランキングモデル": phase4_ranking_model,
        "Phase 4 回帰予測結果": phase4_regression_input
    }
    
    all_files_exist = True
    for name, path in files_to_check.items():
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"   {status} {name}: {path}")
        if not exists:
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ 必要なファイルが見つかりません")
        return
    
    print("\n✅ 全ファイル確認完了")
    
    # Step 1: Phase 3 二値分類予測
    df_binary = predict_phase3_binary(test_csv, phase3_model, phase3_output)
    
    # Step 2: Phase 4 ランキング予測
    df_ranking = predict_phase4_ranking(test_csv_with_race_id, phase4_ranking_model, 
                                        phase4_ranking_output)
    
    # Step 3: Phase 5 アンサンブル統合
    df_ensemble = ensemble_integration(
        phase3_output, 
        phase4_ranking_output, 
        phase4_regression_input,
        ensemble_output
    )
    
    # 完了メッセージ
    print("\n" + "="*80)
    print("🎉 Phase 5 アンサンブル統合 完了！")
    print("="*80)
    print(f"\n📁 出力ファイル:")
    print(f"   1️⃣ Phase 3 予測: {phase3_output}")
    print(f"   2️⃣ Phase 4 ランキング: {phase4_ranking_output}")
    print(f"   3️⃣ Phase 5 アンサンブル: {ensemble_output}")
    
    print(f"\n📊 最終統計:")
    print(f"   - 総データ件数: {len(df_ensemble):,}件")
    print(f"   - 総レース数: {df_ensemble['race_key'].nunique()}レース")
    print(f"   - 平均出走頭数: {len(df_ensemble) / df_ensemble['race_key'].nunique():.1f}頭/レース")
    
    print(f"\n🎯 次のステップ:")
    print(f"   Step 4: 買い目生成")
    print(f"   Step 5: バックテスト実行")
    print(f"   Step 6: Phase 5.5 実払戻金バックテスト")


if __name__ == "__main__":
    main()
