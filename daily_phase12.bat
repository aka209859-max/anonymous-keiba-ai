@echo off
chcp 932 >nul
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM =========================================================================
REM Phase 12: 毎日運用スクリプト
REM 対象: 南関東4場（大井・浦和・船橋・川崎）+ 門別
REM =========================================================================

REM 引数チェック
if "%~1"=="" (
    echo 使用法: daily_phase12.bat [DATE]
    echo.
    echo 例: daily_phase12.bat 2026-04-22
    echo 例: daily_phase12.bat today  ^(今日の日付を自動取得^)
    echo.
    echo 対象競馬場: 門別^(30^), 浦和^(42^), 船橋^(43^), 大井^(44^), 川崎^(45^)
    exit /b 1
)

REM 日付の設定
set "TARGET_DATE=%~1"

REM "today"の場合は今日の日付を取得
if /i "%TARGET_DATE%"=="today" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (
        set YEAR=%%a
        set MONTH=%%b
        set DAY=%%c
    )
    REM 年が4桁でない場合は20XXに変換
    if !YEAR! lss 100 set YEAR=20!YEAR!
    REM 月・日を2桁にゼロパディング
    if !MONTH! lss 10 set MONTH=0!MONTH!
    if !DAY! lss 10 set DAY=0!DAY!
    set "TARGET_DATE=!YEAR!-!MONTH!-!DAY!"
)

echo =========================================================================
echo Phase 12: 毎日運用スクリプト
echo =========================================================================
echo 対象日: %TARGET_DATE%
echo =========================================================================
echo.

REM 対象競馬場リスト（Phase 12対象）
set KEIBAJO_LIST=30 42 43 44 45
set KEIBAJO_NAMES=門別 浦和 船橋 大井 川崎

REM 成功カウンター
set SUCCESS_COUNT=0
set TOTAL_COUNT=0

REM 各競馬場で実行
for %%K in (%KEIBAJO_LIST%) do (
    set /a TOTAL_COUNT+=1
    
    echo.
    echo =========================================================================
    echo 競馬場コード: %%K で実行中...
    echo =========================================================================
    
    REM Phase 12を実行
    call run_phase12.bat %%K %TARGET_DATE%
    
    if errorlevel 1 (
        echo [SKIP] 競馬場コード %%K はデータなしまたはエラー
    ) else (
        set /a SUCCESS_COUNT+=1
        echo [SUCCESS] 競馬場コード %%K の予測完了
    )
)

echo.
echo =========================================================================
echo 毎日運用完了
echo =========================================================================
echo 実行日: %TARGET_DATE%
echo 処理競馬場: %TOTAL_COUNT% / 成功: %SUCCESS_COUNT%
echo.

REM 生成されたファイルを確認
echo 生成された買い目ファイル:
dir /b data\phase12_umatan\predictions\tickets\*%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%*.txt 2>nul

if %SUCCESS_COUNT% gtr 0 (
    echo.
    echo 買い目ファイルを開くには:
    for %%F in (data\phase12_umatan\predictions\tickets\*%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%*.txt) do (
        echo   notepad "%%F"
    )
)

echo =========================================================================

endlocal
