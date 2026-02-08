@echo off
REM ==================================================
REM 地方競馬AI予想システム - 毎日運用バッチ
REM Note & ブッカーズ用テキスト自動生成
REM ==================================================

setlocal enabledelayedexpansion

REM ============================================
REM 基本設定
REM ============================================
cd /d E:\anonymous-keiba-ai

REM ============================================
REM 引数チェック（競馬場コード と 日付）
REM ============================================
if "%~1"=="" goto :SHOW_USAGE
if "%~2"=="" goto :SHOW_USAGE

set KEIBA_CODE=%~1
set TARGET_DATE=%~2

REM ============================================
REM 競馬場名マッピング
REM ============================================
if "%KEIBA_CODE%"=="30" set KEIBA_NAME=門別
if "%KEIBA_CODE%"=="35" set KEIBA_NAME=盛岡
if "%KEIBA_CODE%"=="36" set KEIBA_NAME=水沢
if "%KEIBA_CODE%"=="42" set KEIBA_NAME=浦和
if "%KEIBA_CODE%"=="43" set KEIBA_NAME=船橋
if "%KEIBA_CODE%"=="44" set KEIBA_NAME=大井
if "%KEIBA_CODE%"=="45" set KEIBA_NAME=川崎
if "%KEIBA_CODE%"=="46" set KEIBA_NAME=金沢
if "%KEIBA_CODE%"=="47" set KEIBA_NAME=笠松
if "%KEIBA_CODE%"=="48" set KEIBA_NAME=名古屋
if "%KEIBA_CODE%"=="50" set KEIBA_NAME=園田
if "%KEIBA_CODE%"=="51" set KEIBA_NAME=姫路
if "%KEIBA_CODE%"=="54" set KEIBA_NAME=高知
if "%KEIBA_CODE%"=="55" set KEIBA_NAME=佐賀

if "%KEIBA_NAME%"=="" (
    echo [エラー] 無効な競馬場コード: %KEIBA_CODE%
    goto :SHOW_USAGE
)

REM ============================================
REM 日付フォーマット変換
REM ============================================
REM YYYY-MM-DD → YYYYMMDD
set DATE_SHORT=%TARGET_DATE:-=%

REM ============================================
REM ファイルパス設定
REM ============================================
set ENSEMBLE_CSV=data\predictions\phase5\%KEIBA_NAME%_%DATE_SHORT%_ensemble.csv
set NOTE_TXT=predictions\%KEIBA_NAME%_%DATE_SHORT%_note.txt
set BOOKERS_TXT=predictions\%KEIBA_NAME%_%DATE_SHORT%_bookers.txt

echo ==================================================
echo 🏇 地方競馬AI予想 - 配信用テキスト生成
echo ==================================================
echo.
echo 競馬場: %KEIBA_NAME% (コード: %KEIBA_CODE%)
echo 対象日: %TARGET_DATE%
echo.
echo 入力CSV: %ENSEMBLE_CSV%
echo 出力1  : %NOTE_TXT%
echo 出力2  : %BOOKERS_TXT%
echo.
echo ==================================================

REM ============================================
REM 入力ファイル存在確認
REM ============================================
if not exist "%ENSEMBLE_CSV%" (
    echo [エラー] 入力ファイルが見つかりません
    echo ファイル: %ENSEMBLE_CSV%
    echo.
    echo Phase 5 までの処理が完了しているか確認してください。
    exit /b 1
)

REM ============================================
REM Phase 6-1: Note用テキスト生成
REM ============================================
echo.
echo [Phase 6-1] Note用テキスト生成中...
python scripts\phase6_betting\generate_distribution_note.py "%ENSEMBLE_CSV%" "%NOTE_TXT%"

if errorlevel 1 (
    echo [エラー] Note用テキスト生成に失敗しました
    exit /b 1
)

echo [完了] Note用テキスト生成完了: %NOTE_TXT%
echo.

REM ============================================
REM Phase 6-2: ブッカーズ用テキスト生成
REM ============================================
echo [Phase 6-2] ブッカーズ用テキスト生成中...
python scripts\phase6_betting\generate_distribution_bookers.py "%ENSEMBLE_CSV%" "%BOOKERS_TXT%"

if errorlevel 1 (
    echo [エラー] ブッカーズ用テキスト生成に失敗しました
    exit /b 1
)

echo [完了] ブッカーズ用テキスト生成完了: %BOOKERS_TXT%
echo.

REM ============================================
REM 完了メッセージと次のステップ
REM ============================================
echo ==================================================
echo ✅ すべての処理が完了しました！
echo ==================================================
echo.
echo 📝 生成されたファイル:
echo   1. Note用    : %NOTE_TXT%
echo   2. ブッカーズ用: %BOOKERS_TXT%
echo.
echo 📋 次のステップ:
echo   1. 各ファイルをメモ帳で開いて内容を確認
echo   2. Note に投稿（コピー＆ペースト）
echo   3. ブッカーズに投稿（コピー＆ペースト）
echo.
echo 🚀 確認用コマンド:
echo   notepad "%NOTE_TXT%"
echo   notepad "%BOOKERS_TXT%"
echo.
echo ==================================================
goto :EOF

REM ============================================
REM 使用方法表示
REM ============================================
:SHOW_USAGE
echo ==================================================
echo 🏇 地方競馬AI予想 - 配信用テキスト生成
echo ==================================================
echo.
echo 使用方法:
echo   DAILY_OPERATION.bat [競馬場コード] [対象日付]
echo.
echo 競馬場コード一覧:
echo   30: 門別    35: 盛岡    36: 水沢    42: 浦和
echo   43: 船橋    44: 大井    45: 川崎    46: 金沢
echo   47: 笠松    48: 名古屋  50: 園田    51: 姫路
echo   54: 高知    55: 佐賀
echo.
echo 日付フォーマット: YYYY-MM-DD
echo.
echo 使用例:
echo   REM 佐賀競馬 2026年2月8日
echo   DAILY_OPERATION.bat 55 2026-02-08
echo.
echo   REM 大井競馬 2026年2月10日
echo   DAILY_OPERATION.bat 44 2026-02-10
echo.
echo   REM 川崎競馬 2026年2月10日
echo   DAILY_OPERATION.bat 45 2026-02-10
echo.
echo ==================================================
exit /b 1
