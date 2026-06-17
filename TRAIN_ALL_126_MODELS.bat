@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ================================================================================
echo Train All 126 Models with Distance Categories (Option 3: SHORT/MILE/LONG)
echo ================================================================================
echo.
echo Model Structure:
echo   - 14 Racecourses × 3 Distance Categories × 3 Tasks = 126 models
echo.
echo Distance Categories:
echo   - SHORT: ≤1200m
echo   - MILE:  1300-1700m  
echo   - LONG:  ≥1800m
echo.
echo Estimated Time:
echo   - Binary:     8-10 hours
echo   - Ranking:   10-12 hours
echo   - Regression: 7-9 hours
echo   - TOTAL:     25-30 hours
echo.
echo ================================================================================
echo.

set INPUT_DIR=data\features\67features_FULL
set OUTPUT_DIR_BINARY=models\binary_distance
set OUTPUT_DIR_RANKING=models\ranking_distance
set OUTPUT_DIR_REGRESSION=models\regression_distance

REM Check input directory
if not exist "%INPUT_DIR%" (
    echo [ERROR] Input directory not found: %INPUT_DIR%
    echo Please ensure 67features_FULL directory exists with CSV files.
    pause
    exit /b 1
)

echo [INFO] Input directory: %INPUT_DIR%
echo [INFO] Output directories:
echo   - Binary:     %OUTPUT_DIR_BINARY%
echo   - Ranking:    %OUTPUT_DIR_RANKING%
echo   - Regression: %OUTPUT_DIR_REGRESSION%
echo.

REM Create output directories
if not exist "%OUTPUT_DIR_BINARY%" mkdir "%OUTPUT_DIR_BINARY%"
if not exist "%OUTPUT_DIR_RANKING%" mkdir "%OUTPUT_DIR_RANKING%"
if not exist "%OUTPUT_DIR_REGRESSION%" mkdir "%OUTPUT_DIR_REGRESSION%"

echo ================================================================================
echo STEP 1/3: Binary Classification Training (42 models)
echo ================================================================================
echo Start Time: %TIME%
echo.

python scripts\phase3_binary\train_phase3_binary_distance.py ^
    --input "%INPUT_DIR%" ^
    --output "%OUTPUT_DIR_BINARY%"

if errorlevel 1 (
    echo.
    echo [ERROR] Binary training failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Binary training completed!
echo End Time: %TIME%
echo.
echo ================================================================================
echo STEP 2/3: Ranking Model Training (42 models)
echo ================================================================================
echo Start Time: %TIME%
echo.

python scripts\phase4_ranking\train_phase4_ranking_distance.py ^
    --input "%INPUT_DIR%" ^
    --output "%OUTPUT_DIR_RANKING%"

if errorlevel 1 (
    echo.
    echo [ERROR] Ranking training failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Ranking training completed!
echo End Time: %TIME%
echo.
echo ================================================================================
echo STEP 3/3: Regression Model Training (42 models)
echo ================================================================================
echo Start Time: %TIME%
echo.

python scripts\phase4_regression\train_phase4_regression_distance.py ^
    --input "%INPUT_DIR%" ^
    --output "%OUTPUT_DIR_REGRESSION%"

if errorlevel 1 (
    echo.
    echo [ERROR] Regression training failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Regression training completed!
echo End Time: %TIME%
echo.
echo ================================================================================
echo ALL TRAINING COMPLETED!
echo ================================================================================
echo.
echo Total Models: 126 (14 racecourses × 3 categories × 3 tasks)
echo.
echo Output Directories:
echo   - Binary:     %OUTPUT_DIR_BINARY%
echo   - Ranking:    %OUTPUT_DIR_RANKING%
echo   - Regression: %OUTPUT_DIR_REGRESSION%
echo.
echo Model Naming Convention:
echo   [racecourse]_[SHORT|MILE|LONG]_[binary|ranking|regression]_model.txt
echo.
echo Examples:
echo   urawa_SHORT_binary_model.txt
echo   funabashi_MILE_ranking_model.txt
echo   ooi_LONG_regression_model.txt
echo.
echo ================================================================================
echo.
pause
