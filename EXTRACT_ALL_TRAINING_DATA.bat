@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM =========================================================
REM Extract Training Data for 14 Venues
REM =========================================================

cd /d E:\anonymous-keiba-ai

echo ================================================================================
echo Phase 7 Preparation: Extract Training Data for 14 Venues
echo ================================================================================
echo.

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
set START[30]=2020
set END[30]=2025

set START[35]=2020
set END[35]=2025

set START[36]=2020
set END[36]=2025

set START[42]=2020
set END[42]=2025

set START[43]=2020
set END[43]=2025

set START[44]=2023
set END[44]=2025

set START[45]=2020
set END[45]=2025

set START[46]=2020
set END[46]=2025

set START[47]=2020
set END[47]=2025

set START[48]=2022
set END[48]=2025

set START[50]=2020
set END[50]=2025

set START[51]=2020
set END[51]=2025

set START[54]=2020
set END[54]=2025

set START[55]=2020
set END[55]=2025

REM Counters
set TOTAL=0
set SUCCESS=0
set FAIL=0

REM Loop through 14 venues
for %%C in (30 35 36 42 43 44 45 46 47 48 50 51 54 55) do (
    set /a TOTAL+=1
    
    set CODE=%%C
    set VENUE=!VENUES[%%C]!
    set START_YEAR=!START[%%C]!
    set END_YEAR=!END[%%C]!
    
    echo.
    echo --------------------------------------------------------------------------------
    echo [!TOTAL!/14] !VENUE! ^(Code: !CODE!^) - !START_YEAR! to !END_YEAR!
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
    
    set OUTPUT=!FILENAME!_!START_YEAR!-!END_YEAR!_v3.csv
    
    REM Check if file already exists
    if exist "!OUTPUT!" (
        echo [SKIP] Already exists: !OUTPUT!
        set /a SUCCESS+=1
    ) else (
        echo [RUN] Extracting data...
        python scripts\phase0_data_acquisition\extract_training_data_v2.py --keibajo !CODE! --start-date !START_YEAR! --end-date !END_YEAR! --output "!OUTPUT!"
        
        if exist "!OUTPUT!" (
            echo [OK] Success: !OUTPUT!
            set /a SUCCESS+=1
        ) else (
            echo [ERROR] Failed: !OUTPUT!
            set /a FAIL+=1
        )
    )
)

echo.
echo ================================================================================
echo Extraction Complete
echo ================================================================================
echo Total: !TOTAL! venues
echo Success: !SUCCESS! venues
echo Failed: !FAIL! venues
echo ================================================================================

if !FAIL! gtr 0 (
    echo [WARNING] Some venues failed to extract data
    exit /b 1
) else (
    echo [SUCCESS] All 14 venues completed!
    echo.
    echo Next step: Run Phase 7 Boruta feature selection
    echo   RUN_PHASE7_ALL_VENUES.bat
)

pause
