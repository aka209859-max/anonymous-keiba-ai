@echo off
setlocal enabledelayedexpansion

echo ========================================
echo E:\JRAVAN データ年次完全性検証
echo ========================================
echo.

set OUTPUT=E:\jravan_completeness_report.txt

echo ======================================== > "%OUTPUT%"
echo JRA-VAN データ年次完全性検証レポート >> "%OUTPUT%"
echo 実行日時: %DATE% %TIME% >> "%OUTPUT%"
echo ======================================== >> "%OUTPUT%"
echo. >> "%OUTPUT%"

REM ========================================
REM 1. 年度別ファイル数カウント（1986-2025）
REM ========================================

echo [1/4] 年度別ファイル数確認中...
echo === 1. 年度別ファイル数分布 === >> "%OUTPUT%"
echo. >> "%OUTPUT%"

set TOTAL_FILES=0
set MISSING_YEARS=0

for /L %%y in (1986,1,2025) do (
    set YEAR_FILES=0
    
    REM RDATA フォルダ内の該当年ファイルをカウント
    for /f %%c in ('dir /s /b "E:\JRAVAN\*%%y*.txt" 2^>nul ^| find /c "\"') do set YEAR_FILES=%%c
    
    set /a TOTAL_FILES+=!YEAR_FILES!
    
    REM 判定基準: 年間 500 ファイル以上なら 完全、100-500 なら 部分的、100 未満なら 少量
    if !YEAR_FILES! GEQ 500 (
        echo %%y : !YEAR_FILES! : 完全 >> "%OUTPUT%"
    ) else if !YEAR_FILES! GEQ 100 (
        echo %%y : !YEAR_FILES! : 部分的 >> "%OUTPUT%"
    ) else if !YEAR_FILES! GEQ 1 (
        echo %%y : !YEAR_FILES! : 少量 >> "%OUTPUT%"
    ) else (
        echo %%y : 0 : なし >> "%OUTPUT%"
        set /a MISSING_YEARS+=1
    )
)

echo. >> "%OUTPUT%"
echo 総ファイル数: %TOTAL_FILES% >> "%OUTPUT%"
echo データなし年度: %MISSING_YEARS% 年 >> "%OUTPUT%"
echo. >> "%OUTPUT%"

REM ========================================
REM 2. 最古と最新のファイル日付確認
REM ========================================

echo [2/4] 最古・最新ファイル確認中...
echo === 2. データ期間の確定 === >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo 【最古のファイル（作成日時順）】 >> "%OUTPUT%"
for /f "tokens=*" %%f in ('dir /s /b /o:d "E:\JRAVAN\*.txt" 2^>nul') do (
    echo ファイル: %%~nxf >> "%OUTPUT%"
    dir "%%f" | find "/" >> "%OUTPUT%"
    goto :oldest_done
)
:oldest_done

echo. >> "%OUTPUT%"
echo 【最新のファイル（作成日時順）】 >> "%OUTPUT%"
for /f "tokens=*" %%f in ('dir /s /b /o:-d "E:\JRAVAN\*.txt" 2^>nul') do (
    echo ファイル: %%~nxf >> "%OUTPUT%"
    dir "%%f" | find "/" >> "%OUTPUT%"
    goto :newest_done
)
:newest_done

echo. >> "%OUTPUT%"

REM ========================================
REM 3. サブフォルダ別のファイル数
REM ========================================

echo [3/4] サブフォルダ別ファイル数確認中...
echo === 3. サブフォルダ別データ量 === >> "%OUTPUT%"
echo. >> "%OUTPUT%"

for /d %%d in (E:\JRAVAN\*) do (
    for /f %%c in ('dir /s /b "%%d\*.txt" 2^>nul ^| find /c "\"') do (
        echo %%~nxd : %%c >> "%OUTPUT%"
    )
)

echo. >> "%OUTPUT%"

REM ========================================
REM 4. 2025年12月データの存在確認（重要）
REM ========================================

echo [4/4] 2025年12月データ確認中...
echo === 4. 最新データ確認（2025年12月） === >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo 【2025年12月のファイル検索】 >> "%OUTPUT%"

REM パターン1: ファイル名に 202512 を含む
set DEC2025_COUNT=0
for /f %%c in ('dir /s /b "E:\JRAVAN\*202512*.txt" 2^>nul ^| find /c "\"') do set DEC2025_COUNT=%%c

echo パターン1 (*202512*.txt): %DEC2025_COUNT% 件 >> "%OUTPUT%"

REM パターン2: ファイル名に 2512 を含む（年省略形式）
set DEC2025_SHORT=0
for /f %%c in ('dir /s /b "E:\JRAVAN\*2512*.txt" 2^>nul ^| find /c "\"') do set DEC2025_SHORT=%%c

echo パターン2 (*2512*.txt): %DEC2025_SHORT% 件 >> "%OUTPUT%"

REM パターン3: 2025年全体
set YEAR2025_COUNT=0
for /f %%c in ('dir /s /b "E:\JRAVAN\*2025*.txt" 2^>nul ^| find /c "\"') do set YEAR2025_COUNT=%%c

echo パターン3 (*2025*.txt): %YEAR2025_COUNT% 件 >> "%OUTPUT%"

echo. >> "%OUTPUT%"

REM サンプルファイル名表示（最大5件）
echo 【2025年ファイルのサンプル（最大5件）】 >> "%OUTPUT%"
set SAMPLE_COUNT=0
for /f "tokens=*" %%f in ('dir /s /b "E:\JRAVAN\*2025*.txt" 2^>nul') do (
    if !SAMPLE_COUNT! LSS 5 (
        echo %%~nxf >> "%OUTPUT%"
        set /a SAMPLE_COUNT+=1
    )
)

echo. >> "%OUTPUT%"

REM ========================================
REM 5. 総合判定
REM ========================================

echo === 5. 総合判定 === >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo 【データ完全性スコア】 >> "%OUTPUT%"
echo. >> "%OUTPUT%"

REM 判定ロジック
set SCORE=0

REM 総ファイル数が 30,000 以上なら +30 点
if %TOTAL_FILES% GEQ 30000 set /a SCORE+=30

REM 欠損年度が 5 年以下なら +20 点
if %MISSING_YEARS% LEQ 5 set /a SCORE+=20

REM 2025 年データがあれば +50 点
if %YEAR2025_COUNT% GTR 0 set /a SCORE+=50

echo スコア: %SCORE% / 100 >> "%OUTPUT%"
echo. >> "%OUTPUT%"

if %SCORE% GEQ 80 (
    echo 判定: データは完全です >> "%OUTPUT%"
    echo 推奨アクション: TARGET で CSV エクスポートを実行 >> "%OUTPUT%"
) else if %SCORE% GEQ 50 (
    echo 判定: データは部分的です >> "%OUTPUT%"
    echo 推奨アクション: 欠損年度を確認し、必要なら追加取得 >> "%OUTPUT%"
) else (
    echo 判定: データが不十分です >> "%OUTPUT%"
    echo 推奨アクション: Phase 0 フル実行（約30時間） >> "%OUTPUT%"
)

echo. >> "%OUTPUT%"

REM ========================================
REM 6. 次のステップ
REM ========================================

echo === 6. 次のステップ === >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo 【オプション A: 既存データ活用】 >> "%OUTPUT%"
echo 条件: スコア 80点以上 >> "%OUTPUT%"
echo 手順: >> "%OUTPUT%"
echo   1. TARGET frontier JV を起動 >> "%OUTPUT%"
echo   2. レース検索（全期間） >> "%OUTPUT%"
echo   3. 開催成績 CSV 出力 >> "%OUTPUT%"
echo   4. Python で Parquet 変換 >> "%OUTPUT%"
echo 時間: 数時間 >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo 【オプション B: 部分追加取得】 >> "%OUTPUT%"
echo 条件: スコア 50-79点 >> "%OUTPUT%"
echo 手順: >> "%OUTPUT%"
echo   1. 欠損年度リストを確認 >> "%OUTPUT%"
echo   2. JV-Link で不足分のみ取得 >> "%OUTPUT%"
echo   3. TARGET で CSV 出力 >> "%OUTPUT%"
echo 時間: 数時間から1日 >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo 【オプション C: 完全再取得】 >> "%OUTPUT%"
echo 条件: スコア 50点未満 >> "%OUTPUT%"
echo 手順: >> "%OUTPUT%"
echo   1. JV-Link セットアップモード >> "%OUTPUT%"
echo   2. 全データダウンロード >> "%OUTPUT%"
echo 時間: 約30時間 >> "%OUTPUT%"
echo. >> "%OUTPUT%"

echo ========================================
echo 検証完了！
echo ========================================
echo.
echo レポートファイル: %OUTPUT%
echo.
notepad "%OUTPUT%"
