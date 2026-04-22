@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ================================================================================
REM シンプル版: 今日の予測（競馬場を指定）
REM ================================================================================

if "%~1"=="" (
    echo Usage: run_today.bat [KEIBAJO_CODE]
    echo.
    echo 競馬場コード:
    echo   30: 門別    42: 浦和    43: 船橋
    echo   44: 大井    45: 川崎    48: 名古屋
    echo   50: 園田    55: 佐賀
    echo.
    echo 例: run_today.bat 42  (浦和の今日の予測)
    exit /b 1
)

REM 今日の日付を取得（YYYY-MM-DD形式）
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (
    set YEAR=%%c
    set MONTH=%%a
    set DAY=%%b
)

REM 月・日が1桁の場合は0埋め
if !MONTH! LSS 10 set MONTH=0!MONTH:~-1!
if !DAY! LSS 10 set DAY=0!DAY:~-1!

set "TODAY=!YEAR!-!MONTH!-!DAY!"

echo ================================================================================
echo 今日の予測実行
echo ================================================================================
echo 日付: !TODAY!
echo 競馬場コード: %~1
echo ================================================================================

call run_phase12_umatan.bat %~1 !TODAY!

endlocal
