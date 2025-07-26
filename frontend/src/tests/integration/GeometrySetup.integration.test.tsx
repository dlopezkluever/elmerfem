import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import geometryReducer from '../../store/slices/geometrySlice';
import { GeometrySetupConnected } from '../../components/simulation/GeometrySetupConnected';

describe('GeometrySetup Integration Tests', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        geometry: geometryReducer,
      },
    });
  });

  it('should complete full workflow: select geometry, set parameters, and validate', async () => {
    const user = userEvent.setup();
    
    render(
      <Provider store={store}>
        <GeometrySetupConnected />
      </Provider>
    );

    // 1. Initially no geometry is selected
    expect(screen.queryByText('Geometry Parameters')).not.toBeInTheDocument();

    // 2. Select Rectangle geometry
    const rectangleButton = screen.getByRole('button', { name: /rectangle/i });
    await user.click(rectangleButton);

    // 3. Geometry parameters form should appear
    await waitFor(() => {
      expect(screen.getByText('Geometry Parameters')).toBeInTheDocument();
    });
    
    expect(screen.getByLabelText(/width/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/height/i)).toBeInTheDocument();

    // 4. Set valid parameters
    const widthInput = screen.getByLabelText(/width/i) as HTMLInputElement;
    const heightInput = screen.getByLabelText(/height/i) as HTMLInputElement;
    
    await user.clear(widthInput);
    await user.type(widthInput, '2.5');
    
    await user.clear(heightInput);
    await user.type(heightInput, '3.5');

    // 5. Check mesh settings are shown
    expect(screen.getByText('Mesh Settings')).toBeInTheDocument();
    
    // 6. Change mesh density
    const fineDensity = screen.getByLabelText(/fine/i);
    await user.click(fineDensity);

    // 7. Enable boundary layer
    const boundaryLayerCheckbox = screen.getByLabelText(/enable boundary layer/i);
    await user.click(boundaryLayerCheckbox);

    // 8. Boundary layer thickness input should appear
    await waitFor(() => {
      expect(screen.getByLabelText(/boundary layer thickness/i)).toBeInTheDocument();
    });

    // 9. Verify preview is updated
    expect(screen.getByText('Geometry Preview')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/mesh density: level 4/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/estimated elements/i)).toBeInTheDocument();
  });

  it('should show validation errors for invalid parameters', async () => {
    const user = userEvent.setup();
    
    render(
      <Provider store={store}>
        <GeometrySetupConnected />
      </Provider>
    );

    // Select Circle geometry
    const circleButton = screen.getByRole('button', { name: /circle/i });
    await user.click(circleButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/radius/i)).toBeInTheDocument();
    });

    // Enter invalid radius
    const radiusInput = screen.getByLabelText(/radius/i) as HTMLInputElement;
    await user.clear(radiusInput);
    await user.type(radiusInput, '10'); // Too large

    // Should show error
    await waitFor(() => {
      expect(screen.getByText(/radius must be between/i)).toBeInTheDocument();
    });
  });

  it('should handle annulus validation correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <Provider store={store}>
        <GeometrySetupConnected />
      </Provider>
    );

    // Select Annulus geometry
    const annulusButton = screen.getByRole('button', { name: /annulus/i });
    await user.click(annulusButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/inner radius/i)).toBeInTheDocument();
    });

    // Set inner radius larger than outer radius
    const innerRadiusInput = screen.getByLabelText(/inner radius/i) as HTMLInputElement;
    const outerRadiusInput = screen.getByLabelText(/outer radius/i) as HTMLInputElement;
    
    await user.clear(innerRadiusInput);
    await user.type(innerRadiusInput, '2');
    
    await user.clear(outerRadiusInput);
    await user.type(outerRadiusInput, '1');

    // Should show errors
    await waitFor(() => {
      expect(screen.getByText(/inner radius must be smaller than outer radius/i)).toBeInTheDocument();
    });
  });

  it('should handle L-shape parameters correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <Provider store={store}>
        <GeometrySetupConnected />
      </Provider>
    );

    // Select L-shape geometry
    const lShapeButton = screen.getByRole('button', { name: /l.shape/i });
    await user.click(lShapeButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/total width/i)).toBeInTheDocument();
    });

    // Verify all L-shape parameters are present
    expect(screen.getByLabelText(/total height/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/notch width/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/notch height/i)).toBeInTheDocument();

    // Set valid parameters
    const widthInput = screen.getByLabelText(/total width/i) as HTMLInputElement;
    const notchWidthInput = screen.getByLabelText(/notch width/i) as HTMLInputElement;
    
    await user.clear(widthInput);
    await user.type(widthInput, '4');
    
    await user.clear(notchWidthInput);
    await user.type(notchWidthInput, '2');

    // Should not show errors for valid parameters
    await waitFor(() => {
      expect(screen.queryByText(/notch width must be smaller/i)).not.toBeInTheDocument();
    });
  });

  it('should update mesh density levels correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <Provider store={store}>
        <GeometrySetupConnected />
      </Provider>
    );

    // Select any geometry
    const rectangleButton = screen.getByRole('button', { name: /rectangle/i });
    await user.click(rectangleButton);

    await waitFor(() => {
      expect(screen.getByText('Mesh Settings')).toBeInTheDocument();
    });

    // Test selecting the fine density level
    const fineDensity = screen.getByLabelText(/fine/i);
    await user.click(fineDensity);
    
    await waitFor(() => {
      expect(screen.getByText('Mesh Density: Level 4')).toBeInTheDocument();
    });

    // Test selecting the coarse density level
    const coarseDensity = screen.getByLabelText(/coarse/i);
    await user.click(coarseDensity);
    
    await waitFor(() => {
      expect(screen.getByText('Mesh Density: Level 1')).toBeInTheDocument();
    });
  });
}); 