# -*- coding: utf-8 -*-
"""
ブッカーズ投稿用テキスト生成スクリプト（馬名補完対応版）
地方競馬AI予想システム - Phase 6 ブッカーズ配信用フォーマット
全14競馬場対応
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


def get_keibajo_name_from_df(df):
    """
    DataFrameの keibajo_code から競馬場日本語名を取得
    
    Args:
        df: ensemble結果のDataFrame
    
    Returns:
        str: 競馬場の日本語名（例: '高知'）
    """
    if 'keibajo_code' in df.columns:
        keibajo_code = str(df['keibajo_code'].iloc[0])
        return KEIBAJO_CODE_TO_NAME.get(keibajo_code, '競馬場')
    return '競馬場'


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


def assign_mark(rank_idx):
    """順位に基づいて印を付与"""
    if rank_idx == 1:
        return '◎'
    elif rank_idx == 2:
        return '○'
    elif rank_idx == 3:
        return '▲'
    elif rank_idx in [4, 5]:
        return '△'
    else:
        return '  '


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
    # 新モデル（ensemble_optimized）と旧モデル（ensemble）の両方に対応
    if '_ensemble_optimized' in filename:
        keibajo_date = filename.replace('_ensemble_optimized', '')
    else:
        keibajo_date = filename.replace('_ensemble', '')
    
    # temp_ プレフィックスを除去
    if keibajo_date.startswith('temp_'):
        keibajo_date = keibajo_date[5:]  # "temp_" を削除
    
    parts = keibajo_date.split('_')
    if len(parts) < 2:
        # temp_YYYYMMDD のような形式の場合、ensemble CSV から競馬場コードを取得
        date_short = parts[0] if parts else keibajo_date
    else:
        date_short = parts[1]
    
    year = date_short[:4]
    month = date_short[4:6]
    
    # ensemble CSV から競馬場名を取得する試み
    try:
        df_ensemble = pd.read_csv(ensemble_csv_path, encoding='shift-jis', nrows=1)
    except:
        try:
            df_ensemble = pd.read_csv(ensemble_csv_path, encoding='utf-8', nrows=1)
        except:
            safe_print(f"[ERROR] ensemble CSV を読み込めません: {ensemble_csv_path}")
            return {}
    
    # keibajo_code から競馬場名を取得
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
    
    safe_print(f"[INFO] 馬名を取得中: {raw_csv_path}")
    
    if not raw_csv_path.exists():
        safe_print(f"[WARN] raw CSV が見つかりません: {raw_csv_path}")
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
        
        safe_print(f"[OK] 馬名マッピング作成完了: {len(horse_names)}件")
    else:
        safe_print(f"[WARN] raw CSV に必要なカラムがありません")
    
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


def generate_betting_recommendations_bookers(df_race):
    """
    購入推奨を生成（ブッカーズ最適化版）
    
    Args:
        df_race: レースデータ（DataFrameの1レース分）
    
    Returns:
        str: 購入推奨テキスト
    """
    top_horses = df_race.nsmallest(7, 'final_rank')['umaban'].tolist()
    
    if len(top_horses) < 3:
        return ""
    
    h1 = top_horses[0]
    h2 = top_horses[1] if len(top_horses) > 1 else None
    h3 = top_horses[2] if len(top_horses) > 2 else None
    
    top4 = top_horses[:4] if len(top_horses) >= 4 else top_horses
    top5 = top_horses[:5] if len(top_horses) >= 5 else top_horses
    top7 = top_horses if len(top_horses) >= 7 else top_horses
    
    # 2着候補: 2,3,4位
    second_place = top4[1:] if len(top4) > 1 else []
    
    # 3着候補: 2,3,4,5,6,7位
    third_place = top7[1:] if len(top7) > 1 else []
    
    # 三連複の新フォーマット: 1・2位 - 2・3・4位 - 2・3・4・5・6・7位
    first_positions = [h1, h2] if h2 else [h1]
    sanrenpuku_text = f"{'.'.join(map(str, first_positions))} - {'.'.join(map(str, second_place))} - {'.'.join(map(str, third_place))}"
    
    recommendations = [
        "",
        "💰 購入推奨（買い目）",
        "",
        "【単勝/複勝】",
        f"・単勝：{h1}",
        f"・複勝：{h1}, {h2}" if h2 else f"・複勝：{h1}",
        "",
        "【馬単/馬連】",
    ]
    
    # 馬単の構築
    if h2 and h3:
        recommendations.append(f"・{h1} ↔ {h2}, {h3} (各2点)")
    elif h2:
        recommendations.append(f"・{h1} ↔ {h2}")
    
    recommendations.extend([
        "",
        "【三連複】",
        f"・三連複：{sanrenpuku_text}",
        ""
    ])
    
    return "\n".join(recommendations)


def generate_distribution_text_bookers(input_csv, output_txt):
    """
    ブッカーズ投稿用テキストを生成
    
    Args:
        input_csv (str): 入力CSVファイルパス
        output_txt (str): 出力テキストファイルパス
    """
    safe_print("[INFO] ブッカーズ投稿用テキスト生成開始")
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
    
    horse_names = load_horse_names_from_raw(input_csv)
    df['rank_label'] = df['ensemble_score'].apply(assign_rank_label)
    
    output_path = Path(output_txt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 競馬場名をDataFrameから取得（CSVデータの keibajo_code を使用）
    keibajo_name = get_keibajo_name_from_df(df)
    
    # 日付を抽出
    filename = Path(input_csv).stem
    # 新モデル（ensemble_optimized）と旧モデル（ensemble）の両方に対応
    if '_ensemble_optimized' in filename:
        keibajo_date = filename.replace('_ensemble_optimized', '')
    else:
        keibajo_date = filename.replace('_ensemble', '')
    
    # temp_ プレフィックスを削除
    if keibajo_date.startswith('temp_'):
        keibajo_date = keibajo_date[5:]
    
    parts = keibajo_date.split('_')
    date_str = parts[1] if len(parts) > 1 else parts[0] if len(parts) > 0 else ""
    
    # 日付フォーマット変換
    if len(date_str) == 8:
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        formatted_date = f"{year}年{month}月{day}日"
        weekday = datetime.strptime(date_str, '%Y%m%d').strftime('(%a)')
    else:
        formatted_date = date_str
        weekday = ""
    
    # テキスト生成
    lines = []
    
    # タイトル
    lines.append(f"🏇 【地方競馬AI】{keibajo_name}競馬 全{len(df['race_bango'].unique())}R予想")
    lines.append("")
    lines.append(f"📅 {formatted_date}{weekday}")
    lines.append("")
    lines.append("本日はAI予想システムによる分析結果をお届けします。")
    lines.append("過去の膨大なレースデータから、今日の馬場状態と出走馬の相性を完全数値化しました。")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # レースごとに処理
    race_count = 0
    for race_num in sorted(df['race_bango'].unique()):
        df_race = df[df['race_bango'] == race_num].copy()
        df_race = df_race.sort_values('final_rank')
        
        race_count += 1
        
        # レースヘッダー
        lines.append("")
        lines.append(f"🏁 第{race_num}R 予想結果")
        lines.append("")
        
        # AI推奨馬セクション
        lines.append("🎯 AI推奨馬")
        lines.append("")
        
        for rank_idx, (_, row) in enumerate(df_race.iterrows(), 1):
            if rank_idx > 5:  # トップ5のみ表示
                break
            
            umaban = int(row['umaban'])
            bamei = get_horse_name(row, horse_names)
            score = row['ensemble_score']
            rank_label = row['rank_label']
            mark = assign_mark(rank_idx)
            
            # 1-3位は詳細表示
            if rank_idx <= 3:
                lines.append(f"{mark} {umaban} {bamei} (ランク{rank_label})")
                lines.append(f"AIスコア: {score:.2f}")
                lines.append("")
            else:
                lines.append(f"{mark} {umaban} {bamei}")
        
        # 購入推奨を追加
        recommendations = generate_betting_recommendations_bookers(df_race)
        if recommendations:
            lines.append(recommendations)
        
        # レース間の区切り
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # フッター
    lines.append("")
    lines.append("⚠️ ご利用上の注意")
    lines.append("")
    lines.append("本予想はAIによる統計分析に基づくデータです。")
    lines.append("レース結果を保証するものではありません。")
    lines.append("馬券購入は自己判断・自己責任でお願いいたします。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("📌 ランク評価基準")
    lines.append("")
    lines.append("S：スコア0.80以上（最有力）")
    lines.append("A：スコア0.70-0.79（有力）")
    lines.append("B：スコア0.60-0.69（注目）")
    lines.append("C：スコア0.50-0.59（穴）")
    lines.append("D：スコア0.50未満（警戒）")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"#{keibajo_name}競馬 #AI予想 #地方競馬予想 #{formatted_date.replace('年', '').replace('月', '').replace('日', '')}")
    
    # ファイルに書き込み
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    safe_print(f"[OK] ブッカーズ投稿用テキスト生成完了: {output_txt}")
    safe_print(f"  - レース数: {race_count}R")
    safe_print(f"  - 行数: {len(lines)}行")


def main():
    """メイン処理"""
    if len(sys.argv) != 3:
        safe_print("使用方法: python generate_distribution_bookers.py <入力CSV> <出力テキスト>")
        safe_print("例: python generate_distribution_bookers.py data\\predictions\\phase5\\佐賀_20260208_ensemble.csv predictions\\佐賀_20260208_bookers.txt")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_txt = sys.argv[2]
    
    if not Path(input_csv).exists():
        safe_print(f"[ERROR] 入力ファイルが見つかりません: {input_csv}")
        sys.exit(1)
    
    generate_distribution_text_bookers(input_csv, output_txt)


if __name__ == "__main__":
    main()
