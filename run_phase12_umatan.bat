@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if "%~1"=="" (
    echo Usage: run_phase12_umatan.bat [KEIBAJO_CODE] [DATE]
    exit /b 1
)

if "%~2"=="" (
    echo Usage: run_phase12_umatan.bat [KEIBAJO_CODE] [DATE]
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

REM 競馬場名マッピング
set "KEIBA_NAME="
if "%KEIBAJO_CODE%"=="30" set "KEIBA_NAME=門別"
if "%KEIBAJO_CODE%"=="35" set "KEIBA_NAME=盛岡"
if "%KEIBAJO_CODE%"=="36" set "KEIBA_NAME=水沢"
if "%KEIBAJO_CODE%"=="42" set "KEIBA_NAME=浦和"
if "%KEIBAJO_CODE%"=="43" set "KEIBA_NAME=船橋"
if "%KEIBAJO_CODE%"=="44" set "KEIBA_NAME=大井"
if "%KEIBAJO_CODE%"=="45" set "KEIBA_NAME=川崎"
if "%KEIBAJO_CODE%"=="46" set "KEIBA_NAME=金沢"
if "%KEIBAJO_CODE%"=="47" set "KEIBA_NAME=笠松"
if "%KEIBAJO_CODE%"=="48" set "KEIBA_NAME=名古屋"
if "%KEIBAJO_CODE%"=="50" set "KEIBA_NAME=園田"
if "%KEIBAJO_CODE%"=="51" set "KEIBA_NAME=姫路"
if "%KEIBAJO_CODE%"=="54" set "KEIBA_NAME=高知"
if "%KEIBAJO_CODE%"=="55" set "KEIBA_NAME=佐賀"

if not defined KEIBA_NAME (
    echo ERROR: Invalid venue code: %KEIBAJO_CODE%
    exit /b 1
)

echo ================================================================================
echo Phase 12: トリプル馬単AI予測システム
echo ================================================================================
echo.
echo 競馬場: %KEIBA_NAME% (Code: %KEIBAJO_CODE%)
echo 開催日: %TARGET_DATE%
echo.
echo ================================================================================

REM Phase 0: データ取得
echo.
echo [Phase 0] データ取得中...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %TARGET_DATE%
if errorlevel 1 (
    echo ERROR: Phase 0 failed
    exit /b 1
)

REM Phase 1: 特徴量作成
echo.
echo [Phase 1] 特徴量作成中...
python scripts\phase1_feature_engineering\prepare_features_safe.py %KEIBAJO_CODE% %YEAR% %MONTH% %DATE_SHORT%
if errorlevel 1 (
    echo ERROR: Phase 1 failed
    exit /b 1
)

REM 特徴量ファイルパス
set "FEATURES_CSV=data\features\%YEAR%\%MONTH%\%KEIBA_NAME%_%DATE_SHORT%_features.csv"

if not exist "%FEATURES_CSV%" (
    echo ERROR: Feature file not found: %FEATURES_CSV%
    exit /b 1
)

echo Found: %FEATURES_CSV%

REM Phase 12: 馬単AI予測
echo.
echo ================================================================================
echo Phase 12: 馬単AI予測開始
echo ================================================================================

REM Step 5-1: Binary予測（2着以内）
echo.
echo [Step 5-1] Binary予測（2着以内）中...
set "BINARY_OUT=data\phase12_umatan\predictions\binary\%KEIBA_NAME%_%DATE_SHORT%_binary.csv"
python scripts\phase12_umatan_model\step5_1_predict_binary.py "%FEATURES_CSV%" data\phase12_umatan\models\binary "%BINARY_OUT%"
if errorlevel 1 (
    echo ERROR: Step 5-1 failed
    exit /b 1
)

REM Step 5-2: Ranking予測
echo.
echo [Step 5-2] Ranking予測中...
set "RANKING_OUT=data\phase12_umatan\predictions\ranking\%KEIBA_NAME%_%DATE_SHORT%_ranking.csv"
python scripts\phase12_umatan_model\step5_2_predict_ranking.py "%FEATURES_CSV%" data\phase12_umatan\models\ranking "%RANKING_OUT%"
if errorlevel 1 (
    echo ERROR: Step 5-2 failed
    exit /b 1
)

REM Step 5-3: Regression予測（タイム）
echo.
echo [Step 5-3] Regression予測（タイム）中...
set "REGRESSION_OUT=data\phase12_umatan\predictions\regression\%KEIBA_NAME%_%DATE_SHORT%_regression.csv"
python scripts\phase12_umatan_model\step5_3_predict_regression.py "%FEATURES_CSV%" data\phase12_umatan\models\regression "%REGRESSION_OUT%"
if errorlevel 1 (
    echo ERROR: Step 5-3 failed
    exit /b 1
)

REM Step 6: アンサンブル統合
echo.
echo [Step 6] アンサンブル統合中...
set "ENSEMBLE_OUT=data\phase12_umatan\predictions\ensemble\%KEIBA_NAME%_%DATE_SHORT%_ensemble.csv"
python scripts\phase12_umatan_model\step6_ensemble.py "%BINARY_OUT%" "%RANKING_OUT%" "%REGRESSION_OUT%" "%ENSEMBLE_OUT%"
if errorlevel 1 (
    echo ERROR: Step 6 failed
    exit /b 1
)

REM Step 7: 馬単買い目生成
echo.
echo [Step 7] 馬単買い目生成中...
set "UMATAN_OUT=predictions\phase12_umatan\%KEIBA_NAME%_%DATE_SHORT%_umatan.txt"
REM 動的閾値モード: min_binary_proba=0.30 で自動的にレースごとに最適閾値を設定
REM （本命明確→40%, 中本命→35%, 混戦→30%, 大混戦→25%）
python scripts\phase12_umatan_model\step7_generate_umatan.py "%ENSEMBLE_OUT%" "%UMATAN_OUT%" 5 4 0.30
if errorlevel 1 (
    echo ERROR: Step 7 failed
    exit /b 1
)

echo.
echo ================================================================================
echo ✅ Phase 12 完了！
echo ================================================================================
echo.
echo 馬単買い目ファイル:
echo   %UMATAN_OUT%
echo.
echo 買い目を確認:
echo   notepad "%UMATAN_OUT%"
echo.
echo ================================================================================

endlocal
