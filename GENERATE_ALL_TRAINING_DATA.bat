@echo off
REM UTF-8 BOM付きで保存すること
setlocal EnableDelayedExpansion

echo ============================================================
echo [Training Data Generation] Remaining 13 Venues
echo ============================================================
echo.
echo Target: 13 venues (Funabashi already completed)
echo Estimated time: 1-2 hours
echo.

REM データディレクトリの作成
if not exist "data\training" mkdir "data\training"

REM Venue list (13 venues)
set VENUES[0]=30:monbetsu:Monbetsu
set VENUES[1]=33:obihiro:Obihiro
set VENUES[2]=35:morioka:Morioka
set VENUES[3]=36:mizusawa:Mizusawa
set VENUES[4]=42:urawa:Urawa
REM 43=funabashi already completed
set VENUES[5]=44:ooi:Ooi
set VENUES[6]=45:kawasaki:Kawasaki
set VENUES[7]=46:kanazawa:Kanazawa
set VENUES[8]=47:kasamatsu:Kasamatsu
set VENUES[9]=48:nagoya:Nagoya
set VENUES[10]=50:sonoda:Sonoda
set VENUES[11]=51:himeji:Himeji
set VENUES[12]=54:kochi:Kochi
set VENUES[13]=55:saga:Saga

REM Create log file
set LOG_FILE=data\training\generation_log_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set LOG_FILE=%LOG_FILE: =0%
echo [%date% %time%] Training data batch generation started > "%LOG_FILE%"

REM Generate data for each venue
set COUNT=0
for /L %%i in (0,1,13) do (
    set VENUE_INFO=!VENUES[%%i]!
    for /F "tokens=1,2,3 delims=:" %%a in ("!VENUE_INFO!") do (
        set /A COUNT+=1
        echo.
        echo ============================================================
        echo [!COUNT!/13] %%c (Code: %%a) Generating data...
        echo ============================================================
        echo [%date% %time%] %%c (%%a) Started >> "%LOG_FILE%"
        
        python extract_training_data_v2.py ^
          --keibajo %%a ^
          --start-date 2020 ^
          --end-date 2026 ^
          --output "data\training\%%b_2020-2026_with_time_PHASE78.csv"
        
        if !ERRORLEVEL! EQU 0 (
            echo [%date% %time%] %%c (%%a) Completed >> "%LOG_FILE%"
            echo [OK] %%c Completed!
        ) else (
            echo [%date% %time%] %%c (%%a) Error >> "%LOG_FILE%"
            echo [ERROR] %%c Error! Check the log file.
        )
    )
)

echo.
echo ============================================================
echo [OK] All 13 venues data generation completed!
echo ============================================================
echo.
echo Output: data\training\
echo Log file: %LOG_FILE%
echo.
echo Next steps:
echo   1. Verify generated CSV files
echo   2. Run Phase 7 Ranking feature selection
echo   3. Run Phase 7 Regression feature selection
echo.
pause
