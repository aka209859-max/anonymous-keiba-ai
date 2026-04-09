"""
JRA-VAN Data Lab データ取得スクリプト (Phase 0)

目的: JRA-VAN Data Lab (JV-Link) から過去15年分のレースデータを取得
期間: 2010-01-01 ~ 2024-12-31
取得データ: RACE (RA, SE, HR, H1-H6, O1-O6), BLOD, WF
保存先: data/jravan/raw/

必須環境:
- Windows OS
- Python 3.8+ (32ビット版推奨)
- pywin32
- JV-Link SDK (JRA-VAN Data Lab契約後にインストール)

実行方法:
    python scripts_jra/phase0_data_acquisition/fetch_jravan_data.py
"""

import win32com.client
import time
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/jravan_download.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class JVLinkDownloader:
    """
    JV-Link インターフェースを使用したデータダウンローダー
    """
    
    def __init__(self, output_dir: str = 'data/jravan/raw'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.jv = None
        self.error_log = []
        
        # レコードIDごとの出力先ディレクトリ
        self.record_dirs = {
            'RA': self.output_dir / 'races',
            'SE': self.output_dir / 'entries',
            'HR': self.output_dir / 'results',
            'H1': self.output_dir / 'payouts',
            'H2': self.output_dir / 'payouts',
            'H3': self.output_dir / 'payouts',
            'H4': self.output_dir / 'payouts',
            'H5': self.output_dir / 'payouts',
            'H6': self.output_dir / 'payouts',
            'O1': self.output_dir / 'odds',
            'O2': self.output_dir / 'odds',
            'O3': self.output_dir / 'odds',
            'O4': self.output_dir / 'odds',
            'O5': self.output_dir / 'odds',
            'O6': self.output_dir / 'odds',
            'WF': self.output_dir / 'training',
            'BLOD': self.output_dir / 'pedigree',
        }
        
        for dir_path in self.record_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> bool:
        """
        JV-Linkの初期化
        """
        try:
            logger.info("JV-Link初期化開始...")
            self.jv = win32com.client.Dispatch("JVDTLab.JVLink")
            result = self.jv.JVInit("UNKNOWN")
            
            if result == 0:
                logger.info("JV-Link初期化成功")
                return True
            else:
                logger.error(f"JV-Link初期化失敗: エラーコード {result}")
                return False
        except Exception as e:
            logger.error(f"JV-Link初期化例外: {e}")
            return False
    
    def download_year_data(
        self, 
        year: int, 
        dataspec: str = 'RACE'
    ) -> bool:
        """
        特定年のデータをダウンロード
        
        Args:
            year: 取得年（例: 2010）
            dataspec: データ種別（'RACE', 'BLOD', 'WF'）
        
        Returns:
            成功したらTrue
        """
        from_time = f"{year}0101000000"
        logger.info(f"--- {year}年 {dataspec} データ取得開始 ---")
        
        try:
            # JVOpen: option=3 (セットアップモード)
            res = self.jv.JVOpen(dataspec, from_time, 3, 0, 0, "")
            
            if res < 0:
                logger.error(f"JVOpenエラー: {res}")
                self.error_log.append({
                    'year': year,
                    'dataspec': dataspec,
                    'error': f'JVOpen failed with code {res}'
                })
                return False
            
            total_files = res
            logger.info(f"ダウンロード開始: 総ファイル数 {total_files}")
            
            # ダウンロード進捗監視
            while True:
                status = self.jv.JVStatus()
                
                if status == total_files:
                    logger.info(f"ダウンロード完了: {status}/{total_files}")
                    break
                elif status < 0:
                    logger.error(f"ダウンロードエラー: {status}")
                    self.error_log.append({
                        'year': year,
                        'dataspec': dataspec,
                        'error': f'JVStatus error {status}'
                    })
                    return False
                else:
                    logger.info(f"ダウンロード中: {status}/{total_files} ({status/total_files*100:.1f}%)")
                
                time.sleep(5)  # CPU負荷軽減
            
            # データ読み込み
            logger.info("データ読み込み開始...")
            records_count = self._read_and_save_data(year, dataspec)
            logger.info(f"データ保存完了: {records_count} レコード")
            
            # ストリームを閉じる
            self.jv.JVClose()
            
            return True
        
        except Exception as e:
            logger.error(f"{year}年データ取得例外: {e}")
            self.error_log.append({
                'year': year,
                'dataspec': dataspec,
                'error': str(e)
            })
            return False
    
    def _read_and_save_data(self, year: int, dataspec: str) -> int:
        """
        JVReadでデータを読み込み、ファイルに保存
        
        Returns:
            保存したレコード数
        """
        records_count = 0
        buffer_size = 100000  # 100KB
        
        # 年月日ごとのバッファ
        daily_buffers: Dict[str, Dict[str, List[str]]] = {}
        
        while True:
            try:
                # JVReadでバッファ読み込み
                buff, read_count, file_name = self.jv.JVRead("", buffer_size, "")
                
                if read_count == 0:
                    # 全ファイル読み込み完了
                    break
                elif read_count == -1:
                    # ファイルの切り替わり
                    continue
                elif read_count < 0:
                    logger.warning(f"JVRead警告: {read_count}")
                    continue
                
                # レコードID取得（先頭2文字）
                if len(buff) < 2:
                    continue
                
                record_id = buff[:2]
                
                # 年月日を抽出（位置2-10）
                if len(buff) < 10:
                    continue
                
                race_date = buff[2:10]  # YYYYMMDD
                
                # 年チェック（指定年のみ保存）
                if not race_date.startswith(str(year)):
                    continue
                
                # バッファに追加
                if race_date not in daily_buffers:
                    daily_buffers[race_date] = {}
                
                if record_id not in daily_buffers[race_date]:
                    daily_buffers[race_date][record_id] = []
                
                daily_buffers[race_date][record_id].append(buff)
                records_count += 1
                
                # 1000レコードごとにログ
                if records_count % 1000 == 0:
                    logger.info(f"読み込み中: {records_count} レコード")
            
            except Exception as e:
                logger.error(f"データ読み込み例外: {e}")
                break
        
        # ファイルに書き込み
        logger.info(f"ファイル書き込み開始: {len(daily_buffers)} 日分")
        
        for race_date, records_by_type in daily_buffers.items():
            for record_id, lines in records_by_type.items():
                self._save_records_to_file(race_date, record_id, lines)
        
        return records_count
    
    def _save_records_to_file(
        self, 
        race_date: str, 
        record_id: str, 
        lines: List[str]
    ):
        """
        レコードをファイルに保存
        
        Args:
            race_date: YYYYMMDD形式の日付
            record_id: レコードID（RA, SE等）
            lines: レコード行のリスト
        """
        if record_id not in self.record_dirs:
            logger.warning(f"未知のレコードID: {record_id}")
            return
        
        output_dir = self.record_dirs[record_id]
        
        # 年月でサブディレクトリ作成
        year_month = race_date[:6]  # YYYYMM
        year_month_dir = output_dir / year_month
        year_month_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名
        file_path = year_month_dir / f"{record_id}_{race_date}.txt"
        
        # 追記モードで保存（既存データがあれば追加）
        with open(file_path, 'a', encoding='shift_jis') as f:
            for line in lines:
                f.write(line + '\n')
    
    def download_all_years(
        self, 
        start_year: int = 2010, 
        end_year: int = 2024,
        dataspecs: List[str] = ['RACE', 'BLOD', 'WF']
    ):
        """
        複数年にわたるデータを一括ダウンロード
        
        Args:
            start_year: 開始年
            end_year: 終了年
            dataspecs: 取得するデータ種別のリスト
        """
        logger.info(f"=== データ取得開始: {start_year}-{end_year} ===")
        logger.info(f"データ種別: {dataspecs}")
        
        total_start_time = time.time()
        
        for year in range(start_year, end_year + 1):
            for dataspec in dataspecs:
                success = self.download_year_data(year, dataspec)
                
                if not success:
                    logger.warning(f"{year}年 {dataspec} 取得失敗（続行）")
                
                # サーバー負荷軽減のため待機
                time.sleep(3)
        
        total_elapsed = time.time() - total_start_time
        logger.info(f"=== 全データ取得完了 ===")
        logger.info(f"総所要時間: {total_elapsed/3600:.2f} 時間")
        
        # エラーログ出力
        if self.error_log:
            logger.warning(f"エラー発生件数: {len(self.error_log)}")
            error_df = pd.DataFrame(self.error_log)
            error_df.to_csv('logs/jravan_errors.csv', index=False, encoding='utf-8-sig')
            logger.info("エラーログ保存: logs/jravan_errors.csv")
    
    def close(self):
        """
        JV-Linkクローズ
        """
        if self.jv:
            try:
                self.jv.JVClose()
                logger.info("JV-Linkクローズ完了")
            except Exception as e:
                logger.error(f"JV-Linkクローズ例外: {e}")


def main():
    """
    メイン実行関数
    """
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    logger.info("========================================")
    logger.info("JRA-VAN Data Lab データ取得スクリプト")
    logger.info("========================================")
    
    # ダウンローダー初期化
    downloader = JVLinkDownloader(output_dir='data/jravan/raw')
    
    if not downloader.initialize():
        logger.error("初期化失敗。終了します。")
        return
    
    # データ取得実行
    try:
        downloader.download_all_years(
            start_year=2010,
            end_year=2024,
            dataspecs=['RACE', 'BLOD', 'WF']
        )
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
    finally:
        downloader.close()
    
    logger.info("スクリプト終了")


if __name__ == '__main__':
    main()
