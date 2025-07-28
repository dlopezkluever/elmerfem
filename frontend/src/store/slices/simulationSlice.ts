import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { SimulationType, JobStatus } from '../../types/api';
import { WebSocketConnectionState, ProgressData, StatusData } from '../../types/websocket';

interface SimulationState {
  activeSimulationId: string | null;
  simulationType: SimulationType | null;
  status: JobStatus | null;
  progress: number;
  error: string | null;
  
  // WebSocket state
  wsConnectionState: WebSocketConnectionState;
  progressMessages: string[];
  currentMessage: string;
  lastUpdate: string | null;
}

const initialState: SimulationState = {
  activeSimulationId: null,
  simulationType: null,
  status: null,
  progress: 0,
  error: null,
  
  // WebSocket state
  wsConnectionState: WebSocketConnectionState.DISCONNECTED,
  progressMessages: [],
  currentMessage: '',
  lastUpdate: null
};

const simulationSlice = createSlice({
  name: 'simulation',
  initialState,
  reducers: {
    setActiveSimulation: (state, action: PayloadAction<{
      id: string;
      type: SimulationType;
    }>) => {
      state.activeSimulationId = action.payload.id;
      state.simulationType = action.payload.type;
      state.status = JobStatus.PENDING;
      state.progress = 0;
      state.error = null;
      state.progressMessages = [];
      state.currentMessage = '';
      state.lastUpdate = null;
    },
    updateSimulationStatus: (state, action: PayloadAction<{
      status: JobStatus;
      progress: number;
      error?: string;
    }>) => {
      state.status = action.payload.status;
      state.progress = action.payload.progress;
      if (action.payload.error) {
        state.error = action.payload.error;
      }
    },
    
    // WebSocket actions
    setWebSocketConnectionState: (state, action: PayloadAction<WebSocketConnectionState>) => {
      state.wsConnectionState = action.payload;
    },
    
    handleProgressMessage: (state, action: PayloadAction<ProgressData>) => {
      state.progress = action.payload.pct;
      state.currentMessage = action.payload.msg;
      state.progressMessages.push(`[${new Date(action.payload.timestamp).toLocaleTimeString()}] ${action.payload.msg}`);
      state.lastUpdate = action.payload.timestamp;
      
      // Keep only last 100 messages to prevent memory issues
      if (state.progressMessages.length > 100) {
        state.progressMessages = state.progressMessages.slice(-100);
      }
    },
    
    handleStatusMessage: (state, action: PayloadAction<StatusData>) => {
      const statusMap: Record<string, JobStatus> = {
        'pending': JobStatus.PENDING,
        'running': JobStatus.RUNNING,
        'completed': JobStatus.COMPLETED,
        'failed': JobStatus.FAILED,
        'cancelled': JobStatus.CANCELLED
      };
      
      const mappedStatus = statusMap[action.payload.status.toLowerCase()];
      if (mappedStatus) {
        state.status = mappedStatus;
      }
      state.lastUpdate = action.payload.timestamp;
    },
    
    setWebSocketError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.wsConnectionState = WebSocketConnectionState.ERROR;
    },
    
    clearSimulation: (state) => {
      Object.assign(state, initialState);
    }
  }
});

export const {
  setActiveSimulation,
  updateSimulationStatus,
  setWebSocketConnectionState,
  handleProgressMessage,
  handleStatusMessage,
  setWebSocketError,
  clearSimulation
} = simulationSlice.actions;

export default simulationSlice.reducer; 