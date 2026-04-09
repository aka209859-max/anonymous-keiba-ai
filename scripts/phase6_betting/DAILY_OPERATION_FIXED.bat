@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM カレントディレクトリをスクリプト実行ディレクトリのルートに設定
cd /d "%~dp0..\.."

if "%~1"=="" goto :SHOW_USAGE
if "%~2"=="" goto :SHOW_USAGE

REM 引数から余分なスペース・タブ・改行を完全削除
set "KEIBA_CODE=%~1"
set "KEIBA_CODE=%KEIBA_CODE: =%"
set "TARGET_DATE=%~2"
set "TARGET_DATE=%TARGET_DATE: =%"
set "DATE_SHORT=%TARGET_DATE:-=%"

set "KEIBA_NAME="

if "!KEIBA_CODE!"=="30" set "KEIBA_NAME=門別"
if "!KEIBA_CODE!"=="35" set "KEIBA_NAME=盛岡"
if "!KEIBA_CODE!"=="36" set "KEIBA_NAME=水沢"
if "!KEIBA_CODE!"=="42" set "KEIBA_NAME=浦和"
if "!KEIBA_CODE!"=="43" set "KEIBA_NAME=船橋"
if "!KEIBA_CODE!"=="44" set "KEIBA_NAME=大井"
if "!KEIBA_CODE!"=="45" set "KEIBA_NAME=川崎"
if "!KEIBA_CODE!"=="46" set "KEIBA_NAME=金沢"
if "!KEIBA_CODE!"=="47" set "KEIBA_NAME=笠松"
if "!KEIBA_CODE!"=="48" set "KEIBA_NAME=名古屋"
if "!KEIBA_CODE!"=="50" set "KEIBA_NAME=園田"
if "!KEIBA_CODE!"=="51" set "KEIBA_NAME=姫路"
if "!KEIBA_CODE!"=="54" set "KEIBA_NAME=高知"
if "!KEIBA_CODE!"=="55" set "KEIBA_NAME=佐賀"

if "!KEIBA_NAME!"=="" (
    echo [ERROR] Invalid venue code: !KEIBA_CODE!
    goto :SHOW_USAGE
)

REM アンサンブルファイルパス（第3引数で指定可能、指定なしは旧モデル）
if "%~3"=="" (
    set "ENSEMBLE_CSV=data\predictions\phase5\!KEIBA_NAME!_!DATE_SHORT!_ensemble.csv"
    echo [INFO] Using old model ensemble file
) else (
    set "ENSEMBLE_CSV=%~3"
    echo [INFO] Using custom ensemble file
)

set "NOTE_TXT=predictions\!KEIBA_NAME!_!DATE_SHORT!_note.txt"
set "BOOKERS_TXT=predictions\!KEIBA_NAME!_!DATE_SHORT!_bookers.txt"
set "TWEET_TXT=predictions\!KEIBA_NAME!_!DATE_SHORT!_tweet.txt"

echo ==================================================
echo Keiba AI Daily Operation
echo ==================================================
echo.
echo Venue: !KEIBA_NAME! (Code: !KEIBA_CODE!)
echo Date: !TARGET_DATE!
echo.
echo Input : !ENSEMBLE_CSV!
echo Output: !NOTE_TXT!
echo        !BOOKERS_TXT!
echo        !TWEET_TXT!
echo ==================================================
echo.

if not exist "!ENSEMBLE_CSV!" (
    echo [ERROR] Ensemble CSV not found: !ENSEMBLE_CSV!
    echo [INFO] Please run Phase 0-5 first.
    exit /b 1
)

echo [DEBUG] Ensemble CSV found: !ENSEMBLE_CSV!

REM note.txt 生成
echo [1/3] Generating note.txt...
python scripts\phase6_betting\generate_distribution_note.py "!ENSEMBLE_CSV!" "!NOTE_TXT!"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to generate note.txt
    exit /b 1
)
if not exist "!NOTE_TXT!" (
    echo [ERROR] note.txt was not created
    exit /b 1
)
echo [OK] note.txt created

REM bookers.txt 生成
echo [2/3] Generating bookers.txt...
python scripts\phase6_betting\generate_distribution_bookers.py "!ENSEMBLE_CSV!" "!BOOKERS_TXT!"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to generate bookers.txt
    exit /b 1
)
if not exist "!BOOKERS_TXT!" (
    echo [ERROR] bookers.txt was not created
    exit /b 1
)
echo [OK] bookers.txt created

REM tweet.txt 生成
echo [3/3] Generating tweet.txt...
python scripts\phase6_betting\generate_distribution_tweet.py "!ENSEMBLE_CSV!" "!TWEET_TXT!"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to generate tweet.txt
    exit /b 1
)
if not exist "!TWEET_TXT!" (
    echo [ERROR] tweet.txt was not created
    exit /b 1
)
echo [OK] tweet.txt created

echo.
echo ==================================================
echo Daily Operation Completed!
echo ==================================================
echo.
echo Generated files:
echo   - !NOTE_TXT!
echo   - !BOOKERS_TXT!
echo   - !TWEET_TXT!
echo.
echo To open the files, run:
echo   notepad "!NOTE_TXT!"
echo   notepad "!BOOKERS_TXT!"
echo   notepad "!TWEET_TXT!"
echo.
exit /b 0

:SHOW_USAGE
echo ==================================================
echo Keiba AI Daily Operation
echo ==================================================
echo.
echo Usage: DAILY_OPERATION.bat [Venue Code] [Date]
echo.
echo Venue Codes:
echo   30: 門別 (Monbetsu)   35: 盛岡 (Morioka)   36: 水沢 (Mizusawa)
echo   42: 浦和 (Urawa)      43: 船橋 (Funabashi) 44: 大井 (Ooi)
echo   45: 川崎 (Kawasaki)   46: 金沢 (Kanazawa)  47: 笠松 (Kasamatsu)
echo   48: 名古屋 (Nagoya)   50: 園田 (Sonoda)    51: 姫路 (Himeji)
echo   54: 高知 (Kochi)      55: 佐賀 (Saga)
echo.
echo Date Format: YYYY-MM-DD
echo.
echo Example:
echo   DAILY_OPERATION.bat 55 2026-02-08
echo   DAILY_OPERATION.bat 43 2026-02-10
echo.
exit /b 1
