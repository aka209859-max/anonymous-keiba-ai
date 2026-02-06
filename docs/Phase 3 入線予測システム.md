Phase 3 入線予測システム（binary classification）の技術的実装と運用に関する包括的調査報告書1. 序論：競馬予測システムにおける推論フェーズの重要性と位置付け現代のスポーツアナリティクス、とりわけ競馬予測の領域においては、膨大な過去データに基づく機械学習モデルの構築（Phase 2）と同等、あるいはそれ以上に、実戦環境における推論プロセス（Phase 3）の堅牢性が求められる。本報告書は、匿名化された競馬AIプロジェクト「anonymous-keiba-ai」における、Phase 1で生成された特徴量を用いたPhase 3入線予測（3着以内=1、4着以下=0の二値分類）の実装、検証、および運用手順に関する詳細な技術レポートである。本フェーズの目的は、学習済みモデル（LightGBM）を用いて、未知のレースデータに対して確率的な予測を行い、投資判断の基礎となるデータを提供することにある。特に、競馬データは不完全性（欠損値）、非定常性（環境の変化）、および高次元性（多数の特徴量）を伴うため、推論スクリプト predict_phase3.py の実装には、単なるAPIの呼び出しに留まらない、深いデータエンジニアリングとエラーハンドリングの設計が不可欠である。本報告書では、提示された要件定義に基づき、スクリプトの動作検証、モデル読み込みの仕様、特徴量アライメントの厳密性、および出力データの整合性について、ソースコードレベルでの解析と、運用を見据えた包括的な提言を行う。特に、学習時と推論時の「特徴量の不一致（Feature Mismatch）」や「列順序の齟齬（Column Order Mismatch）」は、予測精度を著しく低下させるサイレントキラー（静かなる障害）であるため 、これに対する防御策を中心に論じる。2. 理論的背景とアーキテクチャ設計2.1 勾配ブースティング決定木（GBDT）と二値分類本システムの中核となる学習済みモデルは、LightGBM（Light Gradient Boosting Machine）を用いて構築されている。LightGBMは、決定木の成長においてLeaf-wise（葉ごとの）アプローチを採用しており、深さ優先の探索を行うことで学習速度と精度を両立させている 。Phase 3におけるタスクは「二値分類（Binary Classification）」である。具体的には、各出走馬（サンプル）に対して、特徴量ベクトル $\mathbf{x}$ を入力とし、その馬が3着以内に入線する確率 $P(y=1|\mathbf{x})$ を推定する。モデルの出力は、ロジット（対数オッズ）形式の生のスコア $z$ として計算され、シグモイド関数を通じて $$ の確率空間に写像される 。$$P(y=1|\mathbf{x}) = \frac{1}{1 + e^{-z}}$$ここで算出された確率は、単純な勝ち負けではなく「複勝圏内への入線期待値」を表すため、馬券戦略（複勝、ワイド、三連複の軸馬選定など）において極めて重要な指標となる。2.2 システム構成とデータフロー本プロジェクトのディレクトリ構成とデータフローは、バッチ処理を前提とした設計となっている。モデル格納場所: models/binary/{keibajo}_2020-2025_v3_model.txt競馬場ごとの特性（コース形状、芝・ダートの傾向）を反映するため、モデルは競馬場コード（keibajo）単位で分割されている。また、テキスト形式（.txt）で保存されている点は、異なるライブラリバージョン間での互換性を保つ上で有利である 。入力データ: data/features/YYYY/MM/{keibajo}_{YYYYMMDD}_features.csvPhase 1の特徴量エンジニアリング済みデータ。開催年（YYYY）、月（MM）で階層化されており、日次バッチ処理に適した構造となっている。出力データ: data/predictions/phase3/{keibajo}_{YYYYMMDD}_phase3.csv推論結果は、元の識別子に加え、予測確率とクラス判定を付与して保存される。このアーキテクチャにおいて、predict_phase3.py は入力とモデルを結合する「推論エンジン」として機能する。このエンジンの信頼性を担保するためには、以下の検証項目をクリアしなければならない。3. 検証項目詳解3.1 モデル読み込み機構の検証LightGBM Booster形式の採用PythonにおけるLightGBMの利用には、scikit-learn準拠のAPI（LGBMClassifier）と、ネイティブな Booster APIの2種類が存在する。本プロジェクトのモデルファイル ..._model.txt は、LightGBMのネイティブ形式で保存されたテキストファイルである。したがって、モデルの読み込みには lightgbm.Booster(model_file='path/to/model.txt') を使用する必要がある 。joblib や pickle を用いたオブジェクトの直列化とは異なり、テキスト形式のモデルファイルは可読性があり、モデル内部のツリー構造や特徴量名を目視で確認することも可能である 。これはデバッグ時に極めて有用である。特徴量名の取得と整合性モデル読み込み後の最初かつ最も重要なステップは、モデルが学習時に使用した「特徴量リスト」の取得である。Booster オブジェクトには feature_name() メソッドが存在し、これにより学習時の特徴量名をリスト形式で取得できる 。リスク要因: scikit-learn APIの LGBMClassifier で学習した場合、特徴量名は feature_name_ 属性に格納されるが、テキスト形式で保存されたモデルを Booster で読み込む場合、これらのメタデータの一部（例えばクラスラベルのマッピングなど）が失われる場合がある 。しかし、特徴量名そのものはモデルファイルのヘッダー部分（feature_names セクション）に記録されているため、Booster.feature_name() を通じて確実に復元可能である 。3.2 予測実行ロジックとデータ前処理特徴量のアライメント（Feature Alignment）推論時の最大の落とし穴は、DataFrameの列順序が学習時と異なる場合に発生する。LightGBMのネイティブAPIは、列名ではなく「列のインデックス（順序）」に基づいて予測を行う場合がある（特にPandas DataFrameを直接渡さず、Numpy配列化して渡す場合など）。たとえ列名が一致していても、順序が入れ替わっていれば、モデルは誤った特徴量を誤ったノードの判定に使用してしまう。これを防ぐため、本スクリプトでは pandas.DataFrame.reindex メソッドを使用し、入力データをモデルの feature_name() の順序に強制的に従わせる実装が必須となる 。欠損情報の処理戦略Phase 1データには、学習データには存在しなかった欠損や、逆に学習時には存在したが推論データには存在しない特徴量が含まれる可能性がある。欠損特徴量の補完（Missing Columns）:モデルが要求する特徴量が入力CSVに存在しない場合（例：新しい特徴量セットで学習したモデルを、古い形式のデータに適用する場合）、該当列を作成し、値を「0」で埋める 。理由: 多くの特徴量（例：過去の賞金、出走回数）において、0は「情報なし」や「該当なし」を意味するニュートラルな値として機能するためである。また、ワンホットエンコーディングされたカテゴリ変数の場合、0はそのカテゴリに該当しないことを意味するため、論理的に整合する。欠損値の補完（NaN Values）:存在する列の中に NaN が含まれる場合、これを「平均値（Mean）」で補完する。理由: LightGBMは本来 NaN を許容し、分岐学習時に NaN 専用のパスを学習する能力を持つ 。しかし、システム要件として明示的な補完が求められている場合、平均値補完はデータの分布を大きく歪めずに欠損を埋める標準的な手法である。特に、標準化された数値データにおいて平均値（多くの場合0に近い値）は安全な代替値となる 。3.3 予測確率の算出と閾値処理Booster.predict(data) メソッドは、デフォルトで各クラスの予測確率（二値分類の場合は正例の確率）を返す 。出力はNumPy配列となり、各要素は $$ の範囲の実数である。閾値処理:要件に基づき、確率が0.5以上の場合を「入線（1）」、未満を「入線なし（0）」と判定する。predicted_class = (probability >= 0.5).astype(int)この閾値0.5は、適合率（Precision）と再現率（Recall）のバランスを取る標準的な値であるが、運用においては回収率を最大化するために、オッズと組み合わせて閾値を動的に変更する戦略も考えられる。Phase 3の出力としては、生の確率 binary_probability を残すことで、後続のシステム（馬券購入エンジン等）での柔軟な活用を可能にする。3.4 出力形式と文字コード出力ファイルはCSV形式とし、エンコーディングは UTF-8 とする。これは、馬名や騎手名などの日本語文字列が含まれる可能性があるため、Shift-JIS等の機種依存文字によるトラブルを避けるために必須の要件である。ファイル名規則 {keibajo}_{YYYYMMDD}_phase3.csv は、データパイプラインにおけるトレーサビリティを確保するために厳格に遵守されなければならない。4. predict_phase3.py 実装詳細と動作フローここでは、検証項目に基づき再設計された predict_phase3.py の完全な実装コードとその解説を行う。このコードは、エラーハンドリング、バッチ処理対応、およびデータ整合性の確保を考慮したプロダクション品質のものである。4.1 推奨実装コードPythonimport sys
import os
import argparse
import logging
import pandas as pd
import numpy as np
import lightgbm as lgb
from pathlib import Path

# ロギング設定：標準出力とファイルへの記録
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=
)
logger = logging.getLogger(__name__)

def parse_args():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description='Phase 3 Inference Script for Keiba Prediction')
    parser.add_argument('test_csv', type=str, help='Path to input feature CSV file')
    parser.add_argument('model_path', type=str, help='Path to trained LightGBM model (.txt)')
    parser.add_argument('output_path', type=str, help='Path to save prediction output CSV')
    return parser.parse_args()

def load_model(model_path):
    """LightGBMモデル（Booster）の読み込み"""
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        sys.exit(1)
    
    try:
        # テキスト形式のモデルをBoosterとして読み込む
        bst = lgb.Booster(model_file=model_path)
        logger.info(f"Model loaded successfully from {model_path}")
        return bst
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

def load_data(data_path):
    """入力CSVデータの読み込み"""
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    try:
        # ID列などは文字列として読み込む必要があるため、dtypeを指定
        # 実際にはデータに合わせて調整が必要だが、主要なID列はstr推奨
        df = pd.read_csv(data_path, encoding='utf-8')
        logger.info(f"Data loaded successfully from {data_path}. Shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

def align_features(df, model_features):
    """
    モデルの特徴量リストに合わせてDataFrameを整形する
    1. 不足している特徴量は0で埋める
    2. 不要な特徴量は削除する
    3. 特徴量の順序をモデルと一致させる
    """
    # 現在のデータフレームに含まれる特徴量
    current_columns = set(df.columns)
    model_features_set = set(model_features)
    
    # 不足している特徴量を特定
    missing_features = list(model_features_set - current_columns)
    if missing_features:
        logger.warning(f"Missing features detected: {len(missing_features)} columns. Filling with 0.")
        # 欠損特徴量を0で一括作成（メモリ効率のため、まとめて追加推奨だが、reindexで処理可能）
    
    # reindexを使用して、整列・追加・削除を一括で行う
    # fill_value=0 により、新規追加される列（不足していた列）は0で埋められる [10, 11]
    # 既存の列データは保持される
    aligned_df = df.reindex(columns=model_features, fill_value=0)
    
    # データ型の一貫性を確保（数値型へ変換）
    # エラーが発生する場合は、非数値が含まれている可能性があるためcoerceする
    aligned_df = aligned_df.apply(pd.to_numeric, errors='coerce')
    
    # NaNが存在する場合の処理（要件：平均値補完）
    # 注意: 全てがNaNの列（reindexで追加された列など）の平均はNaNになるため、その場合は0とする
    if aligned_df.isnull().any().any():
        logger.info("NaN values detected. Filling with column means.")
        aligned_df = aligned_df.fillna(aligned_df.mean()).fillna(0)
    
    return aligned_df

def main():
    args = parse_args()
    
    # 1. モデル読み込み
    bst = load_model(args.model_path)
    
    # モデルが必要とする特徴量名の取得
    model_feature_names = bst.feature_name()
    logger.info(f"Model expects {len(model_feature_names)} features.")
    
    # 2. データ読み込み
    input_df = load_data(args.test_csv)
    
    # 3. 特徴量アライメントと補完
    # 予測に使用する特徴量データ（X）を作成
    X = align_features(input_df, model_feature_names)
    
    # 4. 予測実行
    logger.info("Starting prediction...")
    try:
        # predictメソッドは確率(0~1)を返す
        probabilities = bst.predict(X)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        sys.exit(1)
    
    # 5. 結果の整形
    # 必須列の抽出（入力データフレームからメタデータを取得）
    required_id_cols = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 'ketto_toroku_bango', 'umaban']
    
    # 入力データに必要なID列が存在するか確認
    missing_ids = [col for col in required_id_cols if col not in input_df.columns]
    if missing_ids:
        logger.warning(f"Input data is missing identifier columns: {missing_ids}. Output may be incomplete.")
    
    # 結果データフレームの構築
    result_df = input_df[required_id_cols].copy() if not missing_ids else input_df.copy()
    
    # 確率とクラスの付与
    result_df['binary_probability'] = probabilities
    result_df['predicted_class'] = (probabilities >= 0.5).astype(int)
    
    # 6. 出力保存
    output_path = Path(args.output_path)
    # ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        result_df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Predictions saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save output: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
4.2 スクリプトの主要機能と適合性分析Q1. 予測専用データ（target列なし）への対応本スクリプトは、入力データに正解ラベル（target列）が含まれているかどうかを感知しない設計となっている。align_features 関数において、モデルが要求する特徴量名のみを reindex で抽出・構築するため、入力CSVに目的変数（例：rank, is_top3など）が含まれていなくても動作する。逆に、含まれていたとしても無視されるため、学習用データを用いたテスト実行も可能である。Q2. モデルとデータの特徴量不一致の処理align_features 関数がこの問題の解決策となる。過剰な列: 入力データにモデルが知らない列が含まれていても、reindex により除外される。不足の列: reindex(columns=model_features, fill_value=0) により、自動的に0で埋められた列が生成される。これにより、LightGBMの入力次元数エラーを防ぐ。順序: reindex は指定されたリストの順序通りに列を並べ替えるため、LightGBMが期待する列順序と完全に一致する 。Q3. 評価指標の扱いスクリプト内では accuracy_score や roc_auc_score などの評価指標計算を行わない。これは、Phase 3が未来のレース（正解ラベルが存在しない）を対象としているためである。評価が必要な場合は、出力されたCSVと別途用意した正解データを突き合わせる別の評価スクリプトで実施すべきである。Q4. バッチ処理への対応本スクリプトはPandas DataFrame全体を一括で処理する。つまり、入力CSVに1レース分のデータが含まれていようと、1年分のデータ（数万行）が含まれていようと、メモリが許す限り一度の predict コールで全行の予測を行う。ループ処理を行わないベクトル化演算であるため、非常に高速に動作する 。Q5. エラーハンドリングtry-except ブロックを、ファイルI/O（読み書き）、モデルロード、予測実行の各クリティカルパスに配置している。また、logging モジュールを使用し、エラー発生時には標準出力に詳細なログを出力して終了コード1を返す設計としているため、ジョブ管理システム（AirflowやCronなど）からの異常検知が容易である。5. 運用および検証手順書Phase 3 予測システムの導入にあたり、以下の手順で動作確認と運用を行うことを推奨する。5.1 事前準備ディレクトリ確認:E:/anonymous-keiba-ai/ 配下に以下の構造が存在することを確認する。models/binary/ : 学習済みモデル格納data/features/ : 入力特徴量データ格納data/predictions/phase3/ : 出力先（なければスクリプトが作成する）ライブラリ依存関係:以下のバージョン（またはそれ以上）のインストールを推奨する。lightgbm >= 3.0pandas >= 1.0numpy5.2 実行コマンドの形式コマンドプロンプトまたはPowerShellで以下を実行する。Bash# 実行例：東京競馬場（05）の2024年11月24日のレースを予測
python E:/anonymous-keiba-ai/predict_phase3.py ^
  "E:/anonymous-keiba-ai/data/features/2024/11/05_20241124_features.csv" ^
  "E:/anonymous-keiba-ai/models/binary/05_2020-2025_v3_model.txt" ^
  "E:/anonymous-keiba-ai/data/predictions/phase3/05_20241124_phase3.csv"
5.3 動作確認チェックリスト検証項目確認内容期待される結果起動確認引数なしで実行ヘルプメッセージが表示され、エラー終了しないことモデル読込存在するモデルパスを指定ログに "Model loaded successfully" と表示されることデータ読込存在するCSVを指定ログに "Data loaded successfully" と行数が表示されること特徴量補完一部カラムを削除したダミーCSVを入力ログに警告が出ず（またはInfoレベルで補完通知）、正常に終了すること出力確認出力CSVを開くbinary_probability 列と predicted_class 列が存在し、0.5以上でクラス1になっていることID整合性入力と出力を比較ketto_toroku_bango や race_bango が入力と完全に行単位で一致していること5.4 バッチ実行の自動化（参考）日次の運用では、特定の日付の全競馬場の予測を行う必要がある。以下のようなバッチファイル（Windows）またはシェルスクリプトを作成することで、運用の効率化が可能である。コード スニペット:: run_daily_prediction.bat
@echo off
set YYYY=2024
set MM=11
set DATE=20241124
set BASE_DIR=E:/anonymous-keiba-ai

:: 各競馬場コードでループ（例：01〜10）
for %%K in (01 02 03 04 05 06 07 08 09 10) do (
    set INPUT_FILE=%BASE_DIR%/data/features/%YYYY%/%MM%/%%K_%DATE%_features.csv
    set MODEL_FILE=%BASE_DIR%/models/binary/%%K_2020-2025_v3_model.txt
    set OUTPUT_FILE=%BASE_DIR%/data/predictions/phase3/%%K_%DATE%_phase3.csv

    if exist "%INPUT_FILE%" (
        if exist "%MODEL_FILE%" (
            echo Processing %%K...
            python %BASE_DIR%/predict_phase3.py "%INPUT_FILE%" "%MODEL_FILE%" "%OUTPUT_FILE%"
        ) else (
            echo Model for %%K not found. Skipping.
        )
    )
)
pause
6. 結論と提言本調査報告書では、Phase 3における入線予測システムの要件定義に基づき、堅牢な推論スクリプトの実装詳細と運用ガイドラインを提示した。主要な結論LightGBM Boosterの優位性: テキスト形式のモデルとBooster APIを使用することで、特徴量名の可視性と管理が容易になり、ブラックボックス化を防ぐことができる。アライメントの重要性: pandas.reindex による特徴量の強制整列は、予測精度を担保するための最も重要な工程である。これを省略すると、列順序の不一致により、予測結果がランダムに近いものになるリスクがある 。欠損処理の標準化: 欠損特徴量を0、欠損値を平均値で埋めるロジックをコード内で明文化することで、入力データの品質変動に対するシステムの耐性（レジリエンス）を高めることができる。今後の展望と提言特徴量ドリフトの監視: 本システムは静的なモデルを使用しているが、競馬の傾向は時間とともに変化する。出力された binary_probability の分布を定期的に監視し、平均確率が大きく変動している場合は、モデルの再学習（Phase 2の再実行）を検討すべきである 。メタデータの拡張: 現在の出力は必要最小限のIDのみだが、デバッグや分析のために feature_importance の高いトップ5の特徴量の値を予測結果に付記することも、説明可能性（Explainability）の観点から有用である。以上の実装と運用手順を遵守することで、「anonymous-keiba-ai」プロジェクトは、信頼性の高い入線予測を安定的かつ継続的に生成する能力を獲得するに至るだろう。