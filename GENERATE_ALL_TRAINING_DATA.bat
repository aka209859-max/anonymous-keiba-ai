@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

echo ============================================================
echo 🚀 地方競馬AI 学習データ一括生成 (残り13会場)
echo ============================================================
echo.
echo 📊 対象競馬場: 13会場 (船橋は完了済み)
echo ⏱️  推定時間: 約1〜2時間
echo.

REM データディレクトリの作成
if not exist "data\training" mkdir "data\training"

REM 会場リスト (13会場)
set VENUES[0]=30:monbetsu:門別
set VENUES[1]=33:obihiro:帯広
set VENUES[2]=35:morioka:盛岡
set VENUES[3]=36:mizusawa:水沢
set VENUES[4]=42:urawa:浦和
REM 43=funabashi は完了済み
set VENUES[5]=44:ooi:大井
set VENUES[6]=45:kawasaki:川崎
set VENUES[7]=46:kanazawa:金沢
set VENUES[8]=47:kasamatsu:笠松
set VENUES[9]=48:nagoya:名古屋
set VENUES[10]=50:sonoda:園田
set VENUES[11]=51:himeji:姫路
set VENUES[12]=54:kochi:高知
set VENUES[13]=55:saga:佐賀

REM ログファイル作成
set LOG_FILE=data\training\generation_log_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set LOG_FILE=%LOG_FILE: =0%
echo [%date% %time%] 学習データ一括生成開始 > "%LOG_FILE%"

REM 各会場のデータ生成
set COUNT=0
for /L %%i in (0,1,13) do (
    set VENUE_INFO=!VENUES[%%i]!
    for /F "tokens=1,2,3 delims=:" %%a in ("!VENUE_INFO!") do (
        set /A COUNT+=1
        echo.
        echo ============================================================
        echo [!COUNT!/13] %%c (コード: %%a) データ生成中...
        echo ============================================================
        echo [%date% %time%] %%c (%%a) 開始 >> "%LOG_FILE%"
        
        python extract_training_data_v2.py ^
          --keibajo %%a ^
          --start-date 2020 ^
          --end-date 2026 ^
          --output "data\training\%%b_2020-2026_with_time_PHASE78.csv"
        
        if !ERRORLEVEL! EQU 0 (
            echo [%date% %time%] %%c (%%a) 完了 >> "%LOG_FILE%"
            echo ✅ %%c 完了！
        ) else (
            echo [%date% %time%] %%c (%%a) エラー >> "%LOG_FILE%"
            echo ❌ %%c エラー！ログを確認してください。
        )
    )
)

echo.
echo ============================================================
echo ✅ 全13会場のデータ生成が完了しました！
echo ============================================================
echo.
echo 📁 出力先: data\training\
echo 📄 ログ: %LOG_FILE%
echo.
echo 次のステップ:
echo   1. 生成されたCSVファイルを確認
echo   2. Phase 7 Ranking 特徴量選択を実行
echo   3. Phase 7 Regression 特徴量選択を実行
echo.
pause
