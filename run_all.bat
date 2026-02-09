@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if "%~1"=="" (
    echo Usage: run_all.bat [KEIBAJO_CODE] [DATE]
    echo Example: run_all.bat 55 2026-02-07
    exit /b 1
)

if "%~2"=="" (
    echo Usage: run_all.bat [KEIBAJO_CODE] [DATE]
    echo Example: run_all.bat 55 2026-02-07
    exit /b 1
)

REM 引数から余分なスペース・タブを削除
set "KEIBAJO_CODE=%~1"
set "KEIBAJO_CODE=%KEIBAJO_CODE: =%"
set "KEIBAJO_CODE=%KEIBAJO_CODE:	=%"
set "TARGET_DATE=%~2"
set "TARGET_DATE=%TARGET_DATE: =%"
set "TARGET_DATE=%TARGET_DATE:	=%"

for /f "tokens=1,2,3 delims=-" %%a in ("!TARGET_DATE!") do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)
set "DATE_SHORT=!YEAR!!MONTH!!DAY!"

REM デバッグ出力
echo [DEBUG] KEIBAJO_CODE = [!KEIBAJO_CODE!]
echo [DEBUG] TARGET_DATE = [!TARGET_DATE!]
echo [DEBUG] DATE_SHORT = [!DATE_SHORT!]
echo.

if "!KEIBAJO_CODE!"=="30" set KEIBAJO_NAME=門別
if "!KEIBAJO_CODE!"=="35" set KEIBAJO_NAME=盛岡
if "!KEIBAJO_CODE!"=="36" set KEIBAJO_NAME=水沢
if "!KEIBAJO_CODE!"=="42" set KEIBAJO_NAME=浦和
if "!KEIBAJO_CODE!"=="43" set KEIBAJO_NAME=船橋
if "!KEIBAJO_CODE!"=="44" set KEIBAJO_NAME=大井
if "!KEIBAJO_CODE!"=="45" set KEIBAJO_NAME=川崎
if "!KEIBAJO_CODE!"=="46" set KEIBAJO_NAME=金沢
if "!KEIBAJO_CODE!"=="47" set KEIBAJO_NAME=笠松
if "!KEIBAJO_CODE!"=="48" set KEIBAJO_NAME=名古屋
if "!KEIBAJO_CODE!"=="50" set KEIBAJO_NAME=園田
if "!KEIBAJO_CODE!"=="51" set KEIBAJO_NAME=姫路
if "!KEIBAJO_CODE!"=="54" set KEIBAJO_NAME=高知
if "!KEIBAJO_CODE!"=="55" set KEIBAJO_NAME=佐賀

if "!KEIBAJO_NAME!"=="" (
    echo [ERROR] Invalid venue code: !KEIBAJO_CODE!
    exit /b 1
)

echo [DEBUG] KEIBAJO_NAME = [!KEIBAJO_NAME!]
echo.

set LOG_DIR=logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\execution_%DATE_SHORT%_%TIME:~0,2%%TIME:~3,2%.log

echo ============================================================
echo 地方競馬AI予想システム 一括実行（全14競馬場対応）
echo ============================================================
echo 実行開始: %DATE% %TIME%
echo 競馬場: %KEIBAJO_NAME% (コード: %KEIBAJO_CODE%)
echo 対象日付: %TARGET_DATE%
echo ============================================================
echo.

echo [Phase 0] データ取得中...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %TARGET_DATE%
if errorlevel 1 (
    echo [ERROR] Phase 0 失敗
    exit /b 1
)
echo [OK] Phase 0 完了
echo.

set INPUT_CSV=data\raw\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_raw.csv
set OUTPUT_CSV=data\features\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv

echo [Phase 1] 特徴量作成中...
python scripts\phase1_feature_engineering\prepare_features.py "%INPUT_CSV%" --output "%OUTPUT_CSV%"
if errorlevel 1 (
    echo [ERROR] Phase 1 失敗
    exit /b 1
)
echo [OK] Phase 1 完了
echo.

set FEATURES_CSV=data\features\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv
set OUTPUT_P3=data\predictions\phase3\%KEIBAJO_NAME%_%DATE_SHORT%_phase3_binary.csv

echo [Phase 3] 二値分類予測中...
echo   競馬場自動検出: %KEIBAJO_NAME%
python scripts\phase3_binary\predict_phase3_inference.py "%FEATURES_CSV%" models\binary "%OUTPUT_P3%"
if errorlevel 1 (
    echo [ERROR] Phase 3 失敗
    exit /b 1
)
echo [OK] Phase 3 完了
echo.

set OUTPUT_P4_RANK=data\predictions\phase4_ranking\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_ranking.csv

echo [Phase 4-1] ランキング予測中...
echo   競馬場自動検出: %KEIBAJO_NAME%
python scripts\phase4_ranking\predict_phase4_ranking_inference.py "%FEATURES_CSV%" models\ranking "%OUTPUT_P4_RANK%"
if errorlevel 1 (
    echo [ERROR] Phase 4-1 失敗
    exit /b 1
)
echo [OK] Phase 4-1 完了
echo.

set OUTPUT_P4_REG=data\predictions\phase4_regression\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_regression.csv

echo [Phase 4-2] 回帰予測中...
echo   競馬場自動検出: %KEIBAJO_NAME%
python scripts\phase4_regression\predict_phase4_regression_inference.py "%FEATURES_CSV%" models\regression "%OUTPUT_P4_REG%"
if errorlevel 1 (
    echo [ERROR] Phase 4-2 失敗
    exit /b 1
)
echo [OK] Phase 4-2 完了
echo.

set "OUTPUT_ENSEMBLE=data\predictions\phase5\!KEIBAJO_NAME!_!DATE_SHORT!_ensemble.csv"

echo [Phase 5] アンサンブル統合中...
python scripts\phase5_ensemble\ensemble_predictions.py "!OUTPUT_P3!" "!OUTPUT_P4_RANK!" "!OUTPUT_P4_REG!" "!OUTPUT_ENSEMBLE!"
if errorlevel 1 (
    echo [ERROR] Phase 5 失敗
    exit /b 1
)
echo [OK] Phase 5 完了
echo.

REM Phase 5 出力ファイルの存在確認
if not exist "!OUTPUT_ENSEMBLE!" (
    echo [ERROR] Phase 5 output not found: !OUTPUT_ENSEMBLE!
    exit /b 1
)
echo [DEBUG] Phase 5 output confirmed: !OUTPUT_ENSEMBLE!
echo.

REM Phase 6: 配信用ファイル生成（DAILY_OPERATION.bat を呼び出し）
echo [Phase 6] 配信用ファイル生成中（Note/Bookers/Tweet）...
call scripts\phase6_betting\DAILY_OPERATION.bat !KEIBAJO_CODE! !TARGET_DATE!
if errorlevel 1 (
    echo [ERROR] Phase 6 失敗
    exit /b 1
)
echo [OK] Phase 6 完了
echo.

echo ============================================================
echo 全フェーズ完了
echo ============================================================
echo.
echo 予想結果: !OUTPUT_ENSEMBLE!
echo.
echo 配信用ファイル:
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_note.txt
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_bookers.txt
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_tweet.txt
echo.
echo ============================================================

endlocal
