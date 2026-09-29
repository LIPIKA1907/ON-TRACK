@echo off
setlocal
title OnTrack AI - Launch System (SIH26103 / MoSPI PAIMANA)
echo =====================================================================
echo   Starting OnTrack AI System (SIH26103 / MoSPI PAIMANA)
echo =====================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found. Running setup_ontrack.bat first...
    call "%~dp0setup_ontrack.bat"
)

echo [1/2] Starting FastAPI backend on http://127.0.0.1:8001 ...
start "OnTrack AI - Backend (Port 8001)" cmd /k "cd /d "%CD%" && call .venv\Scripts\activate.bat && uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload"

echo [2/2] Starting React/Vite frontend on http://localhost:5173 ...
start "OnTrack AI - Frontend (Port 5173)" cmd /k "cd /d "%CD%\frontend" && npm run dev"

echo.
echo =====================================================================
echo   Services Launched!
echo   - Backend:  http://127.0.0.1:8001 (API Docs: http://127.0.0.1:8001/docs)
echo   - Frontend: http://localhost:5173
echo.
echo   Opening dashboard in your default browser...
echo =====================================================================
timeout /t 3 >nul
start http://localhost:5173
