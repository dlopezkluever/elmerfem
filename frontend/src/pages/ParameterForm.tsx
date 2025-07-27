import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { SimulationType, SimulationParams, BoundaryConditionType } from '../types/api';
import { 
  heatTransferFormSchema, 
  structuralMechanicsFormSchema
} from '../utils/validation';
import { simulationApi } from '../api';
import { useMaterials } from '../hooks/useMaterials';
import { MaterialSelector } from '../components/MaterialSelector';

function ParameterForm() {
  const navigate = useNavigate();
  const [simulationType, setSimulationType] = useState<SimulationType | null>(null);
  const { materials, loading: materialsLoading } = useMaterials();

  useEffect(() => {
    const stored = sessionStorage.getItem('selectedSimulationType');
    if (!stored) {
      navigate('/');
      return;
    }
    setSimulationType(stored as SimulationType);
  }, [navigate]);

  if (!simulationType || materialsLoading) {
    return <div className="text-center py-20">Loading...</div>;
  }

  if (simulationType === SimulationType.HEAT_TRANSFER) {
    return <HeatTransferForm materials={materials} />;
  } else {
    return <StructuralMechanicsForm materials={materials} />;
  }
}

// Heat Transfer Form Component
function HeatTransferForm({ materials }: { materials: any[] }) {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [geometryType, setGeometryType] = useState<'box' | 'cylinder' | 'sphere'>('box');

  // Form data type for inputs (all strings)
  type HeatTransferInputs = {
    geometry_type: "box" | "cylinder" | "sphere";
    length: string;
    width: string;
    height: string;
    radius: string;
    material_id: string;
    mesh_density: string;
    temperature_left: string;
    temperature_right: string;
    heat_flux_top?: string;
    heat_flux_bottom?: string;
  };

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors },
  } = useForm<HeatTransferInputs>({
    resolver: zodResolver(heatTransferFormSchema) as any,
    defaultValues: {
      geometry_type: 'box',
      mesh_density: '1.0',
      material_id: '1',
      temperature_left: '100',
      temperature_right: '0',
      length: '1',
      width: '1',
      height: '1',
      radius: '0.5',
    },
  });

  // Watch geometry type to show/hide relevant fields
  const watchedGeometryType = watch('geometry_type');
  useEffect(() => {
    setGeometryType(watchedGeometryType);
  }, [watchedGeometryType]);

  const onSubmit = async (data: HeatTransferInputs) => {
    try {
      setSubmitting(true);
      
      // Transform form data to API format - convert strings to numbers
      const params: SimulationParams = {
        simulation_type: SimulationType.HEAT_TRANSFER,
        geometry: {
          type: data.geometry_type,
          dimensions: data.geometry_type === 'sphere' 
            ? { radius: Number(data.radius) }
            : data.geometry_type === 'cylinder'
            ? { radius: Number(data.radius), height: Number(data.height) }
            : { length: Number(data.length), width: Number(data.width), height: Number(data.height) }
        },
        // Handle material selection - provide fallback if no material selected
        material_id: data.material_id && data.material_id.trim() !== '' ? data.material_id : undefined,
        custom_material: (!data.material_id || data.material_id.trim() === '') ? {
          k: 50.0,  // Default thermal conductivity (Steel-like)
          rho: 7850.0,  // Default density (Steel-like)
          C: 500.0  // Default heat capacity
        } : undefined,
        mesh_density: Number(data.mesh_density),
        boundary_conditions: [
          {
            type: BoundaryConditionType.TEMPERATURE,
            location: 'left',
            value: Number(data.temperature_left),
          },
          {
            type: BoundaryConditionType.TEMPERATURE,
            location: 'right',
            value: Number(data.temperature_right),
          },
        ],
      };

      if (data.heat_flux_top) {
        params.boundary_conditions.push({
          type: BoundaryConditionType.HEAT_FLUX,
          location: 'top',
          value: Number(data.heat_flux_top),
        });
      }

      if (data.heat_flux_bottom) {
        params.boundary_conditions.push({
          type: BoundaryConditionType.HEAT_FLUX,
          location: 'bottom',
          value: Number(data.heat_flux_bottom),
        });
      }
      
      // Create simulation
      const result = await simulationApi.createSimulation(params);
      
      // Navigate to progress page
      navigate(`/progress/${result.id}`);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to create simulation');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Heat Transfer Simulation</h1>

      <form onSubmit={handleSubmit(onSubmit as any)} className="space-y-8">
        {/* Geometry Section */}
        <div className="card-neumorphic p-8">
          <h2 className="text-2xl font-semibold mb-6">Geometry</h2>
          
          <div className="grid gap-6">
            <FormField
              label="Geometry Type"
              {...register('geometry_type')}
              type="select"
              options={[
                { value: 'box', label: 'Box' },
                { value: 'cylinder', label: 'Cylinder' },
                { value: 'sphere', label: 'Sphere' },
              ]}
              error={errors.geometry_type}
            />

            {geometryType === 'box' && (
              <>
                <FormField label="Length (m)" {...register('length')} error={errors.length} />
                <FormField label="Width (m)" {...register('width')} error={errors.width} />
                <FormField label="Height (m)" {...register('height')} error={errors.height} />
              </>
            )}

            {geometryType === 'cylinder' && (
              <>
                <FormField label="Radius (m)" {...register('radius')} error={errors.radius} />
                <FormField label="Height (m)" {...register('height')} error={errors.height} />
              </>
            )}

            {geometryType === 'sphere' && (
              <FormField label="Radius (m)" {...register('radius')} error={errors.radius} />
            )}
          </div>
        </div>

        {/* Material Section */}
        <div className="card-neumorphic p-8">
          <h2 className="text-2xl font-semibold mb-6">Material</h2>
          
          <Controller
            name="material_id"
            control={control}
            render={({ field }) => (
              <MaterialSelector
                materials={materials}
                value={field.value}
                onChange={field.onChange}
                error={errors.material_id}
                name={field.name}
              />
            )}
          />
        </div>

        {/* Boundary Conditions Section */}
        <div className="card-neumorphic p-8">
          <h2 className="text-2xl font-semibold mb-6">Boundary Conditions</h2>
          
          <div className="grid gap-6">
            <FormField 
              label="Temperature Left (°C)" 
              {...register('temperature_left')} 
              error={errors.temperature_left}
            />
            <FormField 
              label="Temperature Right (°C)" 
              {...register('temperature_right')} 
              error={errors.temperature_right}
            />
            <FormField 
              label="Heat Flux Top (W/m²) - Optional" 
              {...register('heat_flux_top')} 
              error={errors.heat_flux_top}
            />
            <FormField 
              label="Heat Flux Bottom (W/m²) - Optional" 
              {...register('heat_flux_bottom')} 
              error={errors.heat_flux_bottom}
            />
          </div>
        </div>

        {/* Mesh Settings */}
        <div className="card-neumorphic p-8">
          <h2 className="text-2xl font-semibold mb-6">Mesh Settings</h2>
          
          <FormField
            label="Mesh Density (0.1 - 10)"
            {...register('mesh_density')}
            error={errors.mesh_density}
            helperText="Higher values create finer mesh but increase computation time"
          />
        </div>

        {/* Submit Buttons */}
        <div className="flex gap-4 justify-end">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-neumorphic px-8 py-3"
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-neumorphic-primary px-8 py-3"
            disabled={submitting}
          >
            {submitting ? 'Creating...' : 'Run Simulation'}
          </button>
        </div>
      </form>
    </div>
  );
}

// Structural Mechanics Form Component
function StructuralMechanicsForm({ materials }: { materials: any[] }) {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [geometryType, setGeometryType] = useState<'box' | 'cylinder' | 'sphere'>('box');

  // Form data type for inputs (all strings)
  type StructuralMechanicsInputs = {
    geometry_type: "box" | "cylinder" | "sphere";
    length: string;
    width: string;
    height: string;
    radius: string;
    material_id: string;
    mesh_density: string;
    fixed_surface: string;
    force_x: string;
    force_y: string;
    force_z: string;
    pressure?: string;
  };

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors },
  } = useForm<StructuralMechanicsInputs>({
    resolver: zodResolver(structuralMechanicsFormSchema) as any,
    defaultValues: {
      geometry_type: 'box',
      mesh_density: '1.0',
      material_id: '1',
      fixed_surface: 'bottom',
      force_x: '0',
      force_y: '0',
      force_z: '-1000',
      length: '1',
      width: '1',
      height: '1',
      radius: '0.5',
    },
  });

  // Watch geometry type to show/hide relevant fields
  const watchedGeometryType = watch('geometry_type');
  useEffect(() => {
    setGeometryType(watchedGeometryType);
  }, [watchedGeometryType]);

  const onSubmit = async (data: StructuralMechanicsInputs) => {
    try {
      setSubmitting(true);
      
      // Transform form data to API format - convert strings to numbers
      const params: SimulationParams = {
        simulation_type: SimulationType.STRUCTURAL_MECHANICS,
        geometry: {
          type: data.geometry_type,
          dimensions: data.geometry_type === 'sphere' 
            ? { radius: Number(data.radius) }
            : data.geometry_type === 'cylinder'
            ? { radius: Number(data.radius), height: Number(data.height) }
            : { length: Number(data.length), width: Number(data.width), height: Number(data.height) }
        },
        material_id: data.material_id && data.material_id.trim() !== '' ? data.material_id : undefined,
        custom_material: (!data.material_id || data.material_id.trim() === '') ? {
          E: 200e9, // Default Young's Modulus (Steel-like)
          nu: 0.3, // Default Poisson's Ratio (Steel-like)
          rho: 7850.0, // Default density (Steel-like)
          C: 500.0 // Default heat capacity
        } : undefined,
        mesh_density: Number(data.mesh_density),
        boundary_conditions: [
          {
            type: BoundaryConditionType.FIXED,
            location: data.fixed_surface,
            value: 0.0, // Fixed constraints typically have value 0
          },
          {
            type: BoundaryConditionType.FORCE,
            location: 'top',
            value: Number(data.force_x),
            component: 'x',
          },
          {
            type: BoundaryConditionType.FORCE,
            location: 'top',
            value: Number(data.force_y),
            component: 'y',
          },
          {
            type: BoundaryConditionType.FORCE,
            location: 'top',
            value: Number(data.force_z),
            component: 'z',
          },
        ],
      };

      if (data.pressure) {
        params.boundary_conditions.push({
          type: BoundaryConditionType.PRESSURE,
          location: 'all',
          value: Number(data.pressure),
        });
      }
      
      // Create simulation
      const result = await simulationApi.createSimulation(params);
      
      // Navigate to progress page
      navigate(`/progress/${result.id}`);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to create simulation');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Structural Mechanics Simulation</h1>

      <form onSubmit={handleSubmit(onSubmit as any)} className="space-y-8">
        {/* Geometry Section */}
        <div className="card-neumorphic p-8">
          <h2 className="text-2xl font-semibold mb-6">Geometry</h2>
          
          <div className="grid gap-6">
            <FormField
              label="Geometry Type"
              {...register('geometry_type')}
              type="select"
              options={[
                { value: 'box', label: 'Box' },
                { value: 'cylinder', label: 'Cylinder' },
                { value: 'sphere', label: 'Sphere' },
              ]}
              error={errors.geometry_type}
            />

            {geometryType === 'box' && (
              <>
                <FormField label="Length (m)" {...register('length')} error={errors.length} />
                <FormField label="Width (m)" {...register('width')} error={errors.width} />
                <FormField label="Height (m)" {...register('height')} error={errors.height} />
              </>
            )}

            {geometryType === 'cylinder' && (
              <>
                <FormField label="Radius (m)" {...register('radius')} error={errors.radius} />
                <FormField label="Height (m)" {...register('height')} error={errors.height} />
              </>
            )}

            {geometryType === 'sphere' && (
              <FormField label="Radius (m)" {...register('radius')} error={errors.radius} />
            )}
          </div>
        </div>

        {/* Material Section */}
        <div className="card-neumorphic p-8">
          <h2 className="text-2xl font-semibold mb-6">Material</h2>
          
          <Controller
            name="material_id"
            control={control}
            render={({ field }) => (
              <MaterialSelector
                materials={materials}
                value={field.value}
                onChange={field.onChange}
                error={errors.material_id}
                name={field.name}
              />
            )}
          />
        </div>

        {/* Boundary Conditions Section */}
        <div className="card-neumorphic p-8">
          <h2 className="text-2xl font-semibold mb-6">Boundary Conditions</h2>
          
          <div className="grid gap-6">
            <FormField
              label="Fixed Surface"
              {...register('fixed_surface')}
              type="select"
              options={[
                { value: 'bottom', label: 'Bottom' },
                { value: 'top', label: 'Top' },
                { value: 'left', label: 'Left' },
                { value: 'right', label: 'Right' },
              ]}
              error={errors.fixed_surface}
            />
            
            <div className="grid grid-cols-3 gap-4">
              <FormField 
                label="Force X (N)" 
                {...register('force_x')} 
                error={errors.force_x}
              />
              <FormField 
                label="Force Y (N)" 
                {...register('force_y')} 
                error={errors.force_y}
              />
              <FormField 
                label="Force Z (N)" 
                {...register('force_z')} 
                error={errors.force_z}
              />
            </div>

            <FormField 
              label="Pressure (Pa) - Optional" 
              {...register('pressure')} 
              error={errors.pressure}
            />
          </div>
        </div>

        {/* Mesh Settings */}
        <div className="card-neumorphic p-8">
          <h2 className="text-2xl font-semibold mb-6">Mesh Settings</h2>
          
          <FormField
            label="Mesh Density (0.1 - 10)"
            {...register('mesh_density')}
            error={errors.mesh_density}
            helperText="Higher values create finer mesh but increase computation time"
          />
        </div>

        {/* Submit Buttons */}
        <div className="flex gap-4 justify-end">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-neumorphic px-8 py-3"
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-neumorphic-primary px-8 py-3"
            disabled={submitting}
          >
            {submitting ? 'Creating...' : 'Run Simulation'}
          </button>
        </div>
      </form>
    </div>
  );
}

// Reusable Form Field Component
interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement | HTMLSelectElement> {
  label: string;
  error?: any;
  helperText?: string;
  type?: 'text' | 'number' | 'select';
  options?: { value: string; label: string }[];
}

const FormField = React.forwardRef<HTMLInputElement | HTMLSelectElement, FormFieldProps>(
  ({ label, error, helperText, type = 'text', options, ...props }, ref) => {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
        {type === 'select' ? (
          <select
            ref={ref as React.Ref<HTMLSelectElement>}
            className="input-neumorphic w-full"
            {...props}
          >
            {options?.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            ref={ref as React.Ref<HTMLInputElement>}
            type={type}
            className="input-neumorphic w-full"
            {...props}
          />
        )}
        {helperText && !error && (
          <p className="mt-1 text-sm text-gray-500">{helperText}</p>
        )}
        {error && (
          <p className="mt-1 text-sm text-red-600">{error.message}</p>
        )}
      </div>
    );
  }
);

FormField.displayName = 'FormField';

export default ParameterForm; 