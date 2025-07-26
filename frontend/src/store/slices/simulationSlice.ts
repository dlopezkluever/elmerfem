import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { SimulationType, JobStatus } from '../../types/api';

interface SimulationState {
  activeSimulationId: string | null;
  simulationType: SimulationType | null;
  status: JobStatus | null;
  progress: number;
  error: string | null;
}

const initialState: SimulationState = {
  activeSimulationId: null,
  simulationType: null,
  status: null,
  progress: 0,
  error: null
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
    clearSimulation: (state) => {
      Object.assign(state, initialState);
    }
  }
});

export const {
  setActiveSimulation,
  updateSimulationStatus,
  clearSimulation
} = simulationSlice.actions;

export default simulationSlice.reducer; 