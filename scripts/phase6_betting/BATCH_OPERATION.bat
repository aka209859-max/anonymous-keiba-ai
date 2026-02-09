@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

if "%~1"=="" goto :SHOW_USAGE

set "TARGET_DATE=%~1"
set "TARGET_DATE=%TARGET_DATE: =%"
set "TARGET_DATE=%TARGET_DATE:	=%"
set "DATE_SHORT=%TARGET_DATE:-=%"

REM デバッグ出力
echo ==================================================
echo Keiba AI Batch Operation
echo ==================================================
echo.
echo Date: !TARGET_DATE! (Short: !DATE_SHORT!)
echo.

REM 競馬場コードリスト初期化
set "KEIBA_CODES="

REM 競馬場マッピング（スペース削除版）
set "CODE_30=門別"
set "CODE_35=盛岡"
set "CODE_36=水沢"
set "CODE_42=浦和"
set "CODE_43=船橋"
set "CODE_44=大井"
set "CODE_45=川崎"
set "CODE_46=金沢"
set "CODE_47=笠松"
set "CODE_48=名古屋"
set "CODE_50=園田"
set "CODE_51=姫路"
set "CODE_54=高知"
set "CODE_55=佐賀"

echo [Step 1] Detecting Phase 5 venues...
echo.

REM Phase 5 の ensemble.csv が存在する競馬場を検出（スペースなしで追加）
for %%C in (30 35 36 42 43 44 45 46 47 48 50 51 54 55) do (
    set "KNAME=!CODE_%%C!"
    set "ENSEMBLE_PATH=data\predictions\phase5\!KNAME!_!DATE_SHORT!_ensemble.csv"
    
    echo [DEBUG] Checking: !ENSEMBLE_PATH!
    
    if exist "!ENSEMBLE_PATH!" (
        echo [FOUND] !KNAME! (Code: %%C)
        REM スペースなしで追加
        if "!KEIBA_CODES!"=="" (
            set "KEIBA_CODES=%%C"
        ) else (
            set "KEIBA_CODES=!KEIBA_CODES! %%C"
        )
    ) else (
        echo [SKIP] !KNAME! - No Phase 5 data
    )
)

echo.

if "!KEIBA_CODES!"=="" (
    echo [ERROR] No Phase 5 data found for %TARGET_DATE%
    echo.
    echo Please verify:
    echo   1. Phase 0-5 has been executed successfully
    echo   2. data\predictions\phase5\ contains *_!DATE_SHORT!_ensemble.csv files
    echo   3. Date format is correct (YYYY-MM-DD)
    echo.
    goto :SHOW_USAGE
)

echo [Step 2] Detected venue codes: !KEIBA_CODES!
echo.
echo [Step 3] Processing each venue...
echo.

set SUCCESS_COUNT=0
set FAIL_COUNT=0

REM 各競馬場の処理（余分なスペースを削除）
for %%K in (!KEIBA_CODES!) do (
    REM スペース・タブ削除
    set "CODE=%%K"
    set "CODE=!CODE: =!"
    set "CODE=!CODE:	=!"
    
    set "VENUE_NAME=!CODE_%%K!"
    
    echo ==================================================
    echo Processing: !VENUE_NAME! (Code: !CODE!)
    echo ==================================================
    
    REM DAILY_OPERATION.bat を呼び出し（絶対パスで）
    call scripts\phase6_betting\DAILY_OPERATION.bat !CODE! !TARGET_DATE!
    
    if !errorlevel! equ 0 (
        echo [SUCCESS] !VENUE_NAME! completed
        set /a SUCCESS_COUNT+=1
    ) else (
        echo [ERROR] !VENUE_NAME! failed
        set /a FAIL_COUNT+=1
    )
    echo.
)

echo.
echo ==================================================
echo Batch Operation Summary
echo ==================================================
echo.
echo Success: !SUCCESS_COUNT! venue(s)
echo Failed : !FAIL_COUNT! venue(s)
echo.

if !FAIL_COUNT! gtr 0 (
    echo [WARNING] Some venues failed
    exit /b 1
)

echo [Step 4] Listing generated files...
echo.

for %%K in (!KEIBA_CODES!) do (
    set "CODE=%%K"
    set "CODE=!CODE: =!"
    set "CODE=!CODE:	=!"
    set "VENUE_NAME=!CODE_%%K!"
    
    set "NOTE_TXT=predictions\!VENUE_NAME!_!DATE_SHORT!_note.txt"
    set "BOOKERS_TXT=predictions\!VENUE_NAME!_!DATE_SHORT!_bookers.txt"
    set "TWEET_TXT=predictions\!VENUE_NAME!_!DATE_SHORT!_tweet.txt"
    
    if exist "!NOTE_TXT!" (
        echo [OK] !NOTE_TXT!
    )
    if exist "!BOOKERS_TXT!" (
        echo [OK] !BOOKERS_TXT!
    )
    if exist "!TWEET_TXT!" (
        echo [OK] !TWEET_TXT!
    )
)

echo.
echo ==================================================
echo All Completed!
echo ==================================================
echo.
echo Next step:
echo   explorer predictions
echo.
exit /b 0

:SHOW_USAGE
echo ==================================================
echo Keiba AI Batch Operation
echo ==================================================
echo.
echo Usage: BATCH_OPERATION.bat [Date]
echo.
echo Date Format: YYYY-MM-DD
echo.
echo Examples:
echo   BATCH_OPERATION.bat 2026-02-08
echo   BATCH_OPERATION.bat 2026-02-10
echo.
echo Note:
echo   Only venues with Phase 5 data will be processed.
echo   Make sure to run Phase 0-5 for each venue before running this script.
echo.
exit /b 1
