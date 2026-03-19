@echo off
chcp 65001 >nul

echo.
echo [INFO] Stopping app services (Docker infra stays running)...
echo.

taskkill /F /FI "WINDOWTITLE eq FastAPI-Backend*" >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
echo [OK]   Backend stopped

taskkill /F /FI "WINDOWTITLE eq Vite-Frontend*" >nul 2>&1
echo [OK]   Frontend stopped

echo.
echo [OK]   App services stopped
echo [INFO] Docker (PostgreSQL, n8n) still running
echo        To stop infra: docker compose stop
pause
