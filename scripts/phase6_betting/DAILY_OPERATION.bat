@echo off
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

if "%~1"=="" goto :SHOW_USAGE
if "%~2"=="" goto :SHOW_USAGE

set KEIBA_CODE=%~1
set TARGET_DATE=%~2

if "%KEIBA_CODE%"=="30" set KEIBA_NAME=Monbetsu
if "%KEIBA_CODE%"=="35" set KEIBA_NAME=Morioka
if "%KEIBA_CODE%"=="36" set KEIBA_NAME=Mizusawa
if "%KEIBA_CODE%"=="42" set KEIBA_NAME=Urawa
if "%KEIBA_CODE%"=="43" set KEIBA_NAME=Funabashi
if "%KEIBA_CODE%"=="44" set KEIBA_NAME=Ooi
if "%KEIBA_CODE%"=="45" set KEIBA_NAME=Kawasaki
if "%KEIBA_CODE%"=="46" set KEIBA_NAME=Kanazawa
if "%KEIBA_CODE%"=="47" set KEIBA_NAME=Kasamatsu
if "%KEIBA_CODE%"=="48" set KEIBA_NAME=Nagoya
if "%KEIBA_CODE%"=="50" set KEIBA_NAME=Sonoda
if "%KEIBA_CODE%"=="51" set KEIBA_NAME=Himeji
if "%KEIBA_CODE%"=="54" set KEIBA_NAME=Kochi
if "%KEIBA_CODE%"=="55" set KEIBA_NAME=Saga

if "%KEIBA_NAME%"=="" (
    echo [ERROR] Invalid venue code: %KEIBA_CODE%
    goto :SHOW_USAGE
)

set DATE_SHORT=%TARGET_DATE:-=%

set ENSEMBLE_CSV=data\predictions\phase5\%KEIBA_NAME%_%DATE_SHORT%_ensemble.csv
set NOTE_TXT=predictions\%KEIBA_NAME%_%DATE_SHORT%_note.txt
set BOOKERS_TXT=predictions\%KEIBA_NAME%_%DATE_SHORT%_bookers.txt

echo ==================================================
echo Local Keiba AI Prediction - Daily Operation
echo ==================================================
echo.
echo Venue: %KEIBA_NAME% (Code: %KEIBA_CODE%)
echo Date: %TARGET_DATE%
echo.
echo Input CSV: %ENSEMBLE_CSV%
echo Output 1  : %NOTE_TXT%
echo Output 2  : %BOOKERS_TXT%
echo.
echo ==================================================

if not exist "%ENSEMBLE_CSV%" (
    echo [ERROR] Input file not found
    echo File: %ENSEMBLE_CSV%
    echo.
    echo Please complete Phase 0-5 first
    exit /b 1
)

echo.
echo [Phase 6-1] Generating Note format text...
python scripts\phase6_betting\generate_distribution_note.py "%ENSEMBLE_CSV%" "%NOTE_TXT%"

if errorlevel 1 (
    echo [ERROR] Note format generation failed
    exit /b 1
)

echo [COMPLETE] Note format: %NOTE_TXT%
echo.

echo [Phase 6-2] Generating Bookers format text...
python scripts\phase6_betting\generate_distribution_bookers.py "%ENSEMBLE_CSV%" "%BOOKERS_TXT%"

if errorlevel 1 (
    echo [ERROR] Bookers format generation failed
    exit /b 1
)

echo [COMPLETE] Bookers format: %BOOKERS_TXT%
echo.

echo ==================================================
echo All processing complete!
echo ==================================================
echo.
echo Generated files:
echo   1. Note    : %NOTE_TXT%
echo   2. Bookers : %BOOKERS_TXT%
echo.
echo Next steps:
echo   1. Review files in notepad
echo   2. Copy and paste to Note
echo   3. Copy and paste to Bookers
echo.
echo Commands:
echo   notepad "%NOTE_TXT%"
echo   notepad "%BOOKERS_TXT%"
echo.
echo ==================================================
goto :EOF

:SHOW_USAGE
echo ==================================================
echo Local Keiba AI Prediction - Daily Operation
echo ==================================================
echo.
echo Usage:
echo   DAILY_OPERATION.bat [venue_code] [target_date]
echo.
echo Venue Codes:
echo   30: Monbetsu   35: Morioka    36: Mizusawa   42: Urawa
echo   43: Funabashi  44: Ooi        45: Kawasaki   46: Kanazawa
echo   47: Kasamatsu  48: Nagoya     50: Sonoda     51: Himeji
echo   54: Kochi      55: Saga
echo.
echo Date Format: YYYY-MM-DD
echo.
echo Examples:
echo   DAILY_OPERATION.bat 55 2026-02-08
echo   DAILY_OPERATION.bat 44 2026-02-10
echo   DAILY_OPERATION.bat 45 2026-02-10
echo.
echo ==================================================
exit /b 1
