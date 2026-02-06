#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配信用フォーマット生成スクリプト

Twitter/ブログ用の予想テキストを自動生成
"""

import pandas as pd
import sys
from datetime import datetime

def generate_distribution_text(csv_path, keibajo_name, target_date):
    """
    配信用テキスト生成
    
    Parameters
    ----------
    csv_path : str
        Phase 5アンサンブル結果CSV
    keibajo_name : str
        競馬場名（例: 佐賀）
    target_date : str
        開催日（例: 2026-02-07）
    """
    # データ読み込み
    try:
        df = pd.read_csv(csv_path, encoding='shift-jis')
    except:
        df = pd.read_csv(csv_path, encoding='utf-8')
    
    # 日付フォーマット
    dt = datetime.strptime(target_date, '%Y-%m-%d')
    date_str = f"{dt.month}/{dt.day}"
    
    # ブログ用フォーマット
    blog_text = []
    blog_text.append("=" * 80)
    blog_text.append(f"【{keibajo_name}競馬 {date_str} AI予想】")
    blog_text.append("=" * 80)
    blog_text.append("")
    blog_text.append("川崎競馬での検証結果: 単勝41.7%, 複勝66.7%, 三連複41.7%")
    blog_text.append("")
    
    # Twitter用フォーマット
    twitter_text = []
    twitter_text.append(f"{date_str} {keibajo_name}競馬 AI予想📊")
    twitter_text.append("")
    
    # レース別予想
    for race_id in sorted(df['race_id'].unique()):
        race_data = df[df['race_id'] == race_id].sort_values('final_rank')
        race_num = int(str(race_id)[-2:])
        
        top5 = race_data.head(5)
        pred_1 = int(top5.iloc[0]['umaban'])
        pred_2 = int(top5.iloc[1]['umaban'])
        pred_3 = int(top5.iloc[2]['umaban'])
        pred_4 = int(top5.iloc[3]['umaban'])
        pred_5 = int(top5.iloc[4]['umaban'])
        
        score_1 = top5.iloc[0]['ensemble_score']
        score_2 = top5.iloc[1]['ensemble_score']
        score_3 = top5.iloc[2]['ensemble_score']
        
        prob_1 = top5.iloc[0]['binary_probability']
        prob_2 = top5.iloc[1]['binary_probability']
        prob_3 = top5.iloc[2]['binary_probability']
        
        # ブログ用
        blog_text.append("-" * 80)
        blog_text.append(f"■第{race_num}R")
        blog_text.append("-" * 80)
        blog_text.append(f"◎ 本命: {pred_1:02d}番 (スコア: {score_1:.3f}, 入線確率: {prob_1:.1%})")
        blog_text.append(f"○ 対抗: {pred_2:02d}番 (スコア: {score_2:.3f}, 入線確率: {prob_2:.1%})")
        blog_text.append(f"▲ 単穴: {pred_3:02d}番 (スコア: {score_3:.3f}, 入線確率: {prob_3:.1%})")
        blog_text.append(f"△ 連下: {pred_4:02d}, {pred_5:02d}")
        blog_text.append("")
        blog_text.append("推奨馬券:")
        blog_text.append(f"  ・単勝: {pred_1}")
        blog_text.append(f"  ・複勝: {pred_1}, {pred_2}")
        blog_text.append(f"  ・馬連: {pred_1}-{pred_2}, {pred_1}-{pred_3}")
        blog_text.append(f"  ・三連複: {pred_1},{pred_2},{pred_3},{pred_4},{pred_5} BOX")
        blog_text.append("")
        
        # Twitter用（最初の3レースのみ）
        if race_num <= 3:
            twitter_text.append(f"{race_num}R")
            twitter_text.append(f"◎{pred_1:02d}({prob_1*100:.0f}%) ○{pred_2:02d} ▲{pred_3:02d}")
            twitter_text.append("")
    
    blog_text.append("=" * 80)
    blog_text.append("※この予想はAIによる統計的分析に基づいています")
    blog_text.append("※馬券購入は自己責任でお願いします")
    blog_text.append("=" * 80)
    
    twitter_text.append("全レース詳細→ブログへ")
    twitter_text.append(f"#地方競馬 #{keibajo_name}競馬 #AI予想")
    
    return {
        'blog': '\n'.join(blog_text),
        'twitter': '\n'.join(twitter_text)
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用法: python generate_distribution.py <ensemble_csv> <output_txt>")
        print("\n例:")
        print("  python generate_distribution.py data/predictions/phase5/佐賀_20260207_ensemble.csv predictions/佐賀_20260207_配信用.txt")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    output_txt = sys.argv[2]
    
    # ファイル名から競馬場名と日付を抽出
    import os
    basename = os.path.basename(csv_path)
    # 例: 佐賀_20260207_ensemble.csv → keibajo_name='佐賀', target_date='2026-02-07'
    parts = basename.replace('_ensemble.csv', '').split('_')
    keibajo_name = parts[0]
    date_str = parts[1]  # YYYYMMDD
    target_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    texts = generate_distribution_text(csv_path, keibajo_name, target_date)
    
    # 統合テキスト保存
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("【ブログ用フォーマット】\n")
        f.write("=" * 80 + "\n\n")
        f.write(texts['blog'])
        f.write("\n\n\n")
        f.write("=" * 80 + "\n")
        f.write("【Twitter用フォーマット】\n")
        f.write("=" * 80 + "\n\n")
        f.write(texts['twitter'])
    
    print(f"✅ 配信用テキスト: {output_txt}")
    print()
    print("【Twitter用プレビュー】")
    print(texts['twitter'])
