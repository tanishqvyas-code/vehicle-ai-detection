@echo off
title VehicleAI — Detection System
color 0B

echo.
echo  =========================================
echo   🚦 VehicleAI — Vehicle Detection System
echo  =========================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Install dependencies if needed
echo  [1/3] Checking / installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo  [OK] Dependencies ready.
echo.

:: Create outputs dir
if not exist "backend\outputs" mkdir "backend\outputs"

:: Start the server
echo  [2/3] Starting FastAPI backend on http://localhost:8000 ...
echo.
cd backend

:: Open browser after a short delay (runs in background)
start "" cmd /c "timeout /t 3 >nul && start http://localhost:8000"

echo  [3/3] Server running. Press Ctrl+C to stop.
echo  Open your browser at: http://localhost:8000
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
