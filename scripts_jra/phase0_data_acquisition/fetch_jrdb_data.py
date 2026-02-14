"""
JRDB データ取得スクリプト (Phase 0)

目的: JRDBから過去15年分の成績・指数データを取得
期間: 2010-01-01 ~ 2024-12-31
取得データ: SED, KYI, BAC, CYB, CHA, SKB, TYB, UKC
保存先: data/jrdb/raw/

必須環境:
- Windows OS (LZH解凍のため)
- Python 3.8+
- JRDB会員登録（過去コメント有プラン推奨）
- 専用ダウンローダー「Ikkatsu」または「GetJRDB」

前提条件:
1. JRDBから15年分のLZHファイルをダウンロード済み（手動または専用ツール使用）
2. ダウンロード先: E:\jrdb_data\lzh\
3. 解凍先: data/jrdb/raw/

実行方法:
    python scripts_jra/phase0_data_acquisition/fetch_jrdb_data.py
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
import glob
import shutil

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/jrdb_download.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class JRDBDataExtractor:
    """
    JRDB LZHファイルの解凍・整理クラス
    """
    
    def __init__(
        self, 
        lzh_source_dir: str = 'E:/jrdb_data/lzh',
        output_dir: str = 'data/jrdb/raw'
    ):
        self.lzh_source_dir = Path(lzh_source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.error_log = []
        
        # ファイル種別ごとの出力先
        self.file_type_dirs = {
            'SED': self.output_dir / 'sed',  # 成績データ
            'KYI': self.output_dir / 'kyi',  # 騎手・調教師データ
            'BAC': self.output_dir / 'bac',  # 馬場データ
            'CYB': self.output_dir / 'cyb',  # 前日情報
            'CHA': self.output_dir / 'cha',  # 調教データ
            'SKB': self.output_dir / 'skb',  # 成績拡張データ
            'TYB': self.output_dir / 'tyb',  # 当日情報
            'UKC': self.output_dir / 'ukc',  # 馬基本データ
        }
        
        for dir_path in self.file_type_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 7-zipの実行パス（環境に応じて変更）
        self.seven_zip_path = r'C:\Program Files\7-Zip\7z.exe'
        
        if not Path(self.seven_zip_path).exists():
            logger.warning(f"7-zip not found at {self.seven_zip_path}")
            logger.warning("Please install 7-zip or update the path")
    
    def extract_lzh_file(self, lzh_path: Path, temp_dir: Path) -> bool:
        """
        LZHファイルを解凍
        
        Args:
            lzh_path: LZHファイルのパス
            temp_dir: 一時解凍先ディレクトリ
        
        Returns:
            成功したらTrue
        """
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 7-zipコマンド実行
            cmd = f'"{self.seven_zip_path}" x "{lzh_path}" -o"{temp_dir}" -y'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                encoding='cp932'
            )
            
            if result.returncode == 0:
                logger.info(f"解凍成功: {lzh_path.name}")
                return True
            else:
                logger.error(f"解凍失敗: {lzh_path.name}")
                logger.error(f"Error: {result.stderr}")
                self.error_log.append({
                    'file': lzh_path.name,
                    'error': result.stderr
                })
                return False
        
        except Exception as e:
            logger.error(f"解凍例外: {lzh_path.name} - {e}")
            self.error_log.append({
                'file': lzh_path.name,
                'error': str(e)
            })
            return False
    
    def organize_extracted_files(self, temp_dir: Path):
        """
        解凍されたファイルを種別ごとに整理
        
        Args:
            temp_dir: 解凍ファイルがある一時ディレクトリ
        """
        extracted_files = list(temp_dir.glob('*.txt'))
        logger.info(f"解凍ファイル数: {len(extracted_files)}")
        
        for file_path in extracted_files:
            file_name = file_path.name
            
            # ファイル種別を判定（先頭3文字）
            if len(file_name) < 3:
                continue
            
            file_type = file_name[:3].upper()
            
            if file_type in self.file_type_dirs:
                # 対応するディレクトリへ移動
                dest_dir = self.file_type_dirs[file_type]
                
                # 年月でサブディレクトリ作成
                # ファイル名形式: SED241231.txt → 2024年12月
                if len(file_name) >= 9:
                    year_str = '20' + file_name[3:5]  # YY → YYYY
                    month_str = file_name[5:7]
                    year_month_dir = dest_dir / f"{year_str}{month_str}"
                    year_month_dir.mkdir(parents=True, exist_ok=True)
                    
                    dest_path = year_month_dir / file_name
                else:
                    dest_path = dest_dir / file_name
                
                # ファイル移動
                shutil.move(str(file_path), str(dest_path))
                logger.debug(f"移動: {file_name} -> {dest_path.parent.name}/")
            else:
                logger.warning(f"未知のファイル種別: {file_name}")
    
    def process_all_lzh_files(self, start_year: int = 2010, end_year: int = 2024):
        """
        指定期間のLZHファイルをすべて処理
        
        Args:
            start_year: 開始年
            end_year: 終了年
        """
        logger.info(f"=== JRDB データ処理開始: {start_year}-{end_year} ===")
        
        if not self.lzh_source_dir.exists():
            logger.error(f"LZHソースディレクトリが存在しません: {self.lzh_source_dir}")
            return
        
        # LZHファイル一覧取得
        lzh_files = list(self.lzh_source_dir.glob('*.lzh'))
        logger.info(f"検出されたLZHファイル数: {len(lzh_files)}")
        
        # 一時解凍ディレクトリ
        temp_dir = Path('data/jrdb/temp_extract')
        
        processed_count = 0
        failed_count = 0
        
        for lzh_file in lzh_files:
            # 一時ディレクトリクリア
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            # 解凍
            if self.extract_lzh_file(lzh_file, temp_dir):
                # ファイル整理
                self.organize_extracted_files(temp_dir)
                processed_count += 1
            else:
                failed_count += 1
            
            # 進捗表示
            if processed_count % 10 == 0:
                logger.info(f"処理進捗: {processed_count}/{len(lzh_files)} 完了")
        
        # 一時ディレクトリ削除
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        logger.info(f"=== 処理完了 ===")
        logger.info(f"成功: {processed_count} / 失敗: {failed_count}")
        
        # エラーログ出力
        if self.error_log:
            logger.warning(f"エラー発生件数: {len(self.error_log)}")
            error_df = pd.DataFrame(self.error_log)
            error_df.to_csv('logs/jrdb_errors.csv', index=False, encoding='utf-8-sig')
            logger.info("エラーログ保存: logs/jrdb_errors.csv")
    
    def verify_data_completeness(self):
        """
        データの完全性チェック
        """
        logger.info("=== データ完全性チェック ===")
        
        for file_type, type_dir in self.file_type_dirs.items():
            file_count = len(list(type_dir.rglob('*.txt')))
            logger.info(f"{file_type}: {file_count} ファイル")
        
        # 推奨ファイル数（15年 × 365日 ≈ 5,500ファイル/種別）
        expected_files = 5500
        
        for file_type, type_dir in self.file_type_dirs.items():
            actual_count = len(list(type_dir.rglob('*.txt')))
            if actual_count < expected_files * 0.8:  # 80%未満なら警告
                logger.warning(
                    f"{file_type}: 期待値 {expected_files} に対し {actual_count} ファイル（不足の可能性）"
                )


class JRDBDataDownloadHelper:
    """
    JRDBデータダウンロード支援クラス
    （手動ダウンロードのガイダンス）
    """
    
    @staticmethod
    def print_download_instructions():
        """
        ダウンロード手順を表示
        """
        instructions = """
========================================
JRDB データダウンロード手順
========================================

【前提条件】
1. JRDB会員登録（推奨プラン: 過去コメント有 3,630円/月）
   → https://www.jrdb.com/

【ダウンロード方法】

■ 方法1: 専用ツール「Ikkatsu」を使用（推奨）
   1. JRDB会員ページからIkkutsuをダウンロード
   2. Ikkutsuを起動し、ログイン
   3. 取得期間を設定: 2010-01-01 ~ 2024-12-31
   4. 取得ファイル種別を選択:
      - SED (成績データ) ✅
      - KYI (騎手・調教師) ✅
      - BAC (馬場) ✅
      - CYB (前日情報) ✅
      - CHA (調教) ✅
      - SKB (成績拡張) ✅
      - TYB (当日) ✅
      - UKC (馬基本) ✅
   5. ダウンロード先: E:\jrdb_data\lzh\
   6. ダウンロード開始（所要時間: 数時間～1日）

■ 方法2: 手動ダウンロード
   1. JRDB会員ページにログイン
   2. 「データダウンロード」→「過去データ」
   3. 年月ごとにLZHファイルをダウンロード
   4. 保存先: E:\jrdb_data\lzh\

【ダウンロード後】
   このスクリプト (fetch_jrdb_data.py) を実行してください。
   LZHファイルを自動解凍・整理します。

========================================
        """
        print(instructions)
        logger.info("ダウンロード手順を表示しました")


def main():
    """
    メイン実行関数
    """
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    logger.info("========================================")
    logger.info("JRDB データ取得スクリプト")
    logger.info("========================================")
    
    # ダウンロード手順表示
    JRDBDataDownloadHelper.print_download_instructions()
    
    # ユーザー確認
    response = input("\nLZHファイルのダウンロードは完了していますか? (y/n): ")
    if response.lower() != 'y':
        logger.info("ダウンロード完了後に再実行してください。")
        return
    
    # データ抽出器初期化
    extractor = JRDBDataExtractor(
        lzh_source_dir='E:/jrdb_data/lzh',
        output_dir='data/jrdb/raw'
    )
    
    # LZHファイル処理実行
    try:
        extractor.process_all_lzh_files(start_year=2010, end_year=2024)
        
        # データ完全性チェック
        extractor.verify_data_completeness()
    
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
    
    logger.info("スクリプト終了")


if __name__ == '__main__':
    main()
