import { 
  GeometryParameters, 
  EducationalGeometryType, 
  GeometryValidationResult,
  RectangleParameters,
  CircleParameters,
  AnnulusParameters,
  LShapeParameters 
} from '../types/geometry';

const MIN_DIMENSION = 0.001; // 1mm minimum
const MAX_DIMENSION = 10; // 10m maximum

export function validateRectangle(params: RectangleParameters): GeometryValidationResult {
  const errors: { [field: string]: string } = {};

  if (params.width < MIN_DIMENSION || params.width > MAX_DIMENSION) {
    errors.width = `Width must be between ${MIN_DIMENSION}m and ${MAX_DIMENSION}m`;
  }

  if (params.height < MIN_DIMENSION || params.height > MAX_DIMENSION) {
    errors.height = `Height must be between ${MIN_DIMENSION}m and ${MAX_DIMENSION}m`;
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

export function validateCircle(params: CircleParameters): GeometryValidationResult {
  const errors: { [field: string]: string } = {};

  if (params.radius < MIN_DIMENSION || params.radius > MAX_DIMENSION / 2) {
    errors.radius = `Radius must be between ${MIN_DIMENSION}m and ${MAX_DIMENSION / 2}m`;
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

export function validateAnnulus(params: AnnulusParameters): GeometryValidationResult {
  const errors: { [field: string]: string } = {};

  if (params.innerRadius < MIN_DIMENSION || params.innerRadius > MAX_DIMENSION / 2) {
    errors.innerRadius = `Inner radius must be between ${MIN_DIMENSION}m and ${MAX_DIMENSION / 2}m`;
  }

  if (params.outerRadius < MIN_DIMENSION || params.outerRadius > MAX_DIMENSION / 2) {
    errors.outerRadius = `Outer radius must be between ${MIN_DIMENSION}m and ${MAX_DIMENSION / 2}m`;
  }

  if (params.innerRadius >= params.outerRadius) {
    errors.innerRadius = 'Inner radius must be smaller than outer radius';
    errors.outerRadius = 'Outer radius must be larger than inner radius';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

export function validateLShape(params: LShapeParameters): GeometryValidationResult {
  const errors: { [field: string]: string } = {};

  if (params.width < MIN_DIMENSION || params.width > MAX_DIMENSION) {
    errors.width = `Width must be between ${MIN_DIMENSION}m and ${MAX_DIMENSION}m`;
  }

  if (params.height < MIN_DIMENSION || params.height > MAX_DIMENSION) {
    errors.height = `Height must be between ${MIN_DIMENSION}m and ${MAX_DIMENSION}m`;
  }

  if (params.notchWidth < MIN_DIMENSION || params.notchWidth >= params.width) {
    errors.notchWidth = 'Notch width must be smaller than total width';
  }

  if (params.notchHeight < MIN_DIMENSION || params.notchHeight >= params.height) {
    errors.notchHeight = 'Notch height must be smaller than total height';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

export function validateGeometry(geometry: GeometryParameters): GeometryValidationResult {
  switch (geometry.type) {
    case EducationalGeometryType.RECTANGLE:
      return validateRectangle(geometry.params);
    case EducationalGeometryType.CIRCLE:
      return validateCircle(geometry.params);
    case EducationalGeometryType.ANNULUS:
      return validateAnnulus(geometry.params);
    case EducationalGeometryType.L_SHAPE:
      return validateLShape(geometry.params);
    default:
      return {
        isValid: false,
        errors: { type: 'Unknown geometry type' }
      };
  }
}

export function estimateMeshElements(geometry: GeometryParameters, meshDensity: number): number {
  let area = 0;
  
  switch (geometry.type) {
    case EducationalGeometryType.RECTANGLE:
      area = geometry.params.width * geometry.params.height;
      break;
    case EducationalGeometryType.CIRCLE:
      area = Math.PI * geometry.params.radius * geometry.params.radius;
      break;
    case EducationalGeometryType.ANNULUS:
      area = Math.PI * (geometry.params.outerRadius ** 2 - geometry.params.innerRadius ** 2);
      break;
    case EducationalGeometryType.L_SHAPE:
      area = (geometry.params.width * geometry.params.height) - 
             (geometry.params.notchWidth * geometry.params.notchHeight);
      break;
  }

  // Estimate based on mesh density level (1-5) and area
  const baseElementsPerSquareMeter = [50, 200, 500, 1000, 2000][meshDensity - 1];
  return Math.round(area * baseElementsPerSquareMeter);
} 