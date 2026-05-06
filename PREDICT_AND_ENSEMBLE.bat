@echo off
REM ================================================================================
REM Phase 3-4-5 統合予測実行バッチ（距離カテゴリ対応）
REM
REM 処理内容:
REM   1. Phase 3: Binary（二値分類）予測
REM   2. Phase 4-1: Ranking（順位）予測
REM   3. Phase 4-2: Regression（タイム）予測
REM   4. Phase 5: Ensemble（アンサンブル統合）
REM
REM 使用法:
REM   PREDICT_AND_ENSEMBLE.bat <競馬場名> <日付> <入力CSV> <モデルディレクトリ>
REM
REM 例:
REM   PREDICT_AND_ENSEMBLE.bat urawa 20250207 data\test\urawa_20250207_67features.csv models
REM ================================================================================

setlocal enabledelayedexpansion

REM ====================
REM 1. 引数チェック
REM ====================

if "%1"=="" (
    echo エラー: 競馬場名が指定されていません
    echo.
    echo 使用法: PREDICT_AND_ENSEMBLE.bat ^<競馬場名^> ^<日付^> ^<入力CSV^> ^<モデルディレクトリ^>
    echo.
    echo 例:
    echo   PREDICT_AND_ENSEMBLE.bat urawa 20250207 data\test\urawa_20250207_67features.csv models
    exit /b 1
)

if "%2"=="" (
    echo エラー: 日付が指定されていません
    exit /b 1
)

if "%3"=="" (
    echo エラー: 入力CSVファイルが指定されていません
    exit /b 1
)

if "%4"=="" (
    echo エラー: モデルディレクトリが指定されていません
    exit /b 1
)

set KEIBAJO=%1
set DATE=%2
set INPUT_CSV=%3
set MODEL_BASE_DIR=%4

echo ================================================================================
echo Phase 3-4-5 統合予測実行（距離カテゴリ対応）
echo ================================================================================
echo.
echo 設定:
echo   - 競馬場: %KEIBAJO%
echo   - 日付: %DATE%
echo   - 入力CSV: %INPUT_CSV%
echo   - モデルベースディレクトリ: %MODEL_BASE_DIR%
echo.

REM ====================
REM 2. 入力ファイルチェック
REM ====================

if not exist "%INPUT_CSV%" (
    echo.
    echo [ERROR] 入力CSVファイルが見つかりません: %INPUT_CSV%
    exit /b 1
)

echo [OK] 入力CSVファイル確認完了: %INPUT_CSV%

REM ====================
REM 3. モデルディレクトリチェック
REM ====================

set BINARY_MODEL_DIR=%MODEL_BASE_DIR%\binary_distance
set RANKING_MODEL_DIR=%MODEL_BASE_DIR%\ranking_distance
set REGRESSION_MODEL_DIR=%MODEL_BASE_DIR%\regression_distance

if not exist "%BINARY_MODEL_DIR%" (
    echo.
    echo [ERROR] Binaryモデルディレクトリが見つかりません: %BINARY_MODEL_DIR%
    exit /b 1
)

if not exist "%RANKING_MODEL_DIR%" (
    echo.
    echo [ERROR] Rankingモデルディレクトリが見つかりません: %RANKING_MODEL_DIR%
    exit /b 1
)

if not exist "%REGRESSION_MODEL_DIR%" (
    echo.
    echo [ERROR] Regressionモデルディレクトリが見つかりません: %REGRESSION_MODEL_DIR%
    exit /b 1
)

echo [OK] 全モデルディレクトリ確認完了
echo.

REM ====================
REM 4. 出力ディレクトリ作成
REM ====================

set OUTPUT_BASE=data\predictions
set OUTPUT_BINARY=%OUTPUT_BASE%\binary
set OUTPUT_RANKING=%OUTPUT_BASE%\ranking
set OUTPUT_REGRESSION=%OUTPUT_BASE%\regression
set OUTPUT_ENSEMBLE=%OUTPUT_BASE%\ensemble

if not exist "%OUTPUT_BINARY%" mkdir "%OUTPUT_BINARY%"
if not exist "%OUTPUT_RANKING%" mkdir "%OUTPUT_RANKING%"
if not exist "%OUTPUT_REGRESSION%" mkdir "%OUTPUT_REGRESSION%"
if not exist "%OUTPUT_ENSEMBLE%" mkdir "%OUTPUT_ENSEMBLE%"

echo [OK] 出力ディレクトリ作成完了:
echo   - %OUTPUT_BINARY%
echo   - %OUTPUT_RANKING%
echo   - %OUTPUT_REGRESSION%
echo   - %OUTPUT_ENSEMBLE%
echo.

REM ====================
REM 5. 出力ファイル名設定
REM ====================

set BINARY_OUTPUT=%OUTPUT_BINARY%\%KEIBAJO%_%DATE%_binary.csv
set RANKING_OUTPUT=%OUTPUT_RANKING%\%KEIBAJO%_%DATE%_ranking.csv
set REGRESSION_OUTPUT=%OUTPUT_REGRESSION%\%KEIBAJO%_%DATE%_regression.csv
set ENSEMBLE_OUTPUT=%OUTPUT_ENSEMBLE%\%KEIBAJO%_%DATE%_ensemble.csv

echo 出力ファイル:
echo   - Binary: %BINARY_OUTPUT%
echo   - Ranking: %RANKING_OUTPUT%
echo   - Regression: %REGRESSION_OUTPUT%
echo   - Ensemble: %ENSEMBLE_OUTPUT%
echo.

REM ====================
REM 6. Phase 3: Binary予測
REM ====================

echo ================================================================================
echo [1/4] Phase 3: Binary（二値分類）予測実行
echo ================================================================================
echo.

python scripts\predict\predict_binary_distance.py ^
    --input "%INPUT_CSV%" ^
    --models "%BINARY_MODEL_DIR%" ^
    --output "%BINARY_OUTPUT%" ^
    --keibajo %KEIBAJO%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Binary予測でエラーが発生しました
    exit /b 1
)

echo.
echo [SUCCESS] Binary予測完了: %BINARY_OUTPUT%
echo.

REM ====================
REM 7. Phase 4-1: Ranking予測
REM ====================

echo ================================================================================
echo [2/4] Phase 4-1: Ranking（順位）予測実行
echo ================================================================================
echo.

python scripts\predict\predict_ranking_distance.py ^
    --input "%INPUT_CSV%" ^
    --models "%RANKING_MODEL_DIR%" ^
    --output "%RANKING_OUTPUT%" ^
    --keibajo %KEIBAJO%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Ranking予測でエラーが発生しました
    exit /b 1
)

echo.
echo [SUCCESS] Ranking予測完了: %RANKING_OUTPUT%
echo.

REM ====================
REM 8. Phase 4-2: Regression予測
REM ====================

echo ================================================================================
echo [3/4] Phase 4-2: Regression（タイム）予測実行
echo ================================================================================
echo.

python scripts\predict\predict_regression_distance.py ^
    --input "%INPUT_CSV%" ^
    --models "%REGRESSION_MODEL_DIR%" ^
    --output "%REGRESSION_OUTPUT%" ^
    --keibajo %KEIBAJO%

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Regression予測でエラーが発生しました
    exit /b 1
)

echo.
echo [SUCCESS] Regression予測完了: %REGRESSION_OUTPUT%
echo.

REM ====================
REM 9. Phase 5: Ensemble統合
REM ====================

echo ================================================================================
echo [4/4] Phase 5: Ensemble（アンサンブル統合）実行
echo ================================================================================
echo.

python scripts\phase5_ensemble\ensemble_distance_category.py ^
    --binary "%BINARY_OUTPUT%" ^
    --ranking "%RANKING_OUTPUT%" ^
    --regression "%REGRESSION_OUTPUT%" ^
    --output "%ENSEMBLE_OUTPUT%" ^
    --weight-binary 0.3 ^
    --weight-ranking 0.5 ^
    --weight-regression 0.2

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Ensemble統合でエラーが発生しました
    exit /b 1
)

echo.
echo [SUCCESS] Ensemble統合完了: %ENSEMBLE_OUTPUT%
echo.

REM ====================
REM 10. 完了メッセージ
REM ====================

echo ================================================================================
echo ✅ Phase 3-4-5 統合予測完了！
echo ================================================================================
echo.
echo 出力ファイル:
echo   [1] Binary予測:     %BINARY_OUTPUT%
echo   [2] Ranking予測:    %RANKING_OUTPUT%
echo   [3] Regression予測: %REGRESSION_OUTPUT%
echo   [4] Ensemble統合:   %ENSEMBLE_OUTPUT%
echo.
echo 次のステップ:
echo   - %ENSEMBLE_OUTPUT% を開いて予測結果を確認してください
echo   - final_rank列が最終予測順位です
echo   - ensemble_score_normalized列が0〜1の信頼スコアです
echo.

endlocal
exit /b 0
