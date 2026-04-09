@echo off
chcp 932 >nul
setlocal enabledelayedexpansion

echo ================================================================================
echo 2025年 全競馬場予測データ生成バッチ
echo ================================================================================
echo.

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM 競馬場コードと期間の定義
REM 30=盛岡(4/16-11/13), 35=門別(5/3-11/18), 36=水沢(3/9-12/31)
REM 42=浦和(1/7-12/25), 43=船橋(1/20-12/12), 44=大井(1/13-12/31)
REM 45=川崎(1/1-12/19), 46=金沢(3/16-12/28), 47=笠松(1/7-12/31)
REM 48=名古屋(1/1-12/24), 50=園田(1/2-12/31), 51=姫路(1/21-3/6)
REM 54=高知(1/1-12/31), 55=佐賀(1/4-12/28)

echo [警告] このバッチは全競馬場の予測を生成するため、数時間かかります
echo.
echo 生成対象: 14競馬場 x 約1,000レース = 約14,000レース
echo.
pause

REM 各競馬場の代表日（月初）で予測生成
echo.
echo ========================================
echo 42: 浦和 2025-01-07
echo ========================================
call run_all_FINAL.bat 42 2025-01-07
if errorlevel 1 goto error

echo.
echo ========================================
echo 43: 船橋 2025-01-20
echo ========================================
call run_all_FINAL.bat 43 2025-01-20
if errorlevel 1 goto error

echo.
echo ========================================
echo 44: 大井 (スキップ - 既存)
echo ========================================
echo 大井は既に predictions\phase5_ooi_2025\ に存在します

echo.
echo ========================================
echo 45: 川崎 2025-01-01
echo ========================================
call run_all_FINAL.bat 45 2025-01-01
if errorlevel 1 goto error

echo.
echo ========================================
echo 46: 金沢 2025-03-16
echo ========================================
call run_all_FINAL.bat 46 2025-03-16
if errorlevel 1 goto error

echo.
echo ========================================
echo 47: 笠松 2025-01-07
echo ========================================
call run_all_FINAL.bat 47 2025-01-07
if errorlevel 1 goto error

echo.
echo ========================================
echo 48: 名古屋 2025-01-01
echo ========================================
call run_all_FINAL.bat 48 2025-01-01
if errorlevel 1 goto error

echo.
echo ========================================
echo 50: 園田 2025-01-02
echo ========================================
call run_all_FINAL.bat 50 2025-01-02
if errorlevel 1 goto error

echo.
echo ========================================
echo 51: 姫路 2025-01-21
echo ========================================
call run_all_FINAL.bat 51 2025-01-21
if errorlevel 1 goto error

echo.
echo ========================================
echo 54: 高知 2025-01-01
echo ========================================
call run_all_FINAL.bat 54 2025-01-01
if errorlevel 1 goto error

echo.
echo ========================================
echo 55: 佐賀 2025-01-04
echo ========================================
call run_all_FINAL.bat 55 2025-01-04
if errorlevel 1 goto error

echo.
echo ========================================
echo 30: 盛岡 2025-04-16
echo ========================================
call run_all_FINAL.bat 30 2025-04-16
if errorlevel 1 goto error

echo.
echo ========================================
echo 35: 門別 2025-05-03
echo ========================================
call run_all_FINAL.bat 35 2025-05-03
if errorlevel 1 goto error

echo.
echo ========================================
echo 36: 水沢 2025-03-09
echo ========================================
call run_all_FINAL.bat 36 2025-03-09
if errorlevel 1 goto error

echo.
echo ================================================================================
echo 完了！全競馬場の予測データを生成しました
echo ================================================================================
echo.
echo 次のステップ:
echo 1. predictions\phase5\ ディレクトリを確認
echo 2. python scripts\evaluation\analyze_all_venues_2025_from_db.py を実行
echo.
goto end

:error
echo.
echo ========================================
echo エラーが発生しました
echo ========================================
exit /b 1

:end
endlocal
