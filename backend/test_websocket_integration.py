"""
Integration test for WebSocket progress streaming

This test verifies the WebSocket implementation by:
1. Starting the backend server
2. Creating a simulation job
3. Connecting via WebSocket
4. Verifying progress messages are received
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx
import websockets

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"


async def create_simulation_job():
    """Create a simulation job via the API"""
    async with httpx.AsyncClient() as client:
        # First, get available materials
        response = await client.get(f"{BASE_URL}/api/materials")
        if response.status_code != 200:
            logger.error(f"Failed to get materials: {response.text}")
            return None
        
        materials = response.json()["materials"]
        if not materials:
            logger.error("No materials available")
            return None
        
        # Create a simple heat conduction simulation
        simulation_data = {
            "simulation_type": "heat_conduction",
            "geometry": {
                "type": "rectangle",
                "dimensions": {
                    "length": 1.0,
                    "width": 0.5
                }
            },
            "material": materials[0]["name"],  # Use first available material
            "mesh_density": 5,  # Medium density
            "boundary_conditions": {
                "left": {"type": "temperature", "value": 100},
                "right": {"type": "temperature", "value": 0},
                "top": {"type": "insulated"},
                "bottom": {"type": "insulated"}
            },
            "solver_settings": {
                "max_iterations": 1000,
                "convergence_tolerance": 1e-6
            }
        }
        
        logger.info(f"Creating simulation with data: {json.dumps(simulation_data, indent=2)}")
        
        # Submit simulation
        response = await client.post(
            f"{BASE_URL}/api/v1/simulations/submit",
            json=simulation_data
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create simulation: {response.text}")
            return None
        
        job_data = response.json()
        job_id = job_data["job_id"]
        logger.info(f"Created simulation job: {job_id}")
        return job_id


async def monitor_websocket_progress(job_id: str, timeout: int = 60):
    """Connect to WebSocket and monitor progress"""
    uri = f"{WS_BASE_URL}/api/v1/ws/simulations/{job_id}"
    
    messages_received = []
    progress_updates = []
    status_updates = []
    
    try:
        logger.info(f"Connecting to WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("WebSocket connected successfully")
            
            start_time = time.time()
            
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    messages_received.append(data)
                    logger.info(f"Received message: {json.dumps(data, indent=2)}")
                    
                    # Categorize message
                    if data.get("type") == "progress":
                        progress_updates.append(data["data"])
                        
                        # Check if complete
                        if data["data"].get("pct") == 100:
                            logger.info("Simulation completed (100% progress)")
                            break
                    
                    elif data.get("type") == "status":
                        status_updates.append(data["data"])
                        
                        # Check if completed/failed
                        status = data["data"].get("status")
                        if status in ["completed", "failed", "cancelled"]:
                            logger.info(f"Simulation finished with status: {status}")
                            break
                    
                    # Check timeout
                    if time.time() - start_time > timeout:
                        logger.warning(f"Timeout reached after {timeout} seconds")
                        break
                        
                except asyncio.TimeoutError:
                    logger.debug("No message received in 5 seconds, continuing...")
                    
                    # Check if job is still running
                    if time.time() - start_time > timeout:
                        logger.warning(f"Overall timeout reached after {timeout} seconds")
                        break
                        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    return {
        "total_messages": len(messages_received),
        "progress_updates": progress_updates,
        "status_updates": status_updates,
        "all_messages": messages_received
    }


async def check_job_status(job_id: str):
    """Check job status via REST API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/simulations/{job_id}/status")
        if response.status_code == 200:
            return response.json()
        return None


async def test_websocket_flow():
    """Test the complete WebSocket flow"""
    logger.info("Starting WebSocket integration test")
    
    # Step 1: Create a simulation job
    job_id = await create_simulation_job()
    if not job_id:
        logger.error("Failed to create simulation job")
        return False
    
    # Wait a moment for job to start
    await asyncio.sleep(2)
    
    # Step 2: Connect via WebSocket and monitor progress
    logger.info(f"Monitoring progress for job {job_id}")
    results = await monitor_websocket_progress(job_id, timeout=120)
    
    # Step 3: Analyze results
    logger.info("\n=== WebSocket Test Results ===")
    logger.info(f"Total messages received: {results['total_messages']}")
    logger.info(f"Progress updates: {len(results['progress_updates'])}")
    logger.info(f"Status updates: {len(results['status_updates'])}")
    
    # Check progress sequence
    if results['progress_updates']:
        logger.info("\nProgress sequence:")
        for update in results['progress_updates']:
            logger.info(f"  {update['pct']}% - {update['msg']}")
    
    # Check for 5Hz throttling (max 5 messages per second)
    if len(results['progress_updates']) > 1:
        timestamps = []
        for msg in results['all_messages']:
            if msg.get('type') == 'progress' and 'timestamp' in msg.get('data', {}):
                timestamps.append(msg['data']['timestamp'])
        
        if len(timestamps) > 1:
            # Calculate time differences
            import dateutil.parser
            parsed_times = [dateutil.parser.parse(ts) for ts in timestamps]
            time_diffs = []
            
            for i in range(1, len(parsed_times)):
                diff = (parsed_times[i] - parsed_times[i-1]).total_seconds()
                time_diffs.append(diff)
            
            min_diff = min(time_diffs) if time_diffs else 0
            avg_diff = sum(time_diffs) / len(time_diffs) if time_diffs else 0
            
            logger.info(f"\nThrottling analysis:")
            logger.info(f"  Minimum time between messages: {min_diff:.3f}s")
            logger.info(f"  Average time between messages: {avg_diff:.3f}s")
            logger.info(f"  Expected minimum (5Hz): 0.2s")
            
            if min_diff >= 0.19:  # Allow small variance
                logger.info("  ✓ 5Hz throttling is working correctly")
            else:
                logger.warning("  ✗ Messages arriving faster than 5Hz limit")
    
    # Step 4: Verify final job status
    await asyncio.sleep(2)
    final_status = await check_job_status(job_id)
    if final_status:
        logger.info(f"\nFinal job status: {final_status}")
    
    # Determine success
    success = (
        results['total_messages'] > 0 and
        (len(results['progress_updates']) > 0 or len(results['status_updates']) > 0)
    )
    
    if success:
        logger.info("\n✅ WebSocket integration test PASSED")
    else:
        logger.error("\n❌ WebSocket integration test FAILED")
    
    return success


async def test_multiple_clients():
    """Test multiple WebSocket clients connecting to same job"""
    logger.info("\n=== Testing Multiple Concurrent Clients ===")
    
    # Create a job
    job_id = await create_simulation_job()
    if not job_id:
        logger.error("Failed to create simulation job")
        return False
    
    await asyncio.sleep(1)
    
    # Connect multiple clients
    async def client_monitor(client_id: int):
        """Monitor progress for a specific client"""
        messages = []
        uri = f"{WS_BASE_URL}/api/v1/ws/simulations/{job_id}"
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Client {client_id} connected")
                
                start_time = time.time()
                while time.time() - start_time < 30:  # 30 second timeout
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)
                        messages.append(data)
                        
                        if data.get("type") == "progress" and data["data"].get("pct") == 100:
                            break
                        if data.get("type") == "status" and data["data"].get("status") in ["completed", "failed"]:
                            break
                            
                    except asyncio.TimeoutError:
                        continue
                        
        except Exception as e:
            logger.error(f"Client {client_id} error: {e}")
        
        logger.info(f"Client {client_id} received {len(messages)} messages")
        return messages
    
    # Run multiple clients concurrently
    results = await asyncio.gather(
        client_monitor(1),
        client_monitor(2),
        client_monitor(3)
    )
    
    # Verify all clients received messages
    success = all(len(msgs) > 0 for msgs in results)
    
    if success:
        logger.info("✅ Multiple clients test PASSED - all clients received messages")
    else:
        logger.error("❌ Multiple clients test FAILED - some clients didn't receive messages")
    
    return success


if __name__ == "__main__":
    print("=" * 60)
    print("WebSocket Integration Test")
    print("=" * 60)
    print("\nPrerequisites:")
    print("1. Backend server must be running (uvicorn app.main:app)")
    print("2. Docker/ElmerFEM container must be available")
    print("3. Redis (optional) for distributed progress relay")
    print("\nPress Enter to start tests...")
    input()
    
    # Install dateutil if needed
    try:
        import dateutil.parser
    except ImportError:
        print("Installing python-dateutil...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dateutil"])
        import dateutil.parser
    
    # Run tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test 1: Basic WebSocket flow
        test1_result = loop.run_until_complete(test_websocket_flow())
        
        # Test 2: Multiple clients
        test2_result = loop.run_until_complete(test_multiple_clients())
        
        print("\n" + "=" * 60)
        print("Test Summary:")
        print(f"  Basic WebSocket Flow: {'PASSED' if test1_result else 'FAILED'}")
        print(f"  Multiple Clients: {'PASSED' if test2_result else 'FAILED'}")
        print("=" * 60)
        
    finally:
        loop.close() 