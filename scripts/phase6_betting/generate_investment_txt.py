#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6: 投資判断アドバイスTXT生成スクリプト
投資競馬最適化版 - 改良案B（Binary強化型）対応

目的:
    投資判断アドバイスCSVから、読みやすいTXT形式で出力

入力:
    investment_advice_csv: 投資判断アドバイスCSV
    ensemble_csv: Phase 5アンサンブル結果CSV（馬名取得用）

出力:
    投資判断アドバイスTXT
"""

import sys
import os
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


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
        dict: {(kaisai_yen, kaisai_tsukihi, race_bango, umaban): bamei}
    """
    # ensemble CSV のパスから raw CSV のパスを推測
    ensemble_path = Path(ensemble_csv_path)
    
    # data/predictions/phase5/浦和_20260423_ensemble.csv
    # → data/raw/2026/04/浦和_20260423_raw.csv
    
    filename = ensemble_path.stem  # "浦和_20260423_ensemble"
    keibajo_date = filename.replace('_ensemble', '')  # "浦和_20260423"
    
    # 日付部分を抽出
    parts = keibajo_date.split('_')
    if len(parts) < 2:
        return {}
    
    date_short = parts[1]  # "20260423"
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


def get_horse_name(kaisai_nen, kaisai_tsukihi, race_bango, umaban, horse_names):
    """
    馬名を取得
    
    Args:
        kaisai_nen: 開催年
        kaisai_tsukihi: 開催月日
        race_bango: レース番号
        umaban: 馬番
        horse_names: 馬名マッピング辞書
    
    Returns:
        str: 馬名
    """
    key = (str(kaisai_nen), str(kaisai_tsukihi), str(race_bango), int(umaban))
    
    if key in horse_names:
        name = horse_names[key]
        if name.endswith('号'):
            name = name[:-1]
        return name
    
    return "未登録"


def get_keibajo_name(keibajo_code):
    """
    競馬場コードから競馬場名を取得
    
    Args:
        keibajo_code: 競馬場コード
    
    Returns:
        str: 競馬場名
    """
    keibajo_map = {
        30: '門別', 35: '盛岡', 36: '水沢', 42: '浦和',
        43: '船橋', 44: '大井', 45: '川崎', 46: '金沢',
        47: '笠松', 48: '名古屋', 50: '園田', 51: '姫路',
        54: '高知', 55: '佐賀'
    }
    return keibajo_map.get(int(keibajo_code), '不明')


def format_date(kaisai_nen, kaisai_tsukihi):
    """
    日付フォーマット
    
    Args:
        kaisai_nen: 開催年（例: 2026）
        kaisai_tsukihi: 開催月日（例: 423）
    
    Returns:
        str: フォーマット済み日付（例: 2026年04月23日）
    """
    kaisai_tsukihi_str = str(kaisai_tsukihi).zfill(4)
    month = kaisai_tsukihi_str[:2]
    day = kaisai_tsukihi_str[2:4]
    return f"{kaisai_nen}年{month}月{day}日"


def generate_investment_txt(investment_advice_csv, ensemble_csv, output_txt):
    """
    投資判断アドバイスTXT生成
    
    Args:
        investment_advice_csv: 投資判断アドバイスCSV
        ensemble_csv: Phase 5アンサンブル結果CSV
        output_txt: 出力テキストファイルパス
    """
    safe_print("[INFO] 投資判断アドバイスTXT生成開始")
    safe_print(f"  入力: {investment_advice_csv}")
    safe_print(f"  出力: {output_txt}")
    
    # CSV読み込み
    try:
        df_advice = pd.read_csv(investment_advice_csv, encoding='shift-jis')
    except:
        df_advice = pd.read_csv(investment_advice_csv, encoding='utf-8')
    
    # 馬名マッピング取得
    horse_names = load_horse_names_from_raw(ensemble_csv)
    
    # 出力先ディレクトリを作成
    output_path = Path(output_txt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # テキスト生成
    lines = []
    lines.append("=" * 80)
    lines.append("        地方競馬AI予想システム - 投資判断アドバイス")
    lines.append("=" * 80)
    lines.append("")
    lines.append("【アンサンブル比率】改良案B: Binary強化型（投資競馬最適化版）")
    lines.append("  - Binary（3着以内確率）: 40%")
    lines.append("  - Ranking（順位予測）  : 40%")
    lines.append("  - Regression（タイム予測）: 20%")
    lines.append("")
    lines.append("【推奨馬券種】複勝・馬連・ワイド・三連複")
    lines.append("")
    lines.append("=" * 80)
    lines.append("")
    
    # レースごとに処理
    race_count = 0
    total_investment = 0
    
    for race_id in sorted(df_advice['race_id'].unique()):
        df_race_advice = df_advice[df_advice['race_id'] == race_id].copy()
        
        if len(df_race_advice) == 0:
            continue
        
        race_count += 1
        
        # レース情報
        first_row = df_race_advice.iloc[0]
        keibajo_name = get_keibajo_name(first_row['keibajo_code'])
        date_str = format_date(first_row['kaisai_nen'], first_row['kaisai_tsukihi'])
        race_num = int(first_row['race_bango'])
        
        # レースヘッダー
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"投資判断アドバイス - {keibajo_name} {date_str} 第{race_num}レース")
        lines.append("=" * 80)
        lines.append("")
        
        race_investment = 0
        
        # 馬券種別ごとに出力
        for _, row in df_race_advice.iterrows():
            betting_type = row['betting_type']
            
            lines.append(f"■ {betting_type}")
            
            if betting_type == '複勝':
                umaban = int(row['umaban'])
                bamei = get_horse_name(
                    row['kaisai_nen'], row['kaisai_tsukihi'], 
                    row['race_bango'], umaban, horse_names
                )
                lines.append(f"  - 馬番: {umaban}番 ({bamei})")
                lines.append(f"  - アンサンブルスコア: {row['ensemble_score']:.3f}")
                lines.append(f"  - 的中予想確率: {row['binary_probability']:.1%}")
                lines.append(f"  - 損益分岐オッズ: {row['breakeven_odds']:.2f}倍")
                lines.append(f"  - 推奨購入額: {row['bet_amount']:,}円（資金の{row['bet_pct']:.1f}%）")
            
            elif betting_type in ['馬連', 'ワイド']:
                lines.append(f"  - 買い目: {row['horses']}")
                lines.append(f"  - 的中予想確率: {row['win_probability']:.1%}")
                lines.append(f"  - 損益分岐オッズ: {row['breakeven_odds']:.2f}倍")
                lines.append(f"  - 推奨購入額: {row['bet_amount']:,}円（資金の{row['bet_pct']:.1f}%）")
            
            elif betting_type == '三連複':
                combo_index = int(row.get('combo_index', 1))
                total_combos = int(row.get('total_combos', 1))
                lines.append(f"  - 買い目: {row['horses']} ({combo_index}/{total_combos}点)")
                lines.append(f"  - 的中予想確率: {row['win_probability']:.1%}")
                lines.append(f"  - 損益分岐オッズ: {row['breakeven_odds']:.2f}倍")
                lines.append(f"  - 推奨購入額: {row['bet_amount']:,}円（資金の{row['bet_pct']:.1f}%/点）")
            
            lines.append("")
            race_investment += row['bet_amount']
        
        # レースサマリー
        lines.append("【当レース投資サマリー】")
        lines.append(f"  - 合計投資額: {race_investment:,}円")
        lines.append(f"  - 購入点数: {len(df_race_advice)}点")
        lines.append("")
        
        total_investment += race_investment
    
    # フッター
    lines.append("")
    lines.append("=" * 80)
    lines.append("【全体サマリー】")
    lines.append(f"  - 対象レース数: {race_count}R")
    lines.append(f"  - 総投資額: {total_investment:,}円")
    lines.append(f"  - 総購入点数: {len(df_advice)}点")
    lines.append("")
    lines.append("【注意事項】")
    lines.append("  ・本アドバイスはAIによる分析結果です")
    lines.append("  ・オッズは損益分岐オッズを参考に、実際のオッズで判断してください")
    lines.append("  ・投資判断は自己責任でお願いします")
    lines.append("  ・過去の成績は将来の結果を保証するものではありません")
    lines.append("=" * 80)
    
    # ファイルに書き込み
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    safe_print(f"[OK] 投資判断アドバイスTXT生成完了: {output_txt}")
    safe_print(f"  - レース数: {race_count}R")
    safe_print(f"  - 行数: {len(lines)}行")


def main():
    """メイン処理"""
    if len(sys.argv) < 4:
        safe_print("使用法: python generate_investment_txt.py <investment_advice_csv> <ensemble_csv> <output_txt>")
        safe_print("")
        safe_print("例:")
        safe_print("  python generate_investment_txt.py \\")
        safe_print("         data/predictions/phase5/浦和_20260423_investment_advice.csv \\")
        safe_print("         data/predictions/phase5/浦和_20260423_ensemble.csv \\")
        safe_print("         predictions/浦和_20260423_投資判断.txt")
        sys.exit(1)
    
    investment_advice_csv = sys.argv[1]
    ensemble_csv = sys.argv[2]
    output_txt = sys.argv[3]
    
    # 入力ファイルの存在確認
    if not Path(investment_advice_csv).exists():
        safe_print(f"[ERROR] 入力ファイルが見つかりません: {investment_advice_csv}")
        sys.exit(1)
    
    if not Path(ensemble_csv).exists():
        safe_print(f"[ERROR] 入力ファイルが見つかりません: {ensemble_csv}")
        sys.exit(1)
    
    # TXT生成実行
    generate_investment_txt(investment_advice_csv, ensemble_csv, output_txt)


if __name__ == "__main__":
    main()
