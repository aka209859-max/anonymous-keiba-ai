#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
競馬場ごとの特徴量マッピング
analyze_venue_features_detailed.py の出力結果に基づく
"""

import lightgbm as lgb
import os

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


def load_venue_features(venue_code, model_file=None):
    """
    競馬場のモデルファイルから実際の特徴量リストを取得
    
    Args:
        venue_code: 競馬場コード (例: '44')
        model_file: モデルファイルパス（省略時は VENUE_MODELS から取得）
    
    Returns:
        list: 特徴量名のリスト
    """
    if model_file is None:
        if venue_code not in VENUE_MODELS:
            raise ValueError(f"未対応の競馬場コード: {venue_code}")
        model_file = VENUE_MODELS[venue_code]['model']
    
    if not os.path.exists(model_file):
        raise FileNotFoundError(f"モデルファイルが見つかりません: {model_file}")
    
    try:
        model = lgb.Booster(model_file=model_file)
        feature_names = model.feature_name()
        return feature_names
    except Exception as e:
        raise RuntimeError(f"モデル読み込みエラー: {e}")


def get_venue_name(venue_code):
    """競馬場名を取得"""
    return VENUE_MODELS.get(venue_code, {}).get('name', '不明')


def get_model_path(venue_code):
    """モデルファイルパスを取得"""
    return VENUE_MODELS.get(venue_code, {}).get('model')


def categorize_features(feature_names):
    """
    特徴量をカテゴリ別に分類
    
    Returns:
        dict: {
            'id': ID列のリスト,
            'race': レース情報のリスト,
            'entry': 出馬情報のリスト,
            'horse': 馬情報のリスト,
            'prev': 前走データのリスト
        }
    """
    id_features = []
    race_features = []
    entry_features = []
    horse_features = []
    prev_features = []
    
    # ID列の定義
    id_columns = {
        'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
        'race_bango', 'ketto_toroku_bango', 'umaban'
    }
    
    # レース情報の定義
    race_columns = {
        'kyori', 'track_code', 'babajotai_code_shiba', 'babajotai_code_dirt',
        'tenko_code', 'shusso_tosu', 'grade_code'
    }
    
    # 出馬情報の定義
    entry_columns = {
        'wakuban', 'seibetsu_code', 'barei', 'futan_juryo',
        'kishu_code', 'chokyoshi_code', 'blinker_shiyo_kubun', 'tozai_shozoku_code'
    }
    
    # 馬情報の定義
    horse_columns = {'moshoku_code'}
    
    for feature in feature_names:
        if feature in id_columns:
            id_features.append(feature)
        elif feature in race_columns:
            race_features.append(feature)
        elif feature in entry_columns:
            entry_features.append(feature)
        elif feature in horse_columns:
            horse_features.append(feature)
        elif feature.startswith('prev'):
            prev_features.append(feature)
        else:
            # その他（念のため）
            race_features.append(feature)
    
    return {
        'id': id_features,
        'race': race_features,
        'entry': entry_features,
        'horse': horse_features,
        'prev': prev_features
    }


if __name__ == '__main__':
    """テスト実行"""
    print("=" * 80)
    print("競馬場ごとの特徴量マッピング確認")
    print("=" * 80)
    print()
    
    for venue_code in VENUE_MODELS.keys():
        venue_name = get_venue_name(venue_code)
        try:
            features = load_venue_features(venue_code)
            categories = categorize_features(features)
            
            print(f"✅ {venue_name} ({venue_code}): {len(features)}特徴量")
            print(f"   ID列: {len(categories['id'])}個")
            print(f"   レース情報: {len(categories['race'])}個")
            print(f"   出馬情報: {len(categories['entry'])}個")
            print(f"   馬情報: {len(categories['horse'])}個")
            print(f"   前走データ: {len(categories['prev'])}個")
            print()
        except Exception as e:
            print(f"❌ {venue_name} ({venue_code}): {e}")
            print()
