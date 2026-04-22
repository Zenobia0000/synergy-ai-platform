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
    echo [FAIL] .venv not found - run: uv venv .venv ^&^& uv pip install -r backend/requirements.txt
    pause
    exit /b 1
)
echo [OK]   Python venv exists

REM === 2.5. Check backend/.env (required secrets) ===
if not exist "%PROJECT_ROOT%\backend\.env" (
    echo [FAIL] backend\.env not found
    echo        Run: copy backend\.env.example backend\.env
    echo        Then edit backend\.env and set N8N_WEBHOOK_SECRET and SECRET_KEY
    pause
    exit /b 1
)
findstr /C:"N8N_WEBHOOK_SECRET=your-webhook-secret-here" "%PROJECT_ROOT%\backend\.env" >nul 2>&1
if %errorlevel%==0 (
    echo [FAIL] backend\.env still contains default placeholder secrets
    echo        Edit backend\.env and replace N8N_WEBHOOK_SECRET / SECRET_KEY with real values
    pause
    exit /b 1
)
echo [OK]   backend\.env exists with non-default secrets

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
echo [INFO] Starting FastAPI backend (port 8000)...
start "FastAPI-Backend" /min cmd /k "cd /d %PROJECT_ROOT%\backend && call %PROJECT_ROOT%\.venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
echo [OK]   Backend started (minimized window)

REM === 6. Check frontend deps ===
cd /d "%PROJECT_ROOT%\frontend"
if not exist "node_modules" (
    echo.
    echo [INFO] Installing frontend deps...
    npm install
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
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/api/v1/docs
echo   n8n:       http://localhost:5678
echo.
echo   Stop all:  scripts\stop-dev.bat
echo ========================================
echo.
pause
