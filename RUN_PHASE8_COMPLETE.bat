@echo off
chcp 65001 >nul
REM ========================================================================
REM Phase 8 完全実行バッチ
REM 
REM 目的: 3つのモデルタイプ（Binary, Ranking, Regression）に対して
REM       Optunaハイパーパラメータ最適化を実行します
REM
REM 実行内容:
REM   1. Binary分類モデル最適化（AUC最大化）
REM   2. Rankingモデル最適化（NDCG@5最大化）
REM   3. Regressionモデル最適化（RMSE最小化）
REM
REM 必要な入力:
REM   - data/training/{venue}_2020-2025_with_time.csv
REM   - data/features/selected/{venue}_selected_features.csv (Binary)
REM   - data/features/selected/{venue}_ranking_selected_features.csv (Ranking)
REM   - data/features/selected/{venue}_regression_selected_features.csv (Regression)
REM
REM 出力先:
REM   - data/models/tuned/{venue}_tuned_model.txt (Binary)
REM   - data/models/tuned/{venue}_ranking_tuned_model.txt (Ranking)
REM   - data/models/tuned/{venue}_regression_tuned_model.txt (Regression)
REM   - data/models/tuned/{venue}_*_best_params.csv (各種パラメータ)
REM   - data/models/tuned/{venue}_*_tuning_history.png (最適化履歴)
REM ========================================================================

echo ================================================================================
echo Phase 8 完全実行: Optunaハイパーパラメータ最適化 (Binary + Ranking + Regression)
echo ================================================================================
echo.
echo 実行対象: 全14競馬場
echo 推定所要時間: 約4〜8時間（会場数・データ量・試行回数により変動）
echo.

REM 会場リスト（14競馬場）
set VENUES=funabashi kawasaki ohi urawa hunabashi morioka mizusawa kasamatsu kanazawa sonoda himeji kochi saga arao

echo [確認] 以下の14会場でPhase 8を実行します:
echo   船橋 川崎 大井 浦和 盛岡 水沢 笠松 金沢 園田 姫路 高知 佐賀 荒尾
echo.
echo 各会場につき3つのモデル (Binary/Ranking/Regression) を最適化します
echo 総処理数: 14会場 × 3モデル = 42回のOptuna最適化
echo.
echo [最適化設定]
echo   - 試行回数: 100回/モデル
echo   - タイムアウト: 2時間/モデル
echo   - Cross-Validation: 3-fold (Binary/Regression), 3-GroupFold (Ranking)
echo.

pause

echo.
echo ================================================================================
echo Phase 8 実行開始: %date% %time%
echo ================================================================================
echo.

REM カウンター初期化
set /a total_count=0
set /a success_count=0
set /a error_count=0

REM 各会場に対してループ実行
for %%V in (%VENUES%) do (
    echo.
    echo ========================================
    echo 会場: %%V
    echo ========================================
    
    REM 学習データファイルの存在確認
    set TRAINING_FILE=data\training\%%V_2020-2025_with_time.csv
    if not exist "!TRAINING_FILE!" (
        echo [警告] 学習データが見つかりません: !TRAINING_FILE!
        echo [スキップ] 会場 %%V をスキップします
        set /a error_count+=3
        goto :next_venue
    )
    
    echo [OK] 学習データ確認: !TRAINING_FILE!
    echo.
    
    REM ----------------------------------------
    REM 1. Binary分類モデル最適化
    REM ----------------------------------------
    echo [1/3] Binary分類モデル最適化実行中...
    set /a total_count+=1
    
    set BINARY_FEATURES=data\features\selected\%%V_selected_features.csv
    if exist "!BINARY_FEATURES!" (
        python scripts\phase8_auto_tuning\run_optuna_tuning.py ^
            "!TRAINING_FILE!" ^
            --selected-features "!BINARY_FEATURES!" ^
            --n-trials 100 ^
            --timeout 7200 ^
            --cv-folds 3
    ) else (
        echo [警告] Binary用特徴量ファイルが見つかりません: !BINARY_FEATURES!
        python scripts\phase8_auto_tuning\run_optuna_tuning.py ^
            "!TRAINING_FILE!" ^
            --n-trials 100 ^
            --timeout 7200 ^
            --cv-folds 3
    )
    
    if errorlevel 1 (
        echo [エラー] Binary分類モデル最適化に失敗しました
        set /a error_count+=1
    ) else (
        echo [成功] Binary分類モデル最適化完了
        set /a success_count+=1
    )
    
    echo.
    
    REM ----------------------------------------
    REM 2. Rankingモデル最適化
    REM ----------------------------------------
    echo [2/3] Rankingモデル最適化実行中...
    set /a total_count+=1
    
    set RANKING_FEATURES=data\features\selected\%%V_ranking_selected_features.csv
    if exist "!RANKING_FEATURES!" (
        python scripts\phase8_auto_tuning\run_optuna_tuning_ranking.py ^
            "!TRAINING_FILE!" ^
            --selected-features "!RANKING_FEATURES!" ^
            --n-trials 100 ^
            --timeout 7200 ^
            --cv-folds 3
    ) else (
        echo [警告] Ranking用特徴量ファイルが見つかりません: !RANKING_FEATURES!
        python scripts\phase8_auto_tuning\run_optuna_tuning_ranking.py ^
            "!TRAINING_FILE!" ^
            --n-trials 100 ^
            --timeout 7200 ^
            --cv-folds 3
    )
    
    if errorlevel 1 (
        echo [エラー] Rankingモデル最適化に失敗しました
        set /a error_count+=1
    ) else (
        echo [成功] Rankingモデル最適化完了
        set /a success_count+=1
    )
    
    echo.
    
    REM ----------------------------------------
    REM 3. Regressionモデル最適化
    REM ----------------------------------------
    echo [3/3] Regressionモデル最適化実行中...
    set /a total_count+=1
    
    set REGRESSION_FEATURES=data\features\selected\%%V_regression_selected_features.csv
    if exist "!REGRESSION_FEATURES!" (
        python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py ^
            "!TRAINING_FILE!" ^
            --selected-features "!REGRESSION_FEATURES!" ^
            --n-trials 100 ^
            --timeout 7200 ^
            --cv-folds 3
    ) else (
        echo [警告] Regression用特徴量ファイルが見つかりません: !REGRESSION_FEATURES!
        python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py ^
            "!TRAINING_FILE!" ^
            --n-trials 100 ^
            --timeout 7200 ^
            --cv-folds 3
    )
    
    if errorlevel 1 (
        echo [エラー] Regressionモデル最適化に失敗しました
        set /a error_count+=1
    ) else (
        echo [成功] Regressionモデル最適化完了
        set /a success_count+=1
    )
    
    echo.
    echo [完了] 会場 %%V の3モデル最適化完了
    
    :next_venue
)

echo.
echo ================================================================================
echo Phase 8 実行完了: %date% %time%
echo ================================================================================
echo.
echo [実行統計]
echo   - 総処理数: %total_count%
echo   - 成功: %success_count%
echo   - 失敗: %error_count%
echo.

if %error_count% gtr 0 (
    echo [注意] %error_count%件のエラーが発生しました
    echo 詳細はログを確認してください
) else (
    echo [完了] 全ての処理が正常に完了しました！
)

echo.
echo [次のステップ]
echo   RUN_ULTIMATE_FUNABASHI.bat で船橋会場のテストを実行してください
echo   または RUN_ULTIMATE_ALL_VENUES.bat で全会場に展開してください
echo.

pause
