@echo off
chcp 932 >nul
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM =========================================================================
REM Phase 12: トリプル馬単専用予測パイプライン
REM 対象: 南関東4場（大井・浦和・船橋・川崎）+ 門別
REM =========================================================================

if "%~1"=="" (
    echo 使用法: run_phase12.bat [KEIBAJO_CODE] [DATE]
    echo.
    echo 例: run_phase12.bat 43 2026-04-22  ^(船橋^)
    echo 例: run_phase12.bat 44 2026-04-22  ^(大井^)
    echo 例: run_phase12.bat 42 2026-04-22  ^(浦和^)
    echo 例: run_phase12.bat 45 2026-04-22  ^(川崎^)
    echo 例: run_phase12.bat 30 2026-04-22  ^(門別^)
    exit /b 1
)

if "%~2"=="" (
    echo 使用法: run_phase12.bat [KEIBAJO_CODE] [DATE]
    exit /b 1
)

set "KEIBAJO_CODE=%~1"
set "TARGET_DATE=%~2"

REM 競馬場コードから日本語名に変換
set "KEIBA_NAME="
if "%KEIBAJO_CODE%"=="30" set "KEIBA_NAME=門別"
if "%KEIBAJO_CODE%"=="42" set "KEIBA_NAME=浦和"
if "%KEIBAJO_CODE%"=="43" set "KEIBA_NAME=船橋"
if "%KEIBAJO_CODE%"=="44" set "KEIBA_NAME=大井"
if "%KEIBAJO_CODE%"=="45" set "KEIBA_NAME=川崎"

if "%KEIBA_NAME%"=="" (
    echo エラー: 対応していない競馬場コードです: %KEIBAJO_CODE%
    echo Phase 12対象: 30^(門別^), 42^(浦和^), 43^(船橋^), 44^(大井^), 45^(川崎^)
    exit /b 1
)

REM 日付をパース
for /f "tokens=1,2,3 delims=-" %%a in ("%TARGET_DATE%") do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)
set "DATE_SHORT=%YEAR%%MONTH%%DAY%"

echo =========================================================================
echo Phase 12: トリプル馬単予測パイプライン
echo =========================================================================
echo 競馬場: %KEIBA_NAME% ^(コード: %KEIBAJO_CODE%^)
echo 日付: %TARGET_DATE%
echo =========================================================================
echo.

REM =========================================================================
REM Phase 0: データ取得
REM =========================================================================
echo [Phase 0] データ取得開始...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %TARGET_DATE%
if errorlevel 1 (
    echo エラー: Phase 0 データ取得失敗
    exit /b 1
)
echo.

REM =========================================================================
REM Phase 1: 特徴量生成
REM =========================================================================
echo [Phase 1] 特徴量生成開始...
python scripts\phase1_feature_engineering\prepare_features_safe.py %KEIBAJO_CODE% %YEAR% %MONTH% %DATE_SHORT%
if errorlevel 1 (
    echo エラー: Phase 1 特徴量生成失敗
    exit /b 1
)
echo.

REM 特徴量ファイルのパスを設定
set "FEATURES_FILENAME=%KEIBA_NAME%_%DATE_SHORT%_features.csv"
set "FEATURES_CSV=data\features\%YEAR%\%MONTH%\%FEATURES_FILENAME%"

if not exist "%FEATURES_CSV%" (
    echo エラー: 特徴量ファイルが見つかりません: %FEATURES_CSV%
    exit /b 1
)

echo 特徴量ファイル: %FEATURES_CSV%
echo.

REM =========================================================================
REM Phase 12: Step 5-1 - バイナリ分類予測
REM =========================================================================
echo [Phase 12 Step 5-1] バイナリ分類予測（2着以内）...
set "BINARY_OUTPUT=data\phase12_umatan\predictions\binary\%KEIBA_NAME%_%DATE_SHORT%_binary.csv"
python scripts\phase12_umatan_model\step5_1_predict_binary.py "%FEATURES_CSV%" data\phase12_umatan\models\binary\phase12_binary_top2_model.txt "%BINARY_OUTPUT%"
if errorlevel 1 (
    echo エラー: Phase 12 Step 5-1 バイナリ分類予測失敗
    exit /b 1
)
echo.

REM =========================================================================
REM Phase 12: Step 5-2 - ランキング予測
REM =========================================================================
echo [Phase 12 Step 5-2] ランキング予測...
set "RANKING_OUTPUT=data\phase12_umatan\predictions\ranking\%KEIBA_NAME%_%DATE_SHORT%_ranking.csv"
python scripts\phase12_umatan_model\step5_2_predict_ranking.py "%FEATURES_CSV%" data\phase12_umatan\models\ranking\phase12_ranking_model.txt "%RANKING_OUTPUT%"
if errorlevel 1 (
    echo エラー: Phase 12 Step 5-2 ランキング予測失敗
    exit /b 1
)
echo.

REM =========================================================================
REM Phase 12: Step 5-3 - 回帰予測
REM =========================================================================
echo [Phase 12 Step 5-3] 回帰予測（タイム予測）...
set "REGRESSION_OUTPUT=data\phase12_umatan\predictions\regression\%KEIBA_NAME%_%DATE_SHORT%_regression.csv"
python scripts\phase12_umatan_model\step5_3_predict_regression.py "%FEATURES_CSV%" data\phase12_umatan\models\regression\phase12_regression_model.txt "%REGRESSION_OUTPUT%"
if errorlevel 1 (
    echo エラー: Phase 12 Step 5-3 回帰予測失敗
    exit /b 1
)
echo.

REM =========================================================================
REM Phase 12: Step 6 - アンサンブル予測
REM =========================================================================
echo [Phase 12 Step 6] アンサンブル予測...
set "ENSEMBLE_OUTPUT=data\phase12_umatan\predictions\ensemble\%KEIBA_NAME%_%DATE_SHORT%_ensemble.csv"
python scripts\phase12_umatan_model\step6_ensemble.py "%BINARY_OUTPUT%" "%RANKING_OUTPUT%" "%REGRESSION_OUTPUT%" "%ENSEMBLE_OUTPUT%"
if errorlevel 1 (
    echo エラー: Phase 12 Step 6 アンサンブル予測失敗
    exit /b 1
)
echo.

REM =========================================================================
REM Phase 12: Step 7 - 馬単買い目生成
REM =========================================================================
echo [Phase 12 Step 7] 馬単買い目生成...
set "UMATAN_OUTPUT=data\phase12_umatan\predictions\tickets\%KEIBA_NAME%_%DATE_SHORT%_umatan.txt"
python scripts\phase12_umatan_model\step7_generate_umatan.py "%ENSEMBLE_OUTPUT%" "%UMATAN_OUTPUT%"
if errorlevel 1 (
    echo エラー: Phase 12 Step 7 馬単買い目生成失敗
    exit /b 1
)
echo.

REM =========================================================================
REM 完了
REM =========================================================================
echo =========================================================================
echo Phase 12: トリプル馬単予測パイプライン完了！
echo =========================================================================
echo 馬単買い目ファイル: %UMATAN_OUTPUT%
echo.
echo 買い目を確認するには:
echo   notepad "%UMATAN_OUTPUT%"
echo =========================================================================

endlocal
