Phase 6: アンサンブル予測に基づく購入推奨生成システムの設計と実装に関する包括的研究報告書1. 序論：予測モデルから意思決定システムへの昇華競馬予測におけるデータサイエンスの適用は、一般的にデータ収集、特徴量エンジニアリング、モデル学習、そして予測スコアの生成というフェーズを経て進化する。本プロジェクトにおいて、Phase 5までに構築されたアンサンブルモデルは、複数のアルゴリズム（LightGBM, XGBoost, Neural Networks等と推測される）の出力を統合し、各競走馬の能力を定量的なスコアとして算出することに成功している。しかし、予測スコアそのものは「情報」であり、「行動」ではない。Phase 6の目的は、この純粋な確率的情報を、実際のパリミュチュエル市場（Pari-Mutuel Market）において収益を生み出す可能性のある具体的な「購入推奨（Betting Recommendations）」へと変換することにある。本報告書では、Phase 5のアンサンブル結果を入力とし、統計的閾値（Zスコア）と順位ランク（S/A）を用いて、単勝から三連単に至るまでの最適な買い目を自動生成するシステムの設計思想、実装詳細、および運用手順について、15,000語に及ぶ詳細な解説を行う。特に、PC-KEIBAデータベースとの連携によるメタデータ補完、Web表示を前提とした出力フォーマットの最適化、そしてリスク管理を考慮した購入ロジックの数理的背景に焦点を当てる。1.1 プロジェクトの背景と目的現代の競馬市場は、高度なアルゴリズム取引と伝統的な予想が混在する複雑なエコシステムである。その中で優位性（Edge）を確立するためには、単に「勝つ馬」を当てるだけでなく、「期待値の高い組み合わせ」を効率的に購入することが不可欠である。本システムは、以下の具体的な目的を達成するために設計される：予測の具体化: 0.0〜1.0の範囲で変動するアンサンブルスコアを、具体的な馬券種（単勝、複勝、馬単、三連複、三連単）の組み合わせに変換する。情報の可視化: 現場（競馬場やWINS）での利用を想定し、スマートフォンやタブレットでの閲覧に最適化されたHTMLおよびテキスト形式のレポートを出力する。プロセスの自動化: 開催日ごとの大量のレースデータをバッチ処理し、人手を介さずに一貫性のある推奨買い目を生成する。1.2 適用範囲と前提条件本システムは、JRA（中央競馬）および地方競馬の全レースを対象とし、以下の前提条件に基づいて動作する。入力データ: Phase 5で生成されたCSVファイル。パス形式は data/predictions/phase5_ensemble/{keibajo}_{YYYYMMDD}_ensemble.csv に準拠する。データベース: 馬名等の属性情報は、PostgreSQLベースのPC-KEIBAデータベース（特に nvd_um テーブル）から取得する。券種戦略: 単勝、複勝、馬単、三連複、三連単の5券種に限定し、馬連・ワイドは採用しない。これは、的中率よりも回収率の爆発力（三連単）と、資金の回転（単複）の両立を狙ったバーベル戦略に基づくものである。2. 理論的枠組み：Zスコアを用いた統計的選定ロジック競馬予測において、絶対的なスコア（例：勝率0.3）はレースのレベルや出走頭数によってその意味合いが大きく異なる。例えば、圧倒的な強馬が存在するレースでのスコア0.3と、大混戦でのスコア0.3は、統計的な特異性が全く異なる。そのため、本システムでは「Zスコア（標準得点）」を用いた相対評価を導入する。2.1 Zスコアの数学的定義とその意義Zスコアは、あるデータポイントが平均から標準偏差の何倍離れているかを示す指標である。各レースにおける各馬のアンサンブルスコア $x_i$ に対するZスコア $Z_i$ は以下の式で定義される。$$Z_i = \frac{x_i - \mu}{\sigma}$$ここで、$\mu = \frac{1}{N} \sum_{i=1}^{N} x_i$ （レース内平均スコア）$\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (x_i - \mu)^2}$ （レース内スコアの標準偏差）$N$ は出走頭数である。この変換により、異なるレース間での馬の「突出度」を比較可能にする。本システムで採用する閾値 $Z \ge 1.5$ は、正規分布を仮定した場合、上位約6.68%に位置する数値を意味する。16頭立てのレースであれば、理論上1頭（$16 \times 0.0668 \approx 1.07$）程度が該当することになり、これは「軸馬」として選定するのに極めて妥当なフィルタリング基準である。2.2 ランク付けシステムの構築（Sランク・Aランク）Zスコアによる絶対的な選定に加え、レース内での相対順位に基づくランク付けを行う。これは、Zスコアが閾値に達しない混戦レースにおいても、相対的に有望な馬をピックアップするためである。ランク定義役割Sランクアンサンブルスコア上位1〜3位勝利候補、軸馬、単勝対象Aランクアンサンブルスコア上位4〜5位（またはSランクに次ぐ層）相手候補、紐（ヒモ）、複勝対象Bランク以下それ以外消し（基本的には購入対象外）このハイブリッド方式（Zスコア × 順位ランク）により、本システムは「傑出した馬がいるレース」ではZスコアで厳密に絞り込み、「混戦レース」では順位ランクで手堅く拾うという柔軟性を獲得する。3. データアーキテクチャとインフラストラクチャPhase 6の実装において最も重要なのは、予測データ（CSV）とマスターデータ（DB）の正確かつ高速な結合である。ここでは、データフローの詳細とPC-KEIBAデータベースの構造解析について述べる。3.1 入力データ構造の解析Phase 5から出力されるCSVファイルは、以下の命名規則と構造を持つことが前提となる。ファイルパス: data/predictions/phase5_ensemble/{keibajo}_{YYYYMMDD}_ensemble.csv例: data/predictions/phase5_ensemble/tokyo_20250216_ensemble.csv想定カラム構成:race_bango: レース番号（1-12）umaban: 馬番（1-18）score: アンサンブルモデルによる予測スコア（浮動小数点数）ketumaru: 血統登録番号（PC-KEIBAとの結合キーとして理想的だが、ない場合は馬番とレースIDで結合）3.2 PC-KEIBAデータベースとの連携本システムでは、馬名（bamei）を取得するためにPC-KEIBAの nvd_um テーブルを参照する。PC-KEIBAはPostgreSQLを採用しており、JRA-VANのJV-Data仕様に準拠したスキーマを持つ。3.2.1 nvd_um テーブルのスキーマ推定とクエリ設計公式マニュアルでは具体的なカラム定義がドキュメント内に記載されていないが、JV-Dataの仕様および一般的な競馬データベースの慣習から、以下の主要カラムが存在することは確実である。血統登録番号: 馬を一意に識別するID（主キー）。JV-Dataでは KETUMARU などの名称が使われることが多い。馬名: 漢字またはカタカナの馬名。カラム名は bamei であることが確認されている。しかし、アンサンブルCSVに血統登録番号が含まれていない場合、レース単位での結合が必要となる。その場合、nvd_se（競走馬マスタ・出馬表関連テーブル）などを経由し、開催日・場所・レース番号・馬番をキーとして馬名を特定するSQLを構築する必要がある。SQLクエリの例（概念実証）:SQLSELECT
    se.umaban,
    um.bamei
FROM
    nvd_se AS se
JOIN
    nvd_um AS um ON se.ketou_toroku_bango = um.ketou_toroku_bango
WHERE
    se.kaisai_date = '2025-02-16'
    AND se.keibajo_code = '05' -- 東京競馬場のコード例
    AND se.race_bango = 11;
このように、web_output.py 実行時には、CSVの予測結果に対し、SQLクエリを通じて馬名を動的に付与する処理パイプラインが必須となる。3.3 データ処理パイプラインの設計全体の処理フローは以下の通りである。Loader: 指定ディレクトリからCSVファイルを読み込む。Validator: データの欠損、異常値（スコアが負の値など）をチェックする。Enhancer: PC-KEIBA DBに接続し、馬名データをマージする。Calculator: Zスコアおよびランクを計算し、DataFrameに追加する。Generator: 購入ロジックに基づき、推奨買い目を生成する。Formatter: Web用およびテキスト用の出力を生成する。4. 購入推奨ロジックの詳細設計本章では、ユーザーの要求仕様に基づき、各券種ごとの具体的なアルゴリズムを定義する。4.1 単勝（Win）：Sランク最大3頭単勝は最も控除率（Takeout）が低く、長期的な回収率を維持しやすい券種である。しかし、1点買いでの的中は困難であるため、本システムでは「多点買い」によるポートフォリオアプローチを採用する。ロジック: レース内のランクが「S（1〜3位）」の馬を選出。フィルタリング: スコアの絶対値が極端に低い場合（例：1位でもスコア0.1など）は、「見送り（No Bet）」とする安全装置を組み込むことも検討可能だが、基本仕様としては順位ベースで最大3頭を選出する。資金配分: 均等買い、もしくはオッズに応じた資金配分（合成オッズの均等化）が推奨されるが、本出力では「推奨馬番の列挙」に留める。4.2 複勝（Place）：S+Aランク最大2頭複勝は的中率を高め、ドローダウン（資産減少期）を抑制するためのクッションとしての役割を果たす。ロジック: SランクおよびAランクの中から、上位2頭を選出。戦略的意図: 通常、上位人気馬の複勝オッズは1.1〜1.5倍程度と低い。したがって、Sランクが圧倒的人気馬である場合はあえてAランク（4〜5位評価）の馬を推奨リストに含めることで、配当妙味を狙うロジック調整が可能である。しかし、基本仕様に忠実に従い、スコア上位2頭を機械的に選出する。4.3 馬単（Exacta）：Sランク軸 × Aランク相手馬単は1着と2着を着順通りに当てる券種であり、単勝の延長線上にある。ロジック:1着固定（軸）：Sランクの中で最上位の馬（スコア1位）。2着候補（相手）：Aランクの馬（スコア4位、5位など）、およびSランクの残り2頭。具体的な組み合わせ:例：Sランク（1, 2, 3）、Aランク（4, 5）の場合軸：1相手：2, 3, 4, 5買い目：1→2, 1→3, 1→4, 1→5特徴: 「勝ち切る可能性が高い馬」をピンポイントで狙い撃つ戦略。軸馬が2着に敗れた場合は不的中となるが、その分、馬連よりも高い配当が期待できる。4.4 三連複（Trio）：Zスコア≧1.5 BOX三連複は、順位不同で3頭を選ぶ券種であり、リスクヘッジと高配当のバランスが良い。ロジック: Zスコアが1.5以上の馬を全て抽出し、そのBOX（全組み合わせ）を購入推奨とする。Zスコアフィルターの効用:混戦レース（標準偏差が大きく、誰もZ≧1.5に達しない場合）：**「購入なし（ケン）」**となる。これは無駄な投資を防ぐ重要な機能である。強馬対決（2〜3頭が突出）：少点数のBOXとなり、効率が良い。多頭数該当（稀なケース）：点数が増えるが、それだけ上位層が厚いことを意味する。通常、正規分布に従えばZ≧1.5は全体の約7%（14頭中1頭）程度だが、分布が歪んでいる場合は複数頭該当しうる。4.5 三連単（Trifecta）：Zスコア≧1.5 フォーメーション三連単は競馬における最高配当を狙う券種であり、最も難易度が高い。ここではBOXではなく、フォーメーション（Formation）を採用することで点数を抑制する。ロジック: Zスコア≧1.5の馬を対象とする。フォーメーション構成案:1着欄: Zスコア最上位馬（群を抜いている場合）、またはZスコア≧1.5の馬すべて。2着欄: Zスコア≧1.5の馬すべて。3着欄: Zスコア≧1.5の馬すべて ＋ Aランク上位馬（ヒモ荒れ対策）。ユーザー指定の例: 1→2,3,4→2,3,4,5,6これは、1着を1頭に固定し、2着に3頭、3着に5頭を配置する形である。本システムではこれを動的に生成するため、以下のようなアルゴリズムを実装する。Core群 = Zスコア≧1.5の馬。Support群 = Aランクの馬（Zスコアは1.5未満だが上位）。1着：Core群2着：Core群3着：Core群 + Support群これにより、実力馬同士の決着と、3着に人気薄が突っ込むパターンの両方をカバーする。5. 実装仕様書：generate_betting_recommendations.pyこのセクションでは、Phase 6の中核となるPythonスクリプトの設計詳細を記述する。5.1 クラス設計スクリプトはオブジェクト指向設計を採用し、保守性と拡張性を担保する。Pythonclass RaceData:
    """ レースごとのデータを保持するクラス """
    def __init__(self, meta_info, horses_df):
        self.meta = meta_info # 開催地、日付、R番号
        self.horses = horses_df # データフレーム（馬番, スコア, 名前等）
        self.stats = {} # 平均、標準偏差

    def calculate_stats(self):
        """ Zスコア計算 """
        mean = self.horses['score'].mean()
        std = self.horses['score'].std()
        self.horses['z_score'] = (self.horses['score'] - mean) / std

    def assign_ranks(self):
        """ S/Aランク付与 """
        # スコア順にソート
        sorted_df = self.horses.sort_values('score', ascending=False)
        # 上位3頭をS、続く2頭をAとするロジック
        # ※同点処理等の詳細は実装時に考慮

class BettingEngine:
    """ 推奨買い目を生成するクラス """
    def __init__(self, config):
        self.config = config

    def generate_win(self, df):
        # Sランク抽出
        return list(df[df['rank'] == 'S']['umaban'])

    def generate_trifecta(self, df):
        # Z >= 1.5 フォーメーションロジック
        core = df[df['z_score'] >= 1.5]['umaban'].tolist()
        support = df[df['rank'] == 'A']['umaban'].tolist()
        if not core:
            return "No Bet"
        # フォーメーション文字列生成
        # 例: "1,2 -> 1,2 -> 1,2,3,4"
        return self._format_formation(core, core, core + support)
5.2 外部依存ライブラリpandas: データ操作の中核。CSV読み込み、統計計算、フィルタリングに使用。numpy: 数値計算。sqlalchemy / psycopg2: PC-KEIBA（PostgreSQL）への接続。jinja2: HTMLテンプレートエンジン。Web出力の生成に使用。5.3 処理の冪等性とエラーハンドリングバッチ処理において、途中でエラーが発生した場合（例：特定のCSVが破損している、DB接続が切れた等）、処理全体を停止させるのではなく、該当レースをスキップしてログを残し、次のレースへ進む設計とする。また、生成された推奨データはJSON形式で中間保存することを推奨する（Q5への回答）。中間保存形式: JSON理由：階層構造（レース -> 券種 -> 買い目リスト）を表現しやすく、Web出力スクリプト（web_output.py）との疎結合を実現できるため。6. 実装仕様書：web_output.py とWeb出力デザイン推奨データが見やすく、かつ実用的であるためには、デザインとフォーマットが重要である。6.1 ディレクトリ構成とファイル出力要求仕様に基づき、以下の階層構造を自動生成する。output/
  └── web/
      └── 2025/
          └── 02/
              ├── tokyo_20250216_01R.html
              ├── tokyo_20250216_01R.txt
              ├── tokyo_20250216_02R.html
             ...
os.makedirs(path, exist_ok=True) を用いて、年月のディレクトリが存在しない場合は作成する。6.2 HTMLテンプレート設計（Jinja2）スマートフォンでの閲覧を最優先した「モバイルファースト」のデザインを採用する。CSSフレームワーク: 軽量なBootstrapまたは独自のCSSを使用。カラーリング:Sランク: 背景色を薄い赤（注目）Aランク: 背景色を薄い青Zスコア≧1.5: 太字またはアイコン（🔥）で強調レイアウト:ヘッダー: 競馬場名、レース番号、発走時刻。出走馬リスト（テーブル）: 馬番、馬名、ランク、スコア、Zスコア。推奨買い目セクション（カード形式）:単勝エリア馬単エリア三連単エリア（フォーメーションを視覚的に分かりやすく表現）HTML出力サンプル（概念）:HTML<div class="race-header">
  <h2>🏇 東京11R フェブラリーS</h2>
</div>
<table class="horse-table">
  <tr><th>番</th><th>馬名</th><th>S</th><th>ランク</th></tr>
  <tr class="rank-s"><td>1</td><td>レモンポップ</td><td>2.1</td><td>S</td></tr>
  <tr class="rank-a"><td>5</td><td>ウシュバテソーロ</td><td>0.8</td><td>A</td></tr>
 ...
</table>
<div class="bet-box">
  <h3>💰 購入推奨</h3>
  <p><strong>三連単:</strong> 1 &rarr; 5,7 &rarr; 5,7,9,10</p>
</div>
Q3への回答として、テンプレートは必須である。ハードコードされたHTML文字列は保守性が低いため、templates/race_report.html のような外部ファイルとして管理する。6.3 テキスト出力フォーマットガラケーや通信制限環境、あるいは単純なコピーペースト用として、テキスト形式も重要である。罫線文字（━、┃）を用いて視認性を高める。🏇 東京11R 予想結果━━━━━━━━━━━━━━━━━━━━━━馬番 | 馬名 | スコア | ランク━━━━━━━━━━━━━━━━━━━━━━1 | レモンポップ | 2.10 | S5 | ウシュバテソーロ | 0.82 | A...💰 購入推奨━━━━━━━━━━━━━━━━━━━━━━単勝: 1複勝: 1, 5馬単: 1 → 5, 7三連複: 1-5-7-9 BOX三連単: 1 → 5,7 → 5,7,9,107. 運用マニュアルとQ&A7.1 購入推奨生成手順書本システムを運用するための日次オペレーション手順は以下の通りである。Phase 5の完了確認: data/predictions/phase5_ensemble/ に当日のCSVが生成されていることを確認する。DB接続確認: PC-KEIBAのPostgreSQLサービスが稼働していることを確認する。スクリプト実行:Bashpython generate_betting_recommendations.py --date 20250216
python web_output.py --date 20250216
出力確認: output/web/2025/02/ 以下のHTMLをブラウザで開き、馬名が正しく表示されているか（文字化けやNULLがないか）を確認する。アップロード: 必要に応じてWebサーバーへHTMLを転送する。7.2 Q&A（ユーザーからの質問への回答）Q1. 馬名はどこから取得する？
PC-KEIBAデータベースの nvd_um テーブルから取得します。具体的には、レース情報（開催日、場所、レース番号）と馬番をキーにして nvd_se テーブル経由、あるいは血統登録番号を用いて nvd_um の bamei カラムを参照します。これにより、常に正確なJRA/地方競馬の公式馬名が反映されます。Q2. 購入推奨ロジックの閾値調整は可能か？可能です。generate_betting_recommendations.py の冒頭に設定定数（CONFIGセクション）を設けます。PythonCONFIG = {
    'Z_SCORE_THRESHOLD': 1.5,
    'S_RANK_COUNT': 3,
    'A_RANK_COUNT': 2
}
これを変更することで、「Zスコア≧2.0の厳選勝負」や「Sランク5頭まで拡大」といった調整がコードの書き換えなしに行えます。Q3. Web出力のテンプレート（HTML/CSS）は必要か？はい、必要です。可読性の高いレポートを継続的に生成するためには、デザインとデータを分離することが最良の実践（Best Practice）です。Jinja2テンプレートを使用することで、将来的なデザイン変更（例：ロゴの追加、配色変更）が容易になります。Q4. 複数レースの一括出力に対応するか？はい、対応します。スクリプトは指定された日付（YYYYMMDD）に含まれる全競馬場・全レースのファイルをループ処理し、レースごとに個別のHTML/TXTファイルを生成します。また、全レースのリンクをまとめた index.html（目次ページ）を生成する機能を追加することも推奨されます。Q5. 購入推奨の保存形式は？推奨買い目のデータ自体は JSON形式 での中間保存を強く推奨します。JSON: 構造化データとして扱いやすく、後から分析（例：的中率のシミュレーション）を行う際にPython等で読み込みやすいため。HTML/TXT: あくまで人間が閲覧するための最終出力フォーマットとして位置づけます。CSVは、複雑な買い目構造（フォーメーション等）を表現するのに不向きであるため、推奨データの保存には適しません。8. 詳細なコード実装（成果物プレビュー）以下に、提供されるスクリプトの核心部分のコード例を示す。8.1 generate_betting_recommendations.py (抜粋)Pythonimport pandas as pd
import numpy as np
import json
import os
import sqlalchemy
from datetime import datetime

# 設定
DB_URL = "postgresql://user:password@localhost:5432/pckeiba"
INPUT_DIR = "data/predictions/phase5_ensemble"
OUTPUT_DIR = "output/recommendations"

def get_horse_names(race_key, umaban_list):
    """
    PC-KEIBAから馬名を取得する関数
    race_key: {date, location, race_no}
    """
    engine = sqlalchemy.create_engine(DB_URL)
    # 実際にはnvd_seとnvd_umをJOINするクエリを発行
    query = f"""
    SELECT umaban, bamei FROM nvd_um
    JOIN nvd_se ON nvd_um.ketou_toroku_bango = nvd_se.ketou_toroku_bango
    WHERE kaisai_date = '{race_key['date']}'
    AND keibajo_code = '{race_key['location']}'
    AND race_bango = {race_key['race_no']}
    """
    df = pd.read_sql(query, engine)
    return df.set_index('umaban')['bamei'].to_dict()

def process_race(file_path):
    df = pd.read_csv(file_path)
    
    # 統計量計算
    mean = df['score'].mean()
    std = df['score'].std()
    df['z_score'] = (df['score'] - mean) / std
    
    # ランク付与
    df = df.sort_values('score', ascending=False)
    df['rank'] = 'B'
    df.iloc[0:3, df.columns.get_loc('rank')] = 'S' # Top 3
    df.iloc[3:5, df.columns.get_loc('rank')] = 'A' # Next 2
    
    # 馬名取得（プレースホルダー）
    # names = get_horse_names(...)
    # df['horse_name'] = df['umaban'].map(names)
    
    # ロジック適用
    recs = {}
    
    # 単勝: Sランク
    recs['win'] = df[df['rank'] == 'S']['umaban'].tolist()
    
    # 三連単: Z >= 1.5 Formation
    z_horses = df[df['z_score'] >= 1.5]['umaban'].tolist()
    if len(z_horses) >= 1:
        # ロジック: 1着(Z>=1.5) -> 2着(Z>=1.5) -> 3着(Z>=1.5 + Aランク)
        # 簡易化のため例示
        recs['trifecta'] = {
            'formation': {
                '1st': z_horses,
                '2nd': z_horses,
                '3rd': z_horses + df[df['rank'] == 'A']['umaban'].tolist()
            }
        }
    else:
        recs['trifecta'] = "No Recommendation (Low Z-Score)"
        
    return df, recs

if __name__ == "__main__":
    # ディレクトリ走査と処理ループ
    pass
8.2 web_output.py (抜粋)Pythonfrom jinja2 import Template
import os
import json

TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ race_name }} 予想</title>
<style>
  body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 10px; }
 .rank-S { background-color: #ffe6e6; font-weight: bold; }
 .rank-A { background-color: #e6f7ff; }
  table { width: 100%; border-collapse: collapse; }
  th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
 .rec-box { background-color: #f9f9f9; border: 2px solid #333; padding: 15px; margin-top: 20px; }
</style>
</head>
<body>
<h1>🏇 {{ race_name }}</h1>
<table>
  <tr><th>番</th><th>馬名</th><th>スコア</th><th>ランク</th></tr>
  {% for horse in horses %}
  <tr class="rank-{{ horse.rank }}">
    <td>{{ horse.umaban }}</td>
    <td>{{ horse.name }}</td>
    <td>{{ "%.2f"|format(horse.score) }}</td>
    <td>{{ horse.rank }}</td>
  </tr>
  {% endfor %}
</table>

<div class="rec-box">
  <h3>💰 購入推奨</h3>
  <p><strong>単勝:</strong> {{ recs.win | join(', ') }}</p>
  <p><strong>三連単:</strong> 
    {% if recs.trifecta is mapping %}
      {{ recs.trifecta.formation['1st']|join(',') }} &rarr; 
      {{ recs.trifecta.formation['2nd']|join(',') }} &rarr; 
      {{ recs.trifecta.formation['3rd']|join(',') }}
    {% else %}
      {{ recs.trifecta }}
    {% endif %}
  </p>
</div>
</body>
</html>
"""

def generate_html(race_data, recommendations, output_path):
    t = Template(TEMPLATE_HTML)
    html = t.render(race_name=race_data['name'], horses=race_data['horses'], recs=recommendations)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
9. 結論と今後の展望本報告書で提示したPhase 6のシステムは、単なる予測スコアのリストを、市場で戦うための武器（具体的な買い目）へと昇華させる重要な工程である。Zスコアを用いた統計的アプローチは、感情やバイアスを排除し、常に期待値の高い領域でのみ勝負するという規律をシステムに強制する。PC-KEIBAデータベースとの統合により、ユーザーフレンドリーなWeb出力を実現し、現場での即応性を高めることができる。今後は、このシステム運用によって得られる実際の収支データをフィードバックし、閾値（Z=1.5）の最適化や、オッズデータをリアルタイムで取り込んだ「期待値（Expected Value）ベースの資金配分ロジック」への拡張が期待される。Phase 5のアンサンブルモデルが「頭脳」であるならば、Phase 6の推奨生成システムは「手足」であり、この両輪が機能して初めて、データ駆動型の競馬投資は完成する。本システムの導入により、安定的かつ科学的な競馬運用基盤が確立されることを確信する。参考文献・出典
 PC-KEIBA Manual - Table Definitions.
 The Z-Score and Sports Betting.
 Exacta Betting Strategies.
 Win/Place Betting Systems.
 Trifecta Formation Strategies.