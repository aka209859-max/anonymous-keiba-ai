"""
Phase 0 データ取得マスタースクリプト

目的: JRA-VANとJRDBのデータ取得を並行実行
機能:
  1. JRA-VAN: 15年分のレースデータ取得（約30時間）
  2. JRDB: LZHファイル解凍・整理（数時間）
  3. 進捗監視とログ出力

実行方法:
    python scripts_jra/phase0_data_acquisition/run_parallel_download.py
"""

import subprocess
import threading
import time
import logging
from pathlib import Path
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/parallel_download.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ParallelDownloader:
    """
    JRA-VANとJRDBを並行ダウンロードするクラス
    """
    
    def __init__(self):
        self.jravan_process = None
        self.jrdb_process = None
        self.jravan_completed = False
        self.jrdb_completed = False
        self.start_time = None
    
    def run_jravan_download(self):
        """
        JRA-VANダウンロードをサブプロセスで実行
        """
        logger.info("[JRA-VAN] ダウンロード開始")
        
        try:
            self.jravan_process = subprocess.run(
                ['python', 'scripts_jra/phase0_data_acquisition/fetch_jravan_data.py'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if self.jravan_process.returncode == 0:
                logger.info("[JRA-VAN] ダウンロード完了")
                self.jravan_completed = True
            else:
                logger.error(f"[JRA-VAN] エラー終了: {self.jravan_process.stderr}")
        
        except Exception as e:
            logger.error(f"[JRA-VAN] 例外発生: {e}")
    
    def run_jrdb_download(self):
        """
        JRDBダウンロードをサブプロセスで実行
        """
        logger.info("[JRDB] データ処理開始")
        
        try:
            self.jrdb_process = subprocess.run(
                ['python', 'scripts_jra/phase0_data_acquisition/fetch_jrdb_data.py'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if self.jrdb_process.returncode == 0:
                logger.info("[JRDB] データ処理完了")
                self.jrdb_completed = True
            else:
                logger.error(f"[JRDB] エラー終了: {self.jrdb_process.stderr}")
        
        except Exception as e:
            logger.error(f"[JRDB] 例外発生: {e}")
    
    def monitor_progress(self):
        """
        進捗を監視してログ出力
        """
        while not (self.jravan_completed and self.jrdb_completed):
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            
            status = {
                'JRA-VAN': '完了' if self.jravan_completed else '実行中',
                'JRDB': '完了' if self.jrdb_completed else '実行中'
            }
            
            logger.info(
                f"[進捗] 経過時間: {hours}時間{minutes}分 | "
                f"JRA-VAN: {status['JRA-VAN']} | JRDB: {status['JRDB']}"
            )
            
            time.sleep(300)  # 5分ごとに進捗表示
    
    def run_parallel(self):
        """
        並行ダウンロードを実行
        """
        logger.info("========================================")
        logger.info("Phase 0 並行データ取得開始")
        logger.info("========================================")
        
        self.start_time = time.time()
        
        # スレッド作成
        jravan_thread = threading.Thread(target=self.run_jravan_download)
        jrdb_thread = threading.Thread(target=self.run_jrdb_download)
        monitor_thread = threading.Thread(target=self.monitor_progress)
        
        # スレッド開始
        jravan_thread.start()
        jrdb_thread.start()
        monitor_thread.start()
        
        # 完了待機
        jravan_thread.join()
        jrdb_thread.join()
        
        # 完了フラグ設定（監視スレッド終了）
        self.jravan_completed = True
        self.jrdb_completed = True
        monitor_thread.join()
        
        # 結果サマリー
        elapsed = time.time() - self.start_time
        logger.info("========================================")
        logger.info("Phase 0 並行データ取得完了")
        logger.info(f"総所要時間: {elapsed/3600:.2f} 時間")
        logger.info(f"JRA-VAN: {'成功' if self.jravan_completed else '失敗'}")
        logger.info(f"JRDB: {'成功' if self.jrdb_completed else '失敗'}")
        logger.info("========================================")


def main():
    """
    メイン実行
    """
    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)
    
    # 実行確認
    print("========================================")
    print("Phase 0 並行データ取得")
    print("========================================")
    print("予想所要時間: JRA-VAN 約30時間 + JRDB 数時間")
    print("※ 両者は並行実行されます")
    print()
    
    response = input("実行しますか? (y/n): ")
    if response.lower() != 'y':
        print("キャンセルしました。")
        return
    
    # 並行ダウンロード実行
    downloader = ParallelDownloader()
    
    try:
        downloader.run_parallel()
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")


if __name__ == '__main__':
    main()
