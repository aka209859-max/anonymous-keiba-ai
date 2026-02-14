#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_features_safe.py
Phase 1: 特徴量作成スクリプト（文字化け対策版）

競馬場コードと日付から自動的にファイルパスを生成
"""

import sys
import os

# 競馬場コードから日本語名への変換
KEIBAJO_MAP = {
    '30': '門別', '35': '盛岡', '36': '水沢', '42': '浦和',
    '43': '船橋', '44': '大井', '45': '川崎', '46': '金沢',
    '47': '笠松', '48': '名古屋', '50': '園田', '51': '姫路',
    '54': '高知', '55': '佐賀'
}

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: prepare_features_safe.py [KEIBAJO_CODE] [YEAR] [MONTH] [DATE_SHORT]")
        print("Example: prepare_features_safe.py 43 2026 02 20260213")
        sys.exit(1)
    
    keibajo_code = sys.argv[1]
    year = sys.argv[2]
    month = sys.argv[3]
    date_short = sys.argv[4]
    
    # 競馬場名を取得
    keibajo_name = KEIBAJO_MAP.get(keibajo_code)
    if not keibajo_name:
        print(f"❌ エラー: 無効な競馬場コード {keibajo_code}")
        sys.exit(1)
    
    # ファイルパスを生成
    input_csv = f"data/raw/{year}/{month}/{keibajo_name}_{date_short}_raw.csv"
    output_csv = f"data/features/{year}/{month}/{keibajo_name}_{date_short}_features.csv"
    
    # 既存の prepare_features.py を呼び出し
    import subprocess
    cmd = [sys.executable, "scripts/phase1_feature_engineering/prepare_features.py", input_csv, "--output", output_csv]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
