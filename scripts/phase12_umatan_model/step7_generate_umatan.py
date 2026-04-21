#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: Step 7 - 馬単買い目生成（SPAT4 LOTO トリプル馬単用）
"""

import sys
import os
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def generate_umatan_tickets(ensemble_csv, output_txt, top_n=5, max_combinations=10):
    """Phase 12 馬単買い目生成"""
    print(f"\n{'='*80}")
    print(f"Phase 12: Step 7 - 馬単買い目生成（トリプル馬単）")
    print(f"{'='*80}")
    
    # データ読み込み
    print(f"\n[1/3] アンサンブル結果読み込み: {ensemble_csv}")
    try:
        df = pd.read_csv(ensemble_csv, encoding='shift-jis')
        print("  - エンコーディング: Shift-JIS")
    except:
        df = pd.read_csv(ensemble_csv, encoding='utf-8')
        print("  - エンコーディング: UTF-8")
    
    print(f"  - データ件数: {len(df):,}")
    print(f"  - レース数: {df['race_id'].nunique()}件")
    
    # 買い目生成
    print(f"\n[2/3] 馬単買い目生成")
    print(f"  - 上位候補数: {top_n}頭")
    print(f"  - 最大組合せ数: {max_combinations}通り")
    
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("Phase 12: トリプル馬単 買い目")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    for race_id, group in df.groupby('race_id'):
        # アンサンブルスコア上位N頭を取得
        top_horses = group.nsmallest(top_n, 'ensemble_rank').sort_values('ensemble_rank')
        
        output_lines.append(f"【レース: {race_id}】")
        output_lines.append("")
        
        # 上位候補の情報
        output_lines.append("  上位候補:")
        for idx, row in top_horses.iterrows():
            output_lines.append(
                f"    {int(row['ensemble_rank'])}位: {int(row['umaban'])}番 "
                f"(スコア: {row['ensemble_score']:.4f}, "
                f"2着以内確率: {row['binary_proba']:.2f})"
            )
        output_lines.append("")
        
        # 馬単の組合せ生成
        output_lines.append("  推奨馬単:")
        combinations = []
        for i, row1 in top_horses.iterrows():
            for j, row2 in top_horses.iterrows():
                if row1['umaban'] != row2['umaban']:
                    uma1 = int(row1['umaban'])
                    uma2 = int(row2['umaban'])
                    score1 = row1['ensemble_score']
                    score2 = row2['ensemble_score']
                    # 組合せスコア = 1着候補スコア * 2 + 2着候補スコア
                    combo_score = score1 * 2 + score2
                    combinations.append((uma1, uma2, combo_score))
        
        # スコア順にソート
        combinations.sort(key=lambda x: x[2], reverse=True)
        
        # 上位組合せを表示
        for idx, (uma1, uma2, score) in enumerate(combinations[:max_combinations], 1):
            output_lines.append(f"    {idx:2d}. {uma1}番 → {uma2}番 (スコア: {score:.4f})")
        
        output_lines.append("")
        output_lines.append("-" * 80)
        output_lines.append("")
    
    # 保存
    print(f"\n[3/3] 買い目ファイル保存")
    output_dir = os.path.dirname(output_txt)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(output_txt, 'w', encoding='shift-jis') as f:
            f.write('\n'.join(output_lines))
        print(f"  ✅ 買い目を保存（Shift-JIS）: {output_txt}")
    except:
        output_txt_utf8 = output_txt.replace('.txt', '_utf8.txt')
        with open(output_txt_utf8, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"  ✅ 買い目を保存（UTF-8）: {output_txt_utf8}")
    
    print(f"\n{'='*80}")
    print("✅ Phase 12 Step 7 完了")
    print(f"{'='*80}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用法: python step7_generate_umatan.py <ensemble_csv> <output_txt> [top_n] [max_combinations]")
        print("\n例: python step7_generate_umatan.py \\")
        print("      data/phase12_umatan/predictions/ensemble/船橋_20260422_ensemble.csv \\")
        print("      data/phase12_umatan/predictions/tickets/船橋_20260422_umatan.txt \\")
        print("      5 10  # オプション: top_n（デフォルト: 5）, max_combinations（デフォルト: 10）")
        sys.exit(1)
    
    try:
        ensemble_csv = sys.argv[1]
        output_txt = sys.argv[2]
        top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        max_combinations = int(sys.argv[4]) if len(sys.argv) > 4 else 10
        
        generate_umatan_tickets(ensemble_csv, output_txt, top_n, max_combinations)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
