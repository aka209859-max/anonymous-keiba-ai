#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_target_to_time.py
CSVファイルのtargetカラムを走破タイム（秒）に変更

使用法:
    python convert_target_to_time.py <csvファイル名>

出力:
    {csv_file}_time.csv
"""
import pandas as pd
import sys
import os


def main():
    """メイン処理"""
    
    if len(sys.argv) < 2:
        print("使用法: python convert_target_to_time.py <csvファイル名>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"エラー: ファイル '{csv_file}' が見つかりません")
        sys.exit(1)
    
    print("=" * 80)
    print("target → 走破タイム 変換ツール")
    print("=" * 80)
    print(f"処理中: {csv_file}\n")
    
    # データ読み込み
    print("[1/4] データ読み込み中...")
    try:
        df = pd.read_csv(csv_file, encoding='shift-jis')
        print(f"  ✓ Shift-JIS で読み込み成功")
    except UnicodeDecodeError:
        print("  警告: Shift-JISで失敗。UTF-8で再試行...")
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"  ✓ UTF-8 で読み込み成功")
    except Exception as e:
        print(f"  ✗ エラー: {e}")
        sys.exit(1)
    
    print(f"  - データ件数: {len(df):,}件")
    print(f"  - カラム数: {len(df.columns)}個\n")
    
    # timeカラムが存在するか確認
    print("[2/4] タイムカラム確認中...")
    
    time_column = None
    if 'time' in df.columns:
        time_column = 'time'
        print(f"  ✓ 'time' カラムを検出")
    elif 'prev1_time' in df.columns:
        time_column = 'prev1_time'
        print(f"  ⚠️ 'time' カラムが見つかりません")
        print(f"  → 'prev1_time' カラムを代替使用（応急処置）")
    else:
        print(f"  ✗ エラー: タイムカラム（time または prev1_time）が見つかりません")
        print(f"  利用可能なカラム: {df.columns.tolist()}")
        sys.exit(1)
    
    # targetを走破タイムに変更
    print("\n[3/4] target を走破タイム（秒）に変換中...")
    
    if time_column == 'time':
        # timeは1/10秒単位 → 秒に変換
        df['target'] = df[time_column] / 10.0
        print(f"  - 変換式: target = time / 10.0")
    else:
        # prev1_timeをそのまま使用
        df['target'] = df[time_column]
        print(f"  - 変換式: target = prev1_time")
    
    # 統計情報
    print(f"\n  【変換前の統計】")
    print(f"    - {time_column} の範囲: {df[time_column].min()} ~ {df[time_column].max()}")
    print(f"    - {time_column} の平均: {df[time_column].mean():.2f}")
    
    # 欠損値・異常値を除去
    original_count = len(df)
    df = df[df['target'].notna()]
    df = df[df['target'] > 0]
    removed_count = original_count - len(df)
    
    if removed_count > 0:
        print(f"\n  ⚠️ 欠損値・異常値を除去: {removed_count}件")
    
    print(f"\n  【変換後の統計】")
    print(f"    - target（秒）の範囲: {df['target'].min():.2f}秒 ~ {df['target'].max():.2f}秒")
    print(f"    - target（秒）の平均: {df['target'].mean():.2f}秒")
    print(f"    - target（秒）の中央値: {df['target'].median():.2f}秒")
    print(f"    - target（秒）の標準偏差: {df['target'].std():.2f}秒\n")
    
    # 保存
    print("[4/4] 保存中...")
    output_file = csv_file.replace('.csv', '_time.csv')
    
    try:
        df.to_csv(output_file, index=False, encoding='shift-jis')
        print(f"  ✓ Shift-JIS で保存成功")
    except Exception as e:
        print(f"  警告: Shift-JISで保存失敗。UTF-8で再試行...")
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"  ✓ UTF-8 で保存成功")
    
    print("\n" + "=" * 80)
    print("完了！")
    print("=" * 80)
    print(f"\n出力ファイル: {output_file}")
    print(f"  - データ件数: {len(df):,}件")
    print(f"  - タイム範囲: {df['target'].min():.2f}秒 ~ {df['target'].max():.2f}秒")
    print(f"  - タイム平均: {df['target'].mean():.2f}秒\n")


if __name__ == "__main__":
    main()
