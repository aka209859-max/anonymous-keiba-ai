#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: Step 2 - 2着以内二値分類モデル学習

Phase 3と同じLightGBM二値分類を使用
- ターゲット: is_top2（2着以内に入るか）
- 特徴量: 63列（元の52列 + 2着特化11列）
- 競馬場ID埋め込み: keibajo_code を特徴量として使用
- 最終3R重み付け: is_last_3_race=1 のサンプルに2倍の重み
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import argparse
from pathlib import Path
import json

def safe_print(text):
    """安全な日本語出力"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='ignore').decode('utf-8'))

def train_binary_model(input_dir: str, output_dir: str):
    """
    2着以内二値分類モデルを学習
    
    Args:
        input_dir: 特徴量CSVディレクトリ
        output_dir: モデル出力ディレクトリ
    """
    safe_print("\n" + "="*80)
    safe_print("Phase 12: Step 2 - 2着以内二値分類モデル学習")
    safe_print("="*80)
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 全CSVファイルを読み込み
    safe_print(f"\n📂 入力ディレクトリ: {input_dir}")
    csv_files = sorted(input_path.glob("*.csv"))
    safe_print(f"📄 発見したCSVファイル数: {len(csv_files)}")
    
    dfs = []
    for csv_file in csv_files:
        safe_print(f"  - 読み込み中: {csv_file.name}")
        df = pd.read_csv(csv_file, encoding='shift-jis')
        dfs.append(df)
    
    # 全データを結合
    df_all = pd.concat(dfs, ignore_index=True)
    safe_print(f"\n✅ 全データ読み込み完了: {len(df_all):,}行 × {len(df_all.columns)}列")
    
    # ターゲットと特徴量の分離
    if 'is_top2' not in df_all.columns:
        safe_print("❌ エラー: is_top2 列が見つかりません")
        return
    
    y = df_all['is_top2']
    safe_print(f"\n📊 ターゲット分布:")
    safe_print(f"  - 2着以内: {y.sum():,}頭 ({y.mean()*100:.1f}%)")
    safe_print(f"  - 3着以下: {(~y.astype(bool)).sum():,}頭 ({(1-y.mean())*100:.1f}%)")
    
    # 除外列
    exclude_cols = [
        'target', 'rank_target', 'time', 'is_1st', 'is_2nd', 'is_top2', 
        'finish_position', 'race_id', 'kaisai_tsukihi', 'ketto_toroku_bango'
    ]
    
    # 特徴量選択
    feature_cols = [col for col in df_all.columns if col not in exclude_cols]
    X = df_all[feature_cols]
    
    safe_print(f"\n📊 使用する特徴量: {len(feature_cols)}個")
    safe_print(f"  - keibajo_code を含む: {'keibajo_code' in feature_cols}")
    
    # 欠損値を0で補完
    X = X.fillna(0)
    
    # サンプル重み（最終3Rは2倍）
    sample_weights = np.ones(len(X))
    if 'is_last_3_race' in df_all.columns:
        sample_weights[df_all['is_last_3_race'] == 1] = 2.0
        safe_print(f"  - 最終3R重み付け: {(df_all['is_last_3_race']==1).sum():,}サンプル（重み2倍）")
    
    # Train/Validationに分割
    X_train, X_val, y_train, y_val, w_train, w_val = train_test_split(
        X, y, sample_weights, test_size=0.2, random_state=42, stratify=y
    )
    
    safe_print(f"\n📊 データ分割:")
    safe_print(f"  - Train: {len(X_train):,}サンプル")
    safe_print(f"  - Val:   {len(X_val):,}サンプル")
    
    # LightGBMデータセット作成
    train_data = lgb.Dataset(X_train, label=y_train, weight=w_train)
    val_data = lgb.Dataset(X_val, label=y_val, weight=w_val, reference=train_data)
    
    # ハイパーパラメータ
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'seed': 42
    }
    
    safe_print("\n🚀 LightGBM学習開始...")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        valid_names=['train', 'val'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50),
            lgb.log_evaluation(period=100)
        ]
    )
    
    safe_print(f"\n✅ 学習完了（{model.best_iteration}イテレーション）")
    
    # 評価
    y_pred_proba = model.predict(X_val, num_iteration=model.best_iteration)
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    acc = accuracy_score(y_val, y_pred)
    prec = precision_score(y_val, y_pred)
    rec = recall_score(y_val, y_pred)
    f1 = f1_score(y_val, y_pred)
    auc = roc_auc_score(y_val, y_pred_proba)
    
    safe_print(f"\n📊 Validation 評価結果:")
    safe_print(f"  - Accuracy:  {acc:.4f}")
    safe_print(f"  - Precision: {prec:.4f}")
    safe_print(f"  - Recall:    {rec:.4f}")
    safe_print(f"  - F1-Score:  {f1:.4f}")
    safe_print(f"  - ROC-AUC:   {auc:.4f}")
    
    # 特徴量重要度Top20
    importance = model.feature_importance(importance_type='gain')
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    safe_print(f"\n📊 特徴量重要度 Top 20:")
    for idx, row in feature_importance.head(20).iterrows():
        safe_print(f"  {row['feature']:30s}: {row['importance']:10.0f}")
    
    # モデル保存
    model_path = output_path / "phase12_binary_top2_model.txt"
    model.save_model(str(model_path))
    safe_print(f"\n💾 モデル保存: {model_path}")
    
    # メタデータ保存
    metadata = {
        'model_type': 'binary_top2',
        'target': 'is_top2',
        'n_samples': len(df_all),
        'n_features': len(feature_cols),
        'features': feature_cols,
        'best_iteration': model.best_iteration,
        'metrics': {
            'accuracy': float(acc),
            'precision': float(prec),
            'recall': float(rec),
            'f1_score': float(f1),
            'roc_auc': float(auc)
        }
    }
    
    metadata_path = output_path / "phase12_binary_top2_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    safe_print(f"💾 メタデータ保存: {metadata_path}")
    
    safe_print("\n" + "="*80)
    safe_print("✅ Phase 12 Step 2 完了")
    safe_print("="*80)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Phase 12: 2着以内二値分類モデル学習')
    parser.add_argument('--input_dir', type=str, default='data/phase12_umatan/features',
                        help='入力ディレクトリ（特徴量CSV）')
    parser.add_argument('--output_dir', type=str, default='data/phase12_umatan/models/binary',
                        help='出力ディレクトリ（モデル）')
    
    args = parser.parse_args()
    train_binary_model(args.input_dir, args.output_dir)
