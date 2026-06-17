#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_features_v3.py
Phase 1: 特徴量作成スクリプト（統計特徴量17個：単純平均11個+加重平均6個）

Phase 0の生データから、67特徴量を作成します（元49個 + 統計17個）。

使用法:
    python prepare_features_v3.py <Phase0のCSVファイル> [オプション]

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
    4. 統計特徴量17個を追加（単純平均11個 + 加重平均6個）
    5. 特徴量フィルタリング（67個抽出）
    6. CSV保存
"""

import sys
import os
import pandas as pd
import numpy as np
import argparse
from pathlib import Path

# 必要な49特徴量（識別情報 + 学習用特徴量）
REQUIRED_FEATURES = [
    # 識別情報（6項目）
    'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 'ketto_toroku_bango', 'umaban',
    
    # レース情報（7項目）
    'kyori', 'track_code', 'babajotai_code_shiba', 'babajotai_code_dirt', 'tenko_code', 'shusso_tosu', 'grade_code',
    
    # 出馬情報（8項目）
    'wakuban', 'seibetsu_code', 'barei', 'futan_juryo', 'kishu_code', 'chokyoshi_code', 'blinker_shiyo_kubun', 'tozai_shozoku_code',
    
    # 馬情報（1項目）
    'moshoku_code',
    
    # 前走1（14項目）
    'prev1_rank', 'prev1_time', 'prev1_last3f', 'prev1_last4f', 'prev1_corner1', 'prev1_corner2', 'prev1_corner3', 'prev1_corner4',
    'prev1_weight', 'prev1_kyori', 'prev1_keibajo', 'prev1_track', 'prev1_baba_shiba', 'prev1_baba_dirt',
    
    # 前走2（6項目）
    'prev2_rank', 'prev2_time', 'prev2_last3f', 'prev2_weight', 'prev2_kyori', 'prev2_keibajo',
    
    # 前走3（3項目）
    'prev3_rank', 'prev3_time', 'prev3_weight',
    
    # 前走4（2項目）
    'prev4_rank', 'prev4_time',
    
    # 前走5（2項目）
    'prev5_rank', 'prev5_time',
]

# 単純平均統計特徴量（11項目）
SIMPLE_STATISTICAL_FEATURES = [
    'recent5_avg_rank',
    'recent5_top3_rate',
    'recent5_win_rate',
    'recent5_avg_time',
    'recent5_time_std',
    'recent5_avg_popularity',
    'recent5_favorites_rate',
    'recent5_avg_prize',
    'trend_rank_change',
    'distance_change',
    'track_change',
]

# 加重平均統計特徴量（6項目）
WEIGHTED_STATISTICAL_FEATURES = [
    'recent5_weighted_avg_rank',
    'recent5_weighted_avg_time',
    'recent3_avg_rank',
    'recent3_top3_rate',
    'form_trend',
    'consistency_score',
]


def load_data(csv_file, encoding=None):
    """Phase 0のCSVを読み込み"""
    print("\n" + "=" * 80)
    print("[1/8] Phase 0データ読み込み中...")
    print("=" * 80)
    print(f"ファイル: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"❌ エラー: ファイルが見つかりません - {csv_file}")
        sys.exit(1)
    
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
    """欠損値処理"""
    print("\n" + "=" * 80)
    print("[2/8] 欠損値処理中...")
    print("=" * 80)
    
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
    
    # 過去走データ → 0埋め
    print("\n[優先度1] 過去走データ → 0埋め")
    past_race_columns = [
        'prev1_rank', 'prev1_time', 'prev1_last3f', 'prev1_last4f',
        'prev1_corner1', 'prev1_corner2', 'prev1_corner3', 'prev1_corner4',
        'prev1_kyori', 'prev1_keibajo', 'prev1_track', 'prev1_baba_shiba', 'prev1_baba_dirt',
        'prev2_rank', 'prev2_time', 'prev2_last3f', 'prev2_kyori', 'prev2_keibajo',
        'prev3_rank', 'prev3_time', 'prev4_rank', 'prev4_time', 'prev5_rank', 'prev5_time',
    ]
    
    filled_count = 0
    for col in past_race_columns:
        if col in df.columns:
            before_null = df[col].isnull().sum()
            if before_null > 0:
                df[col] = df[col].fillna(0)
                filled_count += 1
                print(f"  - {col}: {before_null}件 → 0埋め完了")
    
    if filled_count == 0:
        print("  - 欠損値なし")
    
    # 馬体重 → 平均値補完
    print("\n[優先度2] 物理量（馬体重・負担重量） → 平均値補完")
    weight_columns = ['prev1_weight', 'prev2_weight', 'prev3_weight']
    
    filled_count = 0
    for col in weight_columns:
        if col in df.columns:
            before_null = df[col].isnull().sum()
            if before_null > 0:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                mean_value = df[col].mean()
                
                if pd.notna(mean_value):
                    df[col] = df[col].fillna(mean_value)
                    filled_count += 1
                    print(f"  - {col}: {before_null}件 → 平均値補完完了（平均値: {mean_value:.2f}）")
                else:
                    df[col] = df[col].fillna(0)
                    filled_count += 1
                    print(f"  - {col}: {before_null}件 → 全て欠損のため0埋め")
    
    if 'futan_juryo' in df.columns:
        before_null = df['futan_juryo'].isnull().sum()
        if before_null > 0:
            df['futan_juryo'] = pd.to_numeric(df['futan_juryo'], errors='coerce')
            mean_value = df['futan_juryo'].mean()
            if pd.notna(mean_value):
                df['futan_juryo'] = df['futan_juryo'].fillna(mean_value)
                filled_count += 1
                print(f"  - futan_juryo: {before_null}件 → 平均値補完完了（平均値: {mean_value:.2f}）")
    
    if filled_count == 0:
        print("  - 欠損値なし")
    
    print("\n[優先度3] 行削除")
    print("  ⚠️  行削除は実行しません（全馬の予測が必要）")
    print("\n✅ 欠損値処理完了")
    
    return df


def generate_race_id(df):
    """Race IDを生成"""
    print("\n" + "=" * 80)
    print("[3/8] Race ID生成中...")
    print("=" * 80)
    
    required_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"❌ エラー: 必須カラムが見つかりません - {missing_cols}")
        sys.exit(1)
    
    def create_race_id(row):
        kaisai_nen = str(row['kaisai_nen'])
        kaisai_tsukihi = str(row['kaisai_tsukihi']).zfill(4)
        keibajo_code = str(row['keibajo_code']).zfill(2)
        race_bango = str(row['race_bango']).zfill(2)
        return int(kaisai_nen + kaisai_tsukihi + keibajo_code + race_bango)
    
    df['race_id'] = df.apply(create_race_id, axis=1)
    
    print("✅ Race ID生成完了")
    print(f"  - ユニークなレース数: {df['race_id'].nunique():,}件")
    print(f"  - サンプルRace ID: {df['race_id'].iloc[0]}")
    
    return df


def add_simple_statistical_features(df):
    """単純平均統計特徴量11個を追加"""
    print("\n" + "=" * 80)
    print("[4/8] 単純平均統計特徴量追加中（11項目）...")
    print("=" * 80)
    
    rank_cols = ['prev1_rank', 'prev2_rank', 'prev3_rank', 'prev4_rank', 'prev5_rank']
    time_cols = ['prev1_time', 'prev2_time', 'prev3_time', 'prev4_time', 'prev5_time']
    
    for col in rank_cols + time_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 1. recent5_avg_rank
    print("  [1/11] recent5_avg_rank - 直近5走平均着順")
    rank_cols_existing = [col for col in rank_cols if col in df.columns]
    if rank_cols_existing:
        df['recent5_avg_rank'] = df[rank_cols_existing].replace(0, np.nan).mean(axis=1).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['recent5_avg_rank'] = 0
        print("    ⚠️  着順データなし → 0埋め")
    
    # 2. recent5_top3_rate
    print("  [2/11] recent5_top3_rate - 直近5走3着以内率")
    if rank_cols_existing:
        top3_count = df[rank_cols_existing].apply(lambda x: ((x > 0) & (x <= 3)).sum(), axis=1)
        valid_count = df[rank_cols_existing].apply(lambda x: (x > 0).sum(), axis=1)
        df['recent5_top3_rate'] = (top3_count / valid_count.replace(0, 1)).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['recent5_top3_rate'] = 0
        print("    ⚠️  着順データなし → 0埋め")
    
    # 3. recent5_win_rate
    print("  [3/11] recent5_win_rate - 直近5走1着率")
    if rank_cols_existing:
        win_count = df[rank_cols_existing].apply(lambda x: (x == 1).sum(), axis=1)
        valid_count = df[rank_cols_existing].apply(lambda x: (x > 0).sum(), axis=1)
        df['recent5_win_rate'] = (win_count / valid_count.replace(0, 1)).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['recent5_win_rate'] = 0
        print("    ⚠️  着順データなし → 0埋め")
    
    # 4. recent5_avg_time
    print("  [4/11] recent5_avg_time - 直近5走平均タイム")
    time_cols_existing = [col for col in time_cols if col in df.columns]
    if time_cols_existing:
        df['recent5_avg_time'] = df[time_cols_existing].replace(0, np.nan).mean(axis=1).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['recent5_avg_time'] = 0
        print("    ⚠️  タイムデータなし → 0埋め")
    
    # 5. recent5_time_std
    print("  [5/11] recent5_time_std - 直近5走タイム標準偏差")
    if time_cols_existing:
        df['recent5_time_std'] = df[time_cols_existing].replace(0, np.nan).std(axis=1).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['recent5_time_std'] = 0
        print("    ⚠️  タイムデータなし → 0埋め")
    
    # 6-8: Phase 0にないデータ
    print("  [6/11] recent5_avg_popularity - 直近5走平均人気")
    df['recent5_avg_popularity'] = 0
    print("    ⚠️  Phase 0にデータなし → 0埋め")
    
    print("  [7/11] recent5_favorites_rate - 直近5走1-3番人気率")
    df['recent5_favorites_rate'] = 0
    print("    ⚠️  Phase 0にデータなし → 0埋め")
    
    print("  [8/11] recent5_avg_prize - 直近5走平均賞金")
    df['recent5_avg_prize'] = 0
    print("    ⚠️  Phase 0にデータなし → 0埋め")
    
    # 9. trend_rank_change
    print("  [9/11] trend_rank_change - 着順トレンド")
    if 'prev1_rank' in df.columns and 'prev5_rank' in df.columns:
        prev1 = df['prev1_rank'].replace(0, np.nan)
        prev5 = df['prev5_rank'].replace(0, np.nan)
        df['trend_rank_change'] = (prev1 - prev5).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['trend_rank_change'] = 0
        print("    ⚠️  着順データ不足 → 0埋め")
    
    # 10. distance_change
    print("  [10/11] distance_change - 前走距離変化")
    if 'kyori' in df.columns and 'prev1_kyori' in df.columns:
        kyori = df['kyori'].replace(0, np.nan)
        prev1_kyori = df['prev1_kyori'].replace(0, np.nan)
        df['distance_change'] = (kyori - prev1_kyori).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['distance_change'] = 0
        print("    ⚠️  距離データ不足 → 0埋め")
    
    # 11. track_change
    print("  [11/11] track_change - 前走コース変更フラグ")
    if 'track_code' in df.columns and 'prev1_track' in df.columns:
        df['track_change'] = (df['track_code'] != df['prev1_track']).astype(int)
        print(f"    ✅ 完了")
    else:
        df['track_change'] = 0
        print("    ⚠️  コースデータ不足 → 0埋め")
    
    print("\n✅ 単純平均統計特徴量追加完了（11項目）")
    
    return df


def add_weighted_statistical_features(df):
    """加重平均統計特徴量6個を追加"""
    print("\n" + "=" * 80)
    print("[5/8] 加重平均統計特徴量追加中（6項目）...")
    print("=" * 80)
    print("  重み設定: [5, 4, 3, 2, 1] - 直近ほど重視")
    
    weights = [5, 4, 3, 2, 1]
    rank_cols = ['prev1_rank', 'prev2_rank', 'prev3_rank', 'prev4_rank', 'prev5_rank']
    time_cols = ['prev1_time', 'prev2_time', 'prev3_time', 'prev4_time', 'prev5_time']
    
    # 1. recent5_weighted_avg_rank
    print("\n  [1/6] recent5_weighted_avg_rank - 直近5走加重平均着順")
    weighted_sum = pd.Series(0, index=df.index, dtype=float)
    weight_sum = pd.Series(0, index=df.index, dtype=float)
    
    for i, col in enumerate(rank_cols):
        if col in df.columns:
            valid_mask = df[col] > 0
            weighted_sum += df[col] * weights[i] * valid_mask
            weight_sum += weights[i] * valid_mask
    
    df['recent5_weighted_avg_rank'] = (weighted_sum / weight_sum.replace(0, 1)).fillna(0)
    print(f"    ✅ 完了")
    
    # 2. recent5_weighted_avg_time
    print("  [2/6] recent5_weighted_avg_time - 直近5走加重平均タイム")
    weighted_sum_time = pd.Series(0, index=df.index, dtype=float)
    weight_sum_time = pd.Series(0, index=df.index, dtype=float)
    
    for i, col in enumerate(time_cols):
        if col in df.columns:
            valid_mask = df[col] > 0
            weighted_sum_time += df[col] * weights[i] * valid_mask
            weight_sum_time += weights[i] * valid_mask
    
    df['recent5_weighted_avg_time'] = (weighted_sum_time / weight_sum_time.replace(0, 1)).fillna(0)
    print(f"    ✅ 完了")
    
    # 3. recent3_avg_rank
    print("  [3/6] recent3_avg_rank - 直近3走平均着順")
    recent3_cols = ['prev1_rank', 'prev2_rank', 'prev3_rank']
    recent3_existing = [col for col in recent3_cols if col in df.columns]
    if recent3_existing:
        df['recent3_avg_rank'] = df[recent3_existing].replace(0, np.nan).mean(axis=1).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['recent3_avg_rank'] = 0
        print("    ⚠️  着順データなし → 0埋め")
    
    # 4. recent3_top3_rate
    print("  [4/6] recent3_top3_rate - 直近3走3着以内率")
    if recent3_existing:
        top3_count = df[recent3_existing].apply(lambda x: ((x > 0) & (x <= 3)).sum(), axis=1)
        valid_count = df[recent3_existing].apply(lambda x: (x > 0).sum(), axis=1)
        df['recent3_top3_rate'] = (top3_count / valid_count.replace(0, 1)).fillna(0)
        print(f"    ✅ 完了")
    else:
        df['recent3_top3_rate'] = 0
        print("    ⚠️  着順データなし → 0埋め")
    
    # 5. form_trend
    print("  [5/6] form_trend - 調子トレンド（加重平均 - 単純平均）")
    df['form_trend'] = df['recent5_weighted_avg_rank'] - df['recent5_avg_rank']
    print(f"    ✅ 完了（正の値=調子下降、負の値=調子上昇）")
    
    # 6. consistency_score
    print("  [6/6] consistency_score - 安定度スコア")
    df['consistency_score'] = 1 / (df['recent5_time_std'] + 1)
    print(f"    ✅ 完了（値が大きいほど安定）")
    
    print("\n✅ 加重平均統計特徴量追加完了（6項目）")
    
    return df


def filter_features(df):
    """必要な特徴量のみを抽出（67個）"""
    print("\n" + "=" * 80)
    print("[6/8] 特徴量フィルタリング中...")
    print("=" * 80)
    
    all_features = ['race_id'] + REQUIRED_FEATURES + SIMPLE_STATISTICAL_FEATURES + WEIGHTED_STATISTICAL_FEATURES
    
    available_features = [col for col in all_features if col in df.columns]
    missing_features = [col for col in all_features if col not in df.columns]
    
    print(f"✅ 使用可能な特徴量: {len(available_features)} / {len(all_features)}")
    
    if missing_features:
        print(f"⚠️  不足している特徴量: {len(missing_features)}個")
        for col in missing_features[:10]:
            print(f"  - {col}")
        if len(missing_features) > 10:
            print(f"  ... 他 {len(missing_features) - 10}個")
    
    df_filtered = df[available_features].copy()
    
    print(f"\n✅ 特徴量フィルタリング完了")
    print(f"  - 最終特徴量数: {len(df_filtered.columns)}個")
    print(f"  - 内訳: race_id(1) + 元特徴量(49) + 単純平均(11) + 加重平均(6)")
    
    return df_filtered


def convert_data_types(df):
    """データ型を適切に変換"""
    print("\n" + "=" * 80)
    print("[7/8] データ型変換中...")
    print("=" * 80)
    
    numeric_columns = [
        'kyori', 'shusso_tosu', 'wakuban', 'barei', 'futan_juryo',
        'prev1_rank', 'prev1_time', 'prev1_last3f', 'prev1_last4f',
        'prev1_corner1', 'prev1_corner2', 'prev1_corner3', 'prev1_corner4',
        'prev1_weight', 'prev1_kyori',
        'prev2_rank', 'prev2_time', 'prev2_last3f', 'prev2_weight', 'prev2_kyori',
        'prev3_rank', 'prev3_time', 'prev3_weight',
        'prev4_rank', 'prev4_time',
        'prev5_rank', 'prev5_time',
    ] + SIMPLE_STATISTICAL_FEATURES + WEIGHTED_STATISTICAL_FEATURES
    
    converted_count = 0
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0)
            converted_count += 1
    
    print(f"✅ データ型変換完了")
    print(f"  - 数値カラム: {converted_count}個")
    
    return df


def save_features(df, output_file):
    """Phase 1の特徴量CSVを保存"""
    print("\n" + "=" * 80)
    print("[8/8] CSV保存中...")
    print("=" * 80)
    
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ ディレクトリ作成: {output_dir}")
    
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
        description='Phase 1: 特徴量作成スクリプト（統計特徴量17個：単純平均11個+加重平均6個）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
    python prepare_features_v3.py data/raw/2026/02/川崎_20260205_raw.csv
    python prepare_features_v3.py data/raw/2026/02/川崎_20260205_raw.csv --output my_features.csv
    python prepare_features_v3.py data/raw/2026/02/川崎_20260205_raw.csv --encoding utf-8
        """
    )
    
    parser.add_argument('csv_file', help='Phase 0のCSVファイルパス')
    parser.add_argument('--output', type=str, help='出力CSVファイル名（デフォルト: 自動生成）')
    parser.add_argument('--encoding', type=str, help='入力CSVのエンコーディング（デフォルト: 自動判定）')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Phase 1: 特徴量作成スクリプト（統計特徴量17個：単純平均11個+加重平均6個）")
    print("=" * 80)
    print(f"入力ファイル: {args.csv_file}")
    
    if args.output is None:
        basename = os.path.basename(args.csv_file)
        basename_noext = os.path.splitext(basename)[0]
        output_basename = basename_noext.replace('_raw', '_features') + '.csv'
        input_path = Path(args.csv_file)
        
        if 'data' in input_path.parts and 'raw' in input_path.parts:
            output_parts = list(input_path.parts)
            raw_idx = output_parts.index('raw')
            output_parts[raw_idx] = 'features'
            output_parts[-1] = output_basename
            args.output = str(Path(*output_parts))
        else:
            args.output = str(input_path.parent / output_basename)
    
    print(f"出力ファイル: {args.output}")
    print()
    
    # Phase 1: 特徴量作成
    df = load_data(args.csv_file, encoding=args.encoding)
    df = preprocess_missing_values(df)
    df = generate_race_id(df)
    df = add_simple_statistical_features(df)
    df = add_weighted_statistical_features(df)
    df = filter_features(df)
    df = convert_data_types(df)
    save_features(df, args.output)
    
    print("\n" + "=" * 80)
    print("✅ Phase 1: 特徴量作成完了（統計特徴量17個：単純平均11個+加重平均6個）")
    print("=" * 80)
    print(f"\n次のステップ: Phase 3〜5で予測を実行してください")
    print(f"  Phase 3（二値分類）: python predict_phase3.py {args.output}")
    print(f"  Phase 4（ランキング）: python predict_phase4_ranking.py {args.output}")
    print(f"  Phase 4（回帰）: python predict_phase4_regression.py {args.output}")


if __name__ == '__main__':
    main()
