#!/bin/bash

# ScholarNet 2.0 Onboarding Script
# This script helps new team members verify their setup

echo "Welcome to ScholarNet 2.0 Onboarding!"
echo "======================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "Python: $PYTHON_VERSION"
else
    echo "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "Node.js: $NODE_VERSION"
else
    echo "Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "npm: $NPM_VERSION"
else
    echo "npm not found. Please install npm"
    exit 1
fi

# Check git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "Git: $GIT_VERSION"
else
    echo "Git not found. Please install Git"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "Docker: $DOCKER_VERSION"
else
    echo "Docker not found. Please install Docker Desktop"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "Docker Compose: $COMPOSE_VERSION"
else
    echo "Docker Compose not found. Please install Docker Compose"
    exit 1
fi

echo ""
echo "Prerequisites check complete!"
echo ""

# Navigate to project root (one level up from onboarding folder)
cd ..

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt
echo "Python dependencies installed"

# Check if frontend dependencies are installed
if [ ! -d "visual-search-engine/node_modules" ]; then
    echo ""
    echo "Installing frontend dependencies..."
    cd visual-search-engine
    npm install --legacy-peer-deps
    cd ..
    echo "Frontend dependencies installed"
else
    echo "Frontend dependencies already installed"
fi

echo ""
echo "Setting up database infrastructure..."
echo "Make sure Docker Desktop is running, then:"
python3 setup_database.py

echo ""
echo "Setup complete! Here's what to do next:"
echo ""
echo "1. Start the backend (Terminal 1):"
echo "   source venv/bin/activate"
echo "   python3 src/run.py"
echo ""
echo "2. Start the frontend (Terminal 2):"
echo "   cd visual-search-engine"
echo "   npm run dev"
echo ""
echo "3. Open your browser to:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000/docs"
echo ""
echo "4. Test the CRUD endpoints:"
echo "   GET /api/v1/papers - List all papers"
echo "   GET /api/v1/papers/{id} - Get specific paper"
echo "   POST /api/v1/papers - Create new paper"
echo ""
echo "For more details, check the onboarding/ONBOARDING.md file"
echo "For help, check the troubleshooting section in onboarding/ONBOARDING.md"
echo ""
echo "Welcome to the team!"
