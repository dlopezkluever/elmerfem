"""
WebSocket endpoints for real-time simulation progress streaming
"""

import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.exceptions import WebSocketException

from ...dependencies import get_job_store_ws
from ...jobs.store import JobStore
from ...models import JobStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for simulation progress"""
    
    def __init__(self):
        # Dictionary mapping simulation_id to set of connected websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Progress queues for each simulation
        self.progress_queues: Dict[str, asyncio.Queue] = {}
        # Tasks for broadcasting progress
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}
        # Last emission time for throttling
        self.last_emission_times: Dict[str, float] = {}
        # Throttle rate: max 5 emissions per second (200ms minimum between emissions)
        self.throttle_interval = 0.2  # 200ms = 5Hz
    
    async def connect(self, websocket: WebSocket, simulation_id: str):
        """Accept a new WebSocket connection for a simulation"""
        await websocket.accept()
        
        if simulation_id not in self.active_connections:
            self.active_connections[simulation_id] = set()
            self.progress_queues[simulation_id] = asyncio.Queue()
            self.last_emission_times[simulation_id] = 0
            
            # Start broadcast task for this simulation if not already running
            if simulation_id not in self.broadcast_tasks or self.broadcast_tasks[simulation_id].done():
                self.broadcast_tasks[simulation_id] = asyncio.create_task(
                    self._broadcast_progress(simulation_id)
                )
        
        self.active_connections[simulation_id].add(websocket)
        logger.info(f"WebSocket connected for simulation {simulation_id}. Total connections: {len(self.active_connections[simulation_id])}")
    
    def disconnect(self, websocket: WebSocket, simulation_id: str):
        """Remove a WebSocket connection"""
        if simulation_id in self.active_connections:
            self.active_connections[simulation_id].discard(websocket)
            logger.info(f"WebSocket disconnected for simulation {simulation_id}. Remaining connections: {len(self.active_connections[simulation_id])}")
            
            # Clean up if no more connections
            if not self.active_connections[simulation_id]:
                del self.active_connections[simulation_id]
                
                # Cancel broadcast task
                if simulation_id in self.broadcast_tasks:
                    self.broadcast_tasks[simulation_id].cancel()
                    del self.broadcast_tasks[simulation_id]
                
                # Clean up queues and timers
                if simulation_id in self.progress_queues:
                    del self.progress_queues[simulation_id]
                if simulation_id in self.last_emission_times:
                    del self.last_emission_times[simulation_id]
    
    async def send_progress(self, simulation_id: str, progress_data: dict):
        """Queue progress data for a simulation"""
        if simulation_id in self.progress_queues:
            await self.progress_queues[simulation_id].put(progress_data)
    
    async def _broadcast_progress(self, simulation_id: str):
        """Broadcast progress updates to all connected clients with throttling"""
        logger.info(f"Starting progress broadcast task for simulation {simulation_id}")
        
        try:
            while simulation_id in self.active_connections:
                try:
                    # Wait for progress data with timeout
                    progress_data = await asyncio.wait_for(
                        self.progress_queues[simulation_id].get(),
                        timeout=1.0
                    )
                    
                    # Apply throttling
                    current_time = time.time()
                    time_since_last = current_time - self.last_emission_times[simulation_id]
                    
                    if time_since_last < self.throttle_interval:
                        # Too soon, wait before sending
                        await asyncio.sleep(self.throttle_interval - time_since_last)
                    
                    # Update last emission time
                    self.last_emission_times[simulation_id] = time.time()
                    
                    # Broadcast to all connected clients
                    disconnected = set()
                    for websocket in self.active_connections[simulation_id]:
                        try:
                            await websocket.send_json(progress_data)
                        except Exception as e:
                            logger.warning(f"Failed to send to websocket: {e}")
                            disconnected.add(websocket)
                    
                    # Remove disconnected websockets
                    for ws in disconnected:
                        self.disconnect(ws, simulation_id)
                        
                except asyncio.TimeoutError:
                    # No new progress, continue loop
                    continue
                except Exception as e:
                    logger.error(f"Error in broadcast loop for simulation {simulation_id}: {e}")
                    
        except asyncio.CancelledError:
            logger.info(f"Broadcast task cancelled for simulation {simulation_id}")
        except Exception as e:
            logger.error(f"Unexpected error in broadcast task for simulation {simulation_id}: {e}")
        finally:
            logger.info(f"Broadcast task ended for simulation {simulation_id}")


# Global connection manager instance
manager = ConnectionManager()


def parse_progress_line(line: str) -> Optional[Dict[str, any]]:
    """
    Parse a progress line from ElmerSolver output
    
    Expected format: PROGRESS:<percentage>:<message>
    Example: PROGRESS:25:Assembling system matrix
    
    Returns:
        Dictionary with 'pct' and 'msg' fields, or None if not a progress line
    """
    if not line.startswith("PROGRESS:"):
        return None
    
    try:
        parts = line.strip().split(":", 2)
        if len(parts) >= 3:
            _, pct_str, msg = parts
            pct = int(pct_str)
            
            return {
                "type": "progress",
                "data": {
                    "pct": pct,
                    "msg": msg,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse progress line '{line}': {e}")
    
    return None


@router.websocket("/simulations/{simulation_id}")
async def websocket_simulation_progress(
    websocket: WebSocket,
    simulation_id: str,
    job_store: JobStore = Depends(get_job_store_ws)
):
    """
    WebSocket endpoint for real-time simulation progress updates
    
    Clients connect to this endpoint to receive progress updates for a specific simulation.
    Updates are throttled to a maximum of 5Hz to prevent overwhelming clients.
    
    Message format:
    {
        "type": "progress",
        "data": {
            "pct": 50,
            "msg": "Solving linear system",
            "timestamp": "2024-01-15T10:30:45.123456"
        }
    }
    
    Or for status updates:
    {
        "type": "status",
        "data": {
            "status": "completed",
            "timestamp": "2024-01-15T10:31:00.123456"
        }
    }
    """
    try:
        # Validate simulation exists
        try:
            job_id = UUID(simulation_id)
            job = await job_store.get(job_id)
            if not job:
                await websocket.close(code=4004, reason="Simulation not found")
                return
        except ValueError:
            await websocket.close(code=4003, reason="Invalid simulation ID format")
            return
        
        # Connect this websocket
        await manager.connect(websocket, simulation_id)
        
        # Send initial status
        await manager.send_progress(simulation_id, {
            "type": "status",
            "data": {
                "status": job.status.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Keep connection alive and handle incoming messages (if any)
        try:
            while True:
                # We don't expect client messages, but we need to keep the connection alive
                # and detect disconnections
                message = await websocket.receive_text()
                logger.debug(f"Received message from client: {message}")
                
                # Could implement client-side commands here if needed
                # For now, just echo back a confirmation
                await websocket.send_json({
                    "type": "echo",
                    "data": {"message": message}
                })
                
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from simulation {simulation_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error for simulation {simulation_id}: {e}")
    finally:
        manager.disconnect(websocket, simulation_id)


# Export for use in other modules
def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return manager 