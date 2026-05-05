@echo off
chcp 65001 > nul
REM プロジェクト整理バッチファイル - Phase 2高性能化の準備
REM 作成日: 2026-05-05
REM 目的: 不要ファイル・旧モデルをold/フォルダに移動

echo ========================================
echo anonymous-keiba-ai プロジェクト整理
echo Phase 2高性能化（67特徴量版）準備
echo ========================================
echo.

REM 実行確認
echo このスクリプトは以下の処理を実行します:
echo - 学習結果（PNG/TXT）を old\results\ に移動
echo - 学習データCSVを old\data\training_csv\ に移動
echo - 旧バッチファイルを old\batch_scripts\ に移動
echo - 旧モデル（34特徴量）を old\models_34features\ に移動
echo - 旧スクリプトを old\scripts\ に移動
echo - 古いドキュメントを old\docs_archive\ に移動
echo.
echo 実行前に必ずプロジェクト全体をバックアップしてください！
echo.
set /p CONFIRM="続行しますか？ (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 処理をキャンセルしました。
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 1: old\フォルダ構造の作成
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

echo フォルダ構造を作成しました。
echo.

echo ========================================
echo Step 2: 学習結果（PNG/TXT）の移動
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

echo 学習結果を移動しました。
echo.

echo ========================================
echo Step 3: 学習データCSVの移動
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

echo 学習データCSVを移動しました。
echo.

echo ========================================
echo Step 4: 旧バッチファイルの移動
echo ========================================

move run_all_*.bat old\batch_scripts\run_all_variants\ 2>nul
move RUN_PHASE7_*.bat old\batch_scripts\phase7-8\ 2>nul
move RUN_PHASE8_*.bat old\batch_scripts\phase7-8\ 2>nul
move RUN_PHASE10_*.bat old\batch_scripts\phase10-12\ 2>nul
move EXTRACT_ALL_TRAINING_DATA.bat old\batch_scripts\ 2>nul
move GENERATE_ALL_TRAINING_DATA.bat old\batch_scripts\ 2>nul

echo 旧バッチファイルを移動しました。
echo.

echo ========================================
echo Step 5: payoutsファイルの移動
echo ========================================

move *_payouts_official.csv old\data\payouts\ 2>nul
move *_payouts.csv old\data\payouts\ 2>nul

echo payoutsファイルを移動しました。
echo.

echo ========================================
echo Step 6: アーカイブファイルの移動
echo ========================================

move *.zip old\archives\ 2>nul
move *.tar.gz old\archives\ 2>nul

echo アーカイブファイルを移動しました。
echo.

echo ========================================
echo Step 7: 旧モデル（34特徴量版）の移動
echo ========================================

xcopy /s models\binary\*.txt old\models_34features\binary\ 2>nul
xcopy /s models\ranking\*.txt old\models_34features\ranking\ 2>nul
xcopy /s models\regression\*.txt old\models_34features\regression\ 2>nul
del /q models\binary\*.txt 2>nul
del /q models\ranking\*.txt 2>nul
del /q models\regression\*.txt 2>nul

echo 旧モデルを移動しました。
echo.

echo ========================================
echo Step 8: 旧スクリプトの移動
echo ========================================

REM Phase1旧バージョン
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

REM 削除
if exist scripts\phase7_binary rmdir /s /q scripts\phase7_binary 2>nul
if exist scripts\phase7_feature_selection rmdir /s /q scripts\phase7_feature_selection 2>nul
if exist scripts\phase8_auto_tuning rmdir /s /q scripts\phase8_auto_tuning 2>nul
if exist scripts\phase8_prediction rmdir /s /q scripts\phase8_prediction 2>nul
if exist scripts\phase8_ranking rmdir /s /q scripts\phase8_ranking 2>nul
if exist scripts\phase8_regression rmdir /s /q scripts\phase8_regression 2>nul
if exist scripts\phase11_triple_umatan rmdir /s /q scripts\phase11_triple_umatan 2>nul
if exist scripts\phase12_umatan_model rmdir /s /q scripts\phase12_umatan_model 2>nul

echo 旧スクリプトを移動しました。
echo.

echo ========================================
echo Step 9: 古いドキュメントの移動
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
move PHASE12_*.md old\docs_archive\phase_specific\ 2>nul
move COMPLETE_*.md old\docs_archive\ 2>nul
move FINAL_*.md old\docs_archive\ 2>nul
move EXECUTION_*.md old\docs_archive\ 2>nul
move DATATYPE_*.md old\docs_archive\ 2>nul
move DEVELOPMENT_*.md old\docs_archive\ 2>nul
move FUNABASHI_*.md old\docs_archive\ 2>nul
move IMPLEMENTATION_*.md old\docs_archive\ 2>nul
move INVESTIGATION_*.md old\docs_archive\ 2>nul
move JRA_*.md old\docs_archive\ 2>nul
move MODEL_*.md old\docs_archive\ 2>nul
move OLD_*.md old\docs_archive\ 2>nul
move OPTION*.md old\docs_archive\ 2>nul
move OTHER_*.md old\docs_archive\ 2>nul
move RECONSTRUCTION_*.md old\docs_archive\ 2>nul
move SCORE_*.md old\docs_archive\ 2>nul
move SIMPLE_*.md old\docs_archive\ 2>nul
move SQL_*.md old\docs_archive\ 2>nul
move SUMMARY_*.md old\docs_archive\ 2>nul
move ULTIMATE_*.md old\docs_archive\ 2>nul
move WHAT_*.md old\docs_archive\ 2>nul
move ALL_*.md old\docs_archive\ 2>nul
move CURRENT_*.md old\docs_archive\ 2>nul

REM 例外: PHASE2とULTIMATE_IMPROVEMENT_PLANは残す
if exist old\docs_archive\PHASE2_HIGHPERFORMANCE_PROGRESS.md move old\docs_archive\PHASE2_HIGHPERFORMANCE_PROGRESS.md . 2>nul
if exist old\docs_archive\ULTIMATE_IMPROVEMENT_PLAN.md move old\docs_archive\ULTIMATE_IMPROVEMENT_PLAN.md . 2>nul

echo 古いドキュメントを移動しました。
echo.

echo ========================================
echo Step 10: その他のファイル移動
echo ========================================

REM Pythonスクリプト（ルート直下）
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

REM バッチファイル（ルート直下）
move daily_*.bat old\batch_scripts\ 2>nul
move run_*.bat old\batch_scripts\ 2>nul
move rename_models.bat old\batch_scripts\ 2>nul
move check_csv_files.bat old\batch_scripts\ 2>nul
move generate_all_*.bat old\batch_scripts\ 2>nul

REM SQLファイル
move *.sql old\misc\ 2>nul

REM PowerShellスクリプト
move *.ps1 old\batch_scripts\ 2>nul

echo その他のファイルを移動しました。
echo.

echo ========================================
echo 整理完了！
echo ========================================
echo.
echo 移動したファイル:
echo - 学習結果（PNG/TXT） → old\results\
echo - 学習データCSV → old\data\training_csv\
echo - 旧バッチファイル → old\batch_scripts\
echo - 旧モデル（34特徴量） → old\models_34features\
echo - 旧スクリプト → old\scripts\
echo - 古いドキュメント → old\docs_archive\
echo - その他 → old\misc\
echo.
echo 残されたファイル:
echo - 最新スクリプト（scripts/phase0-6）
echo - 最新ドキュメント（PHASE2_HIGHPERFORMANCE_PROGRESS.md等）
echo - 必須設定ファイル（requirements.txt, .gitignore, README.md）
echo.
echo 次のステップ:
echo 1. プロジェクト構造を確認: tree /F /A
echo 2. Git commit: git add . ^&^& git commit -m "chore: プロジェクト整理 - 旧ファイルをold/に移動"
echo 3. Phase 2実装開始: 工程2-1-B（学習データ収集）
echo.

pause
