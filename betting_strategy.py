#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
betting_strategy.py
Phase 5: 買い目生成ロジック

アンサンブル予測結果から馬券の買い目を自動生成
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime


class BettingStrategy:
    """買い目生成エンジン"""
    
    def __init__(
        self,
        min_confidence_tansho: float = 0.80,  # 単勝の最低信頼度
        min_confidence_umaren: float = 0.65,  # 馬連の最低信頼度
        min_confidence_wide: float = 0.50,    # ワイドの最低信頼度
        max_bet_horses: int = 5               # 最大購入頭数
    ):
        """
        初期化
        
        Args:
            min_confidence_tansho: 単勝購入の最低信頼度
            min_confidence_umaren: 馬連購入の最低信頼度
            min_confidence_wide: ワイド購入の最低信頼度
            max_bet_horses: 最大購入頭数
        """
        self.min_confidence_tansho = min_confidence_tansho
        self.min_confidence_umaren = min_confidence_umaren
        self.min_confidence_wide = min_confidence_wide
        self.max_bet_horses = max_bet_horses
    
    def load_ensemble_predictions(self, ensemble_path: str) -> pd.DataFrame:
        """
        アンサンブル予測結果を読み込み
        
        Args:
            ensemble_path: アンサンブル予測結果のパス
        
        Returns:
            アンサンブル予測データフレーム
        """
        print("\n📂 アンサンブル予測結果の読み込み...")
        df = pd.read_csv(ensemble_path)
        print(f"  ✅ 読み込み完了: {len(df)}件")
        return df
    
    def generate_race_bets(self, race_df: pd.DataFrame) -> Dict:
        """
        1レース分の買い目を生成
        
        Args:
            race_df: レースのデータフレーム（1レース分）
        
        Returns:
            買い目情報の辞書
        """
        # スコア順にソート
        race_df = race_df.sort_values('ensemble_score', ascending=False).reset_index(drop=True)
        
        bets = {
            'race_id': f"{race_df.iloc[0]['kaisai_nen']}{race_df.iloc[0]['kaisai_tsukihi']:04d}{race_df.iloc[0]['keibajo_code']:02d}{race_df.iloc[0]['race_bango']:02d}",
            'race_info': {
                'kaisai_nen': int(race_df.iloc[0]['kaisai_nen']),
                'kaisai_tsukihi': int(race_df.iloc[0]['kaisai_tsukihi']),
                'keibajo_code': int(race_df.iloc[0]['keibajo_code']),
                'race_bango': int(race_df.iloc[0]['race_bango'])
            },
            'horses': [],
            'bets': {
                'tansho': [],      # 単勝
                'umaren': [],      # 馬連
                'wide': [],        # ワイド
                'sanrenpuku': []   # 三連複
            },
            'confidence': 'NONE'
        }
        
        # 馬情報の収集
        for idx, row in race_df.iterrows():
            horse_info = {
                'umaban': int(row.get('umaban', idx + 1)),
                'ketto_toroku_bango': str(row['ketto_toroku_bango']),
                'ensemble_score': float(row['ensemble_score']),
                'rank': str(row['rank']),
                'phase3_score': float(row['phase3_score']),
                'phase4_ranking_score': float(row['phase4_ranking_score']),
                'phase4_regression_score': float(row['phase4_regression_score'])
            }
            bets['horses'].append(horse_info)
        
        # Sランク馬（本命）の抽出
        s_rank_horses = race_df[race_df['rank'] == 'S']
        
        # Aランク馬（対抗）の抽出
        a_rank_horses = race_df[race_df['rank'] == 'A']
        
        # Bランク馬（注意）の抽出
        b_rank_horses = race_df[race_df['rank'] == 'B']
        
        # 単勝：Sランク馬のみ
        if len(s_rank_horses) > 0:
            top_horse = s_rank_horses.iloc[0]
            if top_horse['ensemble_score'] >= self.min_confidence_tansho:
                bets['bets']['tansho'].append({
                    'umaban': int(top_horse.get('umaban', 1)),
                    'confidence': float(top_horse['ensemble_score']),
                    'reason': f"Sランク本命（スコア: {top_horse['ensemble_score']:.4f}）"
                })
                bets['confidence'] = 'HIGH'
        
        # 馬連：S×A（軸馬流し）
        if len(s_rank_horses) > 0 and len(a_rank_horses) > 0:
            axis_horse = s_rank_horses.iloc[0]
            for idx, companion_horse in a_rank_horses.head(min(3, len(a_rank_horses))).iterrows():
                combined_score = (axis_horse['ensemble_score'] + companion_horse['ensemble_score']) / 2
                if combined_score >= self.min_confidence_umaren:
                    bets['bets']['umaren'].append({
                        'horses': [
                            int(axis_horse.get('umaban', 1)),
                            int(companion_horse.get('umaban', 2))
                        ],
                        'confidence': float(combined_score),
                        'reason': f"S×A流し（軸: {axis_horse['ensemble_score']:.4f}, 相手: {companion_horse['ensemble_score']:.4f}）"
                    })
        
        # ワイド：S×B（穴馬狙い）
        if len(s_rank_horses) > 0 and len(b_rank_horses) > 0:
            axis_horse = s_rank_horses.iloc[0]
            for idx, dark_horse in b_rank_horses.head(min(2, len(b_rank_horses))).iterrows():
                combined_score = (axis_horse['ensemble_score'] + dark_horse['ensemble_score']) / 2
                if combined_score >= self.min_confidence_wide:
                    bets['bets']['wide'].append({
                        'horses': [
                            int(axis_horse.get('umaban', 1)),
                            int(dark_horse.get('umaban', 3))
                        ],
                        'confidence': float(combined_score),
                        'reason': f"S×B穴馬（軸: {axis_horse['ensemble_score']:.4f}, 穴: {dark_horse['ensemble_score']:.4f}）"
                    })
        
        # 三連複：S-A-A/B（フォーメーション）
        if len(s_rank_horses) > 0 and (len(a_rank_horses) + len(b_rank_horses)) >= 2:
            axis_horse = s_rank_horses.iloc[0]
            companion_horses = pd.concat([a_rank_horses, b_rank_horses]).head(4)
            
            # 上位3頭の組み合わせ
            if len(companion_horses) >= 2:
                for i in range(len(companion_horses)):
                    for j in range(i+1, min(i+3, len(companion_horses))):
                        horse2 = companion_horses.iloc[i]
                        horse3 = companion_horses.iloc[j]
                        combined_score = (
                            axis_horse['ensemble_score'] + 
                            horse2['ensemble_score'] + 
                            horse3['ensemble_score']
                        ) / 3
                        
                        if combined_score >= self.min_confidence_wide:
                            bets['bets']['sanrenpuku'].append({
                                'horses': [
                                    int(axis_horse.get('umaban', 1)),
                                    int(horse2.get('umaban', 2)),
                                    int(horse3.get('umaban', 3))
                                ],
                                'confidence': float(combined_score),
                                'reason': f"S-A/B（{axis_horse['ensemble_score']:.4f}/{horse2['ensemble_score']:.4f}/{horse3['ensemble_score']:.4f}）"
                            })
        
        # 信頼度の設定
        if bets['confidence'] == 'NONE':
            if len(a_rank_horses) > 0:
                bets['confidence'] = 'MEDIUM'
            elif len(b_rank_horses) > 0:
                bets['confidence'] = 'LOW'
        
        return bets
    
    def generate_all_bets(self, ensemble_df: pd.DataFrame) -> List[Dict]:
        """
        全レースの買い目を生成
        
        Args:
            ensemble_df: アンサンブル予測結果
        
        Returns:
            全レースの買い目リスト
        """
        print("\n🎫 買い目の生成...")
        
        # レースごとにグループ化
        race_groups = ensemble_df.groupby(['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango'])
        
        all_bets = []
        high_conf_count = 0
        medium_conf_count = 0
        low_conf_count = 0
        
        for race_key, race_df in race_groups:
            bets = self.generate_race_bets(race_df)
            all_bets.append(bets)
            
            if bets['confidence'] == 'HIGH':
                high_conf_count += 1
            elif bets['confidence'] == 'MEDIUM':
                medium_conf_count += 1
            elif bets['confidence'] == 'LOW':
                low_conf_count += 1
        
        print(f"  ✅ 買い目生成完了: {len(all_bets)}レース")
        print(f"     - 高信頼度: {high_conf_count}レース")
        print(f"     - 中信頼度: {medium_conf_count}レース")
        print(f"     - 低信頼度: {low_conf_count}レース")
        
        return all_bets
    
    def save_bets(self, bets: List[Dict], output_path: str):
        """
        買い目をJSON形式で保存
        
        Args:
            bets: 買い目リスト
            output_path: 出力先パス
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'total_races': len(bets),
            'total_bets': {
                'tansho': sum(len(b['bets']['tansho']) for b in bets),
                'umaren': sum(len(b['bets']['umaren']) for b in bets),
                'wide': sum(len(b['bets']['wide']) for b in bets),
                'sanrenpuku': sum(len(b['bets']['sanrenpuku']) for b in bets)
            },
            'races': bets
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 買い目を保存: {output_path}")
        print(f"   総レース数: {len(bets)}")
        print(f"   単勝: {output_data['total_bets']['tansho']}点")
        print(f"   馬連: {output_data['total_bets']['umaren']}点")
        print(f"   ワイド: {output_data['total_bets']['wide']}点")
        print(f"   三連複: {output_data['total_bets']['sanrenpuku']}点")
    
    def generate(self, ensemble_path: str, output_path: str) -> List[Dict]:
        """
        買い目生成のメイン処理
        
        Args:
            ensemble_path: アンサンブル予測結果のパス
            output_path: 出力先パス
        
        Returns:
            買い目リスト
        """
        print("\n" + "="*60)
        print("🎫 Phase 5: 買い目生成開始")
        print("="*60)
        
        # アンサンブル予測結果の読み込み
        ensemble_df = self.load_ensemble_predictions(ensemble_path)
        
        # 買い目の生成
        bets = self.generate_all_bets(ensemble_df)
        
        # 買い目の保存
        self.save_bets(bets, output_path)
        
        print("\n✅ Phase 5 買い目生成完了！")
        print("="*60)
        
        return bets


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("使用法: python betting_strategy.py <ensemble_pred> <output>")
        print("例: python betting_strategy.py predictions/phase5_ooi_test/ooi_test_ensemble.csv predictions/phase5_ooi_test/ooi_test_bets.json")
        sys.exit(1)
    
    ensemble_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # 買い目生成の実行
    strategy = BettingStrategy(
        min_confidence_tansho=0.80,
        min_confidence_umaren=0.65,
        min_confidence_wide=0.50,
        max_bet_horses=5
    )
    
    bets = strategy.generate(ensemble_path, output_path)
