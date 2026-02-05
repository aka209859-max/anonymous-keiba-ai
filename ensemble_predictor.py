#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ensemble_predictor.py
Phase 5: アンサンブル統合予測エンジン

Phase 3（二値分類）、Phase 4（ランキング）、Phase 4（回帰）の
3モデルの予測結果を統合し、総合的な予測スコアを算出
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import json
from datetime import datetime

class EnsemblePredictor:
    """アンサンブル予測エンジン"""
    
    def __init__(
        self,
        weight_phase3: float = 0.3,
        weight_phase4_ranking: float = 0.5,
        weight_phase4_regression: float = 0.2
    ):
        """
        初期化
        
        Args:
            weight_phase3: Phase 3（二値分類）の重み
            weight_phase4_ranking: Phase 4（ランキング）の重み
            weight_phase4_regression: Phase 4（回帰）の重み
        """
        self.weight_phase3 = weight_phase3
        self.weight_phase4_ranking = weight_phase4_ranking
        self.weight_phase4_regression = weight_phase4_regression
        
        # 重みの合計が1.0であることを確認
        total_weight = weight_phase3 + weight_phase4_ranking + weight_phase4_regression
        if not np.isclose(total_weight, 1.0):
            raise ValueError(f"重みの合計が1.0ではありません: {total_weight}")
    
    def load_predictions(
        self,
        binary_path: str,
        ranking_path: str,
        regression_path: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        3モデルの予測結果を読み込み
        
        Args:
            binary_path: Phase 3 予測結果のパス
            ranking_path: Phase 4 ランキング予測結果のパス
            regression_path: Phase 4 回帰予測結果のパス
        
        Returns:
            (binary_df, ranking_df, regression_df)
        """
        print("\n📂 予測結果の読み込み...")
        
        binary_df = pd.read_csv(binary_path)
        print(f"  ✅ Phase 3 二値分類: {len(binary_df)}件")
        
        ranking_df = pd.read_csv(ranking_path)
        print(f"  ✅ Phase 4 ランキング: {len(ranking_df)}件")
        
        regression_df = pd.read_csv(regression_path)
        print(f"  ✅ Phase 4 回帰: {len(regression_df)}件")
        
        return binary_df, ranking_df, regression_df
    
    def normalize_scores(self, df: pd.DataFrame, score_col: str) -> pd.Series:
        """
        スコアを0-1に正規化
        
        Args:
            df: データフレーム
            score_col: スコア列名
        
        Returns:
            正規化されたスコア
        """
        scores = df[score_col].copy()
        min_val = scores.min()
        max_val = scores.max()
        
        if max_val - min_val < 1e-10:
            return pd.Series(0.5, index=scores.index)
        
        normalized = (scores - min_val) / (max_val - min_val)
        return normalized
    
    def calculate_ensemble_score(
        self,
        binary_df: pd.DataFrame,
        ranking_df: pd.DataFrame,
        regression_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        アンサンブルスコアを計算
        
        Args:
            binary_df: Phase 3 予測結果
            ranking_df: Phase 4 ランキング予測結果
            regression_df: Phase 4 回帰予測結果
        
        Returns:
            統合スコア付きデータフレーム
        """
        print("\n🔄 アンサンブルスコアの計算...")
        
        # 必要なカラムの確認
        if 'predicted_probability' in binary_df.columns:
            binary_pred_col = 'predicted_probability'
        elif 'predicted_proba' in binary_df.columns:
            binary_pred_col = 'predicted_proba'
        else:
            binary_pred_col = 'predicted'
        
        if 'predicted_rank' in ranking_df.columns:
            ranking_pred_col = 'predicted_rank'
        else:
            ranking_pred_col = 'predicted'
        
        if 'predicted_time' in regression_df.columns:
            regression_pred_col = 'predicted_time'
        else:
            regression_pred_col = 'predicted'
        
        # 共通キーの作成（レース特定のため）
        # kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, umaban でマージ
        key_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 'ketto_toroku_bango']
        
        # データフレームのマージ
        ensemble_df = binary_df[key_cols + [binary_pred_col]].copy()
        ensemble_df = ensemble_df.merge(
            ranking_df[key_cols + [ranking_pred_col]],
            on=key_cols,
            how='inner'
        )
        ensemble_df = ensemble_df.merge(
            regression_df[key_cols + [regression_pred_col]],
            on=key_cols,
            how='inner'
        )
        
        print(f"  統合データ件数: {len(ensemble_df)}件")
        
        # Phase 3: 二値分類の確率をそのまま使用（0-1）
        phase3_score = ensemble_df[binary_pred_col]
        
        # Phase 4 ランキング: 順位を逆転してスコア化（1位 → 1.0, 最下位 → 0.0）
        max_rank = ensemble_df[ranking_pred_col].max()
        phase4_ranking_score = 1.0 - (ensemble_df[ranking_pred_col] - 1) / (max_rank - 1)
        
        # Phase 4 回帰: タイムを逆転してスコア化（速い → 1.0, 遅い → 0.0）
        phase4_regression_score = self.normalize_scores(
            ensemble_df.assign(neg_time=-ensemble_df[regression_pred_col]),
            'neg_time'
        )
        
        # アンサンブルスコアの計算
        ensemble_df['phase3_score'] = phase3_score
        ensemble_df['phase4_ranking_score'] = phase4_ranking_score
        ensemble_df['phase4_regression_score'] = phase4_regression_score
        
        ensemble_df['ensemble_score'] = (
            self.weight_phase3 * phase3_score +
            self.weight_phase4_ranking * phase4_ranking_score +
            self.weight_phase4_regression * phase4_regression_score
        )
        
        # 推奨度ランクの付与
        ensemble_df['rank'] = ensemble_df['ensemble_score'].apply(self._assign_rank)
        
        print(f"  ✅ アンサンブルスコア計算完了")
        print(f"     - 平均スコア: {ensemble_df['ensemble_score'].mean():.4f}")
        print(f"     - Sランク: {(ensemble_df['rank'] == 'S').sum()}頭")
        print(f"     - Aランク: {(ensemble_df['rank'] == 'A').sum()}頭")
        print(f"     - Bランク: {(ensemble_df['rank'] == 'B').sum()}頭")
        print(f"     - Cランク: {(ensemble_df['rank'] == 'C').sum()}頭")
        print(f"     - Dランク: {(ensemble_df['rank'] == 'D').sum()}頭")
        
        return ensemble_df
    
    def _assign_rank(self, score: float) -> str:
        """
        スコアから推奨度ランクを付与
        
        Args:
            score: アンサンブルスコア
        
        Returns:
            ランク（S/A/B/C/D）
        """
        if score >= 0.80:
            return 'S'
        elif score >= 0.65:
            return 'A'
        elif score >= 0.50:
            return 'B'
        elif score >= 0.35:
            return 'C'
        else:
            return 'D'
    
    def predict(
        self,
        binary_path: str,
        ranking_path: str,
        regression_path: str,
        output_path: str
    ) -> pd.DataFrame:
        """
        統合予測を実行
        
        Args:
            binary_path: Phase 3 予測結果のパス
            ranking_path: Phase 4 ランキング予測結果のパス
            regression_path: Phase 4 回帰予測結果のパス
            output_path: 出力先パス
        
        Returns:
            統合予測結果
        """
        print("\n" + "="*60)
        print("🚀 Phase 5: アンサンブル統合予測開始")
        print("="*60)
        
        # 予測結果の読み込み
        binary_df, ranking_df, regression_df = self.load_predictions(
            binary_path, ranking_path, regression_path
        )
        
        # アンサンブルスコアの計算
        ensemble_df = self.calculate_ensemble_score(
            binary_df, ranking_df, regression_df
        )
        
        # 結果の保存
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        ensemble_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n💾 統合予測結果を保存: {output_path}")
        print(f"   総件数: {len(ensemble_df)}件")
        
        # サマリー情報の保存
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(ensemble_df),
            'weights': {
                'phase3': self.weight_phase3,
                'phase4_ranking': self.weight_phase4_ranking,
                'phase4_regression': self.weight_phase4_regression
            },
            'rank_distribution': {
                'S': int((ensemble_df['rank'] == 'S').sum()),
                'A': int((ensemble_df['rank'] == 'A').sum()),
                'B': int((ensemble_df['rank'] == 'B').sum()),
                'C': int((ensemble_df['rank'] == 'C').sum()),
                'D': int((ensemble_df['rank'] == 'D').sum())
            },
            'score_stats': {
                'mean': float(ensemble_df['ensemble_score'].mean()),
                'std': float(ensemble_df['ensemble_score'].std()),
                'min': float(ensemble_df['ensemble_score'].min()),
                'max': float(ensemble_df['ensemble_score'].max())
            }
        }
        
        summary_path = output_file.parent / f"{output_file.stem}_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📊 サマリー情報を保存: {summary_path}")
        
        print("\n✅ Phase 5 アンサンブル統合予測完了！")
        print("="*60)
        
        return ensemble_df


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 5:
        print("使用法: python ensemble_predictor.py <binary_pred> <ranking_pred> <regression_pred> <output>")
        print("例: python ensemble_predictor.py predictions/phase45_ooi_test/ooi_test_binary_prediction.csv predictions/phase45_ooi_test/ooi_test_ranking_prediction.csv predictions/phase45_ooi_test/ooi_test_regression_prediction.csv predictions/phase5_ooi_test/ooi_test_ensemble.csv")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    ranking_path = sys.argv[2]
    regression_path = sys.argv[3]
    output_path = sys.argv[4]
    
    # アンサンブル予測の実行
    predictor = EnsemblePredictor(
        weight_phase3=0.3,
        weight_phase4_ranking=0.5,
        weight_phase4_regression=0.2
    )
    
    ensemble_df = predictor.predict(
        binary_path,
        ranking_path,
        regression_path,
        output_path
    )
