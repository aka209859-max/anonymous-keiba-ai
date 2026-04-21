@echo off
chcp 932 >nul
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if "%~1"=="" (
    echo Usage: run_all.bat [KEIBAJO_CODE] [DATE]
    exit /b 1
)

if "%~2"=="" (
    echo Usage: run_all.bat [KEIBAJO_CODE] [DATE]
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

REM Phase 1 Complete - auto-detect feature file by date only
echo Phase 1 Complete - Auto-detecting feature file...

REM Get the first matching file by date (ignore venue code mismatch)
for /f "delims=" %%F in ('dir /b data\features\%YEAR%\%MONTH%\*%DATE_SHORT%_features.csv 2^>nul') do (
    if not defined FEATURES_FILENAME set "FEATURES_FILENAME=%%F"
)

if not defined FEATURES_FILENAME (
    echo ERROR: Feature file not found for date %DATE_SHORT%
    echo Available files:
    dir /b data\features\%YEAR%\%MONTH%\*.csv 2>nul
    exit /b 1
)

set "FEATURES_CSV=data\features\%YEAR%\%MONTH%\%FEATURES_FILENAME%"

if not exist "%FEATURES_CSV%" (
    echo ERROR: Feature file not found: %FEATURES_CSV%
    exit /b 1
)

echo Found: %FEATURES_CSV%

echo [Phase 3] Starting...
python scripts\phase3_binary\predict_phase3_inference.py "%FEATURES_CSV%" models\binary data\predictions\phase3\temp_%DATE_SHORT%_phase3_binary.csv
if errorlevel 1 exit /b 1

echo [Phase 4-1] Starting...
python scripts\phase4_ranking\predict_phase4_ranking_inference.py "%FEATURES_CSV%" models\ranking data\predictions\phase4_ranking\temp_%DATE_SHORT%_phase4_ranking.csv
if errorlevel 1 exit /b 1

echo [Phase 4-2] Starting...
python scripts\phase4_regression\predict_phase4_regression_inference.py "%FEATURES_CSV%" models\regression data\predictions\phase4_regression\temp_%DATE_SHORT%_phase4_regression.csv
if errorlevel 1 exit /b 1

echo [Phase 5] Starting...
python scripts\phase5_ensemble\ensemble_predictions.py data\predictions\phase3\temp_%DATE_SHORT%_phase3_binary.csv data\predictions\phase4_ranking\temp_%DATE_SHORT%_phase4_ranking.csv data\predictions\phase4_regression\temp_%DATE_SHORT%_phase4_regression.csv data\predictions\phase5\temp_%DATE_SHORT%_ensemble.csv
if errorlevel 1 exit /b 1

echo [Phase 6] Starting...
call scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE% "data\predictions\phase5\temp_%DATE_SHORT%_ensemble.csv"

echo Complete!

endlocal
