REM ============================================================
REM 地方競馬AI予想システム Phase 7-8-5 (Encoding Fix Applied)
REM ============================================================

REM ------------------------------------------------------------
REM Self-Reentry Section (自己再入セクション)
REM
REM 現在のコードページが65001(UTF-8)でない場合、変更して再起動する。
REM これにより、cmd.exeのバッファ不整合バグを回避し、
REM 最初からUTF-8としてファイルを読み込ませる。
REM ------------------------------------------------------------
chcp 65001 > nul
if "%~1"=="__REENTRY__" goto :MAIN_LOGIC

REM 同じスクリプトを新しいCMDプロセスで再起動（引数はそのまま渡す）
cmd /c "%~f0" __REENTRY__ %*
exit /b

:MAIN_LOGIC
REM 再入用フラグ(__REENTRY__)を引数リストから除去
shift /1

setlocal enabledelayedexpansion

REM ------------------------------------------------------------
REM [Python Environment Configuration: Python環境設定]
REM コンソール入出力をUTF-8に強制し、文字化けを防ぐ。
REM ------------------------------------------------------------
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM ------------------------------------------------------------
REM [Argument Validation: 引数検証]
REM ------------------------------------------------------------
if "%~1"=="" (
    echo [ERROR] Usage: run_all_optimized.bat [KEIBAJO_CODE] [DATE]
    echo [ERROR] Example: run_all_optimized.bat 43 2026-02-13
    echo.
    echo Venue Codes:
    echo   30=門別  35=盛岡  36=水沢  42=浦和  43=船橋  44=大井  45=川崎
    echo   46=金沢  47=笠松  48=名古屋 50=園田  51=姫路  54=高知  55=佐賀
    exit /b 1
)

if "%~2"=="" (
    echo [ERROR] DATE required (YYYY-MM-DD)
    exit /b 1
)

set "KEIBAJO_CODE=%~1"
set "TARGET_DATE=%~2"

REM 日付のパース (YYYY-MM-DD -> YYYYMMDD)
for /f "tokens=1,2,3 delims=-" %%a in ("%TARGET_DATE%") do (
    set YEAR=%%a
    set MONTH=%%b
    set DAY=%%c
)
set "DATE_SHORT=%YEAR%%MONTH%%DAY%"

REM ------------------------------------------------------------
REM [Venue Code Mapping: 競馬場コード定義]
REM NAR（地方競馬全国協会）コードに基づくマッピング
REM 文字列は全てUTF-8で処理される
REM ------------------------------------------------------------
set "KEIBAJO_NAME="
if "%KEIBAJO_CODE%"=="30" set "KEIBAJO_NAME=門別"
if "%KEIBAJO_CODE%"=="35" set "KEIBAJO_NAME=盛岡"
if "%KEIBAJO_CODE%"=="36" set "KEIBAJO_NAME=水沢"
if "%KEIBAJO_CODE%"=="42" set "KEIBAJO_NAME=浦和"
if "%KEIBAJO_CODE%"=="43" set "KEIBAJO_NAME=船橋"
if "%KEIBAJO_CODE%"=="44" set "KEIBAJO_NAME=大井"
if "%KEIBAJO_CODE%"=="45" set "KEIBAJO_NAME=川崎"
if "%KEIBAJO_CODE%"=="46" set "KEIBAJO_NAME=金沢"
if "%KEIBAJO_CODE%"=="47" set "KEIBAJO_NAME=笠松"
if "%KEIBAJO_CODE%"=="48" set "KEIBAJO_NAME=名古屋"
if "%KEIBAJO_CODE%"=="50" set "KEIBAJO_NAME=園田"
if "%KEIBAJO_CODE%"=="51" set "KEIBAJO_NAME=姫路"
if "%KEIBAJO_CODE%"=="54" set "KEIBAJO_NAME=高知"
if "%KEIBAJO_CODE%"=="55" set "KEIBAJO_NAME=佐賀"

if "%KEIBAJO_NAME%"=="" (
    echo [ERROR] Invalid venue code: %KEIBAJO_CODE%
    exit /b 1
)

REM ログディレクトリ作成
if not exist logs mkdir logs

echo ============================================================
echo 地方競馬AI予想システム Phase 7-8-5
echo ============================================================
echo 開始: %DATE% %TIME%
echo 競馬場: %KEIBAJO_NAME% (%KEIBAJO_CODE%)
echo 日付: %TARGET_DATE%
echo ============================================================

REM ------------------------------------------------------------
REM [Phase 0: Data Acquisition]
REM ------------------------------------------------------------
echo [Phase 0] データ取得...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %KEIBAJO_CODE% --date %DATE_SHORT%
if errorlevel 1 (
    echo [ERROR] Phase 0 failed
    exit /b 1
)
echo [OK] Phase 0

set "INPUT_CSV=data\raw\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_raw.csv"
set "OUTPUT_CSV=data\features\%YEAR%\%MONTH%\%KEIBAJO_NAME%_%DATE_SHORT%_features.csv"

REM ------------------------------------------------------------
REM [Phase 1: Feature Engineering]
REM ------------------------------------------------------------
echo [Phase 1] 特徴量生成...
python scripts\phase1_feature_engineering\prepare_features.py "%INPUT_CSV%" --output "%OUTPUT_CSV%"
if errorlevel 1 (
    echo [ERROR] Phase 1 failed
    exit /b 1
)
echo [OK] Phase 1

set "FEATURES_CSV=%OUTPUT_CSV%"
set "OUTPUT_P7_BINARY=data\predictions\phase7_binary\%KEIBAJO_NAME%_%DATE_SHORT%_phase7_binary.csv"
set "OUTPUT_P8_RANKING=data\predictions\phase8_ranking\%KEIBAJO_NAME%_%DATE_SHORT%_phase8_ranking.csv"
set "OUTPUT_P8_REGRESSION=data\predictions\phase8_regression\%KEIBAJO_NAME%_%DATE_SHORT%_phase8_regression.csv"

REM ------------------------------------------------------------
REM [Phase 7: Binary Prediction]
REM ------------------------------------------------------------
echo [Phase 7] Binary予測...
python scripts\phase7_binary\predict_optimized_binary.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P7_BINARY%"
if errorlevel 1 (
    echo [ERROR] Phase 7 failed
    exit /b 1
)
echo [OK] Phase 7

REM ------------------------------------------------------------
REM [Phase 8: Ranking Prediction]
REM ------------------------------------------------------------
echo [Phase 8] Ranking予測...
python scripts\phase8_ranking\predict_optimized_ranking.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P8_RANKING%"
if errorlevel 1 (
    echo [ERROR] Phase 8 Ranking failed
    exit /b 1
)
echo [OK] Phase 8 Ranking

echo [Phase 8] Regression予測...
python scripts\phase8_regression\predict_optimized_regression.py "%FEATURES_CSV%" "data\models\tuned" "%OUTPUT_P8_REGRESSION%"
if errorlevel 1 (
    echo [ERROR] Phase 8 Regression failed
    exit /b 1
)
echo [OK] Phase 8 Regression

REM ------------------------------------------------------------
REM [Phase 5: Ensemble Integration]
REM ------------------------------------------------------------
set "OUTPUT_ENSEMBLE=data\predictions\phase5\%KEIBAJO_NAME%_%DATE_SHORT%_ensemble_optimized.csv"

echo [Phase 5] アンサンブル統合...
python scripts\phase5_ensemble\ensemble_optimized.py "%OUTPUT_P7_BINARY%" "%OUTPUT_P8_RANKING%" "%OUTPUT_P8_REGRESSION%" "%OUTPUT_ENSEMBLE%"
if errorlevel 1 (
    echo [ERROR] Phase 5 failed
    exit /b 1
)
echo [OK] Phase 5

REM ------------------------------------------------------------
REM [Phase 6: Distribution Text Generation]
REM ------------------------------------------------------------
echo [Phase 6] 配信テキスト生成...
call scripts\phase6_betting\DAILY_OPERATION.bat %KEIBAJO_CODE% %TARGET_DATE% "%OUTPUT_ENSEMBLE%"
if errorlevel 1 (
    echo [WARNING] Phase 6 failed
) else (
    echo [OK] Phase 6
)

echo ============================================================
echo 完了: %DATE% %TIME%
echo ============================================================
echo.
echo [出力ファイル]
echo   - Ensemble : %OUTPUT_ENSEMBLE%
echo   - Note     : predictions\%KEIBAJO_NAME%_%DATE_SHORT%_note.txt
echo   - Bookers  : predictions\%KEIBAJO_NAME%_%DATE_SHORT%_bookers.txt
echo   - Tweet    : predictions\%KEIBAJO_NAME%_%DATE_SHORT%_tweet.txt
echo ============================================================

endlocal
exit /b 0
