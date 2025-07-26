import { configureStore } from '@reduxjs/toolkit';
import geometryReducer from './slices/geometrySlice';
import simulationReducer from './slices/simulationSlice';

export const store = configureStore({
  reducer: {
    geometry: geometryReducer,
    simulation: simulationReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 