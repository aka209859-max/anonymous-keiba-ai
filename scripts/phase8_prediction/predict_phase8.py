#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
predict_phase8.py
Phase 8最適化モデルで予測を実行し、Phase 6で使える形式で保存

Phase 8で学習済みのモデルとPhase 7で選択された特徴量を使用して、
Phase 1の特徴量データから予測を実行し、Phase 5相当の結果を生成します。

使用法:
    python predict_phase8.py --venue-code 43 --date 2026-02-11

入力:
    - data/models/tuned/{venue}_tuned_model.txt: Phase 8で学習済みのモデル
    - data/features/selected/{venue}_selected_features.csv: Phase 7で選択された特徴量
    - data/features/YYYY/MM/*YYYYMMDD*_features.csv: Phase 1の特徴量データ
    
出力:
    - data/predictions/phase8/{venue}_{date}_phase8_predictions.csv: 予測結果（Phase 5互換形式）
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import lightgbm as lgb
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 競馬場コード→名前の辞書
VENUE_CODE_TO_NAME = {
    '30': 'monbetsu', '35': 'morioka', '36': 'mizusawa', '42': 'urawa',
    '43': 'funabashi', '44': 'ooi', '45': 'kawasaki', '46': 'kanazawa',
    '47': 'kasamatsu', '48': 'nagoya', '50': 'sonoda', '51': 'himeji',
    '54': 'kochi', '55': 'saga',
}

VENUE_NAME_TO_JA = {
    'monbetsu': '門別', 'morioka': '盛岡', 'mizusawa': '水沢', 'urawa': '浦和',
    'funabashi': '船橋', 'ooi': '大井', 'kawasaki': '川崎', 'kanazawa': '金沢',
    'kasamatsu': '笠松', 'nagoya': '名古屋', 'sonoda': '園田', 'himeji': '姫路',
    'kochi': '高知', 'saga': '佐賀',
}


def load_phase8_model(venue_name):
    """Phase 8で学習済みのLightGBMモデルを読み込む"""
    model_path = project_root / 'data' / 'models' / 'tuned' / f'{venue_name}_tuned_model.txt'
    
    if not model_path.exists():
        raise FileNotFoundError(f"❌ Phase 8モデルが見つかりません: {model_path}")
    
    print(f"✅ Phase 8モデル読み込み: {model_path}")
    model = lgb.Booster(model_file=str(model_path))
    return model


def load_selected_features(venue_name):
    """Phase 7で選択された特徴量リストを読み込む"""
    features_path = project_root / 'data' / 'features' / 'selected' / f'{venue_name}_selected_features.csv'
    
    if not features_path.exists():
        raise FileNotFoundError(f"❌ Phase 7特徴量が見つかりません: {features_path}")
    
    print(f"✅ Phase 7特徴量読み込み: {features_path}")
    df = pd.read_csv(features_path, encoding='utf-8')
    selected_features = df['feature'].tolist()
    print(f"  - 選択特徴量数: {len(selected_features)}個")
    
    return selected_features


def load_phase1_data(venue_code, target_date):
    """Phase 1の特徴量データを読み込む"""
    date_short = target_date.replace('-', '')
    year = target_date.split('-')[0]
    month = target_date.split('-')[1]
    
    search_patterns = [
        project_root / 'data' / 'features' / year / month / f'*{date_short}*features.csv',
        project_root / 'data' / 'features' / year / month / f'*{date_short}*.csv',
    ]
    
    for pattern in search_patterns:
        if not pattern.parent.exists():
            continue
            
        matches = list(pattern.parent.glob(pattern.name))
        matches = [m for m in matches if 'ensemble' not in m.name.lower()]
        
        if matches:
            csv_path = matches[0]
            print(f"✅ Phase 1データ読み込み: {csv_path}")
            
            try:
                df = pd.read_csv(csv_path, encoding='shift-jis')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_path, encoding='utf-8')
            
            print(f"  - レコード数: {len(df)}件")
            print(f"  - カラム数: {len(df.columns)}個")
            
            if len(df.columns) < 30:
                print(f"⚠️ 警告: カラム数が少ない({len(df.columns)}個)")
                continue
            
            return df
    
    raise FileNotFoundError(
        f"❌ Phase 1の特徴量データが見つかりません\n"
        f"   競馬場コード: {venue_code}\n"
        f"   対象日: {target_date}\n"
        f"   まずPhase 0-1を実行してください:\n"
        f"   > run_all.bat {venue_code} {target_date}"
    )


def predict_phase8(model, df, selected_features):
    """Phase 8モデルで予測を実行"""
    print(f"\n{'='*60}")
    print(f"Phase 8予測実行中...")
    print(f"{'='*60}")
    
    # 特徴量の存在確認
    missing_features = [f for f in selected_features if f not in df.columns]
    if missing_features:
        print(f"⚠️ 警告: {len(missing_features)}個の特徴量がデータに存在しません")
        available_features = [f for f in selected_features if f in df.columns]
        print(f"  - 使用可能な特徴量: {len(available_features)}/{len(selected_features)}個")
        
        if len(available_features) == 0:
            raise ValueError("❌ 使用可能な特徴量が1つもありません")
        
        selected_features = available_features
    
    # 特徴量を抽出
    X = df[selected_features].copy()
    
    # 欠損値を0で埋める
    X = X.fillna(0)
    
    # object型を数値に変換
    for col in X.select_dtypes(include=['object']).columns:
        X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    
    print(f"  - 使用特徴量: {len(selected_features)}個")
    print(f"  - サンプル数: {len(X)}件")
    
    # 予測実行
    y_pred = model.predict(X)
    
    print(f"✅ 予測完了")
    print(f"  - 平均予測確率: {y_pred.mean():.4f}")
    print(f"  - 最大予測確率: {y_pred.max():.4f}")
    print(f"  - 最小予測確率: {y_pred.min():.4f}")
    
    return y_pred


def save_phase8_predictions(df, predictions, venue_name, target_date):
    """
    Phase 8の予測結果をPhase 5互換形式で保存
    Phase 6の配信テキスト生成で使用できる形式
    """
    output_dir = project_root / 'data' / 'predictions' / 'phase8'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_short = target_date.replace('-', '')
    venue_ja = VENUE_NAME_TO_JA.get(venue_name, venue_name)
    
    # Phase 5互換の形式で保存
    df_output = df[['race_id', 'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
                    'race_bango', 'ketto_toroku_bango', 'umaban']].copy()
    
    # Phase 8の予測確率を追加
    df_output['phase8_probability'] = predictions
    df_output['phase8_score'] = predictions  # Phase 5のensemble_scoreと同等
    
    # ランキングを追加（確率降順）
    df_output['phase8_rank'] = df_output.groupby('race_id')['phase8_probability'].rank(
        ascending=False, method='min'
    ).astype(int)
    
    # Phase 5形式のカラムも追加（互換性のため）
    df_output['ensemble_score'] = predictions
    df_output['binary_probability'] = predictions
    df_output['final_rank'] = df_output['phase8_rank']
    
    # 保存
    output_path = output_dir / f'{venue_name}_{date_short}_phase8_predictions.csv'
    df_output.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ Phase 8予測結果保存: {output_path}")
    print(f"  - Phase 6配信テキスト生成で使用可能")
    
    # Phase 5互換の場所にもコピー（Phase 6が読み込めるように）
    phase5_dir = project_root / 'data' / 'predictions' / 'phase5'
    phase5_dir.mkdir(parents=True, exist_ok=True)
    phase5_path = phase5_dir / f'{venue_ja}_{date_short}_ensemble.csv'
    df_output.to_csv(phase5_path, index=False, encoding='shift-jis')
    print(f"✅ Phase 5互換形式で保存: {phase5_path}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Phase 8予測実行（配信用）')
    parser.add_argument('--venue-code', type=str, required=True, help='競馬場コード（例: 43）')
    parser.add_argument('--date', type=str, required=True, help='対象日（例: 2026-02-11）')
    
    args = parser.parse_args()
    
    # 競馬場名を取得
    venue_name = VENUE_CODE_TO_NAME.get(args.venue_code)
    if venue_name is None:
        print(f"❌ 無効な競馬場コード: {args.venue_code}")
        sys.exit(1)
    
    venue_ja = VENUE_NAME_TO_JA.get(venue_name, venue_name)
    
    print(f"\n{'='*60}")
    print(f"Phase 8予測システム（配信用）")
    print(f"{'='*60}")
    print(f"競馬場: {venue_ja} ({venue_name})")
    print(f"対象日: {args.date}")
    print(f"{'='*60}\n")
    
    try:
        # [1/4] Phase 8モデル読み込み
        print(f"[1/4] Phase 8モデル読み込み中...")
        model = load_phase8_model(venue_name)
        print()
        
        # [2/4] Phase 7特徴量読み込み
        print(f"[2/4] Phase 7特徴量読み込み中...")
        selected_features = load_selected_features(venue_name)
        print()
        
        # [3/4] Phase 1データ読み込み
        print(f"[3/4] Phase 1データ読み込み中...")
        df = load_phase1_data(args.venue_code, args.date)
        print()
        
        # [4/4] 予測実行 & 保存
        print(f"[4/4] Phase 8予測実行 & 保存中...")
        predictions = predict_phase8(model, df, selected_features)
        output_path = save_phase8_predictions(df, predictions, venue_name, args.date)
        print()
        
        print(f"{'='*60}")
        print(f"✅ Phase 8予測完了！")
        print(f"{'='*60}")
        print(f"次のステップ: Phase 6配信テキスト生成")
        print(f"コマンド: scripts\\phase6_betting\\DAILY_OPERATION.bat {args.venue_code} {args.date}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
