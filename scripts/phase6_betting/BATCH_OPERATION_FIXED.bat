@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

if "%~1"=="" goto :SHOW_USAGE

set "TARGET_DATE=%~1"
set "TARGET_DATE=%TARGET_DATE: =%"
set "TARGET_DATE=%TARGET_DATE:	=%"
set "DATE_SHORT=%TARGET_DATE:-=%"

REM ============================================================
REM モード選択（第2引数で新モデル/旧モデルを選択）
REM ============================================================
set "USE_OPTIMIZED=0"
if /i "%~2"=="optimized" set "USE_OPTIMIZED=1"
if /i "%~2"=="new" set "USE_OPTIMIZED=1"

if "!USE_OPTIMIZED!"=="1" (
    set "MODEL_TYPE=New Model (Phase 7-8-5 Optimized)"
    set "ENSEMBLE_SUFFIX=_ensemble_optimized.csv"
) else (
    set "MODEL_TYPE=Old Model (Phase 3-4-5)"
    set "ENSEMBLE_SUFFIX=_ensemble.csv"
)

echo ==================================================
echo Keiba AI Batch Operation
echo ==================================================
echo.
echo Date: !TARGET_DATE! (Short: !DATE_SHORT!)
echo Model: !MODEL_TYPE!
echo.

set "KEIBA_CODES="

REM 競馬場マッピング
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

echo [Step 1] Detecting Phase 5 venues with !MODEL_TYPE!...
echo.

REM Phase 5 の ensemble*.csv が存在する競馬場を検出
for %%C in (30 35 36 42 43 44 45 46 47 48 50 51 54 55) do (
    set "KNAME=!CODE_%%C!"
    set "ENSEMBLE_PATH=data\predictions\phase5\!KNAME!_!DATE_SHORT!!ENSEMBLE_SUFFIX!"
    
    echo [DEBUG] Checking: !ENSEMBLE_PATH!
    
    if exist "!ENSEMBLE_PATH!" (
        echo [FOUND] !KNAME! (Code: %%C)
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
    echo   1. Phase 0-5 (or Phase 0-7-8-5) has been executed successfully
    echo   2. data\predictions\phase5\ contains *!ENSEMBLE_SUFFIX! files
    echo   3. Date format is correct (YYYY-MM-DD)
    echo   4. Model type is correct (use 'optimized' or 'new' for new model)
    echo.
    goto :SHOW_USAGE
)

echo [Step 2] Detected venue codes: !KEIBA_CODES!
echo.
echo [Step 3] Processing each venue with !MODEL_TYPE!...
echo.

set SUCCESS_COUNT=0
set FAIL_COUNT=0

REM 各競馬場の処理（スペース・タブを削除）
for %%K in (!KEIBA_CODES!) do (
    set "CODE=%%K"
    set "CODE=!CODE: =!"
    set "CODE=!CODE:	=!"
    
    set "VENUE_NAME=!CODE_%%K!"
    
    echo ==================================================
    echo Processing: !VENUE_NAME! (Code: !CODE!)
    echo ==================================================
    
    REM アンサンブルファイルパスを構築
    set "ENSEMBLE_PATH=data\predictions\phase5\!VENUE_NAME!_!DATE_SHORT!!ENSEMBLE_SUFFIX!"
    
    REM DAILY_OPERATION.bat を第3引数付きで呼び出し
    call scripts\phase6_betting\DAILY_OPERATION.bat !CODE! !TARGET_DATE! "!ENSEMBLE_PATH!"
    
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
echo Model: !MODEL_TYPE!
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
    
    if exist "!NOTE_TXT!" echo [OK] !NOTE_TXT!
    if exist "!BOOKERS_TXT!" echo [OK] !BOOKERS_TXT!
    if exist "!TWEET_TXT!" echo [OK] !TWEET_TXT!
)

echo.
echo ==================================================
echo All Completed!
echo ==================================================
echo.
echo Next step: explorer predictions
echo.
exit /b 0

:SHOW_USAGE
echo ==================================================
echo Keiba AI Batch Operation
echo ==================================================
echo.
echo Usage: BATCH_OPERATION.bat [Date] [Model Type (optional)]
echo.
echo Date Format: YYYY-MM-DD
echo Model Type:
echo   (none)    : Old model (Phase 3-4-5 ensemble.csv)
echo   optimized : New model (Phase 7-8-5 ensemble_optimized.csv)
echo   new       : New model (alias for 'optimized')
echo.
echo Examples:
echo   REM Old model (Phase 3-4-5)
echo   BATCH_OPERATION.bat 2026-02-10
echo.
echo   REM New model (Phase 7-8-5)
echo   BATCH_OPERATION.bat 2026-02-10 optimized
echo   BATCH_OPERATION.bat 2026-02-10 new
echo.
exit /b 1
