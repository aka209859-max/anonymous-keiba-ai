#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年1-2月シミュレーション実行スクリプト (Phase 3)
Phase 3の二値分類モデルを使用して2026年1-2月の実データで予測を実行し、
的中率・回収率を印別で分析する
"""

import sys
import os
import psycopg2
import pandas as pd
import numpy as np
import lightgbm as lgb
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

# 競馬場コードとモデルファイルのマッピング
VENUE_MODELS = {
    '44': {'name': '大井', 'model': 'ooi_2023-2024_v3_model.txt'},
    '43': {'name': '船橋', 'model': 'funabashi_2020-2025_v3_model.txt'},
    '45': {'name': '川崎', 'model': 'kawasaki_2020-2025_v3_model.txt'},
    '42': {'name': '浦和', 'model': 'urawa_2020-2025_v3_model.txt'},
    '48': {'name': '名古屋', 'model': 'nagoya_2022-2025_v3_model.txt'},
    '50': {'name': '園田', 'model': 'sonoda_2020-2025_v3_model.txt'},
    '47': {'name': '笠松', 'model': 'kasamatsu_2020-2025_v3_model.txt'},
    '55': {'name': '佐賀', 'model': 'saga_2020-2025_v3_model.txt'},
    '54': {'name': '高知', 'model': 'kochi_2020-2025_v3_model.txt'},
    '51': {'name': '姫路', 'model': 'himeji_2020-2025_v3_model.txt'},
}

def extract_2026_data(venue_code):
    """2026年1-2月のデータを抽出"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        query = """
        SELECT 
            -- レース識別情報
            s.kaisai_nen,
            s.kaisai_tsukihi,
            s.keibajo_code,
            s.race_bango,
            s.umaban,
            
            -- 結果（正解ラベル）
            CASE WHEN CAST(s.kakutei_chakujun AS INTEGER) <= 3 THEN 1 ELSE 0 END as target,
            s.kakutei_chakujun,
            
            -- 払戻金情報（nvd_hrテーブルから取得）
            CAST(hr.haraimodoshi_tansho_1a AS INTEGER) AS tansho_haraimodoshi,
            CAST(hr.haraimodoshi_fukusho_1a AS INTEGER) AS fukusho_haraimodoshi_1,
            CAST(hr.haraimodoshi_fukusho_2a AS INTEGER) AS fukusho_haraimodoshi_2,
            CAST(hr.haraimodoshi_fukusho_3a AS INTEGER) AS fukusho_haraimodoshi_3,
            
            -- レース情報
            s.shusso_tosu,
            r.kyori,
            r.track_code,
            r.baba_jotai_code,
            
            -- 馬情報
            s.seibetsu,
            s.barei,
            s.kishu_code,
            s.chokyoshi_code,
            s.futan_juryo,
            
            -- 前走情報（過去5走）
            s.prev1_rank,
            s.prev1_time,
            s.prev1_last3f,
            s.prev1_weight,
            s.prev1_corner1,
            s.prev1_corner2,
            s.prev1_corner3,
            s.prev1_corner4,
            s.prev1_kyori,
            s.prev1_track,
            s.prev1_baba,
            
            s.prev2_rank,
            s.prev2_time,
            s.prev2_last3f,
            s.prev2_weight,
            s.prev2_corner1,
            s.prev2_corner2,
            s.prev2_corner3,
            s.prev2_corner4,
            s.prev2_kyori,
            s.prev2_track,
            s.prev2_baba,
            
            s.prev3_rank,
            s.prev3_time,
            s.prev3_last3f,
            s.prev3_weight,
            s.prev3_corner1,
            s.prev3_corner2,
            s.prev3_corner3,
            s.prev3_corner4,
            s.prev3_kyori,
            s.prev3_track,
            s.prev3_baba,
            
            s.prev4_rank,
            s.prev4_time,
            s.prev4_last3f,
            s.prev4_weight,
            s.prev4_corner1,
            s.prev4_corner2,
            s.prev4_corner3,
            s.prev4_corner4,
            s.prev4_kyori,
            s.prev4_track,
            s.prev4_baba,
            
            s.prev5_rank,
            s.prev5_time,
            s.prev5_last3f,
            s.prev5_weight,
            s.prev5_corner1,
            s.prev5_corner2,
            s.prev5_corner3,
            s.prev5_corner4,
            s.prev5_kyori,
            s.prev5_track,
            s.prev5_baba,
            
            s.ketto_toroku_bango
            
        FROM nvd_se s
        LEFT JOIN nvd_ra r ON 
            r.kaisai_nen = s.kaisai_nen AND
            r.kaisai_tsukihi = s.kaisai_tsukihi AND
            r.keibajo_code = s.keibajo_code AND
            r.race_bango = s.race_bango
        LEFT JOIN nvd_hr hr ON 
            hr.kaisai_nen = s.kaisai_nen AND
            hr.kaisai_tsukihi = s.kaisai_tsukihi AND
            hr.keibajo_code = s.keibajo_code AND
            hr.race_bango = s.race_bango
        WHERE s.kaisai_nen = '2026'
        AND s.keibajo_code = %s
        AND (
            (s.kaisai_tsukihi >= '0101' AND s.kaisai_tsukihi <= '0131') OR
            (s.kaisai_tsukihi >= '0201' AND s.kaisai_tsukihi <= '0203')
        )
        AND s.kakutei_chakujun IS NOT NULL
        AND s.kakutei_chakujun != '0'
        ORDER BY s.kaisai_tsukihi, s.race_bango, s.umaban
        """
        
        df = pd.read_sql_query(query, conn, params=(venue_code,))
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"❌ データ抽出エラー: {e}")
        return None

def load_model(model_path):
    """LightGBMモデルをロード"""
    
    try:
        if not os.path.exists(model_path):
            print(f"❌ モデルファイルが見つかりません: {model_path}")
            return None
            
        model = lgb.Booster(model_file=model_path)
        return model
        
    except Exception as e:
        print(f"❌ モデル読み込みエラー: {e}")
        return None

def preprocess_features(df):
    """特徴量の前処理"""
    
    # 識別情報と正解ラベルを保存
    id_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 
               'umaban', 'target', 'kakutei_chakujun',
               'tansho_haraimodoshi', 'fukusho_haraimodoshi_1',
               'fukusho_haraimodoshi_2', 'fukusho_haraimodoshi_3']
    
    df_id = df[id_cols].copy()
    
    # 特徴量のみ抽出
    feature_cols = [col for col in df.columns if col not in id_cols]
    X = df[feature_cols].copy()
    
    # 数値型に変換
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    
    # 欠損値を平均値で補完
    X = X.fillna(X.mean())
    
    # 無限大を0に置換
    X = X.replace([np.inf, -np.inf], 0)
    
    return X, df_id

def assign_mark(prob):
    """確率に基づいて印を割り当て"""
    
    if prob >= 0.7:
        return '◎'
    elif prob >= 0.5:
        return '○'
    elif prob >= 0.35:
        return '▲'
    elif prob >= 0.2:
        return '△'
    else:
        return '×'

def calculate_hitrate_and_recovery(df_results):
    """的中率と回収率を計算"""
    
    summary = []
    
    # 全体
    total_races = len(df_results)
    total_hits = (df_results['target'] == 1).sum()
    hitrate = total_hits / total_races * 100 if total_races > 0 else 0
    
    # 単勝回収率（本命◎のみ）
    honmei = df_results[df_results['mark'] == '◎']
    if len(honmei) > 0:
        honmei_hits = (honmei['target'] == 1).sum()
        honmei_hitrate = honmei_hits / len(honmei) * 100
        
        # 単勝払戻（1着の場合のみ）
        honmei_1st = honmei[honmei['kakutei_chakujun'] == '1'].copy()
        tansho_return = honmei_1st['tansho_haraimodoshi'].fillna(0).sum()
        tansho_investment = len(honmei) * 100  # 100円×点数
        tansho_recovery = tansho_return / tansho_investment * 100 if tansho_investment > 0 else 0
    else:
        honmei_hitrate = 0
        tansho_recovery = 0
        tansho_return = 0
    
    # 複勝回収率（◎○▲）
    fukusho_marks = df_results[df_results['mark'].isin(['◎', '○', '▲'])]
    if len(fukusho_marks) > 0:
        fukusho_hits = (fukusho_marks['target'] == 1).sum()
        fukusho_hitrate = fukusho_hits / len(fukusho_marks) * 100
        
        # 複勝払戻（3着以内）
        fukusho_return = 0
        for _, row in fukusho_marks.iterrows():
            chaku = str(row['kakutei_chakujun'])
            if chaku == '1':
                fukusho_return += row['fukusho_haraimodoshi_1'] if pd.notna(row['fukusho_haraimodoshi_1']) else 0
            elif chaku == '2':
                fukusho_return += row['fukusho_haraimodoshi_2'] if pd.notna(row['fukusho_haraimodoshi_2']) else 0
            elif chaku == '3':
                fukusho_return += row['fukusho_haraimodoshi_3'] if pd.notna(row['fukusho_haraimodoshi_3']) else 0
        
        fukusho_investment = len(fukusho_marks) * 100
        fukusho_recovery = fukusho_return / fukusho_investment * 100 if fukusho_investment > 0 else 0
    else:
        fukusho_hitrate = 0
        fukusho_recovery = 0
        fukusho_return = 0
    
    summary.append({
        'category': '全体',
        'count': total_races,
        'hits': total_hits,
        'hitrate': hitrate,
        'investment': 0,
        'return': 0,
        'recovery': 0
    })
    
    summary.append({
        'category': '単勝（◎本命のみ）',
        'count': len(honmei),
        'hits': honmei['target'].sum() if len(honmei) > 0 else 0,
        'hitrate': honmei_hitrate,
        'investment': len(honmei) * 100,
        'return': tansho_return if len(honmei) > 0 else 0,
        'recovery': tansho_recovery
    })
    
    summary.append({
        'category': '複勝（◎○▲）',
        'count': len(fukusho_marks),
        'hits': fukusho_hits if len(fukusho_marks) > 0 else 0,
        'hitrate': fukusho_hitrate,
        'investment': len(fukusho_marks) * 100,
        'return': fukusho_return if len(fukusho_marks) > 0 else 0,
        'recovery': fukusho_recovery
    })
    
    # 印別集計
    for mark in ['◎', '○', '▲', '△', '×']:
        mark_df = df_results[df_results['mark'] == mark]
        if len(mark_df) > 0:
            mark_hits = (mark_df['target'] == 1).sum()
            mark_hitrate = mark_hits / len(mark_df) * 100
            
            summary.append({
                'category': f'印別: {mark}',
                'count': len(mark_df),
                'hits': mark_hits,
                'hitrate': mark_hitrate,
                'investment': 0,
                'return': 0,
                'recovery': 0
            })
    
    return pd.DataFrame(summary)

def simulate_venue(venue_code, venue_name, model_path):
    """競馬場別のシミュレーション実行"""
    
    print(f"\n{'='*80}")
    print(f"シミュレーション実行: {venue_name} (コード: {venue_code})")
    print(f"{'='*80}")
    
    # データ抽出
    print(f"📊 データ抽出中...")
    df = extract_2026_data(venue_code)
    
    if df is None or len(df) == 0:
        print(f"⚠️  データが見つかりませんでした")
        return None, None
    
    print(f"✅ データ件数: {len(df):,} 件")
    
    # モデル読み込み
    print(f"🤖 モデル読み込み中: {model_path}")
    model = load_model(model_path)
    
    if model is None:
        print(f"❌ モデル読み込み失敗")
        return None, None
    
    print(f"✅ モデル読み込み完了")
    
    # 特徴量前処理
    print(f"⚙️  特徴量前処理中...")
    X, df_id = preprocess_features(df)
    
    # 予測実行
    print(f"🔮 予測実行中...")
    y_pred_prob = model.predict(X, num_iteration=model.best_iteration)
    
    # 結果結合
    df_results = df_id.copy()
    df_results['prob'] = y_pred_prob
    df_results['mark'] = df_results['prob'].apply(assign_mark)
    df_results['venue_name'] = venue_name
    
    # 的中率・回収率計算
    print(f"📈 的中率・回収率計算中...")
    df_summary = calculate_hitrate_and_recovery(df_results)
    df_summary['venue_name'] = venue_name
    df_summary['venue_code'] = venue_code
    
    print(f"✅ シミュレーション完了: {venue_name}")
    
    return df_results, df_summary

def main():
    """メイン処理"""
    
    print("=" * 80)
    print("2026年1-2月シミュレーション実行 (Phase 3)")
    print("=" * 80)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象期間: 2026-01-01 ～ 2026-02-03")
    print(f"対象競馬場: 10競馬場")
    print("=" * 80)
    
    all_results = []
    all_summaries = []
    
    # 各競馬場でシミュレーション実行
    for venue_code, venue_info in VENUE_MODELS.items():
        venue_name = venue_info['name']
        model_path = venue_info['model']
        
        df_results, df_summary = simulate_venue(venue_code, venue_name, model_path)
        
        if df_results is not None:
            all_results.append(df_results)
        
        if df_summary is not None:
            all_summaries.append(df_summary)
    
    # 結果を結合
    if len(all_results) > 0:
        df_all_results = pd.concat(all_results, ignore_index=True)
        df_all_summaries = pd.concat(all_summaries, ignore_index=True)
        
        # CSV出力
        output_results = 'simulation_2026_results.csv'
        output_summary = 'simulation_2026_summary.csv'
        
        df_all_results.to_csv(output_results, index=False, encoding='utf-8-sig')
        df_all_summaries.to_csv(output_summary, index=False, encoding='utf-8-sig')
        
        print(f"\n{'='*80}")
        print(f"✅ シミュレーション完了")
        print(f"{'='*80}")
        print(f"📄 予測結果: {output_results}")
        print(f"📄 サマリー: {output_summary}")
        print(f"{'='*80}")
        
        # テキストレポート出力
        generate_text_report(df_all_summaries, df_all_results)
        
    else:
        print("\n❌ シミュレーション失敗: データまたはモデルが見つかりませんでした")

def generate_text_report(df_summary, df_results):
    """テキストレポート生成"""
    
    report = []
    report.append("=" * 80)
    report.append("2026年1-2月シミュレーション結果レポート (Phase 3)")
    report.append("=" * 80)
    report.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"対象期間: 2026-01-01 ～ 2026-02-03")
    report.append(f"対象競馬場: {len(VENUE_MODELS)}競馬場")
    report.append(f"総データ件数: {len(df_results):,} 件")
    report.append("=" * 80)
    report.append("")
    
    # 競馬場別サマリー
    report.append("【競馬場別サマリー】")
    report.append("")
    
    for venue_code, venue_info in VENUE_MODELS.items():
        venue_name = venue_info['name']
        venue_summary = df_summary[df_summary['venue_name'] == venue_name]
        
        if len(venue_summary) > 0:
            report.append(f"■ {venue_name}")
            
            for _, row in venue_summary.iterrows():
                if row['category'] == '全体':
                    report.append(f"  総件数: {int(row['count']):,} 件")
                    report.append(f"  的中数: {int(row['hits']):,} 件")
                    report.append(f"  的中率: {row['hitrate']:.2f}%")
                elif row['category'] == '単勝（◎本命のみ）':
                    report.append(f"  単勝◎: {int(row['count']):,}点 / 的中率 {row['hitrate']:.2f}% / 回収率 {row['recovery']:.2f}%")
                elif row['category'] == '複勝（◎○▲）':
                    report.append(f"  複勝◎○▲: {int(row['count']):,}点 / 的中率 {row['hitrate']:.2f}% / 回収率 {row['recovery']:.2f}%")
            
            report.append("")
    
    # 全体集計
    report.append("=" * 80)
    report.append("【全体集計】")
    report.append("")
    
    total_count = len(df_results)
    total_hits = (df_results['target'] == 1).sum()
    total_hitrate = total_hits / total_count * 100 if total_count > 0 else 0
    
    report.append(f"総データ件数: {total_count:,} 件")
    report.append(f"総的中数: {total_hits:,} 件")
    report.append(f"総的中率: {total_hitrate:.2f}%")
    report.append("")
    
    # 印別集計
    report.append("【印別パフォーマンス】")
    report.append("")
    
    for mark in ['◎', '○', '▲', '△', '×']:
        mark_df = df_results[df_results['mark'] == mark]
        if len(mark_df) > 0:
            mark_hits = (mark_df['target'] == 1).sum()
            mark_hitrate = mark_hits / len(mark_df) * 100
            report.append(f"{mark}: {len(mark_df):,}件 / 的中 {mark_hits:,}件 / 的中率 {mark_hitrate:.2f}%")
    
    report.append("")
    report.append("=" * 80)
    
    # ファイル出力
    output_txt = 'simulation_2026_summary.txt'
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"📄 テキストレポート: {output_txt}")

if __name__ == '__main__':
    main()
