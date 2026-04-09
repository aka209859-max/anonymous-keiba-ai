# 🏇 競馬場別・ランク別 複勝率分析ツール 完全ガイド

## 📌 概要

PC-KEIBAデータベースから過去の予測結果と実際の着順を取得し、**ランク別の複勝率**を自動計算するツールです。

### 分析対象
- **1位のSランク** → 複勝率（1位予測馬がSランクの場合、実際に3着以内に入る確率）
- **1位のAランク** → 複勝率
- **2位のSランク** → 複勝率（2位予測馬がSランクの場合、実際に3着以内に入る確率）
- **2位のAランク** → 複勝率
- **2位のBランク** → 複勝率

---

## 🚀 使い方

### 基本実行コマンド

```cmd
cd E:\anonymous-keiba-ai

REM 2026年全競馬場・全レースを分析
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026

REM 川崎競馬場のみ（コード45）
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --venue 45

REM 2026年2月～3月のみ
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --month 02-03

REM 出力ファイル名を指定
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --output results_2026.txt

REM 川崎・2月～3月・ファイル指定
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --venue 45 --month 02-03 --output kawasaki_0203.txt
```

### オプション一覧

| オプション | 必須 | 説明 | 例 |
|-----------|------|------|-----|
| `--year` | ✅ | 分析対象年 | `2026` |
| `--venue` | ❌ | 競馬場コード | `45` (川崎), `47` (笠松), `54` (高知) |
| `--month` | ❌ | 月範囲 | `01-06` (1月～6月), `02-03` (2月～3月) |
| `--output` | ❌ | 出力ファイルパス | `results_2026.txt`, `analysis.txt` |

---

## 📊 出力例

### コンソール＆TXTファイル出力

```
========================================================================================================================
📊 競馬場別・ランク別 複勝率分析結果（PC-KEIBAデータベース）
========================================================================================================================

競馬場       レース数 |     1位S複勝 |     1位A複勝 |     2位S複勝 |     2位A複勝 |     2位B複勝
------------------------------------------------------------------------------------------------------------------------
川崎               45 | 32/38 (84.2%) |    3/4 (75.0%) | 28/34 (82.4%) |   8/9 (88.9%) |   2/5 (40.0%)
佐賀               38 | 28/34 (82.4%) |    2/3 (66.7%) | 24/30 (80.0%) |   6/7 (85.7%) |   1/4 (25.0%)
笠松               42 | 35/40 (87.5%) |    4/5 (80.0%) | 30/38 (78.9%) |   9/10 (90.0%) |   3/6 (50.0%)
...
========================================================================================================================

📈 全体サマリー
------------------------------------------------------------------------------------------------------------------------
総レース数: 280

【1位Sランク】 312/378 (82.5%)
【1位Aランク】 41/48 (85.4%)
【2位Sランク】 248/302 (82.1%)
【2位Aランク】 89/108 (82.4%)
【2位Bランク】 28/68 (41.2%)

💾 結果を保存しました: analysis_results_2026_all_20260312_235959.txt
```

### TXTファイル出力について

#### 📁 自動生成ファイル名（`--output`未指定時）

形式: `analysis_results_{年}_{競馬場}_{月範囲}_{タイムスタンプ}.txt`

例:
- `analysis_results_2026_all_20260312_235959.txt` （全競馬場）
- `analysis_results_2026_venue45_20260312_235959.txt` （川崎のみ）
- `analysis_results_2026_venue45_month0203_20260312_235959.txt` （川崎・2月～3月）

#### 📝 ファイル指定（`--output`使用時）

```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --output my_analysis.txt
```

→ `E:\anonymous-keiba-ai\my_analysis.txt` に保存

---

## 🗂️ ファイル配置

### スクリプト本体

```
E:\anonymous-keiba-ai\
└─ scripts\
   └─ evaluation\
      └─ analyze_rank_fukusho_rate_from_db.py  ← ★このファイルを使用
```

### 予測CSVファイル

```
E:\anonymous-keiba-ai\
└─ data\
   └─ predictions\
      └─ phase5_ensemble\  または phase5\
         ├─ 川崎_20260205_ensemble.csv
         ├─ 佐賀_20260207_ensemble.csv
         ├─ 笠松_20260305_ensemble.csv
         └─ ...
```

**重要**: スクリプトは以下のディレクトリを自動検索します：
1. `data/predictions/phase5_ensemble`
2. `data/predictions/phase5`
3. `predictions/phase5_ooi_2025`
4. `predictions`
5. `results`
6. `data/results`
7. `.` (カレントディレクトリ)

---

## 🔧 データソース

### 予測データ（CSV）
- **場所**: `data/predictions/phase5_ensemble/*.csv`
- **必須カラム**:
  - `race_id` (例: `202602034501` = 2026年2月3日・川崎・1R)
  - `horse_no` または `umaban` (馬番)
  - `ensemble_score` (予測スコア 0.0～1.0)

### 実績データ（PostgreSQL）
- **テーブル**: `nvd_se` (出馬表・結果)
- **カラム**: `kakutei_chakujun` (確定着順)
- **接続情報**:
  ```python
  DB_CONFIG = {
      'host': 'localhost',
      'port': 5432,
      'database': 'pckeiba',
      'user': 'postgres',
      'password': 'postgres123'
  }
  ```

---

## 🎯 ランク判定基準

| スコア範囲 | ランク |
|-----------|-------|
| 0.80 ≦ score | **S** |
| 0.70 ≦ score < 0.80 | **A** |
| 0.60 ≦ score < 0.70 | **B** |
| 0.50 ≦ score < 0.60 | **C** |
| score < 0.50 | **D** |

### 複勝的中判定
実際の着順が **1着～3着** なら「的中」としてカウント

---

## 📋 競馬場コード一覧

| コード | 競馬場 | コマンド例 |
|-------|--------|-----------|
| 30 | 門別 | `--venue 30` |
| 35 | 盛岡 | `--venue 35` |
| 36 | 水沢 | `--venue 36` |
| 42 | 浦和 | `--venue 42` |
| 43 | 船橋 | `--venue 43` |
| 44 | 大井 | `--venue 44` |
| 45 | 川崎 | `--venue 45` |
| 46 | 金沢 | `--venue 46` |
| 47 | 笠松 | `--venue 47` |
| 48 | 名古屋 | `--venue 48` |
| 50 | 園田 | `--venue 50` |
| 51 | 姫路 | `--venue 51` |
| 54 | 高知 | `--venue 54` |
| 55 | 佐賀 | `--venue 55` |

---

## 🛠️ トラブルシューティング

### ❌ エラー: 予測CSVが見つかりません

**原因**: 
- `data/predictions/phase5_ensemble` または `phase5` ディレクトリが存在しない
- CSVファイルが存在しない

**解決策**:
```cmd
REM ディレクトリ構造確認
cd E:\anonymous-keiba-ai
dir /s data\predictions

REM CSVファイル検索
dir /s /b *.csv | findstr /i ensemble
dir /s /b *.csv | findstr /i 2026

REM Phase 5を実行してCSV生成
run_all_FINAL.bat 45 2026-03-03
```

### ❌ エラー: DB接続失敗

**原因**: PostgreSQLが起動していない、または接続情報が間違っている

**解決策**:
```cmd
REM PostgreSQL起動確認
psql -U postgres -d pckeiba -c "SELECT COUNT(*) FROM nvd_se;"

REM 接続情報確認（スクリプト内を編集）
notepad scripts\evaluation\analyze_rank_fukusho_rate_from_db.py
```

スクリプト内の `DB_CONFIG` を環境に合わせて修正:
```python
DB_CONFIG = {
    'host': 'localhost',  # または '127.0.0.1'
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'  # ← 実際のパスワード
}
```

### ❌ エラー: ModuleNotFoundError: No module named 'psycopg2'

**原因**: 必要なPythonライブラリがインストールされていない

**解決策**:
```cmd
pip install psycopg2-binary
pip install pandas numpy
```

### ❌ エラー: ValueError: columns overlap but no suffix specified

**原因**: データ型の不一致（修正済み）

**解決策**:
最新版スクリプトをダウンロード・上書き:
```
/home/user/webapp/anonymous-keiba-ai/scripts/evaluation/analyze_rank_fukusho_rate_from_db.py
→ E:\anonymous-keiba-ai\scripts\evaluation\analyze_rank_fukusho_rate_from_db.py
```

### ⚠️ 警告: データが見つかりませんでした

**原因**: 指定した年・競馬場・月のデータが存在しない

**確認方法**:
```cmd
REM 2026年のCSVを確認
dir data\predictions\phase5_ensemble\*2026*.csv

REM 川崎のCSVを確認
dir data\predictions\phase5_ensemble\川崎*.csv

REM 特定月のCSVを確認
dir data\predictions\phase5_ensemble\*202602*.csv  (2月)
dir data\predictions\phase5_ensemble\*202603*.csv  (3月)
```

---

## 📈 活用例

### 1. note記事への掲載

```markdown
## 🎯 予測精度データ（2026年2月～3月実績）

### 全体サマリー（280レース）
- **1位Sランク複勝率**: 82.5% (312/378)
- **1位Aランク複勝率**: 85.4% (41/48)
- **2位Sランク複勝率**: 82.1% (248/302)

### 推奨購入パターン
- 1位S + 2位S の複勝ボックス → 的中率 82%超
- 1位A のみ単独 → 的中率 85%超
```

### 2. 記事への複勝率表示

```
【川崎競馬場 実績】
- 1位Sランク: 84.2% (45レース中38的中)
- 2位Sランク: 82.4% (45レース中34的中)
```

### 3. 競馬場別の強み分析

```cmd
REM 各競馬場の精度を比較
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --venue 45 --output kawasaki.txt
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --venue 47 --output kasamatsu.txt
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --venue 54 --output kochi.txt
```

→ 各競馬場の精度を比較し、得意場を訴求

---

## 🔄 定期実行（推奨）

### 毎月末に全データ分析

```cmd
REM 月末に実行
cd E:\anonymous-keiba-ai
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --output monthly_report_2026.txt
```

### 競馬場ごとに月次レポート

```batch
@echo off
setlocal

set YEAR=2026
set MONTH=03

python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year %YEAR% --venue 45 --month %MONTH%-%MONTH% --output reports\kawasaki_%YEAR%%MONTH%.txt
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year %YEAR% --venue 47 --month %MONTH%-%MONTH% --output reports\kasamatsu_%YEAR%%MONTH%.txt
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year %YEAR% --venue 54 --month %MONTH%-%MONTH% --output reports\kochi_%YEAR%%MONTH%.txt

echo レポート作成完了
```

---

## 📦 必要環境

### Python環境
- Python 3.7 以上
- ライブラリ:
  - `pandas`
  - `numpy`
  - `psycopg2-binary`

### データベース
- PostgreSQL 12 以上
- PC-KEIBAデータベース（テーブル `nvd_se`, `nvd_ra`）

### データファイル
- Phase 5の予測CSV（`data/predictions/phase5_ensemble/*.csv`）
- 必須カラム: `race_id`, `ensemble_score`, `horse_no` または `umaban`

---

## 🎓 よくある質問（FAQ）

### Q1: 2025年のデータを分析したいが、CSVが2026年しかない

**A**: `--year 2025` で実行し、データが無い場合はCSVファイルを確認:
```cmd
dir /s /b *.csv | findstr /i 2025
```
2025年のCSVが無ければ、Phase 5を実行してCSVを生成するか、データを2026年で実行してください。

### Q2: TXTファイルが文字化けする

**A**: メモ帳で開く際、エンコーディングを **UTF-8** に指定してください。

### Q3: 複数の競馬場をまとめて分析したい

**A**: `--venue`を省略すると全競馬場が対象になります:
```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026
```

### Q4: 特定のレース（例: 第8R）だけ分析したい

**A**: 現在のバージョンでは未対応です。全レースが対象です。

### Q5: 結果をExcel形式で出力したい

**A**: TXTファイルをExcelで開き、「区切り文字」で「|」（パイプ）を指定すると表形式になります。

---

## 📝 更新履歴

### v1.2 (2026-03-12)
- ✅ `umaban`列の型変換エラーを修正
- ✅ TXT出力機能を追加（`--output`オプション）
- ✅ 自動ファイル名生成機能追加

### v1.1 (2026-03-12)
- ✅ `phase5_ensemble`ディレクトリ対応
- ✅ 複数ディレクトリ自動検索機能追加
- ✅ デバッグ情報出力強化

### v1.0 (2026-03-12)
- ✅ 初版リリース
- ✅ PC-KEIBAデータベース対応
- ✅ 競馬場別・ランク別複勝率計算

---

## 📞 サポート

問題が発生した場合は、以下の情報を提供してください：

1. **実行コマンド**（例: `python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026`）
2. **エラーメッセージ**（全文）
3. **ディレクトリ構造**（`dir /s data\predictions`の結果）
4. **CSVファイル一覧**（`dir /s /b *.csv | findstr /i ensemble`の結果）
5. **データベース接続情報**（パスワードは隠してください）

---

## 🎉 まとめ

このツールを使えば、**PC-KEIBAデータベース**から過去の予測精度を自動計算し、**TXT形式**で出力できます。

### 推奨ワークフロー

1. **Phase 5実行** → 予測CSVを生成
2. **複勝率分析** → このツールで精度を算出
3. **TXT出力** → note記事や報告書に活用
4. **定期実行** → 月次・年次で精度をモニタリング

---

**ダウンロード場所**:
```
/home/user/webapp/anonymous-keiba-ai/scripts/evaluation/analyze_rank_fukusho_rate_from_db.py
```

**保存先**:
```
E:\anonymous-keiba-ai\scripts\evaluation\analyze_rank_fukusho_rate_from_db.py
```

---

🏇 **Happy Horse Racing!** 🎯
