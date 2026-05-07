@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"

if not exist "%FRONTEND_DIR%" (
    echo [ERROR] frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

cd /d "%FRONTEND_DIR%"

if not exist "node_modules" (
    echo [ERROR] node_modules not found.
    echo Please run npm install in frontend directory first.
    pause
    exit /b 1
)

echo [INFO] Starting frontend service...
echo [INFO] Frontend: http://127.0.0.1:5173
npm run dev

endlocal
