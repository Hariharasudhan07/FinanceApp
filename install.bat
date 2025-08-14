@echo off
REM FinanceApp Installation Script for Windows
REM This script automates the installation and setup of FinanceApp

echo 🚀 FinanceApp Installation Script
echo ==================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.12 or higher first.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2^>nul') do set PYTHON_VERSION=%%i

echo ✅ Python %PYTHON_VERSION% detected

REM Check if uv is available
uv --version >nul 2>&1
if errorlevel 1 (
    echo ℹ️  uv not found, will use pip instead
    set USE_UV=false
) else (
    echo ✅ uv package manager detected
    set USE_UV=true
)

REM Create virtual environment if using pip
if "%USE_UV%"=="false" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment created and activated
)

REM Install dependencies
echo 📥 Installing dependencies...
if "%USE_UV%"=="true" (
    uv sync
) else (
    pip install -r requirements.txt
)
echo ✅ Dependencies installed

REM Download spaCy model
echo 🧠 Downloading spaCy language model...
if "%USE_UV%"=="true" (
    uv run python -m spacy download en_core_web_lg
) else (
    python -m spacy download en_core_web_lg
)
echo ✅ spaCy model downloaded

REM Test the installation
echo 🧪 Testing the installation...
if "%USE_UV%"=="true" (
    uv run python -c "import fastapi, spacy; print('✅ All imports successful')"
) else (
    python -c "import fastapi, spacy; print('✅ All imports successful')"
)

echo.
echo 🎉 FinanceApp installation completed successfully!
echo.
echo To start the application:
if "%USE_UV%"=="true" (
    echo   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) else (
    echo   venv\Scripts\activate.bat
    echo   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
)
echo.
echo Then visit: http://localhost:8000/docs for the API documentation
echo.
pause
