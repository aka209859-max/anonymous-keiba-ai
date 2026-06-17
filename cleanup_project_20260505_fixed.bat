@echo off
REM Project Cleanup Batch - Phase 2 Preparation
REM Date: 2026-05-05
REM Purpose: Move old files to old/ folder

echo ========================================
echo anonymous-keiba-ai Project Cleanup
echo Phase 2 Preparation (67 features)
echo ========================================
echo.

REM Confirmation
echo This script will:
echo - Move training results (PNG/TXT) to old\results\
echo - Move training CSV to old\data\training_csv\
echo - Move old batch files to old\batch_scripts\
echo - Move old models (34 features) to old\models_34features\
echo - Move old scripts to old\scripts\
echo - Move old documents to old\docs_archive\
echo.
echo Please backup the entire project before execution!
echo.
set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Process cancelled.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 1: Creating old\ folder structure
echo ========================================

mkdir old 2>nul
mkdir old\models_34features 2>nul
mkdir old\models_34features\binary 2>nul
mkdir old\models_34features\ranking 2>nul
mkdir old\models_34features\regression 2>nul
mkdir old\scripts 2>nul
mkdir old\scripts\phase1 2>nul
mkdir old\scripts\phase7-8 2>nul
mkdir old\scripts\phase11-12 2>nul
mkdir old\data 2>nul
mkdir old\data\training_csv 2>nul
mkdir old\data\payouts 2>nul
mkdir old\data\features_old 2>nul
mkdir old\docs_archive 2>nul
mkdir old\docs_archive\completion_reports 2>nul
mkdir old\docs_archive\quickstart_guides 2>nul
mkdir old\docs_archive\phase_specific 2>nul
mkdir old\results 2>nul
mkdir old\results\binary_results 2>nul
mkdir old\results\ranking_results 2>nul
mkdir old\results\regression_results 2>nul
mkdir old\batch_scripts 2>nul
mkdir old\batch_scripts\run_all_variants 2>nul
mkdir old\batch_scripts\phase7-8 2>nul
mkdir old\batch_scripts\phase10-12 2>nul
mkdir old\archives 2>nul
mkdir old\misc 2>nul

echo Folder structure created.
echo.

echo ========================================
echo Step 2: Moving training results
echo ========================================

move *_model.png old\results\binary_results\ 2>nul
move *_score.txt old\results\binary_results\ 2>nul
move *_ranking_model.png old\results\ranking_results\ 2>nul
move *_ranking_score.txt old\results\ranking_results\ 2>nul
move *_time_regression_model.png old\results\regression_results\ 2>nul
move *_time_regression_score.txt old\results\regression_results\ 2>nul
move *_with_race_id_ranking_model.png old\results\ranking_results\ 2>nul
move *_with_race_id_ranking_score.txt old\results\ranking_results\ 2>nul
move *_with_time_regression_model.png old\results\regression_results\ 2>nul
move *_with_time_regression_score.txt old\results\regression_results\ 2>nul

echo Training results moved.
echo.

echo ========================================
echo Step 3: Moving training CSV files
echo ========================================

move *_2020-2025_v3.csv old\data\training_csv\ 2>nul
move *_2020-2025_v3_with_race_id.csv old\data\training_csv\ 2>nul
move *_2020-2025_v3_time.csv old\data\training_csv\ 2>nul
move *_2020-2025_with_time.csv old\data\training_csv\ 2>nul
move *_2020-2025_soha_time.csv old\data\training_csv\ 2>nul
move *_2023-2025_v3.csv old\data\training_csv\ 2>nul
move *_2023-2025_v3_with_race_id.csv old\data\training_csv\ 2>nul
move *_2023-2025_v3_time.csv old\data\training_csv\ 2>nul
move *_2023-2025_with_time.csv old\data\training_csv\ 2>nul
move *_2023-2025_soha_time.csv old\data\training_csv\ 2>nul
move *_2022-2025_v3.csv old\data\training_csv\ 2>nul
move *_2022-2025_v3_with_race_id.csv old\data\training_csv\ 2>nul
move *_2022-2025_v3_time.csv old\data\training_csv\ 2>nul
move *_2022-2025_with_time.csv old\data\training_csv\ 2>nul
move training_data_v2.csv old\data\training_csv\ 2>nul
move test_data.csv old\data\training_csv\ 2>nul
move test_data_v2.csv old\data\training_csv\ 2>nul

echo Training CSV files moved.
echo.

echo ========================================
echo Step 4: Moving old batch files
echo ========================================

move run_all_*.bat old\batch_scripts\run_all_variants\ 2>nul
move RUN_PHASE7_*.bat old\batch_scripts\phase7-8\ 2>nul
move RUN_PHASE8_*.bat old\batch_scripts\phase7-8\ 2>nul
move RUN_PHASE10_*.bat old\batch_scripts\phase10-12\ 2>nul
move EXTRACT_ALL_TRAINING_DATA.bat old\batch_scripts\ 2>nul
move GENERATE_ALL_TRAINING_DATA.bat old\batch_scripts\ 2>nul

echo Old batch files moved.
echo.

echo ========================================
echo Step 5: Moving payout files
echo ========================================

move *_payouts_official.csv old\data\payouts\ 2>nul
move *_payouts.csv old\data\payouts\ 2>nul

echo Payout files moved.
echo.

echo ========================================
echo Step 6: Moving archive files
echo ========================================

move *.zip old\archives\ 2>nul
move *.tar.gz old\archives\ 2>nul

echo Archive files moved.
echo.

echo ========================================
echo Step 7: Moving old models (34 features)
echo ========================================

xcopy /s models\binary\*.txt old\models_34features\binary\ 2>nul
xcopy /s models\ranking\*.txt old\models_34features\ranking\ 2>nul
xcopy /s models\regression\*.txt old\models_34features\regression\ 2>nul
del /q models\binary\*.txt 2>nul
del /q models\ranking\*.txt 2>nul
del /q models\regression\*.txt 2>nul

echo Old models moved.
echo.

echo ========================================
echo Step 8: Moving old scripts
echo ========================================

REM Phase1 old versions
if exist scripts\phase1_feature_engineering\prepare_features.py move scripts\phase1_feature_engineering\prepare_features.py old\scripts\phase1\ 2>nul
if exist scripts\phase1_feature_engineering\prepare_features_v2.py move scripts\phase1_feature_engineering\prepare_features_v2.py old\scripts\phase1\ 2>nul
if exist scripts\phase1_feature_engineering\prepare_features_safe.py move scripts\phase1_feature_engineering\prepare_features_safe.py old\scripts\phase1\ 2>nul

REM Phase7-8
if exist scripts\phase7_binary xcopy /s /i scripts\phase7_binary old\scripts\phase7-8\phase7_binary 2>nul
if exist scripts\phase7_feature_selection xcopy /s /i scripts\phase7_feature_selection old\scripts\phase7-8\phase7_feature_selection 2>nul
if exist scripts\phase8_auto_tuning xcopy /s /i scripts\phase8_auto_tuning old\scripts\phase7-8\phase8_auto_tuning 2>nul
if exist scripts\phase8_prediction xcopy /s /i scripts\phase8_prediction old\scripts\phase7-8\phase8_prediction 2>nul
if exist scripts\phase8_ranking xcopy /s /i scripts\phase8_ranking old\scripts\phase7-8\phase8_ranking 2>nul
if exist scripts\phase8_regression xcopy /s /i scripts\phase8_regression old\scripts\phase7-8\phase8_regression 2>nul

REM Phase11-12
if exist scripts\phase11_triple_umatan xcopy /s /i scripts\phase11_triple_umatan old\scripts\phase11-12\phase11_triple_umatan 2>nul
if exist scripts\phase12_umatan_model xcopy /s /i scripts\phase12_umatan_model old\scripts\phase11-12\phase12_umatan_model 2>nul

REM Delete
if exist scripts\phase7_binary rmdir /s /q scripts\phase7_binary 2>nul
if exist scripts\phase7_feature_selection rmdir /s /q scripts\phase7_feature_selection 2>nul
if exist scripts\phase8_auto_tuning rmdir /s /q scripts\phase8_auto_tuning 2>nul
if exist scripts\phase8_prediction rmdir /s /q scripts\phase8_prediction 2>nul
if exist scripts\phase8_ranking rmdir /s /q scripts\phase8_ranking 2>nul
if exist scripts\phase8_regression rmdir /s /q scripts\phase8_regression 2>nul
if exist scripts\phase11_triple_umatan rmdir /s /q scripts\phase11_triple_umatan 2>nul
if exist scripts\phase12_umatan_model rmdir /s /q scripts\phase12_umatan_model 2>nul

echo Old scripts moved.
echo.

echo ========================================
echo Step 9: Moving old documents
echo ========================================

move *COMPLETION_REPORT*.md old\docs_archive\completion_reports\ 2>nul
move *QUICKSTART*.md old\docs_archive\quickstart_guides\ 2>nul
move *GUIDE*.md old\docs_archive\phase_specific\ 2>nul
move PHASE3_*.md old\docs_archive\phase_specific\ 2>nul
move PHASE4_*.md old\docs_archive\phase_specific\ 2>nul
move PHASE5_*.md old\docs_archive\phase_specific\ 2>nul
move PHASE6_*.md old\docs_archive\phase_specific\ 2>nul
move PHASE7_*.md old\docs_archive\phase_specific\ 2>nul
move PHASE8_*.md old\docs_archive\phase_specific\ 2>nul
move PHASE9_*.md old\docs_archive\phase_specific\ 2>nul
move PHASE10_*.md old\docs_archive\phase_specific\ 2>nul
move PHASE11_*.md old\docs_archive\phase_specific\ 2>nul
move COMPLETE_*.md old\docs_archive\ 2>nul
move FINAL_*.md old\docs_archive\ 2>nul
move EXECUTION_*.md old\docs_archive\ 2>nul
move DATATYPE_*.md old\docs_archive\ 2>nul
move DEVELOPMENT_*.md old\docs_archive\ 2>nul
move FUNABASHI_*.md old\docs_archive\ 2>nul
move INVESTIGATION_*.md old\docs_archive\ 2>nul
move JRA_*.md old\docs_archive\ 2>nul
move JRDB_*.md old\docs_archive\ 2>nul
move JRAVAN_*.md old\docs_archive\ 2>nul
move MODEL_*.md old\docs_archive\ 2>nul
move OLD_*.md old\docs_archive\ 2>nul
move OPTION*.md old\docs_archive\ 2>nul
move OTHER_*.md old\docs_archive\ 2>nul
move RECONSTRUCTION_*.md old\docs_archive\ 2>nul
move REGIMAG_*.md old\docs_archive\ 2>nul
move RUN_*.md old\docs_archive\ 2>nul
move SCORE_*.md old\docs_archive\ 2>nul
move SIMPLE_*.md old\docs_archive\ 2>nul
move SQL_*.md old\docs_archive\ 2>nul
move SUMMARY_*.md old\docs_archive\ 2>nul
move WHAT_*.md old\docs_archive\ 2>nul
move ALL_*.md old\docs_archive\ 2>nul
move CURRENT_*.md old\docs_archive\ 2>nul
move BATCH_*.md old\docs_archive\ 2>nul
move COMMANDS_*.md old\docs_archive\ 2>nul
move CRITICAL_*.md old\docs_archive\ 2>nul
move DEEPSEARCH_*.md old\docs_archive\ 2>nul
move DOCUMENT_*.md old\docs_archive\ 2>nul
move FILE_*.md old\docs_archive\ 2>nul
move FIX_*.md old\docs_archive\ 2>nul
move GITHUB_*.md old\docs_archive\ 2>nul
move INSTRUCTION_*.md old\docs_archive\ 2>nul
move DIAGNOSIS_*.md old\docs_archive\ 2>nul
move DYNAMIC_*.md old\docs_archive\ 2>nul
move PREDICTION_*.md old\docs_archive\ 2>nul
move QUICK_*.md old\docs_archive\ 2>nul
move RANK_*.md old\docs_archive\ 2>nul
move ROADMAP_*.md old\docs_archive\ 2>nul
move SCRIPTS_*.md old\docs_archive\ 2>nul
move TARGET_*.md old\docs_archive\ 2>nul
move TECHNICAL_*.md old\docs_archive\ 2>nul
move VALIDATION_*.md old\docs_archive\ 2>nul

REM Exception: Keep PHASE2 and recent ULTIMATE/IMPLEMENTATION
if exist old\docs_archive\PHASE2_HIGHPERFORMANCE_PROGRESS.md move old\docs_archive\PHASE2_HIGHPERFORMANCE_PROGRESS.md . 2>nul
if exist old\docs_archive\ULTIMATE_IMPROVEMENT_PLAN.md move old\docs_archive\ULTIMATE_IMPROVEMENT_PLAN.md . 2>nul
if exist old\docs_archive\IMPLEMENTATION_PLAN_20260505.md move old\docs_archive\IMPLEMENTATION_PLAN_20260505.md . 2>nul

echo Old documents moved.
echo.

echo ========================================
echo Step 10: Moving other files
echo ========================================

REM Python scripts (root)
move train_development.py old\misc\ 2>nul
move train_all_venues.py old\misc\ 2>nul
move train_ranking_model.py old\misc\ 2>nul
move train_regression_model.py old\misc\ 2>nul
move ensemble_model.py old\misc\ 2>nul
move check_*.py old\misc\ 2>nul
move extract_*.py old\misc\ 2>nul
move predict_*.py old\misc\ 2>nul
move run_*.py old\misc\ 2>nul
move simulate_*.py old\misc\ 2>nul
move verify_*.py old\misc\ 2>nul
move add_*.py old\misc\ 2>nul
move analyze_*.py old\misc\ 2>nul
move backtesting_engine.py old\misc\ 2>nul
move betting_strategy.py old\misc\ 2>nul
move convert_*.py old\misc\ 2>nul
move dynamic_*.py old\misc\ 2>nul
move ensemble_predictor.py old\misc\ 2>nul
move generate_*.py old\misc\ 2>nul
move venue_*.py old\misc\ 2>nul
move inspect_*.py old\misc\ 2>nul

REM Batch files (root)
move daily_*.bat old\batch_scripts\ 2>nul
move run_*.bat old\batch_scripts\ 2>nul
move rename_models.bat old\batch_scripts\ 2>nul
move check_csv_files.bat old\batch_scripts\ 2>nul
move generate_all_*.bat old\batch_scripts\ 2>nul

REM SQL files
move *.sql old\misc\ 2>nul

REM PowerShell scripts
move *.ps1 old\batch_scripts\ 2>nul

REM Old cleanup files (keep latest)
move CREATE_BATCH_POWERSHELL.ps1 old\batch_scripts\ 2>nul

echo Other files moved.
echo.

echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Moved files:
echo - Training results (PNG/TXT) to old\results\
echo - Training CSV to old\data\training_csv\
echo - Old batch files to old\batch_scripts\
echo - Old models (34 features) to old\models_34features\
echo - Old scripts to old\scripts\
echo - Old documents to old\docs_archive\
echo - Other files to old\misc\
echo.
echo Remaining files:
echo - Latest scripts (scripts/phase0-6)
echo - Latest documents (PHASE2_HIGHPERFORMANCE_PROGRESS.md, etc.)
echo - Required config files (requirements.txt, .gitignore, README.md)
echo.
echo Next steps:
echo 1. Check project structure: tree /F /A
echo 2. Git commit: git add . ^&^& git commit -m "chore: cleanup old files to old/"
echo 3. Start Phase 2: Step 2-1-B (Data collection)
echo.

pause
