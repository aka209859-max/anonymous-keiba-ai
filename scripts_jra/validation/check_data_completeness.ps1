# ========================================
# JRA-VAN & JRDB データ検証スクリプト (PowerShell版)
# ========================================
# 目的: Eドライブのデータが公式仕様を満たしているか詳細確認
# 実行方法: PowerShell でこのスクリプトを実行
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JRA-VAN / JRDB データ検証スクリプト" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 出力ファイル
$OutputFile = Join-Path $PSScriptRoot "data_validation_report_detailed.txt"
Write-Host "検証結果を $OutputFile に出力します..." -ForegroundColor Yellow
Write-Host ""

# ========================================
# 1. JRA-VAN データ検証
# ========================================

Write-Host "[1/9] JRA-VAN ディレクトリ確認中..." -ForegroundColor Green

$Report = @"
========================================
JRA-VAN / JRDB データ検証レポート (詳細版)
実行日時: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
========================================

"@

$JravanBase = "E:\jra-keiba-data\jravan\raw"

$Report += @"
=== 1. JRA-VAN データ構造 ===

"@

if (Test-Path $JravanBase) {
    $Report += "✓ $JravanBase が存在します`n`n"
    
    # ディレクトリ数カウント
    $DirCount = (Get-ChildItem -Path $JravanBase -Recurse -Directory).Count
    $Report += "  サブディレクトリ数: $DirCount`n"
    
    # ファイル数カウント
    $FileCount = (Get-ChildItem -Path $JravanBase -Recurse -File).Count
    $Report += "  総ファイル数: $FileCount`n"
    $Report += "  （推奨: 30,000-50,000 ファイル）`n`n"
    
} else {
    $Report += "✗ $JravanBase が存在しません`n"
    $Report += "  推奨パス: E:\jra-keiba-data\jravan\raw\`n`n"
}

# ========================================
# 2. JRA-VAN レコードタイプ別詳細
# ========================================

Write-Host "[2/9] JRA-VAN レコードタイプ確認中..." -ForegroundColor Green

$Report += @"
=== 2. JRA-VAN レコードタイプ別ファイル数 ===

"@

$RecordTypes = @{
    "RA" = "レース詳細"
    "SE" = "競走馬詳細"
    "HR" = "競走成績"
    "H1" = "払戻金（単勝複勝）"
    "H2" = "払戻金（枠連）"
    "H3" = "払戻金（馬連）"
    "H4" = "払戻金（馬単）"
    "H5" = "払戻金（ワイド）"
    "H6" = "払戻金（3連単）"
    "O1" = "オッズ（単勝）"
    "O2" = "オッズ（複勝）"
    "O3" = "オッズ（枠連）"
    "O4" = "オッズ（馬連）"
    "O5" = "オッズ（馬単）"
    "O6" = "オッズ（3連単）"
    "WF" = "調教"
    "BLOD" = "血統"
}

if (Test-Path $JravanBase) {
    foreach ($Type in $RecordTypes.Keys | Sort-Object) {
        $Files = Get-ChildItem -Path $JravanBase -Recurse -Filter "*$Type*.txt" -File -ErrorAction SilentlyContinue
        $Count = $Files.Count
        $Description = $RecordTypes[$Type]
        
        if ($Count -gt 0) {
            $TotalSize = ($Files | Measure-Object -Property Length -Sum).Sum / 1MB
            $Report += "  $Type ($Description): $Count ファイル (合計 $([math]::Round($TotalSize, 2)) MB)`n"
        } else {
            $Report += "  $Type ($Description): 0 ファイル ⚠️`n"
        }
    }
    $Report += "`n"
}

# ========================================
# 3. JRA-VAN 年度別ファイル分布
# ========================================

Write-Host "[3/9] JRA-VAN 年度別分布確認中..." -ForegroundColor Green

$Report += @"
=== 3. JRA-VAN 年度別ファイル分布 ===

"@

if (Test-Path $JravanBase) {
    $YearDirs = Get-ChildItem -Path $JravanBase -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^\d{4}$' }
    
    if ($YearDirs) {
        foreach ($YearDir in $YearDirs | Sort-Object Name) {
            $YearFiles = (Get-ChildItem -Path $YearDir.FullName -Recurse -File).Count
            $YearSize = (Get-ChildItem -Path $YearDir.FullName -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
            $Report += "  $($YearDir.Name): $YearFiles ファイル ($([math]::Round($YearSize, 2)) GB)`n"
        }
        $Report += "`n"
    } else {
        $Report += "  年度別ディレクトリが見つかりません`n`n"
    }
}

# ========================================
# 4. JRA-VAN 総データサイズ
# ========================================

Write-Host "[4/9] JRA-VAN データサイズ確認中..." -ForegroundColor Green

$Report += @"
=== 4. JRA-VAN 総データサイズ ===

"@

if (Test-Path $JravanBase) {
    $TotalSize = (Get-ChildItem -Path $JravanBase -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
    $Report += "  総データサイズ: $([math]::Round($TotalSize, 2)) GB`n"
    $Report += "  （推奨: 20-50 GB）`n"
    
    if ($TotalSize -lt 20) {
        $Report += "  ⚠️ データ量が少ない可能性があります`n"
    } elseif ($TotalSize -gt 50) {
        $Report += "  ℹ️ 時系列オッズ等が含まれている可能性があります`n"
    } else {
        $Report += "  ✓ データ量は適切です`n"
    }
    $Report += "`n"
}

# ========================================
# 5. JRDB データ検証
# ========================================

Write-Host "[5/9] JRDB ディレクトリ確認中..." -ForegroundColor Green

$Report += @"
=== 5. JRDB データ構造 ===

"@

$JrdbRaw = "E:\jrdb_data\raw"
$JrdbLzh = "E:\jrdb_data\lzh"

if (Test-Path $JrdbRaw) {
    $Report += "✓ $JrdbRaw が存在します`n"
    
    $FileCount = (Get-ChildItem -Path $JrdbRaw -Recurse -File).Count
    $Report += "  総ファイル数: $FileCount`n"
    $Report += "  （推奨: 40,000-60,000 ファイル）`n`n"
} else {
    $Report += "✗ $JrdbRaw が存在しません`n`n"
}

if (Test-Path $JrdbLzh) {
    $LzhCount = (Get-ChildItem -Path $JrdbLzh -Filter "*.lzh" -File).Count
    $Report += "✓ $JrdbLzh が存在します`n"
    $Report += "  LZHファイル数: $LzhCount`n`n"
} else {
    $Report += "✗ $JrdbLzh が存在しません`n`n"
}

# ========================================
# 6. JRDB ファイル種別詳細
# ========================================

Write-Host "[6/9] JRDB ファイル種別確認中..." -ForegroundColor Green

$Report += @"
=== 6. JRDB ファイル種別別ファイル数 ===

"@

$JrdbFileTypes = @{
    "SED" = "成績データ（IDM・指数）"
    "KYI" = "騎手・調教師データ"
    "BAC" = "馬場データ"
    "CYB" = "前日情報"
    "CHA" = "調教データ"
    "SKB" = "成績拡張データ（外厩）"
    "TYB" = "当日情報"
    "UKC" = "馬基本データ"
}

if (Test-Path $JrdbRaw) {
    foreach ($Type in $JrdbFileTypes.Keys | Sort-Object) {
        $Files = Get-ChildItem -Path $JrdbRaw -Recurse -Filter "$Type*.txt" -File -ErrorAction SilentlyContinue
        $Count = $Files.Count
        $Description = $JrdbFileTypes[$Type]
        
        if ($Count -gt 0) {
            $TotalSize = ($Files | Measure-Object -Property Length -Sum).Sum / 1MB
            $Report += "  $Type ($Description): $Count ファイル (合計 $([math]::Round($TotalSize, 2)) MB)`n"
        } else {
            $Report += "  $Type ($Description): 0 ファイル ⚠️`n"
        }
    }
    $Report += "`n"
}

# ========================================
# 7. JRDB 総データサイズ
# ========================================

Write-Host "[7/9] JRDB データサイズ確認中..." -ForegroundColor Green

$Report += @"
=== 7. JRDB 総データサイズ ===

"@

if (Test-Path $JrdbRaw) {
    $TotalSize = (Get-ChildItem -Path $JrdbRaw -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
    $Report += "  総データサイズ: $([math]::Round($TotalSize, 2)) GB`n"
    $Report += "  （推奨: 10-30 GB）`n"
    
    if ($TotalSize -lt 10) {
        $Report += "  ⚠️ データ量が少ない可能性があります`n"
    } else {
        $Report += "  ✓ データ量は適切です`n"
    }
    $Report += "`n"
}

# ========================================
# 8. TARGET frontier JV データベース検索
# ========================================

Write-Host "[8/9] TARGET frontier JV データベース検索中..." -ForegroundColor Green

$Report += @"
=== 8. TARGET frontier JV データベース検索 ===

"@

$TargetPaths = @(
    "C:\TARGET",
    "C:\Program Files\TARGET",
    "C:\Program Files (x86)\TARGET",
    "$env:USERPROFILE\Documents\TARGET",
    "$env:APPDATA\TARGET",
    "$env:LOCALAPPDATA\TARGET"
)

$FoundDatabases = @()

foreach ($Path in $TargetPaths) {
    if (Test-Path $Path) {
        $Report += "✓ $Path が存在します`n"
        
        # データベースファイル検索
        $DbFiles = Get-ChildItem -Path $Path -Recurse -Include "*.db", "*.sqlite", "*.sqlite3", "*.mdb" -File -ErrorAction SilentlyContinue
        
        if ($DbFiles) {
            foreach ($DbFile in $DbFiles) {
                $Size = $DbFile.Length / 1MB
                $Report += "  📁 $($DbFile.FullName) ($([math]::Round($Size, 2)) MB)`n"
                $FoundDatabases += $DbFile.FullName
            }
        }
    }
}

if ($FoundDatabases.Count -eq 0) {
    $Report += "`n⚠️ TARGET frontier JV のデータベースファイルが見つかりませんでした`n"
} else {
    $Report += "`n✓ $($FoundDatabases.Count) 個のデータベースファイルが見つかりました`n"
}

$Report += "`n"

# ========================================
# 9. 統合サマリー
# ========================================

Write-Host "[9/9] 統合サマリー作成中..." -ForegroundColor Green

$Report += @"
=== 9. 統合サマリー ===

【JRA-VAN データ状況】
"@

if (Test-Path $JravanBase) {
    $JravanTotalFiles = (Get-ChildItem -Path $JravanBase -Recurse -File).Count
    $JravanTotalSize = (Get-ChildItem -Path $JravanBase -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
    
    $Report += @"
  ✓ データあり
  ファイル数: $JravanTotalFiles
  データサイズ: $([math]::Round($JravanTotalSize, 2)) GB
  
  判定: 
"@
    
    if ($JravanTotalFiles -ge 30000 -and $JravanTotalSize -ge 20) {
        $Report += "✅ 15年分のデータが揃っている可能性が高い`n"
    } elseif ($JravanTotalFiles -ge 10000) {
        $Report += "⚠️ 一部のデータのみ（5-10年程度の可能性）`n"
    } else {
        $Report += "❌ データが不足しています`n"
    }
} else {
    $Report += "  ✗ データなし`n"
}

$Report += @"

【JRDB データ状況】
"@

if (Test-Path $JrdbRaw) {
    $JrdbTotalFiles = (Get-ChildItem -Path $JrdbRaw -Recurse -File).Count
    $JrdbTotalSize = (Get-ChildItem -Path $JrdbRaw -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
    
    $Report += @"
  ✓ データあり
  ファイル数: $JrdbTotalFiles
  データサイズ: $([math]::Round($JrdbTotalSize, 2)) GB
  
  判定: 
"@
    
    if ($JrdbTotalFiles -ge 40000 -and $JrdbTotalSize -ge 10) {
        $Report += "✅ 15年分のデータが揃っている可能性が高い`n"
    } elseif ($JrdbTotalFiles -ge 15000) {
        $Report += "⚠️ 一部のデータのみ（5-10年程度の可能性）`n"
    } else {
        $Report += "❌ データが不足しています`n"
    }
} else {
    $Report += "  ✗ データなし`n"
}

$Report += @"

【TARGET frontier JV】
"@

if ($FoundDatabases.Count -gt 0) {
    $Report += @"
  ✓ データベースファイル検出
  ファイル数: $($FoundDatabases.Count)
  
  次のステップ:
  1. DB Browser for SQLite でスキーマ確認
  2. テーブル構造解析
  3. Python で読み込みテスト
"@
} else {
    $Report += @"
  ✗ データベースファイル未検出
  
  確認事項:
  - TARGET frontier JV がインストールされているか
  - データベースファイルのカスタムパスを使用していないか
"@
}

$Report += "`n`n"

$Report += @"
========================================
検証完了
========================================
実行日時: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

"@

# レポート出力
$Report | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "検証完了！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "レポートファイル: $OutputFile" -ForegroundColor Yellow
Write-Host ""
Write-Host "レポートを開きますか? (Y/N)" -ForegroundColor Yellow
$OpenReport = Read-Host

if ($OpenReport -eq "Y" -or $OpenReport -eq "y") {
    notepad $OutputFile
}

Write-Host ""
Write-Host "終了するには何かキーを押してください..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
