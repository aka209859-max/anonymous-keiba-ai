@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

echo ============================================================
echo 🧪 船橋 Phase 7 Ranking 特徴量選択テスト
echo ============================================================
echo.
echo 📊 対象データ: funabashi_2020-2026_with_time_PHASE78.csv
echo 🎯 目的: Ranking学習に最適な特徴量を選定
echo ⏱️  推定時間: 約10〜20分
echo.

REM 出力ディレクトリの作成
if not exist "data\features\selected" mkdir "data\features\selected"
if not exist "data\reports\phase7_feature_selection" mkdir "data\reports\phase7_feature_selection"

REM 入力ファイルの確認
set INPUT_FILE=data\training\funabashi_2020-2026_with_time_PHASE78.csv
if not exist "%INPUT_FILE%" (
    echo ❌ エラー: 入力ファイルが見つかりません
    echo    %INPUT_FILE%
    echo.
    echo 先に GENERATE_ALL_TRAINING_DATA.bat を実行してください。
    pause
    exit /b 1
)

echo ✅ 入力ファイル確認完了
echo.
echo ============================================================
echo Phase 7 Ranking 特徴量選択を開始します...
echo ============================================================
echo.

REM Phase 7 Ranking 実行
python scripts\phase7_feature_selection\run_boruta_ranking.py ^
  "%INPUT_FILE%" ^
  --max-iter 100 ^
  --verbose

if !ERRORLEVEL! EQU 0 (
    echo.
    echo ============================================================
    echo ✅ 船橋 Phase 7 Ranking 特徴量選択が完了しました！
    echo ============================================================
    echo.
    echo 📁 出力ファイル:
    echo   - data\features\selected\funabashi_ranking_selected_features.csv
    echo   - data\reports\phase7_feature_selection\funabashi_ranking_importance.png
    echo   - data\reports\phase7_feature_selection\funabashi_ranking_report.json
    echo.
    echo 次のステップ:
    echo   1. 特徴量重要度グラフを確認
    echo   2. Phase 7 Regression を実行
    echo   3. Phase 8 Optuna最適化を実行
    echo.
) else (
    echo.
    echo ============================================================
    echo ❌ エラーが発生しました
    echo ============================================================
    echo.
    echo トラブルシューティング:
    echo   1. データファイルの構造を確認してください
    echo   2. 必要なPythonパッケージがインストールされているか確認してください
    echo      pip install boruta scikit-learn pandas numpy matplotlib
    echo   3. --max-iter を減らしてみてください (100 → 50)
    echo.
)

pause
