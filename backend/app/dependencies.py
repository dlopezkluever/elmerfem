"""
FastAPI dependency injection providers
"""

import logging
from typing import Optional

from fastapi import Request, WebSocket
import redis.asyncio as redis

from .jobs.store import JobStore, InMemoryJobStore, AsyncRedisJobStore
from .jobs.launcher import JobLauncher
from .services.docker_wrapper import DockerWrapper

logger = logging.getLogger(__name__)

# Singletons for when Redis is not available
_in_memory_store: Optional[InMemoryJobStore] = None
_docker_wrapper: Optional[DockerWrapper] = None
_job_launcher: Optional[JobLauncher] = None


async def get_job_store(request: Request) -> JobStore:
    """Get the appropriate job store based on Redis availability"""
    global _in_memory_store
    
    if hasattr(request.app.state, 'redis_pool') and request.app.state.redis_pool:
        return AsyncRedisJobStore(request.app.state.redis_pool)
    else:
        # Use singleton in-memory store
        if _in_memory_store is None:
            _in_memory_store = InMemoryJobStore()
            logger.info("Created singleton InMemoryJobStore")
        return _in_memory_store


async def get_job_store_ws(websocket: WebSocket) -> JobStore:
    """Get the appropriate job store for WebSocket connections"""
    global _in_memory_store
    
    if hasattr(websocket.app.state, 'redis_pool') and websocket.app.state.redis_pool:
        return AsyncRedisJobStore(websocket.app.state.redis_pool)
    else:
        # Use singleton in-memory store
        if _in_memory_store is None:
            _in_memory_store = InMemoryJobStore()
            logger.info("Created singleton InMemoryJobStore for WebSocket")
        return _in_memory_store


async def get_docker_wrapper() -> DockerWrapper:
    """Get the Docker wrapper instance"""
    global _docker_wrapper
    
    if _docker_wrapper is None:
        _docker_wrapper = DockerWrapper()
    
    return _docker_wrapper


async def get_job_launcher(request: Request) -> JobLauncher:
    """Get the job launcher instance"""
    global _job_launcher
    
    job_store = await get_job_store(request)
    docker_wrapper = await get_docker_wrapper()
    
    # Create new launcher if store type changes
    if _job_launcher is None or _job_launcher.job_store != job_store:
        _job_launcher = JobLauncher(job_store, docker_wrapper)
        logger.info(f"Created JobLauncher with {type(job_store).__name__}")
    
    return _job_launcher 