# -*- coding: utf-8 -*-
"""
ツイート用コピペフォーマット生成スクリプト
地方競馬AI予想システム - Phase 6 Twitter投稿用
全14競馬場対応
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime


def safe_print(msg):
    """安全な出力（Windows CP932対応）"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('cp932', errors='ignore').decode('cp932'))


def load_horse_names_from_raw(ensemble_csv_path):
    """
    raw CSV から馬名を取得してマッピングを作成
    
    Args:
        ensemble_csv_path: ensemble CSV のパス
    
    Returns:
        dict: {(kaisai_nen, kaisai_tsukihi, race_bango, umaban): bamei}
    """
    ensemble_path = Path(ensemble_csv_path)
    filename = ensemble_path.stem
    keibajo_date = filename.replace('_ensemble', '')
    
    parts = keibajo_date.split('_')
    if len(parts) < 2:
        return {}
    
    date_short = parts[1]
    year = date_short[:4]
    month = date_short[4:6]
    
    raw_csv_path = ensemble_path.parent.parent.parent / 'raw' / year / month / f"{keibajo_date}_raw.csv"
    
    safe_print(f"[INFO] Loading horse names from: {raw_csv_path}")
    
    if not raw_csv_path.exists():
        safe_print(f"[WARN] raw CSV not found: {raw_csv_path}")
        return {}
    
    try:
        df_raw = pd.read_csv(raw_csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df_raw = pd.read_csv(raw_csv_path, encoding='shift-jis')
    
    horse_names = {}
    
    required_cols = ['kaisai_nen', 'kaisai_tsukihi', 'race_bango', 'umaban', 'bamei']
    if all(col in df_raw.columns for col in required_cols):
        for _, row in df_raw.iterrows():
            key = (
                str(row['kaisai_nen']),
                str(row['kaisai_tsukihi']),
                str(row['race_bango']),
                int(row['umaban'])
            )
            horse_names[key] = str(row['bamei']).strip()
        
        safe_print(f"[OK] Horse name mapping created: {len(horse_names)} entries")
    else:
        safe_print(f"[WARN] Required columns not found in raw CSV")
    
    return horse_names


def get_horse_name(row, horse_names):
    """馬名を取得"""
    if 'bamei' in row and pd.notna(row['bamei']) and str(row['bamei']).strip():
        name = str(row['bamei']).strip()
        if name.endswith('号'):
            name = name[:-1]
        return name
    
    key = (
        str(row['kaisai_nen']),
        str(row['kaisai_tsukihi']),
        str(row['race_bango']),
        int(row['umaban'])
    )
    
    if key in horse_names:
        name = horse_names[key]
        if name.endswith('号'):
            name = name[:-1]
        return name
    
    return "未登録"


def generate_tweet_format(df_race):
    """
    ツイート用コピペフォーマットを生成
    
    Args:
        df_race: レースデータ（DataFrameの1レース分）
    
    Returns:
        str: ツイート用テキスト
    """
    top_horses = df_race.nsmallest(7, 'final_rank')['umaban'].tolist()
    
    if len(top_horses) < 3:
        return ""
    
    h1 = top_horses[0]
    h2 = top_horses[1] if len(top_horses) > 1 else None
    h3 = top_horses[2] if len(top_horses) > 2 else None
    h4 = top_horses[3] if len(top_horses) > 3 else None
    h5 = top_horses[4] if len(top_horses) > 4 else None
    h6 = top_horses[5] if len(top_horses) > 5 else None
    
    top5 = top_horses[:5] if len(top_horses) >= 5 else top_horses
    top7 = top_horses if len(top_horses) >= 7 else top_horses
    
    # 2着候補: 2,3,4位
    second_place = [h2, h3, h4] if h2 and h3 and h4 else []
    second_place = [h for h in second_place if h is not None]
    
    # 3着候補: 2,3,4,5,6,7位（上位7頭から1位を除外）
    third_place = top7[1:] if len(top7) > 1 else []
    
    # 馬単フォーマット
    umatan_parts = []
    if h2:
        umatan_parts.extend([f"{h1}→{h2}", f"{h2}→{h1}"])
    if h3:
        umatan_parts.extend([f"{h1}→{h3}", f"{h3}→{h1}"])
    
    umatan_str = "、".join(umatan_parts) if umatan_parts else f"{h1}軸"
    
    # 三連複BOX
    sanrenpuku_str = f"{'.'.join(map(str, top5))} BOX" if len(top5) >= 3 else ""
    
    # 三連単フォーマット
    if second_place and third_place:
        second_str = '.'.join(map(str, second_place))
        third_str = '.'.join(map(str, third_place))
        sanrentan_str = f"{h1}→{second_str}→{third_str}"
    else:
        sanrentan_str = f"{h1}軸"
    
    tweet = [
        "📊 購入推奨",
        f"・単勝: {h1}番",
        f"・複勝: {h1}番、{h2}番" if h2 else f"・複勝: {h1}番",
        f"・馬単: {umatan_str}",
        f"・三連複: {sanrenpuku_str}" if sanrenpuku_str else "",
        f"・三連単: {sanrentan_str}"
    ]
    
    return "\n".join([line for line in tweet if line])


def generate_distribution_text_tweet(input_csv, output_txt):
    """
    ツイート用テキストを生成
    
    Args:
        input_csv (str): 入力CSVファイルパス
        output_txt (str): 出力テキストファイルパス
    """
    safe_print("[INFO] Tweet format generation started")
    safe_print(f"  Input: {input_csv}")
    safe_print(f"  Output: {output_txt}")
    
    try:
        df = pd.read_csv(input_csv, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(input_csv, encoding='utf-8')
    
    required_cols = ['race_bango', 'umaban', 'ensemble_score', 'final_rank']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        safe_print(f"[ERROR] Missing required columns: {missing_cols}")
        return
    
    horse_names = load_horse_names_from_raw(input_csv)
    
    output_path = Path(output_txt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 競馬場名と日付を抽出
    filename = Path(input_csv).stem
    keibajo_date = filename.replace('_ensemble', '')
    parts = keibajo_date.split('_')
    
    # 競馬場名を日本語に変換（既に日本語の場合はそのまま）
    keibajo_code_to_jp = {
        'Saga': '佐賀',
        'Ooi': '大井',
        'Kawasaki': '川崎',
        'Funabashi': '船橋',
        'Urawa': '浦和',
        'Monbetsu': '門別',
        'Morioka': '盛岡',
        'Mizusawa': '水沢',
        'Kanazawa': '金沢',
        'Kasamatsu': '笠松',
        'Nagoya': '名古屋',
        'Sonoda': '園田',
        'Himeji': '姫路',
        'Kochi': '高知',
        # 日本語のままの場合
        '佐賀': '佐賀',
        '大井': '大井',
        '川崎': '川崎',
        '船橋': '船橋',
        '浦和': '浦和',
        '門別': '門別',
        '盛岡': '盛岡',
        '水沢': '水沢',
        '金沢': '金沢',
        '笠松': '笠松',
        '名古屋': '名古屋',
        '園田': '園田',
        '姫路': '姫路',
        '高知': '高知'
    }
    
    keibajo_name_raw = parts[0] if len(parts) > 0 else "競馬場"
    keibajo_name = keibajo_code_to_jp.get(keibajo_name_raw, keibajo_name_raw)
    date_str = parts[1] if len(parts) > 1 else ""
    
    # 日付フォーマット変換
    if len(date_str) == 8:
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        weekday_jp = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]
        formatted_date = f"{month}/{day}（{weekday_jp}）"
    else:
        formatted_date = date_str
    
    # テキスト生成
    lines = []
    
    # レースごとに処理
    race_count = 0
    for race_num in sorted(df['race_bango'].unique()):
        df_race = df[df['race_bango'] == race_num].copy()
        df_race = df_race.sort_values('final_rank')
        
        race_count += 1
        
        # レースヘッダー
        if race_count > 1:
            lines.append("")
            lines.append("=" * 50)
            lines.append("")
        
        lines.append(f"{formatted_date}{keibajo_name}{race_num}R")
        
        # ツイート用フォーマット生成
        tweet_format = generate_tweet_format(df_race)
        if tweet_format:
            lines.append(tweet_format)
    
    # ファイルに書き込み
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    safe_print(f"[OK] Tweet format generation complete: {output_txt}")
    safe_print(f"  - Races: {race_count}R")
    safe_print(f"  - Lines: {len(lines)}")


def main():
    """メイン処理"""
    if len(sys.argv) != 3:
        safe_print("Usage: python generate_distribution_tweet.py <input_csv> <output_txt>")
        safe_print("Example: python generate_distribution_tweet.py data\\predictions\\phase5\\Saga_20260208_ensemble.csv predictions\\Saga_20260208_tweet.txt")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_txt = sys.argv[2]
    
    if not Path(input_csv).exists():
        safe_print(f"[ERROR] Input file not found: {input_csv}")
        sys.exit(1)
    
    generate_distribution_text_tweet(input_csv, output_txt)


if __name__ == "__main__":
    main()
