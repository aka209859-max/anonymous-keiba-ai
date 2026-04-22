#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: Step 3 - ランキングモデル学習
"""

import argparse
import pandas as pd
import lightgbm as lgb
import numpy as np
import os
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def safe_print(text):
    """文字化け対策のprint"""
    try:
        print(text.encode('shift-jis', errors='ignore').decode('shift-jis'))
    except:
        print(text)

def train_ranking_model(input_dir, output_dir):
    """ランキングモデル学習"""
    safe_print("=" * 80)
    safe_print("Phase 12: Step 3 - ランキングモデル学習")
    safe_print("=" * 80)
    
    # 入力ディレクトリの確認
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"入力ディレクトリが見つかりません: {input_dir}")
    
    # CSVファイルの読み込み
    csv_files = list(input_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"CSVファイルが見つかりません: {input_dir}")
    
    safe_print(f"\n📂 入力ディレクトリ: {input_dir}")
    safe_print(f"📄 発見したCSVファイル数: {len(csv_files)}")
    
    # 競馬場別にモデルを学習
    keibajo_mapping = {
        'funabashi': '船橋',
        'ooi': '大井',
        'urawa': '浦和',
        'kawasaki': '川崎',
        'monbetsu': '門別'
    }
    
    for keibajo_en, keibajo_jp in keibajo_mapping.items():
        safe_print(f"\n{'='*80}")
        safe_print(f"📍 競馬場: {keibajo_jp} ({keibajo_en})")
        safe_print(f"{'='*80}")
        
        # 対応するCSVファイルを探す
        csv_file = input_path / f"{keibajo_en}.csv"
        if not csv_file.exists():
            safe_print(f"⚠️  CSVファイルが見つかりません: {csv_file.name}")
            continue
        
        safe_print(f"  - 読み込み中: {csv_file.name}")
        try:
            df_combined = pd.read_csv(csv_file, encoding='shift-jis')
        except:
            df_combined = pd.read_csv(csv_file, encoding='utf-8')
        
        safe_print(f"✅ データ読み込み完了: {len(df_combined):,}行 × {len(df_combined.columns)}列")
        
        # 必須列の確認
        if 'rank_target' not in df_combined.columns:
            raise ValueError("rank_target列が見つかりません")
        if 'race_id' not in df_combined.columns:
            raise ValueError("race_id列が見つかりません")
        
        # ターゲットの準備（順位を数値化）
        df_combined['rank_target'] = pd.to_numeric(df_combined['rank_target'], errors='coerce')
        
        # レースIDでグループ化するための準備
        df_combined['group'] = df_combined.groupby('race_id').ngroup()
        
        # データの統計情報
        safe_print(f"\n📊 データセットの統計情報:")
        safe_print(f"  - レース数: {df_combined['race_id'].nunique():,}件")
        safe_print(f"  - 総馬数: {len(df_combined):,}頭")
        safe_print(f"  - 平均出走頭数: {df_combined.groupby('race_id').size().mean():.1f}頭")
        safe_print(f"  - 順位範囲: {df_combined['rank_target'].min():.0f}位 ～ {df_combined['rank_target'].max():.0f}位")
    
        # 特徴量の準備（データリーク防止）
        exclude_cols = ['target', 'rank_target', 'race_id', 'group',
                        'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
                        'race_bango', 'ketto_toroku_bango', 'umaban',
                        'finish_position', 'kakutei_chakujun',
                        'time', 'bamei']  # データリーク防止（time=着順タイム、bamei=馬名）
        feature_cols = [col for col in df_combined.columns if col not in exclude_cols]
        
        safe_print(f"\n🔧 特徴量:")
        safe_print(f"  - 使用する特徴量数: {len(feature_cols)}")
        safe_print(f"  - keibajo_code 除外済み（競馬場別モデルのため）")
        
        # 特徴量の準備（keibajo_codeは除外）
        X = df_combined[feature_cols].copy()
    
        y = df_combined['rank_target'].values
        groups = df_combined['group'].values
        
        # 欠損値補完
        X = X.fillna(0)
        
        # 最終3レースの重み付け
        if 'is_last_3_race' in df_combined.columns:
            weights = np.where(df_combined['is_last_3_race'] == 1, 2.0, 1.0)
            safe_print(f"  - 最終3レース重み付けサンプル数: {(df_combined['is_last_3_race']==1).sum():,}件（重み×2）")
        else:
            weights = np.ones(len(X))
        
        # データ分割（8:2）
        unique_groups = df_combined['race_id'].unique()
        np.random.seed(42)
        train_groups = np.random.choice(unique_groups, size=int(len(unique_groups)*0.8), replace=False)
        
        train_mask = df_combined['race_id'].isin(train_groups)
        val_mask = ~train_mask
        
        X_train, y_train = X[train_mask], y[train_mask]
        X_val, y_val = X[val_mask], y[val_mask]
        groups_train = df_combined.loc[train_mask, 'group'].values
        groups_val = df_combined.loc[val_mask, 'group'].values
        weights_train = weights[train_mask]
        weights_val = weights[val_mask]
        
        safe_print(f"\n📊 データ分割:")
        safe_print(f"  - Train: {len(X_train):,}サンプル ({len(df_combined.loc[train_mask, 'race_id'].unique()):,}レース)")
        safe_print(f"  - Validation: {len(X_val):,}サンプル ({len(df_combined.loc[val_mask, 'race_id'].unique()):,}レース)")
        
        # group_idを0から連番に再割り当て（LightGBM LambdaRankの要件）
        train_group_sizes = df_combined[train_mask].groupby('group').size().values
        val_group_sizes = df_combined[val_mask].groupby('group').size().values
        
        # LightGBMデータセット作成
        train_data = lgb.Dataset(
            X_train, 
            label=y_train, 
            group=train_group_sizes,
            weight=weights_train
        )
        val_data = lgb.Dataset(
            X_val, 
            label=y_val, 
            group=val_group_sizes,
            weight=weights_val,
            reference=train_data
        )
        
        # LightGBMパラメータ（LambdaRank）
        params = {
            'objective': 'lambdarank',
            'metric': 'ndcg',
            'ndcg_eval_at': [1, 3, 5],
            'learning_rate': 0.05,
            'num_leaves': 31,
            'max_depth': -1,
            'min_data_in_leaf': 20,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'seed': 42
        }
        
        safe_print(f"\n🚀 LightGBM学習開始（LambdaRank）")
        safe_print(f"  - Objective: lambdarank")
        safe_print(f"  - Metric: NDCG@1,3,5")
        
        # 学習
        model = lgb.train(
            params,
            train_data,
            num_boost_round=2000,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'valid'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=100, verbose=True),
                lgb.log_evaluation(period=50)
            ]
        )
        
        safe_print(f"\n✅ 学習完了: Best iteration = {model.best_iteration}")
        
        # 予測（Validation）
        y_pred = model.predict(X_val, num_iteration=model.best_iteration)
        
        # レースごとに順位付け
        val_df = df_combined[val_mask].copy()
        val_df['predicted_score'] = y_pred
        val_df['predicted_rank'] = val_df.groupby('race_id')['predicted_score'].rank(ascending=False, method='min')
        val_df['actual_rank'] = val_df['rank_target']
        
        # デバッグ：actual_rankの統計情報
        safe_print(f"\n📊 actual_rank統計:")
        safe_print(f"  - 最小値: {val_df['actual_rank'].min()}")
        safe_print(f"  - 最大値: {val_df['actual_rank'].max()}")
        safe_print(f"  - 欠損値: {val_df['actual_rank'].isna().sum()}件")
        safe_print(f"  - ユニーク値: {val_df['actual_rank'].nunique()}種類")
        
        # 最初のレースの全馬のactual_rankとumabanを表示
        first_race = val_df.groupby('race_id').first().index[0]
        first_race_df = val_df[val_df['race_id'] == first_race][['umaban', 'actual_rank', 'predicted_score']].sort_values('actual_rank')
        safe_print(f"\n📊 最初のレース({first_race})の全馬:")
        for idx, row in first_race_df.head(10).iterrows():
            safe_print(f"  馬番{int(row['umaban'])}番: actual_rank={row['actual_rank']}, predicted_score={row['predicted_score']:.4f}")
        
        # Top-K精度計算（デバッグ付き）
        def calc_topk_accuracy(df, k):
            """
            Top-K的中率：予測上位K頭の中に、実際の上位K頭が何頭含まれているか
            """
            total_matches = 0
            total_races = df['race_id'].nunique()
            debug_count = 0
            hit_races = 0  # 的中レース数
            for race_id, group in df.groupby('race_id'):
                # 予測上位K頭（predicted_scoreが大きい方から）
                top_k_predicted = set(group.nlargest(k, 'predicted_score')['umaban'].values)
                # 実際の上位K頭（actual_rankが小さい方から、つまり1位、2位、3位...）
                top_k_actual = set(group.nsmallest(k, 'actual_rank')['umaban'].values)
                # 一致数をカウント
                matches = len(top_k_predicted & top_k_actual)
                if matches > 0:
                    total_matches += matches
                    hit_races += 1
                # デバッグ出力（最初の10レースのみ）
                if debug_count < 10 and k == 1:
                    safe_print(f"  [Debug] レース{race_id}: 予測上位{k}={top_k_predicted}, 実際上位{k}={top_k_actual}, 一致数={matches}")
                    debug_count += 1
            # 的中率 = 一致した馬の総数 / (レース数 × K)
            accuracy = total_matches / (total_races * k)
            # 的中レース率も表示
            if k == 1:
                safe_print(f"  [統計] Top-{k}的中レース: {hit_races}/{total_races}レース ({hit_races/total_races*100:.2f}%)")
            return accuracy
        
        top1_acc = calc_topk_accuracy(val_df, 1)
        top3_acc = calc_topk_accuracy(val_df, 3)
        top5_acc = calc_topk_accuracy(val_df, 5)
        
        safe_print(f"\n📊 Validation 性能:")
        safe_print(f"  - Top-1的中率: {top1_acc:.4f}")
        safe_print(f"  - Top-3的中率: {top3_acc:.4f}")
        safe_print(f"  - Top-5的中率: {top5_acc:.4f}")
        
        # 特徴量重要度
        feature_importance = pd.DataFrame({
            'feature': model.feature_name(),
            'importance': model.feature_importance(importance_type='gain')
        }).sort_values('importance', ascending=False)
        
        safe_print(f"\n📊 特徴量重要度 Top 20:")
        for idx, row in feature_importance.head(20).iterrows():
            safe_print(f"  {row['feature']:30s} {row['importance']:>10.0f}")
        
        # モデル保存
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        model_file = output_path / f"phase12_{keibajo_en}_ranking_model.txt"
        model.save_model(str(model_file))
        safe_print(f"\n💾 モデル保存: {model_file}")
        
        # メタデータ保存
        metadata = {
            'model_type': 'ranking',
            'keibajo': keibajo_jp,
            'objective': 'lambdarank',
            'num_features': len(feature_cols),
            'best_iteration': model.best_iteration,
            'top1_accuracy': float(top1_acc),
            'top3_accuracy': float(top3_acc),
            'top5_accuracy': float(top5_acc),
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'train_races': len(df_combined.loc[train_mask, 'race_id'].unique()),
            'val_races': len(df_combined.loc[val_mask, 'race_id'].unique())
        }
        
        metadata_file = output_path / f"phase12_{keibajo_en}_ranking_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        safe_print(f"💾 メタデータ保存: {metadata_file}")
    
    safe_print(f"\n{'='*80}")
    safe_print("✅ Phase 12 Step 3 完了（全競馬場）")
    safe_print(f"{'='*80}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Phase 12 Step 3: ランキングモデル学習')
    parser.add_argument('--input_dir', type=str, required=True, help='特徴量ディレクトリ')
    parser.add_argument('--output_dir', type=str, required=True, help='モデル出力ディレクトリ')
    
    args = parser.parse_args()
    
    try:
        train_ranking_model(args.input_dir, args.output_dir)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
