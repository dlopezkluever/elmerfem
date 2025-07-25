# ElmerFEM Educational Web Platform

This document describes the educational web platform built on top of ElmerFEM to provide an accessible, student-friendly interface for learning Finite Element Analysis (FEA).

## Overview

The ElmerFEM Educational Web Platform consists of three main components:

- **Frontend**: React-based web interface with TypeScript and Vite
- **Backend**: FastAPI-based REST API for simulation management
- **ElmerFEM**: Containerized ElmerFEM solver for computational engine

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │    Backend      │    │   ElmerFEM      │
│  (React + TS)   │◄──►│  (FastAPI)      │◄──►│   Container     │
│  Port: 5173     │    │  Port: 8000     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                     ┌─────────────────┐
                     │   Shared        │
                     │   Workspace     │
                     │   Volume        │
                     └─────────────────┘
```

## Prerequisites

- **Docker** and **Docker Compose** (Required)
- **Node.js 20.11+** and **pnpm** (For local development)
- **Make** (Optional, for convenience commands)

## Quick Start

### 1. Clone and Setup

```bash
# The web platform is integrated into the main ElmerFEM repository
cd elmerfem

# View available commands
make help
```

### 2. Start the Platform

```bash
# Build and start all services
make build
make up

# Or in one command
make dev-setup
```

### 3. Access the Platform

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### 4. Verify Installation

```bash
# Check service status
make status

# View logs
make logs

# Test backend health
curl http://localhost:8000/health

# Test ElmerSolver
make elmer-shell
# Inside container: ElmerSolver --version
```

## Development Commands

### Docker Compose Management

```bash
# Build all images
make build

# Start services
make up

# Stop services and cleanup
make down

# View service status
make status

# Follow logs
make logs

# Restart all services
make restart

# Complete cleanup
make clean
```

### Container Access

```bash
# Backend container shell
make shell

# ElmerFEM container shell
make elmer-shell
```

### Direct Docker Compose Commands

```bash
# If make is not available
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down -v
```

## Development Workflow

### Frontend Development

```bash
# The frontend runs in development mode with hot reload
# Changes to files in frontend/ are automatically reflected

# Install dependencies locally (optional)
cd frontend
npm install -g pnpm
pnpm install

# Run local development server (alternative to Docker)
pnpm dev
```

### Backend Development

```bash
# The backend runs with auto-reload in the container
# Changes to files in backend/ trigger automatic restart

# Access backend container for debugging
make shell

# Install dependencies locally (optional)
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run local development server (alternative to Docker)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ElmerFEM Integration

```bash
# Access ElmerFEM container
make elmer-shell

# Shared workspace is mounted at /usr/src/elmerfem/work
# Backend can write SIF files here for ElmerSolver to process
# Results are accessible to both backend and ElmerFEM containers
```

## Project Structure

```
elmerfem/
├── frontend/                 # React frontend application
│   ├── src/                 # Source code
│   ├── public/              # Static assets
│   ├── package.json         # Dependencies and scripts
│   ├── vite.config.ts       # Vite configuration
│   └── tsconfig.json        # TypeScript configuration
│
├── backend/                 # FastAPI backend application
│   ├── app/                 # Application code
│   │   ├── main.py          # FastAPI app entry point
│   │   └── __init__.py      # Package marker
│   ├── requirements.txt     # Python dependencies
│   ├── pyproject.toml       # Poetry configuration
│   ├── Dockerfile           # Container configuration
│   └── README.md            # Backend documentation
│
├── docker/                  # ElmerFEM Docker configurations
│   └── elmer.dockerfile     # ElmerFEM container build
│
├── docker-compose.yml       # Multi-service orchestration
├── Makefile                 # Development commands
├── pnpm-workspace.yaml      # Workspace configuration
└── README-WebPlatform.md    # This documentation
```

## Health Checks

The platform includes automated health checks:

### Backend Health Check
- **Endpoint**: `GET http://localhost:8000/health`
- **Interval**: 30 seconds
- **Expected Response**: `{"status": "healthy"}`

### ElmerFEM Health Check
- **Command**: `ElmerSolver --version`
- **Interval**: 1 minute
- **Expected**: Version string output

### Monitoring Service Health

```bash
# View health status
docker compose ps

# Should show STATE as "healthy" for backend and elmer services
# Frontend service doesn't have health check (normal Node.js behavior)
```

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker is running
docker --version
docker compose --version

# Check for port conflicts
netstat -tulpn | grep -E ':(5173|8000)'

# View detailed logs
make logs
```

#### Frontend Not Loading
```bash
# Check frontend container logs
docker compose logs frontend

# Verify Node.js and pnpm installation
docker compose exec frontend node --version
docker compose exec frontend pnpm --version
```

#### Backend API Errors
```bash
# Check backend health
curl http://localhost:8000/health

# View backend logs
docker compose logs backend

# Access backend container for debugging
make shell
```

#### ElmerSolver Issues
```bash
# Access ElmerFEM container
make elmer-shell

# Test ElmerSolver
ElmerSolver --version

# Check workspace volume
ls -la /usr/src/elmerfem/work
```

### Performance Issues

#### Slow Container Startup
- Increase Docker memory allocation (recommended: 4GB+)
- Use Docker BuildKit for faster builds: `export DOCKER_BUILDKIT=1`

#### Hot Reload Not Working
- Ensure proper volume mounts in docker-compose.yml
- Check file permissions if on Windows/WSL

### Network Issues

#### Service Communication Problems
```bash
# Check custom network
docker network ls | grep simnet

# Test inter-service communication
docker compose exec frontend ping backend
docker compose exec backend ping elmer
```

## Security Considerations

### Development Environment
- CORS is configured for development (frontend origin only)
- Health check endpoints are publicly accessible
- No authentication implemented (suitable for local development)

### Production Deployment
This setup is designed for **local development and educational use**. For production deployment, consider:
- Adding authentication and authorization
- Implementing HTTPS/TLS
- Restricting CORS origins
- Adding rate limiting
- Implementing proper logging and monitoring

## Contributing

### Code Standards
- **Frontend**: Follow TypeScript and React best practices
- **Backend**: Follow PEP 8 and FastAPI conventions
- **Documentation**: Update this README when adding features

### Testing
```bash
# Frontend tests (when implemented)
cd frontend && pnpm test

# Backend tests (when implemented)
cd backend && poetry run pytest
```

### Pre-commit Hooks
The project includes pre-commit hooks for code formatting:
- **Frontend**: ESLint, Prettier
- **Backend**: Black, Ruff, isort

## Educational Goals

This platform is designed to:
1. **Lower the barrier to entry** for FEA learning
2. **Provide guided workflows** for common simulation types
3. **Offer immediate visual feedback** on simulation results
4. **Maintain computational accuracy** while hiding complexity

## Next Steps

After completing the basic setup, the platform will be extended with:
- Pre-built simulation templates
- Material library with common materials
- Real-time progress monitoring
- 3D result visualization
- Input validation and error handling

## Support

For issues related to:
- **ElmerFEM core**: Refer to main ElmerFEM documentation
- **Web platform**: Check this documentation and logs
- **Development setup**: Use the troubleshooting section above 