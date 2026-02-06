#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
予想結果と実際の着順を照合して的中率を計算

川崎競馬 2026-02-05 の検証
"""

import pandas as pd

def check_predictions(csv_path, actual_results):
    """
    予想結果と実際の着順を照合
    
    Parameters
    ----------
    csv_path : str
        Phase 5アンサンブル結果CSV
    actual_results : dict
        実際の着順 {race_num: [1位馬番, 2位馬番, 3位馬番]}
    """
    # データ読み込み
    try:
        df = pd.read_csv(csv_path, encoding='shift-jis')
    except:
        df = pd.read_csv(csv_path, encoding='utf-8')
    
    print("=" * 100)
    print("川崎競馬 2026-02-05 予想結果と実績の照合")
    print("=" * 100)
    print()
    
    # 購入基準
    print("【購入基準】")
    print("・単勝: 1位")
    print("・複勝: 1位、2位")
    print("・馬単: 1→2、1→3、2→1、3→1")
    print("・三連複: 1,2,3,4,5位 BOX")
    print("・三連単: 1→2,3,4→2,3,4,5,6,7位")
    print()
    
    # 集計用
    total_races = len(actual_results)
    hit_stats = {
        '単勝': 0,
        '複勝_1位': 0,
        '複勝_2位': 0,
        '馬単': 0,
        '三連複': 0,
        '三連単': 0
    }
    
    # レース別詳細
    for race_num, actual in actual_results.items():
        # race_num が 1〜12 なので、4501〜4512 の形式に変換
        race_id = 202602050000 + 4500 + race_num
        
        race_data = df[df['race_id'] == race_id].sort_values('final_rank')
        
        if len(race_data) == 0:
            print(f"⚠️  第{race_num}R: データなし")
            continue
        
        # 予想トップ7
        top_7 = race_data.head(7)
        pred_1 = int(top_7.iloc[0]['umaban'])
        pred_2 = int(top_7.iloc[1]['umaban'])
        pred_3 = int(top_7.iloc[2]['umaban'])
        pred_4 = int(top_7.iloc[3]['umaban']) if len(top_7) > 3 else None
        pred_5 = int(top_7.iloc[4]['umaban']) if len(top_7) > 4 else None
        pred_6 = int(top_7.iloc[5]['umaban']) if len(top_7) > 5 else None
        pred_7 = int(top_7.iloc[6]['umaban']) if len(top_7) > 6 else None
        
        # 実際の着順
        actual_1, actual_2, actual_3 = actual
        
        print("=" * 100)
        print(f"第{race_num}R")
        print("=" * 100)
        print(f"予想: ◎{pred_1}番 ○{pred_2}番 ▲{pred_3}番 △{pred_4}番 {pred_5}番")
        print(f"実績: {actual_1}-{actual_2}-{actual_3}")
        print()
        
        # 単勝チェック
        hit_tansho = (pred_1 == actual_1)
        if hit_tansho:
            hit_stats['単勝'] += 1
            print("✅ 単勝的中！")
        else:
            print(f"❌ 単勝不的中 (予想{pred_1}番 → 実際{actual_1}番)")
        
        # 複勝チェック（1位）
        hit_fukusho_1 = (pred_1 in [actual_1, actual_2, actual_3])
        if hit_fukusho_1:
            hit_stats['複勝_1位'] += 1
            print(f"✅ 複勝(1位)的中！ {pred_1}番が{[actual_1, actual_2, actual_3].index(pred_1)+1}着")
        else:
            print(f"❌ 複勝(1位)不的中 (予想{pred_1}番)")
        
        # 複勝チェック（2位）
        hit_fukusho_2 = (pred_2 in [actual_1, actual_2, actual_3])
        if hit_fukusho_2:
            hit_stats['複勝_2位'] += 1
            print(f"✅ 複勝(2位)的中！ {pred_2}番が{[actual_1, actual_2, actual_3].index(pred_2)+1}着")
        else:
            print(f"❌ 複勝(2位)不的中 (予想{pred_2}番)")
        
        # 馬単チェック
        umatan_patterns = [
            (pred_1, pred_2),
            (pred_1, pred_3),
            (pred_2, pred_1),
            (pred_3, pred_1)
        ]
        hit_umatan = (actual_1, actual_2) in umatan_patterns
        if hit_umatan:
            hit_stats['馬単'] += 1
            print(f"✅ 馬単的中！ {actual_1}→{actual_2}")
        else:
            print(f"❌ 馬単不的中 (実際{actual_1}→{actual_2})")
        
        # 三連複チェック（1〜5位BOX）
        pred_box = {pred_1, pred_2, pred_3, pred_4, pred_5}
        actual_set = {actual_1, actual_2, actual_3}
        hit_sanrenpuku = actual_set.issubset(pred_box)
        if hit_sanrenpuku:
            hit_stats['三連複'] += 1
            print(f"✅ 三連複的中！ {actual_1}-{actual_2}-{actual_3}")
        else:
            print(f"❌ 三連複不的中 (実際{actual_1}-{actual_2}-{actual_3}, 予想BOX{sorted(pred_box)})")
        
        # 三連単チェック（1→2,3,4→2,3,4,5,6,7）
        hit_sanrentan = False
        if actual_1 == pred_1:
            if actual_2 in [pred_2, pred_3, pred_4]:
                if actual_3 in [pred_2, pred_3, pred_4, pred_5, pred_6, pred_7]:
                    hit_sanrentan = True
        
        if hit_sanrentan:
            hit_stats['三連単'] += 1
            print(f"✅ 三連単的中！ {actual_1}→{actual_2}→{actual_3}")
        else:
            print(f"❌ 三連単不的中 (実際{actual_1}→{actual_2}→{actual_3})")
        
        print()
    
    # 総合結果
    print("=" * 100)
    print("総合結果")
    print("=" * 100)
    print(f"総レース数: {total_races}レース")
    print()
    print(f"【的中率】")
    print(f"・単勝       : {hit_stats['単勝']:2d}/{total_races} ({hit_stats['単勝']/total_races*100:5.1f}%)")
    print(f"・複勝(1位)  : {hit_stats['複勝_1位']:2d}/{total_races} ({hit_stats['複勝_1位']/total_races*100:5.1f}%)")
    print(f"・複勝(2位)  : {hit_stats['複勝_2位']:2d}/{total_races} ({hit_stats['複勝_2位']/total_races*100:5.1f}%)")
    print(f"・馬単       : {hit_stats['馬単']:2d}/{total_races} ({hit_stats['馬単']/total_races*100:5.1f}%)")
    print(f"・三連複     : {hit_stats['三連複']:2d}/{total_races} ({hit_stats['三連複']/total_races*100:5.1f}%)")
    print(f"・三連単     : {hit_stats['三連単']:2d}/{total_races} ({hit_stats['三連単']/total_races*100:5.1f}%)")
    print()
    
    # 評価
    print("=" * 100)
    print("評価")
    print("=" * 100)
    
    tansho_rate = hit_stats['単勝'] / total_races * 100
    fukusho_rate = (hit_stats['複勝_1位'] + hit_stats['複勝_2位']) / (total_races * 2) * 100
    sanrenpuku_rate = hit_stats['三連複'] / total_races * 100
    
    if tansho_rate >= 30:
        print("✅ 単勝的中率: 優秀（30%以上）")
    elif tansho_rate >= 20:
        print("🟡 単勝的中率: 良好（20%以上）")
    else:
        print("⚠️  単勝的中率: 要改善（20%未満）")
    
    if fukusho_rate >= 50:
        print("✅ 複勝的中率: 優秀（50%以上）")
    elif fukusho_rate >= 40:
        print("🟡 複勝的中率: 良好（40%以上）")
    else:
        print("⚠️  複勝的中率: 要改善（40%未満）")
    
    if sanrenpuku_rate >= 40:
        print("✅ 三連複的中率: 優秀（40%以上）")
    elif sanrenpuku_rate >= 30:
        print("🟡 三連複的中率: 良好（30%以上）")
    else:
        print("⚠️  三連複的中率: 要改善（30%未満）")
    
    print()
    print("=" * 100)
    
    return hit_stats

if __name__ == "__main__":
    # 実際の着順
    actual_results = {
        1: [2, 8, 11],
        2: [5, 10, 3],
        3: [12, 1, 10],
        4: [8, 2, 1],
        5: [9, 5, 1],
        6: [10, 5, 4],
        7: [3, 12, 2],
        8: [3, 1, 4],
        9: [6, 10, 9],
        10: [2, 11, 4],
        11: [4, 3, 1],
        12: [1, 7, 9]
    }
    
    csv_path = "/home/user/uploaded_files/川崎_20260205_ensemble.csv"
    check_predictions(csv_path, actual_results)
