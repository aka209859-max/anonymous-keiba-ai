#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026年1月シミュレーション（的中率のみ）
Phase 3互換 + 競馬場ごとの特徴量完全対応版

各競馬場のモデルから実際の特徴量リストを取得し、
それに完全一致するデータを動的に抽出して予測を実行
"""

import psycopg2
import pandas as pd
import numpy as np
import lightgbm as lgb
import os
import sys
from datetime import datetime

# 自作モジュール
from venue_feature_mapping import load_venue_features, get_venue_name, get_model_path
from dynamic_sql_generator import generate_sql_for_venue_features

# データベース接続情報
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'
}

# 競馬場コードとモデルファイルのマッピング
VENUE_CONFIG = {
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

# シミュレーション期間
START_DATE = '2026-01-01'
END_DATE = '2026-01-31'


def connect_db():
    """データベースに接続"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        sys.exit(1)


def extract_2026_data_for_venue(conn, venue_code, feature_names):
    """
    競馬場の特徴量リストに基づいてデータを抽出
    
    Args:
        conn: データベース接続
        venue_code: 競馬場コード
        feature_names: モデルの特徴量リスト
    
    Returns:
        DataFrame: 抽出データ（特徴量の順序も一致）
    """
    venue_name = get_venue_name(venue_code)
    
    try:
        # SQLクエリを動的生成
        query = generate_sql_for_venue_features(
            feature_names, venue_code, START_DATE, END_DATE
        )
        
        # データ抽出
        df = pd.read_sql_query(query, conn)
        
        if len(df) == 0:
            print(f"  ⚠️  データなし")
            return None
        
        print(f"  データ抽出: {len(df):,}件")
        
        # kakutei_chakujun を保存（結果確認用）
        df_result = df[['kakutei_chakujun']].copy()
        
        # 特徴量のみを抽出し、順序を合わせる
        df_features = df[feature_names].copy()
        
        # 結果を結合
        df_final = pd.concat([df_result, df_features], axis=1)
        
        return df_final
        
    except Exception as e:
        print(f"  ❌ データ抽出エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def preprocess_features(df, feature_names):
    """
    特徴量の前処理
    
    Args:
        df: データフレーム
        feature_names: 特徴量名のリスト
    
    Returns:
        (X, df_id): 特徴量とID情報
    """
    # kakutei_chakujun を保存
    df_id = df[['kakutei_chakujun']].copy()
    
    # 特徴量のみを抽出
    X = df[feature_names].copy()
    
    # 数値型に変換
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    
    # 欠損値を平均値で補完
    X = X.fillna(X.mean())
    
    # 無限大を0に置換
    X = X.replace([np.inf, -np.inf], 0)
    
    return X, df_id


def load_model(model_file):
    """モデルを読み込み"""
    try:
        model = lgb.Booster(model_file=model_file)
        return model
    except Exception as e:
        print(f"  ❌ モデル読み込みエラー: {e}")
        return None


def assign_mark(prob):
    """確率から印を割り当て"""
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
    """的中率を計算"""
    df = df_results.copy()
    
    # kakutei_chakujunを数値に変換
    df['kakutei_chakujun'] = pd.to_numeric(df['kakutei_chakujun'], errors='coerce')
    
    # 3着以内を的中とする
    df['hit'] = (df['kakutei_chakujun'] <= 3).astype(int)
    
    # 全体の的中率
    total_races = len(df)
    total_hits = df['hit'].sum()
    overall_hitrate = total_hits / total_races if total_races > 0 else 0
    
    # カテゴリ別の的中率
    honmei_df = df[df['mark'] == '◎']
    honmei_hitrate = honmei_df['hit'].sum() / len(honmei_df) if len(honmei_df) > 0 else 0
    
    fukusho_df = df[df['mark'].isin(['◎', '○', '▲'])]
    fukusho_hitrate = fukusho_df['hit'].sum() / len(fukusho_df) if len(fukusho_df) > 0 else 0
    
    # 印別の的中率
    mark_stats = {}
    for mark in ['◎', '○', '▲', '△', '×']:
        mark_df = df[df['mark'] == mark]
        mark_count = len(mark_df)
        mark_hits = mark_df['hit'].sum()
        mark_hitrate = mark_hits / mark_count if mark_count > 0 else 0
        mark_stats[mark] = {
            'count': mark_count,
            'hits': mark_hits,
            'hitrate': mark_hitrate
        }
    
    return {
        'total_races': total_races,
        'total_hits': total_hits,
        'overall_hitrate': overall_hitrate,
        'honmei_hitrate': honmei_hitrate,
        'fukusho_hitrate': fukusho_hitrate,
        'mark_stats': mark_stats
    }


def simulate_venue(conn, venue_code):
    """競馬場のシミュレーション実行"""
    venue_name = get_venue_name(venue_code)
    model_file = get_model_path(venue_code)
    
    print(f"\n{'='*80}")
    print(f"Phase: {venue_name} (コード: {venue_code})")
    print(f"{'='*80}")
    
    # モデルファイルの存在確認
    if not os.path.exists(model_file):
        print(f"  ⚠️  モデルファイルが見つかりません: {model_file}")
        return None
    
    # Step 1: モデルから特徴量リストを取得
    try:
        feature_names = load_venue_features(venue_code, model_file)
        print(f"  モデル: {model_file}")
        print(f"  特徴量数: {len(feature_names)}")
    except Exception as e:
        print(f"  ❌ 特徴量リスト取得エラー: {e}")
        return None
    
    # Step 2: データ抽出
    df = extract_2026_data_for_venue(conn, venue_code, feature_names)
    if df is None or len(df) == 0:
        print(f"  ⚠️  データが見つかりませんでした")
        return None
    
    # Step 3: 特徴量前処理
    print(f"  進捗: 特徴量前処理中...")
    X, df_id = preprocess_features(df, feature_names)
    
    # Step 4: モデル読み込み
    print(f"  進捗: モデル読み込み中...")
    model = load_model(model_file)
    if model is None:
        return None
    
    # Step 5: 予測実行
    print(f"  進捗: 予測実行中...")
    try:
        y_pred_proba = model.predict(X)
        df_id['prob'] = y_pred_proba
        df_id['mark'] = df_id['prob'].apply(assign_mark)
    except Exception as e:
        print(f"  ❌ 予測エラー: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Step 6: 的中率計算
    print(f"  進捗: 的中率計算中...")
    stats = calculate_hitrate(df_id)
    
    print(f"\n  ✅ {venue_name} 完了")
    print(f"     レース数: {stats['total_races']:,}件")
    print(f"     全体的中率: {stats['overall_hitrate']*100:.2f}%")
    print(f"     本命的中率: {stats['honmei_hitrate']*100:.2f}%")
    
    return {
        'venue_code': venue_code,
        'venue_name': venue_name,
        'stats': stats,
        'df_results': df_id
    }


def main():
    """メイン処理"""
    print("=" * 80)
    print("2026年1月シミュレーション（的中率のみ）")
    print("Phase 3互換 + 競馬場ごとの特徴量完全対応版")
    print("=" * 80)
    print(f"期間: {START_DATE} 〜 {END_DATE}")
    print(f"対象競馬場: {len(VENUE_CONFIG)}競馬場")
    print("=" * 80)
    
    # データベース接続
    conn = connect_db()
    
    # 各競馬場のシミュレーション実行
    all_results = []
    for venue_code in VENUE_CONFIG.keys():
        result = simulate_venue(conn, venue_code)
        if result:
            all_results.append(result)
    
    # データベース接続を閉じる
    conn.close()
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("シミュレーション完了サマリー")
    print("=" * 80)
    
    for result in all_results:
        stats = result['stats']
        print(f"\n{result['venue_name']} ({result['venue_code']})")
        print(f"  レース数: {stats['total_races']:,}件")
        print(f"  全体的中率: {stats['overall_hitrate']*100:.2f}%")
        print(f"  本命的中率: {stats['honmei_hitrate']*100:.2f}%")
        print(f"  複勝的中率: {stats['fukusho_hitrate']*100:.2f}%")
    
    print("\n" + "=" * 80)
    print("✅ 全競馬場のシミュレーション完了")
    print("=" * 80)


if __name__ == '__main__':
    main()
