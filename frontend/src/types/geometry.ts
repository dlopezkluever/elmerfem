// Educational Geometry Types

export enum EducationalGeometryType {
  RECTANGLE = "rectangle",
  CIRCLE = "circle",
  ANNULUS = "annulus",
  L_SHAPE = "l_shape",
}

export interface RectangleParameters {
  width: number;
  height: number;
}

export interface CircleParameters {
  radius: number;
}

export interface AnnulusParameters {
  innerRadius: number;
  outerRadius: number;
}

export interface LShapeParameters {
  width: number;
  height: number;
  notchWidth: number;
  notchHeight: number;
}

export type GeometryParameters = 
  | { type: EducationalGeometryType.RECTANGLE; params: RectangleParameters }
  | { type: EducationalGeometryType.CIRCLE; params: CircleParameters }
  | { type: EducationalGeometryType.ANNULUS; params: AnnulusParameters }
  | { type: EducationalGeometryType.L_SHAPE; params: LShapeParameters };

export interface MeshDensityLevel {
  level: 1 | 2 | 3 | 4 | 5;
  label: string;
  description: string;
  estimatedElements: number;
}

export const MESH_DENSITY_LEVELS: MeshDensityLevel[] = [
  { level: 1, label: "Coarse", description: "Quick analysis", estimatedElements: 100 },
  { level: 2, label: "Medium-Coarse", description: "Basic accuracy", estimatedElements: 500 },
  { level: 3, label: "Medium", description: "Balanced speed/accuracy", estimatedElements: 1000 },
  { level: 4, label: "Fine", description: "High accuracy", estimatedElements: 2500 },
  { level: 5, label: "Very Fine", description: "Maximum accuracy", estimatedElements: 5000 },
];

export interface EducationalMeshParams {
  geometry: GeometryParameters;
  meshDensity: number;
  boundaryLayer: boolean;
  boundaryLayerThickness?: number;
}

export interface MeshQuality {
  minAngle: number;
  maxAngle: number;
  aspectRatioAvg: number;
  aspectRatioMax: number;
  totalElements: number;
  totalNodes: number;
}

export interface GeometryValidationResult {
  isValid: boolean;
  errors: { [field: string]: string };
} 