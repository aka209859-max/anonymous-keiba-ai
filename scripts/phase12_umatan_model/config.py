#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12: トリプル馬単特化予測モデル - 設定ファイル
"""

# 対象競馬場（南関東4場 + 門別）
TARGET_VENUES = {
    30: "門別",
    42: "浦和",
    43: "船橋",
    44: "大井",
    45: "川崎"
}

# 競馬場コードとフルゲート頭数のマッピング
FULLGATE_MAP = {
    30: 16,  # 門別
    42: 14,  # 浦和
    43: 14,  # 船橋
    44: 16,  # 大井
    45: 14   # 川崎
}

# 特徴量カラム（2着以内特化）
FEATURE_COLUMNS = [
    # 基本情報
    'umaban',
    'wakuban',
    'keibajo_code',
    
    # 過去成績（2着以内特化）
    'recent_1st_rate',      # 過去10走の1着率
    'recent_2nd_rate',      # 過去10走の2着率
    'recent_top2_rate',     # 過去10走の2着以内率
    'recent_1st_count',     # 過去10走の1着回数
    'recent_2nd_count',     # 過去10走の2着回数
    
    # 上がり・ペース
    'agari_3f_rank',        # 上がり3F順位
    'agari_3f_time',        # 上がり3F時計
    'final_corner_rank',    # 最終コーナー通過順位
    
    # 騎手・調教師（2着以内特化）
    'jockey_1st_rate',      # 騎手の1着率
    'jockey_2nd_rate',      # 騎手の2着率
    'jockey_top2_rate',     # 騎手の2着以内率
    'trainer_1st_rate',     # 調教師の1着率
    'trainer_2nd_rate',     # 調教師の2着率
    
    # 馬体重
    'bataiju',
    'bataiju_zougen',
    
    # オッズ情報
    'tansho_odds',
    'fukusho_odds_min',
    
    # クラス・レース条件
    'class_code',
    'race_class_1st_rate',  # このクラスでの1着率
    'race_class_2nd_rate',  # このクラスでの2着率
    
    # 脚質・展開
    'kakushitsu_code',
    'tenkai_code',
    
    # 距離・馬場
    'kyori',
    'baba_joutai',
    
    # 最終3Rフラグ（重み付け用）
    'is_last_3_race',
    
    # 統計特徴量
    'ensemble_score_mean',
    'ensemble_score_std',
]

# ターゲットカラム（マルチタスク学習）
TARGET_COLUMNS = {
    'task1': 'is_1st',           # 1着かどうか（Binary）
    'task2': 'is_2nd',           # 2着かどうか（Binary）
    'task3': 'finish_position'   # 着順（Ranking用）
}

# モデルハイパーパラメータ
MODEL_PARAMS = {
    # 共有層
    'shared_layers': [256, 128, 64],
    'dropout_rate': 0.4,
    'l2_regularization': 0.001,
    
    # タスク固有層
    'task_layers': [32, 16],
    
    # 学習設定
    'batch_size': 512,
    'epochs': 100,
    'learning_rate': 0.001,
    'early_stopping_patience': 15,
    
    # 損失関数の重み
    'loss_weights': {
        'task1_1st': 1.0,      # 1着予測の重み
        'task2_2nd': 0.8,      # 2着予測の重み
        'task3_rank': 0.5      # ランキングの重み
    },
    
    # クラス重み（不均衡対策）
    'class_weight_1st': 10.0,   # 1着のクラス重み
    'class_weight_2nd': 8.0,    # 2着のクラス重み
    
    # 最終3R重み付け
    'last3_race_weight': 2.0,
    
    # 競馬場ID埋め込み
    'venue_embedding_dim': 8
}

# 評価指標の閾値
EVALUATION_THRESHOLDS = {
    'top1_accuracy_threshold': 0.40,   # Top-1 Accuracy > 40%
    'top2_accuracy_threshold': 0.60,   # Top-2 Accuracy > 60%
    'top3_accuracy_threshold': 0.75,   # Top-3 Accuracy > 75%
    'exacta_hit_rate_threshold': 0.15  # 馬単的中率 > 15%
}

# データ分割設定
DATA_SPLIT = {
    'train_ratio': 0.7,
    'valid_ratio': 0.15,
    'test_ratio': 0.15,
    'time_series_split': True  # 時系列分割を使用
}

# ファイルパス
PATHS = {
    'raw_data_dir': 'data/phase12_umatan/raw',
    'features_dir': 'data/phase12_umatan/features',
    'models_dir': 'data/phase12_umatan/models',
    'predictions_dir': 'data/phase12_umatan/predictions',
    'logs_dir': 'data/phase12_umatan/logs'
}

# ロギング設定
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

# その他設定
MISC = {
    'random_seed': 42,
    'n_jobs': -1,  # 並列処理のCPU数（-1 = 全て使用）
    'verbose': 1
}
