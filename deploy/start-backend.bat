@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"

if not exist "%BACKEND_DIR%" (
    echo [ERROR] backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] backend virtual environment not found.
    echo Please create backend\.venv and install dependencies first.
    pause
    exit /b 1
)

echo [INFO] Starting backend service...
echo [INFO] Backend docs: http://127.0.0.1:8000/docs
"%PYTHON_EXE%" -m uvicorn app.main:app --reload

endlocal
