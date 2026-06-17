# 🏇 地方競馬AI予想 - 毎日の運用コマンド集

## 📋 基本的な1日の流れ

### ステップ1: Phase 0-5 の実行（データ取得〜予測）

```batch
REM 指定した日付・競馬場のデータを取得して予測まで実行
REM 構文: run_all.bat [競馬場コード] [日付]

REM 例: 2026年2月8日の佐賀競馬
run_all.bat 55 2026-02-08

REM 例: 2026年2月10日の大井競馬
run_all.bat 44 2026-02-10

REM 例: 2026年2月10日の川崎競馬
run_all.bat 45 2026-02-10
```

### ステップ2: Phase 6 配信用テキスト生成

```batch
REM Phase 5完了済みの全競馬場を一括処理
REM 構文: BATCH_OPERATION.bat [日付]

REM 例: 2026年2月8日の全競馬場
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08

REM 例: 2026年2月10日の全競馬場
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-10
```

### ステップ3: 生成ファイルの確認

```batch
REM predictions フォルダを開く
explorer predictions

REM または、特定のファイルを開く
notepad predictions\佐賀_20260208_note.txt
notepad predictions\佐賀_20260208_bookers.txt
```

---

## 🎯 シナリオ別コマンド

### シナリオ1: 土曜日（複数競馬場開催）

```batch
REM ==============================================
REM 2026年2月8日（土曜日）の運用例
REM 開催: 佐賀、大井、川崎、浦和、高知など
REM ==============================================

cd E:\anonymous-keiba-ai

REM --- Phase 0-5: 各競馬場のデータ取得〜予測 ---
run_all.bat 55 2026-02-08
run_all.bat 44 2026-02-08
run_all.bat 45 2026-02-08
run_all.bat 42 2026-02-08
run_all.bat 54 2026-02-08

REM --- Phase 6: 配信用テキスト一括生成 ---
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08

REM --- ファイル確認 ---
explorer predictions
```

---

### シナリオ2: 平日ナイター（大井・川崎）

```batch
REM ==============================================
REM 2026年2月10日（水曜日）の運用例
REM 開催: 大井、川崎
REM ==============================================

cd E:\anonymous-keiba-ai

REM --- Phase 0-5: 各競馬場のデータ取得〜予測 ---
run_all.bat 44 2026-02-10
run_all.bat 45 2026-02-10

REM --- Phase 6: 配信用テキスト一括生成 ---
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-10

REM --- ファイル確認 ---
explorer predictions
```

---

### シナリオ3: 単一競馬場のみ

```batch
REM ==============================================
REM 2026年2月9日（日曜日）の運用例
REM 開催: 佐賀のみ
REM ==============================================

cd E:\anonymous-keiba-ai

REM --- Phase 0-5: データ取得〜予測 ---
run_all.bat 55 2026-02-09

REM --- Phase 6: 配信用テキスト生成 ---
scripts\phase6_betting\DAILY_OPERATION.bat 55 2026-02-09

REM または、一括処理でもOK（自動検出される）
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-09

REM --- ファイル確認 ---
notepad predictions\佐賀_20260209_note.txt
notepad predictions\佐賀_20260209_bookers.txt
```

---

## 📅 日付別コマンドテンプレート

### 当日分の処理

```batch
REM 今日の日付: 2026-02-08
set TODAY=2026-02-08

cd E:\anonymous-keiba-ai

REM Phase 0-5（開催競馬場すべて）
run_all.bat 55 %TODAY%
run_all.bat 44 %TODAY%
run_all.bat 45 %TODAY%

REM Phase 6（一括生成）
scripts\phase6_betting\BATCH_OPERATION.bat %TODAY%

REM 確認
explorer predictions
```

---

### 翌日分の処理（前日夜）

```batch
REM 明日の日付: 2026-02-09
set TOMORROW=2026-02-09

cd E:\anonymous-keiba-ai

REM Phase 0-5（開催競馬場すべて）
run_all.bat 55 %TOMORROW%
run_all.bat 44 %TOMORROW%

REM Phase 6（一括生成）
scripts\phase6_betting\BATCH_OPERATION.bat %TOMORROW%

REM 確認
explorer predictions
```

---

## 🔧 便利なコマンド

### 生成済みファイルの一覧表示

```batch
REM 今日の日付のファイルを表示
dir predictions\*20260208*.txt

REM すべての配信用ファイルを表示
dir predictions\*.txt /o-d
```

---

### 古いファイルの整理

```batch
REM 過去の予想を日付フォルダに移動
mkdir archive\2026-02
move predictions\*_20260208_*.txt archive\2026-02\
```

---

### Phase 5完了状況の確認

```batch
REM 今日の日付で完了している競馬場を確認
dir data\predictions\phase5\*20260208*ensemble.csv
```

---

## 🚀 ワンライナーコマンド（コピペ用）

### 佐賀競馬（2026-02-08）

```batch
cd E:\anonymous-keiba-ai && run_all.bat 55 2026-02-08 && scripts\phase6_betting\DAILY_OPERATION.bat 55 2026-02-08 && notepad predictions\佐賀_20260208_note.txt
```

---

### 複数競馬場一括（2026-02-08）

```batch
cd E:\anonymous-keiba-ai && run_all.bat 55 2026-02-08 && run_all.bat 44 2026-02-08 && run_all.bat 45 2026-02-08 && scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08 && explorer predictions
```

---

## 📝 バッチファイル作成（毎日使う場合）

### daily_run.bat（カスタマイズ版）

```batch
@echo off
REM ==============================================
REM 毎日の運用バッチ（カスタマイズ版）
REM ==============================================

REM 日付を指定（手動更新）
set TARGET_DATE=2026-02-08

REM 開催競馬場コードを指定（スペース区切り）
set VENUES=55 44 45

cd E:\anonymous-keiba-ai

echo ==============================================
echo 地方競馬AI予想 - 毎日の運用
echo 対象日: %TARGET_DATE%
echo 開催場: %VENUES%
echo ==============================================
echo.

REM Phase 0-5 を各競馬場で実行
for %%V in (%VENUES%) do (
    echo [Phase 0-5] 競馬場コード %%V を処理中...
    call run_all.bat %%V %TARGET_DATE%
    echo.
)

REM Phase 6 一括生成
echo [Phase 6] 配信用テキスト一括生成中...
call scripts\phase6_betting\BATCH_OPERATION.bat %TARGET_DATE%
echo.

REM 結果を表示
echo ==============================================
echo すべての処理が完了しました！
echo predictions フォルダを確認してください
echo ==============================================
explorer predictions

pause
```

**使い方:**
1. 上記をコピーして `daily_run.bat` として保存
2. `set TARGET_DATE=2026-02-08` の日付を更新
3. `set VENUES=55 44 45` の競馬場コードを更新
4. `daily_run.bat` をダブルクリックで実行

---

## ⚙️ タスクスケジューラ設定（自動化）

### 毎朝自動実行の設定

```batch
REM タスクスケジューラで以下を設定:

REM プログラム/スクリプト:
E:\anonymous-keiba-ai\daily_run.bat

REM トリガー:
毎日 朝 7:00

REM 操作:
プログラムの開始
```

---

## 🔍 トラブルシューティングコマンド

### Phase 5完了確認

```batch
REM 今日の日付でPhase 5が完了しているか確認
dir data\predictions\phase5\*20260208*

REM 存在しない場合は、run_all.bat を再実行
run_all.bat 55 2026-02-08
```

---

### 生成ファイル確認

```batch
REM 今日の配信用ファイルが生成されているか確認
dir predictions\*20260208*

REM 存在しない場合は、Phase 6を再実行
scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08
```

---

### ログ確認

```batch
REM 実行ログを確認（エラーがある場合）
type logs\phase0_20260208.log
type logs\phase1_20260208.log
```

---

## 📌 競馬場コード早見表

| コード | 競馬場 | 主な開催曜日 | コード | 競馬場 | 主な開催曜日 |
|--------|--------|--------------|--------|--------|--------------|
| 30 | 門別 | 火-日 | 35 | 盛岡 | 土日 |
| 36 | 水沢 | 土日 | 42 | 浦和 | 月水金 |
| 43 | 船橋 | 水木金 | **44** | **大井** | **水金月** |
| **45** | **川崎** | **水金** | 46 | 金沢 | 土日 |
| 47 | 笠松 | 金月 | 48 | 名古屋 | 水金 |
| 50 | 園田 | 水金 | 51 | 姫路 | 月水金 |
| 54 | 高知 | 土日 | **55** | **佐賀** | **土日** |

---

## 💡 Pro Tips

### Tip 1: 複数ウィンドウで並行処理

```batch
REM 各競馬場を別ウィンドウで同時実行（処理時間短縮）
start cmd /k "cd E:\anonymous-keiba-ai && run_all.bat 55 2026-02-08"
start cmd /k "cd E:\anonymous-keiba-ai && run_all.bat 44 2026-02-08"
start cmd /k "cd E:\anonymous-keiba-ai && run_all.bat 45 2026-02-08"
```

---

### Tip 2: 日付を自動取得

```batch
REM 今日の日付を自動取得（YYYY-MM-DD形式）
for /f "tokens=1-3 delims=/" %%a in ("%date%") do set TODAY=%%c-%%a-%%b
echo 今日の日付: %TODAY%
```

---

### Tip 3: エラー時の再実行

```batch
REM エラーが発生した場合のみ再実行
run_all.bat 55 2026-02-08
if errorlevel 1 (
    echo エラーが発生しました。再実行します...
    timeout /t 5
    run_all.bat 55 2026-02-08
)
```

---

## 🎉 クイックコピペ用コマンド集

### 今日（2026-02-08）の全処理

```batch
cd E:\anonymous-keiba-ai && run_all.bat 55 2026-02-08 && run_all.bat 44 2026-02-08 && run_all.bat 45 2026-02-08 && scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-08 && explorer predictions
```

### 明日（2026-02-09）の全処理

```batch
cd E:\anonymous-keiba-ai && run_all.bat 55 2026-02-09 && run_all.bat 44 2026-02-09 && scripts\phase6_betting\BATCH_OPERATION.bat 2026-02-09 && explorer predictions
```

---

**毎日の運用、頑張ってください！** 🏇✨
