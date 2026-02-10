@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM =========================================================
REM Phase 7: Boruta Feature Selection for 14 Venues
REM =========================================================

cd /d E:\anonymous-keiba-ai

echo ================================================================================
echo Phase 7: Boruta Feature Selection for 14 Venues
echo ================================================================================
echo.

REM Create output directory
if not exist "data\features\selected" mkdir "data\features\selected"

REM Venue Code Mapping
set VENUES[30]=Monbetsu
set VENUES[35]=Morioka
set VENUES[36]=Mizusawa
set VENUES[42]=Urawa
set VENUES[43]=Funabashi
set VENUES[44]=Ooi
set VENUES[45]=Kawasaki
set VENUES[46]=Kanazawa
set VENUES[47]=Kasamatsu
set VENUES[48]=Nagoya
set VENUES[50]=Sonoda
set VENUES[51]=Himeji
set VENUES[54]=Kochi
set VENUES[55]=Saga

REM Training Period Settings
set PERIOD[30]=2020-2025
set PERIOD[35]=2020-2025
set PERIOD[36]=2020-2025
set PERIOD[42]=2020-2025
set PERIOD[43]=2020-2025
set PERIOD[44]=2023-2025
set PERIOD[45]=2020-2025
set PERIOD[46]=2020-2025
set PERIOD[47]=2020-2025
set PERIOD[48]=2022-2025
set PERIOD[50]=2020-2025
set PERIOD[51]=2020-2025
set PERIOD[54]=2020-2025
set PERIOD[55]=2020-2025

REM Counters
set TOTAL=0
set SUCCESS=0
set FAIL=0

REM Loop through 14 venues
for %%C in (30 35 36 42 43 44 45 46 47 48 50 51 54 55) do (
    set /a TOTAL+=1
    
    set CODE=%%C
    set VENUE=!VENUES[%%C]!
    set PERIOD_STR=!PERIOD[%%C]!
    
    echo.
    echo --------------------------------------------------------------------------------
    echo [!TOTAL!/14] !VENUE! ^(Code: !CODE!^) - !PERIOD_STR!
    echo --------------------------------------------------------------------------------
    
    REM Generate filename (romaji)
    if "!CODE!"=="30" set FILENAME=monbetsu
    if "!CODE!"=="35" set FILENAME=morioka
    if "!CODE!"=="36" set FILENAME=mizusawa
    if "!CODE!"=="42" set FILENAME=urawa
    if "!CODE!"=="43" set FILENAME=funabashi
    if "!CODE!"=="44" set FILENAME=ooi
    if "!CODE!"=="45" set FILENAME=kawasaki
    if "!CODE!"=="46" set FILENAME=kanazawa
    if "!CODE!"=="47" set FILENAME=kasamatsu
    if "!CODE!"=="48" set FILENAME=nagoya
    if "!CODE!"=="50" set FILENAME=sonoda
    if "!CODE!"=="51" set FILENAME=himeji
    if "!CODE!"=="54" set FILENAME=kochi
    if "!CODE!"=="55" set FILENAME=saga
    
    set INPUT_CSV=!FILENAME!_!PERIOD_STR!_v3.csv
    set OUTPUT_CSV=data\features\selected\!FILENAME!_selected_features.csv
    
    REM Check input file
    if not exist "!INPUT_CSV!" (
        echo [ERROR] Input file not found: !INPUT_CSV!
        echo         Please run EXTRACT_ALL_TRAINING_DATA.bat first
        set /a FAIL+=1
    ) else (
        REM Check if output already exists
        if exist "!OUTPUT_CSV!" (
            echo [SKIP] Already exists: !OUTPUT_CSV!
            set /a SUCCESS+=1
        ) else (
            echo [RUN] Running Boruta feature selection...
            python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
            
            if exist "!OUTPUT_CSV!" (
                echo [OK] Success: !OUTPUT_CSV!
                set /a SUCCESS+=1
            ) else (
                echo [ERROR] Failed: !OUTPUT_CSV!
                set /a FAIL+=1
            )
        )
    )
)

echo.
echo ================================================================================
echo Phase 7 Complete
echo ================================================================================
echo Total: !TOTAL! venues
echo Success: !SUCCESS! venues
echo Failed: !FAIL! venues
echo ================================================================================

REM Show generated files
echo.
echo Generated files:
dir /b data\features\selected\*_selected_features.csv 2>nul
echo.
dir /b data\features\selected\*_importance.png 2>nul
echo.
dir /b data\features\selected\*_boruta_report.json 2>nul

if !FAIL! gtr 0 (
    echo [WARNING] Some venues failed Boruta feature selection
    exit /b 1
) else (
    echo [SUCCESS] All 14 venues completed Phase 7!
    echo.
    echo Next step: Run Phase 8 Optuna auto-tuning
    echo   RUN_PHASE8_ALL_VENUES.bat
)

pause
