@echo off
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

if "%~1"=="" goto :SHOW_USAGE
if "%~2"=="" goto :SHOW_USAGE

set KEIBA_CODE=%~1
set TARGET_DATE=%~2
set DATE_SHORT=%TARGET_DATE:-=%

if "%KEIBA_CODE%"=="30" set KEIBA_NAME=門別
if "%KEIBA_CODE%"=="35" set KEIBA_NAME=盛岡
if "%KEIBA_CODE%"=="36" set KEIBA_NAME=水沢
if "%KEIBA_CODE%"=="42" set KEIBA_NAME=浦和
if "%KEIBA_CODE%"=="43" set KEIBA_NAME=船橋
if "%KEIBA_CODE%"=="44" set KEIBA_NAME=大井
if "%KEIBA_CODE%"=="45" set KEIBA_NAME=川崎
if "%KEIBA_CODE%"=="46" set KEIBA_NAME=金沢
if "%KEIBA_CODE%"=="47" set KEIBA_NAME=笠松
if "%KEIBA_CODE%"=="48" set KEIBA_NAME=名古屋
if "%KEIBA_CODE%"=="50" set KEIBA_NAME=園田
if "%KEIBA_CODE%"=="51" set KEIBA_NAME=姫路
if "%KEIBA_CODE%"=="54" set KEIBA_NAME=高知
if "%KEIBA_CODE%"=="55" set KEIBA_NAME=佐賀

if "%KEIBA_NAME%"=="" (
    echo [ERROR] Invalid venue code: %KEIBA_CODE%
    goto :SHOW_USAGE
)

set ENSEMBLE_CSV=data\predictions\phase5\%KEIBA_NAME%_%DATE_SHORT%_ensemble.csv
set NOTE_TXT=predictions\%KEIBA_NAME%_%DATE_SHORT%_note.txt
set BOOKERS_TXT=predictions\%KEIBA_NAME%_%DATE_SHORT%_bookers.txt
set TWEET_TXT=predictions\%KEIBA_NAME%_%DATE_SHORT%_tweet.txt

echo ==================================================
echo Keiba AI Daily Operation
echo ==================================================
echo.
echo Venue: %KEIBA_NAME% (Code: %KEIBA_CODE%)
echo Date: %TARGET_DATE%
echo.
echo Input : %ENSEMBLE_CSV%
echo Output: %NOTE_TXT%
echo        %BOOKERS_TXT%
echo        %TWEET_TXT%
echo.
echo ==================================================

if not exist "%ENSEMBLE_CSV%" (
    echo.
    echo [ERROR] Input file not found
    echo File: %ENSEMBLE_CSV%
    echo.
    echo Please run Phase 0-5 first
    echo.
    exit /b 1
)

echo.
echo [1/3] Generating Note format...
python scripts\phase6_betting\generate_distribution_note.py "%ENSEMBLE_CSV%" "%NOTE_TXT%"

if errorlevel 1 (
    echo [ERROR] Note generation failed
    exit /b 1
)

echo [OK] Note: %NOTE_TXT%
echo.

echo [2/3] Generating Bookers format...
python scripts\phase6_betting\generate_distribution_bookers.py "%ENSEMBLE_CSV%" "%BOOKERS_TXT%"

if errorlevel 1 (
    echo [ERROR] Bookers generation failed
    exit /b 1
)

echo [OK] Bookers: %BOOKERS_TXT%
echo.

echo [3/3] Generating Tweet format...
python scripts\phase6_betting\generate_distribution_tweet.py "%ENSEMBLE_CSV%" "%TWEET_TXT%"

if errorlevel 1 (
    echo [ERROR] Tweet generation failed
    exit /b 1
)

echo [OK] Tweet: %TWEET_TXT%
echo.

echo ==================================================
echo All Complete!
echo ==================================================
echo.
echo Files:
echo   1. Note    : %NOTE_TXT%
echo   2. Bookers : %BOOKERS_TXT%
echo   3. Tweet   : %TWEET_TXT%
echo.
echo Commands:
echo   notepad "%NOTE_TXT%"
echo   notepad "%BOOKERS_TXT%"
echo   notepad "%TWEET_TXT%"
echo.
echo ==================================================
goto :EOF

:SHOW_USAGE
echo ==================================================
echo Keiba AI Daily Operation
echo ==================================================
echo.
echo Usage:
echo   DAILY_OPERATION.bat [code] [date]
echo.
echo Venue Codes:
echo   30=Monbetsu  35=Morioka   36=Mizusawa  42=Urawa
echo   43=Funabashi 44=Ooi       45=Kawasaki  46=Kanazawa
echo   47=Kasamatsu 48=Nagoya    50=Sonoda    51=Himeji
echo   54=Kochi     55=Saga
echo.
echo Date Format: YYYY-MM-DD
echo.
echo Examples:
echo   DAILY_OPERATION.bat 55 2026-02-08
echo   DAILY_OPERATION.bat 44 2026-02-10
echo.
echo ==================================================
exit /b 1
