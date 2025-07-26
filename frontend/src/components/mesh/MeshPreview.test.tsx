import { render, screen } from '@testing-library/react';
import { MeshPreview } from './MeshPreview';

// Mock the Three.js components since they require WebGL context
jest.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: any) => <div data-testid="canvas">{children}</div>,
  useFrame: () => {},
  useThree: () => ({ scene: {} }),
  useLoader: () => null,
}));

jest.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
  PerspectiveCamera: () => null,
}));

jest.mock('dat.gui', () => ({
  GUI: jest.fn().mockImplementation(() => ({
    addFolder: jest.fn().mockReturnValue({
      add: jest.fn().mockReturnValue({ name: jest.fn(), onChange: jest.fn() }),
      open: jest.fn(),
    }),
    domElement: { style: {} },
    destroy: jest.fn(),
  })),
}));

describe('MeshPreview Component', () => {
  it('renders without crashing', () => {
    render(<MeshPreview />);
    expect(screen.getByText(/Use mouse to rotate/i)).toBeInTheDocument();
  });

  it('renders with mesh ID', () => {
    render(<MeshPreview meshId="test-123" />);
    expect(screen.getByText(/Loading mesh preview/i)).toBeInTheDocument();
  });

  it('displays quality metrics when provided', () => {
    const mockMetrics = {
      total_nodes: 1000,
      total_elements: 2000,
      min_angle: 30.0,
      max_angle: 90.0,
      aspect_ratio_avg: 1.5,
      aspect_ratio_max: 2.0,
    };

    render(<MeshPreview qualityMetrics={mockMetrics} />);
    
    expect(screen.getByText(/Mesh Quality Metrics/i)).toBeInTheDocument();
    expect(screen.getByText(/Nodes: 1,000/i)).toBeInTheDocument();
    expect(screen.getByText(/Elements: 2,000/i)).toBeInTheDocument();
  });
}); 