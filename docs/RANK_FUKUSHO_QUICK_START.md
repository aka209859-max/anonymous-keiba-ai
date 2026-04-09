# 🚀 ランク別複勝率分析ツール クイックスタート

## ⚡ 3分でできる実行手順

### 1️⃣ スクリプト配置確認

```cmd
cd E:\anonymous-keiba-ai
dir scripts\evaluation\analyze_rank_fukusho_rate_from_db.py
```
✅ ファイルが表示されればOK

---

### 2️⃣ 予測CSVを確認

```cmd
dir data\predictions\phase5_ensemble\*.csv
```

**CSVが無い場合**:
```cmd
REM Phase 5を実行してCSV生成
run_all_FINAL.bat 45 2026-03-03
```

---

### 3️⃣ 実行（3パターン）

#### 🔸 パターンA: 全競馬場・全月（推奨）
```cmd
cd E:\anonymous-keiba-ai
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026
```

#### 🔸 パターンB: 特定競馬場のみ（例: 川崎）
```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --venue 45
```

#### 🔸 パターンC: 特定月のみ（例: 2月～3月）
```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --month 02-03
```

---

### 4️⃣ TXTファイル出力

#### 自動ファイル名生成
```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026
```
→ `analysis_results_2026_all_20260312_235959.txt` が自動生成される

#### ファイル名指定
```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --output results_2026.txt
```
→ `E:\anonymous-keiba-ai\results_2026.txt` に保存

---

## 📊 出力結果の見方

```
競馬場       レース数 |     1位S複勝 |     1位A複勝 |     2位S複勝 |     2位A複勝 |     2位B複勝
------------------------------------------------------------------------------------------------------------------------
川崎               45 | 32/38 (84.2%) |    3/4 (75.0%) | 28/34 (82.4%) |   8/9 (88.9%) |   2/5 (40.0%)
                       ↑                                 ↑
                   的中数/予測数 (複勝率)             2位の馬がSランクだった場合の複勝率
```

### 読み方
- **1位S複勝**: 予測1位がSランク（0.80以上）の馬が、実際に3着以内に入った確率
- **2位S複勝**: 予測2位がSランクの馬が、実際に3着以内に入った確率

---

## 🎯 競馬場コード一覧（よく使うもの）

| 競馬場 | コード | コマンド例 |
|--------|--------|-----------|
| 川崎 | 45 | `--venue 45` |
| 笠松 | 47 | `--venue 47` |
| 高知 | 54 | `--venue 54` |
| 佐賀 | 55 | `--venue 55` |
| 船橋 | 43 | `--venue 43` |
| 大井 | 44 | `--venue 44` |
| 園田 | 50 | `--venue 50` |
| 姫路 | 51 | `--venue 51` |

---

## ❌ トラブルシューティング

### エラー: 予測CSVが見つかりません

**対策**:
```cmd
REM CSVファイルを探す
dir /s /b *.csv | findstr /i ensemble

REM 見つかったら、ディレクトリ名を確認
REM 例: data\predictions\phase5_ensemble にある場合
```

**または**、Phase 5を実行:
```cmd
run_all_FINAL.bat 45 2026-03-03
```

---

### エラー: DB接続失敗

**対策**:
```cmd
REM PostgreSQL起動確認
psql -U postgres -d pckeiba -c "SELECT 1;"
```

接続情報を確認（スクリプト内を編集）:
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pckeiba',
    'user': 'postgres',
    'password': 'postgres123'  # ← 実際のパスワードに変更
}
```

---

### エラー: ModuleNotFoundError

**対策**:
```cmd
pip install psycopg2-binary pandas numpy
```

---

## 📝 実用例

### 例1: 月次レポート作成（毎月末実行）

```cmd
cd E:\anonymous-keiba-ai
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --month 03-03 --output reports\2026_03.txt
```

### 例2: 全競馬場の年間成績（年末実行）

```cmd
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --output annual_report_2026.txt
```

### 例3: note記事用データ取得

```cmd
REM 川崎の2月～3月実績
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026 --venue 45 --month 02-03 --output note_kawasaki.txt

REM TXTファイルをコピペしてnote記事に掲載
notepad note_kawasaki.txt
```

---

## 💡 活用のヒント

### ✅ 記事への掲載（コピペ可能）

```markdown
## 🎯 AI予測精度データ（2026年2月～3月）

### 川崎競馬場
- **1位Sランク複勝率**: 84.2% (38/45レース)
- **2位Sランク複勝率**: 82.4% (34/45レース)

### 全競馬場
- **1位Sランク複勝率**: 82.5% (312/378レース)
- **2位Sランク複勝率**: 82.1% (248/302レース)

※AI分析結果です。投資は自己責任でお願いします。
```

---

## 📚 詳細マニュアル

完全版ドキュメント:
```
E:\anonymous-keiba-ai\docs\RANK_FUKUSHO_ANALYSIS_GUIDE.md
```

---

## 🔄 定期実行バッチファイル例

### `monthly_analysis.bat`

```batch
@echo off
setlocal

REM 現在の年月を取得
for /f "tokens=1,2 delims=/ " %%a in ('date /t') do (
    set CURRENT_DATE=%%a
)

set YEAR=2026
set MONTH=03

cd E:\anonymous-keiba-ai

echo ============================================
echo 月次分析実行中...
echo 対象: %YEAR%年%MONTH%月
echo ============================================

python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year %YEAR% --month %MONTH%-%MONTH% --output reports\%YEAR%_%MONTH%_report.txt

if errorlevel 1 (
    echo ❌ エラーが発生しました
    pause
    exit /b 1
)

echo ✅ 完了！
echo 📄 レポート: reports\%YEAR%_%MONTH%_report.txt

pause
```

**実行方法**:
```cmd
cd E:\anonymous-keiba-ai
monthly_analysis.bat
```

---

## 🏁 まとめ

### 基本コマンド（これだけ覚えればOK）

```cmd
cd E:\anonymous-keiba-ai
python scripts\evaluation\analyze_rank_fukusho_rate_from_db.py --year 2026
```

→ 全競馬場の複勝率を計算し、TXTファイルに自動保存

---

**ダウンロード**:
```
/home/user/webapp/anonymous-keiba-ai/scripts/evaluation/analyze_rank_fukusho_rate_from_db.py
→ E:\anonymous-keiba-ai\scripts\evaluation\analyze_rank_fukusho_rate_from_db.py
```

---

🎉 **これで準備完了！実行してください！** 🏇
