@echo off
setlocal enabledelayedexpansion
title OnTrack AI - Environment Setup (SIH26103 / MoSPI PAIMANA)
echo =====================================================================
echo   OnTrack AI - Complete Setup (SIH26103)
echo   Ministry of Statistics and Programme Implementation (MoSPI) PAIMANA
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/3] Setting up Python virtual environment (.venv)...
if not exist ".venv" (
    echo Creating virtual environment with Python...
    python -m venv .venv
    if errorlevel 1 (
        echo Trying 'py' launcher...
        py -3 -m venv .venv
    )
) else (
    echo Virtual environment (.venv) already exists.
)

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Failed to create Python virtual environment. Please ensure Python 3.10+ is installed and on PATH.
    pause
    exit /b 1
)

echo [2/3] Installing Python backend and ML dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some pip dependencies encountered warnings. Verifying core packages...
    pip install fastapi uvicorn pandas numpy scikit-learn joblib xgboost shap requests
)

echo.
echo [3/3] Installing React/Vite frontend dependencies...
if exist "frontend\package.json" (
    cd frontend
    call npm install
    cd ..
) else (
    echo [WARNING] frontend/package.json not found in %CD%
)

echo.
echo =====================================================================
echo   Setup Complete!
echo   To launch the application, run: start_ontrack.bat
echo =====================================================================
pause
