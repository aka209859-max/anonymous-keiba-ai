@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Phase 8: Optuna Hyperparameter Tuning
echo 14 Venues - Batch Processing
echo ========================================
echo.

REM Ensure output directory exists
if not exist "data\models\tuned" mkdir data\models\tuned

REM Optuna parameters
set N_TRIALS=100
set TIMEOUT=7200
set CV_FOLDS=5

set TOTAL=14
set SUCCESS=0
set FAIL=0

REM Process each venue
set CODE=30
set FILENAME=monbetsu
set PERIOD_STR=2020_2025
call :process_venue

set CODE=35
set FILENAME=morioka
set PERIOD_STR=2020_2025
call :process_venue

set CODE=36
set FILENAME=mizusawa
set PERIOD_STR=2020_2025
call :process_venue

set CODE=42
set FILENAME=urawa
set PERIOD_STR=2020_2025
call :process_venue

set CODE=43
set FILENAME=funabashi
set PERIOD_STR=2020_2025
call :process_venue

set CODE=44
set FILENAME=ooi
set PERIOD_STR=2023_2025
call :process_venue

set CODE=45
set FILENAME=kawasaki
set PERIOD_STR=2020_2025
call :process_venue

set CODE=46
set FILENAME=kanazawa
set PERIOD_STR=2020_2025
call :process_venue

set CODE=47
set FILENAME=kasamatsu
set PERIOD_STR=2020_2025
call :process_venue

set CODE=48
set FILENAME=nagoya
set PERIOD_STR=2022_2025
call :process_venue

set CODE=50
set FILENAME=sonoda
set PERIOD_STR=2020_2025
call :process_venue

set CODE=51
set FILENAME=himeji
set PERIOD_STR=2020_2025
call :process_venue

set CODE=54
set FILENAME=kochi
set PERIOD_STR=2020_2025
call :process_venue

set CODE=55
set FILENAME=saga
set PERIOD_STR=2020_2025
call :process_venue

goto :summary

:process_venue
set INPUT_CSV=%FILENAME%_%PERIOD_STR%_v3.csv
set SELECTED_FEATURES=data\features\selected\%FILENAME%_selected_features.csv
set OUTPUT_PARAMS=data\models\tuned\%FILENAME%_best_params.csv

echo.
echo ----------------------------------------
echo [%CODE%] Processing: %FILENAME%
echo ----------------------------------------
echo Input CSV: %INPUT_CSV%
echo Selected Features: %SELECTED_FEATURES%
echo Output: %OUTPUT_PARAMS%
echo.

REM Check if input CSV exists
if not exist "%INPUT_CSV%" (
    echo [ERROR] Input CSV not found: %INPUT_CSV%
    set /a FAIL+=1
    goto :eof
)

REM Check if selected features exist
if not exist "%SELECTED_FEATURES%" (
    echo [ERROR] Selected features not found: %SELECTED_FEATURES%
    set /a FAIL+=1
    goto :eof
)

REM Skip if output already exists
if exist "%OUTPUT_PARAMS%" (
    echo [SKIP] Best params already exist: %OUTPUT_PARAMS%
    set /a SUCCESS+=1
    goto :eof
)

REM Run Optuna tuning
echo [RUN] Starting Optuna tuning for %FILENAME%...
python scripts\phase8_auto_tuning\run_optuna_tuning.py "%INPUT_CSV%" --n-trials %N_TRIALS% --timeout %TIMEOUT% --cv-folds %CV_FOLDS%

REM Check if output was created
if exist "%OUTPUT_PARAMS%" (
    echo [SUCCESS] Tuning completed: %OUTPUT_PARAMS%
    set /a SUCCESS+=1
) else (
    echo [FAIL] Tuning failed for %FILENAME%
    set /a FAIL+=1
)

goto :eof

:summary
echo.
echo ========================================
echo Phase 8 Complete Summary
echo ========================================
echo Total venues: %TOTAL%
echo Success: %SUCCESS%
echo Failed: %FAIL%
echo ========================================

if %FAIL% gtr 0 (
    echo.
    echo [WARNING] Some venues failed Optuna tuning
    exit /b 1
)

echo.
echo [SUCCESS] All 14 venues completed Optuna tuning!
echo.
echo Next step: Phase 9 - Model Training
echo Command: RUN_PHASE9_ALL_VENUES.bat
echo.
pause
