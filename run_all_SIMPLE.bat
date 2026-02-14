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
python scripts\phase1_feature_engineering\prepare_features_wrapper.py %KEIBAJO_CODE% %YEAR% %MONTH% %DATE_SHORT%
if errorlevel 1 exit /b 1

echo [Phase 3-4-5] Starting...
python scripts\run_prediction_pipeline.py %KEIBAJO_CODE% %YEAR% %MONTH% %DATE_SHORT%
if errorlevel 1 exit /b 1

echo [Phase 6] Starting...
call scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE%

echo Complete!

endlocal
