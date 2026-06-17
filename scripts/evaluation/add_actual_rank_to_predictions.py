# 📊 過去データの取得方法ガイド

## 🎯 過去データとは？

`analyze_rank_fukusho_rate.py` スクリプトが分析する「過去データ」とは：

**Phase 5のアンサンブル予測結果CSV** = 予測結果 + 実際の着順

---

## 📂 必要なファイル構成

```
E:\anonymous-keiba-ai\
└─ data\
   └─ predictions\
      └─ phase5\
         ├─ 川崎_20260203_ensemble.csv
         ├─ 大井_20260204_ensemble.csv
         ├─ 姫路_20260205_ensemble.csv
         ├─ 笠松_20260207_ensemble.csv
         ├─ 高知_20260208_ensemble.csv
         └─ 佐賀_20260209_ensemble.csv
```

---

## 🔄 過去データの作成方法

### ステップ1: 過去の予測を実行

過去の日付で `run_all_FINAL.bat` を実行します。

```cmd
cd E:\anonymous-keiba-ai

REM 2026年2月のデータを作成
run_all_FINAL.bat 45 2026-02-03  REM 川崎 2/3
run_all_FINAL.bat 44 2026-02-04  REM 大井 2/4
run_all_FINAL.bat 51 2026-02-05  REM 姫路 2/5
run_all_FINAL.bat 47 2026-02-07  REM 笠松 2/7
run_all_FINAL.bat 54 2026-02-08  REM 高知 2/8
run_all_FINAL.bat 55 2026-02-09  REM 佐賀 2/9
```

これで以下が生成されます：
```
data\predictions\phase5\temp_20260203_ensemble.csv
data\predictions\phase5\temp_20260204_ensemble.csv
data\predictions\phase5\temp_20260205_ensemble.csv
...
```

---

### ステップ2: 実際の着順を追加

**問題**: `run_all_FINAL.bat` で生成されるCSVには **`actual_rank` カラムがありません**。

**解決策**: 以下のいずれかの方法で着順を追加する必要があります。

---

## 🔧 方法1: データベースから着順を取得（推奨）

データベースに実際の結果が保存されている場合：

<function_calls>
<invoke name="Write">
<parameter name="content">#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_actual_rank_to_predictions.py
予測CSVに実際の着順を追加

使用法:
    python add_actual_rank_to_predictions.py --input data/predictions/phase5/temp_20260203_ensemble.csv --date 2026-02-03 --venue 45
"""

import argparse
import pandas as pd
import mysql.connector
from pathlib import Path


def get_actual_ranks(date, venue_code):
    """
    MySQLデータベースから実際の着順を取得
    
    Args:
        date: 開催日 (YYYY-MM-DD)
        venue_code: 競馬場コード (例: 45)
    
    Returns:
        DataFrame: race_id, horse_no, actual_rank
    """
    
    # データベース接続
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='your_password',  # 実際のパスワードに変更
        database='keiba_db'
    )
    
    # 日付をYYYYMMDD形式に変換
    date_str = date.replace('-', '')
    year = date[:4]
    month_day = date[5:].replace('-', '')
    
    # SQLクエリ
    query = """
    SELECT 
        CONCAT(kaisai_year, kaisai_monthday, keibajo_code, race_bango) as race_id,
        umaban as horse_no,
        kakutei_chakujun as actual_rank
    FROM 
        n_uma_race
    WHERE 
        kaisai_year = %s
        AND kaisai_monthday = %s
        AND keibajo_code = %s
        AND kakutei_chakujun IS NOT NULL
    ORDER BY 
        race_bango, umaban
    """
    
    df = pd.read_sql(query, conn, params=(year, month_day, venue_code))
    conn.close()
    
    return df


def add_actual_rank_to_csv(input_csv, date, venue_code, output_csv=None):
    """
    予測CSVに実際の着順を追加
    """
    
    # 予測データ読み込み
    try:
        df_pred = pd.read_csv(input_csv, encoding='shift-jis')
    except UnicodeDecodeError:
        df_pred = pd.read_csv(input_csv, encoding='utf-8')
    
    print(f"📄 予測データ読み込み: {len(df_pred)}件")
    
    # 実際の着順を取得
    df_actual = get_actual_ranks(date, venue_code)
    print(f"🏁 実際の着順取得: {len(df_actual)}件")
    
    if len(df_actual) == 0:
        print("⚠️  着順データが見つかりません")
        return
    
    # マージ
    df_merged = pd.merge(
        df_pred,
        df_actual,
        on=['race_id', 'horse_no'],
        how='left'
    )
    
    # 出力ファイル名
    if output_csv is None:
        output_csv = input_csv.replace('.csv', '_with_actual.csv')
    
    # 保存
    df_merged.to_csv(output_csv, index=False, encoding='shift-jis')
    print(f"✅ 保存完了: {output_csv}")
    print(f"   - 着順データ追加: {df_merged['actual_rank'].notna().sum()}件")


def main():
    parser = argparse.ArgumentParser(description='予測CSVに実際の着順を追加')
    parser.add_argument('--input', required=True, help='入力CSV')
    parser.add_argument('--date', required=True, help='開催日 (YYYY-MM-DD)')
    parser.add_argument('--venue', required=True, help='競馬場コード (例: 45)')
    parser.add_argument('--output', help='出力CSV（省略時は_with_actual.csv）')
    
    args = parser.parse_args()
    
    add_actual_rank_to_csv(
        input_csv=args.input,
        date=args.date,
        venue_code=args.venue,
        output_csv=args.output
    )


if __name__ == '__main__':
    main()
