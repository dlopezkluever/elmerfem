import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import {
  EducationalGeometryType,
  MESH_DENSITY_LEVELS,
} from '../../types/geometry';
import {
  validateGeometry,
  estimateMeshElements
} from '../../utils/geometryValidation';
import { GeometryPreview } from './GeometryPreview';
import {
  setGeometryType,
  setRectangleParameters,
  setCircleParameters,
  setAnnulusParameters,
  setLShapeParameters,
  setMeshDensity,
  setBoundaryLayer,
  setBoundaryLayerThickness,
  setValidation,
  setEstimatedElements,
  selectCurrentGeometry
} from '../../store/slices/geometrySlice';

export const GeometrySetupConnected: React.FC = () => {
  const dispatch = useDispatch();
  const geometryState = useSelector((state: RootState) => state.geometry);
  const currentGeometry = useSelector(selectCurrentGeometry);

  const {
    selectedType,
    parameters,
    meshSettings,
    validation,
    estimatedElements
  } = geometryState;

  // Validate and update when parameters change
  // Use specific state values as dependencies instead of the derived currentGeometry
  useEffect(() => {
    if (selectedType) {
      let geometry;
      switch (selectedType) {
        case EducationalGeometryType.RECTANGLE:
          geometry = { type: EducationalGeometryType.RECTANGLE, params: parameters.rectangle };
          break;
        case EducationalGeometryType.CIRCLE:
          geometry = { type: EducationalGeometryType.CIRCLE, params: parameters.circle };
          break;
        case EducationalGeometryType.ANNULUS:
          geometry = { type: EducationalGeometryType.ANNULUS, params: parameters.annulus };
          break;
        case EducationalGeometryType.L_SHAPE:
          geometry = { type: EducationalGeometryType.L_SHAPE, params: parameters.lShape };
          break;
      }

      if (geometry) {
        const validationResult = validateGeometry(geometry);
        dispatch(setValidation(validationResult));

        if (validationResult.isValid) {
          const elements = estimateMeshElements(geometry, meshSettings.density);
          dispatch(setEstimatedElements(elements));
        }
      }
    } else {
      dispatch(setValidation({ isValid: false, errors: {} }));
      dispatch(setEstimatedElements(0));
    }
  }, [
    selectedType,
    parameters.rectangle,
    parameters.circle,
    parameters.annulus,
    parameters.lShape,
    meshSettings.density,
    dispatch
  ]);

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
                value={parameters.rectangle.width}
                onChange={(e) => dispatch(setRectangleParameters({
                  width: parseFloat(e.target.value) || 0
                }))}
                step="0.1"
                min="0.001"
                max="10"
                className={`input-neumorphic ${validation.errors.width ? 'ring-2 ring-red-400' : ''}`}
              />
              {validation.errors.width && (
                <p className="mt-1 text-sm text-red-600">{validation.errors.width}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Height (m)
              </label>
              <input
                type="number"
                value={parameters.rectangle.height}
                onChange={(e) => dispatch(setRectangleParameters({
                  height: parseFloat(e.target.value) || 0
                }))}
                step="0.1"
                min="0.001"
                max="10"
                className={`input-neumorphic ${validation.errors.height ? 'ring-2 ring-red-400' : ''}`}
              />
              {validation.errors.height && (
                <p className="mt-1 text-sm text-red-600">{validation.errors.height}</p>
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
                value={parameters.circle.radius}
                onChange={(e) => dispatch(setCircleParameters({
                  radius: parseFloat(e.target.value) || 0
                }))}
                step="0.1"
                min="0.001"
                max="5"
                className={`input-neumorphic ${validation.errors.radius ? 'ring-2 ring-red-400' : ''}`}
              />
              {validation.errors.radius && (
                <p className="mt-1 text-sm text-red-600">{validation.errors.radius}</p>
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
                value={parameters.annulus.innerRadius}
                onChange={(e) => dispatch(setAnnulusParameters({
                  innerRadius: parseFloat(e.target.value) || 0
                }))}
                step="0.1"
                min="0.001"
                max="5"
                className={`input-neumorphic ${validation.errors.innerRadius ? 'ring-2 ring-red-400' : ''}`}
              />
              {validation.errors.innerRadius && (
                <p className="mt-1 text-sm text-red-600">{validation.errors.innerRadius}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Outer Radius (m)
              </label>
              <input
                type="number"
                value={parameters.annulus.outerRadius}
                onChange={(e) => dispatch(setAnnulusParameters({
                  outerRadius: parseFloat(e.target.value) || 0
                }))}
                step="0.1"
                min="0.001"
                max="5"
                className={`input-neumorphic ${validation.errors.outerRadius ? 'ring-2 ring-red-400' : ''}`}
              />
              {validation.errors.outerRadius && (
                <p className="mt-1 text-sm text-red-600">{validation.errors.outerRadius}</p>
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
                  value={parameters.lShape.width}
                  onChange={(e) => dispatch(setLShapeParameters({
                    width: parseFloat(e.target.value) || 0
                  }))}
                  step="0.1"
                  min="0.001"
                  max="10"
                  className={`input-neumorphic ${validation.errors.width ? 'ring-2 ring-red-400' : ''}`}
                />
                {validation.errors.width && (
                  <p className="mt-1 text-sm text-red-600">{validation.errors.width}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Height (m)
                </label>
                <input
                  type="number"
                  value={parameters.lShape.height}
                  onChange={(e) => dispatch(setLShapeParameters({
                    height: parseFloat(e.target.value) || 0
                  }))}
                  step="0.1"
                  min="0.001"
                  max="10"
                  className={`input-neumorphic ${validation.errors.height ? 'ring-2 ring-red-400' : ''}`}
                />
                {validation.errors.height && (
                  <p className="mt-1 text-sm text-red-600">{validation.errors.height}</p>
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
                  value={parameters.lShape.notchWidth}
                  onChange={(e) => dispatch(setLShapeParameters({
                    notchWidth: parseFloat(e.target.value) || 0
                  }))}
                  step="0.1"
                  min="0.001"
                  max={parameters.lShape.width - 0.001}
                  className={`input-neumorphic ${validation.errors.notchWidth ? 'ring-2 ring-red-400' : ''}`}
                />
                {validation.errors.notchWidth && (
                  <p className="mt-1 text-sm text-red-600">{validation.errors.notchWidth}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notch Height (m)
                </label>
                <input
                  type="number"
                  value={parameters.lShape.notchHeight}
                  onChange={(e) => dispatch(setLShapeParameters({
                    notchHeight: parseFloat(e.target.value) || 0
                  }))}
                  step="0.1"
                  min="0.001"
                  max={parameters.lShape.height - 0.001}
                  className={`input-neumorphic ${validation.errors.notchHeight ? 'ring-2 ring-red-400' : ''}`}
                />
                {validation.errors.notchHeight && (
                  <p className="mt-1 text-sm text-red-600">{validation.errors.notchHeight}</p>
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
                onClick={() => dispatch(setGeometryType(type))}
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
                      checked={meshSettings.density === level.level}
                      onChange={(e) => dispatch(setMeshDensity(parseInt(e.target.value)))}
                      className="sr-only"
                    />
                    <div className={`w-5 h-5 rounded-full mr-3 transition-all duration-200
                      ${meshSettings.density === level.level 
                        ? 'bg-primary shadow-neumorphic-inset' 
                        : 'bg-neumorphic-bg shadow-neumorphic group-hover:shadow-neumorphic-hover'}`}>
                      {meshSettings.density === level.level && (
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
                  checked={meshSettings.boundaryLayer}
                  onChange={(e) => dispatch(setBoundaryLayer(e.target.checked))}
                  className="sr-only"
                />
                <div className={`w-6 h-6 rounded mr-3 transition-all duration-200
                  ${meshSettings.boundaryLayer 
                    ? 'bg-primary shadow-neumorphic-inset' 
                    : 'bg-neumorphic-bg shadow-neumorphic group-hover:shadow-neumorphic-hover'}`}>
                  {meshSettings.boundaryLayer && (
                    <svg className="w-4 h-4 m-1 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <span className="text-sm font-medium text-gray-700">
                  Enable Boundary Layer (for fluid/heat transfer)
                </span>
              </label>

              {meshSettings.boundaryLayer && (
                <div className="mt-4 ml-9">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Boundary Layer Thickness (m)
                  </label>
                  <input
                    type="number"
                    value={meshSettings.boundaryLayerThickness}
                    onChange={(e) => dispatch(setBoundaryLayerThickness(
                      parseFloat(e.target.value) || 0.01
                    ))}
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
          geometry={currentGeometry}
          meshDensity={meshSettings.density}
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