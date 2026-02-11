@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM Phase 8 -> Phase 6 Integrated Workflow
REM Phase 8 optimized model prediction -> Phase 6 distribution text generation

if "%~1"=="" (
    echo Usage: RUN_PHASE8_TO_PHASE6.bat [VENUE_CODE] [TARGET_DATE]
    echo Example: RUN_PHASE8_TO_PHASE6.bat 43 2026-02-11
    echo.
    echo Venue Codes:
    echo   30: Monbetsu    35: Morioka     36: Mizusawa   42: Urawa
    echo   43: Funabashi   44: Ooi         45: Kawasaki   46: Kanazawa
    echo   47: Kasamatsu   48: Nagoya      50: Sonoda     51: Himeji
    echo   54: Kochi       55: Saga
    pause
    exit /b 1
)

if "%~2"=="" (
    echo Error: TARGET_DATE is required
    pause
    exit /b 1
)

set VENUE_CODE=%~1
set TARGET_DATE=%~2

REM Venue name mapping
set VENUE_NAME=Unknown
if "%VENUE_CODE%"=="30" set VENUE_NAME=Monbetsu
if "%VENUE_CODE%"=="35" set VENUE_NAME=Morioka
if "%VENUE_CODE%"=="36" set VENUE_NAME=Mizusawa
if "%VENUE_CODE%"=="42" set VENUE_NAME=Urawa
if "%VENUE_CODE%"=="43" set VENUE_NAME=Funabashi
if "%VENUE_CODE%"=="44" set VENUE_NAME=Ooi
if "%VENUE_CODE%"=="45" set VENUE_NAME=Kawasaki
if "%VENUE_CODE%"=="46" set VENUE_NAME=Kanazawa
if "%VENUE_CODE%"=="47" set VENUE_NAME=Kasamatsu
if "%VENUE_CODE%"=="48" set VENUE_NAME=Nagoya
if "%VENUE_CODE%"=="50" set VENUE_NAME=Sonoda
if "%VENUE_CODE%"=="51" set VENUE_NAME=Himeji
if "%VENUE_CODE%"=="54" set VENUE_NAME=Kochi
if "%VENUE_CODE%"=="55" set VENUE_NAME=Saga

echo ============================================================
echo Phase 8 -^> Phase 6 Integrated Workflow
echo ============================================================
echo Venue: %VENUE_NAME% (Code: %VENUE_CODE%)
echo Date: %TARGET_DATE%
echo ============================================================
echo.

REM Step 1: Phase 0-1 (Data acquisition + Feature generation)
echo [Step 1/3] Phase 0-1: Data acquisition + Feature generation
echo ------------------------------------------------------------
call run_all.bat %VENUE_CODE% %TARGET_DATE%

if errorlevel 1 (
    echo.
    echo ERROR: Phase 0-1 failed
    pause
    exit /b 1
)

echo.
echo Phase 0-1 completed successfully
echo.

REM Step 2: Phase 8 (Optimized model prediction)
echo [Step 2/3] Phase 8: Optimized model prediction
echo ------------------------------------------------------------
python scripts\phase8_prediction\predict_phase8.py --venue-code %VENUE_CODE% --date %TARGET_DATE%

if errorlevel 1 (
    echo.
    echo ERROR: Phase 8 prediction failed
    pause
    exit /b 1
)

echo.
echo Phase 8 prediction completed successfully
echo.

REM Step 3: Phase 6 (Distribution text generation)
echo [Step 3/3] Phase 6: Distribution text generation
echo ------------------------------------------------------------
call scripts\phase6_betting\BATCH_OPERATION.bat %TARGET_DATE%

if errorlevel 1 (
    echo.
    echo ERROR: Phase 6 text generation failed
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Phase 8 -^> Phase 6 Completed Successfully!
echo ============================================================
echo.
echo Generated files:
echo   Note:    predictions\*%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%*_note.txt
echo   Bookers: predictions\*%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%*_bookers.txt
echo   Tweet:   predictions\*%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%*_tweet.txt
echo.
echo Phase 8 model performance: AUC 0.76+, Accuracy ~76%%
echo ============================================================
echo.

explorer predictions

pause
