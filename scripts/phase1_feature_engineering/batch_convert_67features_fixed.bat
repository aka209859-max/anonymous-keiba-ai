@echo off
setlocal enabledelayedexpansion
REM Batch Convert 14 Racecourses from 50 features to 67 features
REM Date: 2026-05-05

chcp 65001 > nul

echo ========================================
echo Convert 14 Racecourses to 67 Features
echo ========================================
echo.

cd /d %~dp0

set INPUT_DIR=..\..\old\data\training_csv
set OUTPUT_DIR=..\..\data\features\67features
set SCRIPT=add_statistical_features.py

REM Create output directory
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo Input directory: %INPUT_DIR%
echo Output directory: %OUTPUT_DIR%
echo.

echo ========================================
echo Processing 14 Racecourses...
echo ========================================
echo.

REM Process each racecourse
call :process_venue urawa 2020-2025
call :process_venue funabashi 2020-2025
call :process_venue kawasaki 2020-2025
call :process_venue ooi 2023-2025
call :process_venue monbetsu 2020-2025
call :process_venue morioka 2020-2025
call :process_venue mizusawa 2020-2025
call :process_venue kanazawa 2020-2025
call :process_venue kasamatsu 2020-2025
call :process_venue nagoya 2022-2025
call :process_venue sonoda 2020-2025
call :process_venue himeji 2020-2025
call :process_venue kochi 2020-2025
call :process_venue saga 2020-2025

goto :summary

:process_venue
set VENUE=%1
set YEARS=%2
set INPUT_FILE=%INPUT_DIR%\%VENUE%_%YEARS%_v3.csv
set OUTPUT_FILE=%OUTPUT_DIR%\%VENUE%_67features.csv

echo.
echo ========================================
echo Processing: %VENUE% (%YEARS%)
echo ========================================

if exist "%INPUT_FILE%" (
    echo Input: %INPUT_FILE%
    echo Output: %OUTPUT_FILE%
    
    python %SCRIPT% "%INPUT_FILE%" "%OUTPUT_FILE%"
    
    if errorlevel 1 (
        echo [ERROR] Failed to process %VENUE%
    ) else (
        echo [SUCCESS] %VENUE% processed successfully
    )
) else (
    echo [WARNING] Input file not found: %INPUT_FILE%
)

goto :eof

:summary
echo.
echo ========================================
echo Batch Conversion Complete!
echo ========================================
echo.

REM Summary
echo Summary:
set FILE_COUNT=0
for %%f in ("%OUTPUT_DIR%\*.csv") do set /a FILE_COUNT+=1
echo %FILE_COUNT% files created in %OUTPUT_DIR%
echo.

echo Output files:
dir /b "%OUTPUT_DIR%\*.csv" 2>nul
echo.

echo Next steps:
echo 1. Check output files: dir %OUTPUT_DIR%
echo 2. Verify column count (should be 67)
echo 3. Proceed to Phase 2-3: Model training
echo.

pause
