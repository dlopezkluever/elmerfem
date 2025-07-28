"""
Main FastAPI application for ElmerFEM Educational Platform
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import simulations_router, mesh_router, websocket_router
from .api.v1.websocket import get_connection_manager
from .api.simulations import router as simulations_legacy_router
from .config.settings import settings
from .dependencies import get_docker_wrapper
from .jobs.launcher import JobLauncher
from .jobs.store import InMemoryJobStore, AsyncRedisJobStore, JobStore
from .services.docker_wrapper import DockerWrapper
from .services.materials_service import materials_service
from .services.progress_relay import ProgressRelayService

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Store the connection pool and progress relay globally
redis_pool = None
progress_relay = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    global redis_pool, progress_relay
    
    logger.info("Starting ElmerFEM Educational Platform backend...")
    
    # Initialize Redis connection pool if configured
    if settings.redis_url and (settings.use_redis or os.getenv("USE_REDIS", "").lower() == "true"):
        try:
            logger.info(f"Connecting to Redis at {settings.redis_url}")
            redis_pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=True,
                max_connections=10
            )
            
            # Test the connection
            async with redis.Redis(connection_pool=redis_pool) as r:
                await r.ping()
                logger.info("Redis connection successful")
                
                # Initialize and start progress relay service
                ws_manager = get_connection_manager()
                progress_relay = ProgressRelayService(redis_pool)
                await progress_relay.start()
                logger.info("Progress relay service started")
                
                # Connect WebSocket manager to progress relay
                async def relay_to_websocket(job_id: str, progress_data: dict):
                    await ws_manager.send_progress(job_id, progress_data)
                
                progress_relay.progress_callback = relay_to_websocket
                
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory store.")
            redis_pool = None
            progress_relay = None
    else:
        logger.info("Redis not configured. Using in-memory store.")
    
    # Store redis pool in app state
    app.state.redis_pool = redis_pool
    app.state.progress_relay = progress_relay
    
    yield
    
    # Cleanup
    logger.info("Shutting down ElmerFEM Educational Platform backend...")
    
    # Stop progress relay service
    if progress_relay:
        await progress_relay.stop()
        logger.info("Progress relay service stopped")
    
    # Close Redis connection pool
    if redis_pool:
        await redis_pool.disconnect()
        logger.info("Redis connection pool closed")


# Create FastAPI app
app = FastAPI(
    title="ElmerFEM Educational Platform",
    description="Educational FEM simulation platform with real-time progress tracking",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(simulations_router, prefix="/api/v1")
app.include_router(mesh_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1")
app.include_router(simulations_legacy_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ElmerFEM Educational Platform API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    health_status = {
        "status": "ok",
        "service": "elmerfem-backend", 
        "debug": settings.debug,
    }
    
    # Check Redis connection
    if redis_pool:
        try:
            async with redis.Redis(connection_pool=redis_pool) as r:
                await r.ping()
                health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
    else:
        health_status["redis"] = "not configured"
    
    # Don't check Elmer on every health request - it's too slow
    # Just return the last known status
    health_status["elmer"] = "check /api/elmer-status for detailed status"
    
    return health_status


@app.get("/api/elmer-status") 
async def elmer_status(docker_wrapper: DockerWrapper = Depends(get_docker_wrapper)):
    """Detailed Elmer/Docker status check (may be slow)"""
    try:
        # Use dependency injection to get docker_wrapper
        elmer_available = await docker_wrapper.check_elmer_health()
        return {
            "elmer_available": elmer_available,
            "docker_configured": True,
            "message": "Elmer is available" if elmer_available else "Elmer container is not running"
        }
    except Exception as e:
        logger.error(f"Error checking Elmer status: {e}")
        return {
            "elmer_available": False, 
            "docker_configured": False,
            "error": str(e)
        }


@app.get("/api/materials")
async def get_materials():
    """Get available materials for simulations"""
    try:
        materials = materials_service.get_all_materials()
        return {
            "materials": materials,
            "count": len(materials)
        }
    except FileNotFoundError as e:
        logger.error(f"Materials file not found: {e}")
        raise HTTPException(
            status_code=500,
            detail="Materials database not found. Please ensure materials.json is present."
        )
    except Exception as e:
        logger.error(f"Error loading materials: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load materials: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 