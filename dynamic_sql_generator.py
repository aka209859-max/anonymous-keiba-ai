#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
競馬場ごとの動的SQL生成
各競馬場のモデルに合わせた特徴量を抽出するSQLを生成
"""


def generate_sql_for_venue_features(feature_names, venue_code, start_date, end_date):
    """
    競馬場の特徴量リストに基づいて動的SQLを生成
    
    Args:
        feature_names: モデルの特徴量リスト
        venue_code: 競馬場コード
        start_date: 開始日 (例: '2026-01-01')
        end_date: 終了日 (例: '2026-01-31')
    
    Returns:
        str: SQL文字列
    """
    
    # 特徴量を分類
    id_features = []
    race_features = []
    entry_features = []
    horse_features = []
    prev_features = {}  # {prev番号: [特徴量リスト]}
    
    # ID列の定義
    id_columns = {
        'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 
        'race_bango', 'ketto_toroku_bango', 'umaban'
    }
    
    # 各特徴量を分類
    for feature in feature_names:
        if feature in id_columns:
            id_features.append(feature)
        elif feature.startswith('prev'):
            # prev1_rank → prev=1, field=rank
            parts = feature.split('_', 1)
            if len(parts) == 2:
                prev_num = parts[0].replace('prev', '')
                field = parts[1]
                if prev_num not in prev_features:
                    prev_features[prev_num] = []
                prev_features[prev_num].append(field)
        else:
            # レース情報、出馬情報、馬情報として扱う
            if feature in ['kyori', 'track_code', 'babajotai_code_shiba', 'babajotai_code_dirt',
                          'tenko_code', 'shusso_tosu', 'grade_code']:
                race_features.append(feature)
            elif feature in ['wakuban', 'seibetsu_code', 'barei', 'futan_juryo',
                            'kishu_code', 'chokyoshi_code', 'blinker_shiyo_kubun', 'tozai_shozoku_code']:
                entry_features.append(feature)
            elif feature in ['moshoku_code']:
                horse_features.append(feature)
    
    # SQLのSELECT句を生成
    select_parts = []
    
    # 必須: 結果確認用（モデルには含まれない）
    select_parts.append("tr.kakutei_chakujun")
    
    # ID列
    for feature in ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 
                    'ketto_toroku_bango', 'umaban']:
        if feature in id_features:
            select_parts.append(f"tr.{feature}")
    
    # レース情報
    for feature in race_features:
        select_parts.append(f"tr.{feature}")
    
    # 出馬情報
    for feature in entry_features:
        select_parts.append(f"tr.{feature}")
    
    # 馬情報
    for feature in horse_features:
        select_parts.append(f"tr.{feature}")
    
    # 前走データ
    prev_select_parts = []
    for prev_num in sorted(prev_features.keys()):
        fields = prev_features[prev_num]
        for field in fields:
            # フィールドに応じてマッピング
            if field == 'rank':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.kakutei_chakujun END) AS prev{prev_num}_rank"
                )
            elif field == 'time':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.soha_time END) AS prev{prev_num}_time"
                )
            elif field == 'last3f':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.kohan_3f END) AS prev{prev_num}_last3f"
                )
            elif field == 'last4f':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.kohan_4f END) AS prev{prev_num}_last4f"
                )
            elif field == 'weight':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.bataiju END) AS prev{prev_num}_weight"
                )
            elif field == 'kyori':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.past_kyori END) AS prev{prev_num}_kyori"
                )
            elif field == 'keibajo':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.past_keibajo END) AS prev{prev_num}_keibajo"
                )
            elif field == 'track':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.past_track END) AS prev{prev_num}_track"
                )
            elif field == 'baba_shiba':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.past_baba_shiba END) AS prev{prev_num}_baba_shiba"
                )
            elif field == 'baba_dirt':
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.past_baba_dirt END) AS prev{prev_num}_baba_dirt"
                )
            elif field.startswith('corner'):
                corner_num = field.replace('corner', '')
                prev_select_parts.append(
                    f"MAX(CASE WHEN pr.race_order = {prev_num} THEN pr.corner_{corner_num} END) AS prev{prev_num}_corner{corner_num}"
                )
    
    # 前走データを追加
    select_parts.extend(prev_select_parts)
    
    # SQLクエリを構築
    select_clause = ",\n        ".join(select_parts)
    
    query = f"""
    WITH target_race AS (
        SELECT 
            r.kaisai_nen,
            r.kaisai_tsukihi,
            r.keibajo_code,
            r.race_bango,
            s.ketto_toroku_bango,
            s.umaban,
            s.kakutei_chakujun,
            
            r.kyori,
            r.track_code,
            r.babajotai_code_shiba,
            r.babajotai_code_dirt,
            r.tenko_code,
            r.shusso_tosu,
            r.grade_code,
            
            s.wakuban,
            s.seibetsu_code,
            s.barei,
            s.futan_juryo,
            s.kishu_code,
            s.chokyoshi_code,
            s.blinker_shiyo_kubun,
            s.tozai_shozoku_code,
            
            um.moshoku_code
            
        FROM 
            nvd_ra r
            INNER JOIN nvd_se s ON (
                r.kaisai_nen = s.kaisai_nen 
                AND r.kaisai_tsukihi = s.kaisai_tsukihi
                AND r.keibajo_code = s.keibajo_code
                AND r.race_bango = s.race_bango
            )
            LEFT JOIN nvd_um um ON (
                s.ketto_toroku_bango = um.ketto_toroku_bango
            )
        
        WHERE 
            r.keibajo_code = '{venue_code}'
            AND r.kaisai_nen = '2026'
            AND r.kaisai_tsukihi >= '{start_date.replace('-', '')[-4:]}'
            AND r.kaisai_tsukihi <= '{end_date.replace('-', '')[-4:]}'
            AND s.kakutei_chakujun IS NOT NULL
            AND s.kakutei_chakujun ~ '^[0-9]+$'
    ),
    past_races AS (
        SELECT 
            s.ketto_toroku_bango,
            s.kaisai_nen,
            s.kaisai_tsukihi,
            s.keibajo_code,
            s.race_bango,
            
            s.kakutei_chakujun,
            s.soha_time,
            s.kohan_3f,
            s.kohan_4f,
            s.corner_1,
            s.corner_2,
            s.corner_3,
            s.corner_4,
            s.bataiju,
            
            r.kyori AS past_kyori,
            r.keibajo_code AS past_keibajo,
            r.track_code AS past_track,
            r.babajotai_code_shiba AS past_baba_shiba,
            r.babajotai_code_dirt AS past_baba_dirt,
            
            ROW_NUMBER() OVER (
                PARTITION BY s.ketto_toroku_bango 
                ORDER BY s.kaisai_nen DESC, s.kaisai_tsukihi DESC, s.race_bango DESC
            ) AS race_order
            
        FROM nvd_se s
        INNER JOIN nvd_ra r ON (
            s.kaisai_nen = r.kaisai_nen 
            AND s.kaisai_tsukihi = r.kaisai_tsukihi
            AND s.keibajo_code = r.keibajo_code
            AND s.race_bango = r.race_bango
        )
        INNER JOIN target_race tr ON s.ketto_toroku_bango = tr.ketto_toroku_bango
        
        WHERE 
            (s.kaisai_nen || s.kaisai_tsukihi || LPAD(s.race_bango::TEXT, 2, '0')) 
            < (tr.kaisai_nen || tr.kaisai_tsukihi || LPAD(tr.race_bango::TEXT, 2, '0'))
            AND s.kakutei_chakujun IS NOT NULL
            AND s.kakutei_chakujun ~ '^[0-9]+$'
    )
    SELECT 
        {select_clause}
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
        tr.kaisai_nen,
        tr.kaisai_tsukihi,
        tr.race_bango,
        tr.umaban
    """
    
    return query


if __name__ == '__main__':
    """テスト実行"""
    # テスト用の特徴量リスト（大井 32特徴量）
    test_features = [
        'barei', 'chokyoshi_code', 'futan_juryo', 'kaisai_nen', 'ketto_toroku_bango',
        'kishu_code', 'kyori', 'prev1_last3f', 'prev1_rank', 'prev1_time', 'prev1_weight',
        'prev2_keibajo', 'prev2_kyori', 'prev2_last3f', 'prev2_rank', 'prev2_time', 'prev2_weight',
        'prev3_rank', 'prev3_time', 'prev3_weight',
        'prev4_rank', 'prev4_time',
        'prev5_rank',
        'race_bango', 'seibetsu_code', 'shusso_tosu',
        'track_code', 'umaban', 'babajotai_code_shiba', 'babajotai_code_dirt',
        'tenko_code', 'wakuban'
    ]
    
    sql = generate_sql_for_venue_features(test_features, '44', '2026-01-01', '2026-01-31')
    print("=" * 100)
    print("動的SQL生成テスト（大井 32特徴量）")
    print("=" * 100)
    print(sql)
