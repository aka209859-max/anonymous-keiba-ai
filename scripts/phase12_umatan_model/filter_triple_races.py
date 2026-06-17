#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: トリプル馬単開催レース抽出スクリプト

南関東4場（大井/浦和/船橋/川崎）+ 門別のデータのみを抽出
"""

import pandas as pd
import numpy as np
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict
import glob

# config.py をインポート
sys.path.append(str(Path(__file__).parent))
from config import TARGET_VENUES, PATHS, LOGGING_CONFIG

# ロギング設定
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    datefmt=LOGGING_CONFIG['date_format']
)


class TripleRaceFilter:
    """トリプル馬単開催レース抽出クラス"""
    
    def __init__(self, input_dir: str, output_dir: str):
        """
        初期化
        
        Args:
            input_dir: 入力ディレクトリ（生データ）
            output_dir: 出力ディレクトリ
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.target_venue_codes = list(TARGET_VENUES.keys())
        
        # 出力ディレクトリ作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"🎯 対象競馬場: {TARGET_VENUES}")
        logging.info(f"📂 入力ディレクトリ: {self.input_dir}")
        logging.info(f"📂 出力ディレクトリ: {self.output_dir}")
    
    def find_csv_files(self, pattern: str = "*.csv") -> List[Path]:
        """
        CSVファイルを検索
        
        Args:
            pattern: ファイルパターン
        
        Returns:
            list: CSVファイルパスのリスト
        """
        csv_files = list(self.input_dir.glob(pattern))
        logging.info(f"📄 発見したCSVファイル数: {len(csv_files)}")
        return csv_files
    
    def load_csv_safely(self, file_path: Path) -> pd.DataFrame:
        """
        CSVファイルを安全に読み込み
        
        Args:
            file_path: CSVファイルパス
        
        Returns:
            pd.DataFrame: 読み込んだデータ
        """
        try:
            # Shift-JIS でトライ
            df = pd.read_csv(file_path, encoding='shift-jis')
            logging.info(f"✅ 読み込み成功 (shift-jis): {file_path.name} ({len(df)}行)")
            return df
        except:
            try:
                # UTF-8 でトライ
                df = pd.read_csv(file_path, encoding='utf-8')
                logging.info(f"✅ 読み込み成功 (utf-8): {file_path.name} ({len(df)}行)")
                return df
            except Exception as e:
                logging.error(f"❌ 読み込み失敗: {file_path.name} - {e}")
                return pd.DataFrame()
    
    def filter_by_venue(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        競馬場コードでフィルタリング
        
        Args:
            df: データフレーム
        
        Returns:
            pd.DataFrame: フィルタ済みデータ
        """
        # 競馬場コードカラムを探す
        venue_col = None
        for col in ['keibajo_code', '競馬場コード', 'venue_code', 'keibajo']:
            if col in df.columns:
                venue_col = col
                break
        
        if venue_col is None:
            logging.warning("⚠️ 競馬場コードカラムが見つかりません。フィルタをスキップします。")
            return df
        
        # 対象競馬場のみ抽出
        before_count = len(df)
        filtered_df = df[df[venue_col].isin(self.target_venue_codes)].copy()
        after_count = len(filtered_df)
        
        logging.info(f"🔍 競馬場フィルタ: {before_count}行 → {after_count}行（{after_count/before_count*100:.1f}%）")
        
        return filtered_df
    
    def add_last3_race_flag(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        最終3Rフラグを追加
        
        Args:
            df: データフレーム
        
        Returns:
            pd.DataFrame: フラグ追加済みデータ
        """
        # レース番号カラムを探す
        race_col = None
        for col in ['race_bango', 'レース番号', 'race_number', 'race_no']:
            if col in df.columns:
                race_col = col
                break
        
        if race_col is None:
            logging.warning("⚠️ レース番号カラムが見つかりません。最終3Rフラグをスキップします。")
            df['is_last_3_race'] = 0
            return df
        
        # 日付ごとのグループで最終3Rを判定
        date_col = None
        for col in ['date', '年月日', 'kaisai_date', 'race_date']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None:
            # 日付カラムがない場合は、レース番号の最大値から3レースを最終3Rとする
            max_race = df[race_col].max()
            df['is_last_3_race'] = (df[race_col] >= max_race - 2).astype(int)
        else:
            # 日付ごとに最終3Rを判定
            df['is_last_3_race'] = 0
            for date in df[date_col].unique():
                date_mask = df[date_col] == date
                max_race = df[date_mask][race_col].max()
                last_3_mask = date_mask & (df[race_col] >= max_race - 2)
                df.loc[last_3_mask, 'is_last_3_race'] = 1
        
        last3_count = df['is_last_3_race'].sum()
        logging.info(f"🎯 最終3Rフラグ追加: {last3_count}行（{last3_count/len(df)*100:.1f}%）")
        
        return df
    
    def process_file(self, file_path: Path, output_name: str = None):
        """
        ファイルを処理
        
        Args:
            file_path: 入力ファイルパス
            output_name: 出力ファイル名（指定しない場合は元ファイル名を使用）
        """
        logging.info(f"\n{'='*80}")
        logging.info(f"📄 処理中: {file_path.name}")
        logging.info(f"{'='*80}")
        
        # データ読み込み
        df = self.load_csv_safely(file_path)
        
        if df.empty:
            logging.warning(f"⚠️ スキップ: {file_path.name}（空のデータフレーム）")
            return
        
        # 競馬場フィルタ
        df = self.filter_by_venue(df)
        
        if df.empty:
            logging.warning(f"⚠️ スキップ: {file_path.name}（フィルタ後にデータなし）")
            return
        
        # 最終3Rフラグ追加
        df = self.add_last3_race_flag(df)
        
        # 保存
        if output_name is None:
            output_name = file_path.name
        
        output_path = self.output_dir / output_name
        
        try:
            df.to_csv(output_path, index=False, encoding='shift-jis')
            logging.info(f"💾 保存成功: {output_path.name} ({len(df)}行)")
        except:
            df.to_csv(output_path, index=False, encoding='utf-8')
            logging.info(f"💾 保存成功 (utf-8): {output_path.name} ({len(df)}行)")
    
    def process_all_files(self):
        """全ファイルを処理"""
        logging.info(f"\n{'='*80}")
        logging.info(f"トリプル馬単開催レース抽出開始")
        logging.info(f"{'='*80}\n")
        
        # CSVファイルを検索
        csv_files = self.find_csv_files()
        
        if not csv_files:
            logging.error("❌ CSVファイルが見つかりません")
            return
        
        # 各ファイルを処理
        for csv_file in csv_files:
            self.process_file(csv_file)
        
        logging.info(f"\n{'='*80}")
        logging.info(f"✅ 全ファイル処理完了")
        logging.info(f"{'='*80}\n")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='トリプル馬単開催レース抽出（南関東4場 + 門別）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デフォルト設定で実行
  python filter_triple_races.py
  
  # カスタムディレクトリ指定
  python filter_triple_races.py --input_dir data/raw --output_dir data/phase12_umatan/raw
        """
    )
    
    parser.add_argument('--input_dir', type=str, default='data/raw',
                       help='入力ディレクトリ（デフォルト: data/raw）')
    parser.add_argument('--output_dir', type=str, default=PATHS['raw_data_dir'],
                       help=f'出力ディレクトリ（デフォルト: {PATHS["raw_data_dir"]}）')
    
    args = parser.parse_args()
    
    # フィルタ実行
    filter_engine = TripleRaceFilter(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    filter_engine.process_all_files()


if __name__ == "__main__":
    main()
