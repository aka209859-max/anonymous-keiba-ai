@echo off
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if "%~1"=="" (
    echo [ERROR] Usage: run_all_optimized.bat [KEIBAJO_CODE] [DATE]
    echo Example: run_all_optimized.bat 43 2026-02-13
    exit /b 1
)

if "%~2"=="" (
    echo [ERROR] Usage: run_all_optimized.bat [KEIBAJO_CODE] [DATE]
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
if "%KEIBAJO_CODE%"=="30" set "KEIBAJO_NAME=門別"
if "%KEIBAJO_CODE%"=="35" set "KEIBAJO_NAME=盛岡"
if "%KEIBAJO_CODE%"=="36" set "KEIBAJO_NAME=水沢"
if "%KEIBAJO_CODE%"=="42" set "KEIBAJO_NAME=浦和"
if "%KEIBAJO_CODE%"=="43" set "KEIBAJO_NAME=船橋"
if "%KEIBAJO_CODE%"=="44" set "KEIBAJO_NAME=大井"
if "%KEIBAJO_CODE%"=="45" set "KEIBAJO_NAME=川崎"
if "%KEIBAJO_CODE%"=="46" set "KEIBAJO_NAME=金沢"
if "%KEIBAJO_CODE%"=="47" set "KEIBAJO_NAME=笠松"
if "%KEIBAJO_CODE%"=="48" set "KEIBAJO_NAME=名古屋"
if "%KEIBAJO_CODE%"=="50" set "KEIBAJO_NAME=園田"
if "%KEIBAJO_CODE%"=="51" set "KEIBAJO_NAME=姫路"
if "%KEIBAJO_CODE%"=="54" set "KEIBAJO_NAME=高知"
if "%KEIBAJO_CODE%"=="55" set "KEIBAJO_NAME=佐賀"

if "%KEIBAJO_NAME%"=="" (
    echo [ERROR] Invalid venue code: %KEIBAJO_CODE%
    exit /b 1
)

set LOG_DIR=logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================================
echo 地方競馬AI予想システム Phase 7-8-5
echo ============================================================
echo 実行開始: %DATE% %TIME%
echo 競馬場: %KEIBAJO_NAME% (コード: %KEIBAJO_CODE%)
echo 対象日付: %TARGET_DATE%
echo ============================================================
echo.

echo [Phase 0] データ取得中...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %DATE_SHORT%
if errorlevel 1 (
    echo [ERROR] Phase 0 failed
    exit /b 1
)
echo [OK] Phase 0 Complete
echo.

set "INPUT_CSV=data\raw\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_raw.csv"
set "OUTPUT_CSV=data\features\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv"

echo [Phase 1] 特徴量生成中...
python scripts\phase1_feature_engineering\prepare_features.py "%INPUT_CSV%" --output "%OUTPUT_CSV%"
if errorlevel 1 (
    echo [ERROR] Phase 1 failed
    exit /b 1
)
echo [OK] Phase 1 Complete
echo.

set "FEATURES_CSV=%OUTPUT_CSV%"
set "OUTPUT_P7_BINARY=data\predictions\phase7_binary\%KEIBAJO_NAME%_%DATE_SHORT%_phase7_binary.csv"

echo [Phase 7 Binary] 予測実行中...
python scripts\phase7_binary\predict_optimized_binary.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P7_BINARY%"
if errorlevel 1 (
    echo [ERROR] Phase 7 Binary failed
    exit /b 1
)
echo [OK] Phase 7 Binary Complete
echo.

set "OUTPUT_P8_RANKING=data\predictions\phase8_ranking\%KEIBAJO_NAME%_%DATE_SHORT%_phase8_ranking.csv"

echo [Phase 8 Ranking] 予測実行中...
python scripts\phase8_ranking\predict_optimized_ranking.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P8_RANKING%"
if errorlevel 1 (
    echo [ERROR] Phase 8 Ranking failed
    exit /b 1
)
echo [OK] Phase 8 Ranking Complete
echo.

set "OUTPUT_P8_REGRESSION=data\predictions\phase8_regression\%KEIBAJO_NAME%_%DATE_SHORT%_phase8_regression.csv"

echo [Phase 8 Regression] 予測実行中...
python scripts\phase8_regression\predict_optimized_regression.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P8_REGRESSION%"
if errorlevel 1 (
    echo [ERROR] Phase 8 Regression failed
    exit /b 1
)
echo [OK] Phase 8 Regression Complete
echo.

set "OUTPUT_ENSEMBLE=data\predictions\phase5\%KEIBAJO_NAME%_%DATE_SHORT%_ensemble_optimized.csv"

echo [Phase 5 Ensemble] 統合実行中...
python scripts\phase5_ensemble\ensemble_optimized.py "%OUTPUT_P7_BINARY%" "%OUTPUT_P8_RANKING%" "%OUTPUT_P8_REGRESSION%" "%OUTPUT_ENSEMBLE%"
if errorlevel 1 (
    echo [ERROR] Phase 5 Ensemble failed
    exit /b 1
)
echo [OK] Phase 5 Ensemble Complete
echo.

if not exist "%OUTPUT_ENSEMBLE%" (
    echo [ERROR] Ensemble file not found
    exit /b 1
)

echo [Phase 6] 配信用テキスト生成中...
call scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE% "%OUTPUT_ENSEMBLE%"
if errorlevel 1 (
    echo [WARNING] Phase 6 ERROR
) else (
    echo [OK] Phase 6 Complete
)
echo.

echo ============================================================
echo 全フェーズ完了
echo ============================================================
echo 実行終了: %DATE% %TIME%
echo.

set "NOTE_TXT=predictions\%KEIBAJO_NAME%_%DATE_SHORT%_note.txt"
set "BOOKERS_TXT=predictions\%KEIBAJO_NAME%_%DATE_SHORT%_bookers.txt"
set "TWEET_TXT=predictions\%KEIBAJO_NAME%_%DATE_SHORT%_tweet.txt"

echo [配信用テキストファイル]
if exist "%NOTE_TXT%" (
    echo   [OK] Note用: %NOTE_TXT%
) else (
    echo   [NG] Note用: %NOTE_TXT%
)

if exist "%BOOKERS_TXT%" (
    echo   [OK] ブッカーズ用: %BOOKERS_TXT%
) else (
    echo   [NG] ブッカーズ用: %BOOKERS_TXT%
)

if exist "%TWEET_TXT%" (
    echo   [OK] Twitter用: %TWEET_TXT%
) else (
    echo   [NG] Twitter用: %TWEET_TXT%
)
echo.
echo ============================================================

endlocal
