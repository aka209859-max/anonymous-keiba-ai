@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================
REM Phase 10: 日次予測システム
REM Phase 8最適化モデルを使った予測実行
REM ========================================

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if "%~1"=="" (
    echo Usage: RUN_PHASE10_DAILY.bat [KEIBAJO_CODE] [DATE]
    echo Example: RUN_PHASE10_DAILY.bat 44 2026-02-11
    echo.
    echo 競馬場コード:
    echo   30: 門別   35: 盛岡   36: 水沢   42: 浦和
    echo   43: 船橋   44: 大井   45: 川崎   46: 金沢
    echo   47: 笠松   48: 名古屋 50: 園田   51: 姫路
    echo   54: 高知   55: 佐賀
    exit /b 1
)

if "%~2"=="" (
    echo Usage: RUN_PHASE10_DAILY.bat [KEIBAJO_CODE] [DATE]
    echo Example: RUN_PHASE10_DAILY.bat 44 2026-02-11
    exit /b 1
)

set KEIBAJO_CODE=%~1
set TARGET_DATE=%~2

REM 競馬場名の設定
if "%KEIBAJO_CODE%"=="30" set KEIBAJO_NAME=門別
if "%KEIBAJO_CODE%"=="35" set KEIBAJO_NAME=盛岡
if "%KEIBAJO_CODE%"=="36" set KEIBAJO_NAME=水沢
if "%KEIBAJO_CODE%"=="42" set KEIBAJO_NAME=浦和
if "%KEIBAJO_CODE%"=="43" set KEIBAJO_NAME=船橋
if "%KEIBAJO_CODE%"=="44" set KEIBAJO_NAME=大井
if "%KEIBAJO_CODE%"=="45" set KEIBAJO_NAME=川崎
if "%KEIBAJO_CODE%"=="46" set KEIBAJO_NAME=金沢
if "%KEIBAJO_CODE%"=="47" set KEIBAJO_NAME=笠松
if "%KEIBAJO_CODE%"=="48" set KEIBAJO_NAME=名古屋
if "%KEIBAJO_CODE%"=="50" set KEIBAJO_NAME=園田
if "%KEIBAJO_CODE%"=="51" set KEIBAJO_NAME=姫路
if "%KEIBAJO_CODE%"=="54" set KEIBAJO_NAME=高知
if "%KEIBAJO_CODE%"=="55" set KEIBAJO_NAME=佐賀

echo ========================================
echo Phase 10: 日次予測システム
echo ========================================
echo 競馬場: %KEIBAJO_NAME% (コード: %KEIBAJO_CODE%)
echo 対象日: %TARGET_DATE%
echo ========================================
echo.

REM Phase 10実行
echo [Phase 10] Phase 8最適化モデルで予測実行中...
python scripts\phase10_daily_prediction\run_daily_prediction.py --venue-code %KEIBAJO_CODE% --date %TARGET_DATE% --bankroll 100000 --kelly-fraction 0.25

if errorlevel 1 (
    echo.
    echo ❌ Phase 10でエラーが発生しました
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ Phase 10完了！
echo ========================================
echo.
echo 次のステップ:
echo   Phase 6配信用テキスト生成
echo   コマンド: scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE%
echo.

pause
