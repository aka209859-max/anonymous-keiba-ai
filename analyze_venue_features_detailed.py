#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3モデルの特徴量を完全分析
各競馬場のモデルから特徴量リストを抽出し、差異を明確化
"""

import lightgbm as lgb
import os
from collections import defaultdict

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

print("=" * 100)
print("Phase 3モデルの特徴量完全分析")
print("=" * 100)
print()

# 各競馬場の特徴量を収集
venue_features = {}
all_features = set()

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
        
        venue_features[venue_code] = {
            'name': venue_name,
            'features': feature_names,
            'count': num_features,
            'model': model_path
        }
        
        all_features.update(feature_names)
        
        print(f"✅ {venue_name} ({venue_code}): {num_features}特徴量")
        
    except Exception as e:
        print(f"❌ {venue_name} ({venue_code}): エラー - {e}")

print()
print("=" * 100)
print("特徴量数サマリー")
print("=" * 100)
print()

# 特徴量数でグループ化
feature_count_groups = defaultdict(list)
for venue_code, info in venue_features.items():
    feature_count_groups[info['count']].append((venue_code, info['name']))

for count in sorted(feature_count_groups.keys()):
    venues = feature_count_groups[count]
    print(f"{count}特徴量: {', '.join([f'{name}({code})' for code, name in venues])}")

print()
print("=" * 100)
print("特徴量の詳細比較")
print("=" * 100)
print()

# 最も一般的な特徴量数を基準として選択
most_common_count = max(feature_count_groups.keys(), key=lambda k: len(feature_count_groups[k]))
reference_venue_code = feature_count_groups[most_common_count][0][0]
reference_features = set(venue_features[reference_venue_code]['features'])

print(f"基準モデル: {venue_features[reference_venue_code]['name']} ({most_common_count}特徴量)")
print()

# 各競馬場と基準モデルの差異を比較
for venue_code, info in sorted(venue_features.items(), key=lambda x: x[1]['count']):
    venue_name = info['name']
    venue_feature_set = set(info['features'])
    count = info['count']
    
    if venue_code == reference_venue_code:
        print(f"🔵 {venue_name} ({venue_code}): {count}特徴量 [基準モデル]")
        print(f"   特徴量リスト: {', '.join(sorted(info['features']))}")
        print()
        continue
    
    # 差分を計算
    extra_features = venue_feature_set - reference_features
    missing_features = reference_features - venue_feature_set
    
    if extra_features or missing_features:
        print(f"🔴 {venue_name} ({venue_code}): {count}特徴量 [差異あり]")
        
        if extra_features:
            print(f"   追加の特徴量 (+{len(extra_features)}): {', '.join(sorted(extra_features))}")
        
        if missing_features:
            print(f"   欠落の特徴量 (-{len(missing_features)}): {', '.join(sorted(missing_features))}")
        
        print()
    else:
        print(f"🟢 {venue_name} ({venue_code}): {count}特徴量 [基準と一致]")
        print()

print("=" * 100)
print("全特徴量リスト（ユニーク）")
print("=" * 100)
print()
print(f"全競馬場で使用されている特徴量の総数（ユニーク）: {len(all_features)}")
print()
print("特徴量リスト:")
for i, feature in enumerate(sorted(all_features), 1):
    print(f"  {i:2d}. {feature}")

print()
print("=" * 100)
print("結論")
print("=" * 100)
print()

# 特徴量数が異なる競馬場があるかチェック
unique_counts = len(feature_count_groups)
if unique_counts == 1:
    print("✅ すべての競馬場で同じ特徴量数が使用されています。")
    print(f"   共通特徴量数: {list(feature_count_groups.keys())[0]}")
else:
    print("⚠️  競馬場ごとに異なる特徴量数が使用されています。")
    print(f"   パターン数: {unique_counts}")
    print()
    print("【原因】")
    print("  Phase 3学習時、各競馬場ごとに独立してBorutaによる特徴量選択を実行したため、")
    print("  競馬場ごとに異なる特徴量セットが選択されました。")
    print()
    print("【対策】")
    print("  Option 1: 各競馬場のモデルに合わせて、予測データの特徴量を個別に調整")
    print("  Option 2: 全競馬場で共通の特徴量セットを使用してモデルを再学習")
    print("  Option 3: 最小公倍数的な特徴量セット（全モデルが使用している特徴量のみ）を使用")

print()
print("=" * 100)
