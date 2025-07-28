import { useEffect, useRef, useCallback, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../store';
import {
  setWebSocketConnectionState,
  handleProgressMessage,
  handleStatusMessage,
  setWebSocketError
} from '../store/slices/simulationSlice';
import {
  WebSocketConnectionState,
  WebSocketMessageType,
  SimulationWebSocketMessage
} from '../types/websocket';
import { JobStatus } from '../types/api';

interface UseSimulationProgressOptions {
  simulationId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
  maxReconnectAttempts?: number;
  initialReconnectDelay?: number;
  maxReconnectDelay?: number;
}

export function useSimulationProgress({
  simulationId,
  onComplete,
  onError,
  maxReconnectAttempts = 5,
  initialReconnectDelay = 1000, // 1 second
  maxReconnectDelay = 30000 // 30 seconds
}: UseSimulationProgressOptions) {
  const dispatch = useDispatch<AppDispatch>();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectDelayRef = useRef(initialReconnectDelay);
  const isUnmountedRef = useRef(false);
  
  const [isConnected, setIsConnected] = useState(false);
  
  // Get state from Redux
  const {
    status,
    progress,
    currentMessage,
    progressMessages,
    wsConnectionState,
    error
  } = useSelector((state: RootState) => state.simulation);

  // Get WebSocket URL from environment or use default
  const getWebSocketUrl = useCallback(() => {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
    const wsUrl = backendUrl.replace(/^http/, 'ws');
    return `${wsUrl}/api/v1/ws/simulations/${simulationId}`;
  }, [simulationId]);

  // Clean up function
  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      // Remove event listeners before closing
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close(1000, 'Component unmounting');
      }
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (isUnmountedRef.current) return;
    
    cleanup();
    
    dispatch(setWebSocketConnectionState(WebSocketConnectionState.CONNECTING));
    
    try {
      const ws = new WebSocket(getWebSocketUrl());
      wsRef.current = ws;
      
      ws.onopen = () => {
        if (isUnmountedRef.current) return;
        
        console.log('WebSocket connected for simulation:', simulationId);
        dispatch(setWebSocketConnectionState(WebSocketConnectionState.CONNECTED));
        setIsConnected(true);
        
        // Reset reconnect parameters on successful connection
        reconnectAttemptsRef.current = 0;
        reconnectDelayRef.current = initialReconnectDelay;
      };
      
      ws.onmessage = (event) => {
        if (isUnmountedRef.current) return;
        
        try {
          const message = JSON.parse(event.data);
          
          // Handle actual backend message formats
          if (message.progress !== undefined) {
            // Progress message: {job_id, progress, message, timestamp}
            dispatch(handleProgressMessage({
              pct: message.progress,
              msg: message.message,
              timestamp: message.timestamp
            }));
          } else if (message.status !== undefined) {
            // Status message: {job_id, status, timestamp}
            dispatch(handleStatusMessage({
              status: message.status,
              timestamp: message.timestamp
            }));
            
            // Check if simulation completed
            if (message.status.toLowerCase() === 'completed' && onComplete) {
              onComplete();
            } else if (message.status.toLowerCase() === 'failed' && onError) {
              onError('Simulation failed');
            }
          } else if (message.event === 'job_completed') {
            // Completion event: {event: 'job_completed', result_files, timestamp, job_id}
            dispatch(handleStatusMessage({
              status: 'completed',
              timestamp: message.timestamp
            }));
            
            // Call completion callback
            if (onComplete) {
              onComplete();
            }
          } else {
            console.warn('Unknown WebSocket message format:', message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      ws.onerror = (event) => {
        if (isUnmountedRef.current) return;
        
        console.error('WebSocket error:', event);
        dispatch(setWebSocketError('WebSocket connection error'));
      };
      
      ws.onclose = (event) => {
        if (isUnmountedRef.current) return;
        
        setIsConnected(false);
        
        // Handle different close codes
        if (event.code === 1000) {
          // Normal closure
          dispatch(setWebSocketConnectionState(WebSocketConnectionState.DISCONNECTED));
        } else if (event.code === 4003) {
          // Invalid UUID format
          dispatch(setWebSocketError('Invalid simulation ID format'));
          if (onError) {
            onError('Invalid simulation ID format');
          }
        } else if (event.code === 4004) {
          // Simulation not found
          dispatch(setWebSocketError('Simulation not found'));
          if (onError) {
            onError('Simulation not found');
          }
        } else if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          // Attempt to reconnect with exponential backoff
          dispatch(setWebSocketConnectionState(WebSocketConnectionState.RECONNECTING));
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (!isUnmountedRef.current) {
              reconnectAttemptsRef.current += 1;
              reconnectDelayRef.current = Math.min(
                reconnectDelayRef.current * 2,
                maxReconnectDelay
              );
              connect();
            }
          }, reconnectDelayRef.current);
          
          console.log(
            `WebSocket disconnected. Reconnecting in ${reconnectDelayRef.current}ms... ` +
            `(Attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`
          );
        } else {
          // Max reconnect attempts reached
          dispatch(setWebSocketConnectionState(WebSocketConnectionState.ERROR));
          dispatch(setWebSocketError('Failed to connect after multiple attempts'));
          if (onError) {
            onError('Failed to connect to simulation progress updates');
          }
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      dispatch(setWebSocketConnectionState(WebSocketConnectionState.ERROR));
      dispatch(setWebSocketError('Failed to create WebSocket connection'));
    }
  }, [
    simulationId,
    dispatch,
    getWebSocketUrl,
    cleanup,
    initialReconnectDelay,
    maxReconnectDelay,
    maxReconnectAttempts,
    onComplete,
    onError
  ]);

  // Manual reconnect function
  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    reconnectDelayRef.current = initialReconnectDelay;
    connect();
  }, [connect, initialReconnectDelay]);

  // Effect to establish WebSocket connection
  useEffect(() => {
    isUnmountedRef.current = false;
    
    // Don't connect if simulation is already completed or failed
    if (status === JobStatus.COMPLETED || status === JobStatus.FAILED) {
      return;
    }
    
    connect();
    
    return () => {
      isUnmountedRef.current = true;
      cleanup();
    };
  }, [simulationId]); // Only reconnect if simulationId changes

  return {
    // Connection state
    isConnected,
    connectionState: wsConnectionState,
    
    // Simulation data
    status,
    progress,
    currentMessage,
    progressMessages,
    error,
    
    // Actions
    reconnect,
    disconnect: cleanup
  };
} 