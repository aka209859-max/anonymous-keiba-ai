@echo off
chcp 932 >nul
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if "%~1"=="" (
    echo Usage: run_all.bat [KEIBAJO_CODE] [DATE]
    echo Example: run_all.bat 43 2026-02-13
    exit /b 1
)
if "%~2"=="" (
    echo Usage: run_all.bat [KEIBAJO_CODE] [DATE]
    echo Example: run_all.bat 43 2026-02-13
    exit /b 1
)

set "KEIBAJO_CODE=%~1"
set "TARGET_DATE=%~2"

for /f "tokens=1,2,3 delims=-" %%a in ("%TARGET_DATE%") do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)
set "DATE_SHORT=%YEAR%%MONTH%%DAY%"

echo [Phase 0] Starting...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %TARGET_DATE%
if errorlevel 1 exit /b 1

echo [Phase 1] Starting...
python scripts\phase1_feature_engineering\prepare_features_safe.py %KEIBAJO_CODE% %YEAR% %MONTH% %DATE_SHORT%
if errorlevel 1 exit /b 1

echo [Phase 3-4-5] Finding feature file...
for /f "delims=" %%F in ('dir /b /s data\features\%YEAR%\%MONTH%\*%DATE_SHORT%_features.csv 2^>nul ^| findstr /v "名古屋"') do set "FEATURES_CSV=%%F"
if not defined FEATURES_CSV (
    echo [ERROR] Feature file not found
    exit /b 1
)
echo Found: %FEATURES_CSV%

echo [Phase 3] Starting...
python scripts\phase3_binary\predict_phase3_inference.py "%FEATURES_CSV%" models\binary "data\predictions\phase3\temp_%DATE_SHORT%_phase3_binary.csv"
if errorlevel 1 exit /b 1

echo [Phase 4-1] Starting...
python scripts\phase4_ranking\predict_phase4_ranking_inference.py "%FEATURES_CSV%" models\ranking "data\predictions\phase4_ranking\temp_%DATE_SHORT%_phase4_ranking.csv"
if errorlevel 1 exit /b 1

echo [Phase 4-2] Starting...
python scripts\phase4_regression\predict_phase4_regression_inference.py "%FEATURES_CSV%" models\regression "data\predictions\phase4_regression\temp_%DATE_SHORT%_phase4_regression.csv"
if errorlevel 1 exit /b 1

echo [Phase 5] Starting...
python scripts\phase5_ensemble\ensemble_predictions.py "data\predictions\phase3\temp_%DATE_SHORT%_phase3_binary.csv" "data\predictions\phase4_ranking\temp_%DATE_SHORT%_phase4_ranking.csv" "data\predictions\phase4_regression\temp_%DATE_SHORT%_phase4_regression.csv" "data\predictions\phase5\temp_%DATE_SHORT%_ensemble.csv"
if errorlevel 1 exit /b 1

echo [Phase 6] Starting...
call scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE% "data\predictions\phase5\temp_%DATE_SHORT%_ensemble.csv"

echo Complete!
endlocal
