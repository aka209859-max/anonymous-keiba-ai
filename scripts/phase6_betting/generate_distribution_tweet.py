# -*- coding: utf-8 -*-
"""
ツイート用コピペフォーマット生成スクリプト
地方競馬AI予想システム - Phase 6 Twitter投稿用
全14競馬場対応

フォーマット:
【4/9 川崎競馬 AI予想結果】
予想：1R ①③⑤ → 結果：
予想：2R ②④⑦ → 結果：
予想：3R ①②⑥ → 結果：

本日：0/0的中（的中率-%）
今週累計：0/0的中（的中率-%）
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime


# 競馬場コード→日本語名のマッピング
KEIBAJO_CODE_TO_NAME = {
    '30': '門別', '35': '盛岡', '36': '水沢', '42': '浦和',
    '43': '船橋', '44': '大井', '45': '川崎', '46': '金沢',
    '47': '笠松', '48': '名古屋', '50': '園田', '51': '姫路',
    '54': '高知', '55': '佐賀',
}


def safe_print(msg):
    """安全な出力（Windows CP932対応）"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('cp932', errors='ignore').decode('cp932'))


def number_to_circled(num):
    """
    数字を丸数字に変換
    
    Args:
        num: 1-20の整数
    
    Returns:
        str: 丸数字（①-⑳）
    """
    circled_numbers = {
        1: '①', 2: '②', 3: '③', 4: '④', 5: '⑤',
        6: '⑥', 7: '⑦', 8: '⑧', 9: '⑨', 10: '⑩',
        11: '⑪', 12: '⑫', 13: '⑬', 14: '⑭', 15: '⑮',
        16: '⑯', 17: '⑰', 18: '⑱', 19: '⑲', 20: '⑳'
    }
    return circled_numbers.get(num, str(num))


def get_keibajo_name_from_df(df):
    """
    DataFrameの keibajo_code から競馬場日本語名を取得
    
    Args:
        df: ensemble結果のDataFrame
    
    Returns:
        str: 競馬場の日本語名（例: '高知'）
    """
    if 'keibajo_code' in df.columns:
        keibajo_code = str(int(df['keibajo_code'].iloc[0]))
        return KEIBAJO_CODE_TO_NAME.get(keibajo_code, '競馬場')
    return '競馬場'


def generate_tweet_format(df_race, race_num):
    """
    ツイート用フォーマット生成（予想結果版）
    
    Args:
        df_race: レースデータ（DataFrameの1レース分）
        race_num: レース番号
    
    Returns:
        str: ツイート用フォーマット文字列（例: "予想：1R ①③⑤ → 結果："）
    """
    # 上位3頭を取得
    top_horses = df_race.nsmallest(3, 'final_rank')['umaban'].tolist()
    
    if len(top_horses) < 1:
        return ""
    
    # 丸数字に変換
    circled_horses = ''.join([number_to_circled(int(h)) for h in top_horses])
    
    return f"予想：{race_num}R {circled_horses} → 結果："


def generate_distribution_text_tweet(input_csv, output_txt):
    """
    ツイート用テキストを生成（予想結果版）
    
    Args:
        input_csv (str): 入力CSVファイルパス
        output_txt (str): 出力テキストファイルパス
    """
    safe_print("[INFO] Tweet format generation started")
    safe_print(f"  入力: {input_csv}")
    safe_print(f"  出力: {output_txt}")
    
    try:
        df = pd.read_csv(input_csv, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(input_csv, encoding='utf-8')
    
    required_cols = ['race_bango', 'umaban', 'ensemble_score', 'final_rank']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        safe_print(f"[ERROR] 必須カラムが不足しています: {missing_cols}")
        return
    
    output_path = Path(output_txt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 競馬場名をDataFrameから取得
    keibajo_name = get_keibajo_name_from_df(df)
    
    # 日付を抽出
    filename = Path(input_csv).stem
    if '_ensemble_optimized' in filename:
        keibajo_date = filename.replace('_ensemble_optimized', '')
    else:
        keibajo_date = filename.replace('_ensemble', '')
    
    if keibajo_date.startswith('temp_'):
        keibajo_date = keibajo_date[5:]
    
    parts = keibajo_date.split('_')
    date_str = parts[1] if len(parts) > 1 else parts[0] if len(parts) > 0 else ""
    
    # 日付フォーマット変換（YYYYMMDD → M/D）
    if len(date_str) == 8:
        year = date_str[:4]
        month = date_str[4:6].lstrip('0')  # 先頭の0を削除
        day = date_str[6:8].lstrip('0')    # 先頭の0を削除
        formatted_date = f"{month}/{day}"
    else:
        formatted_date = date_str
    
    # テキスト生成
    lines = []
    
    # ヘッダー
    lines.append(f"【{formatted_date} {keibajo_name}競馬 AI予想結果】")
    
    # レースごとに処理
    race_count = 0
    for race_num in sorted(df['race_bango'].unique()):
        df_race = df[df['race_bango'] == race_num].copy()
        df_race = df_race.sort_values('final_rank')
        
        race_count += 1
        
        # 予想行を生成
        tweet_format = generate_tweet_format(df_race, race_num)
        if tweet_format:
            lines.append(tweet_format)
    
    # 空行
    lines.append("")
    
    # 的中率（プレースホルダー）
    lines.append("本日：0/0的中（的中率-%）")
    lines.append("今週累計：0/0的中（的中率-%）")
    
    # ファイルに書き込み
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    safe_print(f"[OK] Tweet format generation complete: {output_txt}")
    safe_print(f"  - Races: {race_count}R")
    safe_print(f"  - Lines: {len(lines)}")


def main():
    """メイン処理"""
    if len(sys.argv) != 3:
        safe_print("使用方法: python generate_distribution_tweet.py <入力CSV> <出力テキスト>")
        safe_print("例: python generate_distribution_tweet.py data\\predictions\\phase5\\川崎_20260409_ensemble.csv predictions\\川崎_20260409_tweet.txt")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_txt = sys.argv[2]
    
    if not Path(input_csv).exists():
        safe_print(f"[ERROR] 入力ファイルが見つかりません: {input_csv}")
        sys.exit(1)
    
    generate_distribution_text_tweet(input_csv, output_txt)


if __name__ == "__main__":
    main()
