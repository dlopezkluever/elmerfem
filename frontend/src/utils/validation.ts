import { z } from 'zod';
import { SimulationType, BoundaryConditionType } from '../types/api';

// Geometry validation schemas
const boxDimensionsSchema = z.object({
  length: z.number().positive("Length must be positive"),
  width: z.number().positive("Width must be positive"),
  height: z.number().positive("Height must be positive"),
});

const cylinderDimensionsSchema = z.object({
  radius: z.number().positive("Radius must be positive"),
  height: z.number().positive("Height must be positive"),
});

const sphereDimensionsSchema = z.object({
  radius: z.number().positive("Radius must be positive"),
});

const geometrySchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("box"),
    dimensions: boxDimensionsSchema,
  }),
  z.object({
    type: z.literal("cylinder"),
    dimensions: cylinderDimensionsSchema,
  }),
  z.object({
    type: z.literal("sphere"),
    dimensions: sphereDimensionsSchema,
  }),
]);

// Material properties schema
const materialPropertiesSchema = z.object({
  E: z.number().positive("Young's Modulus must be positive").optional(),
  nu: z.number().min(0).max(0.5, "Poisson's Ratio must be between 0 and 0.5").optional(),
  rho: z.number().positive("Density must be positive").optional(),
  k: z.number().positive("Thermal Conductivity must be positive").optional(),
  C: z.number().positive("Heat Capacity must be positive").optional(),
});

// Boundary condition schema
const boundaryConditionSchema = z.object({
  type: z.nativeEnum(BoundaryConditionType),
  location: z.string().min(1, "Location is required"),
  value: z.number().optional(),
  values: z.array(z.number()).optional(),
}).refine(
  (data) => data.value !== undefined || data.values !== undefined,
  { message: "Either value or values must be provided" }
);

// Main simulation parameters schema
export const simulationParamsSchema = z.object({
  simulation_type: z.nativeEnum(SimulationType),
  geometry: geometrySchema,
  material_id: z.number().positive().optional(),
  custom_material: materialPropertiesSchema.optional(),
  boundary_conditions: z.array(boundaryConditionSchema).min(1, "At least one boundary condition is required"),
  mesh_density: z.number().min(0.1).max(10, "Mesh density must be between 0.1 and 10"),
  time_settings: z.record(z.string(), z.any()).optional(),
  solver_settings: z.record(z.string(), z.any()).optional(),
}).refine(
  (data) => data.material_id || data.custom_material,
  { message: "Either material_id or custom_material must be provided" }
);

// Form-specific schemas (for react-hook-form)
export const heatTransferFormSchema = z.object({
  geometry_type: z.enum(["box", "cylinder", "sphere"]),
  length: z.string().transform(Number).pipe(z.number().positive("Length must be positive")),
  width: z.string().transform(Number).pipe(z.number().positive("Width must be positive")),
  height: z.string().transform(Number).pipe(z.number().positive("Height must be positive")),
  radius: z.string().transform(Number).pipe(z.number().positive("Radius must be positive")),
  material_id: z.string().optional(), // Changed: material_id is now string and optional
  mesh_density: z.string().transform(Number).pipe(z.number().min(0.1).max(10)),
  // Boundary conditions for heat transfer
  temperature_left: z.string().transform(Number).pipe(z.number()),
  temperature_right: z.string().transform(Number).pipe(z.number()),
  heat_flux_top: z.string().transform(Number).pipe(z.number()).optional(),
  heat_flux_bottom: z.string().transform(Number).pipe(z.number()).optional(),
});

export const structuralMechanicsFormSchema = z.object({
  geometry_type: z.enum(["box", "cylinder", "sphere"]),
  length: z.string().transform(Number).pipe(z.number().positive("Length must be positive")),
  width: z.string().transform(Number).pipe(z.number().positive("Width must be positive")),
  height: z.string().transform(Number).pipe(z.number().positive("Height must be positive")),
  radius: z.string().transform(Number).pipe(z.number().positive("Radius must be positive")),
  material_id: z.string().optional(), // Changed: material_id is now string and optional
  mesh_density: z.string().transform(Number).pipe(z.number().min(0.1).max(10)),
  // Boundary conditions for structural mechanics
  fixed_surface: z.string().min(1, "Fixed surface is required"),
  force_x: z.string().transform(Number).pipe(z.number()),
  force_y: z.string().transform(Number).pipe(z.number()),
  force_z: z.string().transform(Number).pipe(z.number()),
  pressure: z.string().transform(Number).pipe(z.number()).optional(),
});

// Type exports
export type HeatTransferFormData = z.infer<typeof heatTransferFormSchema>;
export type StructuralMechanicsFormData = z.infer<typeof structuralMechanicsFormSchema>; 