@echo off
REM ============================================================
REM 地方競馬AI予想システム Phase 3-4-5版（旧モデル）
REM 使用方法: run_all.bat [KEIBAJO_CODE] [DATE]
REM 例: run_all.bat 43 2026-02-13
REM ============================================================

setlocal enabledelayedexpansion

REM UTF-8環境変数設定
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM 引数チェック
if "%~1"=="" (
    echo [ERROR] Usage: run_all.bat [KEIBAJO_CODE] [DATE]
    echo [ERROR] Example: run_all.bat 43 2026-02-13
    echo.
    echo Venue Codes:
    echo   30=門別  35=盛岡  36=水沢  42=浦和  43=船橋  44=大井  45=川崎
    echo   46=金沢  47=笠松  48=名古屋 50=園田  51=姫路  54=高知  55=佐賀
    exit /b 1
)

if "%~2"=="" (
    echo [ERROR] Usage: run_all.bat [KEIBAJO_CODE] [DATE]
    echo [ERROR] Example: run_all.bat 43 2026-02-13
    exit /b 1
)

REM 引数を変数に設定
set "KEIBAJO_CODE=%~1"
set "TARGET_DATE=%~2"

REM 日付をYYYY-MM-DD形式からYYYYMMDDに変換
for /f "tokens=1,2,3 delims=-" %%a in ("%TARGET_DATE%") do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)
set "DATE_SHORT=%YEAR%%MONTH%%DAY%"

REM 競馬場コードから名前へ変換
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

REM ログディレクトリ作成
set LOG_DIR=logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================================
echo 地方競馬AI予想システム Phase 3-4-5版 (旧モデル)
echo ============================================================
echo 実行開始: %DATE% %TIME%
echo 競馬場: %KEIBAJO_NAME% (コード: %KEIBAJO_CODE%)
echo 対象日付: %TARGET_DATE%
echo ============================================================
echo.

REM ============================================================
REM Phase 0: データ取得
REM ============================================================
echo [Phase 0] データ取得中...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %TARGET_DATE%
if errorlevel 1 (
    echo [ERROR] Phase 0 failed
    exit /b 1
)
echo [OK] Phase 0 Complete
echo.

REM ============================================================
REM Phase 1: 特徴量生成
REM ============================================================
set "INPUT_CSV=data\raw\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_raw.csv"
set "OUTPUT_CSV=data\features\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv"

echo [Phase 1] 特徴量生成中...
echo   Input: %INPUT_CSV%
echo   Output: %OUTPUT_CSV%
python scripts\phase1_feature_engineering\prepare_features.py "%INPUT_CSV%" --output "%OUTPUT_CSV%"
if errorlevel 1 (
    echo [ERROR] Phase 1 failed
    exit /b 1
)
echo [OK] Phase 1 Complete
echo.

set "FEATURES_CSV=%OUTPUT_CSV%"

REM ============================================================
REM Phase 3: Binary予測 (旧モデル)
REM ============================================================
set "OUTPUT_P3_BINARY=data\predictions\phase3\%KEIBAJO_NAME%_%DATE_SHORT%_phase3_binary.csv"

echo [Phase 3 Binary] 予測実行中...
echo   Input: %FEATURES_CSV%
echo   Output: %OUTPUT_P3_BINARY%
python scripts\phase3_binary\predict.py "%FEATURES_CSV%" "data\models" "%OUTPUT_P3_BINARY%"
if errorlevel 1 (
    echo [ERROR] Phase 3 Binary failed
    exit /b 1
)
echo [OK] Phase 3 Binary Complete
echo.

REM ============================================================
REM Phase 4: Ranking予測 (旧モデル)
REM ============================================================
set "OUTPUT_P4_RANKING=data\predictions\phase4\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_ranking.csv"

echo [Phase 4 Ranking] 予測実行中...
echo   Input: %FEATURES_CSV%
echo   Output: %OUTPUT_P4_RANKING%
python scripts\phase4_ranking\predict.py "%FEATURES_CSV%" "data\models" "%OUTPUT_P4_RANKING%"
if errorlevel 1 (
    echo [ERROR] Phase 4 Ranking failed
    exit /b 1
)
echo [OK] Phase 4 Ranking Complete
echo.

REM ============================================================
REM Phase 5: アンサンブル統合 (旧モデル)
REM ============================================================
set "OUTPUT_ENSEMBLE=data\predictions\phase5\%KEIBAJO_NAME%_%DATE_SHORT%_ensemble.csv"

echo [Phase 5 Ensemble] 統合実行中...
echo   Binary Input: %OUTPUT_P3_BINARY%
echo   Ranking Input: %OUTPUT_P4_RANKING%
echo   Output: %OUTPUT_ENSEMBLE%
python scripts\phase5_ensemble\ensemble.py "%OUTPUT_P3_BINARY%" "%OUTPUT_P4_RANKING%" "%OUTPUT_ENSEMBLE%"
if errorlevel 1 (
    echo [ERROR] Phase 5 Ensemble failed
    exit /b 1
)
echo [OK] Phase 5 Ensemble Complete
echo.

if not exist "%OUTPUT_ENSEMBLE%" (
    echo [ERROR] Ensemble file not found: %OUTPUT_ENSEMBLE%
    exit /b 1
)

REM ============================================================
REM Phase 6: 配信用テキスト生成
REM ============================================================
echo [Phase 6] 配信用テキスト生成中...
call scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE%
if errorlevel 1 (
    echo [WARNING] Phase 6 failed
    echo Prediction results are in: %OUTPUT_ENSEMBLE%
)
echo.

echo ============================================================
echo 全フェーズ完了 (Phase 3-4-5)
echo ============================================================
echo 実行終了: %DATE% %TIME%
echo.
echo 出力ファイル:
echo   - Phase 3 Binary: %OUTPUT_P3_BINARY%
echo   - Phase 4 Ranking: %OUTPUT_P4_RANKING%
echo   - Phase 5 Ensemble: %OUTPUT_ENSEMBLE%
echo   - 配信用テキスト: predictions\%KEIBAJO_NAME%_%DATE_SHORT%_note.txt
echo   - 配信用テキスト: predictions\%KEIBAJO_NAME%_%DATE_SHORT%_bookers.txt
echo   - 配信用テキスト: predictions\%KEIBAJO_NAME%_%DATE_SHORT%_tweet.txt
echo ============================================================

endlocal
