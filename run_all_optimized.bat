@echo off
REM ============================================================
REM 地方競馬AI予想システム Phase 7-8-5統合版（新モデル）
REM 使用方法: run_all_optimized.bat [KEIBAJO_CODE] [DATE]
REM 例: run_all_optimized.bat 43 2026-02-13
REM ============================================================

setlocal enabledelayedexpansion

REM UTF-8環境変数設定
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM 引数チェック
if "%~1"=="" (
    echo [ERROR] Usage: run_all_optimized.bat [KEIBAJO_CODE] [DATE]
    echo [ERROR] Example: run_all_optimized.bat 43 2026-02-13
    echo.
    echo Venue Codes:
    echo   30=門別  35=盛岡  36=水沢  42=浦和  43=船橋  44=大井  45=川崎
    echo   46=金沢  47=笠松  48=名古屋 50=園田  51=姫路  54=高知  55=佐賀
    exit /b 1
)

if "%~2"=="" (
    echo [ERROR] Usage: run_all_optimized.bat [KEIBAJO_CODE] [DATE]
    echo [ERROR] Example: run_all_optimized.bat 43 2026-02-13
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
echo 地方競馬AI予想システム Phase 7-8-5統合版
echo ============================================================
echo 実行開始: %DATE% %TIME%
echo 競馬場: %KEIBAJO_NAME% (コード: %KEIBAJO_CODE%)
echo 対象日付: %TARGET_DATE%
echo 新モデル: Phase 7 Boruta特徴量選択 + Phase 8 Optuna最適化
echo Binary: 31特徴量 / Ranking: 25特徴量 / Regression: 24特徴量
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
REM Phase 7: Binary予測
REM ============================================================
set "OUTPUT_P7_BINARY=data\predictions\phase7_binary\%KEIBAJO_NAME%_%DATE_SHORT%_phase7_binary.csv"

echo [Phase 7 Binary] 予測実行中...
echo   Input: %FEATURES_CSV%
echo   Output: %OUTPUT_P7_BINARY%
python scripts\phase7_binary\predict_optimized_binary.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P7_BINARY%"
if errorlevel 1 (
    echo [ERROR] Phase 7 Binary failed
    exit /b 1
)
echo [OK] Phase 7 Binary Complete
echo.

REM ============================================================
REM Phase 8: Ranking予測
REM ============================================================
set "OUTPUT_P8_RANKING=data\predictions\phase8_ranking\%KEIBAJO_NAME%_%DATE_SHORT%_phase8_ranking.csv"

echo [Phase 8 Ranking] 予測実行中...
echo   Input: %FEATURES_CSV%
echo   Output: %OUTPUT_P8_RANKING%
python scripts\phase8_ranking\predict_optimized_ranking.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P8_RANKING%"
if errorlevel 1 (
    echo [ERROR] Phase 8 Ranking failed
    exit /b 1
)
echo [OK] Phase 8 Ranking Complete
echo.

REM ============================================================
REM Phase 8: Regression予測
REM ============================================================
set "OUTPUT_P8_REGRESSION=data\predictions\phase8_regression\%KEIBAJO_NAME%_%DATE_SHORT%_phase8_regression.csv"

echo [Phase 8 Regression] 予測実行中...
echo   Input: %FEATURES_CSV%
echo   Output: %OUTPUT_P8_REGRESSION%
python scripts\phase8_regression\predict_optimized_regression.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P8_REGRESSION%"
if errorlevel 1 (
    echo [ERROR] Phase 8 Regression failed
    exit /b 1
)
echo [OK] Phase 8 Regression Complete
echo.

REM ============================================================
REM Phase 5: アンサンブル統合
REM ============================================================
set "OUTPUT_ENSEMBLE=data\predictions\phase5\%KEIBAJO_NAME%_%DATE_SHORT%_ensemble_optimized.csv"

echo [Phase 5 Ensemble] 統合実行中...
echo   Binary Input: %OUTPUT_P7_BINARY%
echo   Ranking Input: %OUTPUT_P8_RANKING%
echo   Regression Input: %OUTPUT_P8_REGRESSION%
echo   Output: %OUTPUT_ENSEMBLE%
python scripts\phase5_ensemble\ensemble_optimized.py "%OUTPUT_P7_BINARY%" "%OUTPUT_P8_RANKING%" "%OUTPUT_P8_REGRESSION%" "%OUTPUT_ENSEMBLE%"
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
call scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE% "%OUTPUT_ENSEMBLE%"
if errorlevel 1 (
    echo [WARNING] Phase 6 でエラーが発生しました
    echo [INFO] 予測結果は以下に保存されています: %OUTPUT_ENSEMBLE%
    echo [INFO] 手動でPhase 6を実行する場合:
    echo   scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE% "%OUTPUT_ENSEMBLE%"
) else (
    echo [OK] Phase 6 Complete
)
echo.

echo ============================================================
echo 全フェーズ完了 (Phase 7-8-5)
echo ============================================================
echo 実行終了: %DATE% %TIME%
echo.
echo 【出力ファイル一覧】
echo.
echo [予測CSVファイル]
echo   - Phase 7 Binary    : %OUTPUT_P7_BINARY%
echo   - Phase 8 Ranking   : %OUTPUT_P8_RANKING%
echo   - Phase 8 Regression: %OUTPUT_P8_REGRESSION%
echo   - Phase 5 Ensemble  : %OUTPUT_ENSEMBLE%
echo.
echo [配信用テキストファイル]
set "NOTE_TXT=predictions\%KEIBAJO_NAME%_%DATE_SHORT%_note.txt"
set "BOOKERS_TXT=predictions\%KEIBAJO_NAME%_%DATE_SHORT%_bookers.txt"
set "TWEET_TXT=predictions\%KEIBAJO_NAME%_%DATE_SHORT%_tweet.txt"

if exist "%NOTE_TXT%" (
    echo   ✓ Note用    : %NOTE_TXT%
) else (
    echo   ✗ Note用    : %NOTE_TXT% (未作成)
)

if exist "%BOOKERS_TXT%" (
    echo   ✓ ブッカーズ用: %BOOKERS_TXT%
) else (
    echo   ✗ ブッカーズ用: %BOOKERS_TXT% (未作成)
)

if exist "%TWEET_TXT%" (
    echo   ✓ Twitter用 : %TWEET_TXT%
) else (
    echo   ✗ Twitter用 : %TWEET_TXT% (未作成)
)
echo.
echo ============================================================
echo.
echo 【ファイルを開く】
if exist "%NOTE_TXT%" (
    echo Noteファイルを開きますか？ (Enter で開く / Ctrl+C でスキップ)
    pause > nul
    notepad "%NOTE_TXT%"
)
echo.

endlocal
