@echo off
REM ========================================
REM JRA-VAN & JRDB データ検証スクリプト
REM ========================================
REM 目的: Eドライブのデータが公式仕様を満たしているか確認
REM 実行方法: このバッチファイルをダブルクリック
REM ========================================

echo ========================================
echo JRA-VAN / JRDB データ検証スクリプト
echo ========================================
echo.

REM 出力ファイル
set OUTPUT_FILE=%~dp0data_validation_report.txt
echo 検証結果を %OUTPUT_FILE% に出力します...
echo.

REM ========================================
REM 1. JRA-VAN データ検証
REM ========================================

echo ========================================  > "%OUTPUT_FILE%"
echo JRA-VAN データ検証レポート >> "%OUTPUT_FILE%"
echo 実行日時: %DATE% %TIME% >> "%OUTPUT_FILE%"
echo ========================================  >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo [1/6] JRA-VAN ディレクトリ確認中...
echo === 1. JRA-VAN ディレクトリ構造 === >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

if exist "E:\jra-keiba-data\jravan\" (
    echo ✓ E:\jra-keiba-data\jravan\ が存在します >> "%OUTPUT_FILE%"
    echo   ディレクトリ構造: >> "%OUTPUT_FILE%"
    dir /s /b "E:\jra-keiba-data\jravan\" | find /c "\" >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
) else (
    echo ✗ E:\jra-keiba-data\jravan\ が存在しません >> "%OUTPUT_FILE%"
    echo   推奨パス: E:\jra-keiba-data\jravan\raw\ >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

REM ========================================
REM 2. JRA-VAN レコードタイプ別ファイル確認
REM ========================================

echo [2/6] JRA-VAN レコードタイプ確認中...
echo === 2. JRA-VAN レコードタイプ別ファイル数 === >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

set "JRAVAN_BASE=E:\jra-keiba-data\jravan\raw"

if exist "%JRAVAN_BASE%\" (
    echo RA（レース詳細）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*RA*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo SE（競走馬詳細）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*SE*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo HR（競走成績）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*HR*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo H1-H6（払戻金）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*H1*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*H6*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo O1-O6（オッズ）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*O1*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*O6*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo WF（調教）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*WF*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo BLOD（血統）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRAVAN_BASE%\*BLOD*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo. >> "%OUTPUT_FILE%"
) else (
    echo ✗ JRA-VAN データディレクトリが見つかりません >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

REM ========================================
REM 3. JRA-VAN データサイズ確認
REM ========================================

echo [3/6] JRA-VAN データサイズ確認中...
echo === 3. JRA-VAN 総データサイズ === >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

if exist "%JRAVAN_BASE%\" (
    powershell -Command "(Get-ChildItem -Path '%JRAVAN_BASE%' -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB" >> "%OUTPUT_FILE%"
    echo GB （推奨: 20-50 GB） >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
) else (
    echo データなし >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

REM ========================================
REM 4. JRDB データ検証
REM ========================================

echo [4/6] JRDB ディレクトリ確認中...
echo === 4. JRDB ディレクトリ構造 === >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

if exist "E:\jrdb_data\" (
    echo ✓ E:\jrdb_data\ が存在します >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
) else (
    echo ✗ E:\jrdb_data\ が存在しません >> "%OUTPUT_FILE%"
    echo   推奨パス: E:\jrdb_data\lzh\ (LZHファイル) >> "%OUTPUT_FILE%"
    echo   推奨パス: E:\jrdb_data\raw\ (解凍済みTXT) >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

REM ========================================
REM 5. JRDB ファイル種別確認
REM ========================================

echo [5/6] JRDB ファイル種別確認中...
echo === 5. JRDB ファイル種別別ファイル数 === >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

set "JRDB_RAW=E:\jrdb_data\raw"
set "JRDB_LZH=E:\jrdb_data\lzh"

if exist "%JRDB_RAW%\" (
    echo 【解凍済みTXTファイル】 >> "%OUTPUT_FILE%"
    
    echo SED（成績データ）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRDB_RAW%\SED*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo KYI（騎手・調教師）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRDB_RAW%\KYI*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo BAC（馬場）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRDB_RAW%\BAC*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo CYB（前日情報）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRDB_RAW%\CYB*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo CHA（調教）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRDB_RAW%\CHA*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo SKB（成績拡張）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRDB_RAW%\SKB*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo TYB（当日情報）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRDB_RAW%\TYB*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo UKC（馬基本）: >> "%OUTPUT_FILE%"
    dir /s /b "%JRDB_RAW%\UKC*.txt" 2>nul | find /c "\" >> "%OUTPUT_FILE%"
    
    echo. >> "%OUTPUT_FILE%"
) else (
    echo ✗ JRDB 解凍済みデータなし >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

if exist "%JRDB_LZH%\" (
    echo 【LZH圧縮ファイル】 >> "%OUTPUT_FILE%"
    dir /b "%JRDB_LZH%\*.lzh" 2>nul | find /c ".lzh" >> "%OUTPUT_FILE%"
    echo 個のLZHファイル >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
) else (
    echo ✗ JRDB LZHファイルなし >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

REM ========================================
REM 6. JRDB データサイズ確認
REM ========================================

echo [6/6] JRDB データサイズ確認中...
echo === 6. JRDB 総データサイズ === >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

if exist "%JRDB_RAW%\" (
    powershell -Command "(Get-ChildItem -Path '%JRDB_RAW%' -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB" >> "%OUTPUT_FILE%"
    echo GB （推奨: 10-30 GB） >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
) else (
    echo データなし >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

REM ========================================
REM 7. サマリー
REM ========================================

echo === 7. 検証サマリー === >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo 【必須レコードタイプ/ファイル種別】 >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo JRA-VAN（必須8種類）: >> "%OUTPUT_FILE%"
echo   ✓ RA（レース詳細） >> "%OUTPUT_FILE%"
echo   ✓ SE（競走馬詳細） >> "%OUTPUT_FILE%"
echo   ✓ HR（競走成績） >> "%OUTPUT_FILE%"
echo   ✓ H1-H6（払戻金） >> "%OUTPUT_FILE%"
echo   ✓ O1-O6（オッズ） >> "%OUTPUT_FILE%"
echo   ✓ WF（調教） >> "%OUTPUT_FILE%"
echo   ✓ BLOD（血統） >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo JRDB（推奨8種類）: >> "%OUTPUT_FILE%"
echo   ✓ SED（成績データ） >> "%OUTPUT_FILE%"
echo   ✓ KYI（騎手・調教師） >> "%OUTPUT_FILE%"
echo   ✓ BAC（馬場） >> "%OUTPUT_FILE%"
echo   ✓ CYB（前日情報） >> "%OUTPUT_FILE%"
echo   ✓ CHA（調教） >> "%OUTPUT_FILE%"
echo   ✓ SKB（成績拡張） >> "%OUTPUT_FILE%"
echo   ✓ TYB（当日情報） >> "%OUTPUT_FILE%"
echo   ✓ UKC（馬基本） >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo 【推定データ量（15年分）】 >> "%OUTPUT_FILE%"
echo   JRA-VAN: 20-50 GB >> "%OUTPUT_FILE%"
echo   JRDB: 10-30 GB >> "%OUTPUT_FILE%"
echo   合計: 30-80 GB >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo 【推定ファイル数（15年分）】 >> "%OUTPUT_FILE%"
echo   JRA-VAN: 30,000-50,000 ファイル >> "%OUTPUT_FILE%"
echo   JRDB: 40,000-60,000 ファイル >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

REM ========================================
REM 8. TARGET frontier JV データベース確認
REM ========================================

echo === 8. TARGET frontier JV データベース確認 === >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo 【一般的な保存場所】 >> "%OUTPUT_FILE%"

if exist "C:\TARGET\" (
    echo ✓ C:\TARGET\ が存在します >> "%OUTPUT_FILE%"
    dir /s /b "C:\TARGET\*.db" 2>nul >> "%OUTPUT_FILE%"
    dir /s /b "C:\TARGET\*.sqlite" 2>nul >> "%OUTPUT_FILE%"
    dir /s /b "C:\TARGET\*.mdb" 2>nul >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
) else (
    echo ✗ C:\TARGET\ なし >> "%OUTPUT_FILE%"
)

if exist "C:\Program Files\TARGET\" (
    echo ✓ C:\Program Files\TARGET\ が存在します >> "%OUTPUT_FILE%"
    dir /s /b "C:\Program Files\TARGET\*.db" 2>nul >> "%OUTPUT_FILE%"
    dir /s /b "C:\Program Files\TARGET\*.sqlite" 2>nul >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
) else (
    echo ✗ C:\Program Files\TARGET\ なし >> "%OUTPUT_FILE%"
)

if exist "C:\Program Files (x86)\TARGET\" (
    echo ✓ C:\Program Files (x86)\TARGET\ が存在します >> "%OUTPUT_FILE%"
    dir /s /b "C:\Program Files (x86)\TARGET\*.db" 2>nul >> "%OUTPUT_FILE%"
    dir /s /b "C:\Program Files (x86)\TARGET\*.sqlite" 2>nul >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
) else (
    echo ✗ C:\Program Files (x86)\TARGET\ なし >> "%OUTPUT_FILE%"
)

echo 【マイドキュメント】 >> "%OUTPUT_FILE%"
dir /s /b "%USERPROFILE%\Documents\TARGET\*.db" 2>nul >> "%OUTPUT_FILE%"
dir /s /b "%USERPROFILE%\Documents\TARGET\*.sqlite" 2>nul >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

REM ========================================
REM 完了
REM ========================================

echo ========================================
echo 検証完了！
echo ========================================
echo.
echo レポートファイル: %OUTPUT_FILE%
echo.
echo レポートを開きますか？ (Y/N)
set /p OPEN_REPORT=
if /i "%OPEN_REPORT%"=="Y" notepad "%OUTPUT_FILE%"

echo.
echo 終了するには何かキーを押してください...
pause >nul
