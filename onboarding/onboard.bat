@echo off
REM ScholarNet 2.0 Onboarding Script for Windows
REM This script helps new team members verify their setup

echo Welcome to ScholarNet 2.0 Onboarding!
echo ======================================
echo.

REM Check prerequisites
echo Checking prerequisites...
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo Python: %PYTHON_VERSION%
) else (
    echo Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1" %%i in ('node --version') do set NODE_VERSION=%%i
    echo Node.js: %NODE_VERSION%
) else (
    echo Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

REM Check npm
npm --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1" %%i in ('npm --version') do set NPM_VERSION=%%i
    echo npm: %NPM_VERSION%
) else (
    echo npm not found. Please install npm
    pause
    exit /b 1
)

REM Check git
git --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%i in ('git --version') do set GIT_VERSION=%%i
    echo Git: %GIT_VERSION%
) else (
    echo Git not found. Please install Git
    pause
    exit /b 1
)

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%i in ('docker --version') do set DOCKER_VERSION=%%i
    echo Docker: %DOCKER_VERSION%
) else (
    echo Docker not found. Please install Docker Desktop
    pause
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%i in ('docker-compose --version') do set COMPOSE_VERSION=%%i
    echo Docker Compose: %COMPOSE_VERSION%
) else (
    echo Docker Compose not found. Please install Docker Compose
    pause
    exit /b 1
)

echo.
echo Prerequisites check complete!
echo.

REM Navigate to project root (one level up from onboarding folder)
cd ..

REM Check if virtual environment exists
if not exist "venv" (
    echo Setting up Python virtual environment...
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo.
echo Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Python dependencies installed

REM Check if frontend dependencies are installed
if not exist "visual-search-engine\node_modules" (
    echo.
    echo Installing frontend dependencies...
    cd visual-search-engine
    npm install --legacy-peer-deps
    cd ..
    echo Frontend dependencies installed
) else (
    echo Frontend dependencies already installed
)

echo.
echo Setting up database infrastructure...
echo Make sure Docker Desktop is running, then:
python setup_database.py

echo.
echo Setup complete! Here's what to do next:
echo.
echo 1. Start the backend (Command Prompt 1):
echo    venv\Scripts\activate.bat
echo    python src\run.py
echo.
echo 2. Start the frontend (Command Prompt 2):
echo    cd visual-search-engine
echo    npm run dev
echo.
echo 3. Open your browser to:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000/docs
echo.
echo 4. Test the CRUD endpoints:
echo    GET /api/v1/papers - List all papers
echo    GET /api/v1/papers/{id} - Get specific paper
echo    POST /api/v1/papers - Create new paper
echo.
echo For more details, check the onboarding\ONBOARDING.md file
echo For help, check the troubleshooting section in onboarding\ONBOARDING.md
echo.
echo Welcome to the team!
pause
