@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM Phase 10: Daily Prediction System
REM Usage: RUN_PHASE10_DAILY.bat [KEIBAJO_CODE] [TARGET_DATE]
REM Example: RUN_PHASE10_DAILY.bat 43 2026-02-11

if "%~1"=="" (
    echo Usage: RUN_PHASE10_DAILY.bat [KEIBAJO_CODE] [TARGET_DATE]
    echo Example: RUN_PHASE10_DAILY.bat 43 2026-02-11
    echo.
    echo Venue Codes:
    echo   30: Monbetsu    35: Morioka     36: Mizusawa   42: Urawa
    echo   43: Funabashi   44: Ooi         45: Kawasaki   46: Kanazawa
    echo   47: Kasamatsu   48: Nagoya      50: Sonoda     51: Himeji
    echo   54: Kochi       55: Saga
    pause
    exit /b 1
)

if "%~2"=="" (
    echo Error: TARGET_DATE is required
    echo Usage: RUN_PHASE10_DAILY.bat [KEIBAJO_CODE] [TARGET_DATE]
    pause
    exit /b 1
)

set KEIBAJO_CODE=%~1
set TARGET_DATE=%~2

REM Map venue code to name
set KEIBAJO_NAME=Unknown
if "%KEIBAJO_CODE%"=="30" set KEIBAJO_NAME=Monbetsu
if "%KEIBAJO_CODE%"=="35" set KEIBAJO_NAME=Morioka
if "%KEIBAJO_CODE%"=="36" set KEIBAJO_NAME=Mizusawa
if "%KEIBAJO_CODE%"=="42" set KEIBAJO_NAME=Urawa
if "%KEIBAJO_CODE%"=="43" set KEIBAJO_NAME=Funabashi
if "%KEIBAJO_CODE%"=="44" set KEIBAJO_NAME=Ooi
if "%KEIBAJO_CODE%"=="45" set KEIBAJO_NAME=Kawasaki
if "%KEIBAJO_CODE%"=="46" set KEIBAJO_NAME=Kanazawa
if "%KEIBAJO_CODE%"=="47" set KEIBAJO_NAME=Kasamatsu
if "%KEIBAJO_CODE%"=="48" set KEIBAJO_NAME=Nagoya
if "%KEIBAJO_CODE%"=="50" set KEIBAJO_NAME=Sonoda
if "%KEIBAJO_CODE%"=="51" set KEIBAJO_NAME=Himeji
if "%KEIBAJO_CODE%"=="54" set KEIBAJO_NAME=Kochi
if "%KEIBAJO_CODE%"=="55" set KEIBAJO_NAME=Saga

echo ========================================
echo Phase 10: Daily Prediction System
echo ========================================
echo Venue: %KEIBAJO_NAME% (Code: %KEIBAJO_CODE%)
echo Date: %TARGET_DATE%
echo ========================================
echo.

REM Execute Phase 10 prediction
python scripts\phase10_daily_prediction\run_daily_prediction.py --venue-code %KEIBAJO_CODE% --date %TARGET_DATE% --bankroll 100000 --kelly-fraction 0.25

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Phase 10 failed
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo Phase 10 completed successfully!
echo ========================================
echo.
echo Next steps:
echo   Phase 6: Generate distribution text
echo   Command: scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE%
echo.
echo Output files:
echo   - data\predictions\phase10\*%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%*.csv
echo   - data\predictions\phase10\*%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%*.txt
echo ========================================
echo.

pause
