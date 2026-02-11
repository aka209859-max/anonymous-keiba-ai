@echo off
chcp 65001 >nul
REM ========================================================================
REM Phase 7 完全実行バッチ
REM 
REM 目的: 3つのモデルタイプ（Binary, Ranking, Regression）に対して
REM       Boruta特徴選択を実行します
REM
REM 実行内容:
REM   1. Binary分類用Boruta特徴選択
REM   2. Ranking予測用Boruta特徴選択
REM   3. Regression予測用Boruta特徴選択
REM
REM 必要な入力:
REM   - data/training/{venue}_2020-2025_with_time.csv
REM
REM 出力先:
REM   - data/features/selected/{venue}_selected_features.csv (Binary)
REM   - data/features/selected/{venue}_ranking_selected_features.csv (Ranking)
REM   - data/features/selected/{venue}_regression_selected_features.csv (Regression)
REM   - data/reports/phase7_feature_selection/ (各種レポート)
REM ========================================================================

echo ================================================================================
echo Phase 7 完全実行: Boruta特徴選択 (Binary + Ranking + Regression)
echo ================================================================================
echo.
echo 実行対象: 全14競馬場
echo 推定所要時間: 約2〜4時間（会場数・データ量により変動）
echo.

REM 会場リスト（14競馬場）
set VENUES=funabashi kawasaki ohi urawa hunabashi morioka mizusawa kasamatsu kanazawa sonoda himeji kochi saga arao

echo [確認] 以下の14会場でPhase 7を実行します:
echo   船橋 川崎 大井 浦和 盛岡 水沢 笠松 金沢 園田 姫路 高知 佐賀 荒尾
echo.
echo 各会場につき3つのモデル (Binary/Ranking/Regression) を処理します
echo 総処理数: 14会場 × 3モデル = 42回の特徴選択
echo.

pause

echo.
echo ================================================================================
echo Phase 7 実行開始: %date% %time%
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
    REM 1. Binary分類用Boruta特徴選択
    REM ----------------------------------------
    echo [1/3] Binary分類用Boruta特徴選択実行中...
    set /a total_count+=1
    
    python scripts\phase7_feature_selection\run_boruta_selection.py ^
        "!TRAINING_FILE!" ^
        --max-iter 100 ^
        --n-estimators 100
    
    if errorlevel 1 (
        echo [エラー] Binary分類用Boruta特徴選択に失敗しました
        set /a error_count+=1
    ) else (
        echo [成功] Binary分類用Boruta特徴選択完了
        set /a success_count+=1
    )
    
    echo.
    
    REM ----------------------------------------
    REM 2. Ranking予測用Boruta特徴選択
    REM ----------------------------------------
    echo [2/3] Ranking予測用Boruta特徴選択実行中...
    set /a total_count+=1
    
    python scripts\phase7_feature_selection\run_boruta_ranking.py ^
        "!TRAINING_FILE!" ^
        --max-iter 100 ^
        --n-estimators 100
    
    if errorlevel 1 (
        echo [エラー] Ranking予測用Boruta特徴選択に失敗しました
        set /a error_count+=1
    ) else (
        echo [成功] Ranking予測用Boruta特徴選択完了
        set /a success_count+=1
    )
    
    echo.
    
    REM ----------------------------------------
    REM 3. Regression予測用Boruta特徴選択
    REM ----------------------------------------
    echo [3/3] Regression予測用Boruta特徴選択実行中...
    set /a total_count+=1
    
    python scripts\phase7_feature_selection\run_boruta_regression.py ^
        "!TRAINING_FILE!" ^
        --max-iter 100 ^
        --n-estimators 100
    
    if errorlevel 1 (
        echo [エラー] Regression予測用Boruta特徴選択に失敗しました
        set /a error_count+=1
    ) else (
        echo [成功] Regression予測用Boruta特徴選択完了
        set /a success_count+=1
    )
    
    echo.
    echo [完了] 会場 %%V の3モデル処理完了
    
    :next_venue
)

echo.
echo ================================================================================
echo Phase 7 実行完了: %date% %time%
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
echo   RUN_PHASE8_COMPLETE.bat を実行してOptuna最適化を開始してください
echo.

pause
