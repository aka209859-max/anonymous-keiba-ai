@echo off
REM Batch Convert 14 Racecourses from 50 features to 67 features
REM Date: 2026-05-05

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

REM 14 Racecourses
set VENUES=urawa funabashi kawasaki ooi monbetsu morioka mizusawa kanazawa kasamatsu nagoya sonoda himeji kochi saga

echo ========================================
echo Processing 14 Racecourses...
echo ========================================
echo.

for %%V in (%VENUES%) do (
    echo.
    echo ========================================
    echo Processing: %%V
    echo ========================================
    
    REM Find input file (support different year ranges)
    set INPUT_FILE=
    if exist "%INPUT_DIR%\%%V_2020-2025_v3.csv" set INPUT_FILE=%INPUT_DIR%\%%V_2020-2025_v3.csv
    if exist "%INPUT_DIR%\%%V_2023-2025_v3.csv" set INPUT_FILE=%INPUT_DIR%\%%V_2023-2025_v3.csv
    if exist "%INPUT_DIR%\%%V_2022-2025_v3.csv" set INPUT_FILE=%INPUT_DIR%\%%V_2022-2025_v3.csv
    
    if defined INPUT_FILE (
        echo Input: !INPUT_FILE!
        set OUTPUT_FILE=%OUTPUT_DIR%\%%V_67features.csv
        echo Output: !OUTPUT_FILE!
        
        python %SCRIPT% "!INPUT_FILE!" "!OUTPUT_FILE!"
        
        if errorlevel 1 (
            echo [ERROR] Failed to process %%V
        ) else (
            echo [SUCCESS] %%V processed successfully
        )
    ) else (
        echo [WARNING] Input file not found for %%V
    )
    
    echo.
)

echo ========================================
echo Batch Conversion Complete!
echo ========================================
echo.

REM Summary
echo Summary:
dir "%OUTPUT_DIR%\*.csv" 2>nul | find /c /v ""
echo files created in %OUTPUT_DIR%
echo.

echo Next steps:
echo 1. Check output files: dir %OUTPUT_DIR%
echo 2. Verify column count (should be 67)
echo 3. Proceed to Phase 2-3: Model training
echo.

pause
