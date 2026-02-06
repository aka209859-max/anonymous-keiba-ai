@echo off
setlocal enabledelayedexpansion

REM =============================================================================
REM 地方競馬AI予想システム 一括実行バッチ（効率化版）
REM =============================================================================
REM 使用例: run_all.bat 55 2026-02-07

if "%~1"=="" (
    echo ERROR: 競馬場コードが指定されていません。
    echo 使用例: run_all.bat 55 2026-02-07
    pause
    exit /b 1
)

if "%~2"=="" (
    echo ERROR: 開催日が指定されていません。
    echo 使用例: run_all.bat 55 2026-02-07
    pause
    exit /b 1
)

set KEIBAJO_CODE=%~1
set TARGET_DATE=%~2
set DATE_SHORT=%TARGET_DATE:~0,4%%TARGET_DATE:~5,2%%TARGET_DATE:~8,2%

REM 競馬場コード → 名称変換
if "%KEIBAJO_CODE%"=="1" set KEIBAJO_NAME=門別& set MODEL_PREFIX=monbetsu
if "%KEIBAJO_CODE%"=="2" set KEIBAJO_NAME=盛岡& set MODEL_PREFIX=morioka
if "%KEIBAJO_CODE%"=="3" set KEIBAJO_NAME=水沢& set MODEL_PREFIX=mizusawa
if "%KEIBAJO_CODE%"=="42" set KEIBAJO_NAME=浦和& set MODEL_PREFIX=urawa
if "%KEIBAJO_CODE%"=="43" set KEIBAJO_NAME=船橋& set MODEL_PREFIX=funabashi
if "%KEIBAJO_CODE%"=="44" set KEIBAJO_NAME=大井& set MODEL_PREFIX=ooi
if "%KEIBAJO_CODE%"=="45" set KEIBAJO_NAME=川崎& set MODEL_PREFIX=kawasaki
if "%KEIBAJO_CODE%"=="46" set KEIBAJO_NAME=金沢& set MODEL_PREFIX=kanazawa
if "%KEIBAJO_CODE%"=="47" set KEIBAJO_NAME=笠松& set MODEL_PREFIX=kasamatsu
if "%KEIBAJO_CODE%"=="48" set KEIBAJO_NAME=名古屋& set MODEL_PREFIX=nagoya
if "%KEIBAJO_CODE%"=="50" set KEIBAJO_NAME=園田& set MODEL_PREFIX=sonoda
if "%KEIBAJO_CODE%"=="51" set KEIBAJO_NAME=姫路& set MODEL_PREFIX=himeji
if "%KEIBAJO_CODE%"=="54" set KEIBAJO_NAME=高知& set MODEL_PREFIX=kochi
if "%KEIBAJO_CODE%"=="55" set KEIBAJO_NAME=佐賀& set MODEL_PREFIX=saga

if not defined KEIBAJO_NAME (
    echo ERROR: 対応していない競馬場コード: %KEIBAJO_CODE%
    pause
    exit /b 1
)

REM ログファイル
if not exist logs mkdir logs
set LOG_FILE=logs\run_log_%DATE_SHORT%_%KEIBAJO_CODE%.txt

echo =============================================================================
echo 地方競馬AI予想システム 一括実行
echo =============================================================================
echo 競馬場: %KEIBAJO_NAME% (%KEIBAJO_CODE%)
echo 開催日: %TARGET_DATE%
echo 実行開始: %date% %time%
echo =============================================================================
echo.
echo ログファイル: %LOG_FILE%
echo.

REM Phase 0: データ取得
echo Phase 0 - データ取得中... (PC-KEIBA)
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %TARGET_DATE% >> %LOG_FILE% 2>&1
if errorlevel 1 (
    echo ERROR: Phase 0 でエラーが発生しました。ログを確認してください: %LOG_FILE%
    pause
    exit /b 1
)
echo OK - Phase 0 完了
echo.

REM Phase 1: 特徴量作成
echo Phase 1 - 特徴量作成中...
python scripts\phase1_feature_engineering\prepare_features.py data\raw\%TARGET_DATE:~0,4%\%TARGET_DATE:~5,2%\%KEIBAJO_NAME%_%DATE_SHORT%_raw.csv data\features\%TARGET_DATE:~0,4%\%TARGET_DATE:~5,2%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv >> %LOG_FILE% 2>&1
if errorlevel 1 (
    echo ERROR: Phase 1 でエラーが発生しました。ログを確認してください: %LOG_FILE%
    pause
    exit /b 1
)
echo OK - Phase 1 完了
echo.

REM Phase 3: 二値分類予測
echo Phase 3 - 二値分類予測中...
python scripts\phase3_binary\predict_phase3_inference.py data\features\%TARGET_DATE:~0,4%\%TARGET_DATE:~5,2%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv models\binary\%MODEL_PREFIX%_2020-2025_v3_model.txt data\predictions\phase3\%KEIBAJO_NAME%_%DATE_SHORT%_phase3_binary.csv >> %LOG_FILE% 2>&1
if errorlevel 1 (
    echo ERROR: Phase 3 でエラーが発生しました。ログを確認してください: %LOG_FILE%
    pause
    exit /b 1
)
echo OK - Phase 3 完了
echo.

REM Phase 4-1: ランキング予測
echo Phase 4-1 - ランキング予測中...
python scripts\phase4_ranking\predict_phase4_ranking_inference.py data\features\%TARGET_DATE:~0,4%\%TARGET_DATE:~5,2%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv models\ranking\%MODEL_PREFIX%_2020-2025_v3_with_race_id_ranking_model.txt data\predictions\phase4_ranking\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_ranking.csv >> %LOG_FILE% 2>&1
if errorlevel 1 (
    echo ERROR: Phase 4-1 でエラーが発生しました。ログを確認してください: %LOG_FILE%
    pause
    exit /b 1
)
echo OK - Phase 4-1 完了
echo.

REM Phase 4-2: 回帰予測
echo Phase 4-2 - 回帰予測中...
python scripts\phase4_regression\predict_phase4_regression_inference.py data\features\%TARGET_DATE:~0,4%\%TARGET_DATE:~5,2%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv models\regression\%MODEL_PREFIX%_2020-2025_v3_time_regression_model.txt data\predictions\phase4_regression\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_regression.csv >> %LOG_FILE% 2>&1
if errorlevel 1 (
    echo ERROR: Phase 4-2 でエラーが発生しました。ログを確認してください: %LOG_FILE%
    pause
    exit /b 1
)
echo OK - Phase 4-2 完了
echo.

REM Phase 5: アンサンブル統合
echo Phase 5 - アンサンブル統合中...
python scripts\phase5_ensemble\ensemble_predictions.py data\predictions\phase3\%KEIBAJO_NAME%_%DATE_SHORT%_phase3_binary.csv data\predictions\phase4_ranking\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_ranking.csv data\predictions\phase4_regression\%KEIBAJO_NAME%_%DATE_SHORT%_phase4_regression.csv data\predictions\phase5\%KEIBAJO_NAME%_%DATE_SHORT%_ensemble.csv >> %LOG_FILE% 2>&1
if errorlevel 1 (
    echo ERROR: Phase 5 でエラーが発生しました。ログを確認してください: %LOG_FILE%
    pause
    exit /b 1
)
echo OK - Phase 5 完了
echo.

REM 配信用テキスト生成
echo 配信用テキスト - 生成中...
if not exist predictions mkdir predictions
python scripts\phase5_ensemble\generate_distribution.py data\predictions\phase5\%KEIBAJO_NAME%_%DATE_SHORT%_ensemble.csv predictions\%KEIBAJO_NAME%_%DATE_SHORT%_配信用.txt >> %LOG_FILE% 2>&1
if errorlevel 1 (
    echo ERROR: 配信用テキスト生成でエラーが発生しました。ログを確認してください: %LOG_FILE%
    pause
    exit /b 1
)
echo OK - 配信用テキスト生成完了
echo.

echo =============================================================================
echo 全フェーズ完了！
echo =============================================================================
echo 予想結果: data\predictions\phase5\%KEIBAJO_NAME%_%DATE_SHORT%_ensemble.csv
echo 配信用テキスト: predictions\%KEIBAJO_NAME%_%DATE_SHORT%_配信用.txt
echo ログファイル: %LOG_FILE%
echo =============================================================================
echo.
echo 配信用テキストを表示します...
echo.
type predictions\%KEIBAJO_NAME%_%DATE_SHORT%_配信用.txt
echo.
pause

endlocal
