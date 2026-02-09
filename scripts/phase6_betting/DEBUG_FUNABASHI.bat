@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

echo ==================================================
echo 船橋データ検証スクリプト
echo ==================================================
echo.
echo Date: 2026-02-10
echo Venue: 船橋 (Code: 43)
echo.
echo ==================================================
echo.

set TARGET_DATE=2026-02-10
set DATE_SHORT=20260210
set KEIBA_NAME=船橋

echo [1/5] Checking Phase 5 file...
set ENSEMBLE_CSV=data\predictions\phase5\%KEIBA_NAME%_%DATE_SHORT%_ensemble.csv
echo File: %ENSEMBLE_CSV%

if exist "%ENSEMBLE_CSV%" (
    echo [OK] File exists
    echo.
    echo File details:
    dir "%ENSEMBLE_CSV%"
    echo.
    echo First 10 lines:
    type "%ENSEMBLE_CSV%" | more
) else (
    echo [ERROR] File not found
    echo.
    echo Expected location: %ENSEMBLE_CSV%
    echo.
    echo Please check:
    echo   1. Run Phase 0-5 first: run_all.bat 43 2026-02-10
    echo   2. Check data\predictions\phase5\ folder
    echo   3. Verify folder structure
    echo.
    echo Listing all Phase 5 files:
    dir data\predictions\phase5\*20260210*.csv
    exit /b 1
)
echo.

echo [2/5] Checking output directory...
if not exist "predictions" (
    echo [WARNING] predictions folder does not exist, creating...
    mkdir predictions
    echo [OK] Created predictions folder
) else (
    echo [OK] predictions folder exists
)
echo.

echo [3/5] Testing Note generation...
python scripts\phase6_betting\generate_distribution_note.py "%ENSEMBLE_CSV%" "predictions\%KEIBA_NAME%_%DATE_SHORT%_note.txt"

if errorlevel 1 (
    echo [ERROR] Note generation failed
    exit /b 1
)

if exist "predictions\%KEIBA_NAME%_%DATE_SHORT%_note.txt" (
    echo [OK] Note file created
    echo.
    echo File details:
    dir "predictions\%KEIBA_NAME%_%DATE_SHORT%_note.txt"
) else (
    echo [ERROR] Note file not created
    exit /b 1
)
echo.

echo [4/5] Testing Bookers generation...
python scripts\phase6_betting\generate_distribution_bookers.py "%ENSEMBLE_CSV%" "predictions\%KEIBA_NAME%_%DATE_SHORT%_bookers.txt"

if errorlevel 1 (
    echo [ERROR] Bookers generation failed
    exit /b 1
)

if exist "predictions\%KEIBA_NAME%_%DATE_SHORT%_bookers.txt" (
    echo [OK] Bookers file created
    echo.
    echo File details:
    dir "predictions\%KEIBA_NAME%_%DATE_SHORT%_bookers.txt"
) else (
    echo [ERROR] Bookers file not created
    exit /b 1
)
echo.

echo [5/5] Testing Tweet generation...
python scripts\phase6_betting\generate_distribution_tweet.py "%ENSEMBLE_CSV%" "predictions\%KEIBA_NAME%_%DATE_SHORT%_tweet.txt"

if errorlevel 1 (
    echo [ERROR] Tweet generation failed
    exit /b 1
)

if exist "predictions\%KEIBA_NAME%_%DATE_SHORT%_tweet.txt" (
    echo [OK] Tweet file created
    echo.
    echo File details:
    dir "predictions\%KEIBA_NAME%_%DATE_SHORT%_tweet.txt"
) else (
    echo [ERROR] Tweet file not created
    exit /b 1
)
echo.

echo ==================================================
echo All Tests Passed!
echo ==================================================
echo.
echo Generated files:
dir predictions\%KEIBA_NAME%_%DATE_SHORT%*.txt
echo.
echo ==================================================
