// API Types matching backend DTOs

export enum SimulationType {
  HEAT_TRANSFER = "heat_transfer",
  STRUCTURAL_MECHANICS = "structural_mechanics",
  FLUID_DYNAMICS = "fluid_dynamics", // Future
  ELECTROMAGNETICS = "electromagnetics", // Future
}

export enum JobStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export enum BoundaryConditionType {
  TEMPERATURE = "temperature",
  HEAT_FLUX = "heat_flux",
  CONVECTION = "convection",
  FIXED = "fixed",
  FORCE = "force",
  PRESSURE = "pressure",
  DISPLACEMENT = "displacement",
}

export interface MaterialProperties {
  E?: number; // Young's Modulus (Pa)
  nu?: number; // Poisson's Ratio
  rho?: number; // Density (kg/m³)
  k?: number; // Thermal Conductivity (W/mK)
  C?: number; // Heat Capacity (J/kgK)
}

export interface Material {
  id: number;
  name: string;
  properties: MaterialProperties;
}

export interface BoundaryCondition {
  type: BoundaryConditionType;
  location: string;
  value?: number;
  values?: number[];
}

export interface GeometryParams {
  type: "box" | "cylinder" | "sphere";
  dimensions: {
    length?: number;
    width?: number;
    height?: number;
    radius?: number;
  };
}

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

export interface SimulationParams {
  simulation_type: SimulationType;
  geometry: GeometryParams;
  material_id?: number;
  custom_material?: MaterialProperties;
  boundary_conditions: BoundaryCondition[];
  mesh_density: number;
  time_settings?: Record<string, any>;
  solver_settings?: Record<string, any>;
}

export interface SimulationStatus {
  id: string;
  status: JobStatus;
  progress: number;
  message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  current_step?: string;
  total_steps?: number;
}

export interface SimulationResult {
  id: string;
  status: JobStatus;
  result_files: string[];
  output_directory?: string;
  summary?: Record<string, any>;
  vtk_file?: string;
  log_file?: string;
  sif_file?: string;
}

export interface MaterialsResponse {
  materials: Material[];
} 