# WebSocket Implementation for ElmerFEM Educational Platform

## Overview

This document describes the WebSocket implementation for real-time simulation progress tracking in the ElmerFEM Educational Platform frontend.

## Components

### 1. Type Definitions (`types/websocket.ts`)

Defines all WebSocket-related types:
- `WebSocketMessageType`: Enum for message types (progress, status, error)
- `ProgressData`, `StatusData`, `ErrorData`: Data structures for each message type
- `WebSocketConnectionState`: Connection states (connecting, connected, disconnected, reconnecting, error)

### 2. Redux Integration (`store/slices/simulationSlice.ts`)

Enhanced simulation slice with WebSocket state management:
- `wsConnectionState`: Current WebSocket connection state
- `progressMessages`: Array of timestamped progress messages
- `currentMessage`: Latest progress message
- `lastUpdate`: Timestamp of last update

Actions:
- `setWebSocketConnectionState`: Update connection state
- `handleProgressMessage`: Process incoming progress messages
- `handleStatusMessage`: Process incoming status messages
- `setWebSocketError`: Handle WebSocket errors

### 3. useSimulationProgress Hook (`hooks/useSimulationProgress.ts`)

Core WebSocket functionality with:
- **Auto-reconnect**: Exponential backoff strategy (1s → 2s → 4s → ... → 30s max)
- **Connection lifecycle management**: Proper cleanup on unmount
- **Redux integration**: All state updates through Redux
- **Error handling**: Specific handling for different WebSocket close codes
- **Callbacks**: `onComplete` and `onError` for component-specific handling

#### Hook Options

```typescript
interface UseSimulationProgressOptions {
  simulationId: string;              // Required: Simulation ID to monitor
  onComplete?: () => void;           // Called when simulation completes
  onError?: (error: string) => void; // Called on errors
  maxReconnectAttempts?: number;     // Default: 5
  initialReconnectDelay?: number;    // Default: 1000ms
  maxReconnectDelay?: number;        // Default: 30000ms
}
```

#### Hook Return Values

```typescript
{
  // Connection state
  isConnected: boolean;
  connectionState: WebSocketConnectionState;
  
  // Simulation data
  status: JobStatus | null;
  progress: number;
  currentMessage: string;
  progressMessages: string[];
  error: string | null;
  
  // Actions
  reconnect: () => void;    // Manual reconnect
  disconnect: () => void;   // Manual disconnect
}
```

### 4. Updated ProgressPage (`pages/ProgressPage.tsx`)

Enhanced with:
- Live WebSocket updates instead of polling
- Connection status badge showing real-time connection state
- Progress message log showing last 10 messages
- Manual reconnect button on connection errors
- Graceful fallback to initial REST API data

## WebSocket Protocol

### Endpoint
```
ws://localhost:8000/api/v1/ws/simulations/{simulation_id}
```

### Message Format

#### Progress Message
```json
{
  "type": "progress",
  "data": {
    "pct": 50,
    "msg": "Assembling system matrix",
    "timestamp": "2024-01-27T10:30:00Z"
  }
}
```

#### Status Message
```json
{
  "type": "status",
  "data": {
    "status": "running",
    "timestamp": "2024-01-27T10:30:00Z"
  }
}
```

#### Error Message
```json
{
  "type": "error",
  "data": {
    "error": "Solver convergence failed",
    "timestamp": "2024-01-27T10:30:00Z"
  }
}
```

### Close Codes
- `1000`: Normal closure
- `4003`: Invalid UUID format
- `4004`: Simulation not found
- Other codes trigger reconnection attempts

## Testing

### Manual Testing

1. **Using the Test Component**
   ```typescript
   import { WebSocketTest } from './tests/WebSocketTest';
   
   // Add to your app routes for testing
   <Route path="/ws-test" element={<WebSocketTest />} />
   ```

2. **Backend Requirements**
   - Ensure backend is running: `cd backend && python -m uvicorn app.main:app --reload`
   - Create a test simulation to get a valid ID
   - Use the ID in the test component

3. **Testing Scenarios**
   - Connection establishment
   - Progress message reception
   - Reconnection after disconnect
   - Error handling
   - Multiple reconnection attempts

### Unit Testing

Run the test suite:
```bash
npm test useSimulationProgress.test.ts
```

Test coverage includes:
- Connection lifecycle
- Message handling
- Error scenarios
- Reconnection logic
- Component cleanup

### Integration Testing

1. Start a real simulation through the UI
2. Monitor the browser console for WebSocket logs
3. Check Redux DevTools for state updates
4. Verify progress bar and messages update in real-time

## Configuration

### Environment Variables

Set the backend URL in `.env`:
```
VITE_BACKEND_URL=http://localhost:8000
```

The WebSocket URL is automatically derived from this.

### Reconnection Parameters

Customize reconnection behavior:
```typescript
useSimulationProgress({
  simulationId: 'abc-123',
  maxReconnectAttempts: 10,      // Try 10 times
  initialReconnectDelay: 500,    // Start with 500ms
  maxReconnectDelay: 60000       // Cap at 60 seconds
});
```

## Troubleshooting

### Connection Issues

1. **WebSocket fails to connect**
   - Check backend is running
   - Verify simulation ID is valid
   - Check browser console for errors
   - Ensure no firewall/proxy blocking WebSocket

2. **Messages not received**
   - Check backend WebSocket implementation
   - Verify message format matches expected structure
   - Check Redux DevTools for state updates

3. **Frequent disconnections**
   - Check network stability
   - Verify backend isn't timing out connections
   - Check for memory leaks in long-running simulations

### Debug Mode

Enable detailed logging:
```typescript
// In useSimulationProgress.ts, all console.logs are already in place
// Check browser console for:
// - Connection status changes
// - Reconnection attempts
// - Message parsing errors
```

## Future Improvements

1. **Binary message support** for large data transfers
2. **Compression** for message payloads
3. **Message queuing** for offline support
4. **Heartbeat/ping-pong** for connection health monitoring
5. **Authentication** for WebSocket connections
6. **Message encryption** for sensitive data

## Related Documentation

- [WebSocket Backend Implementation](../../../backend/WEBSOCKET_TESTING_GUIDE.md)
- [Task 4 Implementation Report](../../../._docs/Task_4_Implementation_Report.md)
- [Frontend Architecture Guide](../../../._docs/Frontend _ UI Dev_Guide_ Edu_Web_Interface_MVP.md) 