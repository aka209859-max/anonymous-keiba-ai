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

set "KEIBAJO_NAME="
if "%KEIBAJO_CODE%"=="30" set "KEIBAJO_NAME=ñÂï "
if "%KEIBAJO_CODE%"=="35" set "KEIBAJO_NAME=ê∑â™"
if "%KEIBAJO_CODE%"=="36" set "KEIBAJO_NAME=êÖëÚ"
if "%KEIBAJO_CODE%"=="42" set "KEIBAJO_NAME=âYòa"
if "%KEIBAJO_CODE%"=="43" set "KEIBAJO_NAME=ëDã¥"
if "%KEIBAJO_CODE%"=="44" set "KEIBAJO_NAME=ëÂà‰"
if "%KEIBAJO_CODE%"=="45" set "KEIBAJO_NAME=êÏçË"
if "%KEIBAJO_CODE%"=="46" set "KEIBAJO_NAME=ã‡ëÚ"
if "%KEIBAJO_CODE%"=="47" set "KEIBAJO_NAME=ä}èº"
if "%KEIBAJO_CODE%"=="48" set "KEIBAJO_NAME=ñºå√âÆ"
if "%KEIBAJO_CODE%"=="50" set "KEIBAJO_NAME=âÄìc"
if "%KEIBAJO_CODE%"=="51" set "KEIBAJO_NAME=ïPòH"
if "%KEIBAJO_CODE%"=="54" set "KEIBAJO_NAME=çÇím"
if "%KEIBAJO_CODE%"=="55" set "KEIBAJO_NAME=ç≤âÍ"

echo [Phase 0] Starting...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %TARGET_DATE%
if errorlevel 1 exit /b 1

set "INPUT_CSV=data\raw\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_raw.csv"
set "OUTPUT_CSV=data\features\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv"

echo [Phase 1] Starting...
python scripts\phase1_feature_engineering\prepare_features.py "%INPUT_CSV%" --output "%OUTPUT_CSV%"
if errorlevel 1 exit /b 1

set "FEATURES_CSV=%OUTPUT_CSV%"
set "OUTPUT_P3=data\predictions\phase3\%KEIBAJO_NAME%_%DATE_SHORT%_phase3_binary.csv"

echo [Phase 3] Starting...
python scripts\phase3_binary\predict_phase3_inference.py "%FEATURES_CSV%" models\binary "%OUTPUT_P3%"
if errorlevel 1 exit /b 1

set "OUTPUT_P4_RANK=data\predictions\phase4_ranking\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_ranking.csv"

echo [Phase 4-1] Starting...
python scripts\phase4_ranking\predict_phase4_ranking_inference.py "%FEATURES_CSV%" models\ranking "%OUTPUT_P4_RANK%"
if errorlevel 1 exit /b 1

set "OUTPUT_P4_REG=data\predictions\phase4_regression\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_regression.csv"

echo [Phase 4-2] Starting...
python scripts\phase4_regression\predict_phase4_regression_inference.py "%FEATURES_CSV%" models\regression "%OUTPUT_P4_REG%"
if errorlevel 1 exit /b 1

set "OUTPUT_ENSEMBLE=data\predictions\phase5\%KEIBAJO_NAME%_%DATE_SHORT%_ensemble.csv"

echo [Phase 5] Starting...
python scripts\phase5_ensemble\ensemble_predictions.py "%OUTPUT_P3%" "%OUTPUT_P4_RANK%" "%OUTPUT_P4_REG%" "%OUTPUT_ENSEMBLE%"
if errorlevel 1 exit /b 1

echo [Phase 6] Starting...
call scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE%

echo Complete!

endlocal
