@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

echo ==================================================
echo 船橋競馬場 完全デバッグモード
echo ==================================================
echo.

set "TEST_CODE=43"
set "TEST_DATE=2026-02-10"
set "TEST_NAME=船橋"
set "DATE_SHORT=%TEST_DATE:-=%"

echo [Test Configuration]
echo   Venue Code: !TEST_CODE!
echo   Venue Name: !TEST_NAME!
echo   Date: !TEST_DATE!
echo   Date Short: !DATE_SHORT!
echo.

echo ==================================================
echo Step 1: ディレクトリ構造の確認
echo ==================================================
echo.

echo [1-1] data\predictions\phase5\ の存在確認
if exist "data\predictions\phase5\" (
    echo [OK] Phase 5 directory exists
) else (
    echo [ERROR] Phase 5 directory not found
    echo [ACTION] Creating directory...
    mkdir "data\predictions\phase5"
)
echo.

echo [1-2] predictions\ の存在確認
if exist "predictions\" (
    echo [OK] predictions directory exists
) else (
    echo [ERROR] predictions directory not found
    echo [ACTION] Creating directory...
    mkdir "predictions"
)
echo.

echo ==================================================
echo Step 2: Phase 5 ファイルの検証
echo ==================================================
echo.

set "ENSEMBLE_PATH=data\predictions\phase5\!TEST_NAME!_!DATE_SHORT!_ensemble.csv"
echo [2-1] Expected ensemble file: !ENSEMBLE_PATH!

if exist "!ENSEMBLE_PATH!" (
    echo [OK] Ensemble file found
    echo.
    echo [2-2] File size:
    for %%F in ("!ENSEMBLE_PATH!") do echo   Size: %%~zF bytes
    echo.
    echo [2-3] First 5 lines:
    type "!ENSEMBLE_PATH!" | more /E +0 | findstr /N "^" | findstr /R "^[1-5]:"
    echo.
) else (
    echo [ERROR] Ensemble file not found
    echo.
    echo [DIAGNOSTIC] Listing all files in data\predictions\phase5\:
    dir /b "data\predictions\phase5\*!DATE_SHORT!*"
    echo.
    echo [DIAGNOSTIC] Listing all files with "船橋" or "funabashi":
    dir /b /s "data\predictions\phase5\*船橋*"
    dir /b /s "data\predictions\phase5\*funabashi*"
    echo.
    echo [ACTION REQUIRED] Run Phase 0-5 first:
    echo   run_all.bat 43 2026-02-10
    echo.
    pause
    exit /b 1
)

echo ==================================================
echo Step 3: DAILY_OPERATION.bat の呼び出しテスト
echo ==================================================
echo.

echo [3-1] Testing argument handling...
echo   Input Code: [!TEST_CODE!]
echo   Input Date: [!TEST_DATE!]
echo.

REM スペースを削除した引数を作成
set "CLEAN_CODE=!TEST_CODE: =!"
set "CLEAN_CODE=!CLEAN_CODE:	=!"
set "CLEAN_DATE=!TEST_DATE: =!"
set "CLEAN_DATE=!CLEAN_DATE:	=!"

echo [3-2] Cleaned arguments:
echo   Clean Code: [!CLEAN_CODE!]
echo   Clean Date: [!CLEAN_DATE!]
echo.

echo [3-3] Calling DAILY_OPERATION.bat...
echo.

call scripts\phase6_betting\DAILY_OPERATION.bat !CLEAN_CODE! !CLEAN_DATE!

if !errorlevel! equ 0 (
    echo.
    echo [OK] DAILY_OPERATION.bat succeeded
) else (
    echo.
    echo [ERROR] DAILY_OPERATION.bat failed with errorlevel: !errorlevel!
    echo.
    echo [DIAGNOSTIC] Possible causes:
    echo   1. Python script errors
    echo   2. Missing dependencies
    echo   3. Encoding issues
    echo   4. Path problems
    echo.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo Step 4: 出力ファイルの検証
echo ==================================================
echo.

set "NOTE_FILE=predictions\!TEST_NAME!_!DATE_SHORT!_note.txt"
set "BOOKERS_FILE=predictions\!TEST_NAME!_!DATE_SHORT!_bookers.txt"
set "TWEET_FILE=predictions\!TEST_NAME!_!DATE_SHORT!_tweet.txt"

echo [4-1] Checking note.txt...
if exist "!NOTE_FILE!" (
    echo [OK] !NOTE_FILE! exists
    for %%F in ("!NOTE_FILE!") do echo   Size: %%~zF bytes
) else (
    echo [ERROR] !NOTE_FILE! not found
)
echo.

echo [4-2] Checking bookers.txt...
if exist "!BOOKERS_FILE!" (
    echo [OK] !BOOKERS_FILE! exists
    for %%F in ("!BOOKERS_FILE!") do echo   Size: %%~zF bytes
) else (
    echo [ERROR] !BOOKERS_FILE! not found
)
echo.

echo [4-3] Checking tweet.txt...
if exist "!TWEET_FILE!" (
    echo [OK] !TWEET_FILE! exists
    for %%F in ("!TWEET_FILE!") do echo   Size: %%~zF bytes
) else (
    echo [ERROR] !TWEET_FILE! not found
)
echo.

echo ==================================================
echo Step 5: 最終結果
echo ==================================================
echo.

set ALL_OK=1

if not exist "!NOTE_FILE!" set ALL_OK=0
if not exist "!BOOKERS_FILE!" set ALL_OK=0
if not exist "!TWEET_FILE!" set ALL_OK=0

if !ALL_OK! equ 1 (
    echo [SUCCESS] All files generated successfully!
    echo.
    echo Generated files:
    echo   - !NOTE_FILE!
    echo   - !BOOKERS_FILE!
    echo   - !TWEET_FILE!
    echo.
    echo To open files:
    echo   notepad "!NOTE_FILE!"
    echo   notepad "!BOOKERS_FILE!"
    echo   notepad "!TWEET_FILE!"
    echo.
) else (
    echo [FAILURE] Some files were not generated
    echo.
    echo Please check:
    echo   1. Python environment is set up correctly
    echo   2. Required packages are installed
    echo   3. scripts\phase6_betting\*.py files exist
    echo   4. Run: python --version
    echo   5. Run: pip list
    echo.
)

echo ==================================================
echo Debug Complete
echo ==================================================
echo.

pause
