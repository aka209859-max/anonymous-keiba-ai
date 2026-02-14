@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai\data\models\tuned

echo ============================================================
echo Model File Renaming Script
echo ============================================================
echo.

REM 競馬場名とコードの対応
set "VENUES=monbetsu:30 morioka:35 mizusawa:36 urawa:42 funabashi:43 ooi:44 kawasaki:45 kanazawa:46 kasamatsu:47 nagoya:48 sonoda:50 himeji:51 kochi:54 saga:55"

for %%v in (%VENUES%) do (
    for /f "tokens=1,2 delims=:" %%a in ("%%v") do (
        set "VENUE_NAME=%%a"
        set "VENUE_CODE=%%b"
        
        echo Processing: !VENUE_NAME! Code: !VENUE_CODE!
        
        if exist "!VENUE_NAME!_tuned_model" (
            ren "!VENUE_NAME!_tuned_model" "lgb_binary_!VENUE_CODE!_optimized.txt"
            echo   [OK] Binary renamed
        ) else (
            echo   [SKIP] Binary not found
        )
        
        if exist "!VENUE_NAME!_ranking_tuned_model" (
            ren "!VENUE_NAME!_ranking_tuned_model" "lgb_ranking_!VENUE_CODE!_optimized.txt"
            echo   [OK] Ranking renamed
        ) else (
            echo   [SKIP] Ranking not found
        )
        
        if exist "!VENUE_NAME!_regression_tuned_model" (
            ren "!VENUE_NAME!_regression_tuned_model" "lgb_regression_!VENUE_CODE!_optimized.txt"
            echo   [OK] Regression renamed
        ) else (
            echo   [SKIP] Regression not found
        )
        
        echo.
    )
)

echo ============================================================
echo Renaming Complete
echo ============================================================
echo.
echo Renamed files:
dir lgb_*.txt /b

pause
endlocal
