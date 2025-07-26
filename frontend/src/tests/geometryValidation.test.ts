import { describe, it, expect } from 'vitest';
import {
  validateRectangle,
  validateCircle,
  validateAnnulus,
  validateLShape,
  validateGeometry,
  estimateMeshElements
} from '../utils/geometryValidation';
import { EducationalGeometryType } from '../types/geometry';

describe('Geometry Validation', () => {
  describe('validateRectangle', () => {
    it('should validate valid rectangle parameters', () => {
      const result = validateRectangle({ width: 1, height: 2 });
      expect(result.isValid).toBe(true);
      expect(result.errors).toEqual({});
    });

    it('should reject too small dimensions', () => {
      const result = validateRectangle({ width: 0.0001, height: 1 });
      expect(result.isValid).toBe(false);
      expect(result.errors.width).toBeDefined();
    });

    it('should reject too large dimensions', () => {
      const result = validateRectangle({ width: 1, height: 15 });
      expect(result.isValid).toBe(false);
      expect(result.errors.height).toBeDefined();
    });
  });

  describe('validateCircle', () => {
    it('should validate valid circle parameters', () => {
      const result = validateCircle({ radius: 1 });
      expect(result.isValid).toBe(true);
      expect(result.errors).toEqual({});
    });

    it('should reject invalid radius', () => {
      const result = validateCircle({ radius: 10 });
      expect(result.isValid).toBe(false);
      expect(result.errors.radius).toBeDefined();
    });
  });

  describe('validateAnnulus', () => {
    it('should validate valid annulus parameters', () => {
      const result = validateAnnulus({ innerRadius: 0.5, outerRadius: 1 });
      expect(result.isValid).toBe(true);
      expect(result.errors).toEqual({});
    });

    it('should reject when inner radius is larger than outer', () => {
      const result = validateAnnulus({ innerRadius: 2, outerRadius: 1 });
      expect(result.isValid).toBe(false);
      expect(result.errors.innerRadius).toBeDefined();
      expect(result.errors.outerRadius).toBeDefined();
    });

    it('should reject when radii are equal', () => {
      const result = validateAnnulus({ innerRadius: 1, outerRadius: 1 });
      expect(result.isValid).toBe(false);
      expect(result.errors.innerRadius).toBeDefined();
    });
  });

  describe('validateLShape', () => {
    it('should validate valid L-shape parameters', () => {
      const result = validateLShape({
        width: 2,
        height: 2,
        notchWidth: 1,
        notchHeight: 1
      });
      expect(result.isValid).toBe(true);
      expect(result.errors).toEqual({});
    });

    it('should reject when notch is too large', () => {
      const result = validateLShape({
        width: 2,
        height: 2,
        notchWidth: 2.5,
        notchHeight: 1
      });
      expect(result.isValid).toBe(false);
      expect(result.errors.notchWidth).toBeDefined();
    });

    it('should reject when notch equals full dimension', () => {
      const result = validateLShape({
        width: 2,
        height: 2,
        notchWidth: 2,
        notchHeight: 2
      });
      expect(result.isValid).toBe(false);
      expect(result.errors.notchWidth).toBeDefined();
      expect(result.errors.notchHeight).toBeDefined();
    });
  });

  describe('validateGeometry', () => {
    it('should delegate to correct validator for rectangle', () => {
      const geometry = {
        type: EducationalGeometryType.RECTANGLE,
        params: { width: 1, height: 2 }
      };
      const result = validateGeometry(geometry);
      expect(result.isValid).toBe(true);
    });

    it('should delegate to correct validator for circle', () => {
      const geometry = {
        type: EducationalGeometryType.CIRCLE,
        params: { radius: 1 }
      };
      const result = validateGeometry(geometry);
      expect(result.isValid).toBe(true);
    });

    it('should delegate to correct validator for annulus', () => {
      const geometry = {
        type: EducationalGeometryType.ANNULUS,
        params: { innerRadius: 0.5, outerRadius: 1 }
      };
      const result = validateGeometry(geometry);
      expect(result.isValid).toBe(true);
    });

    it('should delegate to correct validator for L-shape', () => {
      const geometry = {
        type: EducationalGeometryType.L_SHAPE,
        params: { width: 2, height: 2, notchWidth: 1, notchHeight: 1 }
      };
      const result = validateGeometry(geometry);
      expect(result.isValid).toBe(true);
    });
  });

  describe('estimateMeshElements', () => {
    it('should estimate elements for rectangle', () => {
      const geometry = {
        type: EducationalGeometryType.RECTANGLE,
        params: { width: 2, height: 3 }
      };
      // Area = 6, density level 3 = 500 elements/m²
      const elements = estimateMeshElements(geometry, 3);
      expect(elements).toBe(3000);
    });

    it('should estimate elements for circle', () => {
      const geometry = {
        type: EducationalGeometryType.CIRCLE,
        params: { radius: 1 }
      };
      // Area = π, density level 1 = 50 elements/m²
      const elements = estimateMeshElements(geometry, 1);
      expect(elements).toBeCloseTo(157, 0); // π * 50 ≈ 157
    });

    it('should estimate elements for annulus', () => {
      const geometry = {
        type: EducationalGeometryType.ANNULUS,
        params: { innerRadius: 1, outerRadius: 2 }
      };
      // Area = π(4-1) = 3π, density level 2 = 200 elements/m²
      const elements = estimateMeshElements(geometry, 2);
      expect(elements).toBeCloseTo(1885, 0); // 3π * 200 ≈ 1885
    });

    it('should estimate elements for L-shape', () => {
      const geometry = {
        type: EducationalGeometryType.L_SHAPE,
        params: { width: 3, height: 3, notchWidth: 1, notchHeight: 1 }
      };
      // Area = 9 - 1 = 8, density level 4 = 1000 elements/m²
      const elements = estimateMeshElements(geometry, 4);
      expect(elements).toBe(8000);
    });

    it('should scale with mesh density', () => {
      const geometry = {
        type: EducationalGeometryType.RECTANGLE,
        params: { width: 1, height: 1 }
      };
      
      const elementsLevel1 = estimateMeshElements(geometry, 1);
      const elementsLevel5 = estimateMeshElements(geometry, 5);
      
      expect(elementsLevel5).toBeGreaterThan(elementsLevel1);
      expect(elementsLevel5 / elementsLevel1).toBe(40); // 2000/50 = 40
    });
  });
}); 