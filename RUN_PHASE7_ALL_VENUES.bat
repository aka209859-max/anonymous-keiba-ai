@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d E:\anonymous-keiba-ai

echo ================================================================================
echo Phase 7: Boruta Feature Selection for 14 Venues
echo ================================================================================
echo.

if not exist "data\features\selected" mkdir "data\features\selected"

set TOTAL=0
set SUCCESS=0
set FAIL=0

REM Process Monbetsu (30)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Monbetsu Code 30 - 2020-2025
set INPUT_CSV=monbetsu_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\monbetsu_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Morioka (35)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Morioka Code 35 - 2020-2025
set INPUT_CSV=morioka_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\morioka_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Mizusawa (36)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Mizusawa Code 36 - 2020-2025
set INPUT_CSV=mizusawa_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\mizusawa_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Urawa (42)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Urawa Code 42 - 2020-2025
set INPUT_CSV=urawa_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\urawa_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Funabashi (43)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Funabashi Code 43 - 2020-2025
set INPUT_CSV=funabashi_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\funabashi_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Ooi (44)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Ooi Code 44 - 2023-2025
set INPUT_CSV=ooi_2023-2025_v3.csv
set OUTPUT_CSV=data\features\selected\ooi_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Kawasaki (45)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Kawasaki Code 45 - 2020-2025
set INPUT_CSV=kawasaki_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\kawasaki_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Kanazawa (46)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Kanazawa Code 46 - 2020-2025
set INPUT_CSV=kanazawa_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\kanazawa_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Kasamatsu (47)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Kasamatsu Code 47 - 2020-2025
set INPUT_CSV=kasamatsu_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\kasamatsu_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Nagoya (48)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Nagoya Code 48 - 2022-2025
set INPUT_CSV=nagoya_2022-2025_v3.csv
set OUTPUT_CSV=data\features\selected\nagoya_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Sonoda (50)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Sonoda Code 50 - 2020-2025
set INPUT_CSV=sonoda_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\sonoda_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Himeji (51)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Himeji Code 51 - 2020-2025
set INPUT_CSV=himeji_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\himeji_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Kochi (54)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Kochi Code 54 - 2020-2025
set INPUT_CSV=kochi_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\kochi_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

REM Process Saga (55)
set /a TOTAL+=1
echo.
echo [!TOTAL!/14] Saga Code 55 - 2020-2025
set INPUT_CSV=saga_2020-2025_v3.csv
set OUTPUT_CSV=data\features\selected\saga_selected_features.csv
if not exist "!INPUT_CSV!" (
    echo [ERROR] Input file not found: !INPUT_CSV!
    set /a FAIL+=1
) else if exist "!OUTPUT_CSV!" (
    echo [SKIP] Already exists: !OUTPUT_CSV!
    set /a SUCCESS+=1
) else (
    echo [RUN] Running Boruta...
    python scripts\phase7_feature_selection\run_boruta_selection.py "!INPUT_CSV!" --alpha 0.10 --max-iter 200
    if exist "!OUTPUT_CSV!" (
        echo [OK] Success: !OUTPUT_CSV!
        set /a SUCCESS+=1
    ) else (
        echo [ERROR] Failed: !OUTPUT_CSV!
        set /a FAIL+=1
    )
)

echo.
echo ================================================================================
echo Phase 7 Complete
echo ================================================================================
echo Total: 14 venues
echo Success: !SUCCESS! venues
echo Failed: !FAIL! venues
echo ================================================================================

if !FAIL! gtr 0 (
    echo [WARNING] Some venues failed
    exit /b 1
) else (
    echo [SUCCESS] All 14 venues completed Phase 7
    echo Next step: RUN_PHASE8_ALL_VENUES.bat
)

pause
