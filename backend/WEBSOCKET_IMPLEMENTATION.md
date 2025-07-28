# WebSocket Progress Streaming Implementation

This document describes the WebSocket-based real-time progress streaming implementation for ElmerFEM simulations.

## Overview

The WebSocket implementation provides real-time progress updates during simulation execution, allowing the frontend to display live feedback to users as their simulations run.

## Architecture

### Components

1. **WebSocket Endpoint** (`/api/v1/ws/simulations/{simulation_id}`)
   - Accepts WebSocket connections from clients
   - Validates simulation existence
   - Manages connection lifecycle

2. **ConnectionManager**
   - Manages multiple WebSocket connections per simulation
   - Implements 5Hz throttling for progress updates
   - Handles connection/disconnection gracefully

3. **Progress Parser**
   - Parses ElmerSolver output for `PROGRESS:<pct>:<msg>` lines
   - Converts to standardized JSON format

4. **Docker Streaming**
   - New `execute_solver_streaming()` method streams output line-by-line
   - Enables real-time progress capture

5. **Job Launcher Integration**
   - Sends progress updates via ConnectionManager during execution
   - Provides fallback progress for non-instrumented solvers

## Message Formats

### Progress Update
```json
{
  "type": "progress",
  "data": {
    "pct": 50,
    "msg": "Solving linear system",
    "timestamp": "2024-01-15T10:30:45.123456"
  }
}
```

### Status Update
```json
{
  "type": "status",
  "data": {
    "status": "completed",
    "timestamp": "2024-01-15T10:31:00.123456"
  }
}
```

### Echo Response (for testing)
```json
{
  "type": "echo",
  "data": {
    "message": "client message"
  }
}
```

## Client Usage

### JavaScript/TypeScript Example
```typescript
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/simulations/${simulationId}`);

ws.onopen = () => {
  console.log('Connected to simulation progress');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'progress':
      updateProgressBar(data.data.pct);
      updateStatusMessage(data.data.msg);
      break;
      
    case 'status':
      handleStatusChange(data.data.status);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  if (event.code === 4004) {
    console.error('Simulation not found');
  }
};
```

## Progress Line Format

ElmerSolver should output progress lines in this format:
```
PROGRESS:<percentage>:<message>
```

Examples:
- `PROGRESS:0:Initializing solver`
- `PROGRESS:25:Loading mesh`
- `PROGRESS:50:Assembling system matrix`
- `PROGRESS:75:Solving linear system`
- `PROGRESS:100:Simulation completed`

## Throttling

Progress updates are throttled to a maximum of 5Hz (200ms between updates) to prevent overwhelming clients. This is implemented in the ConnectionManager's `_broadcast_progress` method.

## Fallback Progress

For solvers without PROGRESS instrumentation, the system provides fallback progress based on key log messages:
- "Loading mesh" → 50%
- "Assembling" → 60%
- "Solving" → 70%
- "Convergence" → 85%
- "SOLVER TOTAL TIME" → 95%

## Testing

### Unit Tests
Run the WebSocket tests:
```bash
pytest backend/tests/test_websocket.py -v
```

### Manual Testing with wscat
```bash
# Install wscat
npm install -g wscat

# Connect to a simulation
wscat -c ws://localhost:8000/api/v1/ws/simulations/YOUR_SIMULATION_ID

# You should see progress updates as the simulation runs
```

### Integration Testing
The test file includes integration tests that simulate the full progress flow:
- Connection lifecycle
- Progress throttling
- Multiple client connections
- Error handling

## Error Handling

### WebSocket Close Codes
- `4003`: Invalid simulation ID format
- `4004`: Simulation not found
- `1000`: Normal closure

### Connection Management
- Automatic cleanup when clients disconnect
- Graceful handling of multiple connections
- Resource cleanup when simulations complete

## Performance Considerations

1. **Memory Usage**: Each active simulation maintains a queue of progress updates
2. **CPU Usage**: Throttling reduces CPU load from rapid updates
3. **Network**: JSON messages are kept small for efficiency
4. **Scalability**: System can handle multiple simultaneous simulations

## Future Enhancements

1. **Binary Messages**: For more efficient data transfer
2. **Compression**: WebSocket compression for large messages
3. **Authentication**: Add JWT-based authentication for WebSocket connections
4. **Metrics**: Progress analytics and performance tracking
5. **Replay**: Ability to replay progress for completed simulations 