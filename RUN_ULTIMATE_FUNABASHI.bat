@echo off
chcp 65001 >nul
REM ========================================================================
REM 船橋競馬場 完全実装テストバッチ
REM 
REM 目的: 船橋競馬場を対象に、Phase 7 → Phase 8 → Phase 5統合の
REM       完全なパイプラインをテスト実行します
REM
REM 実行フロー:
REM   Phase 7: Boruta特徴選択 (Binary/Ranking/Regression)
REM   Phase 8: Optunaハイパーパラメータ最適化 (Binary/Ranking/Regression)
REM   Phase 5: アンサンブル統合予測 (3モデル統合)
REM
REM 推定所要時間: 約1〜2時間
REM ========================================================================

echo ================================================================================
echo 船橋競馬場 完全実装テスト
echo ================================================================================
echo.
echo このバッチは船橋競馬場を対象に、Phase 7→8→5の完全なパイプラインを実行します
echo テスト成功後、RUN_ULTIMATE_ALL_VENUES.bat で全会場に展開できます
echo.

set VENUE=funabashi
set VENUE_JP=船橋
set TRAINING_FILE=data\training\%VENUE%_2020-2025_with_time.csv

echo [対象会場] %VENUE_JP% (%VENUE%)
echo [学習データ] %TRAINING_FILE%
echo.

REM 学習データの存在確認
if not exist "%TRAINING_FILE%" (
    echo [エラー] 学習データが見つかりません: %TRAINING_FILE%
    echo.
    echo 以下のファイルが必要です:
    echo   - data\training\funabashi_2020-2025_with_time.csv
    echo.
    pause
    exit /b 1
)

echo [確認] 学習データが見つかりました: %TRAINING_FILE%
echo.
echo [実行内容]
echo   Phase 7: Boruta特徴選択 (3モデル × 約10分 = 30分)
echo   Phase 8: Optuna最適化 (3モデル × 約20分 = 60分)
echo   Phase 5: アンサンブル統合予測
echo.
echo 推定所要時間: 約1.5〜2時間
echo.

pause

echo.
echo ================================================================================
echo Phase 7: Boruta特徴選択開始 (%VENUE_JP%)
echo ================================================================================
echo 開始時刻: %date% %time%
echo.

REM ----------------------------------------
REM Phase 7-1: Binary分類用特徴選択
REM ----------------------------------------
echo [Phase 7-1/3] Binary分類用Boruta特徴選択実行中...
python scripts\phase7_feature_selection\run_boruta_selection.py ^
    "%TRAINING_FILE%" ^
    --max-iter 100 ^
    --n-estimators 100

if errorlevel 1 (
    echo [エラー] Binary分類用Boruta特徴選択に失敗しました
    pause
    exit /b 1
)

echo [成功] Binary分類用Boruta特徴選択完了
echo.

REM ----------------------------------------
REM Phase 7-2: Ranking予測用特徴選択
REM ----------------------------------------
echo [Phase 7-2/3] Ranking予測用Boruta特徴選択実行中...
python scripts\phase7_feature_selection\run_boruta_ranking.py ^
    "%TRAINING_FILE%" ^
    --max-iter 100 ^
    --n-estimators 100

if errorlevel 1 (
    echo [エラー] Ranking予測用Boruta特徴選択に失敗しました
    pause
    exit /b 1
)

echo [成功] Ranking予測用Boruta特徴選択完了
echo.

REM ----------------------------------------
REM Phase 7-3: Regression予測用特徴選択
REM ----------------------------------------
echo [Phase 7-3/3] Regression予測用Boruta特徴選択実行中...
python scripts\phase7_feature_selection\run_boruta_regression.py ^
    "%TRAINING_FILE%" ^
    --max-iter 100 ^
    --n-estimators 100

if errorlevel 1 (
    echo [エラー] Regression予測用Boruta特徴選択に失敗しました
    pause
    exit /b 1
)

echo [成功] Regression予測用Boruta特徴選択完了
echo.
echo [Phase 7 完了] %VENUE_JP%の特徴選択が完了しました
echo 終了時刻: %date% %time%
echo.

pause

echo.
echo ================================================================================
echo Phase 8: Optunaハイパーパラメータ最適化開始 (%VENUE_JP%)
echo ================================================================================
echo 開始時刻: %date% %time%
echo.

REM ----------------------------------------
REM Phase 8-1: Binary分類モデル最適化
REM ----------------------------------------
echo [Phase 8-1/3] Binary分類モデル最適化実行中...
echo   試行回数: 100回
echo   タイムアウト: 2時間
echo.

python scripts\phase8_auto_tuning\run_optuna_tuning.py ^
    "%TRAINING_FILE%" ^
    --selected-features "data\features\selected\%VENUE%_selected_features.csv" ^
    --n-trials 100 ^
    --timeout 7200 ^
    --cv-folds 3

if errorlevel 1 (
    echo [エラー] Binary分類モデル最適化に失敗しました
    pause
    exit /b 1
)

echo [成功] Binary分類モデル最適化完了
echo.

REM ----------------------------------------
REM Phase 8-2: Rankingモデル最適化
REM ----------------------------------------
echo [Phase 8-2/3] Rankingモデル最適化実行中...
echo   試行回数: 100回
echo   タイムアウト: 2時間
echo.

python scripts\phase8_auto_tuning\run_optuna_tuning_ranking.py ^
    "%TRAINING_FILE%" ^
    --selected-features "data\features\selected\%VENUE%_ranking_selected_features.csv" ^
    --n-trials 100 ^
    --timeout 7200 ^
    --cv-folds 3

if errorlevel 1 (
    echo [エラー] Rankingモデル最適化に失敗しました
    pause
    exit /b 1
)

echo [成功] Rankingモデル最適化完了
echo.

REM ----------------------------------------
REM Phase 8-3: Regressionモデル最適化
REM ----------------------------------------
echo [Phase 8-3/3] Regressionモデル最適化実行中...
echo   試行回数: 100回
echo   タイムアウト: 2時間
echo.

python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py ^
    "%TRAINING_FILE%" ^
    --selected-features "data\features\selected\%VENUE%_regression_selected_features.csv" ^
    --n-trials 100 ^
    --timeout 7200 ^
    --cv-folds 3

if errorlevel 1 (
    echo [エラー] Regressionモデル最適化に失敗しました
    pause
    exit /b 1
)

echo [成功] Regressionモデル最適化完了
echo.
echo [Phase 8 完了] %VENUE_JP%のモデル最適化が完了しました
echo 終了時刻: %date% %time%
echo.

pause

echo.
echo ================================================================================
echo Phase 5: アンサンブル統合予測テスト (%VENUE_JP%)
echo ================================================================================
echo.

REM テストデータがある場合は予測実行
set TEST_FILE=test_data\%VENUE%_test.csv
if exist "%TEST_FILE%" (
    echo [Phase 5] アンサンブル統合予測実行中...
    echo テストデータ: %TEST_FILE%
    echo.
    
    python scripts\phase5_ensemble\ensemble_optimized.py ^
        %VENUE% ^
        "%TEST_FILE%" ^
        --output-dir "data\predictions\phase5_optimized"
    
    if errorlevel 1 (
        echo [エラー] アンサンブル統合予測に失敗しました
        pause
        exit /b 1
    )
    
    echo [成功] アンサンブル統合予測完了
    echo.
) else (
    echo [スキップ] テストデータが見つかりません: %TEST_FILE%
    echo Phase 5のテストをスキップします
    echo.
    echo テストデータがある場合は以下のコマンドで予測を実行できます:
    echo   python scripts\phase5_ensemble\ensemble_optimized.py %VENUE% テストデータ.csv
    echo.
)

echo.
echo ================================================================================
echo 船橋競馬場 完全実装テスト完了
echo ================================================================================
echo 終了時刻: %date% %time%
echo.
echo [生成ファイル確認]
echo.
echo Phase 7 特徴選択結果:
dir /b data\features\selected\%VENUE%*.csv 2>nul
echo.
echo Phase 8 最適化モデル:
dir /b data\models\tuned\%VENUE%*.txt 2>nul
echo.
echo Phase 5 予測結果:
dir /b data\predictions\phase5_optimized\%VENUE%*.csv 2>nul
echo.
echo [次のステップ]
echo   テストが成功しました！
echo   RUN_ULTIMATE_ALL_VENUES.bat を実行して全14会場に展開してください
echo.

pause
