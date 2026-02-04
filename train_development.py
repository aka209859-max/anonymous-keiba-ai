#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_development.py
地方競馬AI学習プログラム (LightGBM + Boruta + Optuna)

使用法:
    python train_development.py <csvファイル名>

出力:
    - {csv_file}_model.txt: 学習済みモデル
    - {csv_file}_model.png: 特徴量重要度グラフ (Top 20)
    - {csv_file}_score.txt: 評価指標ログ
"""

import sys
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from boruta import BorutaPy
import lightgbm as lgb
import optuna.integration.lightgbm as lgb_optuna
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# 日本語フォント設定（環境に応じて調整）
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def main():
    """メイン処理"""
    
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        print("エラー: CSVファイル名が指定されていません")
        print("使用法: python train_development.py <csvファイル名>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # ファイルの存在確認
    if not os.path.exists(csv_file):
        print(f"エラー: ファイル '{csv_file}' が見つかりません")
        sys.exit(1)
    
    print("=" * 80)
    print("地方競馬AI学習プログラム (LightGBM + Boruta + Optuna)")
    print("=" * 80)
    print(f"CSVファイル: {csv_file}\n")
    
    # データ読み込み
    print("[1/7] データ読み込み中...")
    try:
        df = pd.read_csv(csv_file, encoding='shift-jis')
        print(f"  - データ件数: {len(df):,}件")
        print(f"  - カラム数: {len(df.columns)}個")
    except UnicodeDecodeError:
        print("  警告: Shift-JISでの読み込みに失敗。UTF-8で再試行...")
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"  - データ件数: {len(df):,}件")
        print(f"  - カラム数: {len(df.columns)}個")
    except Exception as e:
        print(f"エラー: CSVファイルの読み込みに失敗しました: {e}")
        sys.exit(1)
    
    # 目的変数の確認
    if 'target' not in df.columns:
        print("エラー: 'target' カラムが見つかりません")
        sys.exit(1)
    
    # 目的変数と説明変数の分離
    X = df.drop('target', axis=1)
    y = df['target']
    
    print(f"  - 目的変数 'target' の分布:")
    print(f"    クラス 0: {(y == 0).sum():,}件 ({(y == 0).sum() / len(y) * 100:.1f}%)")
    print(f"    クラス 1: {(y == 1).sum():,}件 ({(y == 1).sum() / len(y) * 100:.1f}%)")
    
    # 非数値カラムのチェックと処理
    non_numeric_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric_cols:
        print(f"  警告: 非数値カラムが検出されました: {non_numeric_cols}")
        print("  これらのカラムを削除します...")
        X = X.select_dtypes(include=[np.number])
    
    # 欠損値のチェック
    if X.isnull().any().any():
        print("  警告: 欠損値が検出されました。平均値で補完します...")
        X = X.fillna(X.mean())
    
    print(f"  - 最終的な説明変数数: {len(X.columns)}個\n")
    
    # Borutaによる特徴量選択
    print("[2/7] Borutaによる特徴量選択中...")
    print("  （この処理には数分〜数十分かかる場合があります）")
    
    try:
        rf = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            max_depth=5  # メモリ効率のため深さを制限
        )
        
        boruta_selector = BorutaPy(
            rf,
            n_estimators='auto',
            max_iter=100,
            random_state=42,
            verbose=0
        )
        
        boruta_selector.fit(X.values, y.values)
        
        # 選択された特徴量のみを使用
        selected_features = X.columns[boruta_selector.support_].tolist()
        
        if len(selected_features) == 0:
            print("  警告: Borutaで選択された特徴量が0個でした。全特徴量を使用します。")
            selected_features = X.columns.tolist()
        
        X_selected = X[selected_features]
        
        print(f"  - 選択された特徴量数: {len(selected_features)} / {len(X.columns)}")
        print(f"  - 選択率: {len(selected_features) / len(X.columns) * 100:.1f}%\n")
        
    except Exception as e:
        print(f"  エラー: Boruta実行中にエラーが発生しました: {e}")
        print("  全特徴量を使用して続行します...")
        selected_features = X.columns.tolist()
        X_selected = X
    
    # データ分割
    print("[3/7] データ分割中...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_selected,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    
    print(f"  - 訓練データ: {len(X_train):,}件")
    print(f"  - テストデータ: {len(X_test):,}件\n")
    
    # LightGBM Dataset作成
    print("[4/7] LightGBM Datasetを作成中...")
    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_eval = lgb.Dataset(X_test, y_test, reference=lgb_train)
    print("  - Dataset作成完了\n")
    
    # LightGBM + Optunaによるハイパーパラメータ最適化
    print("[5/7] LightGBM + Optunaによる学習中...")
    print("  （ハイパーパラメータ自動最適化を実行します）")
    
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'verbosity': -1,
        'boosting_type': 'gbdt',
        'force_col_wise': True  # 警告抑制
    }
    
    try:
        model = lgb_optuna.train(
            params,
            lgb_train,
            valid_sets=[lgb_eval],
            num_boost_round=1000,
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=100)
            ]
        )
        print("  - 学習完了\n")
    except Exception as e:
        print(f"エラー: モデル学習中にエラーが発生しました: {e}")
        sys.exit(1)
    
    # モデル評価
    print("[6/7] モデル評価中...")
    
    # 予測
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # 評価指標計算
    auc = roc_auc_score(y_test, y_pred_proba)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print(f"  - AUC:       {auc:.4f}")
    print(f"  - Accuracy:  {accuracy:.4f}")
    print(f"  - Precision: {precision:.4f}")
    print(f"  - Recall:    {recall:.4f}")
    print(f"  - F1-Score:  {f1:.4f}\n")
    
    # 出力ファイルの準備
    print("[7/7] 結果を保存中...")
    
    base_name = csv_file.replace('.csv', '')
    model_file = f"{base_name}_model.txt"
    image_file = f"{base_name}_model.png"
    score_file = f"{base_name}_score.txt"
    
    # モデルの保存
    try:
        model.save_model(model_file)
        print(f"  - モデル保存: {model_file}")
    except Exception as e:
        print(f"  エラー: モデル保存に失敗しました: {e}")
    
    # 特徴量重要度の可視化
    try:
        importance = model.feature_importance(importance_type='gain')
        feature_importance = pd.DataFrame({
            'feature': selected_features,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        # Top 20を可視化
        top_n = min(20, len(feature_importance))
        plt.figure(figsize=(10, 8))
        plt.barh(
            range(top_n),
            feature_importance['importance'].head(top_n),
            color='steelblue'
        )
        plt.yticks(
            range(top_n),
            feature_importance['feature'].head(top_n),
            fontsize=9
        )
        plt.xlabel('Importance (Gain)', fontsize=11)
        plt.title(f'Feature Importance (Top {top_n})', fontsize=13, fontweight='bold')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(image_file, dpi=150)
        plt.close()
        print(f"  - 重要度グラフ保存: {image_file}")
    except Exception as e:
        print(f"  エラー: グラフ保存に失敗しました: {e}")
    
    # 評価指標の保存
    try:
        with open(score_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("地方競馬AI 学習結果\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"CSVファイル: {csv_file}\n")
            f.write(f"データ件数: {len(df):,}件\n")
            f.write(f"訓練データ: {len(X_train):,}件\n")
            f.write(f"テストデータ: {len(X_test):,}件\n\n")
            
            f.write("【評価指標】\n")
            f.write(f"AUC:       {auc:.4f}\n")
            f.write(f"Accuracy:  {accuracy:.4f}\n")
            f.write(f"Precision: {precision:.4f}\n")
            f.write(f"Recall:    {recall:.4f}\n")
            f.write(f"F1-Score:  {f1:.4f}\n\n")
            
            f.write("【特徴量選択】\n")
            f.write(f"元の特徴量数: {len(X.columns)}\n")
            f.write(f"選択された特徴量数: {len(selected_features)}\n")
            f.write(f"選択率: {len(selected_features) / len(X.columns) * 100:.1f}%\n\n")
            
            f.write("【特徴量重要度 Top 20】\n")
            f.write("-" * 60 + "\n")
            for idx, row in feature_importance.head(20).iterrows():
                f.write(f"{row['feature']:40s} {row['importance']:10.2f}\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        print(f"  - 評価指標保存: {score_file}\n")
    except Exception as e:
        print(f"  エラー: 評価指標保存に失敗しました: {e}")
    
    print("=" * 80)
    print("学習完了！")
    print("=" * 80)
    print(f"\n出力ファイル:")
    print(f"  1. {model_file}")
    print(f"  2. {image_file}")
    print(f"  3. {score_file}\n")


if __name__ == "__main__":
    main()
