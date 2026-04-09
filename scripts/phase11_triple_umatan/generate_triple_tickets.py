#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
トリプル馬単買い目生成スクリプト

AI予想データとキャリーオーバー情報を基に、最適な買い目を生成
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import json
import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class TripleTicketGenerator:
    """トリプル馬単買い目生成クラス"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def extract_target_races(self, ensemble_df: pd.DataFrame) -> pd.DataFrame:
        """
        最終3レースを抽出
        
        Args:
            ensemble_df: ensemble予想データ
        
        Returns:
            pd.DataFrame: 最終3レースのデータ
        """
        max_race = ensemble_df['race_bango'].max()
        target_start = max_race - 2
        
        target_races = ensemble_df[ensemble_df['race_bango'] >= target_start].copy()
        
        logging.info(f"🎯 対象レース: 第{target_start}R〜第{max_race}R")
        
        return target_races
    
    def get_top_horses_per_race(self, race_data: pd.DataFrame, 
                                race_num: int, 
                                top_n: int = 5) -> List[int]:
        """
        レースごとのTOP N頭を取得
        
        Args:
            race_data: レースデータ
            race_num: レース番号
            top_n: 上位何頭まで取得するか
        
        Returns:
            list: 馬番のリスト
        """
        race_horses = race_data[race_data['race_bango'] == race_num].copy()
        race_horses = race_horses.sort_values('ensemble_score', ascending=False)
        
        top_horses = race_horses.head(top_n)['umaban'].tolist()
        
        return top_horses
    
    def generate_umatan_combinations(self, horses_1st: List[int], 
                                    horses_2nd: List[int]) -> List[Tuple[int, int]]:
        """
        馬単の組み合わせを生成（1着→2着）
        
        Args:
            horses_1st: 1着候補の馬番リスト
            horses_2nd: 2着候補の馬番リスト
        
        Returns:
            list: 馬単組み合わせのリスト [(1着, 2着), ...]
        """
        combinations = []
        
        for h1 in horses_1st:
            for h2 in horses_2nd:
                if h1 != h2:  # 同じ馬は除外
                    combinations.append((h1, h2))
        
        return combinations
    
    def generate_triple_tickets(self, race_data: pd.DataFrame, 
                               strategy: str = "balanced") -> List[Tuple[Tuple, Tuple, Tuple]]:
        """
        トリプル馬単の買い目を生成
        
        Args:
            race_data: 最終3レースの予想データ
            strategy: 戦略タイプ
                - "conservative": 超堅実型（2-2-2）
                - "balanced": バランス型（3-3-3）
                - "aggressive": 広範囲型（4-4-4）
                - "very_aggressive": 超広範囲型（6-6-6）
        
        Returns:
            list: トリプル馬単の組み合わせリスト
        """
        race_numbers = sorted(race_data['race_bango'].unique())
        
        if len(race_numbers) != 3:
            logging.error(f"❌ 対象レースが3つではありません: {len(race_numbers)}レース")
            return []
        
        # 戦略ごとの設定
        strategy_config = {
            "conservative": {"1st": 2, "2nd": 2},
            "balanced": {"1st": 2, "2nd": 3},
            "aggressive": {"1st": 2, "2nd": 4},
            "very_aggressive": {"1st": 3, "2nd": 6}
        }
        
        config = strategy_config.get(strategy, strategy_config["balanced"])
        
        # 各レースのTOP馬を取得
        race1_top = self.get_top_horses_per_race(race_data, race_numbers[0], config["1st"])
        race1_2nd = self.get_top_horses_per_race(race_data, race_numbers[0], config["2nd"])
        
        race2_top = self.get_top_horses_per_race(race_data, race_numbers[1], config["1st"])
        race2_2nd = self.get_top_horses_per_race(race_data, race_numbers[1], config["2nd"])
        
        race3_top = self.get_top_horses_per_race(race_data, race_numbers[2], config["1st"])
        race3_2nd = self.get_top_horses_per_race(race_data, race_numbers[2], config["2nd"])
        
        # 各レースの馬単組み合わせを生成
        race1_combos = self.generate_umatan_combinations(race1_top, race1_2nd)
        race2_combos = self.generate_umatan_combinations(race2_top, race2_2nd)
        race3_combos = self.generate_umatan_combinations(race3_top, race3_2nd)
        
        # トリプル馬単の全組み合わせを生成
        triple_tickets = []
        
        for combo1 in race1_combos:
            for combo2 in race2_combos:
                for combo3 in race3_combos:
                    triple_tickets.append((combo1, combo2, combo3))
        
        logging.info(f"✅ 買い目生成完了: {len(triple_tickets)}点")
        logging.info(f"  - 第{race_numbers[0]}R: {len(race1_combos)}通り")
        logging.info(f"  - 第{race_numbers[1]}R: {len(race2_combos)}通り")
        logging.info(f"  - 第{race_numbers[2]}R: {len(race3_combos)}通り")
        
        return triple_tickets
    
    def format_tickets_for_display(self, tickets: List[Tuple], 
                                   race_numbers: List[int]) -> str:
        """
        買い目を表示用にフォーマット
        
        Args:
            tickets: 買い目リスト
            race_numbers: レース番号リスト
        
        Returns:
            str: フォーマット済みテキスト
        """
        output = []
        output.append("="*80)
        output.append("トリプル馬単買い目")
        output.append("="*80)
        output.append(f"対象レース: 第{race_numbers[0]}R - 第{race_numbers[1]}R - 第{race_numbers[2]}R")
        output.append(f"購入点数: {len(tickets)}点")
        output.append(f"投資額: {len(tickets) * 50:,}円")
        output.append("="*80)
        output.append("")
        
        # 各レースごとの買い目を表示
        race1_combos = sorted(set(ticket[0] for ticket in tickets))
        race2_combos = sorted(set(ticket[1] for ticket in tickets))
        race3_combos = sorted(set(ticket[2] for ticket in tickets))
        
        output.append(f"第{race_numbers[0]}R 馬単:")
        for combo in race1_combos:
            output.append(f"  {combo[0]}→{combo[1]}")
        output.append("")
        
        output.append(f"第{race_numbers[1]}R 馬単:")
        for combo in race2_combos:
            output.append(f"  {combo[0]}→{combo[1]}")
        output.append("")
        
        output.append(f"第{race_numbers[2]}R 馬単:")
        for combo in race3_combos:
            output.append(f"  {combo[0]}→{combo[1]}")
        output.append("")
        
        output.append("-"*80)
        output.append(f"全{len(tickets)}通りの組み合わせ")
        output.append("="*80)
        
        return "\n".join(output)
    
    def save_tickets_to_file(self, tickets: List[Tuple], 
                            venue_name: str,
                            race_numbers: List[int],
                            strategy: str,
                            output_dir: str = "data/triple_umatan/predictions"):
        """
        買い目をファイルに保存
        
        Args:
            tickets: 買い目リスト
            venue_name: 競馬場名
            race_numbers: レース番号リスト
            strategy: 戦略名
            output_dir: 出力ディレクトリ
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        today = datetime.datetime.now().strftime("%Y%m%d")
        
        # テキスト形式で保存
        txt_file = output_path / f"{venue_name}_{today}_triple_{strategy}.txt"
        formatted_text = self.format_tickets_for_display(tickets, race_numbers)
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        logging.info(f"💾 買い目保存（テキスト）: {txt_file}")
        
        # JSON形式で保存（機械可読用）
        json_file = output_path / f"{venue_name}_{today}_triple_{strategy}.json"
        
        json_data = {
            'venue': venue_name,
            'date': today,
            'strategy': strategy,
            'race_numbers': race_numbers,
            'num_tickets': len(tickets),
            'total_cost': len(tickets) * 50,
            'tickets': [
                {
                    'race1': {'1st': t[0][0], '2nd': t[0][1]},
                    'race2': {'1st': t[1][0], '2nd': t[1][1]},
                    'race3': {'1st': t[2][0], '2nd': t[2][1]}
                }
                for t in tickets
            ]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"💾 買い目保存（JSON）: {json_file}")


def main():
    """メイン処理"""
    generator = TripleTicketGenerator()
    
    print("="*80)
    print("トリプル馬単買い目生成")
    print("="*80)
    
    # ダミーデータで動作確認
    dummy_data = pd.DataFrame({
        'race_bango': [10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 12, 12, 12, 12, 12],
        'umaban': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 1],
        'ensemble_score': [0.95, 0.88, 0.82, 0.75, 0.70, 0.90, 0.85, 0.80, 0.73, 0.68,
                          0.92, 0.87, 0.83, 0.76, 0.71]
    })
    
    # 最終3レースを抽出
    target_races = generator.extract_target_races(dummy_data)
    
    # バランス型の買い目生成
    print("\n🎯 バランス型（3-3-3）買い目生成")
    print("-"*80)
    
    tickets = generator.generate_triple_tickets(target_races, strategy="balanced")
    
    if tickets:
        race_numbers = sorted(target_races['race_bango'].unique())
        formatted = generator.format_tickets_for_display(tickets, race_numbers)
        print(formatted)
        
        # ファイル保存
        generator.save_tickets_to_file(
            tickets=tickets,
            venue_name="船橋",
            race_numbers=race_numbers,
            strategy="balanced"
        )
    
    print("\n✅ 買い目生成完了")


if __name__ == "__main__":
    main()
