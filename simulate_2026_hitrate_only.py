#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年1月シミュレーション実行スクリプト (的中率のみ)
Phase 3の二値分類モデルを使用して2026年1月の実データで予測を実行し、
的中率を印別で分析する（払戻金データは使用しない）
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
    """2026年1月のデータを抽出（Phase 3学習時と同じロジック）
    
    ROW_NUMBER()を使用してnvd_seテーブルを自己JOINし、
    前走〜5走前のデータを動的に取得します。
    """
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Phase 3学習時と同じSQLロジック
        query = """
        WITH target_race AS (
            -- 予測対象レース（2026年1月のレース）
            SELECT 
                ra.kaisai_nen,
                ra.kaisai_tsukihi,
                ra.keibajo_code,
                ra.race_bango,
                se.ketto_toroku_bango,
                se.umaban,
                se.kakutei_chakujun,
                
                -- レース情報
                ra.kyori,
                ra.track_code,
                ra.babajotai_code_shiba,
                ra.babajotai_code_dirt,
                ra.tenko_code,
                ra.shusso_tosu,
                ra.grade_code,
                
                -- 出馬情報
                se.wakuban,
                se.seibetsu_code,
                se.barei,
                se.futan_juryo,
                se.kishu_code,
                se.chokyoshi_code,
                se.blinker_shiyo_kubun,
                se.tozai_shozoku_code,
                
                -- 馬情報
                um.moshoku_code
                
            FROM 
                nvd_ra ra
                INNER JOIN nvd_se se ON (
                    ra.kaisai_nen = se.kaisai_nen 
                    AND ra.kaisai_tsukihi = se.kaisai_tsukihi
                    AND ra.keibajo_code = se.keibajo_code
                    AND ra.race_bango = se.race_bango
                )
                LEFT JOIN nvd_um um ON (
                    se.ketto_toroku_bango = um.ketto_toroku_bango
                )
            
            WHERE 
                ra.kaisai_nen = '2026'
                AND ra.keibajo_code = %s
                AND ra.kaisai_tsukihi >= '0101'
                AND ra.kaisai_tsukihi <= '0131'
                AND se.kakutei_chakujun IS NOT NULL
                AND se.kakutei_chakujun NOT IN ('00', '取消', '除外', '中止', '失格')
                AND se.kakutei_chakujun ~ '^[0-9]+$'
        ),
        past_races AS (
            -- その馬の過去走を全て取得
            SELECT 
                se.ketto_toroku_bango,
                se.kaisai_nen,
                se.kaisai_tsukihi,
                se.keibajo_code,
                se.race_bango,
                
                -- 過去走の結果データ
                se.kakutei_chakujun,
                se.soha_time,
                se.kohan_3f,
                se.kohan_4f,
                se.corner_1,
                se.corner_2,
                se.corner_3,
                se.corner_4,
                se.bataiju,
                
                -- 過去走のレース情報
                ra.kyori AS past_kyori,
                ra.keibajo_code AS past_keibajo,
                ra.track_code AS past_track,
                ra.babajotai_code_shiba AS past_baba_shiba,
                ra.babajotai_code_dirt AS past_baba_dirt,
                
                -- 最新順に番号を付与（1=前走, 2=2走前, ...）
                ROW_NUMBER() OVER (
                    PARTITION BY se.ketto_toroku_bango 
                    ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC, se.race_bango DESC
                ) AS race_order
                
            FROM nvd_se se
            INNER JOIN nvd_ra ra ON (
                se.kaisai_nen = ra.kaisai_nen 
                AND se.kaisai_tsukihi = ra.kaisai_tsukihi
                AND se.keibajo_code = ra.keibajo_code
                AND se.race_bango = ra.race_bango
            )
            INNER JOIN target_race tr ON se.ketto_toroku_bango = tr.ketto_toroku_bango
            
            WHERE 
                -- 当該レースより前のレースのみ
                (se.kaisai_nen || se.kaisai_tsukihi || LPAD(se.race_bango::TEXT, 2, '0')) 
                < (tr.kaisai_nen || tr.kaisai_tsukihi || LPAD(tr.race_bango::TEXT, 2, '0'))
                -- 着順が確定している
                AND se.kakutei_chakujun IS NOT NULL
                AND se.kakutei_chakujun ~ '^[0-9]+$'
        )
        SELECT 
            -- Target variable: 3rd place or better = 1, others = 0
            CASE 
                WHEN tr.kakutei_chakujun ~ '^[0-9]+$' AND tr.kakutei_chakujun::INTEGER <= 3 THEN 1
                ELSE 0
            END AS target,
            
            -- Race identifiers
            tr.kaisai_nen,
            tr.kaisai_tsukihi,
            tr.keibajo_code,
            tr.race_bango,
            tr.ketto_toroku_bango,
            tr.umaban,
            tr.kakutei_chakujun,
            
            -- Race information
            tr.kyori,
            tr.track_code,
            tr.babajotai_code_shiba,
            tr.babajotai_code_dirt,
            tr.tenko_code,
            tr.shusso_tosu,
            tr.grade_code,
            
            -- Entry information
            tr.wakuban,
            tr.seibetsu_code,
            tr.barei,
            tr.futan_juryo,
            tr.kishu_code,
            tr.chokyoshi_code,
            tr.blinker_shiyo_kubun,
            tr.tozai_shozoku_code,
            
            -- Horse information
            tr.moshoku_code,
            
            -- Previous race 1 (Phase 3互換: 4特徴量のみ)
            MAX(CASE WHEN pr.race_order = 1 THEN pr.kakutei_chakujun END) AS prev1_rank,
            MAX(CASE WHEN pr.race_order = 1 THEN pr.soha_time END) AS prev1_time,
            MAX(CASE WHEN pr.race_order = 1 THEN pr.kohan_3f END) AS prev1_last3f,
            MAX(CASE WHEN pr.race_order = 1 THEN pr.bataiju END) AS prev1_weight,
            
            -- Previous race 2
            MAX(CASE WHEN pr.race_order = 2 THEN pr.kakutei_chakujun END) AS prev2_rank,
            MAX(CASE WHEN pr.race_order = 2 THEN pr.soha_time END) AS prev2_time,
            MAX(CASE WHEN pr.race_order = 2 THEN pr.kohan_3f END) AS prev2_last3f,
            MAX(CASE WHEN pr.race_order = 2 THEN pr.bataiju END) AS prev2_weight,
            MAX(CASE WHEN pr.race_order = 2 THEN pr.past_kyori END) AS prev2_kyori,
            MAX(CASE WHEN pr.race_order = 2 THEN pr.past_keibajo END) AS prev2_keibajo,
            
            -- Previous race 3
            MAX(CASE WHEN pr.race_order = 3 THEN pr.kakutei_chakujun END) AS prev3_rank,
            MAX(CASE WHEN pr.race_order = 3 THEN pr.soha_time END) AS prev3_time,
            MAX(CASE WHEN pr.race_order = 3 THEN pr.bataiju END) AS prev3_weight,
            
            -- Previous race 4
            MAX(CASE WHEN pr.race_order = 4 THEN pr.kakutei_chakujun END) AS prev4_rank,
            MAX(CASE WHEN pr.race_order = 4 THEN pr.soha_time END) AS prev4_time,
            
            -- Previous race 5 (Phase 3互換: 1特徴量のみ)
            MAX(CASE WHEN pr.race_order = 5 THEN pr.kakutei_chakujun END) AS prev5_rank
            
        FROM target_race tr
        LEFT JOIN past_races pr ON tr.ketto_toroku_bango = pr.ketto_toroku_bango AND pr.race_order <= 5
        GROUP BY 
            tr.kaisai_nen,
            tr.kaisai_tsukihi,
            tr.keibajo_code,
            tr.race_bango,
            tr.ketto_toroku_bango,
            tr.umaban,
            tr.kakutei_chakujun,
            tr.kyori,
            tr.track_code,
            tr.babajotai_code_shiba,
            tr.babajotai_code_dirt,
            tr.tenko_code,
            tr.shusso_tosu,
            tr.grade_code,
            tr.wakuban,
            tr.seibetsu_code,
            tr.barei,
            tr.futan_juryo,
            tr.kishu_code,
            tr.chokyoshi_code,
            tr.blinker_shiyo_kubun,
            tr.tozai_shozoku_code,
            tr.moshoku_code
        ORDER BY 
            tr.kaisai_tsukihi,
            tr.race_bango,
            tr.umaban
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
               'umaban', 'ketto_toroku_bango', 'target', 'kakutei_chakujun']
    
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

def calculate_hitrate(df_results):
    """的中率のみを計算（回収率は計算しない）"""
    
    summary = []
    
    # 全体
    total_races = len(df_results)
    total_hits = (df_results['target'] == 1).sum()
    hitrate = total_hits / total_races * 100 if total_races > 0 else 0
    
    summary.append({
        'category': '全体',
        'count': total_races,
        'hits': total_hits,
        'hitrate': hitrate
    })
    
    # 単勝（◎本命のみ）
    honmei = df_results[df_results['mark'] == '◎']
    if len(honmei) > 0:
        honmei_hits = (honmei['target'] == 1).sum()
        honmei_hitrate = honmei_hits / len(honmei) * 100
        
        summary.append({
            'category': '単勝（◎本命のみ）',
            'count': len(honmei),
            'hits': honmei_hits,
            'hitrate': honmei_hitrate
        })
    
    # 複勝（◎○▲）
    fukusho_marks = df_results[df_results['mark'].isin(['◎', '○', '▲'])]
    if len(fukusho_marks) > 0:
        fukusho_hits = (fukusho_marks['target'] == 1).sum()
        fukusho_hitrate = fukusho_hits / len(fukusho_marks) * 100
        
        summary.append({
            'category': '複勝（◎○▲）',
            'count': len(fukusho_marks),
            'hits': fukusho_hits,
            'hitrate': fukusho_hitrate
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
                'hitrate': mark_hitrate
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
    
    # 的中率計算
    print(f"📈 的中率計算中...")
    df_summary = calculate_hitrate(df_results)
    df_summary['venue_name'] = venue_name
    df_summary['venue_code'] = venue_code
    
    print(f"✅ シミュレーション完了: {venue_name}")
    
    return df_results, df_summary

def main():
    """メイン処理"""
    
    print("=" * 80)
    print("2026年1月シミュレーション実行 (的中率のみ)")
    print("=" * 80)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象期間: 2026-01-01 ～ 2026-01-31")
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
        output_results = 'simulation_2026_hitrate_results.csv'
        output_summary = 'simulation_2026_hitrate_summary.csv'
        
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
    report.append("2026年1-2月シミュレーション結果レポート (的中率のみ)")
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
                    report.append(f"  単勝◎: {int(row['count']):,}点 / 的中率 {row['hitrate']:.2f}%")
                elif row['category'] == '複勝（◎○▲）':
                    report.append(f"  複勝◎○▲: {int(row['count']):,}点 / 的中率 {row['hitrate']:.2f}%")
            
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
    report.append("注: 回収率の計算は次回対応予定です")
    report.append("=" * 80)
    
    # ファイル出力
    output_txt = 'simulation_2026_hitrate_summary.txt'
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"📄 テキストレポート: {output_txt}")

if __name__ == '__main__':
    main()
