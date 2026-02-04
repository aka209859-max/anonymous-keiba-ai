#!/usr/bin/env python3
"""
全15競馬場の学習データ抽出・学習を一括実行するスクリプト
各競馬場ごとに実行して、進捗とエラーを記録する
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# 競馬場別の設定
VENUE_CONFIG = {
    # コード: (開始年, 終了年, 名前, データ件数目安)
    '44': ('2023', '2025', '大井', '27K'),       # 改修工事: 2023-2025
    '48': ('2022', '2025', '名古屋', '40K'),     # 改修工事: 2022-2025
    '43': ('2020', '2025', '船橋', '44K'),
    '45': ('2020', '2025', '川崎', '50K'),
    '42': ('2020', '2025', '浦和', '43K'),
    '50': ('2020', '2025', '園田', '60K'),
    '47': ('2020', '2025', '笠松', '35K'),
    '46': ('2020', '2025', '金沢', '30K'),
    '55': ('2020', '2025', '佐賀', '35K'),
    '54': ('2020', '2025', '高知', '40K'),
    '51': ('2020', '2025', '姫路', '35K'),
    '30': ('2020', '2025', '門別', '40K'),
    '35': ('2020', '2025', '盛岡', '35K'),
    '36': ('2020', '2025', '水沢', '35K'),
    '33': ('2020', '2025', '帯広', '30K'),      # ばんえい競馬（別途検討）
}

# 実行順序（Priority順）
EXECUTION_ORDER = [
    '44',  # 大井（完了済み）
    '43',  # 船橋（完了済み）
    '45',  # 川崎（完了済み）
    '42',  # 浦和（完了済み）
    '48',  # 名古屋
    '50',  # 園田
    '47',  # 笠松
    '46',  # 金沢
    '55',  # 佐賀
    '54',  # 高知
    '51',  # 姫路
    '30',  # 門別
    '35',  # 盛岡
    '36',  # 水沢
    '33',  # 帯広
]

# 完了済み競馬場（スキップする）
COMPLETED_VENUES = ['44', '43', '45', '42']

class VenueTrainer:
    def __init__(self, skip_completed=True, skip_extraction=False, skip_training=False):
        self.skip_completed = skip_completed
        self.skip_extraction = skip_extraction
        self.skip_training = skip_training
        self.results = []
        self.log_file = Path(f'training_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        
    def log(self, message):
        """ログをファイルとコンソールに出力"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f'[{timestamp}] {message}'
        print(log_message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def run_command(self, command, venue_name, step_name):
        """コマンドを実行して結果を記録"""
        self.log(f'▶️ {step_name}: {venue_name}')
        self.log(f'   Command: {" ".join(command)}')
        
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            elapsed_time = time.time() - start_time
            
            if result.returncode == 0:
                self.log(f'✅ {step_name}完了: {venue_name} ({elapsed_time:.1f}秒)')
                return True, elapsed_time
            else:
                self.log(f'❌ {step_name}失敗: {venue_name}')
                self.log(f'   Error: {result.stderr[:500]}')
                return False, elapsed_time
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.log(f'❌ {step_name}エラー: {venue_name} - {str(e)}')
            return False, elapsed_time
    
    def extract_data(self, keibajo_code, start_year, end_year, venue_name):
        """データ抽出を実行"""
        if self.skip_extraction:
            self.log(f'⏭️  データ抽出スキップ: {venue_name}')
            return True, 0
        
        # ファイル名の生成（既存の命名規則に従う）
        if keibajo_code == '44':
            filename = f'ooi_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '43':
            filename = f'funabashi_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '45':
            filename = f'kawasaki_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '42':
            filename = f'urawa_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '48':
            filename = f'nagoya_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '50':
            filename = f'sonoda_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '47':
            filename = f'kasamatsu_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '46':
            filename = f'kanazawa_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '55':
            filename = f'saga_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '54':
            filename = f'kochi_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '51':
            filename = f'himeji_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '30':
            filename = f'mombetsu_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '35':
            filename = f'morioka_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '36':
            filename = f'mizusawa_{start_year}-{end_year}_v3.csv'
        elif keibajo_code == '33':
            filename = f'obihiro_{start_year}-{end_year}_v3.csv'
        else:
            filename = f'venue{keibajo_code}_{start_year}-{end_year}_v3.csv'
        
        command = [
            'python', 'extract_training_data_v2.py',
            '--keibajo', keibajo_code,
            '--start-date', start_year,
            '--end-date', end_year,
            '--output', filename
        ]
        
        success, elapsed = self.run_command(command, venue_name, 'データ抽出')
        return success, elapsed, filename if success else None
    
    def train_model(self, csv_filename, venue_name):
        """モデル学習を実行"""
        if self.skip_training:
            self.log(f'⏭️  学習スキップ: {venue_name}')
            return True, 0
        
        command = ['python', 'train_development.py', csv_filename]
        success, elapsed = self.run_command(command, venue_name, 'モデル学習')
        return success, elapsed
    
    def process_venue(self, keibajo_code):
        """1競馬場の処理（抽出→学習）"""
        start_year, end_year, venue_name, data_size = VENUE_CONFIG[keibajo_code]
        
        self.log('=' * 80)
        self.log(f'🏇 競馬場: {venue_name} (コード: {keibajo_code})')
        self.log(f'   期間: {start_year}-{end_year} | データ目安: {data_size}')
        self.log('=' * 80)
        
        venue_result = {
            'code': keibajo_code,
            'name': venue_name,
            'extraction_success': False,
            'training_success': False,
            'extraction_time': 0,
            'training_time': 0,
            'csv_file': None
        }
        
        # データ抽出
        extraction_success, extraction_time, csv_file = self.extract_data(
            keibajo_code, start_year, end_year, venue_name
        )
        venue_result['extraction_success'] = extraction_success
        venue_result['extraction_time'] = extraction_time
        venue_result['csv_file'] = csv_file
        
        if not extraction_success and not self.skip_extraction:
            self.log(f'⚠️  {venue_name} のデータ抽出に失敗したため、学習をスキップします')
            self.results.append(venue_result)
            return venue_result
        
        # 学習実行
        if csv_file or self.skip_extraction:
            # skip_extraction の場合は既存ファイル名を推測
            if not csv_file:
                csv_file = self._guess_csv_filename(keibajo_code, start_year, end_year)
            
            training_success, training_time = self.train_model(csv_file, venue_name)
            venue_result['training_success'] = training_success
            venue_result['training_time'] = training_time
        
        self.results.append(venue_result)
        
        total_time = venue_result['extraction_time'] + venue_result['training_time']
        self.log(f'✅ {venue_name} 完了 (合計: {total_time:.1f}秒)')
        self.log('')
        
        return venue_result
    
    def _guess_csv_filename(self, keibajo_code, start_year, end_year):
        """既存のCSVファイル名を推測"""
        name_map = {
            '44': 'ooi', '43': 'funabashi', '45': 'kawasaki', '42': 'urawa',
            '48': 'nagoya', '50': 'sonoda', '47': 'kasamatsu', '46': 'kanazawa',
            '55': 'saga', '54': 'kochi', '51': 'himeji', '30': 'mombetsu',
            '35': 'morioka', '36': 'mizusawa', '33': 'obihiro'
        }
        name = name_map.get(keibajo_code, f'venue{keibajo_code}')
        return f'{name}_{start_year}-{end_year}_v3.csv'
    
    def run_all(self):
        """全競馬場を順次実行"""
        self.log('🚀 全15競馬場の学習を開始します')
        self.log(f'   完了済みスキップ: {self.skip_completed}')
        self.log(f'   データ抽出スキップ: {self.skip_extraction}')
        self.log(f'   学習スキップ: {self.skip_training}')
        self.log('')
        
        start_time = time.time()
        
        for keibajo_code in EXECUTION_ORDER:
            if self.skip_completed and keibajo_code in COMPLETED_VENUES:
                venue_name = VENUE_CONFIG[keibajo_code][2]
                self.log(f'⏭️  {venue_name} (コード: {keibajo_code}) は完了済みのためスキップ')
                self.log('')
                continue
            
            self.process_venue(keibajo_code)
        
        total_time = time.time() - start_time
        self.print_summary(total_time)
    
    def print_summary(self, total_time):
        """実行結果のサマリーを出力"""
        self.log('=' * 80)
        self.log('📊 全競馬場の学習結果サマリー')
        self.log('=' * 80)
        
        for result in self.results:
            status = '✅' if result['extraction_success'] and result['training_success'] else '❌'
            total = result['extraction_time'] + result['training_time']
            self.log(f'{status} {result["name"]:10s} | '
                    f'抽出: {result["extraction_time"]:6.1f}秒 | '
                    f'学習: {result["training_time"]:6.1f}秒 | '
                    f'合計: {total:6.1f}秒')
        
        self.log('=' * 80)
        success_count = sum(1 for r in self.results 
                          if r['extraction_success'] and r['training_success'])
        self.log(f'✅ 成功: {success_count}/{len(self.results)} 競馬場')
        self.log(f'⏱️  合計実行時間: {total_time/60:.1f}分 ({total_time/3600:.2f}時間)')
        self.log(f'📄 詳細ログ: {self.log_file}')
        self.log('=' * 80)


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='全15競馬場の学習を一括実行')
    parser.add_argument('--include-completed', action='store_true',
                       help='完了済み競馬場も実行する')
    parser.add_argument('--skip-extraction', action='store_true',
                       help='データ抽出をスキップ（既存CSVを使用）')
    parser.add_argument('--skip-training', action='store_true',
                       help='学習をスキップ（データ抽出のみ）')
    parser.add_argument('--venue', type=str,
                       help='特定の競馬場のみ実行（コード指定: 44, 43, etc.）')
    
    args = parser.parse_args()
    
    trainer = VenueTrainer(
        skip_completed=not args.include_completed,
        skip_extraction=args.skip_extraction,
        skip_training=args.skip_training
    )
    
    if args.venue:
        if args.venue in VENUE_CONFIG:
            trainer.log(f'🎯 単一競馬場モード: {VENUE_CONFIG[args.venue][2]}')
            trainer.process_venue(args.venue)
            trainer.print_summary(0)
        else:
            print(f'❌ エラー: 競馬場コード {args.venue} が見つかりません')
            print(f'利用可能なコード: {", ".join(VENUE_CONFIG.keys())}')
            sys.exit(1)
    else:
        trainer.run_all()


if __name__ == '__main__':
    main()
