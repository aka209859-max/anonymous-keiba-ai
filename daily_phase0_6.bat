@echo off
chcp 932 >nul
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM =========================================================================
REM Phase 0-6: 毎日運用スクリプト
REM 対象: 全国の地方競馬場
REM =========================================================================

REM 引数チェック
if "%~1"=="" (
    echo 使用法: daily_phase0_6.bat [DATE] [KEIBAJO_CODES]
    echo.
    echo 例: daily_phase0_6.bat 2026-04-22
    echo 例: daily_phase0_6.bat today  ^(今日の日付を自動取得^)
    echo 例: daily_phase0_6.bat 2026-04-22 "30 42 48 50"  ^(特定の競馬場のみ^)
    echo.
    echo 主要競馬場コード:
    echo   30=門別, 42=浦和, 43=船橋, 44=大井, 45=川崎
    echo   46=金沢, 47=笠松, 48=名古屋, 50=園田, 54=高知, 55=佐賀
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

REM 競馬場コードリスト（第2引数があればそれを使用、なければ全場）
if "%~2"=="" (
    set KEIBAJO_LIST=30 35 36 42 43 44 45 46 47 48 50 51 54 55
) else (
    set KEIBAJO_LIST=%~2
)

echo =========================================================================
echo Phase 0-6: 毎日運用スクリプト
echo =========================================================================
echo 対象日: %TARGET_DATE%
echo =========================================================================
echo.

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
    
    REM Phase 0-6を実行
    call run_all_FINAL.bat %%K %TARGET_DATE%
    
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
set "DATE_SHORT=%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%"
echo 生成された出力ファイル:
dir /b predictions\*%DATE_SHORT%*.txt 2>nul

if %SUCCESS_COUNT% gtr 0 (
    echo.
    echo 出力ファイルを開くには:
    for %%F in (predictions\*%DATE_SHORT%*.txt) do (
        echo   notepad "%%F"
    )
)

echo =========================================================================

endlocal
