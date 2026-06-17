#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_note_to_x_article_v2.py
note記事をX記事用「的中特化型指数上位馬ナビ」形式に変換
"""

import re
import sys
from pathlib import Path
from datetime import datetime

def extract_race_data(note_content):
    """note記事から各レースのトップ3を抽出"""
    
    lines = note_content.split('\n')
    races = []
    
    current_race = None
    horses = []
    
    for line in lines:
        line = line.strip()
        
        # レース番号検出
        if re.match(r'##\s+.*第(\d+)R', line):
            match = re.search(r'第(\d+)R', line)
            if match:
                if current_race and horses:
                    races.append({'race': current_race, 'horses': horses[:3]})
                current_race = match.group(1)
                horses = []
        
        # 予想順位（トップ3のみ）
        # "**1. 8番 キラメキダンサー** （スコア: 1.00 / S）"
        match = re.match(r'^\*\*(\d+)\.\s+(\d+)番\s+([^\*]+)\*\*\s+（スコア:\s+([\d\.]+)\s+/\s+([A-SD]+)）', line)
        if match:
            rank, horse_num, horse_name, score, grade = match.groups()
            if int(rank) <= 3:
                horses.append({
                    'rank': int(rank),
                    'num': horse_num,
                    'name': horse_name.strip(),
                    'score': float(score),
                    'grade': grade
                })
    
    # 最後のレースを追加
    if current_race and horses:
        races.append({'race': current_race, 'horses': horses[:3]})
    
    return races

def determine_rank_emoji(grade):
    """ランクに応じて絵文字を返す"""
    if grade == 'S':
        return '🔥'
    else:
        return ''

def convert_to_x_article_v2(note_content, note_url=None):
    """
    note記事をX記事の「的中特化型指数上位馬ナビ」形式に変換
    """
    
    lines = note_content.split('\n')
    
    # 開催情報を抽出
    venue = None
    date = None
    
    for line in lines:
        # タイトルから競馬場名を抽出
        if line.startswith('# ') and not venue:
            title = line[2:].strip()
            # "🏇 金沢競馬 AI予想" → "金沢"
            match = re.search(r'([^\s]+)競馬', title)
            if match:
                venue = match.group(1)
        
        # 開催日を抽出
        if '**開催日**:' in line and not date:
            match = re.search(r'(\d{4})年(\d{2})月(\d{2})日', line)
            if match:
                year, month, day = match.groups()
                date = f"{year}.{month}.{day}"
    
    # レースデータを抽出
    races = extract_race_data(note_content)
    
    if not races:
        return "エラー: レースデータが見つかりません"
    
    # 出力生成
    output = []
    
    # H1タイトル
    output.append(f"# {date} {venue}競馬｜的中特化AIが導き出した「全レース」指数上位馬公開")
    output.append("")
    output.append("[※ここにアイキャッチ画像を挿入]")
    output.append("")
    
    # H2: 上位馬一覧
    output.append(f"## {venue}1R〜{len(races)}R：的中特化型・指数上位馬ナビ")
    output.append("")
    output.append("的中精度に極振りしたAIが、本日の全レースで「的中確率」が高いと判断した上位3頭です。")
    output.append("")
    
    # 各レース
    for race_data in races:
        race_num = race_data['race']
        horses = race_data['horses']
        
        if not horses:
            continue
        
        # ランク判定（1位のグレードで判定）
        top_grade = horses[0]['grade']
        emoji = determine_rank_emoji(top_grade)
        rank_label = f"{emoji}（{top_grade}ランク）" if emoji else f"（{top_grade}ランク）"
        
        # レース見出し
        output.append(f"第{race_num}R {rank_label}")
        
        # 上位3頭（◎○▲形式）
        marks = ['◎', '○', '▲']
        horse_line = []
        
        for i, horse in enumerate(horses[:3]):
            mark = marks[i] if i < len(marks) else '△'
            # 1位は馬名も表示、2位・3位は番号のみ
            if i == 0:
                horse_line.append(f"{mark} {horse['num']}番 {horse['name']}")
            else:
                horse_line.append(f"{mark} {horse['num']}番")
        
        output.append(" / ".join(horse_line))
        output.append("")
    
    # H2: note誘導
    output.append("## 的中は「ゴール」ではない。資産を増やすための「スタート」だ。")
    output.append("")
    output.append("本日公開した「上位馬」をどう組み合わせ、どの券種で、どのような資金配分で勝負するか。的中を単なるラッキーで終わらせず、継続的な「資産」に変えるための具体的な買い目と詳細スコアについては、こちらのnoteで全レース分を公開しています。")
    output.append("")
    
    if note_url:
        output.append(f"👉 {note_url}")
    else:
        output.append("👉 [ここにnote記事のリンクを配置]")
    output.append("")
    
    # エムダッシュのサニタイズ
    result = '\n'.join(output)
    result = result.replace('—', '-')
    
    return result

def main():
    if len(sys.argv) < 2:
        print("使用方法: python convert_note_to_x_article_v2.py <note記事ファイル.txt> [note記事URL]")
        print("例: python convert_note_to_x_article_v2.py 金沢_20260315_note.txt https://note.com/...")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    note_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not input_file.exists():
        print(f"❌ ファイルが見つかりません: {input_file}")
        sys.exit(1)
    
    print(f"📄 変換中: {input_file.name}")
    
    # ファイル読み込み
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            note_content = f.read()
    except:
        with open(input_file, 'r', encoding='shift-jis') as f:
            note_content = f.read()
    
    # 変換
    x_article_content = convert_to_x_article_v2(note_content, note_url)
    
    # 出力ファイル名生成
    output_file = input_file.parent / input_file.name.replace('_note.txt', '_x_article_v2.txt')
    
    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(x_article_content)
    
    print(f"✅ 変換完了: {output_file.name}")
    print()
    print("=" * 80)
    print("📋 変換結果プレビュー:")
    print("=" * 80)
    # 最初の30行を表示
    preview_lines = x_article_content.split('\n')[:35]
    for line in preview_lines:
        print(line)
    if len(x_article_content.split('\n')) > 35:
        print("...")
    print()
    print("=" * 80)
    print("📋 次のステップ:")
    print("=" * 80)
    print(f"1. {output_file.name} を開く")
    print("2. 全文をコピー")
    print("3. Markdown → HTML変換ツールで変換（例: https://markdowntohtml.com/）")
    print("4. HTML出力をコピー")
    print("5. X記事エディタに貼り付け")
    print("6. アイキャッチ画像を挿入（推奨サイズ: 1792×716px, アスペクト比5:2）")
    print("7. note記事のリンクを挿入")
    print("8. 公開")
    print()
    print("⚠️  重要: 必ずHTML経由で貼り付けてください（Markdown直接貼り付けは不可）")

if __name__ == '__main__':
    main()
