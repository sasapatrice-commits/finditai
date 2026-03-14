@echo off
@chcp 65001 >nul
setlocal enabledelayedexpansion

REM make sure we run from the directory that contains this script
pushd "%~dp0" 2>nul || (
    echo [ERROR] unable to change to script directory
    pause
    exit /b 1
)

echo [START] Setting up FindIt AI Lost-and-Found System
echo ==============================================

REM -----------------------------------------------------------------
REM prerequisites
REM -----------------------------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.8+ first.
    goto :error
)

REM verify Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo Detected: %PYVER%

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js 16+ first.
    goto :error
)

REM verify Node version
for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODEVER=%%i
echo Detected: %NODEVER%

echo [OK] Prerequisites check passed

REM -----------------------------------------------------------------
REM backend
REM -----------------------------------------------------------------
echo.
echo [PACKAGE] Setting up backend...
pushd "%~dp0backend" || goto :error

echo Creating Python virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies
    popd
    goto :error
)

echo [OK] Backend setup complete
popd

REM -----------------------------------------------------------------
REM frontend
REM -----------------------------------------------------------------
echo.
echo [SETUP] Setting up frontend...
pushd "%~dp0frontend" || goto :error

echo Installing Node.js dependencies...
npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies
    popd
    goto :error
)

echo [OK] Frontend setup complete
popd

REM -----------------------------------------------------------------
REM uploads directory
REM -----------------------------------------------------------------
echo.
echo [DIR] Creating uploads directory...
if not exist "%~dp0uploads" mkdir "%~dp0uploads"

echo.
echo [DONE] Setup complete!
echo.
echo To start the application:
echo    1. Backend: cd backend ^&^& venv\Scripts\activate ^&^& python main.py
echo    2. Frontend: cd frontend ^&^& npm start
echo.
echo Then visit http://localhost:3000 in your browser
echo.
echo To populate with sample data, make a POST request to:
echo    http://localhost:8000/seed-data
echo.

pause
endlocal
exit /b 0

:error
echo.
echo Setup failed - see messages above.
pause
endlocal
exit /b 1