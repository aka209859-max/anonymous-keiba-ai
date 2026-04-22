@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ================================================================================
REM 毎日の競馬予測自動実行バッチ
REM ================================================================================

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
echo 競馬AI予測システム - 毎日実行
echo ================================================================================
echo.
echo 実行日: !TODAY!
echo.
echo ================================================================================

REM 対象競馬場のリスト（開催がある場合のみ実行）
REM 30=門別, 42=浦和, 43=船橋, 44=大井, 45=川崎

echo.
echo [INFO] 以下の競馬場の予測を実行します:
echo   - 浦和 (42)
echo   - 船橋 (43)
echo   - 大井 (44)
echo   - 川崎 (45)
echo.

REM Phase 12 馬単AI予測を実行
echo ================================================================================
echo Phase 12: 馬単AI予測
echo ================================================================================

REM 浦和
echo.
echo [1/4] 浦和の予測実行中...
call run_phase12_umatan.bat 42 !TODAY!
if errorlevel 1 (
    echo [WARNING] 浦和の予測に失敗しました（開催がない可能性があります）
)

REM 船橋
echo.
echo [2/4] 船橋の予測実行中...
call run_phase12_umatan.bat 43 !TODAY!
if errorlevel 1 (
    echo [WARNING] 船橋の予測に失敗しました（開催がない可能性があります）
)

REM 大井
echo.
echo [3/4] 大井の予測実行中...
call run_phase12_umatan.bat 44 !TODAY!
if errorlevel 1 (
    echo [WARNING] 大井の予測に失敗しました（開催がない可能性があります）
)

REM 川崎
echo.
echo [4/4] 川崎の予測実行中...
call run_phase12_umatan.bat 45 !TODAY!
if errorlevel 1 (
    echo [WARNING] 川崎の予測に失敗しました（開催がない可能性があります）
)

echo.
echo ================================================================================
echo 全ての予測が完了しました
echo ================================================================================
echo.
echo 生成された買い目ファイル:
dir predictions\phase12_umatan\*!YEAR!!MONTH!!DAY!*.txt 2>nul
echo.
echo ================================================================================

pause
endlocal
