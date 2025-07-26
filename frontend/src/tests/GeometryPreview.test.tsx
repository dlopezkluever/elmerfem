import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GeometryPreview } from '../components/simulation/GeometryPreview';
import { EducationalGeometryType } from '../types/geometry';

describe('GeometryPreview', () => {
  it('should show placeholder when no geometry is selected', () => {
    render(
      <GeometryPreview 
        geometry={null}
        meshDensity={3}
        estimatedElements={0}
      />
    );
    
    expect(screen.getByText('Select a geometry type to preview')).toBeInTheDocument();
  });

  it('should render rectangle geometry', () => {
    const geometry = {
      type: EducationalGeometryType.RECTANGLE,
      params: { width: 2, height: 3 }
    };
    
    const { container } = render(
      <GeometryPreview 
        geometry={geometry}
        meshDensity={3}
        estimatedElements={1000}
      />
    );
    
    expect(screen.getByText('Geometry Preview')).toBeInTheDocument();
    expect(screen.getByText('Mesh Density: Level 3')).toBeInTheDocument();
    expect(screen.getByText('Estimated Elements: ~1,000')).toBeInTheDocument();
    
    const rect = container.querySelector('rect');
    expect(rect).toBeInTheDocument();
  });

  it('should render circle geometry', () => {
    const geometry = {
      type: EducationalGeometryType.CIRCLE,
      params: { radius: 1.5 }
    };
    
    const { container } = render(
      <GeometryPreview 
        geometry={geometry}
        meshDensity={2}
        estimatedElements={500}
      />
    );
    
    expect(screen.getByText('Mesh Density: Level 2')).toBeInTheDocument();
    expect(screen.getByText('Estimated Elements: ~500')).toBeInTheDocument();
    
    const circles = container.querySelectorAll('circle');
    expect(circles.length).toBeGreaterThan(0);
  });

  it('should render annulus geometry', () => {
    const geometry = {
      type: EducationalGeometryType.ANNULUS,
      params: { innerRadius: 0.5, outerRadius: 1.5 }
    };
    
    const { container } = render(
      <GeometryPreview 
        geometry={geometry}
        meshDensity={4}
        estimatedElements={2500}
      />
    );
    
    expect(screen.getByText('Mesh Density: Level 4')).toBeInTheDocument();
    
    const circles = container.querySelectorAll('circle');
    expect(circles.length).toBeGreaterThan(1); // Should have at least inner and outer circles
  });

  it('should render L-shape geometry', () => {
    const geometry = {
      type: EducationalGeometryType.L_SHAPE,
      params: { width: 3, height: 3, notchWidth: 1.5, notchHeight: 1.5 }
    };
    
    const { container } = render(
      <GeometryPreview 
        geometry={geometry}
        meshDensity={5}
        estimatedElements={5000}
      />
    );
    
    expect(screen.getByText('Mesh Density: Level 5')).toBeInTheDocument();
    expect(screen.getByText('Estimated Elements: ~5,000')).toBeInTheDocument();
    
    const path = container.querySelector('path');
    expect(path).toBeInTheDocument();
  });

  it('should render mesh grid lines based on density', () => {
    const geometry = {
      type: EducationalGeometryType.RECTANGLE,
      params: { width: 2, height: 2 }
    };
    
    const { container: container1 } = render(
      <GeometryPreview 
        geometry={geometry}
        meshDensity={1}
        estimatedElements={100}
      />
    );
    
    const lines1 = container1.querySelectorAll('line');
    
    const { container: container5 } = render(
      <GeometryPreview 
        geometry={geometry}
        meshDensity={5}
        estimatedElements={2000}
      />
    );
    
    const lines5 = container5.querySelectorAll('line');
    
    // Higher density should have more mesh lines
    expect(lines5.length).toBeGreaterThan(lines1.length);
  });

  it('should format large numbers with commas', () => {
    const geometry = {
      type: EducationalGeometryType.RECTANGLE,
      params: { width: 10, height: 10 }
    };
    
    render(
      <GeometryPreview 
        geometry={geometry}
        meshDensity={5}
        estimatedElements={10000}
      />
    );
    
    expect(screen.getByText('Estimated Elements: ~10,000')).toBeInTheDocument();
  });
}); 