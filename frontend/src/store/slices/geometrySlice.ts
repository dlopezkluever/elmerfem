import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { 
  EducationalGeometryType, 
  GeometryParameters,
  EducationalMeshParams,
  RectangleParameters,
  CircleParameters,
  AnnulusParameters,
  LShapeParameters
} from '../../types/geometry';

interface GeometryState {
  selectedType: EducationalGeometryType | null;
  parameters: {
    rectangle: RectangleParameters;
    circle: CircleParameters;
    annulus: AnnulusParameters;
    lShape: LShapeParameters;
  };
  meshSettings: {
    density: number;
    boundaryLayer: boolean;
    boundaryLayerThickness: number;
  };
  validation: {
    isValid: boolean;
    errors: { [field: string]: string };
  };
  estimatedElements: number;
}

const initialState: GeometryState = {
  selectedType: null,
  parameters: {
    rectangle: { width: 1, height: 1 },
    circle: { radius: 0.5 },
    annulus: { innerRadius: 0.3, outerRadius: 0.5 },
    lShape: { width: 2, height: 2, notchWidth: 1, notchHeight: 1 }
  },
  meshSettings: {
    density: 3,
    boundaryLayer: false,
    boundaryLayerThickness: 0.01
  },
  validation: {
    isValid: false,
    errors: {}
  },
  estimatedElements: 0
};

const geometrySlice = createSlice({
  name: 'geometry',
  initialState,
  reducers: {
    setGeometryType: (state, action: PayloadAction<EducationalGeometryType | null>) => {
      state.selectedType = action.payload;
    },
    setRectangleParameters: (state, action: PayloadAction<Partial<RectangleParameters>>) => {
      state.parameters.rectangle = { ...state.parameters.rectangle, ...action.payload };
    },
    setCircleParameters: (state, action: PayloadAction<Partial<CircleParameters>>) => {
      state.parameters.circle = { ...state.parameters.circle, ...action.payload };
    },
    setAnnulusParameters: (state, action: PayloadAction<Partial<AnnulusParameters>>) => {
      state.parameters.annulus = { ...state.parameters.annulus, ...action.payload };
    },
    setLShapeParameters: (state, action: PayloadAction<Partial<LShapeParameters>>) => {
      state.parameters.lShape = { ...state.parameters.lShape, ...action.payload };
    },
    setMeshDensity: (state, action: PayloadAction<number>) => {
      state.meshSettings.density = action.payload;
    },
    setBoundaryLayer: (state, action: PayloadAction<boolean>) => {
      state.meshSettings.boundaryLayer = action.payload;
    },
    setBoundaryLayerThickness: (state, action: PayloadAction<number>) => {
      state.meshSettings.boundaryLayerThickness = action.payload;
    },
    setValidation: (state, action: PayloadAction<{ isValid: boolean; errors: { [field: string]: string } }>) => {
      state.validation = action.payload;
    },
    setEstimatedElements: (state, action: PayloadAction<number>) => {
      state.estimatedElements = action.payload;
    },
    resetGeometry: (state) => {
      Object.assign(state, initialState);
    }
  }
});

export const {
  setGeometryType,
  setRectangleParameters,
  setCircleParameters,
  setAnnulusParameters,
  setLShapeParameters,
  setMeshDensity,
  setBoundaryLayer,
  setBoundaryLayerThickness,
  setValidation,
  setEstimatedElements,
  resetGeometry
} = geometrySlice.actions;

export default geometrySlice.reducer;

// Selectors
export const selectCurrentGeometry = (state: { geometry: GeometryState }): GeometryParameters | null => {
  const { selectedType, parameters } = state.geometry;
  
  switch (selectedType) {
    case EducationalGeometryType.RECTANGLE:
      return { type: EducationalGeometryType.RECTANGLE, params: parameters.rectangle };
    case EducationalGeometryType.CIRCLE:
      return { type: EducationalGeometryType.CIRCLE, params: parameters.circle };
    case EducationalGeometryType.ANNULUS:
      return { type: EducationalGeometryType.ANNULUS, params: parameters.annulus };
    case EducationalGeometryType.L_SHAPE:
      return { type: EducationalGeometryType.L_SHAPE, params: parameters.lShape };
    default:
      return null;
  }
};

export const selectMeshParams = (state: { geometry: GeometryState }): EducationalMeshParams | null => {
  const geometry = selectCurrentGeometry(state);
  if (!geometry || !state.geometry.validation.isValid) return null;
  
  const { meshSettings } = state.geometry;
  return {
    geometry,
    meshDensity: meshSettings.density,
    boundaryLayer: meshSettings.boundaryLayer,
    ...(meshSettings.boundaryLayer && { 
      boundaryLayerThickness: meshSettings.boundaryLayerThickness 
    })
  };
}; 