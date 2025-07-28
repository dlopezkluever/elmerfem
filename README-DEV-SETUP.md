# ElmerFEM Development Setup Guide

This guide explains how to run the ElmerFEM Educational Platform with the backend in Docker (for full mesh generation) and frontend in development mode.

## Prerequisites

1. **Docker Desktop** must be running
2. **Node.js** and **npm** installed
3. **Python 3.11+** (for running tests)

## Architecture

- **Backend**: Runs in Docker with:
  - Full Fortran mesh generation (compiled for Linux)
  - Redis for job management
  - ElmerSolver container
  - WebSocket support
- **Frontend**: Runs locally in dev mode (Vite) for hot reloading

## Quick Start

### 1. Start Docker Desktop
Make sure Docker Desktop is running before proceeding.

### 2. Start Backend Services

```powershell
# From project root
.\start-dev.ps1
```

Or manually:
```powershell
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d redis elmer backend
```

This starts:
- Redis on `localhost:6379`
- Backend API on `http://localhost:8000`
- Elmer solver (internal)

### 3. Start Frontend Development Server

In a new terminal:
```powershell
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Testing the Setup

### Basic Test
```powershell
cd backend
pip install websocket-client
python test_docker_backend.py
```

This tests:
- Health endpoints
- Materials API
- Docker access
- Full simulation pipeline with WebSocket progress

### Manual Testing
1. Open `http://localhost:5173`
2. Navigate to Simulation page
3. Create a heat transfer simulation
4. Watch real-time progress updates

## Key Features Working

- ✅ Fortran mesh generation (Linux binary in Docker)
- ✅ Redis job management with pub/sub
- ✅ ElmerSolver execution
- ✅ WebSocket progress streaming
- ✅ VTU to JSON conversion
- ✅ Stage-based progress (0-100%)

## Troubleshooting

### Docker not running
```
error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/...
```
**Solution**: Start Docker Desktop

### Port already in use
```
bind: address already in use
```
**Solution**: 
```powershell
# Find process using port
netstat -ano | findstr :8000
# Kill process
taskkill /PID <PID> /F
```

### Backend can't connect to Redis
Check Redis is running:
```powershell
docker-compose ps redis
```

### Mesh generation fails
Check backend logs:
```powershell
docker-compose logs -f backend
```

## Development Workflow

1. **Backend changes**: Save files → Docker auto-reloads
2. **Frontend changes**: Save files → Vite hot-reloads
3. **View logs**: `docker-compose logs -f backend`
4. **Restart backend**: `docker-compose restart backend`
5. **Stop everything**: `docker-compose down`

## Why This Setup?

- **Fortran mesh library** is compiled for Linux, only works in Docker
- **Frontend dev mode** allows instant hot reloading
- **Redis in Docker** provides proper job management
- **ElmerSolver** runs in its own container as designed

This gives us the best of both worlds: full backend functionality with rapid frontend development! 