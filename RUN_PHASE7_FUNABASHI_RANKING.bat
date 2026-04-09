@echo off
REM UTF-8 BOM付きで保存すること
setlocal EnableDelayedExpansion

echo ============================================================
echo [Phase 7 Ranking] Funabashi Feature Selection Test
echo ============================================================
echo.
echo Target data: funabashi_2020-2026_with_time_PHASE78.csv
echo Purpose: Select optimal features for Ranking model
echo Estimated time: 10-20 minutes
echo.

REM 出力ディレクトリの作成
if not exist "data\features\selected" mkdir "data\features\selected"
if not exist "data\reports\phase7_feature_selection" mkdir "data\reports\phase7_feature_selection"

REM Check input file
set INPUT_FILE=data\training\funabashi_2020-2026_with_time_PHASE78.csv
if not exist "%INPUT_FILE%" (
    echo [ERROR] Input file not found
    echo    %INPUT_FILE%
    echo.
    echo Please run GENERATE_ALL_TRAINING_DATA.bat first.
    pause
    exit /b 1
)

echo [OK] Input file verified
echo.
echo ============================================================
echo Starting Phase 7 Ranking feature selection...
echo ============================================================
echo.

REM Run Phase 7 Ranking (remove --verbose option)
python scripts\phase7_feature_selection\run_boruta_ranking.py ^
  "%INPUT_FILE%" ^
  --max-iter 100

if !ERRORLEVEL! EQU 0 (
    echo.
    echo ============================================================
    echo [OK] Funabashi Phase 7 Ranking feature selection completed!
    echo ============================================================
    echo.
    echo Output files:
    echo   - data\features\selected\funabashi_ranking_selected_features.csv
    echo   - data\reports\phase7_feature_selection\funabashi_ranking_importance.png
    echo   - data\reports\phase7_feature_selection\funabashi_ranking_report.json
    echo.
    echo Next steps:
    echo   1. Check feature importance graph
    echo   2. Run Phase 7 Regression
    echo   3. Run Phase 8 Optuna optimization
    echo.
) else (
    echo.
    echo ============================================================
    echo [ERROR] An error occurred
    echo ============================================================
    echo.
    echo Troubleshooting:
    echo   1. Verify data file structure
    echo   2. Check if required Python packages are installed:
    echo      pip install boruta scikit-learn pandas numpy matplotlib
    echo   3. Try reducing --max-iter (100 to 50)
    echo.
)

pause
