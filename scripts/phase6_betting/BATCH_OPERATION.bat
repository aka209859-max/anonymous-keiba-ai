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
REM 競馬場コードリスト（必要に応じて編集）
REM ============================================
REM 以下は一般的な開催パターン例です
REM 実際の開催スケジュールに合わせて調整してください

set KEIBA_CODES=

REM 水曜日: 大井・川崎
if /i "%~2"=="wed" set KEIBA_CODES=44 45

REM 木曜日: 船橋
if /i "%~2"=="thu" set KEIBA_CODES=43

REM 金曜日: 大井・川崎・船橋
if /i "%~2"=="fri" set KEIBA_CODES=44 45 43

REM 土曜日: 主要地方競馬場
if /i "%~2"=="sat" set KEIBA_CODES=30 35 36 42 43 44 45 46 47 48 50 51 54 55

REM 日曜日: 主要地方競馬場
if /i "%~2"=="sun" set KEIBA_CODES=30 35 36 42 43 44 45 46 47 48 50 51 54 55

REM 手動指定（カンマ区切り）
if /i "%~2"=="custom" set KEIBA_CODES=%~3

REM デフォルト: すべての競馬場をチェック
if "%KEIBA_CODES%"=="" set KEIBA_CODES=30 35 36 42 43 44 45 46 47 48 50 51 54 55

echo 処理対象競馬場コード: %KEIBA_CODES%
echo.

REM ============================================
REM 各競馬場を順次処理
REM ============================================
set SUCCESS_COUNT=0
set FAIL_COUNT=0
set SKIP_COUNT=0

for %%K in (%KEIBA_CODES%) do (
    echo.
    echo --------------------------------------------------
    echo 競馬場コード %%K の処理を開始...
    echo --------------------------------------------------
    
    REM ensemble.csv の存在チェック
    set DATE_SHORT=%TARGET_DATE:-=%
    
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
    
    set CHECK_FILE=data\predictions\phase5\!KNAME!_!DATE_SHORT!_ensemble.csv
    
    if exist "!CHECK_FILE!" (
        echo [OK] !KNAME!競馬のデータが見つかりました
        
        call scripts\phase6_betting\DAILY_OPERATION.bat %%K %TARGET_DATE%
        
        if errorlevel 1 (
            echo [失敗] !KNAME!競馬の処理に失敗しました
            set /a FAIL_COUNT+=1
        ) else (
            echo [成功] !KNAME!競馬の処理が完了しました
            set /a SUCCESS_COUNT+=1
        )
    ) else (
        echo [スキップ] !KNAME!競馬のデータが見つかりません: !CHECK_FILE!
        set /a SKIP_COUNT+=1
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
echo ⏭️  スキップ: %SKIP_COUNT% 競馬場
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
echo   BATCH_OPERATION.bat [対象日付] [曜日パターン/custom]
echo.
echo 日付フォーマット: YYYY-MM-DD
echo.
echo 曜日パターン:
echo   wed    : 水曜日パターン（大井・川崎）
echo   thu    : 木曜日パターン（船橋）
echo   fri    : 金曜日パターン（大井・川崎・船橋）
echo   sat    : 土曜日パターン（全競馬場）
echo   sun    : 日曜日パターン（全競馬場）
echo   custom : 手動指定（第3引数にコード列挙）
echo.
echo 使用例:
echo.
echo   REM パターン1: 2026年2月8日（土曜日）
echo   BATCH_OPERATION.bat 2026-02-08 sat
echo.
echo   REM パターン2: 2026年2月10日（水曜日）
echo   BATCH_OPERATION.bat 2026-02-10 wed
echo.
echo   REM パターン3: 手動指定（佐賀・大井・川崎のみ）
echo   BATCH_OPERATION.bat 2026-02-08 custom "55 44 45"
echo.
echo   REM パターン4: すべての競馬場（パターン指定なし）
echo   BATCH_OPERATION.bat 2026-02-08
echo.
echo ==================================================
exit /b 1
