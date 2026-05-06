@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

echo ================================================================================
echo Add 67 Statistical Features to FULL CSVs (with rank_target and time)
echo ================================================================================
echo.

REM Create output directory
if not exist "data\features\67features_FULL" mkdir "data\features\67features_FULL"

set TOTAL=0
set SUCCESS=0

REM Urawa
echo [1/14] Urawa
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\urawa_2020-2025_v3_FULL.csv data\features\67features_FULL\urawa_67features_FULL.csv
if exist data\features\67features_FULL\urawa_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Funabashi
echo [2/14] Funabashi
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\funabashi_2020-2025_v3_FULL.csv data\features\67features_FULL\funabashi_67features_FULL.csv
if exist data\features\67features_FULL\funabashi_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Kawasaki
echo [3/14] Kawasaki
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\kawasaki_2020-2025_v3_FULL.csv data\features\67features_FULL\kawasaki_67features_FULL.csv
if exist data\features\67features_FULL\kawasaki_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Ooi
echo [4/14] Ooi
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\ooi_2023-2025_v3_FULL.csv data\features\67features_FULL\ooi_67features_FULL.csv
if exist data\features\67features_FULL\ooi_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Morioka
echo [5/14] Morioka
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\morioka_2020-2025_v3_FULL.csv data\features\67features_FULL\morioka_67features_FULL.csv
if exist data\features\67features_FULL\morioka_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Mizusawa
echo [6/14] Mizusawa
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\mizusawa_2020-2025_v3_FULL.csv data\features\67features_FULL\mizusawa_67features_FULL.csv
if exist data\features\67features_FULL\mizusawa_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Monbetsu
echo [7/14] Monbetsu
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\monbetsu_2020-2025_v3_FULL.csv data\features\67features_FULL\monbetsu_67features_FULL.csv
if exist data\features\67features_FULL\monbetsu_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Kanazawa
echo [8/14] Kanazawa
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\kanazawa_2020-2025_v3_FULL.csv data\features\67features_FULL\kanazawa_67features_FULL.csv
if exist data\features\67features_FULL\kanazawa_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Kasamatsu
echo [9/14] Kasamatsu
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\kasamatsu_2020-2025_v3_FULL.csv data\features\67features_FULL\kasamatsu_67features_FULL.csv
if exist data\features\67features_FULL\kasamatsu_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Nagoya
echo [10/14] Nagoya
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\nagoya_2022-2025_v3_FULL.csv data\features\67features_FULL\nagoya_67features_FULL.csv
if exist data\features\67features_FULL\nagoya_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Sonoda
echo [11/14] Sonoda
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\sonoda_2020-2025_v3_FULL.csv data\features\67features_FULL\sonoda_67features_FULL.csv
if exist data\features\67features_FULL\sonoda_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Himeji
echo [12/14] Himeji
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\himeji_2020-2025_v3_FULL.csv data\features\67features_FULL\himeji_67features_FULL.csv
if exist data\features\67features_FULL\himeji_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Kochi
echo [13/14] Kochi
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\kochi_2020-2025_v3_FULL.csv data\features\67features_FULL\kochi_67features_FULL.csv
if exist data\features\67features_FULL\kochi_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

REM Saga
echo [14/14] Saga
python scripts\phase1_feature_engineering\add_statistical_features.py old\data\training_csv\saga_2020-2025_v3_FULL.csv data\features\67features_FULL\saga_67features_FULL.csv
if exist data\features\67features_FULL\saga_67features_FULL.csv (set /a SUCCESS+=1)
set /a TOTAL+=1

echo.
echo ================================================================================
echo Feature Addition Complete
echo ================================================================================
echo Total: %TOTAL% venues
echo Success: %SUCCESS% venues
echo ================================================================================
echo.
echo Output directory: data\features\67features_FULL
echo.
echo Next step: Train Ranking and Regression models with 67 features
pause
