@echo off
chcp 65001 >nul
setlocal

set "PROJECT_ROOT=%~dp0.."

echo.
echo ========================================
echo   Content Distributor - Dev Startup
echo ========================================
echo.

REM === 1. Check Docker ===
echo [INFO] Checking Docker...
docker info >nul 2>&1
if not %errorlevel%==0 (
    echo [FAIL] Docker Desktop not running
    pause
    exit /b 1
)
echo [OK]   Docker Desktop running

REM === 2. Check .venv ===
if not exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    echo [FAIL] .venv not found
    pause
    exit /b 1
)
echo [OK]   Python venv exists

REM === 3. Start PostgreSQL + n8n (skip if running) ===
echo.
echo [INFO] Checking Docker infra...
set "NEED_INFRA=0"
docker ps --format "{{.Names}}" 2>nul | findstr "content_distributor_db" >nul 2>&1
if not %errorlevel%==0 set "NEED_INFRA=1"
docker ps --format "{{.Names}}" 2>nul | findstr "content_distributor_n8n" >nul 2>&1
if not %errorlevel%==0 set "NEED_INFRA=1"
if %NEED_INFRA%==1 (
    echo [INFO] Starting Docker infra...
    cd /d "%PROJECT_ROOT%"
    docker compose up -d
    echo [INFO] Waiting for services...
    timeout /t 5 /nobreak >nul
    echo [OK]   PostgreSQL + n8n started
) else (
    echo [OK]   PostgreSQL + n8n already running
)

REM === 4. Activate venv and run migration ===
echo.
echo [INFO] Running migration...
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
cd /d "%PROJECT_ROOT%\backend"
python -m alembic upgrade head
echo [OK]   Migration done

REM === 5. Start backend in background window ===
echo.
echo [INFO] Starting FastAPI backend (port 8888)...
start "FastAPI-Backend" /min cmd /k "cd /d %PROJECT_ROOT%\backend && call %PROJECT_ROOT%\.venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8888"
timeout /t 3 /nobreak >nul
echo [OK]   Backend started (minimized window)

REM === 6. Check frontend deps ===
cd /d "%PROJECT_ROOT%\frontend"
if not exist "node_modules" (
    echo.
    echo [INFO] Installing frontend deps...
    npm install --legacy-peer-deps
)

REM === 7. Start frontend in background window ===
echo.
echo [INFO] Starting Vite frontend (port 3000)...
start "Vite-Frontend" /min cmd /k "cd /d %PROJECT_ROOT%\frontend && npm run dev"
timeout /t 3 /nobreak >nul
echo [OK]   Frontend started (minimized window)

REM === Done ===
echo.
echo ========================================
echo   Dev environment ready!
echo ========================================
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8888
echo   API Docs:  http://localhost:8888/api/v1/docs
echo   n8n:       http://localhost:5678
echo.
echo   Stop all:  scripts\stop-dev.bat
echo ========================================
echo.
pause
