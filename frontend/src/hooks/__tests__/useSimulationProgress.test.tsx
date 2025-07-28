import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { vi } from 'vitest';
import WS from 'jest-websocket-mock';
import simulationReducer from '../../store/slices/simulationSlice';
import { useSimulationProgress } from '../useSimulationProgress';
import { WebSocketConnectionState, WebSocketMessageType } from '../../types/websocket';

// Mock WebSocket URL
const MOCK_WS_URL = 'ws://localhost:8000/api/v1/ws/simulations';

// Create a test store
function createTestStore() {
  return configureStore({
    reducer: {
      simulation: simulationReducer,
      geometry: (state = {}) => state // Dummy reducer
    }
  });
}

// Wrapper component for providing Redux store
function createWrapper(store: any) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <Provider store={store}>{children}</Provider>;
  };
}

describe('useSimulationProgress', () => {
  let server: WS;
  let store: ReturnType<typeof createTestStore>;

  beforeEach(() => {
    // Create a new WebSocket mock server
    server = new WS(`${MOCK_WS_URL}/test-simulation-id`);
    store = createTestStore();
  });

  afterEach(() => {
    WS.clean();
  });

  it('should connect to WebSocket on mount', async () => {
    const { result } = renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
      }),
      { wrapper: createWrapper(store) }
    );

    // Wait for connection
    await server.connected;

    expect(result.current.connectionState).toBe(WebSocketConnectionState.CONNECTED);
    expect(result.current.isConnected).toBe(true);
  });

  it('should handle progress messages', async () => {
    const { result } = renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
      }),
      { wrapper: createWrapper(store) }
    );

    await server.connected;

    // Send progress message (actual backend format)
    const progressMessage = {
      job_id: 'test-simulation-id',
      progress: 50,
      message: 'Processing...',
      timestamp: new Date().toISOString()
    };

    act(() => {
      server.send(JSON.stringify(progressMessage));
    });

    await waitFor(() => {
      expect(result.current.progress).toBe(50);
      expect(result.current.currentMessage).toBe('Processing...');
      expect(result.current.progressMessages).toHaveLength(1);
    });
  });

  it('should handle status messages', async () => {
    const { result } = renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
      }),
      { wrapper: createWrapper(store) }
    );

    await server.connected;

    // Send status message (actual backend format)
    const statusMessage = {
      job_id: 'test-simulation-id',
      status: 'running',
      timestamp: new Date().toISOString()
    };

    act(() => {
      server.send(JSON.stringify(statusMessage));
    });

    await waitFor(() => {
      expect(result.current.status).toBe('running');
    });
  });

  it('should call onComplete when simulation completes', async () => {
    const onComplete = vi.fn();

    const { result } = renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
        onComplete
      }),
      { wrapper: createWrapper(store) }
    );

    await server.connected;

    // Send completion status (actual backend format)
    const completeMessage = {
      job_id: 'test-simulation-id',
      status: 'completed',
      timestamp: new Date().toISOString()
    };

    act(() => {
      server.send(JSON.stringify(completeMessage));
    });

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalled();
    });
  });

  it('should handle connection errors', async () => {
    const onError = vi.fn();

    const { result } = renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
        onError
      }),
      { wrapper: createWrapper(store) }
    );

    await server.connected;

    // Simulate error
    act(() => {
      server.error();
    });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
      expect(result.current.connectionState).toBe(WebSocketConnectionState.DISCONNECTED);
    });
  });

  it.skip('should attempt to reconnect with exponential backoff', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
        maxReconnectAttempts: 3,
        initialReconnectDelay: 100,
        maxReconnectDelay: 1000
      }),
      { wrapper: createWrapper(store) }
    );

    await server.connected;

    // Close connection abnormally
    act(() => {
      server.close({ code: 1006 });
    });

    // Should be in reconnecting state
    expect(result.current.connectionState).toBe(WebSocketConnectionState.RECONNECTING);

    // Advance timer for first reconnect attempt (100ms)
    act(() => {
      jest.advanceTimersByTime(100);
    });

    // Clean up
    jest.useRealTimers();
  });

  it.skip('should handle manual reconnect', async () => {
    const { result } = renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
      }),
      { wrapper: createWrapper(store) }
    );

    await server.connected;

    // Close connection
    act(() => {
      server.close();
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });

    // Create new server for reconnection
    const newServer = new WS(`${MOCK_WS_URL}/test-simulation-id`);

    // Manual reconnect
    act(() => {
      result.current.reconnect();
    });

    await newServer.connected;

    expect(result.current.isConnected).toBe(true);
  });

  it.skip('should clean up on unmount', async () => {
    const { result, unmount } = renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
      }),
      { wrapper: createWrapper(store) }
    );

    await server.connected;

    expect(result.current.isConnected).toBe(true);

    // Unmount
    unmount();

    // Check that connection is closed
    await server.closed;
  });

  it('should not connect if simulation is already completed', () => {
    // Set initial state with completed simulation
    store.dispatch({
      type: 'simulation/updateSimulationStatus',
      payload: {
        status: 'COMPLETED',
        progress: 100
      }
    });

    renderHook(
      () => useSimulationProgress({
        simulationId: 'test-simulation-id',
      }),
      { wrapper: createWrapper(store) }
    );

    // Should not attempt connection
    expect(server).not.toHaveReceivedMessages([]);
  });
}); 