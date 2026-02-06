#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_features.py
Phase 1: 特徴量作成スクリプト

Phase 0の生データから、学習済みモデルが要求する49特徴量を作成します。

使用法:
    python prepare_features.py <Phase0のCSVファイル> [オプション]

オプション:
    --output FILE       出力CSVファイル名（デフォルト: 自動生成）
    --encoding ENC      入力CSVのエンコーディング（デフォルト: 自動判定）

出力:
    - {keibajo}_{YYYYMMDD}_features.csv: Phase 1の特徴量CSV
    - data/features/YYYY/MM/ に保存

処理内容:
    1. Phase 0のCSV読み込み
    2. 欠損値処理（過去走: 0埋め、物理量: 平均値補完）
    3. Race ID生成
    4. 特徴量フィルタリング（49個抽出）
    5. CSV保存
"""

import sys
import os
import pandas as pd
import numpy as np
import argparse
from pathlib import Path

# 必要な49特徴量（識別情報 + 学習用特徴量）
REQUIRED_FEATURES = [
    # ============================================
    # 識別情報（6項目）
    # ============================================
    'kaisai_nen',
    'kaisai_tsukihi',
    'keibajo_code',
    'race_bango',
    'ketto_toroku_bango',
    'umaban',
    
    # ============================================
    # レース情報（7項目）
    # ============================================
    'kyori',
    'track_code',
    'babajotai_code_shiba',
    'babajotai_code_dirt',
    'tenko_code',
    'shusso_tosu',
    'grade_code',
    
    # ============================================
    # 出馬情報（8項目）
    # ============================================
    'wakuban',
    'seibetsu_code',
    'barei',
    'futan_juryo',
    'kishu_code',
    'chokyoshi_code',
    'blinker_shiyo_kubun',
    'tozai_shozoku_code',
    
    # ============================================
    # 馬情報（1項目）
    # ============================================
    'moshoku_code',
    
    # ============================================
    # 前走1（14項目）
    # ============================================
    'prev1_rank',
    'prev1_time',
    'prev1_last3f',
    'prev1_last4f',
    'prev1_corner1',
    'prev1_corner2',
    'prev1_corner3',
    'prev1_corner4',
    'prev1_weight',
    'prev1_kyori',
    'prev1_keibajo',
    'prev1_track',
    'prev1_baba_shiba',
    'prev1_baba_dirt',
    
    # ============================================
    # 前走2（6項目）
    # ============================================
    'prev2_rank',
    'prev2_time',
    'prev2_last3f',
    'prev2_weight',
    'prev2_kyori',
    'prev2_keibajo',
    
    # ============================================
    # 前走3（3項目）
    # ============================================
    'prev3_rank',
    'prev3_time',
    'prev3_weight',
    
    # ============================================
    # 前走4（2項目）
    # ============================================
    'prev4_rank',
    'prev4_time',
    
    # ============================================
    # 前走5（2項目）
    # ============================================
    'prev5_rank',
    'prev5_time',
]


def load_data(csv_file, encoding=None):
    """
    Phase 0のCSVを読み込み
    
    Args:
        csv_file: CSVファイルパス
        encoding: エンコーディング（Noneの場合は自動判定）
    
    Returns:
        pd.DataFrame: 読み込んだデータ
    """
    print("\n" + "=" * 80)
    print("[1/6] Phase 0データ読み込み中...")
    print("=" * 80)
    print(f"ファイル: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"❌ エラー: ファイルが見つかりません - {csv_file}")
        sys.exit(1)
    
    # エンコーディング自動判定
    if encoding is None:
        try:
            df = pd.read_csv(csv_file, encoding='shift-jis')
            print("✅ エンコーディング: Shift-JIS")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                print("✅ エンコーディング: UTF-8")
            except Exception as e:
                print(f"❌ エラー: CSVファイルの読み込みに失敗しました - {e}")
                sys.exit(1)
    else:
        try:
            df = pd.read_csv(csv_file, encoding=encoding)
            print(f"✅ エンコーディング: {encoding}")
        except Exception as e:
            print(f"❌ エラー: CSVファイルの読み込みに失敗しました - {e}")
            sys.exit(1)
    
    print(f"✅ データ読み込み完了")
    print(f"  - レコード数: {len(df):,}件")
    print(f"  - カラム数: {len(df.columns)}個")
    
    return df


def preprocess_missing_values(df):
    """
    欠損値処理
    
    優先度1: 過去走データ → 0埋め
    優先度2: 物理量（馬体重・負担重量） → 平均値補完
    優先度3: 行削除 → 禁止
    
    Args:
        df: DataFrame
    
    Returns:
        pd.DataFrame: 欠損値処理後のデータ
    """
    print("\n" + "=" * 80)
    print("[2/6] 欠損値処理中...")
    print("=" * 80)
    
    # 欠損値の確認
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    
    if len(null_cols) > 0:
        print(f"⚠️  欠損値が検出されました（{len(null_cols)}カラム）")
        for col in null_cols.index[:10]:
            null_pct = null_counts[col] / len(df) * 100
            print(f"  - {col}: {null_counts[col]}件 ({null_pct:.1f}%)")
        if len(null_cols) > 10:
            print(f"  ... 他 {len(null_cols) - 10}カラム")
    else:
        print("✅ 欠損値はありません")
    
    # ============================================
    # 優先度1: 過去走データ → 0埋め
    # ============================================
    print("\n[優先度1] 過去走データ → 0埋め")
    
    past_race_columns = [
        'prev1_rank', 'prev1_time', 'prev1_last3f', 'prev1_last4f',
        'prev1_corner1', 'prev1_corner2', 'prev1_corner3', 'prev1_corner4',
        'prev1_kyori', 'prev1_keibajo', 'prev1_track', 
        'prev1_baba_shiba', 'prev1_baba_dirt',
        
        'prev2_rank', 'prev2_time', 'prev2_last3f',
        'prev2_kyori', 'prev2_keibajo',
        
        'prev3_rank', 'prev3_time',
        'prev4_rank', 'prev4_time',
        'prev5_rank', 'prev5_time',
    ]
    
    filled_count = 0
    for col in past_race_columns:
        if col in df.columns:
            before_null = df[col].isnull().sum()
            if before_null > 0:
                df[col].fillna(0, inplace=True)
                filled_count += 1
                print(f"  - {col}: {before_null}件 → 0埋め完了")
    
    if filled_count == 0:
        print("  - 欠損値なし")
    
    # ============================================
    # 優先度2: 物理量（馬体重） → 平均値補完
    # ============================================
    print("\n[優先度2] 物理量（馬体重・負担重量） → 平均値補完")
    
    weight_columns = ['prev1_weight', 'prev2_weight', 'prev3_weight']
    
    filled_count = 0
    for col in weight_columns:
        if col in df.columns:
            before_null = df[col].isnull().sum()
            if before_null > 0:
                # 数値型に変換
                df[col] = pd.to_numeric(df[col], errors='coerce')
                mean_value = df[col].mean()
                
                if pd.notna(mean_value):
                    df[col].fillna(mean_value, inplace=True)
                    filled_count += 1
                    print(f"  - {col}: {before_null}件 → 平均値補完完了（平均値: {mean_value:.2f}）")
                else:
                    df[col].fillna(0, inplace=True)
                    filled_count += 1
                    print(f"  - {col}: {before_null}件 → 全て欠損のため0埋め")
    
    # 負担重量
    if 'futan_juryo' in df.columns:
        before_null = df['futan_juryo'].isnull().sum()
        if before_null > 0:
            df['futan_juryo'] = pd.to_numeric(df['futan_juryo'], errors='coerce')
            mean_value = df['futan_juryo'].mean()
            
            if pd.notna(mean_value):
                df['futan_juryo'].fillna(mean_value, inplace=True)
                filled_count += 1
                print(f"  - futan_juryo: {before_null}件 → 平均値補完完了（平均値: {mean_value:.2f}）")
    
    if filled_count == 0:
        print("  - 欠損値なし")
    
    # ============================================
    # 優先度3: 行削除 → 実行しない
    # ============================================
    print("\n[優先度3] 行削除")
    print("  ⚠️  行削除は実行しません（全馬の予測が必要）")
    
    print("\n✅ 欠損値処理完了")
    
    return df


def generate_race_id(df):
    """
    Race IDを生成（12桁）
    
    フォーマット: YYYY + MM + DD + JJ + RR
    - YYYY: 開催年（4桁）
    - MMDD: 月日（4桁）
    - JJ: 競馬場コード（2桁）
    - RR: レース番号（2桁）
    
    Args:
        df: DataFrame
    
    Returns:
        pd.DataFrame: Race ID追加後のデータ
    """
    print("\n" + "=" * 80)
    print("[3/6] Race ID生成中...")
    print("=" * 80)
    
    # 必須カラムの確認
    required_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"❌ エラー: 必須カラムが見つかりません - {missing_cols}")
        sys.exit(1)
    
    # Race ID生成
    def create_race_id(row):
        kaisai_nen = str(row['kaisai_nen'])
        kaisai_tsukihi = str(row['kaisai_tsukihi']).zfill(4)
        keibajo_code = str(row['keibajo_code']).zfill(2)
        race_bango = str(row['race_bango']).zfill(2)
        
        race_id = kaisai_nen + kaisai_tsukihi + keibajo_code + race_bango
        return int(race_id)
    
    df['race_id'] = df.apply(create_race_id, axis=1)
    
    print("✅ Race ID生成完了")
    print(f"  - ユニークなレース数: {df['race_id'].nunique():,}件")
    print(f"  - サンプルRace ID: {df['race_id'].iloc[0]}")
    
    return df


def filter_features(df):
    """
    必要な特徴量のみを抽出
    
    Args:
        df: DataFrame
    
    Returns:
        pd.DataFrame: フィルタリング後のデータ
    """
    print("\n" + "=" * 80)
    print("[4/6] 特徴量フィルタリング中...")
    print("=" * 80)
    
    # race_idを追加
    all_features = ['race_id'] + REQUIRED_FEATURES
    
    # 存在する特徴量のみを抽出
    available_features = [col for col in all_features if col in df.columns]
    missing_features = [col for col in all_features if col not in df.columns]
    
    print(f"✅ 使用可能な特徴量: {len(available_features)} / {len(all_features)}")
    
    if missing_features:
        print(f"⚠️  不足している特徴量: {len(missing_features)}個")
        for col in missing_features[:10]:
            print(f"  - {col}")
        if len(missing_features) > 10:
            print(f"  ... 他 {len(missing_features) - 10}個")
    
    # 特徴量抽出
    df_filtered = df[available_features].copy()
    
    print(f"\n✅ 特徴量フィルタリング完了")
    print(f"  - 最終特徴量数: {len(df_filtered.columns)}個")
    
    return df_filtered


def convert_data_types(df):
    """
    データ型を適切に変換
    
    Args:
        df: DataFrame
    
    Returns:
        pd.DataFrame: データ型変換後のデータ
    """
    print("\n" + "=" * 80)
    print("[5/6] データ型変換中...")
    print("=" * 80)
    
    # 数値カラムの変換
    numeric_columns = [
        'kyori', 'shusso_tosu', 'wakuban', 'barei', 'futan_juryo',
        'prev1_rank', 'prev1_time', 'prev1_last3f', 'prev1_last4f',
        'prev1_corner1', 'prev1_corner2', 'prev1_corner3', 'prev1_corner4',
        'prev1_weight', 'prev1_kyori',
        'prev2_rank', 'prev2_time', 'prev2_last3f', 'prev2_weight', 'prev2_kyori',
        'prev3_rank', 'prev3_time', 'prev3_weight',
        'prev4_rank', 'prev4_time',
        'prev5_rank', 'prev5_time',
    ]
    
    converted_count = 0
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col].fillna(0, inplace=True)
            converted_count += 1
    
    print(f"✅ データ型変換完了")
    print(f"  - 数値カラム: {converted_count}個")
    
    return df


def save_features(df, output_file):
    """
    Phase 1の特徴量CSVを保存
    
    Args:
        df: DataFrame
        output_file: 出力ファイルパス
    """
    print("\n" + "=" * 80)
    print("[6/6] CSV保存中...")
    print("=" * 80)
    
    # 出力ディレクトリの作成
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ ディレクトリ作成: {output_dir}")
    
    # CSV保存
    try:
        df.to_csv(output_file, index=False, encoding='shift-jis')
        print(f"✅ CSV保存完了（Shift-JIS）")
    except Exception as e:
        print(f"⚠️  Shift-JISで保存失敗: {e}")
        print("  UTF-8で再試行...")
        try:
            output_file_utf8 = output_file.replace('.csv', '_utf8.csv')
            df.to_csv(output_file_utf8, index=False, encoding='utf-8')
            print(f"✅ CSV保存完了（UTF-8）: {output_file_utf8}")
            output_file = output_file_utf8
        except Exception as e2:
            print(f"❌ エラー: CSV保存に失敗しました - {e2}")
            sys.exit(1)
    
    print(f"  - 出力ファイル: {output_file}")
    print(f"  - レコード数: {len(df):,}件")
    print(f"  - カラム数: {len(df.columns)}個")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Phase 1: 特徴量作成スクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    # 基本的な使い方
    python prepare_features.py data/raw/2026/02/川崎_20260205_raw.csv
    
    # 出力ファイル名を指定
    python prepare_features.py data/raw/2026/02/川崎_20260205_raw.csv --output my_features.csv
    
    # エンコーディングを指定
    python prepare_features.py data/raw/2026/02/川崎_20260205_raw.csv --encoding utf-8
        """
    )
    
    parser.add_argument('csv_file', help='Phase 0のCSVファイルパス')
    parser.add_argument('--output', type=str, help='出力CSVファイル名（デフォルト: 自動生成）')
    parser.add_argument('--encoding', type=str, help='入力CSVのエンコーディング（デフォルト: 自動判定）')
    
    args = parser.parse_args()
    
    # パラメータ表示
    print("=" * 80)
    print("Phase 1: 特徴量作成スクリプト")
    print("=" * 80)
    print(f"入力ファイル: {args.csv_file}")
    
    # 出力ファイル名の自動生成
    if args.output is None:
        # ファイル名から情報抽出
        basename = os.path.basename(args.csv_file)
        basename_noext = os.path.splitext(basename)[0]
        
        # raw → features に置き換え
        output_basename = basename_noext.replace('_raw', '_features') + '.csv'
        
        # Phase 0のパスから Phase 1のパスを生成
        input_path = Path(args.csv_file)
        
        # data/raw/YYYY/MM/ → data/features/YYYY/MM/ に変更
        if 'data' in input_path.parts and 'raw' in input_path.parts:
            output_parts = list(input_path.parts)
            raw_idx = output_parts.index('raw')
            output_parts[raw_idx] = 'features'
            output_parts[-1] = output_basename
            args.output = str(Path(*output_parts))
        else:
            # data/raw/が見つからない場合は同じディレクトリに保存
            args.output = str(input_path.parent / output_basename)
    
    print(f"出力ファイル: {args.output}")
    print()
    
    # ============================================
    # Phase 1: 特徴量作成
    # ============================================
    
    # [1/6] データ読み込み
    df = load_data(args.csv_file, encoding=args.encoding)
    
    # [2/6] 欠損値処理
    df = preprocess_missing_values(df)
    
    # [3/6] Race ID生成
    df = generate_race_id(df)
    
    # [4/6] 特徴量フィルタリング
    df = filter_features(df)
    
    # [5/6] データ型変換
    df = convert_data_types(df)
    
    # [6/6] CSV保存
    save_features(df, args.output)
    
    # 完了
    print("\n" + "=" * 80)
    print("✅ Phase 1: 特徴量作成完了")
    print("=" * 80)
    print(f"\n次のステップ: Phase 3〜5で予測を実行してください")
    print(f"  Phase 3（二値分類）: python predict_phase3.py {args.output}")
    print(f"  Phase 4（ランキング）: python predict_phase4_ranking.py {args.output}")
    print(f"  Phase 4（回帰）: python predict_phase4_regression.py {args.output}")


if __name__ == '__main__':
    main()
