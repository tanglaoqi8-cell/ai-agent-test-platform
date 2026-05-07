@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "BACKEND_SCRIPT=%SCRIPT_DIR%start-backend.bat"
set "FRONTEND_SCRIPT=%SCRIPT_DIR%start-frontend.bat"

if not exist "%BACKEND_SCRIPT%" (
    echo [ERROR] start-backend.bat not found.
    pause
    exit /b 1
)

if not exist "%FRONTEND_SCRIPT%" (
    echo [ERROR] start-frontend.bat not found.
    pause
    exit /b 1
)

echo [INFO] Starting AI Test Platform...
start "AI Test Backend" cmd /k call "%BACKEND_SCRIPT%"
start "AI Test Frontend" cmd /k call "%FRONTEND_SCRIPT%"

echo.
echo [INFO] Backend docs: http://127.0.0.1:8000/docs
echo [INFO] Frontend: http://127.0.0.1:5173
echo.
echo [INFO] If the browser does not open automatically, open the URLs manually.
echo.

endlocal
