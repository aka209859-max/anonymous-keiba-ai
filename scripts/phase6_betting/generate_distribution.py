# -*- coding: utf-8 -*-
"""
配信用テキスト生成スクリプト（馬名補完対応版）
佐賀競馬AI予想システム - Phase 5 後処理
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
    # ensemble CSV のパスから raw CSV のパスを推測
    ensemble_path = Path(ensemble_csv_path)
    
    # data/predictions/phase5/佐賀_20260207_ensemble.csv
    # → data/raw/2026/02/佐賀_20260207_raw.csv
    
    filename = ensemble_path.stem  # "佐賀_20260207_ensemble"
    keibajo_date = filename.replace('_ensemble', '')  # "佐賀_20260207"
    
    # 日付部分を抽出
    parts = keibajo_date.split('_')
    if len(parts) < 2:
        return {}
    
    date_short = parts[1]  # "20260207"
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


def generate_betting_recommendations(df_race):
    """
    購入推奨を生成
    
    Args:
        df_race: レースデータ（DataFrameの1レース分）
    
    Returns:
        str: 購入推奨テキスト
    """
    top_horses = df_race.nsmallest(7, 'final_rank')['umaban'].tolist()
    
    if len(top_horses) < 3:
        return ""
    
    h1, h2, h3 = top_horses[0], top_horses[1], top_horses[2]
    top5 = top_horses[:5] if len(top_horses) >= 5 else top_horses
    
    recommendations = [
        "",
        "📊 購入推奨",
        f"・単勝: {h1}番",
        f"・複勝: {h1}番、{h2}番",
        f"・馬単: {h1}→{h2}、{h1}→{h3}、{h2}→{h1}、{h3}→{h1}",
        f"・三連複: {'.'.join(map(str, top5))} BOX",
        f"・三連単: {h1}→{'.'.join(map(str, [h2, h3]))}→{'.'.join(map(str, top5))}",
        ""
    ]
    
    return "\n".join(recommendations)


def generate_distribution_text(input_csv, output_txt):
    """
    配信用テキストを生成（馬名補完対応版）
    
    Args:
        input_csv (str): 入力CSVファイルパス
        output_txt (str): 出力テキストファイルパス
    """
    safe_print("[INFO] 配信用テキスト生成開始")
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
    
    # テキスト生成
    lines = []
    lines.append("=" * 60)
    lines.append("      地方競馬AI予想システム - 予想結果")
    lines.append("=" * 60)
    lines.append("")
    
    # レースごとに処理
    race_count = 0
    for race_num in sorted(df['race_bango'].unique()):
        df_race = df[df['race_bango'] == race_num].copy()
        df_race = df_race.sort_values('final_rank')
        
        race_count += 1
        
        # レースヘッダー
        lines.append("")
        lines.append(f"🏇 第{race_num}R 予想結果")
        lines.append("")
        
        # テーブルヘッダー
        lines.append("馬番 | 馬名              | スコア | ランク")
        lines.append("-----|-------------------|--------|-------")
        
        # 各馬の情報を出力
        for _, row in df_race.iterrows():
            umaban = int(row['umaban'])
            bamei = get_horse_name(row, horse_names)[:15].ljust(15)
            score = row['ensemble_score']
            rank = row['rank_label']
            
            line = f" {umaban:2d}  | {bamei} | {score:.2f}   | {rank}"
            lines.append(line)
        
        # 購入推奨を追加
        recommendations = generate_betting_recommendations(df_race)
        if recommendations:
            lines.append(recommendations)
        
        lines.append("-" * 60)
    
    # フッター
    lines.append("")
    lines.append("=" * 60)
    lines.append(f"対象レース数: {race_count}R")
    lines.append("")
    lines.append("【注意事項】")
    lines.append("・本予想はAIによる分析結果です")
    lines.append("・投資判断は自己責任でお願いします")
    lines.append("・過去の成績は将来の結果を保証するものではありません")
    lines.append("=" * 60)
    
    # ファイルに書き込み
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    safe_print(f"[OK] 配信用テキスト生成完了: {output_txt}")
    safe_print(f"  - レース数: {race_count}R")
    safe_print(f"  - 行数: {len(lines)}行")


def main():
    """メイン処理"""
    if len(sys.argv) != 3:
        safe_print("使用方法: python generate_distribution.py <入力CSV> <出力テキスト>")
        safe_print("例: python generate_distribution.py data\\predictions\\phase5\\佐賀_20260207_ensemble.csv predictions\\佐賀_20260207_配信用.txt")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_txt = sys.argv[2]
    
    # 入力ファイルの存在確認
    if not Path(input_csv).exists():
        safe_print(f"[ERROR] 入力ファイルが見つかりません: {input_csv}")
        sys.exit(1)
    
    # テキスト生成実行
    generate_distribution_text(input_csv, output_txt)


if __name__ == "__main__":
    main()