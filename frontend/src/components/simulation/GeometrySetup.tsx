import React, { useState, useEffect } from 'react';
import {
  EducationalGeometryType,
  GeometryParameters,
  MESH_DENSITY_LEVELS,
  EducationalMeshParams
} from '../../types/geometry';
import { validateGeometry, estimateMeshElements } from '../../utils/geometryValidation';
import { GeometryPreview } from './GeometryPreview';

interface GeometrySetupProps {
  onGeometryChange?: (params: EducationalMeshParams | null) => void;
}

export const GeometrySetup: React.FC<GeometrySetupProps> = ({ onGeometryChange }) => {
  const [selectedType, setSelectedType] = useState<EducationalGeometryType | ''>('');
  const [meshDensity, setMeshDensity] = useState<number>(3); // Default to medium
  const [boundaryLayer, setBoundaryLayer] = useState<boolean>(false);
  const [boundaryLayerThickness, setBoundaryLayerThickness] = useState<number>(0.01);

  // Geometry-specific parameters
  const [rectangleParams, setRectangleParams] = useState({ width: 1, height: 1 });
  const [circleParams, setCircleParams] = useState({ radius: 0.5 });
  const [annulusParams, setAnnulusParams] = useState({ innerRadius: 0.3, outerRadius: 0.5 });
  const [lShapeParams, setLShapeParams] = useState({
    width: 2,
    height: 2,
    notchWidth: 1,
    notchHeight: 1
  });

  const [errors, setErrors] = useState<{ [field: string]: string }>({});
  const [estimatedElements, setEstimatedElements] = useState<number>(0);

  // Build current geometry parameters
  const getCurrentGeometry = (): GeometryParameters | null => {
    switch (selectedType) {
      case EducationalGeometryType.RECTANGLE:
        return { type: EducationalGeometryType.RECTANGLE, params: rectangleParams };
      case EducationalGeometryType.CIRCLE:
        return { type: EducationalGeometryType.CIRCLE, params: circleParams };
      case EducationalGeometryType.ANNULUS:
        return { type: EducationalGeometryType.ANNULUS, params: annulusParams };
      case EducationalGeometryType.L_SHAPE:
        return { type: EducationalGeometryType.L_SHAPE, params: lShapeParams };
      default:
        return null;
    }
  };

  // Validate and update on parameter changes
  useEffect(() => {
    const geometry = getCurrentGeometry();
    if (geometry) {
      const validation = validateGeometry(geometry);
      setErrors(validation.errors);

      if (validation.isValid) {
        const elements = estimateMeshElements(geometry, meshDensity);
        setEstimatedElements(elements);

        const meshParams: EducationalMeshParams = {
          geometry,
          meshDensity,
          boundaryLayer,
          ...(boundaryLayer && { boundaryLayerThickness })
        };

        onGeometryChange?.(meshParams);
      } else {
        onGeometryChange?.(null);
      }
    } else {
      setErrors({});
      setEstimatedElements(0);
      onGeometryChange?.(null);
    }
  }, [selectedType, rectangleParams, circleParams, annulusParams, lShapeParams,
      meshDensity, boundaryLayer, boundaryLayerThickness, onGeometryChange]);

  const renderGeometryForm = () => {
    switch (selectedType) {
      case EducationalGeometryType.RECTANGLE:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Width (m)
              </label>
              <input
                type="number"
                value={rectangleParams.width}
                onChange={(e) => setRectangleParams({
                  ...rectangleParams,
                  width: parseFloat(e.target.value) || 0
                })}
                step="0.1"
                min="0.001"
                max="10"
                className={`input-neumorphic ${errors.width ? 'ring-2 ring-red-400' : ''}`}
              />
              {errors.width && (
                <p className="mt-1 text-sm text-red-600">{errors.width}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Height (m)
              </label>
              <input
                type="number"
                value={rectangleParams.height}
                onChange={(e) => setRectangleParams({
                  ...rectangleParams,
                  height: parseFloat(e.target.value) || 0
                })}
                step="0.1"
                min="0.001"
                max="10"
                className={`input-neumorphic ${errors.height ? 'ring-2 ring-red-400' : ''}`}
              />
              {errors.height && (
                <p className="mt-1 text-sm text-red-600">{errors.height}</p>
              )}
            </div>
          </div>
        );

      case EducationalGeometryType.CIRCLE:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Radius (m)
              </label>
              <input
                type="number"
                value={circleParams.radius}
                onChange={(e) => setCircleParams({
                  radius: parseFloat(e.target.value) || 0
                })}
                step="0.1"
                min="0.001"
                max="5"
                className={`input-neumorphic ${errors.radius ? 'ring-2 ring-red-400' : ''}`}
              />
              {errors.radius && (
                <p className="mt-1 text-sm text-red-600">{errors.radius}</p>
              )}
            </div>
          </div>
        );

      case EducationalGeometryType.ANNULUS:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Inner Radius (m)
              </label>
              <input
                type="number"
                value={annulusParams.innerRadius}
                onChange={(e) => setAnnulusParams({
                  ...annulusParams,
                  innerRadius: parseFloat(e.target.value) || 0
                })}
                step="0.1"
                min="0.001"
                max="5"
                className={`input-neumorphic ${errors.innerRadius ? 'ring-2 ring-red-400' : ''}`}
              />
              {errors.innerRadius && (
                <p className="mt-1 text-sm text-red-600">{errors.innerRadius}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Outer Radius (m)
              </label>
              <input
                type="number"
                value={annulusParams.outerRadius}
                onChange={(e) => setAnnulusParams({
                  ...annulusParams,
                  outerRadius: parseFloat(e.target.value) || 0
                })}
                step="0.1"
                min="0.001"
                max="5"
                className={`input-neumorphic ${errors.outerRadius ? 'ring-2 ring-red-400' : ''}`}
              />
              {errors.outerRadius && (
                <p className="mt-1 text-sm text-red-600">{errors.outerRadius}</p>
              )}
            </div>
          </div>
        );

      case EducationalGeometryType.L_SHAPE:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Width (m)
                </label>
                <input
                  type="number"
                  value={lShapeParams.width}
                  onChange={(e) => setLShapeParams({
                    ...lShapeParams,
                    width: parseFloat(e.target.value) || 0
                  })}
                  step="0.1"
                  min="0.001"
                  max="10"
                  className={`input-neumorphic ${errors.width ? 'ring-2 ring-red-400' : ''}`}
                />
                {errors.width && (
                  <p className="mt-1 text-sm text-red-600">{errors.width}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Height (m)
                </label>
                <input
                  type="number"
                  value={lShapeParams.height}
                  onChange={(e) => setLShapeParams({
                    ...lShapeParams,
                    height: parseFloat(e.target.value) || 0
                  })}
                  step="0.1"
                  min="0.001"
                  max="10"
                  className={`input-neumorphic ${errors.height ? 'ring-2 ring-red-400' : ''}`}
                />
                {errors.height && (
                  <p className="mt-1 text-sm text-red-600">{errors.height}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notch Width (m)
                </label>
                <input
                  type="number"
                  value={lShapeParams.notchWidth}
                  onChange={(e) => setLShapeParams({
                    ...lShapeParams,
                    notchWidth: parseFloat(e.target.value) || 0
                  })}
                  step="0.1"
                  min="0.001"
                  max={lShapeParams.width - 0.001}
                  className={`input-neumorphic ${errors.notchWidth ? 'ring-2 ring-red-400' : ''}`}
                />
                {errors.notchWidth && (
                  <p className="mt-1 text-sm text-red-600">{errors.notchWidth}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notch Height (m)
                </label>
                <input
                  type="number"
                  value={lShapeParams.notchHeight}
                  onChange={(e) => setLShapeParams({
                    ...lShapeParams,
                    notchHeight: parseFloat(e.target.value) || 0
                  })}
                  step="0.1"
                  min="0.001"
                  max={lShapeParams.height - 0.001}
                  className={`input-neumorphic ${errors.notchHeight ? 'ring-2 ring-red-400' : ''}`}
                />
                {errors.notchHeight && (
                  <p className="mt-1 text-sm text-red-600">{errors.notchHeight}</p>
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left Column: Form Inputs */}
      <div className="space-y-6">
        {/* Geometry Type Selection */}
        <div className="card-neumorphic">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Select Geometry Type</h3>
          <div className="grid grid-cols-2 gap-4">
            {Object.values(EducationalGeometryType).map((type) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`btn-neumorphic py-4 px-4 text-center transition-all duration-200
                  ${selectedType === type
                    ? 'shadow-neumorphic-inset text-primary font-semibold'
                    : 'hover:shadow-neumorphic-hover font-medium'}`}
              >
                <div className="flex flex-col items-center">
                  <span className="text-2xl mb-2 text-gray-700">
                    {type === EducationalGeometryType.RECTANGLE && '▭'}
                    {type === EducationalGeometryType.CIRCLE && '●'}
                    {type === EducationalGeometryType.ANNULUS && '○'}
                    {type === EducationalGeometryType.L_SHAPE && '└'}
                  </span>
                  <span className="text-sm capitalize">
                    {type.replace('_', ' ')}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Geometry Parameters */}
        {selectedType && (
          <div className="card-neumorphic">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Geometry Parameters</h3>
            {renderGeometryForm()}
          </div>
        )}

        {/* Mesh Settings */}
        {selectedType && (
          <div className="card-neumorphic">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Mesh Settings</h3>

            {/* Mesh Density */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Mesh Density
              </label>
              <div className="space-y-3">
                {MESH_DENSITY_LEVELS.map((level) => (
                  <label key={level.level} className="flex items-center cursor-pointer group">
                    <input
                      type="radio"
                      value={level.level}
                      checked={meshDensity === level.level}
                      onChange={(e) => setMeshDensity(parseInt(e.target.value))}
                      className="sr-only"
                    />
                    <div className={`w-5 h-5 rounded-full mr-3 transition-all duration-200
                      ${meshDensity === level.level
                        ? 'bg-primary shadow-neumorphic-inset'
                        : 'bg-neumorphic-bg shadow-neumorphic group-hover:shadow-neumorphic-hover'}`}>
                      {meshDensity === level.level && (
                        <div className="w-full h-full rounded-full flex items-center justify-center">
                          <div className="w-2 h-2 rounded-full bg-white"></div>
                        </div>
                      )}
                    </div>
                    <span className="flex-1">
                      <span className="font-medium text-gray-800">{level.label}</span>
                      <span className="text-sm text-gray-600 ml-2">
                        ({level.description})
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Boundary Layer */}
            <div className="mt-6">
              <label className="flex items-center cursor-pointer group">
                <input
                  type="checkbox"
                  checked={boundaryLayer}
                  onChange={(e) => setBoundaryLayer(e.target.checked)}
                  className="sr-only"
                />
                <div className={`w-6 h-6 rounded mr-3 transition-all duration-200
                  ${boundaryLayer
                    ? 'bg-primary shadow-neumorphic-inset'
                    : 'bg-neumorphic-bg shadow-neumorphic group-hover:shadow-neumorphic-hover'}`}>
                  {boundaryLayer && (
                    <svg className="w-4 h-4 m-1 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <span className="text-sm font-medium text-gray-700">
                  Enable Boundary Layer (for fluid/heat transfer)
                </span>
              </label>

              {boundaryLayer && (
                <div className="mt-4 ml-9">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Boundary Layer Thickness (m)
                  </label>
                  <input
                    type="number"
                    value={boundaryLayerThickness}
                    onChange={(e) => setBoundaryLayerThickness(parseFloat(e.target.value) || 0.01)}
                    step="0.001"
                    min="0.001"
                    max="0.1"
                    className="input-neumorphic"
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Column: Preview */}
      <div className="lg:sticky lg:top-6 lg:h-fit space-y-6">
        <GeometryPreview
          geometry={getCurrentGeometry()}
          meshDensity={meshDensity}
          estimatedElements={estimatedElements}
        />

        {/* Educational Tips */}
        {selectedType && (
          <div className="card-neumorphic">
            <h4 className="text-sm font-semibold text-gray-800 mb-3">
              Educational Tips
            </h4>
            <ul className="text-sm text-gray-600 space-y-2">
              {selectedType === EducationalGeometryType.RECTANGLE && (
                <>
                  <li>• Good for basic heat transfer and structural analysis</li>
                  <li>• Aspect ratio affects mesh quality - avoid very thin shapes</li>
                </>
              )}
              {selectedType === EducationalGeometryType.CIRCLE && (
                <>
                  <li>• Ideal for radial heat transfer problems</li>
                  <li>• Symmetry can simplify boundary conditions</li>
                </>
              )}
              {selectedType === EducationalGeometryType.ANNULUS && (
                <>
                  <li>• Perfect for pipe flow and cylindrical heat transfer</li>
                  <li>• Inner/outer radius ratio affects mesh distribution</li>
                </>
              )}
              {selectedType === EducationalGeometryType.L_SHAPE && (
                <>
                  <li>• Common in structural mechanics problems</li>
                  <li>• Stress concentrations occur at the inner corner</li>
                </>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}; 