@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if not %errorlevel%==0 (
    echo Python 3 is required but was not found in PATH.
    exit /b 1
  )
  set "PYTHON_CMD=python"
)

where npm >nul 2>nul
if not %errorlevel%==0 (
  echo npm is required but was not found in PATH.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo M-Duino-PCSM cannot start yet:
  echo  - Missing local virtual environment: run Setup-M-Duino-PCSM-WIN.bat first
  echo.
  echo Recommended fix:
  echo   Setup-M-Duino-PCSM-WIN.bat
  exit /b 1
)

call ".venv\Scripts\activate.bat"

python -c "import flask, serial, mduino_pcsm" >nul 2>nul
if not %errorlevel%==0 (
  echo.
  echo M-Duino-PCSM cannot start yet:
  echo  - Python runtime packages are incomplete: run Setup-M-Duino-PCSM-WIN.bat
  echo.
  echo Recommended fix:
  echo   Setup-M-Duino-PCSM-WIN.bat
  exit /b 1
)

if not exist "node_modules\.bin\vite.cmd" (
  echo Installing frontend dependencies...
  npm install
)

echo Launching M-Duino-PCSM...
npm run dev
