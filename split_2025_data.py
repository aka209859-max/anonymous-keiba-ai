#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_2025_data.py
2025年データを学習用80%・テスト用20%に分割
"""

import pandas as pd
import sys

def split_data(input_file: str, train_file: str, test_file: str, test_ratio: float = 0.2):
    """
    データを学習用とテスト用に分割
    
    Args:
        input_file: 入力CSVファイル
        train_file: 学習用出力ファイル
        test_file: テスト用出力ファイル
        test_ratio: テストデータの割合（デフォルト: 0.2 = 20%）
    """
    print(f"\n{'='*80}")
    print(f"📊 データ分割開始")
    print(f"{'='*80}")
    print(f"入力: {input_file}")
    print(f"テスト比率: {test_ratio*100:.0f}%")
    
    # データ読み込み
    df = pd.read_csv(input_file)
    print(f"\n✅ 読み込み完了: {len(df):,}件")
    
    # レースIDでグループ化（同一レースの馬は同じセットに）
    df['race_id'] = (
        df['kaisai_nen'].astype(str) + 
        df['kaisai_tsukihi'].astype(str).str.zfill(4) +
        df['keibajo_code'].astype(str).str.zfill(2) +
        df['race_bango'].astype(str).str.zfill(2)
    )
    
    # レースIDでソート（日付順）
    df = df.sort_values('race_id')
    
    # ユニークなレースIDを取得
    unique_races = df['race_id'].unique()
    total_races = len(unique_races)
    
    # 分割ポイントを計算（最新20%をテストデータ）
    split_idx = int(total_races * (1 - test_ratio))
    train_race_ids = unique_races[:split_idx]
    test_race_ids = unique_races[split_idx:]
    
    # データを分割
    train_df = df[df['race_id'].isin(train_race_ids)].drop('race_id', axis=1)
    test_df = df[df['race_id'].isin(test_race_ids)].drop('race_id', axis=1)
    
    print(f"\n📦 分割結果:")
    print(f"  学習データ:")
    print(f"    - レース数: {len(train_race_ids):,}")
    print(f"    - データ件数: {len(train_df):,}")
    print(f"  テストデータ:")
    print(f"    - レース数: {len(test_race_ids):,}")
    print(f"    - データ件数: {len(test_df):,}")
    
    # ファイル保存
    train_df.to_csv(train_file, index=False)
    test_df.to_csv(test_file, index=False)
    
    print(f"\n💾 保存完了:")
    print(f"  学習: {train_file}")
    print(f"  テスト: {test_file}")
    print(f"\n{'='*80}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python split_2025_data.py <input_csv>")
        print("Example: python split_2025_data.py ooi_2025_full.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    train_file = input_file.replace('.csv', '_train.csv')
    test_file = input_file.replace('.csv', '_test.csv')
    
    split_data(input_file, train_file, test_file)
