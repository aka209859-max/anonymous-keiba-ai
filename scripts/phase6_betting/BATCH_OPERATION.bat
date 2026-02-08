@echo off
REM ==================================================
REM 地方競馬AI予想システム - 複数競馬場一括処理
REM Note & ブッカーズ用テキスト自動生成
REM ==================================================

setlocal enabledelayedexpansion

REM ============================================
REM 基本設定
REM ============================================
cd /d E:\anonymous-keiba-ai

REM ============================================
REM 引数チェック（日付のみ）
REM ============================================
if "%~1"=="" goto :SHOW_USAGE

set TARGET_DATE=%~1

echo ==================================================
echo 🏇 地方競馬AI予想 - 複数競馬場一括処理
echo ==================================================
echo.
echo 対象日: %TARGET_DATE%
echo.
echo ==================================================

REM ============================================
REM 日付フォーマット変換
REM ============================================
set DATE_SHORT=%TARGET_DATE:-=%

REM ============================================
REM Phase 5完了済み競馬場を自動検出
REM ============================================
echo.
echo 📊 Phase 5完了済み競馬場を検出中...
echo.

set KEIBA_CODES=
set ALL_CODES=30 35 36 42 43 44 45 46 47 48 50 51 54 55

for %%K in (%ALL_CODES%) do (
    if "%%K"=="30" set KNAME=門別
    if "%%K"=="35" set KNAME=盛岡
    if "%%K"=="36" set KNAME=水沢
    if "%%K"=="42" set KNAME=浦和
    if "%%K"=="43" set KNAME=船橋
    if "%%K"=="44" set KNAME=大井
    if "%%K"=="45" set KNAME=川崎
    if "%%K"=="46" set KNAME=金沢
    if "%%K"=="47" set KNAME=笠松
    if "%%K"=="48" set KNAME=名古屋
    if "%%K"=="50" set KNAME=園田
    if "%%K"=="51" set KNAME=姫路
    if "%%K"=="54" set KNAME=高知
    if "%%K"=="55" set KNAME=佐賀
    
    set CHECK_FILE=data\predictions\phase5\!KNAME!_%DATE_SHORT%_ensemble.csv
    
    if exist "!CHECK_FILE!" (
        echo [検出] !KNAME!競馬 (コード: %%K)
        set KEIBA_CODES=!KEIBA_CODES! %%K
    )
)

if "%KEIBA_CODES%"=="" (
    echo.
    echo [エラー] Phase 5完了済みの競馬場が見つかりませんでした
    echo.
    echo 確認事項:
    echo   - Phase 0-5 が実行されているか確認してください
    echo   - data\predictions\phase5\ フォルダを確認してください
    echo   - 対象日付が正しいか確認してください: %TARGET_DATE%
    echo.
    exit /b 1
)

echo.
echo ✅ 検出された競馬場コード:%KEIBA_CODES%
echo.

REM ============================================
REM 各競馬場を順次処理
REM ============================================
set SUCCESS_COUNT=0
set FAIL_COUNT=0

for %%K in (%KEIBA_CODES%) do (
    echo.
    echo --------------------------------------------------
    echo 競馬場コード %%K の処理を開始...
    echo --------------------------------------------------
    
    if "%%K"=="30" set KNAME=門別
    if "%%K"=="35" set KNAME=盛岡
    if "%%K"=="36" set KNAME=水沢
    if "%%K"=="42" set KNAME=浦和
    if "%%K"=="43" set KNAME=船橋
    if "%%K"=="44" set KNAME=大井
    if "%%K"=="45" set KNAME=川崎
    if "%%K"=="46" set KNAME=金沢
    if "%%K"=="47" set KNAME=笠松
    if "%%K"=="48" set KNAME=名古屋
    if "%%K"=="50" set KNAME=園田
    if "%%K"=="51" set KNAME=姫路
    if "%%K"=="54" set KNAME=高知
    if "%%K"=="55" set KNAME=佐賀
    
    echo [処理中] !KNAME!競馬の配信用テキスト生成...
    
    call scripts\phase6_betting\DAILY_OPERATION.bat %%K %TARGET_DATE%
    
    if errorlevel 1 (
        echo [失敗] !KNAME!競馬の処理に失敗しました
        set /a FAIL_COUNT+=1
    ) else (
        echo [成功] !KNAME!競馬の処理が完了しました
        set /a SUCCESS_COUNT+=1
    )
)

REM ============================================
REM 結果サマリー
REM ============================================
echo.
echo ==================================================
echo 📊 処理結果サマリー
echo ==================================================
echo.
echo ✅ 成功: %SUCCESS_COUNT% 競馬場
echo ❌ 失敗: %FAIL_COUNT% 競馬場
echo.
echo ==================================================

if %FAIL_COUNT% gtr 0 (
    echo.
    echo ⚠️  一部の競馬場で処理に失敗しました
    echo    上記のログを確認してください
    echo.
)

if %SUCCESS_COUNT% gtr 0 (
    echo.
    echo 📝 生成されたファイル（各競馬場別）:
    echo.
    echo    【Note用】
    for %%K in (%KEIBA_CODES%) do (
        if "%%K"=="30" set KNAME=門別
        if "%%K"=="35" set KNAME=盛岡
        if "%%K"=="36" set KNAME=水沢
        if "%%K"=="42" set KNAME=浦和
        if "%%K"=="43" set KNAME=船橋
        if "%%K"=="44" set KNAME=大井
        if "%%K"=="45" set KNAME=川崎
        if "%%K"=="46" set KNAME=金沢
        if "%%K"=="47" set KNAME=笠松
        if "%%K"=="48" set KNAME=名古屋
        if "%%K"=="50" set KNAME=園田
        if "%%K"=="51" set KNAME=姫路
        if "%%K"=="54" set KNAME=高知
        if "%%K"=="55" set KNAME=佐賀
        
        set CHECK_FILE=predictions\!KNAME!_%DATE_SHORT%_note.txt
        if exist "!CHECK_FILE!" (
            echo      - !KNAME!_%DATE_SHORT%_note.txt
        )
    )
    echo.
    echo    【ブッカーズ用】
    for %%K in (%KEIBA_CODES%) do (
        if "%%K"=="30" set KNAME=門別
        if "%%K"=="35" set KNAME=盛岡
        if "%%K"=="36" set KNAME=水沢
        if "%%K"=="42" set KNAME=浦和
        if "%%K"=="43" set KNAME=船橋
        if "%%K"=="44" set KNAME=大井
        if "%%K"=="45" set KNAME=川崎
        if "%%K"=="46" set KNAME=金沢
        if "%%K"=="47" set KNAME=笠松
        if "%%K"=="48" set KNAME=名古屋
        if "%%K"=="50" set KNAME=園田
        if "%%K"=="51" set KNAME=姫路
        if "%%K"=="54" set KNAME=高知
        if "%%K"=="55" set KNAME=佐賀
        
        set CHECK_FILE=predictions\!KNAME!_%DATE_SHORT%_bookers.txt
        if exist "!CHECK_FILE!" (
            echo      - !KNAME!_%DATE_SHORT%_bookers.txt
        )
    )
    echo.
    echo 📋 次のステップ:
    echo    1. predictions フォルダを開く
    echo    2. 各競馬場のファイルを確認
    echo    3. Note用とブッカーズ用をそれぞれ投稿
    echo.
    echo 🚀 確認用コマンド:
    echo    explorer predictions
    echo.
)

echo ==================================================
goto :EOF

REM ============================================
REM 使用方法表示
REM ============================================
:SHOW_USAGE
echo ==================================================
echo 🏇 地方競馬AI予想 - 複数競馬場一括処理
echo ==================================================
echo.
echo 使用方法:
echo   BATCH_OPERATION.bat [対象日付]
echo.
echo 日付フォーマット: YYYY-MM-DD
echo.
echo 機能:
echo   - Phase 5完了済みの競馬場を自動検出
echo   - 各競馬場のNote用・ブッカーズ用テキストを自動生成
echo   - data\predictions\phase5\{競馬場名}_{YYYYMMDD}_ensemble.csv
echo     の存在を確認して処理対象を決定
echo.
echo 使用例:
echo.
echo   REM 2026年2月8日の全競馬場を一括処理
echo   BATCH_OPERATION.bat 2026-02-08
echo.
echo   REM 2026年2月10日の全競馬場を一括処理
echo   BATCH_OPERATION.bat 2026-02-10
echo.
echo 前提条件:
echo   - Phase 0-5 が事前に実行されていること
echo   - ensemble.csv が生成されていること
echo.
echo ==================================================
exit /b 1
