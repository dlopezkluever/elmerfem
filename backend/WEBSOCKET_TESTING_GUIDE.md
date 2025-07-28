# WebSocket Testing Guide

This guide provides comprehensive instructions for testing the WebSocket progress streaming implementation.

## Overview

The WebSocket implementation provides real-time progress updates for ElmerFEM simulations. The system has been updated to use stage-based progress tracking with the following stages:

1. **validate** (0-5%): Validation and initialization
2. **mesh** (5-30%): Mesh generation
3. **write_sif** (30-35%): SIF file generation
4. **solve** (35-90%): ElmerSolver execution
5. **post** (90-100%): Post-processing and results

## Testing Methods

### 1. Quick Connectivity Test

The fastest way to verify WebSocket connectivity:

```bash
cd backend
python test_websocket_quick.py
```

This will:
- Test WebSocket endpoint accessibility
- Verify error codes (4003 for invalid UUID, 4004 for not found)
- Check if the endpoint is properly registered

### 2. Unit Tests

Test individual components without running the full backend:

```bash
cd backend
python -m pytest test_websocket_unit.py -v
```

Tests include:
- Progress line parsing
- Connection management
- Multi-client support
- 5Hz throttling mechanism
- Message format validation

### 3. Manual Testing

Test the WebSocket with a simulated job:

```bash
cd backend
python test_websocket_manual.py
```

This creates a fake job and simulates progress updates to verify the WebSocket flow.

### 4. Integration Testing

Full end-to-end test with real simulations:

```bash
# First, ensure the backend is running:
cd backend
python -m uvicorn app.main:app --reload

# In another terminal, run integration tests:
cd backend
python test_websocket_integration.py
```

This will:
- Create a real simulation job
- Connect via WebSocket
- Monitor actual progress updates
- Verify throttling behavior
- Test multiple concurrent clients

## Testing with Browser

You can also test WebSocket connections using browser DevTools:

```javascript
// Open browser console and run:
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/simulations/YOUR_JOB_ID');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data));
ws.onerror = (error) => console.error('Error:', error);
ws.onclose = (event) => console.log('Closed:', event.code, event.reason);
```

## Testing with curl/wscat

Using wscat (install with `npm install -g wscat`):

```bash
wscat -c ws://localhost:8000/api/v1/ws/simulations/YOUR_JOB_ID
```

## Expected Message Formats

### Progress Messages
```json
{
  "type": "progress",
  "data": {
    "pct": 50,
    "msg": "Solving linear system",
    "timestamp": "2024-01-27T10:30:45.123456"
  }
}
```

### Status Messages
```json
{
  "type": "status",
  "data": {
    "status": "completed",
    "timestamp": "2024-01-27T10:31:00.123456"
  }
}
```

## Architecture Notes

The current implementation uses:

1. **Stage-based progress tracking** in `JobLauncher` instead of parsing PROGRESS lines
2. **JobStore** with stage information (validate, mesh, write_sif, solve, post)
3. **Redis support** (optional) for distributed progress relay via `ProgressRelayService`
4. **ConnectionManager** for WebSocket client management and 5Hz throttling

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure backend is running: `python -m uvicorn app.main:app --reload`
   - Check port 8000 is not in use

2. **No Progress Updates**
   - Check if job is actually running (view logs)
   - Verify Redis is connected if using distributed setup
   - Check WebSocket connection hasn't timed out

3. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path includes the backend directory

4. **WebSocket Closes Immediately**
   - Code 4003: Invalid UUID format
   - Code 4004: Job not found
   - Check job exists using REST API: `GET /api/v1/simulations/{job_id}/status`

### Debug Logging

Enable debug logging to see WebSocket activity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Verification

The 5Hz throttling ensures clients receive at most 5 messages per second. To verify:

1. Run the integration test
2. Check the throttling analysis output
3. Minimum time between messages should be ~0.2s (200ms)

## Next Steps

After verifying WebSocket functionality:

1. Integrate with frontend progress display
2. Add reconnection logic for dropped connections
3. Implement progress persistence for page refreshes
4. Add WebSocket authentication if needed 