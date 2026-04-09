#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_race_results.py
note記事に結果を追加するスクリプト

使用法:
    python add_race_results.py --input 笠松_20260305_note.txt --race 8 --result "5,7,2" --hit "複勝:5,三連複:5-7-2"
    python add_race_results.py --input 笠松_20260305_note.txt --race 8 --result "3,5,7"  # 不的中の場合
"""

import argparse
import re
from pathlib import Path


def add_race_result(input_file, race_no, result, hit_bets=None, payouts=None):
    """
    note記事に結果を追加
    
    Args:
        input_file: 入力ファイルパス
        race_no: レース番号（1-12）
        result: 着順 "1着,2着,3着" 例: "5,7,2"
        hit_bets: 的中馬券 例: "複勝:5,三連複:5-7-2"
        payouts: 配当 例: "複勝:320,三連複:1240"
    """
    
    # ファイル読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # レース番号を検索
    race_pattern = rf"## 🏇 第{race_no}R 予想\n(.*?)(?=\n## 🏇 第\d+R 予想|\n## ⚠️ 注意事項|$)"
    race_match = re.search(race_pattern, content, re.DOTALL)
    
    if not race_match:
        print(f"❌ 第{race_no}Rが見つかりませんでした")
        return
    
    race_section = race_match.group(0)
    
    # 着順をパース
    places = result.split(',')
    if len(places) != 3:
        print(f"❌ 着順は「1着,2着,3着」の形式で指定してください: {result}")
        return
    
    # 結果セクションを作成
    result_section = "\n\n### 🏁 レース結果\n"
    result_section += f"**1着**: {places[0]}番  \n"
    result_section += f"**2着**: {places[1]}番  \n"
    result_section += f"**3着**: {places[2]}番  \n"
    
    # 的中セクションを作成
    if hit_bets:
        result_section += "\n### 🎯 的中馬券\n"
        for bet in hit_bets.split(','):
            if ':' in bet:
                bet_type, horses = bet.split(':')
                result_section += f"✅ {bet_type}: {horses}  \n"
        
        # 配当がある場合
        if payouts:
            result_section += "\n**配当**\n"
            for payout in payouts.split(','):
                if ':' in payout:
                    bet_type, amount = payout.split(':')
                    result_section += f"- {bet_type}: ¥{amount}  \n"
    else:
        result_section += "\n### ❌ 結果\n"
        result_section += "**不的中**\n"
    
    # 既存の結果セクションを削除
    race_section_clean = re.sub(r'\n### 🏁 レース結果.*?(?=\n---|\n## |$)', '', race_section, flags=re.DOTALL)
    race_section_clean = re.sub(r'\n### 🎯 的中馬券.*?(?=\n---|\n## |$)', '', race_section_clean, flags=re.DOTALL)
    race_section_clean = re.sub(r'\n### ❌ 結果.*?(?=\n---|\n## |$)', '', race_section_clean, flags=re.DOTALL)
    
    # 新しいセクションを追加（区切り線の前に挿入）
    race_section_new = re.sub(r'(\n---)', result_section + r'\1', race_section_clean)
    
    # 元のコンテンツを置換
    content_new = content.replace(race_section, race_section_new)
    
    # 出力ファイル名
    output_file = input_file.replace('.txt', '_updated.txt')
    
    # ファイル書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content_new)
    
    print(f"✅ 結果を追加しました: {output_file}")
    print(f"   第{race_no}R: {result}")
    if hit_bets:
        print(f"   的中: {hit_bets}")


def main():
    parser = argparse.ArgumentParser(description='note記事に結果を追加')
    parser.add_argument('--input', required=True, help='入力ファイル（例: 笠松_20260305_note.txt）')
    parser.add_argument('--race', type=int, required=True, help='レース番号（1-12）')
    parser.add_argument('--result', required=True, help='着順（例: 5,7,2）')
    parser.add_argument('--hit', help='的中馬券（例: 複勝:5,三連複:5-7-2）')
    parser.add_argument('--payout', help='配当（例: 複勝:320,三連複:1240）')
    
    args = parser.parse_args()
    
    add_race_result(
        input_file=args.input,
        race_no=args.race,
        result=args.result,
        hit_bets=args.hit,
        payouts=args.payout
    )


if __name__ == '__main__':
    main()
