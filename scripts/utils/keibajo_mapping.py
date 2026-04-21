"""
競馬場マッピングテーブル
- 日本語名 → ローマ字名の変換
- 競馬場コード → 名称の変換
"""

# 競馬場コード → 日本語名
KEIBAJO_CODE_TO_NAME = {
    '30': '門別',
    '35': '盛岡',
    '36': '水沢',
    '42': '浦和',
    '43': '船橋',
    '44': '大井',
    '45': '川崎',
    '46': '金沢',
    '47': '笠松',
    '48': '名古屋',
    '50': '園田',
    '51': '姫路',
    '54': '高知',
    '55': '佐賀'
}

# 日本語名 → ローマ字名（モデルファイル用）
KEIBAJO_NAME_TO_ROMAJI = {
    '門別': 'monbetsu',
    '盛岡': 'morioka',
    '水沢': 'mizusawa',
    '浦和': 'urawa',
    '船橋': 'funabashi',
    '大井': 'ooi',
    '川崎': 'kawasaki',
    '金沢': 'kanazawa',
    '笠松': 'kasamatsu',
    '名古屋': 'nagoya',
    '園田': 'sonoda',
    '姫路': 'himeji',
    '高知': 'kochi',
    '佐賀': 'saga'
}

# 競馬場コード → ローマ字名（直接変換用）
KEIBAJO_CODE_TO_ROMAJI = {
    code: KEIBAJO_NAME_TO_ROMAJI[name] 
    for code, name in KEIBAJO_CODE_TO_NAME.items()
}

# 各競馬場のモデル学習期間（モデルファイル名に含まれる）
KEIBAJO_MODEL_YEAR_RANGE = {
    'monbetsu': '2020-2025',
    'morioka': '2020-2025',
    'mizusawa': '2020-2025',
    'urawa': '2020-2025',
    'funabashi': '2020-2025',
    'ooi': '2023-2025',        # 大井のみ2023開始
    'kawasaki': '2020-2025',
    'kanazawa': '2020-2025',
    'kasamatsu': '2020-2025',
    'nagoya': '2022-2025',     # 名古屋のみ2022開始
    'sonoda': '2020-2025',
    'himeji': '2020-2025',
    'kochi': '2020-2025',
    'saga': '2020-2025'
}


def get_keibajo_romaji(keibajo_name_or_code):
    """
    競馬場の日本語名またはコードからローマ字名を取得
    
    Args:
        keibajo_name_or_code: 競馬場の日本語名（例: '佐賀'）またはコード（例: '55'）
    
    Returns:
        str: ローマ字名（例: 'saga'）
    
    Raises:
        ValueError: 該当する競馬場が見つからない場合
    """
    # コードの場合
    if keibajo_name_or_code in KEIBAJO_CODE_TO_ROMAJI:
        return KEIBAJO_CODE_TO_ROMAJI[keibajo_name_or_code]
    
    # 日本語名の場合
    if keibajo_name_or_code in KEIBAJO_NAME_TO_ROMAJI:
        return KEIBAJO_NAME_TO_ROMAJI[keibajo_name_or_code]
    
    raise ValueError(f"未知の競馬場です: {keibajo_name_or_code}")


def get_model_filename(keibajo_name_or_code, model_type):
    """
    競馬場名とモデルタイプから適切なモデルファイル名を生成
    
    Args:
        keibajo_name_or_code: 競馬場の日本語名またはコード
        model_type: 'binary', 'ranking', 'regression'
    
    Returns:
        str: モデルファイル名
    
    Example:
        >>> get_model_filename('佐賀', 'binary')
        'saga_2020-2025_v3_model.txt'
        >>> get_model_filename('55', 'ranking')
        'saga_2020-2025_v3_with_race_id_ranking_model.txt'
    """
    romaji = get_keibajo_romaji(keibajo_name_or_code)
    year_range = KEIBAJO_MODEL_YEAR_RANGE[romaji]
    
    if model_type == 'binary':
        return f"{romaji}_{year_range}_v3_model.txt"
    elif model_type == 'ranking':
        return f"{romaji}_{year_range}_v3_with_race_id_ranking_model.txt"
    elif model_type == 'regression':
        return f"{romaji}_{year_range}_v3_time_regression_model.txt"
    else:
        raise ValueError(f"未知のモデルタイプです: {model_type}")


def extract_keibajo_from_filename(filename):
    """
    ファイル名から競馬場名を抽出
    
    Args:
        filename: ファイル名（例: '佐賀_20260207_features.csv'）
    
    Returns:
        str: 競馬場の日本語名（例: '佐賀'）
    
    Example:
        >>> extract_keibajo_from_filename('佐賀_20260207_features.csv')
        '佐賀'
        >>> extract_keibajo_from_filename('川崎_20260205_raw.csv')
        '川崎'
    """
    import os
    basename = os.path.basename(filename)
    keibajo = basename.split('_')[0]
    
    # 有効な競馬場名か確認
    if keibajo not in KEIBAJO_NAME_TO_ROMAJI:
        raise ValueError(f"ファイル名から競馬場名を抽出できません: {filename}")
    
    return keibajo


if __name__ == "__main__":
    # テスト
    print("=== 競馬場マッピングテスト ===")
    
    # テスト1: 日本語名からローマ字名
    print("\n[テスト1] 日本語名 → ローマ字名")
    print(f"佐賀 → {get_keibajo_romaji('佐賀')}")
    print(f"川崎 → {get_keibajo_romaji('川崎')}")
    
    # テスト2: コードからローマ字名
    print("\n[テスト2] コード → ローマ字名")
    print(f"55 → {get_keibajo_romaji('55')}")
    print(f"45 → {get_keibajo_romaji('45')}")
    
    # テスト3: モデルファイル名生成
    print("\n[テスト3] モデルファイル名生成")
    print(f"佐賀 binary: {get_model_filename('佐賀', 'binary')}")
    print(f"川崎 ranking: {get_model_filename('川崎', 'ranking')}")
    print(f"大井 regression: {get_model_filename('大井', 'regression')}")
    
    # テスト4: ファイル名から競馬場名抽出
    print("\n[テスト4] ファイル名 → 競馬場名")
    print(f"佐賀_20260207_features.csv → {extract_keibajo_from_filename('佐賀_20260207_features.csv')}")
    print(f"川崎_20260205_raw.csv → {extract_keibajo_from_filename('川崎_20260205_raw.csv')}")
    
    # テスト5: 全競馬場のモデルファイル名一覧
    print("\n[テスト5] 全競馬場のモデルファイル名")
    for name in KEIBAJO_NAME_TO_ROMAJI.keys():
        print(f"{name}: {get_model_filename(name, 'binary')}")
