@echo off
echo ========================================
echo Simple Test Batch
echo ========================================
echo.
echo KEIBAJO_CODE: %1
echo DATE: %2
echo.

REM Test 1: Check Python
echo [Test 1] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)
echo.

REM Test 2: Check script exists
echo [Test 2] Checking script...
if not exist "scripts\phase0_data_acquisition\extract_race_data.py" (
    echo ERROR: Script not found
    pause
    exit /b 1
)
echo Script found: OK
echo.

REM Test 3: Run Phase 0
echo [Test 3] Running Phase 0...
python scripts\phase0_data_acquisition\extract_race_data.py --keibajo %1 --date %2
if errorlevel 1 (
    echo ERROR: Phase 0 failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo All tests passed!
echo ========================================
pause
