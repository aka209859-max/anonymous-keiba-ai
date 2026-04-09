# JRA版AI予想システム - 完全版コンテキスト維持プロトコル v2.0

**作成日**: 2026年02月14日  
**対象リポジトリ**: `aka209859-max/anonymous-keiba-ai-jra`（新規専用リポジトリ）  
**前提条件**: JRA-VAN + JRDB 15年分データ並行取得完了後に開発開始  

このドキュメントは、JRA版開発セッションでのコンテキスト喪失を防ぐための運用ルールと、データ取得の技術的制約を包括的に記載した決定版です。

---

## 📋 セッション開始時の必須チェックリスト

### ✅ 必読ドキュメント（優先度順）

- [ ] **このファイル（jra_context_protocol_v2_complete.md）** を熟読したか（15分）
- [ ] **JRA_NEW_SESSION_QUICKSTART.md** を読んだか（5分で全体像把握）
- [ ] **JRA_VERSION_COMPLETE_REFERENCE.md** を読んだか（完全なコード例）
- [ ] **JRA_VERSION_INSTRUCTIONS.md** を読んだか（実装手順詳細）
- [ ] **DATA_ACQUISITION_15YEARS_GUIDE.md** を読んだか（データ取得完了確認）
- [ ] 前回のセッションログ（`docs/session_log.md`）を確認したか

### ✅ 初回セッション専用チェック

- [ ] **新規リポジトリ確認**: `aka209859-max/anonymous-keiba-ai-jra` を使用していることを確認
- [ ] **データ取得完了確認**: JRA-VAN 15年分 + JRDB 15年分のダウンロード完了を確認
- [ ] **ディスク容量確認**: 最低500GB以上のSSD空き容量があることを確認
- [ ] **JRA-VAN + JRDB ハイブリッド戦略** を理解したか
- [ ] データソースの分担（JRA-VAN: 基本情報、JRDB: 独自指数）を理解したか
- [ ] 目標精度（AUC 0.85以上、回収率120%以上）を確認したか
- [ ] 10競馬場（札幌、函館、福島、新潟、東京、中山、中京、京都、阪神、小倉）を確認したか

---

## 🎯 プロジェクト固有の制約事項（絶対に忘れないこと）

### 1. リポジトリ分離戦略

```
既存リポジトリ: anonymous-keiba-ai
├─ 地方競馬用（14競馬場）
├─ 無料データソース（PC-KEIBA）
└─ Phase 0-11 実装完了

新規リポジトリ: anonymous-keiba-ai-jra ★
├─ 中央競馬用（10競馬場）
├─ 有料データソース（JRA-VAN + JRDB）
└─ Phase 0-10 実装予定
```

**❌ 絶対にやってはいけないこと:**
- 既存リポジトリのコードをそのまま流用する（データ構造が異なる）
- JRA版コードを既存リポジトリにマージする（混乱の元）

**✅ 推奨アプローチ:**
- 既存リポジトリは「参考資料」として読むのみ
- JRA版は新規リポジトリで完全独立開発

---

### 2. データソース戦略（ハイブリッド必須）

```
[JRA-VAN Data Lab] 公式データ ← 月額 2,090円
├─ 基本情報（馬名、騎手、調教師、枠番、斤量）
├─ 過去成績（着順、走破タイム、着差、通過順位）
├─ 馬場状態、天候、コース条件
├─ オッズ情報（リアルタイム + 確定）
└─ 血統情報（5代血統表）

[JRDB] 独自指数・加工データ ← 月額 3,630円（過去コメント有）
├─ IDM（総合指数） ★ 最重要
├─ タイム指数、ペース指数、上がり指数
├─ 血統評価、コース適性指数
├─ 展開予想（脚質分析）
├─ 調教指数、厩舎指数
├─ パドックコメント（テキスト）
└─ 外厩データ

【ハイブリッド効果（予測値）】
データ源       AUC     回収率   月額費用
───────────────────────────────────
JRA-VANのみ   0.73    85%      2,090円
JRDBのみ      0.79    105%     3,630円
ハイブリッド  0.85↑  120%↑   5,720円 ★
```

### 3. 技術的制約

#### ✅ データ取得の絶対ルール

1. **データ取得は二本立て必須**
   - JRA-VANのみ ❌（精度不足）
   - JRDBのみ ❌（公式データ不足）
   - **ハイブリッド（両方） ✅ 必須**

2. **取得期間: 2010年1月1日 〜 2025年12月31日（15年分）**
   - 推奨理由: ルール変遷を考慮した最適期間
   - あまりに古いデータ（1986〜2009年）は現代と乖離しノイズ化
   - 最低10年以上のデータがないとAI学習に不十分

3. **データ取得方式: 並行取得**
   - JRA-VAN取得（約30時間）とJRDB取得（約5時間）を同時実行
   - 異なるPC、または別プロセスで実行すること
   - ディスク容量: 最低500GB、推奨1TB SSD

#### ✅ 特徴量設計

1. **特徴量は70個以上必須**
   - JRA-VAN基本特徴量: 50個
   - JRDB独自指数: 20個以上
   - 合計: 70個以上

2. **芝・ダート対応必須**
   - 地方競馬（ダート主体）とは異なる
   - `track_type` カラムで区別（`turf`, `dirt`, `jump`）
   - 芝/ダート別の特徴量を追加
   - 芝専用: `straight_length`, `turf_win_rate`
   - ダート専用: `dirt_win_rate`

3. **WIN5対応必須**
   - Phase 6 で実装
   - 指定5レースのTOP3組み合わせ（3^5 = 243点）
   - キャリーオーバー考慮

---

## 🔧 データ取得の技術的詳細（超重要）

この章は、新セッションで「データ取得環境」を理解するための必読情報です。

### 🔴 JRA-VAN Data Lab: 技術的特性と制約

#### 基本情報

- **提供元**: JRAシステムサービス株式会社
- **API名称**: JV-Link（ActiveXコントロール）
- **動作環境**: Windows + 32ビットPython **必須**
- **月額料金**: 2,090円（税込、パソコン2台まで）
- **データ範囲**: 1986年〜現在（本プロジェクトでは2010年〜2025年を使用）
- **公式サイト**: https://www.jra-van.jp/

#### ⚠️ 致命的な技術制約

```
問題: JV-LinkはActiveX（32ビット専用）
      ↓
現代のPython環境は64ビットが標準
      ↓
解決策: 32ビットPython専用環境を別途構築
```

**推奨環境構築手順:**

```bash
# 1. Python 3.10の32ビット版をインストール
# ダウンロード: https://www.python.org/downloads/release/python-3109/
# ファイル名: Windows installer (32-bit)

# 2. 仮想環境作成（32ビット専用）
C:\Python310-32\python.exe -m venv C:\jra_data_env

# 3. 有効化
C:\jra_data_env\Scripts\activate

# 4. 必須ライブラリインストール
pip install pywin32 pandas sqlalchemy psycopg2-binary tqdm
```

#### データ取得実装の核心

**JVOpen のオプション指定:**

| オプション | 名称 | 用途 | 備考 |
|----------|------|------|------|
| `option=1` | 通常更新 | 差分データ取得 | 週次更新で使用 |
| `option=2` | リカバリ | 破損ファイル再取得 | エラー時 |
| `option=3` | セットアップ | **過去データ一括取得** | ⭐ 15年分取得に使用 |
| `option=4` | セットアップ自動 | ダイアログなし版 | 不安定な場合あり |

**実装コード骨子（Python 32ビット環境で実行）:**

```python
import win32com.client
import time
import pandas as pd

def download_jra_15years(start_year=2010, end_year=2025):
    """
    JRA-VAN Data Labから15年分データを年次チャンキングで取得
    """
    jv = win32com.client.Dispatch("JVDTLab.JVLink")
    jv.JVInit("UNKNOWN")
    
    all_records = []
    
    for year in range(start_year, end_year + 1):
        print(f"========== Processing Year: {year} ==========")
        from_time = f"{year}0101000000"
        
        # JVOpen: option=3（セットアップモード）
        res = jv.JVOpen('RACE', from_time, 3, 0, 0, "")
        
        if res != 0:
            print(f"❌ JVOpen Error: {res}")
            continue
        
        total_files = res
        print(f"📥 Download started. Total files: {total_files}")
        
        # ダウンロード待機ループ（JVStatus）
        while True:
            status = jv.JVStatus()
            if status == total_files:
                print(f"\n✅ Download complete: {total_files} files")
                break
            if status < 0:
                print(f"❌ Download Error: {status}")
                break
            print(f"\r📊 Downloaded: {status}/{total_files}", end="")
            time.sleep(2)
        
        # データ読み込みループ（JVRead）
        year_records = []
        while True:
            # バッファサイズ: 100KB
            ret, data = jv.JVRead("", 100000)
            
            if ret == 0:  # 全ファイル読み込み完了
                break
            elif ret == -1:  # ファイル切り替わり
                continue
            
            # レコード種別ID（先頭2バイト）
            rec_id = data[:2]
            
            # 固定長パース処理（詳細は別関数で実装）
            parsed = parse_jravan_record(rec_id, data)
            
            # 年を超えたら打ち切り
            if parsed and parsed.get('date', '').startswith(str(year + 1)):
                break
            
            year_records.append(parsed)
        
        jv.JVClose()
        
        # 年単位でCSV保存（バックアップ）
        df = pd.DataFrame(year_records)
        df.to_csv(f"data/raw/jravan_{year}.csv", index=False, encoding='utf-8-sig')
        print(f"💾 Saved: jravan_{year}.csv ({len(df)} records)")
        
        all_records.extend(year_records)
    
    # 全データをDBに格納
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///data/jravan_15years.db')
    df_all = pd.DataFrame(all_records)
    df_all.to_sql('race_results', engine, if_exists='replace', index=False)
    
    print(f"\n🎉 Complete! Total records: {len(all_records)}")
    return df_all
```

**推定所要時間: 約30時間**

#### 主要レコードID一覧

| レコードID | データ名称 | AIにおける役割 |
|-----------|----------|--------------|
| `RA` | レース詳細 | コース条件、天候、馬場状態、グレード |
| `SE` | 競走馬詳細 | 馬名、負担重量、騎手、調教師、馬体重 |
| `HR` | 競走成績 | 着順、走破タイム、着差、通過順位、上がり3F |
| `H1`-`H6` | 払戻金 | バックテストの収支計算 |
| `O1`-`O6` | オッズ | 単勝〜3連単の確定オッズ |
| `WF` | 坂路調教 | 美浦・栗東の調教タイム |
| `BLOD` | 血統 | 5代血統表 |

---

### 🔴 JRDB: 技術的特性と制約

#### 基本情報

- **提供元**: 株式会社 JRDB
- **プラン**: 「過去コメント有」プラン推奨（月額3,630円）
- **データ形式**: LZH圧縮 + Shift-JIS + 固定長テキスト
- **ダウンローダー**: 専用ツール「Ikkatsu」（一括取得）
- **公式サイト**: http://www.jrdb.com/

#### ⚠️ 技術的制約

```
問題: データがLZH圧縮（レガシー形式）
      ↓
解決策: 7-zip または lhafile ライブラリで解凍

問題: 文字コードがShift-JIS
      ↓
解決策: Python で encoding='cp932' 指定

問題: 固定長テキスト（バイトオフセット指定）
      ↓
解決策: 固定長パーサークラスを実装
```

**推奨ライブラリ:**

```bash
pip install pandas numpy sqlalchemy lhafile chardet
```

#### データ取得手順

1. **Ikkatstuダウンローダー設定**
   - JRDB会員登録 → ログイン
   - Ikkatstuをダウンロード（Windows専用）
   - 取得期間設定: 2010/01/01 〜 2025/12/31
   - 保存先: `E:\jra-keiba-data\jrdb\raw\`

2. **取得データファイル一覧（重要なもの）**

| ファイル名 | データ内容 | AIでの用途 | 容量（15年分推定） |
|----------|----------|-----------|----------------|
| `SED*.txt` | 成績データ | レース結果＋IDM | 5-10GB |
| `KYI*.txt` | 競走馬情報 | 調教指数、厩舎指数 | 3-5GB |
| `BAC*.txt` | 馬場指数 | 馬場補正 | 500MB |
| `CYB*.txt` | 調教ベスト | 調教タイム | 1GB |
| `CHA*.txt` | パドックコメント | テキストデータ | 2GB |

**推定所要時間: 約5時間**（ネットワーク速度依存）

#### 固定長パーサー実装例

```python
import pandas as pd

class FixedWidthParser:
    """
    JRDBの固定長ファイルをパースする基底クラス
    """
    def __init__(self, encoding='cp932'):
        self.encoding = encoding
        self.specs = []  # (開始位置, バイト長, 項目名, 型, スケール)
    
    def parse_line(self, line_bytes):
        """1行をパースして辞書に変換"""
        record = {}
        for start, length, name, dtype, scale in self.specs:
            chunk = line_bytes[start : start + length]
            
            try:
                text = chunk.decode(self.encoding).strip()
            except UnicodeDecodeError:
                text = chunk.decode(self.encoding, errors='replace').strip()
            
            if text == '':
                record[name] = None
            else:
                try:
                    if dtype == int:
                        record[name] = int(text)
                    elif dtype == float:
                        record[name] = float(text) * scale
                    else:
                        record[name] = text
                except ValueError:
                    record[name] = None
        return record
    
    def parse_file(self, file_path):
        """ファイル全体をパースしてDataFrameを返す"""
        records = []
        with open(file_path, 'rb') as f:
            for line in f:
                line = line.rstrip(b'\r\n')
                if not line:
                    continue
                records.append(self.parse_line(line))
        return pd.DataFrame(records)


class SedParser(FixedWidthParser):
    """SEDファイル（成績データ）専用パーサー"""
    def __init__(self):
        super().__init__()
        # ※正確なバイト位置はJRDBの仕様書を参照
        self.specs = [
            (0, 8, 'race_id', str, 1),      # レースID
            (8, 2, 'horse_no', int, 1),     # 馬番
            (10, 10, 'horse_id', str, 1),   # 血統登録番号
            (20, 3, 'idm', int, 1),         # IDM（重要）
            (23, 3, 'pace_idx', int, 1),    # ペース指数
            (26, 3, 'time_idx', int, 1),    # タイム指数
            # ... 他の項目を追加
        ]

# 使用例
parser = SedParser()
df = parser.parse_file('data/raw/SED20100105.txt')
print(df.head())
```

#### JRDB独自指数20種一覧

| 指数名 | 略称 | 説明 | 重要度 |
|-------|-----|------|--------|
| IDM | IDM | 総合能力指数（最重要） | ⭐⭐⭐⭐⭐ |
| タイム指数 | TI | 走破タイム能力 | ⭐⭐⭐⭐ |
| ペース指数 | PI | ペース適性 | ⭐⭐⭐⭐ |
| 上がり指数 | UI | 上がり3F能力 | ⭐⭐⭐ |
| 位置指数 | LSI | ポジション取り能力 | ⭐⭐⭐ |
| 調教指数 | TRI | 調教の良し悪し | ⭐⭐⭐⭐ |
| 厩舎指数 | SI | 厩舎の勝負気配 | ⭐⭐⭐⭐ |
| 前走指数 | LRI | 前走のパフォーマンス | ⭐⭐⭐ |
| 血統指数 | BI | コース適性×血統 | ⭐⭐⭐ |
| 馬場指数 | TCI | 馬場状態補正 | ⭐⭐⭐ |
| ... | ... | ... | ... |

**特に重要: IDM、調教指数、厩舎指数の3つは必須特徴量**

---

### 🔗 JRA-VAN + JRDB データ統合の技術

#### 統合キー設計（Composite Key）

両データソースは異なるID体系を持つため、以下の複合キーで結合する。

```python
# 結合キー生成
def generate_join_key(row):
    return f"{row['race_date']}_{row['place_code']}_{row['race_no']:02d}_{row['horse_no']:02d}"

# JRA-VANデータにキー追加
df_jravan['join_key'] = df_jravan.apply(generate_join_key, axis=1)

# JRDBデータにキー追加
df_jrdb['join_key'] = df_jrdb.apply(generate_join_key, axis=1)

# LEFT JOIN（JRA-VANを左側に）
df_merged = pd.merge(
    df_jravan,
    df_jrdb[['join_key', 'idm', 'training_idx', 'trainer_idx']],  # JRDB独自指数のみ
    on='join_key',
    how='left'
)
```

#### 競馬場コード変換表（マッピング）

| 競馬場 | JRA-VANコード | JRDBコード（推定） | 標準コード |
|-------|-------------|----------------|----------|
| 札幌 | `01` | `01` | `01` |
| 函館 | `02` | `02` | `02` |
| 福島 | `03` | `03` | `03` |
| 新潟 | `04` | `04` | `04` |
| 東京 | `05` | `05` | `05` |
| 中山 | `06` | `06` | `06` |
| 中京 | `07` | `07` | `07` |
| 京都 | `08` | `08` | `08` |
| 阪神 | `09` | `09` | `09` |
| 小倉 | `10` | `10` | `10` |

**もしコードが異なる場合の変換コード:**

```python
place_mapping = {
    '01': '01',  # 札幌
    '02': '02',  # 函館
    # ... 以下略
}

df_jrdb['std_place_code'] = df_jrdb['place_code'].map(place_mapping)
```

#### 統合時の注意事項

1. **欠損値の処理**
   - 出走取消馬: JRDBにデータなし → `idm=None` になる
   - INNER JOINは使わず、**必ずLEFT JOIN**を使用

2. **血統登録番号の活用**
   - 両データに共通で存在する場合は最強の結合キー
   - 馬名は表記ゆれリスクがあるため避ける

3. **データ品質チェック**
   ```python
   # 統合後の欠損率チェック
   print(df_merged['idm'].isna().sum() / len(df_merged))
   # 期待値: 5%未満（出走取消分のみ）
   ```

---

## ⏱️ 20ターンごとの確認事項

### 現在のタスク確認

1. **現在のフェーズ**: Phase X を実施中
2. **実装中の機能**: [具体的な機能名]
3. **進捗率**: X%
4. **データ取得状況**: JRA-VAN [完了/進行中/未着手] / JRDB [完了/進行中/未着手]

### 決定事項リスト

- ✅ [決定事項1]
- ✅ [決定事項2]
- ✅ [決定事項3]

### 未決事項リスト

- ❓ [未決事項1]
- ❓ [未決事項2]

### コード実装状況

```python
# 実装済みスクリプト
scripts/phase0_data_acquisition/download_jravan_15years.py  # ✅
scripts/phase0_data_acquisition/download_jrdb_15years.py    # ✅
scripts/phase0_data_acquisition/merge_jravan_jrdb.py        # 🔄 実装中
scripts/phase1_feature_engineering/prepare_features_jra.py  # ❌ 未着手
scripts/phase3_binary/predict_phase3_inference_jra.py       # ❌ 未着手
```

---

## 📝 セッション終了時のプロトコル

### 1. 作業内容を記録

```bash
# session_log.md に追記
echo "## セッション $(date +%Y-%m-%d)

### 完了タスク
- Phase X の Y 実装完了

### 決定事項
- [決定事項1]
- [決定事項2]

### 次回タスク
- Phase X+1 の実装開始

### データ取得状況
- JRA-VAN: [完了/進行中] XX%
- JRDB: [完了/進行中] XX%
" >> docs/session_log.md
```

### 2. Gitコミット（必須）

```bash
# 必ずcommit → push
git add .
git commit -m "feat(phaseX): [実装内容の簡潔な説明]

- [変更点1]
- [変更点2]
- [変更点3]"

git push origin main
```

### 3. 次回のタスクを明示

```markdown
## 次回セッション開始時のタスク

1. Phase X+1 の実装開始
2. [具体的なタスク1]
3. [具体的なタスク2]

### 必要なファイル
- jra_context_protocol_v2_complete.md（このファイル）
- JRA_VERSION_COMPLETE_REFERENCE.md（Phase X+1 のセクション）
- docs/session_log.md（前回の作業内容）
```

---

## 🚨 コンテキストの腐敗（Context Rot）の兆候

以下の症状が出たら、**即座にセッションをリセット**すること:

### 🔴 重大な兆候（絶対に見逃してはいけない）

- ❌ **リポジトリを間違えている**
  - 例: "anonymous-keiba-ai で開発しています"
  - 正: "anonymous-keiba-ai-jra で開発しています"

- ❌ **JRA-VAN + JRDB ハイブリッド戦略を忘れている**
  - 例: "JRA-VANだけで十分では？"
  - 例: "JRDBは使わない方針にしましょう"
  
- ❌ **データソースの分担を忘れている**
  - 例: JRDBから基本情報を取得しようとする
  - 例: JRA-VANから独自指数を取得しようとする

- ❌ **データ取得完了を確認していない**
  - 例: "Phase 1 から始めましょう"（データがないのに）
  - 正: "データ取得状況を確認します。15年分取得完了していますか？"

- ❌ **目標精度を忘れている**
  - 例: "AUC 0.75で十分では？"（目標は0.85以上）
  - 例: "回収率100%で良いですね"（目標は120%以上）

- ❌ **10競馬場を忘れている**
  - 例: 地方競馬場（門別、船橋など）を含めようとする
  - 例: 競馬場数を14場と言及する

### ⚠️ 一般的な兆候

- ❌ 以前の決定事項を忘れている
- ❌ 制約条件を無視し始める
- ❌ 本来の目的（JRA版AI予想システム構築）から逸脱する
- ❌ 同じ質問を繰り返す
- ❌ Phase 0-10 の実装順序を無視する
- ❌ データ取得の技術的制約を無視する（32ビットPython、LZH解凍など）

---

## 🔧 緊急時の復旧手順

### コンテキスト喪失を検知した場合

1. **現在のセッションを終了**
   - 作業内容を `docs/session_log.md` に記録
   - 未コミットの変更をコミット

2. **新しいセッションを開始**
   - 以下の5ファイルを添付:
     1. `docs/jra_context_protocol_v2_complete.md` ⭐ このファイル
     2. `JRA_NEW_SESSION_QUICKSTART.md`
     3. `JRA_VERSION_COMPLETE_REFERENCE.md`
     4. `JRA_VERSION_INSTRUCTIONS.md`
     5. `DATA_ACQUISITION_15YEARS_GUIDE.md`

3. **コンテキスト再読込**
   - 新規セッションテンプレートを使用
   - このファイルを最初に熟読（15分）
   - `docs/session_log.md` で前回の作業内容を確認

4. **作業再開**
   - 前回の続きから実装を再開

---

## 📚 重要なリファレンス

### データソース関連

- **JRA-VAN Data Lab**: 公式データ（基本情報、オッズ）
  - 技術: JV-Link (ActiveX)、32ビットPython必須
  - 月額: 2,090円
  - 取得時間: 約30時間（15年分）

- **JRDB**: 独自指数（IDM、タイム指数、ペース指数など20指数）
  - 技術: LZH圧縮、Shift-JIS、固定長テキスト
  - 月額: 3,630円（過去コメント有プラン）
  - 取得時間: 約5時間（15年分）

- **ハイブリッド効果**: AUC +16%、回収率 +41%

### 技術スタック

- **データ取得**:
  - JRA-VAN: Python 3.10 (32ビット) + pywin32
  - JRDB: Python 3.14 (64ビット) + lhafile/7-zip

- **AI開発**:
  - Python 3.14
  - LightGBM（二値分類、Ranker、Regressor）
  - Optuna（自動最適化）
  - Kelly基準（資金管理）

### 実装フェーズ

```
Phase 0: JRA-VAN + JRDB ハイブリッドデータ取得（15年分）★
Phase 1: 70特徴量エンジニアリング
Phase 2: 学習データ準備（2010-2025年）
Phase 3: 二値分類（AUC 0.85以上目標）
Phase 4-1: ランキング予測
Phase 4-2: 回帰予測
Phase 5: アンサンブル統合（30/50/20%）
Phase 6: WIN5対応買い目生成
Phase 7: Greedy Boruta特徴量選択
Phase 8: Optuna自動最適化
Phase 9: Kelly基準ベッティングエンジン
Phase 10: バックテスト・ROI検証
```

---

## 🎯 セッション品質チェック

### 毎回確認すべき質問

1. **リポジトリを正しく認識しているか？**
   - 回答: `aka209859-max/anonymous-keiba-ai-jra` を使用している

2. **データ取得完了を確認したか？**
   - 回答: JRA-VAN 15年分 [完了/進行中/未着手]、JRDB 15年分 [完了/進行中/未着手]

3. **データソース戦略を理解しているか？**
   - JRA-VANとJRDBの役割分担を説明できるか？

4. **目標精度を覚えているか？**
   - AUC: 0.85以上、回収率: 120%以上

5. **実装フェーズの順序を守っているか？**
   - Phase 0（データ取得完了）→ Phase 1 → ... → Phase 10

6. **JRA固有の要件を理解しているか？**
   - 芝・ダート対応
   - WIN5対応
   - 10競馬場対応

7. **技術的制約を理解しているか？**
   - JRA-VAN: 32ビットPython必須
   - JRDB: LZH解凍、Shift-JIS、固定長パース

8. **コードの実装例を参照しているか？**
   - `JRA_VERSION_COMPLETE_REFERENCE.md` を活用しているか？

---

## 📖 関連ドキュメント

### 必須ドキュメント

- **jra_context_protocol_v2_complete.md** ⭐ このファイル（完全版）
- **JRA_NEW_SESSION_QUICKSTART.md** - クイックスタート（5分）
- **JRA_VERSION_COMPLETE_REFERENCE.md** - 完全リファレンス（47 KB）
- **JRA_VERSION_INSTRUCTIONS.md** - 実装指示書（23 KB）
- **DATA_ACQUISITION_15YEARS_GUIDE.md** - データ取得ガイド（新規作成予定）

### 参考ドキュメント

- **docs/session_log.md** - セッション履歴
- **README.md** - プロジェクト概要
- **JRAVAN_DATA_DOWNLOAD_SEARCH_QUERY.md** - JRA-VAN詳細調査
- **JRDB_DATA_DOWNLOAD_SEARCH_QUERY.md** - JRDB詳細調査

---

## 📊 ディレクトリ構造（推奨）

```
anonymous-keiba-ai-jra/
├─ data/
│  ├─ raw/
│  │  ├─ jravan/
│  │  │  ├─ jravan_2010.csv
│  │  │  ├─ jravan_2011.csv
│  │  │  └─ ... （2025まで）
│  │  └─ jrdb/
│  │     ├─ SED20100105.txt
│  │     ├─ KYI20100105.txt
│  │     └─ ... （解凍後のテキスト）
│  ├─ processed/
│  │  ├─ jravan_15years.db （SQLite）
│  │  └─ jrdb_15years.db （SQLite）
│  ├─ merged/
│  │  └─ jra_master_15years.db ★ 統合DB
│  ├─ features/
│  ├─ predictions/
│  └─ training/
├─ scripts/
│  ├─ phase0_data_acquisition/
│  │  ├─ download_jravan_15years.py ★
│  │  ├─ download_jrdb_15years.py ★
│  │  └─ merge_jravan_jrdb.py ★
│  ├─ phase1_feature_engineering/
│  ├─ phase3_binary/
│  ├─ phase4_ranking/
│  ├─ phase4_regression/
│  ├─ phase5_ensemble/
│  ├─ phase6_betting/
│  ├─ phase7_feature_selection/
│  ├─ phase8_auto_tuning/
│  ├─ phase9_betting_strategy/
│  └─ phase10_backtest/
├─ models/
│  ├─ binary/ （10競馬場別）
│  ├─ ranking/
│  └─ regression/
├─ docs/
│  ├─ jra_context_protocol_v2_complete.md ⭐
│  ├─ session_log.md
│  └─ ...
├─ tests/
├─ config/
│  └─ config.yaml
├─ README.md
├─ requirements.txt
└─ .gitignore
```

---

## 🔥 最重要事項まとめ（絶対に忘れないこと）

### ✅ 必須確認事項

1. **リポジトリ**: `aka209859-max/anonymous-keiba-ai-jra` ★
2. **データ取得**: JRA-VAN 15年分 + JRDB 15年分 **並行取得**
3. **開発開始条件**: 15年分データ取得完了後
4. **ハイブリッド戦略**: JRA-VAN（基本情報） + JRDB（独自指数）
5. **目標精度**: AUC ≥ 0.85、回収率 ≥ 120%
6. **10競馬場**: 札幌、函館、福島、新潟、東京、中山、中京、京都、阪神、小倉
7. **特徴量**: 70個以上（JRA-VAN 50 + JRDB 20）
8. **技術制約**:
   - JRA-VAN: 32ビットPython + pywin32
   - JRDB: LZH解凍 + Shift-JIS + 固定長パース

---

**最終更新**: 2026年02月14日  
**バージョン**: 2.0 完全版  
**ステータス**: ✅ 完成  
**対象リポジトリ**: `aka209859-max/anonymous-keiba-ai-jra`

---

**🚨 このファイルを必ず新規セッションで最初に読み込んでください！**
