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

def generate_umatan_tickets(ensemble_csv, output_txt, top_n=5, max_combinations=4):
    """Phase 12 馬単買い目生成
    
    Args:
        ensemble_csv: アンサンブル結果CSV
        output_txt: 買い目ファイル出力先
        top_n: 上位候補数（デフォルト: 5）
        max_combinations: 最大買い目数（デフォルト: 4、推奨: 4～5）
    """
    print(f"\n{'='*80}")
    print(f"Phase 12: Step 7 - 馬単買い目生成（トリプル馬単）")
    print(f"{'='*80}")
    
    # 競馬場名マッピング
    keibajo_map = {
        '30': '門別', '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎'
    }
    
    # データ読み込み
    print(f"\n[1/4] アンサンブル結果読み込み: {ensemble_csv}")
    try:
        df = pd.read_csv(ensemble_csv, encoding='shift-jis')
        print("  - エンコーディング: Shift-JIS")
    except:
        df = pd.read_csv(ensemble_csv, encoding='utf-8')
        print("  - エンコーディング: UTF-8")
    
    print(f"  - データ件数: {len(df):,}")
    print(f"  - レース数: {df['race_id'].nunique()}件")
    
    # 馬名列を探す
    bamei_col = None
    for col in df.columns:
        if '馬名' in col or 'bamei' in col.lower() or col == 'name':
            bamei_col = col
            break
    
    if bamei_col:
        print(f"  - 馬名列: {bamei_col}")
    else:
        print(f"  ⚠️  馬名列が見つかりません（馬番のみ表示されます）")
    
    # 1着確率・2着確率の計算
    print(f"\n[2/4] 1着確率・2着確率の計算")
    
    # アンサンブルスコアから1着確率を推定（レースごとに正規化）
    # スコアが高いほど1着の可能性が高い
    df['win_proba_raw'] = df.groupby('race_id')['ensemble_score'].transform(
        lambda x: (x - x.min()) / (x.max() - x.min() + 1e-10)
    )
    
    # 1着確率をソフトマックス風に変換（合計が100%に近づく）
    df['win_proba_exp'] = df.groupby('race_id')['win_proba_raw'].transform(
        lambda x: (x ** 2)  # 2乗して差を広げる
    )
    df['win_proba'] = df.groupby('race_id')['win_proba_exp'].transform(
        lambda x: x / (x.sum() + 1e-10)
    )
    
    # 2着確率は2着以内確率からより控えめに計算
    # binary_proba（2着以内確率）とwin_probaの関係を考慮
    df['place_proba'] = df.groupby('race_id').apply(
        lambda g: (g['binary_proba'] * (1 - g['win_proba'])).clip(0, 1)
    ).reset_index(level=0, drop=True)
    
    print(f"  ✅ 確率計算完了")
    
    # 買い目生成
    print(f"\n[3/4] 馬単買い目生成")
    print(f"  - 上位候補数: {top_n}頭")
    print(f"  - 最大組合せ数: {max_combinations}通り")
    
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("Phase 12: トリプル馬単 買い目")
    output_lines.append("=" * 80)
    output_lines.append("")
    output_lines.append("【スコア・確率の見方】")
    output_lines.append("  - スコア: 総合評価（0.0～1.0、高いほど有力）")
    output_lines.append("  - 1着確率: この馬が1着になる確率（0%～100%）")
    output_lines.append("  - 2着確率: この馬が2着になる確率（0%～100%）")
    output_lines.append("  - 馬単確率: 指定された組合せが的中する確率（0%～100%）")
    output_lines.append("")
    output_lines.append("【確率の目安】")
    output_lines.append("  - 1着確率 30%以上: 本命級")
    output_lines.append("  - 1着確率 20～30%: 対抗～有力")
    output_lines.append("  - 1着確率 10～20%: 穴候補")
    output_lines.append("  - 馬単確率 5%以上: 高期待値")
    output_lines.append("  - 馬単確率 3～5%: 中期待値")
    output_lines.append("  - 馬単確率 1～3%: 低期待値")
    output_lines.append("")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    for race_id, group in df.groupby('race_id'):
        # race_idから競馬場とレース番号を抽出
        # 例: 202604224212 → 2026年04月22日 競馬場42(浦和) 12R
        race_id_str = str(race_id)
        keibajo_code = race_id_str[8:10]
        race_num = int(race_id_str[10:12])
        keibajo_name = keibajo_map.get(keibajo_code, f"競馬場{keibajo_code}")
        
        # アンサンブルスコア上位N頭を取得
        top_horses = group.nsmallest(top_n, 'ensemble_rank').sort_values('ensemble_rank')
        
        output_lines.append(f"【{keibajo_name} {race_num}R】")
        output_lines.append("")
        
        # 上位候補の情報
        output_lines.append("  上位候補:")
        for idx, row in top_horses.iterrows():
            uma_info = f"{int(row['umaban'])}番"
            if bamei_col and bamei_col in row and pd.notna(row[bamei_col]):
                uma_info += f" {row[bamei_col]}"
            
            output_lines.append(
                f"    {int(row['ensemble_rank'])}位: {uma_info} "
                f"(スコア: {row['ensemble_score']:.3f}, "
                f"1着確率: {row['win_proba']:.1%}, 2着確率: {row['place_proba']:.1%})"
            )
        output_lines.append("")
        
        # 馬単の組合せ生成（スマート戦略）
        output_lines.append("  推奨馬単:")
        combinations = []
        
        # 上位3頭を中心に組合せを生成
        # 戦略: 本命軸流し（本命→2,3,4着候補）+ 2番人気軸（2番人気→本命, 3着候補）
        top_3 = top_horses.head(3)
        
        # 馬番→馬名のマッピングを作成
        uma_name_map = {}
        if bamei_col:
            for _, row in top_horses.iterrows():
                umaban = int(row['umaban'])
                if bamei_col in row and pd.notna(row[bamei_col]):
                    uma_name_map[umaban] = row[bamei_col]
        
        for i, row1 in top_3.iterrows():
            for j, row2 in top_horses.iterrows():
                if row1['umaban'] != row2['umaban']:
                    uma1 = int(row1['umaban'])
                    uma2 = int(row2['umaban'])
                    win_proba1 = row1['win_proba']
                    place_proba2 = row2['place_proba']
                    # 馬単確率 = 1着候補の1着確率 × 2着候補の2着確率
                    umatan_proba = win_proba1 * place_proba2
                    
                    # スコア補正: 人気薄を含む組合せにボーナス
                    rank1 = int(row1['ensemble_rank'])
                    rank2 = int(row2['ensemble_rank'])
                    score_bonus = 1.0
                    if rank1 == 1 and rank2 <= 5:  # 本命軸流し
                        score_bonus = 1.05
                    elif rank1 == 2 and rank2 in [1, 3, 4]:  # 2番人気軸
                        score_bonus = 1.02
                    
                    umatan_proba_adj = umatan_proba * score_bonus
                    combinations.append((uma1, uma2, umatan_proba_adj, win_proba1, place_proba2, umatan_proba))
        
        # 確率順にソート
        combinations.sort(key=lambda x: x[2], reverse=True)
        
        # 上位組合せを表示（max_combinations通り、デフォルト4通り）
        for idx, (uma1, uma2, umatan_proba_adj, win1, place2, umatan_original) in enumerate(combinations[:max_combinations], 1):
            # 馬名を取得
            uma1_info = f"{uma1}番"
            uma2_info = f"{uma2}番"
            if uma1 in uma_name_map:
                uma1_info += f" {uma_name_map[uma1]}"
            if uma2 in uma_name_map:
                uma2_info += f" {uma_name_map[uma2]}"
            
            output_lines.append(
                f"    {idx:2d}. {uma1_info} → {uma2_info} "
                f"(馬単確率: {umatan_original:.2%}, {uma1}番1着: {win1:.1%}, {uma2}番2着: {place2:.1%})"
            )
        
        output_lines.append("")
        output_lines.append("-" * 80)
        output_lines.append("")
    
    # 保存
    print(f"\n[4/4] 買い目ファイル保存")
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
        print("      5 4  # オプション: top_n（デフォルト: 5）, max_combinations（デフォルト: 4）")
        print("\n推奨設定:")
        print("  - max_combinations=4: 各レース4通り（資金節約型）")
        print("  - max_combinations=5: 各レース5通り（バランス型）")
        print("  - max_combinations=6: 各レース6通り（網羅型）")
        sys.exit(1)
    
    try:
        ensemble_csv = sys.argv[1]
        output_txt = sys.argv[2]
        top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        max_combinations = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        
        generate_umatan_tickets(ensemble_csv, output_txt, top_n, max_combinations)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
