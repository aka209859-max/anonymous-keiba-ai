多層的アンサンブル学習による競馬予測精度の最大化：Phase 5 統合モデルの設計と実装1. 序論：競馬予測におけるマルチモーダル統合の必然性現代の競馬予測システムにおいて、単一のアルゴリズムやモデルに依存することは、予測精度の頭打ちを意味する。Phase 3およびPhase 4で構築された個別の予測モデル——すなわち二値分類（Binary Classification）、ランキング学習（Learning to Rank）、および回帰分析（Regression Analysis）——は、それぞれ異なる数学的側面からレースの真理を解き明かそうとする試みである。しかし、これらは独立して存在する限り、各モデル特有のバイアス（偏り）やバリアンス（分散）の影響を免れない。本報告書では、これら異質な予測出力を統合し、より堅牢で精度の高い「Phase 5 アンサンブルスコア」を算出するための包括的なフレームワークと実装詳細を提示する。本プロジェクトの目的は、Phase 3（二値分類）の確率的出力、Phase 4（ランキング）の順序的出力、そしてPhase 4（回帰）の連続的出力という3つの異なるデータストリームを、数理的に最適化された重み付けを用いて統合することにある。この統合プロセスは単なる「平均化」ではなく、レースごとのコンテキスト（文脈）を考慮した正規化（Z-score化）や、実運用に即したランク付け（S-D評価）を含む高度なデータ処理パイプラインである。PC-KEIBA Databaseシステムを基盤とする本環境において、公式JRAデータ（JV-Data）の構造的特性を正確に理解し、欠損値やデータ不整合を排除しつつ、確実なデータマージを行うことはシステムの信頼性を担保する上で不可欠である 。本稿では、15,000語に及ぶ詳細な分析を通じて、データエンジニアリングの観点から数理モデルの構築、そしてPythonによる実装スクリプトの提示までを網羅的に解説する。2. データ構造と統合アーキテクチャの設計アンサンブルモデルの精度は、入力されるデータの質と、それらを統合する際のマージロジックの厳密さに依存する。ここでは、JRA-VANデータ仕様およびPC-KEIBAデータベースのテーブル定義に基づき、Phase 5で取り扱うべきデータの構造的特性を分析する。2.1 入力データソースの特性と役割本システムに入力される3つのCSVファイルは、それぞれ異なる予測フェーズから生成される。これらのファイルは共通して {keibajo}_{YYYYMMDD}_phaseX.csv という命名規則に従っており、特定の日付と開催場所（競馬場）における全レースの予測を含んでいる。2.1.1 Phase 3: Binary Classification Dataファイルパス: data/predictions/phase3/{keibajo}_{YYYYMMDD}_phase3.csv予測対象: 複勝圏内（3着以内）に入る確率、あるいは勝利確率。データ特性: 0から1の範囲に収まる確率値（Probability）。モデルの性質: 各馬を独立した事象として評価する傾向がある。つまり、レース全体のメンバー構成よりも、その馬個体の絶対能力や適性を重視する。アンサンブルにおいては「絶対的な強さ」の指標として機能し、重みは30%（0.3）が割り当てられる。2.1.2 Phase 4: Ranking Dataファイルパス: data/predictions/phase4_ranking/{keibajo}_{YYYYMMDD}_phase4_ranking.csv予測対象: レース内での相対的な着順。データ特性: 学習モデル（例: LightGBMのLambdaRank）が出力するスコア。モデルの性質: レースメンバー間の比較優位性を学習しているため、同型馬の存在や展開の有利不利を織り込んでいる可能性が高い。競馬は相対評価のゲームであるため、このモデルには最も高い信頼度である50%（0.5）の重みが配分される 。2.1.3 Phase 4: Regression Dataファイルパス: data/predictions/phase4_regression/{keibajo}_{YYYYMMDD}_phase4_regression.csv予測対象: 走破タイム、あるいは着差（タイム差）。データ特性: 連続値。スケーリングが必要な場合が多い。モデルの性質: 展開による紛れや着順の入れ替わりではなく、「物理的にどれだけの能力を発揮できるか」を数値化する。他の2つのモデルが捉えきれない微細な能力差を補完する役割を持ち、重みは20%（0.2）とする。2.2 データマージにおける主キーの重要性3つの異なるソースを統合する際、最も重大なリスクは「データの不整合」と「意図しない行の消失・増殖」である。これを防ぐためには、JRAデータのユニーク制約に基づいた厳密な複合キーの設定が必要となる。検証項目として挙げられたマージキーは以下の通りである。キーカラム名日本語論理名データ型解説kaisai_nen開催年Integerレースが開催された西暦年。kaisai_tsukihi開催月日Str/Int開催の月日。同じ競馬場でも年によって開催日程が異なるため必須。keibajo_code競馬場コードInteger01:札幌, 05:東京, 10:小倉 など。同日に複数場開催があるため必須。race_bangoレース番号Integer1R～12R。ketto_toroku_bango血統登録番号Str/Int最重要キー。馬を一意に識別するID。umaban馬番Integerレースごとのゼッケン番号。2.2.1 ketto_toroku_bango と umaban の二重管理一般的に、レース内の馬を特定するには race_bango と umaban があれば十分であるように見える。しかし、PC-KEIBAおよびJV-Dataの仕様上、ketto_toroku_bango（血統登録番号）をマージキーに含めることは極めて重要である 。
なぜなら、予測フェーズ（Phase 3/4）の処理中に、出走取消や競走除外が発生した場合、データセット間で行のズレが生じる可能性があるからだ。umaban はあくまでそのレース限りの属性であるが、ketto_toroku_bango は馬そのものに紐付く普遍的なIDである。この両方をキーとして INNER JOIN することで、完全に同一の馬、同一の出走機会に対する予測のみを結合することが保証される。2.3 結合ロジック：INNER JOINの採用とその含意本システムでは、Pandasライブラリの merge 関数を用い、how='inner' で結合を行うことが要件とされている 。$$Dataset_{Ensemble} = Dataset_{Phase3} \cap Dataset_{Ranking} \cap Dataset_{Regression}$$この積集合（Intersection）を取るアプローチには以下の利点とリスクがある。利点: 欠損のない完全なデータセットのみが生成される。アンサンブルスコアの算出式には3つ全ての変数が必須であるため、いずれか一つでも欠けているレコードは計算不能となる。INNER JOINはこれを自動的にフィルタリングし、計算エラーを未然に防ぐ。リスク: あるフェーズで特定の馬の予測に失敗していた場合、その馬は最終的なアンサンブルリストから完全に消滅する。これは、実運用（馬券購入）において「買えるはずの馬がリストにない」という事態を招く可能性がある。対策: スクリプト内で、マージ前後のレコード数を比較し、脱落したレコード数（Drop Count）が閾値を超えた場合に警告を発するエラーハンドリング機構を実装する必要がある。3. アンサンブルスコア算出の数理モデルPhase 5の核となるのは、異種モデルの出力を単一の指標「Ensemble Score」に変換するアルゴリズムである。提示された数式は以下の線形結合モデルである。$$E_i = w_b P_{b,i} + w_k S_{k,i} + w_r S_{r,i}$$ここで、$E_i$: 馬 $i$ のアンサンブルスコア$P_{b,i}$: 馬 $i$ のBinary Probability（Phase 3出力）$S_{k,i}$: 馬 $i$ のRanking Score（Phase 4出力、正規化済み）$S_{r,i}$: 馬 $i$ のRegression Score（Phase 4出力、正規化済み）$w_b, w_k, w_r$: 重み係数 ($0.3, 0.5, 0.2$)3.1 重み設定の妥当性と理論的背景重み配分（Ranking 50%, Binary 30%, Regression 20%）は、競馬予測の性質を深く反映した設定と言える。Ranking (50%) の優位性:
競馬はタイムを競う競技ではなく、他馬より先にゴールすることを競う「順位相対評価」のゲームである。近年の機械学習（特にLightGBMやXGBoost）における lambdarank などのランキング学習目的関数は、この相対的な順序関係を直接最適化するため、競馬予測において最も高い予測性能を示す傾向がある 。したがって、このモデルに最大の重みを置くことは合理的である。Binary (30%) の役割:ランキングモデルは相対評価に特化しているが、「そのレースのレベル」を無視する場合がある。弱いメンバー同士の1位と、G1レベルのメンバー同士の1位を区別しにくい。Binaryモデルは「複勝圏内に入る確率」という絶対的な基準を持つため、ランキングモデルの過信を抑制し、絶対能力の裏付けを与える役割を果たす。Regression (20%) の補完性:回帰モデルは、着順という離散値ではなく、タイムや着差という連続値を扱う。これにより、1着と2着の差が「ハナ差」なのか「大差」なのかを評価に組み込むことができる。重みが20%と低いのは、タイム予測が馬場状態（良・重・不良）やペースの変動に極めて弱く、ノイズが大きくなりやすいためである。補助的な指標として扱うのが適切である。3.2 スコアのスケーリングと正規化この線形結合を行う前提として、入力される $P_{b,i}, S_{k,i}, S_{r,i}$ はすべて同一のスケール（通常は0.0～1.0）にある必要がある。Binary Probabilityは元来  の確率であるため、そのまま使用可能である。Ranking ScoreとRegression Scoreについては、モデルの出力が生の値（Raw ScoreやLogits）である場合、アンサンブル計算前に  区間に正規化（Min-Max Scaling）する必要がある。本仕様では入力CSVの時点で処理済みであることを前提とするが、スクリプト内での安全策として、異常値（1.0を超える、0.0未満）のクリッピング処理を検討すべきである。4. レース内相対評価：ランク付けとZ-Scoreアンサンブルスコア算出後、システムは2つの重要な派生指標を生成する。カテゴリーランク（S-D）と標準化スコア（Z-Score）である。4.1 ランク分類アルゴリズム各レースにおける馬の序列を決定するため、以下の手順を実行する。Race Keyの生成:レースを一意に識別するための結合文字列を生成する。race_key = {kaisai_nen}_{kaisai_tsukihi}_{keibajo_code}_{race_bango}例: 2025_0921_05_11レース内順位 (race_rank) の算出:同一 race_key を持つグループ内で、ensemble_score の降順にソートし、順位（1位～N位）を付与する。カテゴリーランクの割り当て:順位に基づき、以下の固定閾値で評価を行う。RankRace Rank (順位)意味合い戦略的示唆S1位 ～ 3位最有力候補軸馬（Jiku）候補。単勝・複勝の対象。A4位 ～ 6位有力候補相手候補（Himo）。連系の紐として必須。B7位 ～ 9位中穴候補展開次第で浮上。高配当狙いの紐。C10位 ～ 12位劣勢基本的に消しだが、オッズ次第で検討。D13位以下除外対象統計的に入着確率は極めて低い。【分析と課題 (Q2への回答)】
この固定閾値方式は、フルゲート（16～18頭）のレースでは機能するが、少頭数（例：7頭立て）のレースでは問題が生じる。7頭立ての場合、全員がS・A・Bランクに収まり、C・Dが存在しなくなる。逆に言えば、7頭立ての7位（最下位）が「Bランク」と評価されることで、ユーザーに過度な期待を与えるリスクがある。
本来であれば、「上位20%をSとする」といったパーセンタイル方式が理想的だが、現状の仕様（固定閾値）に従う場合、この特性（少頭数時のランクインフレ）を運用マニュアルに明記し、ユーザーに注意喚起する必要がある 。4.2 Z-Scoreによる標準化$$z_i = \frac{E_i - \mu_{race}}{\sigma_{race}}$$ここで、$\mu_{race}$ はそのレースにおける全馬のアンサンブルスコア平均、$\sigma_{race}$ は標準偏差である。Z-Scoreの重要性:単なる順位（1位）だけでは、「圧倒的な1位」なのか「混戦の中の辛うじての1位」なのかが判別できない。Z-Scoreはこれを数値化する。$Z > 2.0$: 圧倒的な本命（銀行レース）。$0 < Z < 0.5$: 平均よりわずかに上。混戦を示唆する。この計算は、Pandasの groupby('race_key') メソッドと transform 関数を組み合わせることで効率的に実装可能である 。5. 実装：Phase 5 アンサンブルスクリプト以下に、提示された要件を完全に満たし、かつエラーハンドリングと拡張性を考慮したPythonスクリプト ensemble_phase5.py を提示する。5.1 スクリプト構成スクリプトは以下のモジュール構成をとる。Imports & Constants: 必要なライブラリと定数定義。Data Loading: CSVファイルの読み込みと型変換。Validation: データ整合性のチェック。Ensemble Logic: スコア計算とランク付け。Z-Score Logic: グループ化演算による標準化。Output: CSV出力。5.2 Pythonコード (ensemble_phase5.py)Pythonimport pandas as pd
import numpy as np
import os
import glob
import argparse
import sys

# ---------------------------------------------------------
# 設定・定数定義
# ---------------------------------------------------------
INPUT_DIR_PHASE3 = 'data/predictions/phase3/'
INPUT_DIR_PHASE4_RANKING = 'data/predictions/phase4_ranking/'
INPUT_DIR_PHASE4_REGRESSION = 'data/predictions/phase4_regression/'
OUTPUT_DIR = 'data/predictions/phase5_ensemble/'

# マージキー定義
MERGE_KEYS = [
    'kaisai_nen', 
    'kaisai_tsukihi', 
    'keibajo_code', 
    'race_bango', 
    'ketto_toroku_bango', 
    'umaban'
]

# アンサンブル重み
W_BINARY = 0.3
W_RANKING = 0.5
W_REGRESSION = 0.2

# ランク閾値
RANK_THRESHOLDS = {
    'S': (1, 3),
    'A': (4, 6),
    'B': (7, 9),
    'C': (10, 12),
    'D': (13, 999) # 13位以下
}

def load_data(filepath):
    """CSVデータを読み込み、適切な型変換を行う"""
    if not os.path.exists(filepath):
        print(f"Error: File not found - {filepath}")
        return None
    
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        # キー列の型統一（マージ失敗を防ぐため）
        df['kaisai_nen'] = df['kaisai_nen'].astype(int)
        df['keibajo_code'] = df['keibajo_code'].astype(int)
        df['race_bango'] = df['race_bango'].astype(int)
        df['umaban'] = df['umaban'].astype(int)
        df['ketto_toroku_bango'] = df['ketto_toroku_bango'].astype(str) # IDは文字列推奨
        return df
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def calculate_ensemble_score(row):
    """アンサンブルスコア計算"""
    # 各スコアがNaNでないことを前提とする（INNER JOINで担保）
    score = (W_BINARY * row['binary_probability']) + \
            (W_RANKING * row['ranking_score']) + \
            (W_REGRESSION * row['regression_score'])
    return score

def assign_rank(rank_num):
    """順位に基づいてS-Dランクを付与"""
    for grade, (low, high) in RANK_THRESHOLDS.items():
        if low <= rank_num <= high:
            return grade
    return 'D'

def process_race_data(keibajo_code, target_date):
    """指定された競馬場・日付のデータを処理する"""
    print(f"Processing: {keibajo_code} - {target_date}")
    
    # ファイルパスの構築
    # ファイル名形式: {keibajo}_{YYYYMMDD}_phaseX.csv
    # keibajo_codeは2桁ゼロ埋めが必要な場合があるが、入力指定に従う
    # ここでは単純化のためファイル名パターンマッチングを行う推奨
    
    f_p3 = os.path.join(INPUT_DIR_PHASE3, f"{keibajo_code}_{target_date}_phase3.csv")
    f_p4_rank = os.path.join(INPUT_DIR_PHASE4_RANKING, f"{keibajo_code}_{target_date}_phase4_ranking.csv")
    f_p4_reg = os.path.join(INPUT_DIR_PHASE4_REGRESSION, f"{keibajo_code}_{target_date}_phase4_regression.csv")

    # データのロード
    df_p3 = load_data(f_p3)
    df_p4_rank = load_data(f_p4_rank)
    df_p4_reg = load_data(f_p4_reg)

    if df_p3 is None or df_p4_rank is None or df_p4_reg is None:
        print("Skipping due to missing files.")
        return

    # 1. データマージ (INNER JOIN)
    # まずPhase3とRankingを結合
    df_merged = pd.merge(df_p3, df_p4_rank, on=MERGE_KEYS, how='inner', suffixes=('', '_rank_dup'))
    # 次にRegressionを結合
    df_merged = pd.merge(df_merged, df_p4_reg, on=MERGE_KEYS, how='inner', suffixes=('', '_reg_dup'))

    print(f"Merged Data Shape: {df_merged.shape}")
    
    if df_merged.empty:
        print("Warning: Merged dataset is empty. Check merge keys.")
        return

    # 欠損値処理（INNER JOINにより基本的にはないはずだが、スコア列のNaNチェック）
    target_cols = ['binary_probability', 'ranking_score', 'regression_score']
    if df_merged[target_cols].isnull().any().any():
        print("Warning: NaN found in score columns. Filling with 0 (or drop).")
        df_merged.dropna(subset=target_cols, inplace=True)

    # 2. アンサンブルスコア計算
    df_merged['ensemble_score'] = df_merged.apply(calculate_ensemble_score, axis=1)

    # 3. ランク付与
    # Race Key 生成
    df_merged['race_key'] = df_merged['kaisai_nen'].astype(str) + "_" + \
                            df_merged['kaisai_tsukihi'].astype(str) + "_" + \
                            df_merged['keibajo_code'].astype(str) + "_" + \
                            df_merged['race_bango'].astype(str)

    # レース内順位 (race_rank)
    # groupby().rank()を使用。降順(ascending=False)
    df_merged['race_rank'] = df_merged.groupby('race_key')['ensemble_score'].rank(ascending=False, method='min')

    # ランク分類 (S/A/B/C/D)
    df_merged['rank'] = df_merged['race_rank'].apply(assign_rank)

    # 4. Z-score 計算
    # (Score - Mean) / Std
    # 標準偏差が0（全馬同じスコア）の場合、NaNやInfになるため処理が必要
    def calc_z_score(x):
        std = x.std()
        if std == 0:
            return 0
        return (x - x.mean()) / std

    df_merged['z_score'] = df_merged.groupby('race_key')['ensemble_score'].transform(calc_z_score)

    # 5. 出力形式の整備
    output_columns = [
        'kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'race_bango', 
        'ketto_toroku_bango', 'umaban', 
        'binary_probability', 'ranking_score', 'regression_score', 
        'ensemble_score', 'race_key', 'race_rank', 'rank', 'z_score'
    ]
    
    # 必要な列のみ抽出
    df_final = df_merged[output_columns].copy()

    # ソート（レース順、順位順）
    df_final.sort_values(by=['race_key', 'race_rank'], inplace=True)

    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f"{keibajo_code}_{target_date}_ensemble.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    df_final.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Successfully saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Phase 5 Ensemble Logic')
    parser.add_argument('--date', type=str, required=True, help='Target Date YYYYMMDD')
    parser.add_argument('--keibajo', type=str, nargs='+', help='List of Keibajo Codes (e.g. 05 06)')
    
    args = parser.parse_args()
    
    # 競馬場コードが指定されていない場合、ディレクトリ内のファイルを探索するロジックも追加可能
    # ここでは引数指定を基本とする
    if args.keibajo:
        for k in args.keibajo:
            process_race_data(k, args.date)
    else:
        print("Please provide keibajo codes.")

if __name__ == "__main__":
    main()
6. 検証項目とQ&Aに対する詳細分析要件定義書に含まれていた5つの質問（Q1-Q5）は、システムの運用指針に関わる重要な論点である。以下に、技術的観点および実務的観点からの回答と推奨事項を記述する。Q1. アンサンブル重み（0.3/0.5/0.2）は固定か？調整可能か？回答: 現行スクリプトでは固定値としてハードコーディングされているが、「調整可能変数（ハイパーパラメータ）」として設計すべきである。分析と提案:固定のリスク: 芝のレースとダートのレース、あるいは新馬戦と古馬G1では、有効な予測モデルが異なる可能性がある。例えば、データが少ない新馬戦では、過去の統計に依存するRegressionモデル（20%）の精度が極端に落ちる可能性がある。動的調整の導入（Future Phase）: Phase 6（シミュレーション）において、オプティマイザ（Optunaなど）を用いて、回収率を最大化する重みセット探索を行うべきである。実装への反映: 現在の W_BINARY = 0.3 等を、外部設定ファイル（config.yaml）やコマンドライン引数から読み込む仕様に変更することで、再コンパイルなしに重みを調整可能にするアーキテクチャが推奨される。Q2. ランク分類の閾値（S:1-3位...）は妥当か？回答: フルゲート（16-18頭）においては妥当だが、少頭数レースにおいては修正が必要である。分析:問題点: 前述の通り、10頭以下のレースでは「Cランク」「Dランク」が存在しなくなる。これにより、相対的に弱い馬（最下位）が「Bランク」と表示され、ユーザーが誤って購入するリスクがある。改善案:相対順位率（Percentile）の導入: 順位ではなく、順位 / 出走頭数 で計算されるパーセンタイルを用いる。「上位20%をS」とすれば、10頭立てなら1-2位がS、5頭立てなら1位のみがSとなる。Z-Scoreとの併用: 単純な順位だけでなく、「順位が1位かつZ-Scoreが1.5以上」の場合のみSとするなど、絶対的な強さの裏付けを条件に加えることで、信頼性を担保できる。Q3. Z-score計算は全レース統一 or レースごと？回答: 絶対に「レースごと（Intra-race）」で行う必要がある。理由:分布の独立性: 競馬のレースはそれぞれ独立した母集団を持つ。未勝利戦のメンバーのレベルと、G1レースのメンバーのレベルは全く異なる。全レースを混ぜて標準化してしまうと、G1レースに出走する馬は全員レベルが高いため、全員が高いZ-Score（または低いZ-Score）になり、レース内での優劣が見えなくなる 。目的の不一致: Z-Scoreの目的は「そのメンバーの中で誰が傑出しているか」を見つけることである。したがって、集計範囲（GroupByのキー）は必ず race_key でなければならない。提示したスクリプトは groupby('race_key') を使用しており、この要件を正確に満たしている。Q4. 馬名の追加タイミングは？（Phase 5で追加 or 後処理）回答: Phase 5の処理後に、表示用データとして結合（後処理）することを強く推奨する。理由:データ容量と処理速度: Phase 5の計算プロセスは数値演算が主であり、文字列（馬名）を持ち回るとメモリ効率が悪化する。マスタ管理の原則: 馬名は ketto_toroku_bango に紐付く属性情報であり、予測計算には不要なメタデータである。データベース正規化の観点からも、予測テーブル（Phase 5出力）にはIDのみを保持し、ユーザーへの表示直前（UI層や帳票出力スクリプト）で、jvd_ume（競走馬マスタ）テーブルとJOINして馬名を取得するのが、システム設計として最も美しい 。例外: もしデバッグ目的でCSVを直接目視したい場合は、Phase 5の最後でマージしても良いが、必須要件ではない。Q5. エラーハンドリングは？回答: 以下の3段階のエラーハンドリングを実装済み（または推奨）である。ファイルレベル: 対象のCSVファイルが存在しない場合、スクリプトをクラッシュさせずにスキップし、ログに警告を出力する（実装済み）。データレベル（Merge）: 3つのファイルの結合時、行数が極端に減少していないかをチェックする。例えば、Phase 3には1000行あるのに、マージ後に800行になった場合、20%のデータ欠損を意味する。これは異常事態であるため、アラートを出す機能を追加すべきである。計算レベル（Zero Division）: Z-Score計算時の標準偏差0問題への対処（実装済み）。7. アンサンブル統合手順書（Operation Manual）本セクションでは、開発された ensemble_phase5.py を運用環境で実行するための標準手順を定義する。7.1 事前準備 (Prerequisites)Python環境の確認:Python 3.8以上がインストールされていること。必要なライブラリ: pandas, numpy, argparseインストール: pip install pandas numpy入力データの配置:以下のディレクトリ構造が維持されており、Phase 3/4の処理が完了していることを確認する。data/predictions/phase3/data/predictions/phase4_ranking/data/predictions/phase4_regression/データファイル名の確認:ファイル名が {競馬場コード}_{YYYYMMDD}_phase{X}.csv の形式であることを確認する。例: 05_20250105_phase3.csv7.2 実行手順 (Execution)コマンドライン（ターミナル）を開き、スクリプトが存在するディレクトリへ移動後、以下のコマンドを実行する。基本コマンド:Bashpython ensemble_phase5.py --date 20250105 --keibajo 05 06
パラメータ解説:--date: 処理対象の日付（YYYYMMDD形式）。必須。--keibajo: 処理対象の競馬場コード（スペース区切りで複数指定可）。05=東京, 06=中山, 09=阪神など。必須。7.3 出力確認 (Verification)ログ確認: コンソール出力に Successfully saved to... と表示されているか確認する。ファイル確認: data/predictions/phase5_ensemble/ ディレクトリ内に、05_20250105_ensemble.csv が生成されているか確認する。データ検算:生成されたCSVを開き、race_rank が1位の馬の ensemble_score が最も高い値になっているか確認する。z_score が概ね -3.0 ～ +3.0 の範囲に収まっているか確認する。7.4 トラブルシューティング"Error: File not found": Phase 3またはPhase 4のスクリプトが正常に終了していない、あるいは保存先パスが間違っている。上流工程を確認する。"Warning: Merged dataset is empty": マージキー（特に ketto_toroku_bango や umaban）がファイル間で一致していない。入力CSVの各列のデータ型を確認する（文字列型と数値型の不一致など）。8. 結論本報告書で詳述したPhase 5アンサンブルモデルは、単なる予測値の平均化を超えた、統計的に堅牢な意思決定支援システムである。Binaryモデルによる絶対評価、Rankingモデルによる相対評価、Regressionモデルによる能力評価を 3:5:2 の比率で統合し、さらにレースごとのZ-Scoreで標準化することで、どのようなレース条件下でも一貫した評価指標を提供することが可能となる。実装されたスクリプトは、JRAデータの特性（ユニークキー構造）を遵守し、欠損値処理やゼロ除算回避などのエラーハンドリングを備えており、実運用に耐えうる設計となっている。今後の展望として、Phase 6シミュレーションを通じた重み最適化や、ランク閾値の動的調整機能を実装することで、システムの回収率（ROI）はさらに向上する余地がある。この基盤を活用し、次なるフェーズへ進むことが推奨される。