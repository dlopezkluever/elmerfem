"""
Unit tests for WebSocket components

Run with: python -m pytest test_websocket_unit.py -v
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4

# Add backend to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.api.v1.websocket import ConnectionManager, parse_progress_line
from app.models import SimulationJob, JobStatus, SimulationType, SimulationParamsDTO


class TestProgressLineParsing:
    """Test the progress line parsing functionality"""
    
    def test_parse_valid_progress_line(self):
        """Test parsing of valid PROGRESS lines"""
        line = "PROGRESS:25:Assembling system matrix"
        result = parse_progress_line(line)
        
        assert result is not None
        assert result["type"] == "progress"
        assert result["data"]["pct"] == 25
        assert result["data"]["msg"] == "Assembling system matrix"
        assert "timestamp" in result["data"]
    
    def test_parse_progress_with_colons_in_message(self):
        """Test parsing when message contains colons"""
        line = "PROGRESS:50:Step 1:2:3 - Processing data"
        result = parse_progress_line(line)
        
        assert result is not None
        assert result["data"]["pct"] == 50
        assert result["data"]["msg"] == "Step 1:2:3 - Processing data"
    
    def test_parse_invalid_percentage(self):
        """Test parsing with invalid percentage value"""
        line = "PROGRESS:invalid:Some message"
        result = parse_progress_line(line)
        
        assert result is None
    
    def test_parse_non_progress_line(self):
        """Test parsing of non-progress lines"""
        lines = [
            "Regular log line",
            "ERROR: Something went wrong",
            "SOLVER: Starting iteration"
        ]
        
        for line in lines:
            result = parse_progress_line(line)
            assert result is None
    
    def test_parse_malformed_progress_line(self):
        """Test parsing of malformed progress lines"""
        lines = [
            "PROGRESS:",
            "PROGRESS:25",
            "PROGRESS::Message",
            "PROGRESS"
        ]
        
        for line in lines:
            result = parse_progress_line(line)
            assert result is None


@pytest.mark.asyncio
class TestConnectionManager:
    """Test the ConnectionManager class"""
    
    async def test_connect_single_client(self):
        """Test connecting a single WebSocket client"""
        manager = ConnectionManager()
        websocket = AsyncMock()
        simulation_id = "test-sim-123"
        
        await manager.connect(websocket, simulation_id)
        
        # Verify connection was accepted
        websocket.accept.assert_called_once()
        
        # Verify internal state
        assert simulation_id in manager.active_connections
        assert websocket in manager.active_connections[simulation_id]
        assert simulation_id in manager.progress_queues
        assert simulation_id in manager.broadcast_tasks
    
    async def test_connect_multiple_clients(self):
        """Test connecting multiple clients to same simulation"""
        manager = ConnectionManager()
        ws1, ws2, ws3 = AsyncMock(), AsyncMock(), AsyncMock()
        simulation_id = "test-sim-456"
        
        # Connect multiple clients
        await manager.connect(ws1, simulation_id)
        await manager.connect(ws2, simulation_id)
        await manager.connect(ws3, simulation_id)
        
        # Verify all connections accepted
        for ws in [ws1, ws2, ws3]:
            ws.accept.assert_called_once()
        
        # Verify all clients in connection set
        assert len(manager.active_connections[simulation_id]) == 3
        assert all(ws in manager.active_connections[simulation_id] for ws in [ws1, ws2, ws3])
    
    async def test_disconnect_client(self):
        """Test disconnecting a client"""
        manager = ConnectionManager()
        ws1, ws2 = AsyncMock(), AsyncMock()
        simulation_id = "test-sim-789"
        
        # Connect two clients
        await manager.connect(ws1, simulation_id)
        await manager.connect(ws2, simulation_id)
        
        # Disconnect one client
        manager.disconnect(ws1, simulation_id)
        
        # Verify only one client remains
        assert len(manager.active_connections[simulation_id]) == 1
        assert ws2 in manager.active_connections[simulation_id]
        assert ws1 not in manager.active_connections[simulation_id]
    
    async def test_disconnect_last_client_cleanup(self):
        """Test that resources are cleaned up when last client disconnects"""
        manager = ConnectionManager()
        websocket = AsyncMock()
        simulation_id = "test-sim-cleanup"
        
        # Connect and then disconnect
        await manager.connect(websocket, simulation_id)
        manager.disconnect(websocket, simulation_id)
        
        # Verify cleanup
        assert simulation_id not in manager.active_connections
        assert simulation_id not in manager.progress_queues
        assert simulation_id not in manager.last_emission_times
    
    async def test_send_progress(self):
        """Test sending progress data to queue"""
        manager = ConnectionManager()
        websocket = AsyncMock()
        simulation_id = "test-sim-progress"
        
        await manager.connect(websocket, simulation_id)
        
        # Send progress data
        progress_data = {
            "type": "progress",
            "data": {"pct": 50, "msg": "Half way there"}
        }
        
        await manager.send_progress(simulation_id, progress_data)
        
        # Verify data was queued
        assert not manager.progress_queues[simulation_id].empty()
        queued_data = await manager.progress_queues[simulation_id].get()
        assert queued_data == progress_data
    
    async def test_throttling_mechanism(self):
        """Test that throttling limits message rate to 5Hz"""
        manager = ConnectionManager()
        manager.throttle_interval = 0.2  # 200ms = 5Hz
        
        # Mock websocket that tracks send times
        send_times = []
        
        async def mock_send_json(data):
            send_times.append(asyncio.get_event_loop().time())
        
        websocket = AsyncMock()
        websocket.send_json.side_effect = mock_send_json
        
        simulation_id = "test-throttle"
        await manager.connect(websocket, simulation_id)
        
        # Send multiple progress updates rapidly
        for i in range(5):
            await manager.send_progress(simulation_id, {
                "type": "progress",
                "data": {"pct": i * 20, "msg": f"Step {i}"}
            })
        
        # Wait for broadcast to process
        await asyncio.sleep(1.5)
        
        # Cancel broadcast task
        if simulation_id in manager.broadcast_tasks:
            manager.broadcast_tasks[simulation_id].cancel()
            try:
                await manager.broadcast_tasks[simulation_id]
            except asyncio.CancelledError:
                pass
        
        # Verify throttling
        if len(send_times) > 1:
            for i in range(1, len(send_times)):
                time_diff = send_times[i] - send_times[i-1]
                # Allow small variance (180ms instead of 200ms)
                assert time_diff >= 0.18, f"Messages sent too quickly: {time_diff}s apart"


@pytest.mark.asyncio
class TestWebSocketEndpointMock:
    """Test WebSocket endpoint behavior with mocks"""
    
    async def test_invalid_simulation_id(self):
        """Test WebSocket rejects invalid simulation ID"""
        from fastapi import WebSocket
        from app.api.v1.websocket import websocket_simulation_progress
        
        # Mock dependencies
        websocket = AsyncMock(spec=WebSocket)
        job_store = AsyncMock()
        job_store.get.return_value = None  # Simulation not found
        
        # Call endpoint
        await websocket_simulation_progress(
            websocket,
            "invalid-uuid-format",
            job_store
        )
        
        # Should close with error code
        websocket.close.assert_called_once()
        args = websocket.close.call_args
        assert args[1]['code'] == 4003  # Invalid format
    
    async def test_simulation_not_found(self):
        """Test WebSocket closes when simulation doesn't exist"""
        from fastapi import WebSocket
        from app.api.v1.websocket import websocket_simulation_progress
        
        # Mock dependencies
        websocket = AsyncMock(spec=WebSocket)
        job_store = AsyncMock()
        job_store.get.return_value = None  # Simulation not found
        
        valid_uuid = str(uuid4())
        
        # Call endpoint
        await websocket_simulation_progress(
            websocket,
            valid_uuid,
            job_store
        )
        
        # Should close with error code
        websocket.close.assert_called_once()
        args = websocket.close.call_args
        assert args[1]['code'] == 4004  # Not found


def test_json_message_format():
    """Test that message formats match specification"""
    from app.api.v1.websocket import parse_progress_line
    
    # Test progress message format
    line = "PROGRESS:75:Computing results"
    result = parse_progress_line(line)
    
    # Verify structure
    assert result["type"] == "progress"
    assert "data" in result
    assert "pct" in result["data"]
    assert "msg" in result["data"]
    assert "timestamp" in result["data"]
    
    # Verify types
    assert isinstance(result["data"]["pct"], int)
    assert isinstance(result["data"]["msg"], str)
    assert isinstance(result["data"]["timestamp"], str)
    
    # Verify timestamp format (ISO 8601)
    try:
        datetime.fromisoformat(result["data"]["timestamp"].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail("Timestamp is not in valid ISO format")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"]) 