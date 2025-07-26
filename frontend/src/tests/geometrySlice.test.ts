import { describe, it, expect } from 'vitest';
import geometryReducer, {
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
  resetGeometry,
  selectCurrentGeometry,
  selectMeshParams
} from '../store/slices/geometrySlice';
import { EducationalGeometryType } from '../types/geometry';

describe('geometrySlice', () => {
  const initialState = {
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

  describe('reducers', () => {
    it('should handle setGeometryType', () => {
      const state = geometryReducer(initialState, setGeometryType(EducationalGeometryType.RECTANGLE));
      expect(state.selectedType).toBe(EducationalGeometryType.RECTANGLE);
    });

    it('should handle setRectangleParameters', () => {
      const state = geometryReducer(initialState, setRectangleParameters({ width: 5 }));
      expect(state.parameters.rectangle.width).toBe(5);
      expect(state.parameters.rectangle.height).toBe(1); // unchanged
    });

    it('should handle setCircleParameters', () => {
      const state = geometryReducer(initialState, setCircleParameters({ radius: 2 }));
      expect(state.parameters.circle.radius).toBe(2);
    });

    it('should handle setAnnulusParameters', () => {
      const state = geometryReducer(initialState, setAnnulusParameters({ 
        innerRadius: 1, 
        outerRadius: 3 
      }));
      expect(state.parameters.annulus.innerRadius).toBe(1);
      expect(state.parameters.annulus.outerRadius).toBe(3);
    });

    it('should handle setLShapeParameters', () => {
      const state = geometryReducer(initialState, setLShapeParameters({ notchWidth: 0.5 }));
      expect(state.parameters.lShape.notchWidth).toBe(0.5);
      expect(state.parameters.lShape.width).toBe(2); // unchanged
    });

    it('should handle setMeshDensity', () => {
      const state = geometryReducer(initialState, setMeshDensity(5));
      expect(state.meshSettings.density).toBe(5);
    });

    it('should handle setBoundaryLayer', () => {
      const state = geometryReducer(initialState, setBoundaryLayer(true));
      expect(state.meshSettings.boundaryLayer).toBe(true);
    });

    it('should handle setBoundaryLayerThickness', () => {
      const state = geometryReducer(initialState, setBoundaryLayerThickness(0.05));
      expect(state.meshSettings.boundaryLayerThickness).toBe(0.05);
    });

    it('should handle setValidation', () => {
      const validation = { isValid: true, errors: { test: 'error' } };
      const state = geometryReducer(initialState, setValidation(validation));
      expect(state.validation).toEqual(validation);
    });

    it('should handle setEstimatedElements', () => {
      const state = geometryReducer(initialState, setEstimatedElements(1500));
      expect(state.estimatedElements).toBe(1500);
    });

    it('should handle resetGeometry', () => {
      // First make some changes
      let state = geometryReducer(initialState, setGeometryType(EducationalGeometryType.CIRCLE));
      state = geometryReducer(state, setMeshDensity(5));
      state = geometryReducer(state, setEstimatedElements(2000));
      
      // Then reset
      state = geometryReducer(state, resetGeometry());
      
      expect(state).toEqual(initialState);
    });
  });

  describe('selectors', () => {
    describe('selectCurrentGeometry', () => {
      it('should return null when no type selected', () => {
        const state = { geometry: initialState };
        expect(selectCurrentGeometry(state)).toBeNull();
      });

      it('should return rectangle geometry when selected', () => {
        const state = {
          geometry: {
            ...initialState,
            selectedType: EducationalGeometryType.RECTANGLE
          }
        };
        const geometry = selectCurrentGeometry(state);
        expect(geometry).toEqual({
          type: EducationalGeometryType.RECTANGLE,
          params: { width: 1, height: 1 }
        });
      });

      it('should return circle geometry when selected', () => {
        const state = {
          geometry: {
            ...initialState,
            selectedType: EducationalGeometryType.CIRCLE
          }
        };
        const geometry = selectCurrentGeometry(state);
        expect(geometry).toEqual({
          type: EducationalGeometryType.CIRCLE,
          params: { radius: 0.5 }
        });
      });

      it('should return annulus geometry when selected', () => {
        const state = {
          geometry: {
            ...initialState,
            selectedType: EducationalGeometryType.ANNULUS
          }
        };
        const geometry = selectCurrentGeometry(state);
        expect(geometry).toEqual({
          type: EducationalGeometryType.ANNULUS,
          params: { innerRadius: 0.3, outerRadius: 0.5 }
        });
      });

      it('should return L-shape geometry when selected', () => {
        const state = {
          geometry: {
            ...initialState,
            selectedType: EducationalGeometryType.L_SHAPE
          }
        };
        const geometry = selectCurrentGeometry(state);
        expect(geometry).toEqual({
          type: EducationalGeometryType.L_SHAPE,
          params: { width: 2, height: 2, notchWidth: 1, notchHeight: 1 }
        });
      });
    });

    describe('selectMeshParams', () => {
      it('should return null when no geometry selected', () => {
        const state = { geometry: initialState };
        expect(selectMeshParams(state)).toBeNull();
      });

      it('should return null when validation fails', () => {
        const state = {
          geometry: {
            ...initialState,
            selectedType: EducationalGeometryType.RECTANGLE,
            validation: { isValid: false, errors: { width: 'Invalid' } }
          }
        };
        expect(selectMeshParams(state)).toBeNull();
      });

      it('should return mesh params when valid without boundary layer', () => {
        const state = {
          geometry: {
            ...initialState,
            selectedType: EducationalGeometryType.RECTANGLE,
            validation: { isValid: true, errors: {} }
          }
        };
        const params = selectMeshParams(state);
        expect(params).toEqual({
          geometry: {
            type: EducationalGeometryType.RECTANGLE,
            params: { width: 1, height: 1 }
          },
          meshDensity: 3,
          boundaryLayer: false
        });
      });

      it('should include boundary layer thickness when enabled', () => {
        const state = {
          geometry: {
            ...initialState,
            selectedType: EducationalGeometryType.CIRCLE,
            validation: { isValid: true, errors: {} },
            meshSettings: {
              density: 4,
              boundaryLayer: true,
              boundaryLayerThickness: 0.02
            }
          }
        };
        const params = selectMeshParams(state);
        expect(params).toEqual({
          geometry: {
            type: EducationalGeometryType.CIRCLE,
            params: { radius: 0.5 }
          },
          meshDensity: 4,
          boundaryLayer: true,
          boundaryLayerThickness: 0.02
        });
      });
    });
  });
}); 