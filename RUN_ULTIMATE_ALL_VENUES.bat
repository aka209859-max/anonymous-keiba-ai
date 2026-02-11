@echo off
chcp 65001 >nul
REM ========================================================================
REM 全競馬場 完全実装展開バッチ
REM 
REM 目的: 全14競馬場に対して、Phase 7 → Phase 8 → Phase 5統合の
REM       完全なパイプラインを実行します
REM
REM 実行フロー:
REM   Phase 7: Boruta特徴選択 (Binary/Ranking/Regression × 14会場)
REM   Phase 8: Optunaハイパーパラメータ最適化 (Binary/Ranking/Regression × 14会場)
REM   Phase 5: アンサンブル統合予測（テストデータがある会場のみ）
REM
REM 推定所要時間: 約12〜24時間（データ量・PC性能により変動）
REM ========================================================================

echo ================================================================================
echo 全競馬場 完全実装展開（究極のAIシステム）
echo ================================================================================
echo.
echo このバッチは全14競馬場に対して完全なパイプラインを実行します
echo.

REM 会場リスト（14競馬場）
set VENUES=funabashi kawasaki ohi urawa morioka mizusawa kasamatsu kanazawa sonoda himeji kochi saga arao
set VENUES_JP=船橋 川崎 大井 浦和 盛岡 水沢 笠松 金沢 園田 姫路 高知 佐賀 荒尾

echo [対象会場] 14競馬場
echo   %VENUES_JP%
echo.
echo [実行内容]
echo   Phase 7: 全会場 Boruta特徴選択 (14会場 × 3モデル = 42回)
echo   Phase 8: 全会場 Optuna最適化 (14会場 × 3モデル = 42回)
echo   Phase 5: 全会場 アンサンブル統合予測（テストデータがある場合）
echo.
echo [推定所要時間]
echo   Phase 7: 約3〜5時間
echo   Phase 8: 約8〜16時間
echo   Phase 5: 約30分〜1時間
echo   合計: 約12〜24時間
echo.
echo [注意事項]
echo   - 長時間実行されるため、PCがスリープしないよう設定してください
echo   - 途中でエラーが発生した会場はスキップされます
echo   - 実行ログは画面に表示されます
echo.

pause

echo.
echo ================================================================================
echo 全競馬場 完全実装展開開始
echo ================================================================================
echo 開始時刻: %date% %time%
echo.

REM ログファイル作成
set LOG_FILE=ULTIMATE_EXECUTION_LOG_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set LOG_FILE=%LOG_FILE: =0%
echo 実行ログ: %LOG_FILE%
echo.

REM カウンター初期化
set /a phase7_success=0
set /a phase7_error=0
set /a phase8_success=0
set /a phase8_error=0
set /a phase5_success=0
set /a phase5_skip=0

echo ================================================================================ >> "%LOG_FILE%"
echo 全競馬場 完全実装展開ログ >> "%LOG_FILE%"
echo 開始時刻: %date% %time% >> "%LOG_FILE%"
echo ================================================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM ========================================================================
REM Phase 7: Boruta特徴選択（全会場）
REM ========================================================================
echo.
echo ################################################################################
echo Phase 7: Boruta特徴選択（全14会場）
echo ################################################################################
echo.

for %%V in (%VENUES%) do (
    echo.
    echo ========================================
    echo Phase 7: 会場 %%V
    echo ========================================
    echo Phase 7: 会場 %%V >> "%LOG_FILE%"
    
    set TRAINING_FILE=data\training\%%V_2020-2025_with_time.csv
    if not exist "!TRAINING_FILE!" (
        echo [スキップ] 学習データが見つかりません: !TRAINING_FILE!
        echo [スキップ] 学習データが見つかりません: !TRAINING_FILE! >> "%LOG_FILE%"
        set /a phase7_error+=3
        goto :next_phase7
    )
    
    REM Binary特徴選択
    echo [Phase 7-1/3] Binary特徴選択中...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!TRAINING_FILE!" --max-iter 100 --n-estimators 100
    if errorlevel 1 (
        echo [エラー] Binary特徴選択失敗 >> "%LOG_FILE%"
        set /a phase7_error+=1
    ) else (
        set /a phase7_success+=1
    )
    
    REM Ranking特徴選択
    echo [Phase 7-2/3] Ranking特徴選択中...
    python scripts\phase7_feature_selection\run_boruta_ranking.py "!TRAINING_FILE!" --max-iter 100 --n-estimators 100
    if errorlevel 1 (
        echo [エラー] Ranking特徴選択失敗 >> "%LOG_FILE%"
        set /a phase7_error+=1
    ) else (
        set /a phase7_success+=1
    )
    
    REM Regression特徴選択
    echo [Phase 7-3/3] Regression特徴選択中...
    python scripts\phase7_feature_selection\run_boruta_regression.py "!TRAINING_FILE!" --max-iter 100 --n-estimators 100
    if errorlevel 1 (
        echo [エラー] Regression特徴選択失敗 >> "%LOG_FILE%"
        set /a phase7_error+=1
    ) else (
        set /a phase7_success+=1
    )
    
    echo [完了] 会場 %%V のPhase 7完了
    echo [完了] 会場 %%V のPhase 7完了 >> "%LOG_FILE%"
    
    :next_phase7
)

echo.
echo [Phase 7 統計] 成功: %phase7_success% / エラー: %phase7_error%
echo [Phase 7 統計] 成功: %phase7_success% / エラー: %phase7_error% >> "%LOG_FILE%"
echo.

pause

REM ========================================================================
REM Phase 8: Optunaハイパーパラメータ最適化（全会場）
REM ========================================================================
echo.
echo ################################################################################
echo Phase 8: Optunaハイパーパラメータ最適化（全14会場）
echo ################################################################################
echo.

for %%V in (%VENUES%) do (
    echo.
    echo ========================================
    echo Phase 8: 会場 %%V
    echo ========================================
    echo Phase 8: 会場 %%V >> "%LOG_FILE%"
    
    set TRAINING_FILE=data\training\%%V_2020-2025_with_time.csv
    if not exist "!TRAINING_FILE!" (
        echo [スキップ] 学習データが見つかりません: !TRAINING_FILE!
        echo [スキップ] 学習データが見つかりません: !TRAINING_FILE! >> "%LOG_FILE%"
        set /a phase8_error+=3
        goto :next_phase8
    )
    
    REM Binary最適化
    echo [Phase 8-1/3] Binary最適化中...
    set BINARY_FEATURES=data\features\selected\%%V_selected_features.csv
    if exist "!BINARY_FEATURES!" (
        python scripts\phase8_auto_tuning\run_optuna_tuning.py "!TRAINING_FILE!" --selected-features "!BINARY_FEATURES!" --n-trials 100 --timeout 7200 --cv-folds 3
    ) else (
        python scripts\phase8_auto_tuning\run_optuna_tuning.py "!TRAINING_FILE!" --n-trials 100 --timeout 7200 --cv-folds 3
    )
    if errorlevel 1 (
        echo [エラー] Binary最適化失敗 >> "%LOG_FILE%"
        set /a phase8_error+=1
    ) else (
        set /a phase8_success+=1
    )
    
    REM Ranking最適化
    echo [Phase 8-2/3] Ranking最適化中...
    set RANKING_FEATURES=data\features\selected\%%V_ranking_selected_features.csv
    if exist "!RANKING_FEATURES!" (
        python scripts\phase8_auto_tuning\run_optuna_tuning_ranking.py "!TRAINING_FILE!" --selected-features "!RANKING_FEATURES!" --n-trials 100 --timeout 7200 --cv-folds 3
    ) else (
        python scripts\phase8_auto_tuning\run_optuna_tuning_ranking.py "!TRAINING_FILE!" --n-trials 100 --timeout 7200 --cv-folds 3
    )
    if errorlevel 1 (
        echo [エラー] Ranking最適化失敗 >> "%LOG_FILE%"
        set /a phase8_error+=1
    ) else (
        set /a phase8_success+=1
    )
    
    REM Regression最適化
    echo [Phase 8-3/3] Regression最適化中...
    set REGRESSION_FEATURES=data\features\selected\%%V_regression_selected_features.csv
    if exist "!REGRESSION_FEATURES!" (
        python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py "!TRAINING_FILE!" --selected-features "!REGRESSION_FEATURES!" --n-trials 100 --timeout 7200 --cv-folds 3
    ) else (
        python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py "!TRAINING_FILE!" --n-trials 100 --timeout 7200 --cv-folds 3
    )
    if errorlevel 1 (
        echo [エラー] Regression最適化失敗 >> "%LOG_FILE%"
        set /a phase8_error+=1
    ) else (
        set /a phase8_success+=1
    )
    
    echo [完了] 会場 %%V のPhase 8完了
    echo [完了] 会場 %%V のPhase 8完了 >> "%LOG_FILE%"
    
    :next_phase8
)

echo.
echo [Phase 8 統計] 成功: %phase8_success% / エラー: %phase8_error%
echo [Phase 8 統計] 成功: %phase8_success% / エラー: %phase8_error% >> "%LOG_FILE%"
echo.

pause

REM ========================================================================
REM Phase 5: アンサンブル統合予測（テストデータがある会場のみ）
REM ========================================================================
echo.
echo ################################################################################
echo Phase 5: アンサンブル統合予測（テストデータがある会場）
echo ################################################################################
echo.

for %%V in (%VENUES%) do (
    echo.
    echo ========================================
    echo Phase 5: 会場 %%V
    echo ========================================
    
    set TEST_FILE=test_data\%%V_test.csv
    if exist "!TEST_FILE!" (
        echo [Phase 5] アンサンブル統合予測実行中...
        echo [Phase 5] 会場 %%V >> "%LOG_FILE%"
        
        python scripts\phase5_ensemble\ensemble_optimized.py %%V "!TEST_FILE!" --output-dir "data\predictions\phase5_optimized"
        
        if errorlevel 1 (
            echo [エラー] Phase 5失敗 >> "%LOG_FILE%"
        ) else (
            echo [成功] Phase 5完了 >> "%LOG_FILE%"
            set /a phase5_success+=1
        )
    ) else (
        echo [スキップ] テストデータなし
        echo [スキップ] テストデータなし >> "%LOG_FILE%"
        set /a phase5_skip+=1
    )
)

echo.
echo [Phase 5 統計] 成功: %phase5_success% / スキップ: %phase5_skip%
echo [Phase 5 統計] 成功: %phase5_success% / スキップ: %phase5_skip% >> "%LOG_FILE%"
echo.

REM ========================================================================
REM 最終サマリー
REM ========================================================================
echo.
echo ================================================================================
echo 全競馬場 完全実装展開完了
echo ================================================================================
echo 終了時刻: %date% %time%
echo 終了時刻: %date% %time% >> "%LOG_FILE%"
echo.
echo [実行統計]
echo   Phase 7 (Boruta特徴選択)
echo     - 成功: %phase7_success% / エラー: %phase7_error%
echo   Phase 8 (Optuna最適化)
echo     - 成功: %phase8_success% / エラー: %phase8_error%
echo   Phase 5 (アンサンブル統合)
echo     - 成功: %phase5_success% / スキップ: %phase5_skip%
echo.
echo [実行統計] >> "%LOG_FILE%"
echo   Phase 7 成功: %phase7_success% / エラー: %phase7_error% >> "%LOG_FILE%"
echo   Phase 8 成功: %phase8_success% / エラー: %phase8_error% >> "%LOG_FILE%"
echo   Phase 5 成功: %phase5_success% / スキップ: %phase5_skip% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo [生成ファイル]
echo.
echo Phase 7 特徴選択結果:
dir /b data\features\selected\*_selected_features.csv 2>nul | find /c /v ""
echo.
echo Phase 8 最適化モデル:
dir /b data\models\tuned\*_tuned_model.txt 2>nul | find /c /v ""
echo.
echo Phase 5 予測結果:
dir /b data\predictions\phase5_optimized\*_ensemble_optimized.csv 2>nul | find /c /v ""
echo.
echo 詳細ログ: %LOG_FILE%
echo.
echo ================================================================================
echo 🎉 究極の競馬AIシステム構築完了！
echo ================================================================================
echo.
echo これで全14会場に対して最適化されたAIシステムが完成しました
echo 各会場のモデルを使って高精度な予測が可能です
echo.

pause
