#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
トリプル馬単キャリーオーバー情報取得スクリプト
南関東4場（浦和、船橋、大井、川崎）、門別、園田、姫路に対応

データソース:
- nankankeiba.com（南関東4場）
- spat4.jp（門別、園田、姫路）
"""

import requests
from bs4 import BeautifulSoup
import re
import datetime
import json
import logging
from pathlib import Path
from typing import Dict, Optional

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TripleUmatanCarryoverScraper:
    """トリプル馬単キャリーオーバー情報スクレイパー"""
    
    def __init__(self):
        self.nankan_url = "https://www.nankankeiba.com/"
        self.spat4_url = "https://www.spat4.jp/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 競馬場コードマッピング
        self.venue_map = {
            '浦和': 42,
            '船橋': 43,
            '大井': 44,
            '川崎': 45,
            '門別': 30,
            '園田': 50,
            '姫路': 51
        }
        
        # フルゲート頭数マッピング
        self.fullgate_map = {
            42: 14,  # 浦和
            43: 14,  # 船橋
            44: 16,  # 大井
            45: 14,  # 川崎
            30: 16,  # 門別
            50: 14,  # 園田（推定）
            51: 14   # 姫路（推定）
        }
    
    def parse_japanese_amount(self, text: str) -> int:
        """
        日本語の金額表記（例：2億3000万円）を整数に変換する
        
        Args:
            text: 金額テキスト（例：11億1321万0000円）
        
        Returns:
            int: 金額（円）
        """
        if not text:
            return 0
        
        # 不要な空白を除去
        text = text.strip()
        
        # 0円判定
        if "なし" in text or "ありません" in text or text == "-" or "0円" in text:
            return 0
        
        # 数値計算ロジック
        total = 0
        
        # '億' の処理
        oku_match = re.search(r'(\d+)億', text)
        if oku_match:
            total += int(oku_match.group(1)) * 100_000_000
        
        # '万' の処理
        man_match = re.search(r'(\d+)万', text)
        if man_match:
            total += int(man_match.group(1)) * 10_000
        
        # '円' の前の端数処理
        # 億・万が含まれない純粋な数字のみのケース
        if total == 0:
            simple_digit = re.sub(r'[^\d]', '', text)
            if simple_digit:
                total = int(simple_digit)
        
        return total
    
    def fetch_nankan_carryover(self) -> Dict[str, int]:
        """
        nankankeiba.com から南関東4場のキャリーオーバー情報を取得
        
        Returns:
            dict: {'浦和': 金額, '船橋': 金額, '大井': 金額, '川崎': 金額}
        """
        result = {}
        
        try:
            response = requests.get(self.nankan_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # SPAT4 LOTO セクションの特定
            logo = soup.find('img', alt=re.compile(r'SPAT4.*LOTO', re.IGNORECASE))
            if not logo:
                logging.warning("SPAT4 LOTO logo not found on nankankeiba.com")
                return result
            
            # ロゴを含むコンテナへ移動
            container = logo.find_parent('div')
            if not container:
                logging.warning("SPAT4 LOTO container not found")
                return result
            
            # コンテナ内のテキストを解析
            text = container.get_text()
            
            # 各競馬場のキャリーオーバー情報を抽出
            for venue_name in ['浦和', '船橋', '大井', '川崎']:
                # パターン: 競馬場名 + キャリーオーバー + 金額
                pattern = rf'{venue_name}.*?キャリーオーバー[：:]\s*([^\n]+)'
                match = re.search(pattern, text, re.DOTALL)
                
                if match:
                    amount_text = match.group(1).strip()
                    amount = self.parse_japanese_amount(amount_text)
                    result[venue_name] = amount
                    logging.info(f"✅ {venue_name}: {amount:,}円 ({amount_text})")
                else:
                    result[venue_name] = 0
                    logging.warning(f"⚠️ {venue_name}: キャリーオーバー情報が見つかりません")
        
        except Exception as e:
            logging.error(f"❌ nankankeiba.com からの取得に失敗: {e}")
        
        return result
    
    def fetch_spat4_carryover(self) -> Dict[str, int]:
        """
        spat4.jp から門別、園田、姫路のキャリーオーバー情報を取得
        
        Returns:
            dict: {'門別': 金額, '園田': 金額, '姫路': 金額}
        """
        result = {}
        
        try:
            response = requests.get(self.spat4_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # SPAT4 LOTO セクションの特定（spat4.jpのDOM構造に合わせて調整）
            # 実際のDOM構造に応じて要修正
            text = soup.get_text()
            
            # 各競馬場のキャリーオーバー情報を抽出
            for venue_name in ['門別', '園田', '姫路']:
                pattern = rf'{venue_name}.*?キャリーオーバー[：:]\s*([^\n]+)'
                match = re.search(pattern, text, re.DOTALL)
                
                if match:
                    amount_text = match.group(1).strip()
                    amount = self.parse_japanese_amount(amount_text)
                    result[venue_name] = amount
                    logging.info(f"✅ {venue_name}: {amount:,}円 ({amount_text})")
                else:
                    result[venue_name] = 0
                    logging.info(f"ℹ️ {venue_name}: キャリーオーバー情報なし")
        
        except Exception as e:
            logging.error(f"❌ spat4.jp からの取得に失敗: {e}")
        
        return result
    
    def fetch_all_carryover(self) -> Dict[int, Dict[str, any]]:
        """
        全競馬場のキャリーオーバー情報を取得
        
        Returns:
            dict: {競馬場コード: {'venue_name': '浦和', 'carryover': 金額, 'fullgate': 14}}
        """
        all_data = {}
        
        # 南関東4場
        nankan_data = self.fetch_nankan_carryover()
        
        # 門別、園田、姫路
        spat4_data = self.fetch_spat4_carryover()
        
        # 統合
        combined_data = {**nankan_data, **spat4_data}
        
        for venue_name, amount in combined_data.items():
            venue_code = self.venue_map.get(venue_name)
            if venue_code:
                all_data[venue_code] = {
                    'venue_name': venue_name,
                    'venue_code': venue_code,
                    'carryover': amount,
                    'fullgate': self.fullgate_map.get(venue_code, 14),
                    'timestamp': datetime.datetime.now().isoformat()
                }
        
        return all_data
    
    def save_to_json(self, data: Dict, output_path: str):
        """
        JSON形式で保存
        
        Args:
            data: 保存するデータ
            output_path: 出力先パス
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"💾 保存完了: {output_file}")


def main():
    """メイン処理"""
    scraper = TripleUmatanCarryoverScraper()
    
    print("="*80)
    print("トリプル馬単キャリーオーバー情報取得")
    print("="*80)
    
    # 全競馬場のキャリーオーバー情報を取得
    carryover_data = scraper.fetch_all_carryover()
    
    # 結果表示
    print("\n📊 取得結果:")
    print("-"*80)
    
    total_carryover = 0
    for venue_code, info in sorted(carryover_data.items()):
        venue_name = info['venue_name']
        carryover = info['carryover']
        fullgate = info['fullgate']
        
        total_carryover += carryover
        
        if carryover > 0:
            print(f"🏇 {venue_name}（{venue_code}）: {carryover:,}円 "
                  f"| フルゲート: {fullgate}頭")
        else:
            print(f"   {venue_name}（{venue_code}）: キャリーオーバーなし "
                  f"| フルゲート: {fullgate}頭")
    
    print("-"*80)
    print(f"💰 合計キャリーオーバー: {total_carryover:,}円")
    print("="*80)
    
    # JSON保存
    today = datetime.datetime.now().strftime("%Y%m%d")
    output_path = f"data/triple_umatan/carryover/carryover_{today}.json"
    scraper.save_to_json(carryover_data, output_path)
    
    print(f"\n✅ キャリーオーバー情報取得完了")


if __name__ == "__main__":
    main()
