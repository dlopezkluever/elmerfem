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