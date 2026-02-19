@echo off
echo ========================================
echo CloudGuardAI - Complete Startup Script
echo ========================================
echo.

REM Use script directory as project root
set PROJECT_ROOT=%~dp0

REM Stop existing CloudGuard processes gracefully
echo [1/5] Stopping existing services...
for /f "tokens=2" %%a in ('tasklist /fi "WINDOWTITLE eq CloudGuard*" /fo list ^| findstr PID') do taskkill /PID %%a /F >nul 2>&1
timeout /t 2 /nobreak >nul

REM Clean and recreate database
echo [2/5] Recreating database...
cd /d "%PROJECT_ROOT%api"
if exist cloudguard.db del /F cloudguard.db
python -c "from app.database import engine, Base; from app.models import Scan, Finding, Feedback, ModelVersion; Base.metadata.create_all(bind=engine); print('✓ Database created')"
python seed_model.py

REM Start API Service
echo [3/5] Starting API service...
start "CloudGuard API" cmd /k "cd /d "%PROJECT_ROOT%api" && set PYTHONPATH=%PROJECT_ROOT%api && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 4 /nobreak >nul

REM Start ML Service
echo [4/5] Starting ML service...
start "CloudGuard ML" cmd /k "cd /d "%PROJECT_ROOT%ml" && set PYTHONPATH=%PROJECT_ROOT%ml && python -m uvicorn ml_service.main:app --host 127.0.0.1 --port 8001"
timeout /t 4 /nobreak >nul

REM Start Web UI
echo [5/5] Starting Web UI...
start "CloudGuard Web" cmd /k "cd /d "%PROJECT_ROOT%web" && npm run dev"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo All services started successfully!
echo ========================================
echo.
echo Web UI:     http://localhost:3000
echo API:        http://127.0.0.1:8000
echo ML Service: http://127.0.0.1:8001
echo.
echo Check your taskbar for three CMD windows.
echo Press any key to exit this window...
pause >nul
