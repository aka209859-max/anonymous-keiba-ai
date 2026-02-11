@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================
REM Phase 10: 複数競馬場一括予測
REM Phase 8最適化モデルを使った予測実行
REM ========================================

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if "%~1"=="" (
    echo Usage: RUN_PHASE10_ALL_VENUES.bat [DATE] [VENUE_CODES...]
    echo Example: RUN_PHASE10_ALL_VENUES.bat 2026-02-11 44 45 55
    echo.
    echo 競馬場コード:
    echo   30: 門別   35: 盛岡   36: 水沢   42: 浦和
    echo   43: 船橋   44: 大井   45: 川崎   46: 金沢
    echo   47: 笠松   48: 名古屋 50: 園田   51: 姫路
    echo   54: 高知   55: 佐賀
    exit /b 1
)

set TARGET_DATE=%~1
shift

REM 競馬場コードを配列に格納
set VENUE_COUNT=0
:parse_venues
if "%~1"=="" goto start_processing
set /a VENUE_COUNT+=1
set VENUE[!VENUE_COUNT!]=%~1
shift
goto parse_venues

:start_processing

if %VENUE_COUNT%==0 (
    echo ❌ 競馬場コードを指定してください
    echo Example: RUN_PHASE10_ALL_VENUES.bat 2026-02-11 44 45 55
    pause
    exit /b 1
)

echo ========================================
echo Phase 10: 複数競馬場一括予測
echo ========================================
echo 対象日: %TARGET_DATE%
echo 競馬場数: %VENUE_COUNT%個
echo ========================================
echo.

set SUCCESS_COUNT=0
set FAIL_COUNT=0

REM 各競馬場で予測実行
for /L %%i in (1,1,%VENUE_COUNT%) do (
    set KEIBAJO_CODE=!VENUE[%%i]!
    
    REM 競馬場名の設定
    if "!KEIBAJO_CODE!"=="30" set KEIBAJO_NAME=門別
    if "!KEIBAJO_CODE!"=="35" set KEIBAJO_NAME=盛岡
    if "!KEIBAJO_CODE!"=="36" set KEIBAJO_NAME=水沢
    if "!KEIBAJO_CODE!"=="42" set KEIBAJO_NAME=浦和
    if "!KEIBAJO_CODE!"=="43" set KEIBAJO_NAME=船橋
    if "!KEIBAJO_CODE!"=="44" set KEIBAJO_NAME=大井
    if "!KEIBAJO_CODE!"=="45" set KEIBAJO_NAME=川崎
    if "!KEIBAJO_CODE!"=="46" set KEIBAJO_NAME=金沢
    if "!KEIBAJO_CODE!"=="47" set KEIBAJO_NAME=笠松
    if "!KEIBAJO_CODE!"=="48" set KEIBAJO_NAME=名古屋
    if "!KEIBAJO_CODE!"=="50" set KEIBAJO_NAME=園田
    if "!KEIBAJO_CODE!"=="51" set KEIBAJO_NAME=姫路
    if "!KEIBAJO_CODE!"=="54" set KEIBAJO_NAME=高知
    if "!KEIBAJO_CODE!"=="55" set KEIBAJO_NAME=佐賀
    
    echo ----------------------------------------
    echo [%%i/%VENUE_COUNT%] !KEIBAJO_NAME! (コード: !KEIBAJO_CODE!)
    echo ----------------------------------------
    
    python scripts\phase10_daily_prediction\run_daily_prediction.py --venue-code !KEIBAJO_CODE! --date %TARGET_DATE% --bankroll 100000 --kelly-fraction 0.25
    
    if errorlevel 1 (
        echo ❌ !KEIBAJO_NAME! の予測でエラーが発生しました
        set /a FAIL_COUNT+=1
    ) else (
        echo ✅ !KEIBAJO_NAME! の予測完了
        set /a SUCCESS_COUNT+=1
    )
    echo.
)

echo ========================================
echo Phase 10 完了サマリー
echo ========================================
echo 対象日: %TARGET_DATE%
echo 総競馬場数: %VENUE_COUNT%
echo 成功: %SUCCESS_COUNT%
echo 失敗: %FAIL_COUNT%
echo ========================================
echo.

if %FAIL_COUNT% GTR 0 (
    echo ⚠️ 一部の競馬場で失敗しました
) else (
    echo ✅ すべての競馬場で予測完了！
)

echo.
echo 次のステップ:
echo   Phase 6配信用テキスト生成
echo   コマンド: scripts\phase6_betting\BATCH_OPERATION.bat %TARGET_DATE%
echo.

pause
