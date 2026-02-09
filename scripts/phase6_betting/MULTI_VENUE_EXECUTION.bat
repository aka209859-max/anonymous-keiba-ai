@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

echo ==================================================
echo 複数競馬場一括予想実行スクリプト
echo ==================================================
echo.
echo Date: 2026-02-10
echo Venues: 名古屋(48), 船橋(43), 姫路(51), 高知(54)
echo.
echo ==================================================
echo.

set TARGET_DATE=2026-02-10
set DATE_SHORT=20260210

echo [Step 1] Phase 0-5: 各競馬場のデータ取得〜予測
echo.

REM 名古屋
echo --------------------------------------------------
echo [1/4] 名古屋競馬 (48)
echo --------------------------------------------------
call run_all.bat 48 %TARGET_DATE%
if errorlevel 1 (
    echo [ERROR] 名古屋 Phase 0-5 failed
    set NAGOYA_STATUS=FAIL
) else (
    echo [OK] 名古屋 Phase 0-5 complete
    set NAGOYA_STATUS=OK
)
echo.

REM 船橋
echo --------------------------------------------------
echo [2/4] 船橋競馬 (43)
echo --------------------------------------------------
call run_all.bat 43 %TARGET_DATE%
if errorlevel 1 (
    echo [ERROR] 船橋 Phase 0-5 failed
    set FUNABASHI_STATUS=FAIL
) else (
    echo [OK] 船橋 Phase 0-5 complete
    set FUNABASHI_STATUS=OK
)
echo.

REM 姫路
echo --------------------------------------------------
echo [3/4] 姫路競馬 (51)
echo --------------------------------------------------
call run_all.bat 51 %TARGET_DATE%
if errorlevel 1 (
    echo [ERROR] 姫路 Phase 0-5 failed
    set HIMEJI_STATUS=FAIL
) else (
    echo [OK] 姫路 Phase 0-5 complete
    set HIMEJI_STATUS=OK
)
echo.

REM 高知
echo --------------------------------------------------
echo [4/4] 高知競馬 (54)
echo --------------------------------------------------
call run_all.bat 54 %TARGET_DATE%
if errorlevel 1 (
    echo [ERROR] 高知 Phase 0-5 failed
    set KOCHI_STATUS=FAIL
) else (
    echo [OK] 高知 Phase 0-5 complete
    set KOCHI_STATUS=OK
)
echo.

echo ==================================================
echo Phase 0-5 Summary
echo ==================================================
echo.
echo Status:
echo   名古屋: %NAGOYA_STATUS%
echo   船橋: %FUNABASHI_STATUS%
echo   姫路: %HIMEJI_STATUS%
echo   高知: %KOCHI_STATUS%
echo.
echo ==================================================
echo.

echo [Step 2] Phase 6: 配信用ファイル生成（一括処理）
echo.

call BATCH_OPERATION.bat %TARGET_DATE%

if errorlevel 1 (
    echo [ERROR] Batch operation failed
    exit /b 1
)

echo.
echo ==================================================
echo All Complete!
echo ==================================================
echo.
echo Generated Files:
echo.
dir predictions\*%DATE_SHORT%*.txt
echo.
echo ==================================================
echo.
echo Next Steps:
echo   1. Check predictions folder
echo   2. Copy files for distribution
echo   3. Post to Note/Twitter/Bookers
echo.
echo Commands:
echo   explorer predictions
echo.
echo ==================================================
