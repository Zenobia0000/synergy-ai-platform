@echo off
chcp 65001 >nul

echo.
echo [INFO] Stopping app services (Docker infra stays running)...
echo.

REM Try title-based kill first (matches start-dev.bat's start "FastAPI-Backend")
taskkill /F /FI "WINDOWTITLE eq FastAPI-Backend*" >nul 2>&1
REM Fallback: kill anything bound to port 8000 (more surgical than /IM uvicorn.exe)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo [OK]   Backend stopped

taskkill /F /FI "WINDOWTITLE eq Vite-Frontend*" >nul 2>&1
REM Fallback: kill anything bound to port 3000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo [OK]   Frontend stopped

echo.
echo [OK]   App services stopped
echo [INFO] Docker (PostgreSQL, n8n) still running
echo        To stop infra: docker compose stop
pause
