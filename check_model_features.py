#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3モデルファイルから実際の特徴量を抽出
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

print("=" * 80)
print("Phase 3モデルの特徴量調査")
print("=" * 80)
print()

for venue_code, venue_info in VENUE_MODELS.items():
    venue_name = venue_info['name']
    model_path = venue_info['model']
    
    if not os.path.exists(model_path):
        print(f"⚠️  {venue_name} ({venue_code}): モデルファイルが見つかりません - {model_path}")
        continue
    
    try:
        model = lgb.Booster(model_file=model_path)
        feature_names = model.feature_name()
        num_features = len(feature_names)
        
        print(f"✅ {venue_name} ({venue_code}): {num_features}特徴量")
        print(f"   モデル: {model_path}")
        print(f"   特徴量: {', '.join(feature_names)}")
        print()
        
    except Exception as e:
        print(f"❌ {venue_name} ({venue_code}): エラー - {e}")
        print()

print("=" * 80)
