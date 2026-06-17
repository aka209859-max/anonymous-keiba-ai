# -*- coding: utf-8 -*-
"""
X記事投稿用テキスト生成スクリプト
地方競馬AI予想システム - Phase 6 X Articles配信用フォーマット

フォーマット:
【H1】 YYYY.MM.DD 競馬場名｜的中特化AIが導き出した「全レース」指数上位馬公開
【H2】 競馬場名1R〜XR：的中特化型・指数上位馬ナビ
【リスト】 各レースの◎○▲
【H2】 的中は「ゴール」ではない。資産を増やすための「スタート」だ。
【リンク】 note記事へのリンク
"""

import sys
import pandas as pd
from pathlib import Path


def safe_print(msg):
    """安全な出力（Windows CP932対応）"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('cp932', errors='ignore').decode('cp932'))


def assign_rank_label(score):
    """スコアに基づいてランクラベルを付与"""
    if score >= 0.80:
        return 'S'
    elif score >= 0.70:
        return 'A'
    elif score >= 0.60:
        return 'B'
    elif score >= 0.50:
        return 'C'
    else:
        return 'D'


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
    if '_ensemble_optimized' in filename:
        keibajo_date = filename.replace('_ensemble_optimized', '')
    else:
        keibajo_date = filename.replace('_ensemble', '')
    
    if keibajo_date.startswith('temp_'):
        keibajo_date = keibajo_date[5:]
    
    parts = keibajo_date.split('_')
    if len(parts) < 2:
        date_short = parts[0] if parts else keibajo_date
    else:
        date_short = parts[1]
    
    year = date_short[:4]
    month = date_short[4:6]
    
    try:
        df_ensemble = pd.read_csv(ensemble_csv_path, encoding='shift-jis', nrows=1)
    except:
        try:
            df_ensemble = pd.read_csv(ensemble_csv_path, encoding='utf-8', nrows=1)
        except:
            return {}
    
    keibajo_code_map = {
        '30': '門別', '35': '盛岡', '36': '水沢',
        '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
        '46': '金沢', '47': '笠松', '48': '名古屋',
        '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
    }
    
    if 'keibajo_code' in df_ensemble.columns:
        keibajo_code = str(int(df_ensemble['keibajo_code'].iloc[0]))
        keibajo_name = keibajo_code_map.get(keibajo_code, '')
        if keibajo_name:
            keibajo_date = f"{keibajo_name}_{date_short}"
    
    raw_csv_path = ensemble_path.parent.parent.parent / 'raw' / year / month / f"{keibajo_date}_raw.csv"
    
    if not raw_csv_path.exists():
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
    
    return horse_names


def get_horse_name(row, horse_names):
    """
    馬名を取得
    
    Args:
        row: DataFrame の行
        horse_names: 馬名マッピング辞書
    
    Returns:
        str: 馬名
    """
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


def generate_distribution_text_x_article(input_csv, output_txt):
    """
    X記事用テキストを生成
    
    Args:
        input_csv (str): 入力CSVファイルパス
        output_txt (str): 出力テキストファイルパス
    """
    safe_print("[INFO] X記事用テキスト生成開始")
    safe_print(f"  入力: {input_csv}")
    safe_print(f"  出力: {output_txt}")
    
    # CSVファイルを読み込み
    try:
        df = pd.read_csv(input_csv, encoding='shift-jis')
    except UnicodeDecodeError:
        df = pd.read_csv(input_csv, encoding='utf-8')
    
    # 必須カラムの確認
    required_cols = ['race_bango', 'umaban', 'ensemble_score', 'final_rank']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        safe_print(f"[ERROR] 必須カラムが不足しています: {missing_cols}")
        return
    
    # raw CSV から馬名を取得
    horse_names = load_horse_names_from_raw(input_csv)
    
    # ランクラベルを付与
    df['rank_label'] = df['ensemble_score'].apply(assign_rank_label)
    
    # 出力先ディレクトリを作成
    output_path = Path(output_txt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 競馬場名と日付を抽出
    filename = Path(input_csv).stem
    keibajo_date = filename.replace('_ensemble_optimized', '').replace('_ensemble', '')
    
    if keibajo_date.startswith('temp_'):
        keibajo_date = keibajo_date[5:]
    
    # 競馬場コードマッピング
    keibajo_code_map = {
        '30': '門別', '35': '盛岡', '36': '水沢',
        '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
        '46': '金沢', '47': '笠松', '48': '名古屋',
        '50': '園田', '51': '姫路', '54': '高知', '55': '佐賀'
    }
    
    # ローマ字競馬場名マッピング
    keibajo_roman_to_ja = {
        'monbetsu': '門別', 'morioka': '盛岡', 'mizusawa': '水沢',
        'urawa': '浦和', 'funabashi': '船橋', 'ooi': '大井', 'kawasaki': '川崎',
        'kanazawa': '金沢', 'kasamatsu': '笠松', 'nagoya': '名古屋',
        'sonoda': '園田', 'himeji': '姫路', 'kochi': '高知', 'saga': '佐賀'
    }
    
    # CSVから競馬場コードを取得
    keibajo_name = "競馬場"
    if 'keibajo_code' in df.columns:
        keibajo_code = str(int(df['keibajo_code'].iloc[0]))
        keibajo_name = keibajo_code_map.get(keibajo_code, "競馬場")
    
    # ファイル名からも試行（フォールバック）
    parts = keibajo_date.split('_')
    if len(parts) >= 2:
        keibajo_name_raw = parts[0]
        # ローマ字なら日本語に変換
        keibajo_name_fallback = keibajo_roman_to_ja.get(keibajo_name_raw.lower(), keibajo_name_raw)
        if keibajo_name == "競馬場":
            keibajo_name = keibajo_name_fallback
        date_str = parts[1] if len(parts) > 1 else "日付不明"
    else:
        # temp_YYYYMMDD の場合
        date_str = parts[0] if len(parts) > 0 else "日付不明"
    
    # 日付フォーマット変換（YYYYMMDD → YYYY.MM.DD）
    if len(date_str) == 8:
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        formatted_date = f"{year}.{month}.{day}"
    else:
        formatted_date = date_str
    
    # テキスト生成
    lines = []
    
    # タイトル（#なし、Add a title枠に貼り付けるため）
    lines.append(f"{formatted_date} {keibajo_name}競馬｜的中特化AIが導き出した「全レース」指数上位馬公開")
    lines.append("")
    lines.append("[※ここにアイキャッチ画像を挿入]")
    lines.append("")
    
    # H2: 指数上位馬ナビ（目印として【H2】を使用）
    race_numbers = sorted(df['race_bango'].unique())
    first_race = race_numbers[0] if race_numbers else 1
    last_race = race_numbers[-1] if race_numbers else 1
    
    lines.append(f"【H2】{keibajo_name}{first_race}R〜{last_race}R：的中特化型・指数上位馬ナビ")
    lines.append("")
    lines.append("的中精度に極振りしたAIが、本日の全レースで「的中確率」が高いと判断した上位3頭です。")
    lines.append("")
    
    # レースごとに処理（1行に繋げる）
    for race_num in race_numbers:
        df_race = df[df['race_bango'] == race_num].copy()
        df_race = df_race.sort_values('final_rank')
        
        # 上位3頭を取得
        top3 = df_race.head(3)
        
        # ランクラベル（Sランクの場合は🔥を付ける）
        rank_label = top3.iloc[0]['rank_label'] if len(top3) > 0 else 'D'
        rank_emoji = " 🔥" if rank_label == 'S' else ""
        rank_text = f"（{rank_label}ランク）{rank_emoji}" if rank_label in ['S', 'A'] else ""
        
        # 馬番と馬名を取得
        horse_list = []
        symbols = ['◎', '○', '▲']
        for idx, (_, row) in enumerate(top3.iterrows()):
            if idx >= 3:
                break
            umaban = int(row['umaban'])
            bamei = get_horse_name(row, horse_names)
            symbol = symbols[idx]
            horse_list.append(f"{symbol} {umaban}番 {bamei}")
        
        # レース行を4行に分割
        lines.append(f"第{race_num}R {rank_text}")
        for horse in horse_list:
            lines.append(horse)
        lines.append("")
    
    # セパレーター
    lines.append("---")
    lines.append("")
    
    # H2: 的中は「ゴール」ではない（目印として【H2】を使用）
    lines.append("【H2】的中は「ゴール」ではない。資産を増やすための「スタート」だ。")
    lines.append("")
    lines.append("本日公開した「上位馬」をどう組み合わせ、どの券種で、どのような資金配分で勝負するか。")
    lines.append("")
    lines.append("的中を単なるラッキーで終わらせず、継続的な「資産」に変えるための具体的な買い目と詳細スコアについては、こちらのnoteで全レース分を公開しています。")
    lines.append("")
    lines.append("👉 [ここにnote記事のリンクを配置]")
    lines.append("")
    
    # ファイルに書き込み
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    safe_print(f"[OK] X記事用テキスト生成完了: {output_txt}")
    safe_print(f"  - レース数: {len(race_numbers)}R")
    safe_print(f"  - 行数: {len(lines)}行")


def main():
    """メイン処理"""
    if len(sys.argv) != 3:
        safe_print("使用方法: python generate_distribution_x_article.py <入力CSV> <出力テキスト>")
        safe_print("例: python generate_distribution_x_article.py data\\predictions\\phase5\\金沢_20260315_ensemble.csv predictions\\金沢_20260315_x_article.txt")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_txt = sys.argv[2]
    
    # 入力ファイルの存在確認
    if not Path(input_csv).exists():
        safe_print(f"[ERROR] 入力ファイルが見つかりません: {input_csv}")
        sys.exit(1)
    
    # テキスト生成実行
    generate_distribution_text_x_article(input_csv, output_txt)


if __name__ == "__main__":
    main()
