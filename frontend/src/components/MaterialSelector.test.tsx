import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MaterialSelector } from './MaterialSelector';
import { Material } from '../api';

describe('MaterialSelector', () => {
  const mockMaterials: Material[] = [
    {
      id: 'steel',
      name: 'Steel',
      E: 210e9,
      nu: 0.3,
      k: 50,
      rho: 7850,
      description: 'Common structural steel',
      units: {
        E: 'Pa',
        nu: 'dimensionless',
        k: 'W/(m·K)',
        rho: 'kg/m³'
      }
    },
    {
      id: 'aluminum',
      name: 'Aluminum',
      E: 70e9,
      nu: 0.33,
      k: 237,
      rho: 2700,
      description: 'Aluminum alloy',
    }
  ];

  const mockOnChange = vi.fn();

  it('renders material dropdown with options', () => {
    render(
      <MaterialSelector
        materials={mockMaterials}
        value=""
        onChange={mockOnChange}
        error={null}
        name="material_id"
      />
    );

    expect(screen.getByText('Select Material')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('View Properties')).toBeInTheDocument();
  });

  it('displays all materials in dropdown', () => {
    render(
      <MaterialSelector
        materials={mockMaterials}
        value=""
        onChange={mockOnChange}
        error={null}
        name="material_id"
      />
    );

    const select = screen.getByRole('combobox');
    expect(select.children).toHaveLength(3); // "Select a material..." + 2 materials
    expect(screen.getByText('Steel')).toBeInTheDocument();
    expect(screen.getByText('Aluminum')).toBeInTheDocument();
  });

  it('calls onChange when material is selected', () => {
    render(
      <MaterialSelector
        materials={mockMaterials}
        value=""
        onChange={mockOnChange}
        error={null}
        name="material_id"
      />
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'steel' } });
    expect(mockOnChange).toHaveBeenCalledWith('steel');
  });

  it('disables View Properties button when no material is selected', () => {
    render(
      <MaterialSelector
        materials={mockMaterials}
        value=""
        onChange={mockOnChange}
        error={null}
        name="material_id"
      />
    );

    const button = screen.getByText('View Properties');
    expect(button).toBeDisabled();
  });

  it('enables View Properties button when material is selected', () => {
    render(
      <MaterialSelector
        materials={mockMaterials}
        value="steel"
        onChange={mockOnChange}
        error={null}
        name="material_id"
      />
    );

    const button = screen.getByText('View Properties');
    expect(button).not.toBeDisabled();
  });

  it('shows modal when View Properties is clicked', () => {
    render(
      <MaterialSelector
        materials={mockMaterials}
        value="steel"
        onChange={mockOnChange}
        error={null}
        name="material_id"
      />
    );

    const button = screen.getByText('View Properties');
    fireEvent.click(button);

    expect(screen.getByText('Steel Properties')).toBeInTheDocument();
    expect(screen.getByText('Common structural steel')).toBeInTheDocument();
    expect(screen.getByText("Young's Modulus (E)")).toBeInTheDocument();
    expect(screen.getByText('2.10e+11')).toBeInTheDocument();
  });

  it('closes modal when Close button is clicked', () => {
    render(
      <MaterialSelector
        materials={mockMaterials}
        value="steel"
        onChange={mockOnChange}
        error={null}
        name="material_id"
      />
    );

    const viewButton = screen.getByText('View Properties');
    fireEvent.click(viewButton);

    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);

    expect(screen.queryByText('Steel Properties')).not.toBeInTheDocument();
  });

  it('displays error message when error prop is provided', () => {
    const error = { message: 'Please select a material' };
    render(
      <MaterialSelector
        materials={mockMaterials}
        value=""
        onChange={mockOnChange}
        error={error}
        name="material_id"
      />
    );

    expect(screen.getByText('Please select a material')).toBeInTheDocument();
  });
}); 