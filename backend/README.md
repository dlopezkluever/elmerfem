# ElmerFEM Educational Platform - Backend API

This is the backend API service for the ElmerFEM Educational Platform, providing REST endpoints for simulation job management and orchestration.

## Architecture

The backend is built with FastAPI and follows a modular architecture:

```
backend/
├── app/
│   ├── api/           # REST API endpoints
│   ├── config/        # Configuration and settings
│   ├── jobs/          # Job management and execution
│   ├── models/        # Data models and DTOs
│   ├── services/      # External service integrations
│   └── main.py        # Application entry point
├── tests/             # Test suite
├── pyproject.toml     # Poetry configuration
└── Dockerfile         # Container configuration
```

## Features

- **RESTful API** for simulation management
- **Asynchronous job execution** using asyncio
- **Docker integration** for ElmerFEM solver execution
- **In-memory job store** (Redis support planned)
- **Real-time progress tracking** (WebSocket support planned)
- **Comprehensive error handling and logging**
- **Type-safe with Pydantic v2**
- **100% async/await throughout**

## API Endpoints

### Health & Status

- `GET /` - Root endpoint
- `GET /health` - Health check with Elmer availability status

### Simulations

- `POST /api/simulations` - Create new simulation job
- `GET /api/simulations` - List all simulations (with filtering)
- `GET /api/simulations/{id}/status` - Get simulation status
- `GET /api/simulations/{id}/result` - Get simulation results
- `GET /api/simulations/{id}/logs` - Download simulation logs
- `GET /api/simulations/{id}/files/{filename}` - Download result files
- `DELETE /api/simulations/{id}` - Cancel running simulation

### Materials (Placeholder)

- `GET /api/materials` - Get available materials

## Development Setup

### Prerequisites

- Python 3.11+
- Poetry
- Docker and Docker Compose
- Make (optional)

### Installation

1. Install dependencies:
```bash
cd backend
poetry install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the development server:
```bash
poetry run python -m app.main
```

Or using uvicorn directly:
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Configuration

The application uses environment variables for configuration with the prefix `ELMERFEM_`:

- `ELMERFEM_DEBUG` - Enable debug mode (default: false)
- `ELMERFEM_WORKSPACE_BASE_DIR` - Base directory for simulation workspaces (default: /workspace)
- `ELMERFEM_DOCKER_COMPOSE_PROJECT` - Docker Compose project name (default: elmerfem)
- `ELMERFEM_ELMER_CONTAINER_NAME` - Elmer container name (default: elmer)
- `ELMERFEM_JOB_TIMEOUT_SECONDS` - Job execution timeout (default: 3600)
- `ELMERFEM_MAX_CONCURRENT_JOBS` - Maximum concurrent jobs (default: 5)
- `ELMERFEM_REDIS_URL` - Redis connection URL (optional)

## Testing

Run the test suite:
```bash
poetry run pytest
```

Run with coverage:
```bash
poetry run pytest --cov=app --cov-report=html
```

Run specific test categories:
```bash
poetry run pytest -m unit        # Unit tests only
poetry run pytest -m integration # Integration tests only
poetry run pytest -m "not slow"  # Skip slow tests
```

## Docker Deployment

Build and run with Docker Compose:
```bash
# From project root
docker compose up backend
```

The backend service will be available at `http://localhost:8000`.

## API Usage Examples

### Create a Simulation

```bash
curl -X POST http://localhost:8000/api/simulations \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_type": "heat_transfer",
    "geometry": {"type": "rectangle", "width": 1.0, "height": 1.0},
    "material_id": 1,
    "boundary_conditions": [
      {"type": "temperature", "value": 100.0, "location": "left"},
      {"type": "temperature", "value": 0.0, "location": "right"}
    ],
    "mesh_density": 2.0
  }'
```

### Check Simulation Status

```bash
curl http://localhost:8000/api/simulations/{job_id}/status
```

### Download Results

```bash
curl http://localhost:8000/api/simulations/{job_id}/files/case.vtu \
  -o results.vtu
```

## Architecture Details

### Job Execution Flow

1. Client sends simulation parameters to `POST /api/simulations`
2. API validates parameters and creates job record
3. Job launcher creates workspace directory
4. SIF file is generated (placeholder - Task 4)
5. ElmerSolver executes in Docker container
6. Progress is monitored (to be enhanced in Task 9)
7. Results are collected and stored
8. Client retrieves results via API

### Key Components

- **JobStore**: Abstract interface for job persistence
- **InMemoryJobStore**: Current implementation using dictionaries
- **JobLauncher**: Manages async job execution
- **DockerWrapper**: Handles Docker Compose interactions
- **SimulationJob**: Core job model with all metadata

### Error Handling

- Input validation with Pydantic
- HTTP exceptions with appropriate status codes
- Comprehensive logging throughout
- Graceful handling of Docker failures
- Job timeout protection

## Future Enhancements

- Redis-based job store for persistence
- WebSocket support for real-time updates
- Mesh generation integration
- Advanced queue management
- Result caching
- Authentication and authorization
- Rate limiting
- Metrics and monitoring

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Run linters before committing:
   ```bash
   poetry run black app tests
   poetry run isort app tests
   poetry run ruff app tests
   poetry run mypy app
   ```

## License

[License information here] 