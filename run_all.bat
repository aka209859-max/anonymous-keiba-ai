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
set "TARGET_DATE=%~2"
set "TARGET_DATE=%TARGET_DATE: =%"

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

REM 競馬場コード→名前の変換
set "KEIBAJO_NAME="
if "!KEIBAJO_CODE!"=="30" set "KEIBAJO_NAME=門別"
if "!KEIBAJO_CODE!"=="35" set "KEIBAJO_NAME=盛岡"
if "!KEIBAJO_CODE!"=="36" set "KEIBAJO_NAME=水沢"
if "!KEIBAJO_CODE!"=="42" set "KEIBAJO_NAME=浦和"
if "!KEIBAJO_CODE!"=="43" set "KEIBAJO_NAME=船橋"
if "!KEIBAJO_CODE!"=="44" set "KEIBAJO_NAME=大井"
if "!KEIBAJO_CODE!"=="45" set "KEIBAJO_NAME=川崎"
if "!KEIBAJO_CODE!"=="46" set "KEIBAJO_NAME=金沢"
if "!KEIBAJO_CODE!"=="47" set "KEIBAJO_NAME=笠松"
if "!KEIBAJO_CODE!"=="48" set "KEIBAJO_NAME=名古屋"
if "!KEIBAJO_CODE!"=="50" set "KEIBAJO_NAME=園田"
if "!KEIBAJO_CODE!"=="51" set "KEIBAJO_NAME=姫路"
if "!KEIBAJO_CODE!"=="54" set "KEIBAJO_NAME=高知"
if "!KEIBAJO_CODE!"=="55" set "KEIBAJO_NAME=佐賀"

if "!KEIBAJO_NAME!"=="" (
    echo [ERROR] Invalid venue code: !KEIBAJO_CODE!
    exit /b 1
)

echo [DEBUG] KEIBAJO_NAME = [!KEIBAJO_NAME!]
echo.

set LOG_DIR=logs
if not exist "!LOG_DIR!" mkdir "!LOG_DIR!"
set LOG_FILE=!LOG_DIR!\execution_!DATE_SHORT!_%TIME:~0,2%%TIME:~3,2%.log

echo ============================================================
echo 地方競馬AI予想システム Phase 8統合版
echo ============================================================
echo 実行開始: %DATE% %TIME%
echo 競馬場: !KEIBAJO_NAME! (コード: !KEIBAJO_CODE!)
echo 対象日付: !TARGET_DATE!
echo Phase 8モデル: Optuna最適化 + Boruta選択特徴量（29個）
echo 平均AUC: 0.7637 / 的中率: 約76%%
echo ============================================================
echo.

REM ============================================================
REM Step 1/3: Phase 0-1 データ取得 + 特徴量生成
REM ============================================================
echo [Step 1/3] Phase 0-1: Data Acquisition + Feature Engineering
echo ------------------------------------------------------------
echo.

echo [Phase 0] データ取得中...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo !KEIBAJO_CODE! --date !TARGET_DATE!
if errorlevel 1 (
    echo [ERROR] Phase 0 失敗
    exit /b 1
)
echo [OK] Phase 0 完了
echo.

set "INPUT_CSV=data\raw\!YEAR!\!MONTH!\!KEIBAJO_NAME!_!DATE_SHORT!_raw.csv"
set "OUTPUT_CSV=data\features\!YEAR!\!MONTH!\!KEIBAJO_NAME!_!DATE_SHORT!_features.csv"

echo [Phase 1] 特徴量作成中...
python scripts\phase1_feature_engineering\prepare_features.py "!INPUT_CSV!" --output "!OUTPUT_CSV!"
if errorlevel 1 (
    echo [ERROR] Phase 1 失敗
    exit /b 1
)
echo [OK] Phase 1 完了
echo.

echo Step 1/3 完了: データ取得 + 特徴量生成（50カラム）
echo.

REM ============================================================
REM Step 2/3: Phase 8 最適化モデルで予測
REM ============================================================
echo [Step 2/3] Phase 8: Optimized Model Prediction
echo ------------------------------------------------------------
echo.

echo [Phase 8] Phase 8最適化モデルで予測中...
echo   モデル: Optuna最適化（200試行）
echo   特徴量: Boruta選択（29個）
echo   競馬場: !KEIBAJO_NAME!
python scripts\phase8_prediction\predict_phase8.py --venue-code !KEIBAJO_CODE! --date !TARGET_DATE!
if errorlevel 1 (
    echo [ERROR] Phase 8 失敗
    exit /b 1
)
echo [OK] Phase 8 完了
echo.

echo Step 2/3 完了: Phase 8予測（Phase 5互換形式で保存）
echo.

REM ============================================================
REM Step 3/3: Phase 6 配信テキスト生成
REM ============================================================
echo [Step 3/3] Phase 6: Distribution Text Generation
echo ------------------------------------------------------------
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

echo Step 3/3 完了: 配信テキスト生成
echo.

echo ============================================================
echo Phase 8統合版 全フェーズ完了
echo ============================================================
echo.
echo Phase 8予測結果:
echo   - data\predictions\phase8\!KEIBAJO_NAME:門別=monbetsu!_!DATE_SHORT!_phase8_predictions.csv
echo   - data\predictions\phase5\!KEIBAJO_NAME!_!DATE_SHORT!_ensemble.csv
echo.
echo 配信用ファイル:
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_note.txt
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_bookers.txt
echo   - predictions\!KEIBAJO_NAME!_!DATE_SHORT!_tweet.txt
echo.
echo Phase 8モデル性能: AUC 0.76+ / 的中率 約76%%
echo Phase 5比較: +6%% 精度向上
echo ============================================================
echo.
echo 配信用ファイルを確認してください:
echo   notepad predictions\!KEIBAJO_NAME!_!DATE_SHORT!_note.txt
echo.

endlocal
