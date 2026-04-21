#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: 2着以内特化特徴量エンジニアリング

新規特徴量:
- recent_1st_rate: 過去10走の1着率
- recent_2nd_rate: 過去10走の2着率
- agari_3f_rank: 上がり3F順位
- final_corner_rank: 最終コーナー通過順位
- jockey_1st_rate: 騎手の1着率
- jockey_2nd_rate: 騎手の2着率
"""

import pandas as pd
import numpy as np
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

# config.py をインポート
sys.path.append(str(Path(__file__).parent))
from config import TARGET_VENUES, FEATURE_COLUMNS, TARGET_COLUMNS, PATHS, LOGGING_CONFIG, MISC

# ロギング設定
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    datefmt=LOGGING_CONFIG['date_format']
)

# 乱数シード設定
np.random.seed(MISC['random_seed'])


class Top2FeatureEngineer:
    """2着以内特化特徴量エンジニアリング"""
    
    def __init__(self, input_dir: str, output_dir: str):
        """
        初期化
        
        Args:
            input_dir: 入力ディレクトリ
            output_dir: 出力ディレクトリ
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # 出力ディレクトリ作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"📂 入力ディレクトリ: {self.input_dir}")
        logging.info(f"📂 出力ディレクトリ: {self.output_dir}")
    
    def load_race_data(self) -> pd.DataFrame:
        """
        レースデータを読み込み
        
        Returns:
            pd.DataFrame: レースデータ
        """
        race_files = list(self.input_dir.glob("*race*.csv"))
        
        if not race_files:
            logging.error("❌ レースデータが見つかりません")
            return pd.DataFrame()
        
        dfs = []
        for file in race_files:
            try:
                df = pd.read_csv(file, encoding='shift-jis')
                dfs.append(df)
                logging.info(f"✅ 読み込み: {file.name} ({len(df)}行)")
            except:
                try:
                    df = pd.read_csv(file, encoding='utf-8')
                    dfs.append(df)
                    logging.info(f"✅ 読み込み (utf-8): {file.name} ({len(df)}行)")
                except Exception as e:
                    logging.warning(f"⚠️ スキップ: {file.name} - {e}")
        
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            logging.info(f"📊 統合後: {len(combined_df)}行")
            return combined_df
        else:
            return pd.DataFrame()
    
    def calculate_recent_finish_rates(self, df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """
        過去N走の1着率・2着率を計算
        
        Args:
            df: データフレーム
            window: 過去何走を見るか
        
        Returns:
            pd.DataFrame: 特徴量追加済みデータ
        """
        logging.info(f"🔄 過去{window}走の着順率を計算中...")
        
        # 必要なカラムの存在確認
        required_cols = ['horse_id', 'date', 'finish_position']
        if not all(col in df.columns for col in required_cols):
            logging.warning(f"⚠️ 必要なカラムが不足: {required_cols}")
            df['recent_1st_rate'] = 0.0
            df['recent_2nd_rate'] = 0.0
            df['recent_top2_rate'] = 0.0
            df['recent_1st_count'] = 0
            df['recent_2nd_count'] = 0
            return df
        
        # 日付でソート
        df = df.sort_values(['horse_id', 'date']).reset_index(drop=True)
        
        # 着順フラグ作成
        df['is_1st'] = (df['finish_position'] == 1).astype(int)
        df['is_2nd'] = (df['finish_position'] == 2).astype(int)
        df['is_top2'] = (df['finish_position'] <= 2).astype(int)
        
        # ローリング計算
        df['recent_1st_rate'] = df.groupby('horse_id')['is_1st'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
        )
        df['recent_2nd_rate'] = df.groupby('horse_id')['is_2nd'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
        )
        df['recent_top2_rate'] = df.groupby('horse_id')['is_top2'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean().shift(1).fillna(0)
        )
        df['recent_1st_count'] = df.groupby('horse_id')['is_1st'].transform(
            lambda x: x.rolling(window=window, min_periods=1).sum().shift(1).fillna(0)
        ).astype(int)
        df['recent_2nd_count'] = df.groupby('horse_id')['is_2nd'].transform(
            lambda x: x.rolling(window=window, min_periods=1).sum().shift(1).fillna(0)
        ).astype(int)
        
        logging.info(f"✅ 過去{window}走の着順率計算完了")
        
        return df
    
    def add_agari_3f_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        上がり3F特徴量を追加
        
        Args:
            df: データフレーム
        
        Returns:
            pd.DataFrame: 特徴量追加済みデータ
        """
        logging.info(f"🔄 上がり3F特徴量を追加中...")
        
        # 上がり3Fカラムを探す
        agari_col = None
        for col in ['agari_3f', '上がり3F', 'last_3f', 'agari3f']:
            if col in df.columns:
                agari_col = col
                break
        
        if agari_col is None:
            logging.warning(f"⚠️ 上がり3Fカラムが見つかりません")
            df['agari_3f_time'] = 0.0
            df['agari_3f_rank'] = 0
            return df
        
        # 上がり3F時計
        df['agari_3f_time'] = df[agari_col].fillna(999.9)
        
        # レースごとに上がり3F順位を計算
        if 'race_id' in df.columns:
            df['agari_3f_rank'] = df.groupby('race_id')['agari_3f_time'].rank(method='min').fillna(99).astype(int)
        else:
            df['agari_3f_rank'] = 0
        
        logging.info(f"✅ 上がり3F特徴量追加完了")
        
        return df
    
    def add_corner_rank_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        最終コーナー通過順位を追加
        
        Args:
            df: データフレーム
        
        Returns:
            pd.DataFrame: 特徴量追加済みデータ
        """
        logging.info(f"🔄 最終コーナー通過順位を追加中...")
        
        # コーナー順位カラムを探す
        corner_col = None
        for col in ['corner_rank_4', '4コーナー', 'final_corner', 'corner4']:
            if col in df.columns:
                corner_col = col
                break
        
        if corner_col is None:
            logging.warning(f"⚠️ 最終コーナー順位カラムが見つかりません")
            df['final_corner_rank'] = 0
            return df
        
        df['final_corner_rank'] = df[corner_col].fillna(99).astype(int)
        
        logging.info(f"✅ 最終コーナー通過順位追加完了")
        
        return df
    
    def add_jockey_trainer_rates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        騎手・調教師の1着率・2着率を追加
        
        Args:
            df: データフレーム
        
        Returns:
            pd.DataFrame: 特徴量追加済みデータ
        """
        logging.info(f"🔄 騎手・調教師の着順率を計算中...")
        
        # 騎手IDカラムを探す
        jockey_col = None
        for col in ['jockey_id', '騎手ID', 'kishu_id']:
            if col in df.columns:
                jockey_col = col
                break
        
        # 調教師IDカラムを探す
        trainer_col = None
        for col in ['trainer_id', '調教師ID', 'chokyoshi_id']:
            if col in df.columns:
                trainer_col = col
                break
        
        if 'is_1st' not in df.columns:
            df['is_1st'] = (df.get('finish_position', 99) == 1).astype(int)
        if 'is_2nd' not in df.columns:
            df['is_2nd'] = (df.get('finish_position', 99) == 2).astype(int)
        if 'is_top2' not in df.columns:
            df['is_top2'] = (df.get('finish_position', 99) <= 2).astype(int)
        
        # 騎手の成績
        if jockey_col:
            jockey_stats = df.groupby(jockey_col).agg({
                'is_1st': 'mean',
                'is_2nd': 'mean',
                'is_top2': 'mean'
            }).reset_index()
            jockey_stats.columns = [jockey_col, 'jockey_1st_rate', 'jockey_2nd_rate', 'jockey_top2_rate']
            df = df.merge(jockey_stats, on=jockey_col, how='left')
            df['jockey_1st_rate'] = df['jockey_1st_rate'].fillna(0.1)
            df['jockey_2nd_rate'] = df['jockey_2nd_rate'].fillna(0.1)
            df['jockey_top2_rate'] = df['jockey_top2_rate'].fillna(0.2)
        else:
            df['jockey_1st_rate'] = 0.1
            df['jockey_2nd_rate'] = 0.1
            df['jockey_top2_rate'] = 0.2
        
        # 調教師の成績
        if trainer_col:
            trainer_stats = df.groupby(trainer_col).agg({
                'is_1st': 'mean',
                'is_2nd': 'mean'
            }).reset_index()
            trainer_stats.columns = [trainer_col, 'trainer_1st_rate', 'trainer_2nd_rate']
            df = df.merge(trainer_stats, on=trainer_col, how='left')
            df['trainer_1st_rate'] = df['trainer_1st_rate'].fillna(0.1)
            df['trainer_2nd_rate'] = df['trainer_2nd_rate'].fillna(0.1)
        else:
            df['trainer_1st_rate'] = 0.1
            df['trainer_2nd_rate'] = 0.1
        
        logging.info(f"✅ 騎手・調教師の着順率計算完了")
        
        return df
    
    def add_class_race_rates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        クラス別1着率・2着率を追加
        
        Args:
            df: データフレーム
        
        Returns:
            pd.DataFrame: 特徴量追加済みデータ
        """
        logging.info(f"🔄 クラス別着順率を計算中...")
        
        class_col = None
        for col in ['class_code', 'クラスコード', 'grade_code']:
            if col in df.columns:
                class_col = col
                break
        
        if class_col is None:
            logging.warning(f"⚠️ クラスコードカラムが見つかりません")
            df['race_class_1st_rate'] = 0.1
            df['race_class_2nd_rate'] = 0.1
            return df
        
        if 'is_1st' not in df.columns:
            df['is_1st'] = (df.get('finish_position', 99) == 1).astype(int)
        if 'is_2nd' not in df.columns:
            df['is_2nd'] = (df.get('finish_position', 99) == 2).astype(int)
        
        class_stats = df.groupby(class_col).agg({
            'is_1st': 'mean',
            'is_2nd': 'mean'
        }).reset_index()
        class_stats.columns = [class_col, 'race_class_1st_rate', 'race_class_2nd_rate']
        
        df = df.merge(class_stats, on=class_col, how='left')
        df['race_class_1st_rate'] = df['race_class_1st_rate'].fillna(0.1)
        df['race_class_2nd_rate'] = df['race_class_2nd_rate'].fillna(0.1)
        
        logging.info(f"✅ クラス別着順率計算完了")
        
        return df
    
    def generate_all_features(self) -> pd.DataFrame:
        """
        全特徴量を生成
        
        Returns:
            pd.DataFrame: 特徴量生成済みデータ
        """
        logging.info(f"\n{'='*80}")
        logging.info(f"2着以内特化特徴量生成開始")
        logging.info(f"{'='*80}\n")
        
        # レースデータ読み込み
        df = self.load_race_data()
        
        if df.empty:
            logging.error("❌ データが空です")
            return df
        
        # 各特徴量を順次追加
        df = self.calculate_recent_finish_rates(df, window=10)
        df = self.add_agari_3f_features(df)
        df = self.add_corner_rank_features(df)
        df = self.add_jockey_trainer_rates(df)
        df = self.add_class_race_rates(df)
        
        # 欠損値処理
        df = df.fillna(0)
        
        logging.info(f"\n{'='*80}")
        logging.info(f"✅ 特徴量生成完了: {len(df)}行 × {len(df.columns)}列")
        logging.info(f"{'='*80}\n")
        
        return df
    
    def save_features(self, df: pd.DataFrame, filename: str = "features_top2.csv"):
        """
        特徴量を保存
        
        Args:
            df: データフレーム
            filename: ファイル名
        """
        output_path = self.output_dir / filename
        
        try:
            df.to_csv(output_path, index=False, encoding='shift-jis')
            logging.info(f"💾 保存成功: {output_path} ({len(df)}行)")
        except:
            df.to_csv(output_path, index=False, encoding='utf-8')
            logging.info(f"💾 保存成功 (utf-8): {output_path} ({len(df)}行)")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='2着以内特化特徴量エンジニアリング',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--input_dir', type=str, default=PATHS['raw_data_dir'],
                       help=f'入力ディレクトリ（デフォルト: {PATHS["raw_data_dir"]}）')
    parser.add_argument('--output_dir', type=str, default=PATHS['features_dir'],
                       help=f'出力ディレクトリ（デフォルト: {PATHS["features_dir"]}）')
    
    args = parser.parse_args()
    
    # 特徴量生成実行
    engineer = Top2FeatureEngineer(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    features_df = engineer.generate_all_features()
    
    if not features_df.empty:
        engineer.save_features(features_df)


if __name__ == "__main__":
    main()
