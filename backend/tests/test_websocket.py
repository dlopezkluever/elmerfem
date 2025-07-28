"""
Test WebSocket progress streaming functionality
"""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from uuid import uuid4

from app.main import app
from app.jobs.store import InMemoryJobStore
from app.models import SimulationJob, SimulationParamsDTO, JobStatus, SimulationType
from app.api.v1.websocket import parse_progress_line, ConnectionManager

# Test client
client = TestClient(app)


class TestProgressLineParsing:
    """Test progress line parsing functionality"""
    
    def test_parse_valid_progress_line(self):
        """Test parsing valid PROGRESS lines"""
        line = "PROGRESS:25:Assembling system matrix"
        result = parse_progress_line(line)
        
        assert result is not None
        assert result["type"] == "progress"
        assert result["data"]["pct"] == 25
        assert result["data"]["msg"] == "Assembling system matrix"
        assert "timestamp" in result["data"]
    
    def test_parse_progress_line_with_colons_in_message(self):
        """Test parsing when message contains colons"""
        line = "PROGRESS:50:Solving: Linear system iteration 1:10"
        result = parse_progress_line(line)
        
        assert result is not None
        assert result["data"]["pct"] == 50
        assert result["data"]["msg"] == "Solving: Linear system iteration 1:10"
    
    def test_parse_invalid_progress_lines(self):
        """Test parsing invalid lines returns None"""
        invalid_lines = [
            "Not a progress line",
            "PROGRESS:not_a_number:message",
            "PROGRESS:50",  # Missing message
            "PROGRESS",     # Missing everything
            "",             # Empty line
        ]
        
        for line in invalid_lines:
            assert parse_progress_line(line) is None
    
    def test_parse_boundary_percentage_values(self):
        """Test parsing boundary percentage values"""
        # 0%
        result = parse_progress_line("PROGRESS:0:Starting")
        assert result["data"]["pct"] == 0
        
        # 100%
        result = parse_progress_line("PROGRESS:100:Completed")
        assert result["data"]["pct"] == 100


class TestConnectionManager:
    """Test ConnectionManager functionality"""
    
    @pytest.mark.asyncio
    async def test_connection_manager_lifecycle(self):
        """Test connection manager connect/disconnect lifecycle"""
        manager = ConnectionManager()
        simulation_id = str(uuid4())
        
        # Mock WebSocket
        class MockWebSocket:
            async def accept(self):
                pass
            
            async def send_json(self, data):
                pass
        
        ws = MockWebSocket()
        
        # Connect
        await manager.connect(ws, simulation_id)
        assert simulation_id in manager.active_connections
        assert ws in manager.active_connections[simulation_id]
        assert simulation_id in manager.progress_queues
        
        # Disconnect
        manager.disconnect(ws, simulation_id)
        assert simulation_id not in manager.active_connections
        assert simulation_id not in manager.progress_queues
    
    @pytest.mark.asyncio
    async def test_multiple_connections_same_simulation(self):
        """Test multiple connections to same simulation"""
        manager = ConnectionManager()
        simulation_id = str(uuid4())
        
        class MockWebSocket:
            def __init__(self, id):
                self.id = id
            
            async def accept(self):
                pass
            
            async def send_json(self, data):
                pass
        
        ws1 = MockWebSocket(1)
        ws2 = MockWebSocket(2)
        
        # Connect both
        await manager.connect(ws1, simulation_id)
        await manager.connect(ws2, simulation_id)
        
        assert len(manager.active_connections[simulation_id]) == 2
        
        # Disconnect one
        manager.disconnect(ws1, simulation_id)
        assert len(manager.active_connections[simulation_id]) == 1
        assert ws2 in manager.active_connections[simulation_id]
        
        # Disconnect last one - should clean up
        manager.disconnect(ws2, simulation_id)
        assert simulation_id not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_send_progress_throttling(self):
        """Test that progress updates are throttled to 5Hz"""
        manager = ConnectionManager()
        simulation_id = str(uuid4())
        received_messages = []
        
        class MockWebSocket:
            async def accept(self):
                pass
            
            async def send_json(self, data):
                received_messages.append({
                    'time': asyncio.get_event_loop().time(),
                    'data': data
                })
        
        ws = MockWebSocket()
        await manager.connect(ws, simulation_id)
        
        # Send multiple progress updates rapidly
        for i in range(10):
            await manager.send_progress(simulation_id, {
                "type": "progress",
                "data": {"pct": i * 10, "msg": f"Step {i}"}
            })
        
        # Wait for broadcast task to process
        await asyncio.sleep(2.5)  # Should take at least 2 seconds for 10 messages at 5Hz
        
        # Check throttling
        assert len(received_messages) == 10
        
        # Check time between messages (should be at least 200ms)
        for i in range(1, len(received_messages)):
            time_diff = received_messages[i]['time'] - received_messages[i-1]['time']
            assert time_diff >= 0.19  # Allow small tolerance


@pytest.mark.asyncio
class TestWebSocketEndpoint:
    """Test the WebSocket endpoint integration"""
    
    async def test_websocket_invalid_simulation_id(self):
        """Test WebSocket connection with invalid simulation ID"""
        with client.websocket_connect("/api/v1/ws/simulations/invalid-uuid") as websocket:
            # Should close with error
            try:
                websocket.receive_text()
                assert False, "Expected WebSocket to close"
            except Exception as e:
                # WebSocket should be closed
                pass
    
    async def test_websocket_nonexistent_simulation(self):
        """Test WebSocket connection with non-existent simulation"""
        fake_id = str(uuid4())
        with client.websocket_connect(f"/api/v1/ws/simulations/{fake_id}") as websocket:
            # Should close because simulation doesn't exist
            try:
                websocket.receive_text()
                assert False, "Expected WebSocket to close"
            except Exception as e:
                # WebSocket should be closed
                pass
    
    async def test_websocket_echo_functionality(self):
        """Test WebSocket echo functionality"""
        # First create a simulation
        response = client.post(
            "/api/v1/simulations/",
            json={
                "simulation_type": "heat_transfer",
                "geometry_type": "box",
                "dimensions": {"length": 1.0, "width": 1.0, "height": 1.0},
                "material_id": "steel",
                "mesh_density": 0.1,
                "boundary_conditions": [
                    {"type": "temperature", "location": "left", "value": 100.0},
                    {"type": "temperature", "location": "right", "value": 20.0}
                ]
            }
        )
        assert response.status_code == 200
        simulation_id = response.json()["id"]
        
        # Connect to WebSocket
        with client.websocket_connect(f"/api/v1/ws/simulations/{simulation_id}") as websocket:
            # Should receive initial status
            data = websocket.receive_json()
            assert data["type"] == "status"
            assert "status" in data["data"]
            
            # Send a message
            websocket.send_text("Hello WebSocket")
            
            # Should receive echo
            echo_data = websocket.receive_json()
            assert echo_data["type"] == "echo"
            assert echo_data["data"]["message"] == "Hello WebSocket"


# Integration test with actual simulation
@pytest.mark.asyncio
async def test_websocket_simulation_progress_integration():
    """Test WebSocket progress updates during actual simulation"""
    # This would require a full integration setup with Docker
    # For now, we'll create a mock simulation that sends progress
    
    from app.main import job_store, job_launcher
    from app.api.v1.websocket import get_connection_manager
    
    # Create a test job
    params = SimulationParamsDTO(
        simulation_type=SimulationType.HEAT_TRANSFER,
        geometry_type="box",
        dimensions={"length": 1.0, "width": 1.0, "height": 1.0},
        material_id="steel",
        mesh_density=0.1,
        boundary_conditions=[
            {"type": "temperature", "location": "left", "value": 100.0},
            {"type": "temperature", "location": "right", "value": 20.0}
        ]
    )
    
    job = SimulationJob(params=params)
    job = await job_store.create(job)
    
    # Simulate progress updates
    manager = get_connection_manager()
    
    # Mock client connection
    received_updates = []
    
    class MockWebSocket:
        async def accept(self):
            pass
        
        async def send_json(self, data):
            received_updates.append(data)
    
    ws = MockWebSocket()
    await manager.connect(ws, str(job.id))
    
    # Simulate progress updates
    progress_updates = [
        (10, "Initializing"),
        (25, "Generating mesh"),
        (50, "Assembling system matrix"),
        (75, "Solving linear system"),
        (90, "Post-processing"),
        (100, "Completed")
    ]
    
    for pct, msg in progress_updates:
        await manager.send_progress(str(job.id), {
            "type": "progress",
            "data": {"pct": pct, "msg": msg, "timestamp": "2024-01-01T00:00:00"}
        })
    
    # Wait for all updates to be processed
    await asyncio.sleep(1.5)
    
    # Verify updates were received
    assert len(received_updates) == len(progress_updates)
    for i, update in enumerate(received_updates):
        assert update["type"] == "progress"
        assert update["data"]["pct"] == progress_updates[i][0]
        assert update["data"]["msg"] == progress_updates[i][1]
    
    # Cleanup
    manager.disconnect(ws, str(job.id))


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 