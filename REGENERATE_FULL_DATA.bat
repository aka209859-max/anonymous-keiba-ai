@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

echo ================================================================================
echo Regenerate Full Training Data with rank_target and time
echo ================================================================================
echo.

REM Process each venue
set TOTAL=0
set SUCCESS=0

REM Urawa
echo [1/14] Urawa (Code: 42)
python old\misc\extract_training_data_v2.py --keibajo 42 --start-date 2020 --end-date 2025 --output old\data\training_csv\urawa_2020-2025_v3_FULL.csv
if exist old\data\training_csv\urawa_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Funabashi
echo [2/14] Funabashi (Code: 43)
python old\misc\extract_training_data_v2.py --keibajo 43 --start-date 2020 --end-date 2025 --output old\data\training_csv\funabashi_2020-2025_v3_FULL.csv
if exist old\data\training_csv\funabashi_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Kawasaki
echo [3/14] Kawasaki (Code: 45)
python old\misc\extract_training_data_v2.py --keibajo 45 --start-date 2020 --end-date 2025 --output old\data\training_csv\kawasaki_2020-2025_v3_FULL.csv
if exist old\data\training_csv\kawasaki_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Ooi
echo [4/14] Ooi (Code: 44)
python old\misc\extract_training_data_v2.py --keibajo 44 --start-date 2023 --end-date 2025 --output old\data\training_csv\ooi_2023-2025_v3_FULL.csv
if exist old\data\training_csv\ooi_2023-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Morioka
echo [5/14] Morioka (Code: 35)
python old\misc\extract_training_data_v2.py --keibajo 35 --start-date 2020 --end-date 2025 --output old\data\training_csv\morioka_2020-2025_v3_FULL.csv
if exist old\data\training_csv\morioka_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Mizusawa
echo [6/14] Mizusawa (Code: 36)
python old\misc\extract_training_data_v2.py --keibajo 36 --start-date 2020 --end-date 2025 --output old\data\training_csv\mizusawa_2020-2025_v3_FULL.csv
if exist old\data\training_csv\mizusawa_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Monbetsu
echo [7/14] Monbetsu (Code: 30)
python old\misc\extract_training_data_v2.py --keibajo 30 --start-date 2020 --end-date 2025 --output old\data\training_csv\monbetsu_2020-2025_v3_FULL.csv
if exist old\data\training_csv\monbetsu_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Kanazawa
echo [8/14] Kanazawa (Code: 46)
python old\misc\extract_training_data_v2.py --keibajo 46 --start-date 2020 --end-date 2025 --output old\data\training_csv\kanazawa_2020-2025_v3_FULL.csv
if exist old\data\training_csv\kanazawa_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Kasamatsu
echo [9/14] Kasamatsu (Code: 47)
python old\misc\extract_training_data_v2.py --keibajo 47 --start-date 2020 --end-date 2025 --output old\data\training_csv\kasamatsu_2020-2025_v3_FULL.csv
if exist old\data\training_csv\kasamatsu_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Nagoya
echo [10/14] Nagoya (Code: 48)
python old\misc\extract_training_data_v2.py --keibajo 48 --start-date 2022 --end-date 2025 --output old\data\training_csv\nagoya_2022-2025_v3_FULL.csv
if exist old\data\training_csv\nagoya_2022-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Sonoda
echo [11/14] Sonoda (Code: 50)
python old\misc\extract_training_data_v2.py --keibajo 50 --start-date 2020 --end-date 2025 --output old\data\training_csv\sonoda_2020-2025_v3_FULL.csv
if exist old\data\training_csv\sonoda_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Himeji
echo [12/14] Himeji (Code: 51)
python old\misc\extract_training_data_v2.py --keibajo 51 --start-date 2020 --end-date 2025 --output old\data\training_csv\himeji_2020-2025_v3_FULL.csv
if exist old\data\training_csv\himeji_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Kochi
echo [13/14] Kochi (Code: 54)
python old\misc\extract_training_data_v2.py --keibajo 54 --start-date 2020 --end-date 2025 --output old\data\training_csv\kochi_2020-2025_v3_FULL.csv
if exist old\data\training_csv\kochi_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Saga
echo [14/14] Saga (Code: 55)
python old\misc\extract_training_data_v2.py --keibajo 55 --start-date 2020 --end-date 2025 --output old\data\training_csv\saga_2020-2025_v3_FULL.csv
if exist old\data\training_csv\saga_2020-2025_v3_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

echo.
echo ================================================================================
echo Extraction Complete
echo ================================================================================
echo Total: %TOTAL% venues
echo Success: %SUCCESS% venues
echo ================================================================================
echo.
echo Next step: Add 67 features to these FULL CSVs
pause
