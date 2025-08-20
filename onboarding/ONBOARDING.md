# ScholarNet 2.0 - New Team Member Onboarding

Welcome to the ScholarNet 2.0 team! This guide will help you get up and running quickly.

## Pre-Onboarding Checklist

Before you start, ensure you have:
- [ ] **Python 3.8+** installed
- [ ] **Node.js 18+** installed  
- [ ] **npm** (comes with Node.js)
- [ ] **Git** installed
- [ ] **Docker Desktop** installed and running
- [ ] **Code editor** (VS Code recommended)
- [ ] **Terminal/Command Prompt** access

## Quick Setup (Choose Your OS)

### macOS/Linux Users
```bash
# Clone the repository
git clone <your-repo-url>
cd ScholarSearchV2

# Run the automated setup script
./onboard.sh
```

### Windows Users
```cmd
# Clone the repository
git clone <your-repo-url>
cd ScholarSearchV2

# Run the automated setup script
onboard.bat
```

### Manual Setup (If scripts don't work)
Follow the detailed steps below.

## Database Setup (Required First)

Before running the application, you need to set up the database infrastructure:

### 1. Start Docker Desktop
Make sure Docker Desktop is running on your machine.

### 2. Run Database Setup
```bash
# From the project root
python3 setup_database.py
```

This will:
- PostgreSQL, Redis, and ChromaDB containers started
- Database tables created
- Sample research papers populated
- Python environment set up

## Verification Checklist

After setup, verify everything works:

### Backend Verification
- [ ] Virtual environment created and activated
- [ ] Python dependencies installed
- [ ] Database services running (PostgreSQL, Redis, ChromaDB)
- [ ] FastAPI server starts without errors
- [ ] Health endpoint responds: `http://localhost:8000/health`
- [ ] API docs accessible: `http://localhost:8000/docs`

### Frontend Verification
- [ ] Node.js dependencies installed
- [ ] Next.js dev server starts
- [ ] Frontend loads: `http://localhost:3000`
- [ ] No console errors in browser
- [ ] API connection status shows "Connected"

### API Endpoints Verification
- [ ] **GET /api/v1/papers** - Lists all papers with pagination
- [ ] **GET /api/v1/papers/{id}** - Gets specific paper details
- [ ] **POST /api/v1/papers** - Creates new paper
- [ ] **PUT /api/v1/papers/{id}** - Updates existing paper
- [ ] **DELETE /api/v1/papers/{id}** - Deletes paper
- [ ] **GET /api/v1/chromadb/status** - ChromaDB service status
- [ ] **GET /health** - Overall system health

## Daily Development Workflow

### Starting Your Day
```bash
# Terminal 1: Start Backend
cd ScholarSearchV2
source venv/bin/activate  # Windows: venv\Scripts\activate.bat
python3 src/run.py

# Terminal 2: Start Frontend  
cd ScholarSearchV2/visual-search-engine
npm run dev
```

### Making Changes
1. **Backend Changes**: Save files → auto-reload
2. **Frontend Changes**: Save files → auto-reload
3. **Test Changes**: Refresh browser, check console

### Stopping Services
- **Backend**: `Ctrl+C` in backend terminal
- **Frontend**: `Ctrl+C` in frontend terminal

## Testing Your Changes

### Backend Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test papers endpoint
curl http://localhost:8000/api/v1/papers

# Test specific paper
curl http://localhost:8000/api/v1/papers/1

# Test ChromaDB status
curl http://localhost:8000/api/v1/chromadb/status
```

### Frontend Testing
- Open http://localhost:3000 in your browser
- Check browser console for errors
- Test API connection status
- Navigate between pages

## Current System Architecture

### What's Available Now:
- **PostgreSQL**: Research paper storage with 5 sample papers
- **Redis**: Caching layer for performance
- **ChromaDB**: Vector database service (ready for future search)
- **FastAPI**: RESTful API with CRUD operations
- **Next.js**: Modern React frontend

### What's Coming Soon:
- **Hybrid Search**: BM25 + BERT vectors with multi-stage retrieval
- **Result Fusion**: Reciprocal Rank Fusion (RRF) for combining search results
- **Enhanced Ranking**: Citation boost, recency boost, diversity enhancement

## Troubleshooting

### Common Issues:

#### 1. Docker Not Running
```bash
# Error: "Cannot connect to the Docker daemon"
# Solution: Start Docker Desktop application
```

#### 2. Port Already in Use
```bash
# Error: "Address already in use"
# Solution: Kill existing process or use different port
lsof -ti :8000 | xargs kill -9  # Kill process on port 8000
```

#### 3. Database Connection Failed
```bash
# Error: "Connection refused"
# Solution: Run setup_database.py first
python3 setup_database.py
```

#### 4. Module Not Found
```bash
# Error: "No module named 'redis'"
# Solution: Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### Getting Help:
- Check Docker logs: `docker-compose logs`
- Check backend logs: Look at terminal running `python3 src/run.py`
- Check frontend logs: Look at terminal running `npm run dev`
- Check browser console for frontend errors

## Next Steps

After getting the basic system running:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Test CRUD operations**: Create, read, update, delete papers
3. **Understand the data model**: Check sample papers and relationships
4. **Prepare for search**: The system is ready for hybrid search implementation

## Welcome to the Team!

You now have a **production-ready research paper platform** with:
- Modern FastAPI backend
- Professional PostgreSQL database
- Scalable architecture
- Ready for advanced search features

Happy coding!
