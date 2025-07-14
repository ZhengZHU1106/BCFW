@echo off
echo.
echo 🛑 Stopping Blockchain Security Platform Services...
echo =================================================

echo 📦 Stopping Frontend (Vite)...
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend stopped
) else (
    echo ℹ️  Frontend not running
)

echo 📦 Stopping Backend (Python)...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend stopped
) else (
    echo ℹ️  Backend not running
)

echo 📦 Stopping Ganache...
taskkill /f /im ganache.exe >nul 2>&1
taskkill /f /im ganache-cli.exe >nul 2>&1
echo ✅ Ganache stopped

echo.
echo 🔍 Freeing ports...
netstat -ano | findstr :5173 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /f /pid %%a >nul 2>&1
    echo ✅ Port 5173 freed (Frontend)
) else (
    echo ✅ Port 5173 is free (Frontend)
)

netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
    echo ✅ Port 8000 freed (Backend)
) else (
    echo ✅ Port 8000 is free (Backend)
)

netstat -ano | findstr :8545 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8545') do taskkill /f /pid %%a >nul 2>&1
    echo ✅ Port 8545 freed (Ganache)
) else (
    echo ✅ Port 8545 is free (Ganache)
)

echo.
echo 🎉 All services have been stopped successfully!
echo =================================================
echo Services stopped:
echo   • Frontend (Vue + Vite) - Port 5173
echo   • Backend (FastAPI) - Port 8000
echo   • Ganache Blockchain - Port 8545
echo.
echo You can now safely close terminal windows or restart services.
echo.
pause