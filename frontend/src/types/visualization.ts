// Visualization Types for 3D Results Display

export interface VTUMetadata {
  format: string;
  source_file: string;
  num_points: number;
  num_cells: number;
  conversion_timestamp: string;
  point_data_fields: string[];
  cell_data_fields: string[];
}

export interface VTUData {
  metadata: VTUMetadata;
  points: number[][]; // [[x,y,z], ...]
  cells: { [cellType: string]: number[][] }; // {triangles: [[i,j,k], ...]}
  point_data: { [field: string]: number[] }; // {Temperature: [t1,t2,...]}
  cell_data: { [field: string]: any };
  field_data: { [field: string]: any };
}

export enum ViewMode {
  TEMPERATURE = 'Temperature',
  HEAT_FLUX = 'Heat Flux',
  GRADIENT = 'Temperature Gradient'
}

export interface PlotlyMeshData {
  x: number[];
  y: number[];
  z: number[];
  i: number[];
  j: number[];
  k: number[];
  intensity: number[];
  colorscale: string;
  type: 'mesh3d';
  showscale: boolean;
  colorbar: {
    title: string;
    titleside: 'right' | 'left';
  };
}

export interface ResultStatistics {
  fieldName: string;
  min: number;
  max: number;
  mean: number;
  std: number;
  median: number;
  p25: number;
  p75: number;
  range: number;
  coefficientOfVariation: number;
  unit: string;
  sampleSize: number;
  hotSpots: Array<{
    value: number;
    location: [number, number, number];
    index: number;
  }>;
  minLocation: [number, number, number];
  maxLocation: [number, number, number];
}

export interface VisualizationProps {
  simulationId: string;
  className?: string;
  onError?: (error: string) => void;
}

export interface UseSimulationResultResult {
  data: VTUData | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  statistics: ResultStatistics | null;
}

export interface ViewControlsProps {
  selectedField: ViewMode;
  onFieldChange: (field: ViewMode) => void;
  availableFields: ViewMode[];
  disabled?: boolean;
}

export interface EducationalPanelProps {
  statistics: ResultStatistics | null;
  selectedField: ViewMode;
  isExpanded: boolean;
  onToggleExpanded: () => void;
}

// Educational content interfaces
export interface EducationalContent {
  title: string;
  description: string;
  keyInsights: string[];
  physicalMeaning: string;
  unitExplanation: string;
}

export const EDUCATIONAL_CONTENT: Record<ViewMode, EducationalContent> = {
  [ViewMode.TEMPERATURE]: {
    title: "Temperature Distribution",
    description: "Shows how temperature varies throughout your material.",
    keyInsights: [
      "Red areas indicate high temperatures",
      "Blue areas indicate low temperatures", 
      "Smooth gradients show good heat conduction",
      "Sharp changes indicate thermal barriers"
    ],
    physicalMeaning: "Temperature represents the average kinetic energy of molecules at each point in the material.",
    unitExplanation: "Temperature is measured in degrees Celsius (°C) or Kelvin (K)."
  },
  [ViewMode.HEAT_FLUX]: {
    title: "Heat Flux Distribution", 
    description: "Shows the rate of heat transfer through the material.",
    keyInsights: [
      "Higher values indicate faster heat transfer",
      "Direction shows heat flow path",
      "Concentrated areas show thermal bottlenecks",
      "Uniform distribution indicates efficient design"
    ],
    physicalMeaning: "Heat flux represents the amount of thermal energy flowing through a unit area per unit time.",
    unitExplanation: "Heat flux is measured in Watts per square meter (W/m²)."
  },
  [ViewMode.GRADIENT]: {
    title: "Temperature Gradient",
    description: "Shows how rapidly temperature changes in space.",
    keyInsights: [
      "High gradients indicate rapid temperature changes",
      "Low gradients indicate uniform temperature regions",
      "Gradient direction shows steepest temperature change",
      "Can identify thermal stress concentration areas"
    ],
    physicalMeaning: "Temperature gradient indicates the driving force for heat conduction according to Fourier's law.",
    unitExplanation: "Temperature gradient is measured in degrees per meter (°C/m or K/m)."
  }
}; 