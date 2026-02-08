# -*- coding: utf-8 -*-
"""
Note投稿用テキスト生成スクリプト（馬名補完対応版）
地方競馬AI予想システム - Phase 6 Note配信用フォーマット
全14競馬場対応
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
    """スコアに基づいてランクラベルを付与（絵文字付き）"""
    if score >= 0.80:
        return '⭐ S'
    elif score >= 0.70:
        return '🔥 A'
    elif score >= 0.60:
        return '💫 B'
    elif score >= 0.50:
        return '✨ C'
    else:
        return '📍 D'


def load_horse_names_from_raw(ensemble_csv_path):
    """
    raw CSV から馬名を取得してマッピングを作成
    
    Args:
        ensemble_csv_path: ensemble CSV のパス
    
    Returns:
        dict: {(kaisai_nen, kaisai_tsukihi, race_bango, umaban): bamei}
    """
    # ensemble CSV のパスから raw CSV のパスを推測
    ensemble_path = Path(ensemble_csv_path)
    
    # data/predictions/phase5/{競馬場名}_{YYYYMMDD}_ensemble.csv
    # → data/raw/{YYYY}/{MM}/{競馬場名}_{YYYYMMDD}_raw.csv
    
    filename = ensemble_path.stem  # "{競馬場名}_{YYYYMMDD}_ensemble"
    keibajo_date = filename.replace('_ensemble', '')  # "{競馬場名}_{YYYYMMDD}"
    
    # 日付部分を抽出
    parts = keibajo_date.split('_')
    if len(parts) < 2:
        return {}
    
    date_short = parts[1]  # "YYYYMMDD"
    year = date_short[:4]
    month = date_short[4:6]
    
    raw_csv_path = ensemble_path.parent.parent.parent / 'raw' / year / month / f"{keibajo_date}_raw.csv"
    
    safe_print(f"[INFO] 馬名を取得中: {raw_csv_path}")
    
    if not raw_csv_path.exists():
        safe_print(f"[WARN] raw CSV が見つかりません: {raw_csv_path}")
        return {}
    
    # raw CSV を読み込み
    try:
        df_raw = pd.read_csv(raw_csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        df_raw = pd.read_csv(raw_csv_path, encoding='shift-jis')
    
    # 馬名マッピングを作成
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
    """
    馬名を取得
    
    Args:
        row: DataFrame の行
        horse_names: 馬名マッピング辞書
    
    Returns:
        str: 馬名
    """
    # ensemble CSV から馬名を取得を試みる
    if 'bamei' in row and pd.notna(row['bamei']) and str(row['bamei']).strip():
        name = str(row['bamei']).strip()
        if name.endswith('号'):
            name = name[:-1]
        return name
    
    # raw CSV の馬名マッピングから取得
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


def generate_betting_recommendations_note(df_race):
    """
    購入推奨を生成（Note最適化版）
    
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
    
    # 馬単の構築
    umatan_parts = []
    if h2:
        umatan_parts.extend([f"{h1}→{h2}", f"{h2}→{h1}"])
    if h3:
        umatan_parts.extend([f"{h1}→{h3}", f"{h3}→{h1}"])
    umatan_text = "、".join(umatan_parts) if umatan_parts else f"{h1}→?"
    
    recommendations = [
        "",
        "### 💰 購入推奨",
        "",
        f"**🎯 本命軸**",
        f"- 単勝: **{h1}番**",
        f"- 複勝: **{h1}番**、{h2}番" if h2 else f"- 複勝: **{h1}番**",
        "",
        f"**🔄 相手候補**",
        f"- 馬単: {umatan_text}",
        f"- 三連複: {'-'.join(map(str, top5))} BOX",
        f"- 三連単: **{h1}** → {'-'.join(map(str, second_place))} → {'-'.join(map(str, third_place))}",
        ""
    ]
    
    return "\n".join(recommendations)


def generate_distribution_text_note(input_csv, output_txt):
    """
    Note投稿用テキストを生成（Note最適化版）
    
    Args:
        input_csv (str): 入力CSVファイルパス
        output_txt (str): 出力テキストファイルパス
    """
    safe_print("[INFO] Note投稿用テキスト生成開始")
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
    keibajo_date = filename.replace('_ensemble', '')
    parts = keibajo_date.split('_')
    keibajo_name = parts[0] if len(parts) > 0 else "競馬場"
    date_str = parts[1] if len(parts) > 1 else "日付不明"
    
    # 日付フォーマット変換（YYYYMMDD → YYYY年MM月DD日）
    if len(date_str) == 8:
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        formatted_date = f"{year}年{month}月{day}日"
    else:
        formatted_date = date_str
    
    # テキスト生成
    lines = []
    
    # ヘッダー（Note用: 大見出しH1相当）
    lines.append(f"# 🏇 {keibajo_name}競馬 AI予想")
    lines.append("")
    lines.append(f"**開催日**: {formatted_date}  ")
    lines.append(f"**対象レース**: {len(df['race_bango'].unique())}R  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📋 予想結果一覧")
    lines.append("")
    
    # レースごとに処理
    race_count = 0
    for race_num in sorted(df['race_bango'].unique()):
        df_race = df[df['race_bango'] == race_num].copy()
        df_race = df_race.sort_values('final_rank')
        
        race_count += 1
        
        # レースヘッダー（Note用: 中見出しH2相当）
        lines.append("")
        lines.append(f"## 🏇 第{race_num}R 予想")
        lines.append("")
        
        # 予想馬リスト（箇条書き形式）
        lines.append("### 📊 予想順位")
        lines.append("")
        
        for rank_idx, (_, row) in enumerate(df_race.iterrows(), 1):
            umaban = int(row['umaban'])
            bamei = get_horse_name(row, horse_names)
            score = row['ensemble_score']
            rank_label = row['rank_label']
            
            # トップ3は太字
            if rank_idx <= 3:
                lines.append(f"**{rank_idx}. {umaban}番 {bamei}** （スコア: {score:.2f} / {rank_label}）")
            else:
                lines.append(f"{rank_idx}. {umaban}番 {bamei} （スコア: {score:.2f} / {rank_label}）")
        
        # 購入推奨を追加
        recommendations = generate_betting_recommendations_note(df_race)
        if recommendations:
            lines.append(recommendations)
        
        # レース間の区切り
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # フッター
    lines.append("")
    lines.append("## ⚠️ 注意事項")
    lines.append("")
    lines.append("> 本予想はAIによる分析結果です。")
    lines.append("> 投資判断は自己責任でお願いします。")
    lines.append("> 過去の成績は将来の結果を保証するものではありません。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### 📌 ランク評価基準")
    lines.append("")
    lines.append("- ⭐ **S**: スコア0.80以上（最有力候補）")
    lines.append("- 🔥 **A**: スコア0.70-0.79（有力候補）")
    lines.append("- 💫 **B**: スコア0.60-0.69（注目候補）")
    lines.append("- ✨ **C**: スコア0.50-0.59（穴候補）")
    lines.append("- 📍 **D**: スコア0.50未満（警戒候補）")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*{keibajo_name}競馬 {formatted_date} 開催分*  ")
    lines.append(f"*地方競馬AI予想システム v3*")
    
    # ファイルに書き込み
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    safe_print(f"[OK] Note投稿用テキスト生成完了: {output_txt}")
    safe_print(f"  - レース数: {race_count}R")
    safe_print(f"  - 行数: {len(lines)}行")


def main():
    """メイン処理"""
    if len(sys.argv) != 3:
        safe_print("使用方法: python generate_distribution_note.py <入力CSV> <出力テキスト>")
        safe_print("例: python generate_distribution_note.py data\\predictions\\phase5\\佐賀_20260208_ensemble.csv predictions\\佐賀_20260208_note.txt")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_txt = sys.argv[2]
    
    # 入力ファイルの存在確認
    if not Path(input_csv).exists():
        safe_print(f"[ERROR] 入力ファイルが見つかりません: {input_csv}")
        sys.exit(1)
    
    # テキスト生成実行
    generate_distribution_text_note(input_csv, output_txt)


if __name__ == "__main__":
    main()
