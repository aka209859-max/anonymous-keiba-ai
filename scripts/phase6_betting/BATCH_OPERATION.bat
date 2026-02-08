@echo off
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

if "%~1"=="" goto :SHOW_USAGE

set TARGET_DATE=%~1

echo ==================================================
echo Local Keiba AI Prediction - Batch Processing
echo ==================================================
echo.
echo Target Date: %TARGET_DATE%
echo.
echo ==================================================

set DATE_SHORT=%TARGET_DATE:-=%

echo.
echo Detecting completed Phase 5 venues...
echo.

set KEIBA_CODES=
set ALL_CODES=30 35 36 42 43 44 45 46 47 48 50 51 54 55

for %%K in (%ALL_CODES%) do (
    if "%%K"=="30" set KNAME=Monbetsu
    if "%%K"=="35" set KNAME=Morioka
    if "%%K"=="36" set KNAME=Mizusawa
    if "%%K"=="42" set KNAME=Urawa
    if "%%K"=="43" set KNAME=Funabashi
    if "%%K"=="44" set KNAME=Ooi
    if "%%K"=="45" set KNAME=Kawasaki
    if "%%K"=="46" set KNAME=Kanazawa
    if "%%K"=="47" set KNAME=Kasamatsu
    if "%%K"=="48" set KNAME=Nagoya
    if "%%K"=="50" set KNAME=Sonoda
    if "%%K"=="51" set KNAME=Himeji
    if "%%K"=="54" set KNAME=Kochi
    if "%%K"=="55" set KNAME=Saga
    
    set CHECK_FILE=data\predictions\phase5\!KNAME!_%DATE_SHORT%_ensemble.csv
    
    if exist "!CHECK_FILE!" (
        echo [DETECTED] !KNAME! (Code: %%K)
        set KEIBA_CODES=!KEIBA_CODES! %%K
    )
)

if "%KEIBA_CODES%"=="" (
    echo.
    echo [ERROR] No Phase 5 completed venues found
    echo.
    echo Check:
    echo   - Run Phase 0-5 first
    echo   - Check data\predictions\phase5\ folder
    echo   - Verify date format: %TARGET_DATE%
    echo.
    exit /b 1
)

echo.
echo Detected venue codes:%KEIBA_CODES%
echo.

set SUCCESS_COUNT=0
set FAIL_COUNT=0

for %%K in (%KEIBA_CODES%) do (
    echo.
    echo --------------------------------------------------
    echo Processing venue code %%K...
    echo --------------------------------------------------
    
    call scripts\phase6_betting\DAILY_OPERATION.bat %%K %TARGET_DATE%
    
    if errorlevel 1 (
        echo [FAILED] Venue %%K processing failed
        set /a FAIL_COUNT+=1
    ) else (
        echo [SUCCESS] Venue %%K processing complete
        set /a SUCCESS_COUNT+=1
    )
)

echo.
echo ==================================================
echo Processing Results Summary
echo ==================================================
echo.
echo Success: %SUCCESS_COUNT% venues
echo Failed: %FAIL_COUNT% venues
echo.
echo ==================================================

if %FAIL_COUNT% gtr 0 (
    echo.
    echo WARNING: Some venues failed processing
    echo Check the log above
    echo.
)

if %SUCCESS_COUNT% gtr 0 (
    echo.
    echo Generated Files (per venue):
    echo.
    echo [Note Format]
    for %%K in (%KEIBA_CODES%) do (
        if "%%K"=="30" set KNAME=Monbetsu
        if "%%K"=="35" set KNAME=Morioka
        if "%%K"=="36" set KNAME=Mizusawa
        if "%%K"=="42" set KNAME=Urawa
        if "%%K"=="43" set KNAME=Funabashi
        if "%%K"=="44" set KNAME=Ooi
        if "%%K"=="45" set KNAME=Kawasaki
        if "%%K"=="46" set KNAME=Kanazawa
        if "%%K"=="47" set KNAME=Kasamatsu
        if "%%K"=="48" set KNAME=Nagoya
        if "%%K"=="50" set KNAME=Sonoda
        if "%%K"=="51" set KNAME=Himeji
        if "%%K"=="54" set KNAME=Kochi
        if "%%K"=="55" set KNAME=Saga
        
        set CHECK_FILE=predictions\!KNAME!_%DATE_SHORT%_note.txt
        if exist "!CHECK_FILE!" (
            echo   - !KNAME!_%DATE_SHORT%_note.txt
        )
    )
    echo.
    echo [Bookers Format]
    for %%K in (%KEIBA_CODES%) do (
        if "%%K"=="30" set KNAME=Monbetsu
        if "%%K"=="35" set KNAME=Morioka
        if "%%K"=="36" set KNAME=Mizusawa
        if "%%K"=="42" set KNAME=Urawa
        if "%%K"=="43" set KNAME=Funabashi
        if "%%K"=="44" set KNAME=Ooi
        if "%%K"=="45" set KNAME=Kawasaki
        if "%%K"=="46" set KNAME=Kanazawa
        if "%%K"=="47" set KNAME=Kasamatsu
        if "%%K"=="48" set KNAME=Nagoya
        if "%%K"=="50" set KNAME=Sonoda
        if "%%K"=="51" set KNAME=Himeji
        if "%%K"=="54" set KNAME=Kochi
        if "%%K"=="55" set KNAME=Saga
        
        set CHECK_FILE=predictions\!KNAME!_%DATE_SHORT%_bookers.txt
        if exist "!CHECK_FILE!" (
            echo   - !KNAME!_%DATE_SHORT%_bookers.txt
        )
    )
    echo.
    echo Next Steps:
    echo   1. Open predictions folder
    echo   2. Review each venue's files
    echo   3. Post to Note and Bookers
    echo.
    echo Command:
    echo   explorer predictions
    echo.
)

echo ==================================================
goto :EOF

:SHOW_USAGE
echo ==================================================
echo Local Keiba AI Prediction - Batch Processing
echo ==================================================
echo.
echo Usage:
echo   BATCH_OPERATION.bat [target_date]
echo.
echo Date Format: YYYY-MM-DD
echo.
echo Features:
echo   - Auto-detect Phase 5 completed venues
echo   - Generate Note and Bookers format texts
echo   - Check data\predictions\phase5\{venue}_{YYYYMMDD}_ensemble.csv
echo.
echo Examples:
echo.
echo   BATCH_OPERATION.bat 2026-02-08
echo   BATCH_OPERATION.bat 2026-02-10
echo.
echo Prerequisites:
echo   - Phase 0-5 must be completed
echo   - ensemble.csv must exist
echo.
echo ==================================================
exit /b 1
