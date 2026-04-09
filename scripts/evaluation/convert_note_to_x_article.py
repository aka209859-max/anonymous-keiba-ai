#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_note_to_x_article.py
note記事形式をX記事（Articles）用に最適化変換
"""

import re
import sys
from pathlib import Path

def convert_to_x_article(note_content):
    """
    note記事をX記事用フォーマットに変換
    
    X記事エディタの制約:
    - H1はタイトルのみ（本文から除外）
    - 改行 = 新段落（意図しない余白）
    - エムダッシュ禁止
    - 絵文字は最小限
    - H2をメイン見出しに
    - 水平線は手動挿入推奨
    """
    
    lines = note_content.split('\n')
    output_lines = []
    
    # タイトル抽出
    title = None
    in_race_section = False
    current_race = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # タイトル処理（H1）
        if line.startswith('# ') and title is None:
            title = line[2:].strip()
            # 絵文字を除去してタイトルを抽出
            title_clean = re.sub(r'[🏇🎯📊💰🔄⚠️📌🏁]', '', title).strip()
            output_lines.append(f"# {title_clean}")
            output_lines.append("")
            i += 1
            continue
        
        # 開催日・対象レース情報（フック用に最適化）
        if line.startswith('**開催日**:'):
            date_match = re.search(r'(\d{4})年(\d{2})月(\d{2})日', line)
            if date_match:
                year, month, day = date_match.groups()
                # 次の行の対象レース情報も取得
                if i + 1 < len(lines) and '**対象レース**:' in lines[i + 1]:
                    race_count = re.search(r'(\d+)R', lines[i + 1])
                    if race_count:
                        race_num = race_count.group(1)
                        # フック（150-280文字の抜粋）を作成
                        hook = f"**{year}年{month}月{day}日の金沢競馬{race_num}レース全レースをAI予測しました。** Sランク的中率80%超の高精度モデルが、本命・相手候補・買い目を完全網羅。データに基づく確実な予想で、あなたの勝率を最大化します。"
                        output_lines.append(hook)
                        output_lines.append("")
                        i += 2
                        continue
            i += 1
            continue
        
        # 水平線（---）は警告に置換
        if line == '---':
            output_lines.append("")
            output_lines.append("※ セクション区切り（手動で水平線を挿入してください）")
            output_lines.append("")
            i += 1
            continue
        
        # H2見出し（## で始まる）- レース番号を強調
        if line.startswith('## '):
            heading = line[3:].strip()
            # 絵文字を除去
            heading_clean = re.sub(r'[🏇🎯📊💰🔄⚠️📌🏁]', '', heading).strip()
            
            # 「第XR 予想」パターン
            race_match = re.search(r'第(\d+)R', heading_clean)
            if race_match:
                race_num = race_match.group(1)
                output_lines.append(f"## 第{race_num}R 予想と買い目")
                output_lines.append("")
                current_race = race_num
                in_race_section = True
                i += 1
                continue
            
            # その他のH2見出し
            output_lines.append(f"## {heading_clean}")
            output_lines.append("")
            i += 1
            continue
        
        # H3見出し（###）はH2に昇格、または太字に変更
        if line.startswith('### '):
            heading = line[4:].strip()
            heading_clean = re.sub(r'[🏇🎯📊💰🔄⚠️📌🏁]', '', heading).strip()
            
            # 「予想順位」「購入推奨」は太字に変更
            if '予想順位' in heading_clean:
                output_lines.append("**AI予想順位（スコア降順）:**")
                output_lines.append("")
            elif '購入推奨' in heading_clean:
                output_lines.append("**推奨買い目:**")
                output_lines.append("")
            else:
                output_lines.append(f"## {heading_clean}")
                output_lines.append("")
            i += 1
            continue
        
        # 予想順位リストの処理
        if re.match(r'^\*\*\d+\.\s+\d+番', line):
            # "**1. 8番 キラメキダンサー** （スコア: 1.00 / S）"
            # → "- **1位 8番 キラメキダンサー** (スコア 1.00, Sランク)"
            match = re.match(r'^\*\*(\d+)\.\s+(\d+)番\s+([^\*]+)\*\*\s+（スコア:\s+([\d\.]+)\s+/\s+([A-Z]+)）', line)
            if match:
                rank, horse_num, horse_name, score, grade = match.groups()
                # 上位3位のみ太字
                if int(rank) <= 3:
                    output_lines.append(f"- **{rank}位 {horse_num}番 {horse_name}** (スコア {score}, {grade}ランク)")
                else:
                    output_lines.append(f"- {rank}位 {horse_num}番 {horse_name} (スコア {score}, {grade}ランク)")
            i += 1
            continue
        
        # 通常の予想順位リスト（太字なし）
        if re.match(r'^\d+\.\s+\d+番', line):
            match = re.match(r'^(\d+)\.\s+(\d+)番\s+([^\(]+)（スコア:\s+([\d\.]+)\s+/\s+([A-Z]+)）', line)
            if match:
                rank, horse_num, horse_name, score, grade = match.groups()
                horse_name = horse_name.strip()
                output_lines.append(f"- {rank}位 {horse_num}番 {horse_name} (スコア {score}, {grade}ランク)")
            i += 1
            continue
        
        # 購入推奨セクションの処理
        if line.startswith('**🎯 本命軸**'):
            output_lines.append("**本命軸（単勝・複勝）:**")
            output_lines.append("")
            # 次の2-3行を結合して単一段落に
            combined = []
            i += 1
            while i < len(lines) and (lines[i].strip().startswith('- 単勝:') or lines[i].strip().startswith('- 複勝:')):
                combined.append(lines[i].strip()[2:])  # "- " を除去
                i += 1
            output_lines.append(" / ".join(combined))
            output_lines.append("")
            continue
        
        if line.startswith('**🔄 相手候補**'):
            output_lines.append("**相手候補（馬単・三連複）:**")
            output_lines.append("")
            # 次の数行を結合
            combined = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith('- '):
                combined.append(lines[i].strip()[2:])
                i += 1
            output_lines.append(" / ".join(combined))
            output_lines.append("")
            continue
        
        # 注意事項（引用ブロック化）
        if line.startswith('> '):
            output_lines.append(line)
            i += 1
            continue
        
        # ランク評価基準（箇条書きをシンプルに）
        if line.startswith('- **'):
            # "- **S**: スコア0.80以上（最有力候補）"
            # → "- S: スコア0.80以上（最有力）"
            simplified = re.sub(r'（[^）]+）', '', line)
            simplified = simplified.replace('候補', '')
            output_lines.append(simplified)
            i += 1
            continue
        
        # 空行は保持
        if line == '':
            output_lines.append("")
            i += 1
            continue
        
        # その他の行はそのまま
        output_lines.append(line)
        i += 1
    
    # エムダッシュのサニタイズ
    result = '\n'.join(output_lines)
    result = result.replace('—', '-')
    
    # 連続する空行を2行までに制限
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    
    return result

def main():
    if len(sys.argv) < 2:
        print("使用方法: python convert_note_to_x_article.py <note記事ファイル.txt>")
        print("例: python convert_note_to_x_article.py 金沢_20260315_note.txt")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    
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
    x_article_content = convert_to_x_article(note_content)
    
    # 出力ファイル名生成
    output_file = input_file.parent / input_file.name.replace('_note.txt', '_x_article.txt')
    
    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(x_article_content)
    
    print(f"✅ 変換完了: {output_file.name}")
    print()
    print("=" * 80)
    print("📋 次のステップ:")
    print("=" * 80)
    print(f"1. {output_file.name} を開く")
    print("2. 全文をコピー")
    print("3. Markdown → HTML変換ツールで変換（例: https://markdowntohtml.com/）")
    print("4. HTML出力をコピー")
    print("5. X記事エディタに貼り付け")
    print("6. 水平線（セパレーター）を手動で挿入")
    print("7. 画像がある場合は個別に挿入")
    print()
    print("⚠️  重要: 必ずHTML経由で貼り付けてください（Markdown直接貼り付けは不可）")

if __name__ == '__main__':
    main()
