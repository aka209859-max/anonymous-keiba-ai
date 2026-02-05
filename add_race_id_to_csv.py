#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_race_id_to_csv.py
既存のCSVファイルに race_id カラムを追加

使用法:
    python add_race_id_to_csv.py <csvファイル名>

出力:
    {csv_file}_with_race_id.csv
"""
import pandas as pd
import sys
import os


def main():
    """メイン処理"""
    
    if len(sys.argv) < 2:
        print("使用法: python add_race_id_to_csv.py <csvファイル名>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"エラー: ファイル '{csv_file}' が見つかりません")
        sys.exit(1)
    
    print("=" * 80)
    print("race_id カラム追加ツール")
    print("=" * 80)
    print(f"処理中: {csv_file}\n")
    
    # データ読み込み
    print("[1/3] データ読み込み中...")
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
    
    # 必要なカラムの確認
    required_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"エラー: 必要なカラムが見つかりません: {missing_cols}")
        print(f"利用可能なカラム: {df.columns.tolist()}")
        sys.exit(1)
    
    # race_idを作成
    print("[2/3] race_id 作成中...")
    df['race_id'] = (
        df['kaisai_nen'].astype(str) + 
        df['kaisai_tsukihi'].astype(str).str.zfill(4) + 
        df['keibajo_code'].astype(str) + 
        df['race_bango'].astype(str).str.zfill(2)
    )
    
    unique_races = df['race_id'].nunique()
    print(f"  ✓ race_id 作成完了")
    print(f"  - ユニークなレース数: {unique_races:,}件")
    print(f"  - race_id の例: {df['race_id'].iloc[0]}\n")
    
    # 保存
    print("[3/3] 保存中...")
    output_file = csv_file.replace('.csv', '_with_race_id.csv')
    
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
    print(f"  - レース数: {unique_races:,}件")
    print(f"  - データ件数: {len(df):,}件")
    print(f"  - カラム数: {len(df.columns)}個（race_id を追加）\n")


if __name__ == "__main__":
    main()
