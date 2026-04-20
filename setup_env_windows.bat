@echo off
setlocal

echo 🔍 Detecting Python...

REM Try Python 3.12 via py launcher
py -3.12 --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_BIN=py -3.12
    goto :found
)

REM Fallback: any Python via py launcher
py --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_BIN=py
    goto :found
)

REM Final fallback: plain python command
python --version >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_BIN=python
    goto :found
)

echo ❌ Python not found. Please install Python.
exit /b 1

:found
echo 🐍 Using:
%PYTHON_BIN% --version

REM Create venv if needed
if not exist .venv (
    echo 📦 Creating virtual environment...
    %PYTHON_BIN% -m venv .venv
) else (
    echo ✅ Virtual environment already exists.
)

echo ⚡ Activating virtual environment...
call .venv\Scripts\activate.bat

echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

if exist requirements.txt (
    echo 📥 Installing dependencies...
    python -m pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt not found!
)

echo 🎉 Setup complete!
echo To activate later, run:
echo .venv\Scripts\activate.bat

endlocal