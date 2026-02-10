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

REM Venue mapping
set VENUE_30=monbetsu
set VENUE_35=morioka
set VENUE_36=mizusawa
set VENUE_42=urawa
set VENUE_43=funabashi
set VENUE_44=ooi
set VENUE_45=kawasaki
set VENUE_46=kanazawa
set VENUE_47=kasamatsu
set VENUE_48=nagoya
set VENUE_50=sonoda
set VENUE_51=himeji
set VENUE_54=kochi
set VENUE_55=saga

REM Learning period per venue
set PERIOD_30=2020_2025
set PERIOD_35=2020_2025
set PERIOD_36=2020_2025
set PERIOD_42=2020_2025
set PERIOD_43=2020_2025
set PERIOD_44=2023_2025
set PERIOD_45=2020_2025
set PERIOD_46=2020_2025
set PERIOD_47=2020_2025
set PERIOD_48=2022_2025
set PERIOD_50=2020_2025
set PERIOD_51=2020_2025
set PERIOD_54=2020_2025
set PERIOD_55=2020_2025

REM Optuna parameters
set N_TRIALS=100
set TIMEOUT=7200
set CV_FOLDS=5

set TOTAL=14
set SUCCESS=0
set FAIL=0

REM Process each venue
for %%C in (30 35 36 42 43 44 45 46 47 48 50 51 54 55) do (
    set /a TOTAL+=0
    set CODE=%%C
    
    REM Get venue name and period
    call set FILENAME=%%VENUE_!CODE!%%
    call set PERIOD_STR=%%PERIOD_!CODE!%%
    
    set INPUT_CSV=!FILENAME!_!PERIOD_STR!_v3.csv
    set SELECTED_FEATURES=data\features\selected\!FILENAME!_selected_features.csv
    set OUTPUT_PARAMS=data\models\tuned\!FILENAME!_best_params.csv
    
    echo.
    echo ----------------------------------------
    echo [!CODE!] Processing: !FILENAME!
    echo ----------------------------------------
    echo Input CSV: !INPUT_CSV!
    echo Selected Features: !SELECTED_FEATURES!
    echo Output: !OUTPUT_PARAMS!
    echo.
    
    REM Check if input CSV exists
    if not exist "!INPUT_CSV!" (
        echo [ERROR] Input CSV not found: !INPUT_CSV!
        set /a FAIL+=1
        goto :next_venue
    )
    
    REM Check if selected features exist
    if not exist "!SELECTED_FEATURES!" (
        echo [ERROR] Selected features not found: !SELECTED_FEATURES!
        set /a FAIL+=1
        goto :next_venue
    )
    
    REM Skip if output already exists
    if exist "!OUTPUT_PARAMS!" (
        echo [SKIP] Best params already exist: !OUTPUT_PARAMS!
        set /a SUCCESS+=1
        goto :next_venue
    )
    
    REM Run Optuna tuning
    echo [RUN] Starting Optuna tuning for !FILENAME!...
    python scripts\phase8_auto_tuning\run_optuna_tuning.py "!INPUT_CSV!" --n-trials !N_TRIALS! --timeout !TIMEOUT! --cv-folds !CV_FOLDS!
    
    REM Check if output was created
    if exist "!OUTPUT_PARAMS!" (
        echo [SUCCESS] Tuning completed: !OUTPUT_PARAMS!
        set /a SUCCESS+=1
    ) else (
        echo [FAIL] Tuning failed for !FILENAME!
        set /a FAIL+=1
    )
    
    :next_venue
)

echo.
echo ========================================
echo Phase 8 Complete Summary
echo ========================================
echo Total venues: !TOTAL!
echo Success: !SUCCESS!
echo Failed: !FAIL!
echo ========================================

if !FAIL! gtr 0 (
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
