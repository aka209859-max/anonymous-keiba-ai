@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM Phase 8 -> Phase 6 Multiple Venues Batch Execution

if "%~1"=="" (
    echo Usage: RUN_PHASE8_TO_PHASE6_MULTI.bat [TARGET_DATE] [VENUE_CODE1] [VENUE_CODE2] ...
    echo Example: RUN_PHASE8_TO_PHASE6_MULTI.bat 2026-02-11 43 44 45
    echo.
    echo Venue Codes:
    echo   30: Monbetsu    35: Morioka     36: Mizusawa   42: Urawa
    echo   43: Funabashi   44: Ooi         45: Kawasaki   46: Kanazawa
    echo   47: Kasamatsu   48: Nagoya      50: Sonoda     51: Himeji
    echo   54: Kochi       55: Saga
    pause
    exit /b 1
)

set TARGET_DATE=%~1
shift

REM Count venues
set VENUE_COUNT=0
:count_venues
if "%~1"=="" goto start_processing
set /a VENUE_COUNT+=1
set VENUE_%VENUE_COUNT%=%~1
shift
goto count_venues

:start_processing

echo ============================================================
echo Phase 8 -^> Phase 6 Multiple Venues Batch Execution
echo ============================================================
echo Date: %TARGET_DATE%
echo Total Venues: %VENUE_COUNT%
echo ============================================================
echo.

set SUCCESS_COUNT=0
set FAIL_COUNT=0

REM Process each venue
for /L %%i in (1,1,%VENUE_COUNT%) do (
    set CURRENT_VENUE=!VENUE_%%i!
    echo.
    echo [Venue %%i/%VENUE_COUNT%] Processing venue code: !CURRENT_VENUE!
    echo ------------------------------------------------------------
    
    call RUN_PHASE8_TO_PHASE6.bat !CURRENT_VENUE! %TARGET_DATE%
    
    if errorlevel 1 (
        echo ERROR: Venue !CURRENT_VENUE! failed
        set /a FAIL_COUNT+=1
    ) else (
        echo SUCCESS: Venue !CURRENT_VENUE! completed
        set /a SUCCESS_COUNT+=1
    )
)

echo.
echo ============================================================
echo Phase 8 -^> Phase 6 Batch Execution Summary
echo ============================================================
echo Date: %TARGET_DATE%
echo Total Venues: %VENUE_COUNT%
echo Success: %SUCCESS_COUNT%
echo Failed: %FAIL_COUNT%
echo ============================================================
echo.

if %FAIL_COUNT% GTR 0 (
    echo WARNING: Some venues failed. Please check the logs.
) else (
    echo All venues completed successfully!
)

echo.
echo Opening predictions folder...
explorer predictions

pause
