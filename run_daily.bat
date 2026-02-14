@echo off
REM ============================================================
REM 地方競馬AI予想システム - 毎日の自動実行スクリプト
REM 指定日に開催される全競馬場を自動検出して予測実行
REM 使用方法: run_daily.bat [DATE]
REM 例: run_daily.bat 2026-02-13
REM ============================================================

setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM 引数チェック（日付が指定されていない場合は今日の日付を使用）
if "%~1"=="" (
    echo [INFO] 日付が指定されていません。今日の日付を使用します。
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (
        set TODAY=%%c-%%a-%%b
    )
    set "TARGET_DATE=!TODAY!"
) else (
    set "TARGET_DATE=%~1"
)

echo ============================================================
echo 地方競馬AI予想システム - 毎日の自動実行
echo ============================================================
echo 対象日付: %TARGET_DATE%
echo ============================================================
echo.

REM 日付を YYYYMMDD 形式に変換
for /f "tokens=1,2,3 delims=-" %%a in ("%TARGET_DATE%") do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)
set "DATE_SHORT=%YEAR%%MONTH%%DAY%"

echo [INFO] データベースから開催競馬場を検索中...
echo.

REM Python で開催競馬場を取得
python -c "import sqlite3; conn = sqlite3.connect('data/raw/keiba.db'); cursor = conn.cursor(); cursor.execute('SELECT DISTINCT keibajo_code FROM race_results WHERE kaisai_nen = ? AND kaisai_tsukihi = ?', ('%YEAR%', '%MONTH%%DAY%')); venues = [row[0] for row in cursor.fetchall()]; conn.close(); print(' '.join(venues) if venues else 'NONE')" > temp_venues.txt

set /p VENUES=<temp_venues.txt
del temp_venues.txt

if "%VENUES%"=="NONE" (
    echo [ERROR] %TARGET_DATE% に開催される競馬場が見つかりませんでした
    echo.
    echo データベースを確認してください:
    echo   python -c "import sqlite3; conn = sqlite3.connect('data/raw/keiba.db'); cursor = conn.cursor(); cursor.execute('SELECT DISTINCT keibajo_code, kaisai_nen, kaisai_tsukihi FROM race_results ORDER BY kaisai_nen DESC, kaisai_tsukihi DESC LIMIT 10'); [print(f'{row[0]} : {row[1]}-{row[2][:2]}-{row[2][2:]}') for row in cursor.fetchall()]; conn.close()"
    echo.
    exit /b 1
)

if "%VENUES%"=="" (
    echo [ERROR] 開催競馬場の取得に失敗しました
    exit /b 1
)

echo [INFO] 開催競馬場: %VENUES%
echo.

REM 競馬場名マッピング
set "KEIBAJO_30=門別"
set "KEIBAJO_35=盛岡"
set "KEIBAJO_36=水沢"
set "KEIBAJO_42=浦和"
set "KEIBAJO_43=船橋"
set "KEIBAJO_44=大井"
set "KEIBAJO_45=川崎"
set "KEIBAJO_46=金沢"
set "KEIBAJO_47=笠松"
set "KEIBAJO_48=名古屋"
set "KEIBAJO_50=園田"
set "KEIBAJO_51=姫路"
set "KEIBAJO_54=高知"
set "KEIBAJO_55=佐賀"

set SUCCESS_COUNT=0
set FAIL_COUNT=0

REM 各競馬場で予測実行
for %%V in (%VENUES%) do (
    set "VENUE_CODE=%%V"
    
    REM 競馬場名を取得
    call set "VENUE_NAME=%%KEIBAJO_!VENUE_CODE!%%"
    
    echo ============================================================
    echo [!VENUE_NAME!] 予測開始 (コード: !VENUE_CODE!)
    echo ============================================================
    
    REM run_all_optimized.bat を実行
    call run_all_optimized.bat !VENUE_CODE! %TARGET_DATE%
    
    if errorlevel 1 (
        echo [ERROR] [!VENUE_NAME!] 予測失敗
        set /a FAIL_COUNT+=1
    ) else (
        echo [OK] [!VENUE_NAME!] 予測完了
        set /a SUCCESS_COUNT+=1
    )
    echo.
)

echo ============================================================
echo 全競馬場の予測完了
echo ============================================================
echo 成功: %SUCCESS_COUNT% 競馬場
echo 失敗: %FAIL_COUNT% 競馬場
echo ============================================================
echo.

REM 生成されたファイル一覧を表示
echo [INFO] 生成されたファイル一覧:
echo.
dir predictions\*_%DATE_SHORT%_note.txt /b 2>nul
echo.

echo [INFO] predictions フォルダを開きますか？ (Enter で開く / Ctrl+C でスキップ)
pause > nul
explorer predictions

endlocal
