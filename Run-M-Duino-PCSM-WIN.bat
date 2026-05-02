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
  echo Creating .venv...
  %PYTHON_CMD% -m venv .venv
)

call ".venv\Scripts\activate.bat"
echo Installing or repairing dependencies...
python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-build-isolation -e .
python -m pip install -r backend\requirements.txt
if not exist "node_modules" npm install

echo Launching M-Duino-PCSM...
npm run dev
