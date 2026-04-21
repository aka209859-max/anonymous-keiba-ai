#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: Step 1 - 2着以内特化の追加特徴量生成

既存の52特徴量に加えて、以下を追加：
- recent_1st_rate: 過去10走の1着率
- recent_2nd_rate: 過去10走の2着率
- recent_top2_rate: 過去10走の2着以内率
- recent_1st_count: 過去10走の1着回数
- recent_2nd_count: 過去10走の2着回数
- is_1st: 1着かどうか（学習用ターゲット）
- is_2nd: 2着かどうか（学習用ターゲット）
- is_top2: 2着以内かどうか（学習用ターゲット）
- is_last_3_race: 最終3Rフラグ（重み付け学習用）
"""

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
import argparse

def safe_print(text):
    """安全な日本語出力"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='ignore').decode('utf-8'))

def add_top2_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    2着以内特化の追加特徴量を生成
    
    Args:
        df: 元データ（52特徴量）
    
    Returns:
        pd.DataFrame: 追加特徴量付きデータ
    """
    safe_print("🔄 2着以内特化の追加特徴量を生成中...")
    
    # ターゲット列の確認（rank_targetを優先使用）
    if 'rank_target' in df.columns:
        safe_print("✅ 'rank_target' カラムを使用（実際の着順）")
        df['finish_position'] = df['rank_target'].astype(float).fillna(99).astype(int)
    elif 'kakutei_chakujun' in df.columns:
        safe_print("✅ 'kakutei_chakujun' カラムを使用（実際の着順）")
        df['finish_position'] = df['kakutei_chakujun'].astype(float).fillna(99).astype(int)
    elif 'target' in df.columns:
        safe_print("⚠️ 'target' カラムは3着以内フラグのため使用不可")
        safe_print("❌ エラー: 着順データが見つかりません")
        return None
    else:
        safe_print("❌ エラー: 着順データが見つかりません")
        return None
    
    # 1着/2着/2着以内フラグ
    df['is_1st'] = (df['finish_position'] == 1).astype(int)
    df['is_2nd'] = (df['finish_position'] == 2).astype(int)
    df['is_top2'] = (df['finish_position'] <= 2).astype(int)
    
    safe_print(f"  - is_1st: {df['is_1st'].sum()}頭（{df['is_1st'].mean()*100:.1f}%）")
    safe_print(f"  - is_2nd: {df['is_2nd'].sum()}頭（{df['is_2nd'].mean()*100:.1f}%）")
    safe_print(f"  - is_top2: {df['is_top2'].sum()}頭（{df['is_top2'].mean()*100:.1f}%）")
    
    # 日付でソート（過去成績計算用）
    if 'kaisai_tsukihi' in df.columns:
        df = df.sort_values(['ketto_toroku_bango', 'kaisai_tsukihi']).reset_index(drop=True)
    
    # 馬ごとの過去10走の成績を計算
    safe_print("🔄 過去10走の1着率・2着率を計算中...")
    
    if 'ketto_toroku_bango' in df.columns:
        # 過去10走の1着率
        df['recent_1st_rate'] = df.groupby('ketto_toroku_bango')['is_1st'].transform(
            lambda x: x.rolling(window=10, min_periods=1).mean().shift(1).fillna(0)
        )
        
        # 過去10走の2着率
        df['recent_2nd_rate'] = df.groupby('ketto_toroku_bango')['is_2nd'].transform(
            lambda x: x.rolling(window=10, min_periods=1).mean().shift(1).fillna(0)
        )
        
        # 過去10走の2着以内率
        df['recent_top2_rate'] = df.groupby('ketto_toroku_bango')['is_top2'].transform(
            lambda x: x.rolling(window=10, min_periods=1).mean().shift(1).fillna(0)
        )
        
        # 過去10走の1着回数
        df['recent_1st_count'] = df.groupby('ketto_toroku_bango')['is_1st'].transform(
            lambda x: x.rolling(window=10, min_periods=1).sum().shift(1).fillna(0)
        ).astype(int)
        
        # 過去10走の2着回数
        df['recent_2nd_count'] = df.groupby('ketto_toroku_bango')['is_2nd'].transform(
            lambda x: x.rolling(window=10, min_periods=1).sum().shift(1).fillna(0)
        ).astype(int)
        
        safe_print(f"✅ 過去10走の成績計算完了")
    else:
        safe_print("⚠️ 'ketto_toroku_bango' カラムが見つかりません。過去成績はデフォルト値になります。")
        df['recent_1st_rate'] = 0.0
        df['recent_2nd_rate'] = 0.0
        df['recent_top2_rate'] = 0.0
        df['recent_1st_count'] = 0
        df['recent_2nd_count'] = 0
    
    # 最終3Rフラグを追加
    safe_print("🔄 最終3Rフラグを追加中...")
    
    if 'race_bango' in df.columns and 'kaisai_tsukihi' in df.columns:
        df['is_last_3_race'] = 0
        
        for date in df['kaisai_tsukihi'].unique():
            date_mask = df['kaisai_tsukihi'] == date
            if 'keibajo_code' in df.columns:
                for venue in df[date_mask]['keibajo_code'].unique():
                    venue_mask = date_mask & (df['keibajo_code'] == venue)
                    max_race = df[venue_mask]['race_bango'].max()
                    last_3_mask = venue_mask & (df['race_bango'] >= max_race - 2)
                    df.loc[last_3_mask, 'is_last_3_race'] = 1
            else:
                max_race = df[date_mask]['race_bango'].max()
                last_3_mask = date_mask & (df['race_bango'] >= max_race - 2)
                df.loc[last_3_mask, 'is_last_3_race'] = 1
        
        last3_count = df['is_last_3_race'].sum()
        safe_print(f"✅ 最終3Rフラグ追加: {last3_count}レース（{last3_count/len(df)*100:.1f}%）")
    else:
        safe_print("⚠️ 'race_bango' または 'kaisai_tsukihi' カラムが見つかりません")
        df['is_last_3_race'] = 0
    
    return df

def process_csv(input_path: str, output_path: str):
    """
    CSVファイルを処理
    
    Args:
        input_path: 入力CSVパス
        output_path: 出力CSVパス
    """
    safe_print(f"\n{'='*80}")
    safe_print(f"📄 処理中: {Path(input_path).name}")
    safe_print(f"{'='*80}")
    
    # データ読み込み
    try:
        df = pd.read_csv(input_path, encoding='shift-jis')
        safe_print(f"✅ 読み込み成功 (shift-jis): {len(df)}行 × {len(df.columns)}列")
    except:
        try:
            df = pd.read_csv(input_path, encoding='utf-8')
            safe_print(f"✅ 読み込み成功 (utf-8): {len(df)}行 × {len(df.columns)}列")
        except Exception as e:
            safe_print(f"❌ 読み込み失敗: {e}")
            return
    
    # 追加特徴量を生成
    df = add_top2_features(df)
    
    # 保存
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False, encoding='shift-jis')
        safe_print(f"💾 保存成功: {Path(output_path).name} ({len(df)}行 × {len(df.columns)}列)")
    except:
        df.to_csv(output_path, index=False, encoding='utf-8')
        safe_print(f"💾 保存成功 (utf-8): {Path(output_path).name} ({len(df)}行 × {len(df.columns)}列)")

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Phase 12: 2着以内特化の追加特徴量生成'
    )
    
    parser.add_argument('--input_dir', type=str, default='data/phase12_umatan/raw',
                       help='入力ディレクトリ')
    parser.add_argument('--output_dir', type=str, default='data/phase12_umatan/features',
                       help='出力ディレクトリ')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    safe_print(f"\n{'='*80}")
    safe_print(f"Phase 12: Step 1 - 2着以内特化の追加特徴量生成")
    safe_print(f"{'='*80}")
    safe_print(f"📂 入力ディレクトリ: {input_dir}")
    safe_print(f"📂 出力ディレクトリ: {output_dir}")
    
    # CSVファイルを検索
    csv_files = list(input_dir.glob("*.csv"))
    
    if not csv_files:
        safe_print("❌ CSVファイルが見つかりません")
        return
    
    safe_print(f"📄 発見したCSVファイル数: {len(csv_files)}")
    
    # 各ファイルを処理
    for csv_file in csv_files:
        output_path = output_dir / csv_file.name
        process_csv(str(csv_file), str(output_path))
    
    safe_print(f"\n{'='*80}")
    safe_print(f"✅ 全ファイル処理完了")
    safe_print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
