"""
Manual test script for WebSocket progress streaming

Run this script to test the WebSocket implementation:
1. First, ensure the backend is running
2. Run this script: python test_websocket_manual.py
3. The script will simulate a job and connect via WebSocket to receive progress updates
"""

import asyncio
import json
import logging
import sys
from uuid import uuid4
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import websockets
from app.models import SimulationJob, SimulationParamsDTO, JobStatus, SimulationType
from app.jobs.store import InMemoryJobStore
from app.api.v1.websocket import get_connection_manager, parse_progress_line

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def simulate_progress_updates(simulation_id: str, connection_manager):
    """Simulate progress updates for testing"""
    progress_lines = [
        "PROGRESS:0:Initializing simulation",
        "PROGRESS:10:Loading mesh file",
        "PROGRESS:25:Assembling system matrix",
        "PROGRESS:50:Solving linear system",
        "PROGRESS:75:Computing results",
        "PROGRESS:90:Writing output files",
        "PROGRESS:100:Simulation complete"
    ]
    
    for line in progress_lines:
        progress_data = parse_progress_line(line)
        if progress_data:
            await connection_manager.send_progress(simulation_id, progress_data)
            logger.info(f"Sent progress: {progress_data}")
            await asyncio.sleep(0.5)  # Simulate time between updates


async def websocket_client(simulation_id: str):
    """WebSocket client to receive progress updates"""
    uri = f"ws://localhost:8000/api/v1/ws/simulations/{simulation_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected to WebSocket at {uri}")
            
            # Receive messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    logger.info(f"Received: {data}")
                    
                    # Check if simulation is complete
                    if (data.get("type") == "progress" and 
                        data.get("data", {}).get("pct") == 100):
                        logger.info("Simulation complete!")
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning("No message received in 10 seconds")
                    break
                    
    except Exception as e:
        logger.error(f"WebSocket client error: {e}")


async def test_websocket_progress():
    """Test the WebSocket progress streaming"""
    # Create a test job
    job_store = InMemoryJobStore()
    job_id = uuid4()
    
    job = SimulationJob(
        id=job_id,
        status=JobStatus.RUNNING,
        simulation_type=SimulationType.HEAT_CONDUCTION,
        params=SimulationParamsDTO(
            simulation_type=SimulationType.HEAT_CONDUCTION,
            geometry_type="rectangle",
            material="steel",
            mesh_density=0.5,
            boundary_conditions={}
        ),
        output_dir=Path("/tmp/test_output")
    )
    
    await job_store.create(job)
    logger.info(f"Created test job: {job_id}")
    
    # Get connection manager
    connection_manager = get_connection_manager()
    
    # Start client and progress simulator tasks
    client_task = asyncio.create_task(websocket_client(str(job_id)))
    
    # Give client time to connect
    await asyncio.sleep(1)
    
    # Start sending progress updates
    progress_task = asyncio.create_task(
        simulate_progress_updates(str(job_id), connection_manager)
    )
    
    # Wait for both tasks to complete
    await asyncio.gather(client_task, progress_task)
    
    # Update job status
    job.status = JobStatus.COMPLETED
    await job_store.update(job_id, job)
    
    logger.info("Test completed successfully!")


async def test_progress_line_parsing():
    """Test the progress line parsing function"""
    test_lines = [
        "PROGRESS:0:Starting simulation",
        "PROGRESS:50:Half way there",
        "PROGRESS:100:Done",
        "Not a progress line",
        "PROGRESS:invalid:Should fail",
        "PROGRESS:25:Multi:colon:message"
    ]
    
    logger.info("Testing progress line parsing:")
    for line in test_lines:
        result = parse_progress_line(line)
        logger.info(f"  '{line}' -> {result}")


if __name__ == "__main__":
    # First test parsing
    asyncio.run(test_progress_line_parsing())
    
    print("\nNOTE: Before running the WebSocket test, ensure the backend is running:")
    print("  cd backend && python -m uvicorn app.main:app --reload")
    print("\nPress Enter to continue with WebSocket test...")
    input()
    
    # Then test WebSocket
    asyncio.run(test_websocket_progress()) 