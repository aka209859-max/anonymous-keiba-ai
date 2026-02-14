# JRA版AI予測システム Phase 0 クイックスタートガイド

**作成日**: 2026-02-14  
**対象リポジトリ**: aka209859-max/anonymous-keiba-ai-jra  
**所要時間**: データ取得 約30時間 + DB構築 数時間

---

## 📋 目次

1. [新セッション開始時の必須手順](#新セッション開始時の必須手順)
2. [環境セットアップ](#環境セットアップ)
3. [Phase 0 実行手順](#phase-0-実行手順)
4. [トラブルシューティング](#トラブルシューティング)
5. [次のフェーズへ](#次のフェーズへ)

---

## 新セッション開始時の必須手順

### ✅ 新セッションで最初に読み込むファイル（必須）

新しいセッションを開始する際は、**必ず以下のファイルを添付またはHub経由で読み込んでください**：

1. **docs/JRAVAN_DATA_SPECIFICATION.md** (14.5 KB)
   - JRA-VANの全レコードタイプ、カラム定義、パース実装例

2. **docs/JRDB_DATA_SPECIFICATION.md** (17.6 KB)
   - JRDBの全ファイル種別、カラム定義、統合戦略

3. **docs/DATABASE_SCHEMA.md** (13.4 KB)
   - データベース設計、統合テーブル定義、インデックス戦略

4. **scripts_jra/phase0_data_acquisition/fetch_jravan_data.py** (10.8 KB)
   - JRA-VANデータ取得スクリプト

5. **scripts_jra/phase0_data_acquisition/fetch_jrdb_data.py** (9.7 KB)
   - JRDBデータ取得スクリプト

6. **scripts_jra/phase0_data_acquisition/run_parallel_download.py** (5.1 KB)
   - 並行ダウンロード実行スクリプト

7. **アップロードされた2つのレポート**:
   - JRA-VAN Data Labを活用したAI競馬予測システムの構築.md
   - 中央競馬（JRA）AI予想システム構築に向けたJRDBデータ取得・実装.md

---

## 環境セットアップ

### 1. 必須ソフトウェア

#### Windows環境（JRA-VAN用）

```bash
# Python 3.8+ (32ビット版推奨)
# JRA-VAN Data Lab契約後、JV-Link SDKをインストール
# pywin32インストール
pip install pywin32
```

#### データ処理環境（Python 3.8+）

```bash
# 必須パッケージインストール
pip install pandas numpy sqlalchemy psycopg2-binary
pip install tqdm pyyaml python-dotenv
```

#### LZH解凍ツール

- [7-Zip](https://www.7-zip.org/) をインストール（JRDB用）

### 2. ディレクトリ構造作成

```bash
# プロジェクトルート
cd /path/to/anonymous-keiba-ai-jra

# 必要なディレクトリ作成
mkdir -p data/jravan/raw/{races,entries,results,payouts,odds,training,pedigree}
mkdir -p data/jrdb/raw/{sed,kyi,bac,cyb,cha,skb,tyb,ukc}
mkdir -p data/jrdb/temp_extract
mkdir -p logs
mkdir -p models
```

### 3. データソース契約

#### JRA-VAN Data Lab

1. [JRA-VAN公式サイト](https://www.jra-van.jp/) にアクセス
2. 「Data Lab」プランに登録（月額2,090円）
3. JV-Link SDK をダウンロード＆インストール
4. 認証情報を環境変数に設定（または `.env` ファイル作成）

```bash
# .env
JVLINK_USER_ID=your_user_id
JVLINK_PASSWORD=your_password
```

#### JRDB

1. [JRDB公式サイト](http://www.jrdb.com/) にアクセス
2. 「過去コメント有」プランに登録（月額3,630円）
3. 専用ダウンローダー「Ikkatsu」をダウンロード
4. Ikkatsuで過去15年分のLZHファイルをダウンロード
   - 保存先: `E:\jrdb_data\lzh\`
   - ファイル種別: SED, KYI, BAC, CYB, CHA, SKB, TYB, UKC
   - 期間: 2010-01-01 ~ 2024-12-31

---

## Phase 0 実行手順

### Step 1: JRA-VANデータ取得（約30時間）

```bash
# Windows 32ビットPython環境で実行
python scripts_jra/phase0_data_acquisition/fetch_jravan_data.py
```

**実行内容**:
- 2010-2024年の15年分データを年次チャンキングで取得
- データ種別: RACE（RA, SE, HR, H1-H6, O1-O6）, BLOD, WF
- 保存先: `data/jravan/raw/` 配下

**ログ監視**:
```bash
tail -f logs/jravan_download.log
```

**進捗確認**:
- ダウンロード進捗は `JVStatus()` で5秒ごとに表示
- エラー発生時は `logs/jravan_errors.csv` に記録

### Step 2: JRDBデータ処理（数時間）

```bash
# LZHファイル解凍・整理
python scripts_jra/phase0_data_acquisition/fetch_jrdb_data.py
```

**前提条件**:
- `E:\jrdb_data\lzh\` にLZHファイルがダウンロード済み

**実行内容**:
- LZHファイルを自動解凍（7-Zip使用）
- ファイル種別ごとに整理（SED → `data/jrdb/raw/sed/` 等）
- 年月サブディレクトリに配置

**ログ監視**:
```bash
tail -f logs/jrdb_download.log
```

### Step 3: 並行実行（推奨）

JRA-VANとJRDBを並行処理することで時間短縮：

```bash
python scripts_jra/phase0_data_acquisition/run_parallel_download.py
```

**実行内容**:
- JRA-VAN取得とJRDB処理を別スレッドで同時実行
- 進捗を5分ごとにログ出力
- 片方が失敗しても他方は継続

---

## トラブルシューティング

### JRA-VAN関連

#### エラー: `JVInit failed`

**原因**: JV-Link SDKが未インストール、または認証失敗

**対処**:
```bash
# JV-Linkインストール確認
# C:\Program Files (x86)\JRA-VAN\JVDTLab\ が存在するか確認

# 32ビットPythonで実行しているか確認
python -c "import platform; print(platform.architecture())"
# → ('32bit', 'WindowsPE') であること
```

#### エラー: `JVOpen returned -1`

**原因**: dataspec指定ミス、または期間指定エラー

**対処**:
- dataspecは 'RACE', 'BLOD', 'WF' のいずれか
- fromtime は 'YYYYMMDD000000' 形式

#### メモリ不足エラー

**対処**:
- チャンキングサイズを小さくする（2年単位 → 1年単位）
- バッファサイズを縮小（100KB → 50KB）

### JRDB関連

#### エラー: `7-zip not found`

**対処**:
```python
# fetch_jrdb_data.py のパスを修正
self.seven_zip_path = r'C:\Program Files\7-Zip\7z.exe'
# ↓ インストール先に合わせて変更
self.seven_zip_path = r'D:\Tools\7-Zip\7z.exe'
```

#### 解凍ファイルが0バイト

**原因**: LZHファイル破損

**対処**:
- JRDBから該当ファイルを再ダウンロード
- エラーログ（`logs/jrdb_errors.csv`）を確認

---

## 次のフェーズへ

### データ取得完了後のチェックリスト

```bash
# ファイル数確認
find data/jravan/raw -name "*.txt" | wc -l
# → 期待値: 30,000以上

find data/jrdb/raw -name "*.txt" | wc -l
# → 期待値: 40,000以上（8種別 × 5,500日）

# データサイズ確認
du -sh data/jravan/raw
# → 期待値: 20-50 GB

du -sh data/jrdb/raw
# → 期待値: 30-50 GB
```

### Phase 1（特徴量エンジニアリング）への準備

1. **データベース構築**:
   ```bash
   # PostgreSQL起動
   psql -U postgres
   CREATE DATABASE jra_keiba_ai;
   
   # スキーマ作成
   psql -U postgres -d jra_keiba_ai -f scripts_jra/database/create_schema.sql
   ```

2. **パーサー実装**:
   - `docs/JRAVAN_DATA_SPECIFICATION.md` のパーサークラスを参考に実装
   - `docs/JRDB_DATA_SPECIFICATION.md` のパーサークラスを参考に実装

3. **ETLパイプライン構築**:
   ```bash
   # 次セッションで実装予定
   python scripts_jra/phase1_etl/load_jravan_to_db.py
   python scripts_jra/phase1_etl/load_jrdb_to_db.py
   python scripts_jra/phase1_etl/create_unified_table.py
   ```

---

## 新セッション開始テンプレート

次のセッションで以下をコピー＆ペーストしてください：

```
# JRA版AI予測システム - 新セッション開始

## プロジェクト概要
- リポジトリ: aka209859-max/anonymous-keiba-ai-jra
- 目的: JRA中央競馬AI予測システム構築
- データソース: JRA-VAN Data Lab + JRDB (ハイブリッド)
- 期間: 2010-2024 (15年分)
- 目標: AUC ≥ 0.85, 回収率 ≥ 120%

## Phase 0 ステータス
- [ ] JRA-VANデータ取得完了 (30時間)
- [ ] JRDBデータ処理完了 (数時間)
- [ ] データベーススキーマ作成完了
- [ ] パーサー実装完了

## 添付ファイル
1. docs/JRAVAN_DATA_SPECIFICATION.md
2. docs/JRDB_DATA_SPECIFICATION.md
3. docs/DATABASE_SCHEMA.md
4. scripts_jra/phase0_data_acquisition/*.py
5. JRA-VAN/JRDBレポート（アップロード済み2ファイル）

## 次のタスク
[ここに具体的な実装指示を記載]
```

---

## 重要な注意事項

### データ取得に関する制約

1. **JRA-VAN Data Lab**:
   - 利用規約の遵守（個人利用範囲）
   - データの再配布禁止
   - 同時アクセス台数制限（2台まで）

2. **JRDB**:
   - 会員規約の遵守
   - データの商用利用は別途契約必要
   - スクレイピング禁止（専用ダウンローダー使用必須）

### セキュリティ

- 認証情報を `.env` ファイルに記載し、`.gitignore` に追加
- 生データファイル（CSV, TXT）は `.gitignore` に追加
- GitHubにプッシュする前に必ず確認

---

**更新履歴**:
- 2026-02-14: 初版作成（Phase 0 クイックスタートガイド）
