# ============================================================================
# Phase 8 Regression 最適化 一括実行スクリプト
# ============================================================================
# 作成日: 2026-02-11
# 目的: 残り13会場のRegression最適化を一括実行
# 推定時間: 6〜13時間
# 注意: Phase 7 Regression 完了後に実行してください
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 8 Regression 一括実行開始" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 対象会場（船橋を除く13会場）
$venues = @(
    "monbetsu",   # 門別 (30)
    "morioka",    # 盛岡 (35)
    "mizusawa",   # 水沢 (36)
    "urawa",      # 浦和 (42)
    "ooi",        # 大井 (44)
    "kawasaki",   # 川崎 (45)
    "kanazawa",   # 金沢 (46)
    "kasamatsu",  # 笠松 (47)
    "nagoya",     # 名古屋 (48)
    "sonoda",     # 園田 (50)
    "himeji",     # 姫路 (51)
    "kochi",      # 高知 (54)
    "saga"        # 佐賀 (55)
)

$total = $venues.Count
$current = 0
$startTime = Get-Date

foreach ($venue in $venues) {
    $current++
    
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    Write-Host "[$current/$total] Phase 8 Regression: $venue" -ForegroundColor Green
    Write-Host "----------------------------------------" -ForegroundColor Yellow
    
    $inputFile = "data\training\${venue}_2020-2026_with_time_PHASE78.csv"
    $selectedFeatures = "data\features\selected\${venue}_regression_selected_features.csv"
    
    # ファイル存在確認
    if (-Not (Test-Path $inputFile)) {
        Write-Host "ERROR: 入力ファイルが見つかりません: $inputFile" -ForegroundColor Red
        continue
    }
    
    if (-Not (Test-Path $selectedFeatures)) {
        Write-Host "ERROR: 選択特徴量ファイルが見つかりません: $selectedFeatures" -ForegroundColor Red
        Write-Host "Phase 7 Regression を先に実行してください" -ForegroundColor Yellow
        continue
    }
    
    # Phase 8 Regression 実行
    $venueStartTime = Get-Date
    
    python scripts\phase8_auto_tuning\run_optuna_tuning_regression.py `
      $inputFile `
      --selected-features $selectedFeatures `
      --n-trials 100 `
      --timeout 7200 `
      --cv-folds 3
    
    if ($LASTEXITCODE -eq 0) {
        $venueEndTime = Get-Date
        $venueElapsed = $venueEndTime - $venueStartTime
        Write-Host "✅ $venue 完了 (所要時間: $($venueElapsed.ToString('hh\:mm\:ss')))" -ForegroundColor Green
    } else {
        Write-Host "❌ $venue 失敗 (終了コード: $LASTEXITCODE)" -ForegroundColor Red
    }
    
    Write-Host ""
}

$endTime = Get-Date
$totalElapsed = $endTime - $startTime

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phase 8 Regression 一括実行完了" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "総実行時間: $($totalElapsed.ToString('hh\:mm\:ss'))" -ForegroundColor Green
Write-Host ""

# 完了ファイル確認
Write-Host "出力ファイル確認:" -ForegroundColor Yellow
Get-ChildItem data\models\tuned\*_regression_best_params.csv | ForEach-Object {
    Write-Host "  ✅ $($_.Name)" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 全Phase完了！" -ForegroundColor Green
Write-Host "次のステップ: Phase 5 Ensemble 統合テストを実行してください" -ForegroundColor Cyan
