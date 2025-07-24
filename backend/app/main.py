"""
Main FastAPI application for ElmerFEM Educational Platform
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import simulations
from .config.settings import settings
from .jobs.launcher import JobLauncher
from .jobs.store import InMemoryJobStore, JobStore
from .services.docker_wrapper import DockerWrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Global instances for dependency injection
job_store: JobStore = InMemoryJobStore()
docker_wrapper: DockerWrapper = DockerWrapper()
job_launcher: JobLauncher = JobLauncher(job_store, docker_wrapper)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    logger.info("Starting ElmerFEM Educational Platform API")
    
    # Check Docker and Elmer availability
    if await docker_wrapper.check_elmer_health():
        logger.info("Elmer container is healthy")
        version = await docker_wrapper.test_elmer_version()
        if version:
            logger.info(f"Elmer version: {version}")
    else:
        logger.warning("Elmer container is not healthy - some features may not work")
    
    # Create workspace directory
    settings.get_workspace_path()
    logger.info(f"Workspace directory: {settings.workspace_base_dir}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ElmerFEM Educational Platform API")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    app = FastAPI(
        title=settings.app_name,
        description="Backend API for the ElmerFEM educational web platform",
        version=settings.app_version,
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(simulations.router)
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": settings.app_name,
            "version": settings.app_version,
            "status": "running"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint for Docker health checks"""
        # Check if Elmer is available
        elmer_healthy = await docker_wrapper.check_elmer_health()
        
        return {
            "status": "healthy",
            "elmer_available": elmer_healthy,
            "active_jobs": await job_store.get_active_job_count()
        }
    
    @app.get("/api/materials")
    async def get_materials():
        """Get available materials for simulations"""
        # This will be properly implemented in Task 6
        return {
            "materials": [
                {
                    "id": 1,
                    "name": "Steel",
                    "properties": {
                        "E": 210e9,  # Young's Modulus (Pa)
                        "nu": 0.3,   # Poisson's Ratio
                        "rho": 7850, # Density (kg/m³)
                        "k": 50      # Thermal Conductivity (W/mK)
                    }
                },
                {
                    "id": 2,
                    "name": "Aluminum",
                    "properties": {
                        "E": 70e9,
                        "nu": 0.33,
                        "rho": 2700,
                        "k": 237
                    }
                },
                {
                    "id": 3,
                    "name": "Copper",
                    "properties": {
                        "E": 110e9,
                        "nu": 0.34,
                        "rho": 8960,
                        "k": 401
                    }
                }
            ]
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 