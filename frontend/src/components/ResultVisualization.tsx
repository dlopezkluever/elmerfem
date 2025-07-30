import React, { useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useSimulationResult } from '../hooks/useSimulationResult';
import { 
  VisualizationProps, 
  ViewMode, 
  PlotlyMeshData,
  VTUData,
  EDUCATIONAL_CONTENT 
} from '../types/visualization';

/**
 * Main 3D visualization component for simulation results
 * Displays interactive 3D mesh with temperature/heat flux contours using Plotly.js
 */
export function ResultVisualization({ simulationId, className = '', onError }: VisualizationProps) {
  const { data, loading, error, refetch, statistics } = useSimulationResult(simulationId);
  const [selectedField, setSelectedField] = useState<ViewMode>(ViewMode.TEMPERATURE);

  // Handle errors by calling the optional onError callback
  React.useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // Determine available fields based on point data
  const availableFields = useMemo(() => {
    if (!data?.point_data) return [ViewMode.TEMPERATURE];
    
    const fields: ViewMode[] = [];
    if (data.point_data.Temperature) fields.push(ViewMode.TEMPERATURE);
    if (data.point_data['Heat Flux']) fields.push(ViewMode.HEAT_FLUX);
    if (data.point_data['Temperature Gradient']) fields.push(ViewMode.GRADIENT);
    
    return fields.length > 0 ? fields : [ViewMode.TEMPERATURE];
  }, [data]);

  // Convert VTU data to Plotly mesh3d format
  const plotlyData = useMemo(() => {
    if (!data) return [];
    return convertVTUToPlotlyData(data, selectedField);
  }, [data, selectedField]);

  if (loading) {
    return (
      <div className={`card-neumorphic ${className}`}>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-lg text-gray-700 font-medium">Loading 3D visualization...</p>
            <p className="text-sm text-gray-500">Processing mesh data</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`card-neumorphic ${className}`}>
        <h2 className="text-xl font-semibold text-gray-700 mb-4">3D Visualization</h2>
        <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-xl p-6">
          <div className="flex items-start">
            <div className="text-primary text-2xl mr-3">⚠️</div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-gray-700 mb-2">Visualization Data Error</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              
              <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-gray-700 mb-2">Possible Causes:</h4>
                <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                  <li>The simulation didn't generate VTU result files</li>
                  <li>VTU to JSON conversion failed during processing</li>
                  <li>Backend data conversion service is unavailable</li>
                  <li>Simulation completed but without mesh data</li>
                </ul>
              </div>
              
              <div className="flex gap-2">
                <button 
                  onClick={() => refetch()}
                  className="btn-neumorphic-primary px-4 py-2 text-sm"
                >
                  Retry Loading
                </button>
                <button 
                  onClick={() => window.open(`/api/v1/simulations/${simulationId}/result-data`, '_blank')}
                  className="btn-neumorphic px-4 py-2 text-sm"
                >
                  Test API Endpoint
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data || plotlyData.length === 0) {
    return (
      <div className={`card-neumorphic ${className}`}>
        <h2 className="text-xl font-semibold text-gray-700 mb-4">3D Visualization</h2>
        <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-xl p-6 text-center">
          <div className="text-primary text-4xl mb-4">📊</div>
          <p className="text-gray-600 mb-2">No mesh data available for visualization</p>
          <p className="text-sm text-gray-500">The simulation may not have generated 3D mesh output</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 3D Visualization and Key Findings Row */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 3D Visualization - Takes most space */}
        <div className="lg:col-span-3">
          <div className="card-neumorphic">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-700 mb-4 lg:mb-0">3D Visualization</h2>
              
              {/* Field Selection Controls */}
              <ViewControls 
                selectedField={selectedField}
                onFieldChange={setSelectedField}
                availableFields={availableFields}
              />
            </div>

            {/* 3D Plot */}
            <div className="h-[600px] bg-neumorphic-bg shadow-neumorphic-inset rounded-xl p-4">
              <Plot
                data={plotlyData}
                layout={{
                  autosize: true,
                  margin: { l: 0, r: 0, t: 0, b: 0 },
                  scene: {
                    xaxis: { title: 'X (m)', gridcolor: '#E0E0E0' },
                    yaxis: { title: 'Y (m)', gridcolor: '#E0E0E0' },
                    zaxis: { title: 'Z (m)', gridcolor: '#E0E0E0' },
                    bgcolor: '#F0F0F0',
                    camera: {
                      eye: { x: 1.5, y: 1.5, z: 1.5 }
                    }
                  },
                  paper_bgcolor: '#F0F0F0',
                  plot_bgcolor: '#F0F0F0',
                }}
                style={{ width: '100%', height: '100%' }}
                config={{
                  displayModeBar: true,
                  displaylogo: false,
                  modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                  responsive: true
                }}
              />
            </div>
          </div>
        </div>

        {/* Key Findings - Right side */}
        <div className="lg:col-span-1">
          <EducationalPanel 
            statistics={statistics}
            selectedField={selectedField}
          />
        </div>
      </div>

      {/* Additional Information - Full width below */}
      <div className="card-neumorphic h-full">
            <h3 className="text-lg font-semibold text-gray-700 mb-6">
              Additional Information Regarding Heat Transfer FEA
            </h3>
            
            <div className="space-y-6">
              {/* Mathematical Foundation */}
              <div>
                <h4 className="font-medium text-gray-700 mb-3 flex items-center">
                  <span className="text-primary mr-2">📐</span>
                  Mathematical Foundation
                </h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {/* Heat Diffusion Equation */}
                  <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">Heat Diffusion Equation</div>
                    <div className="bg-white rounded p-2 font-mono text-sm text-center mb-2">
                      &nabla;·(k&nabla;T) + Q = &rho;cp(&part;T/&part;t)
                    </div>
                    <div className="text-xs text-gray-600">
                      <div><strong>k:</strong> thermal conductivity</div>
                      <div><strong>T:</strong> temperature</div>
                      <div><strong>Q:</strong> heat generation</div>
                    </div>
                  </div>

                  {/* Fourier's Law */}
                  <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">Fourier's Law</div>
                    <div className="bg-white rounded p-2 font-mono text-sm text-center mb-2">
                      q = -k&nabla;T
                    </div>
                    <div className="text-xs text-gray-600">
                      <div><strong>q:</strong> heat flux vector (W/m²)</div>
                                              <div><strong>&nabla;T:</strong> temperature gradient</div>
                      <div>Heat flows from hot to cold</div>
                    </div>
                  </div>

                  {/* Steady State */}
                  <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">Steady State</div>
                    <div className="bg-white rounded p-2 font-mono text-sm text-center mb-2">
                      &nabla;&sup2;T = 0
                    </div>
                    <div className="text-xs text-gray-600">
                      <div>No time dependence</div>
                      <div>Constant material properties</div>
                      <div>No internal heat generation</div>
                    </div>
                  </div>

                  {/* Energy Balance */}
                  <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">Energy Balance</div>
                    <div className="bg-white rounded p-2 font-mono text-sm text-center mb-2">
                      Heat In = Heat Out + Heat Stored
                    </div>
                    <div className="text-xs text-gray-600">
                      <div>Conservation of energy</div>
                      <div>Basis for all thermal analysis</div>
                      <div>Used for validation checks</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Boundary Conditions Deep Dive */}
              <div>
                <h4 className="font-medium text-gray-700 mb-3 flex items-center">
                  <span className="text-primary mr-2">🎯</span>
                  Boundary Conditions Guide
                </h4>
                
                <div className="space-y-3">
                  {/* Dirichlet */}
                  <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-700">Dirichlet (Fixed Temperature)</span>
                      <span className="bg-white px-2 py-1 rounded text-xs font-mono">T = T₀</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div>
                        <div className="font-medium text-gray-600 mb-1">Real Examples:</div>
                        <ul className="text-gray-600 space-y-0.5">
                          <li>• Ice bath surface (0°C)</li>
                          <li>• Hot plate surface (100°C)</li>
                          <li>• Thermostat-controlled wall</li>
                        </ul>
                      </div>
                      <div>
                        <div className="font-medium text-gray-600 mb-1">When to Use:</div>
                        <ul className="text-gray-600 space-y-0.5">
                          <li>• Known surface temperatures</li>
                          <li>• Large thermal reservoirs</li>
                          <li>• Phase change boundaries</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Neumann */}
                  <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-700">Neumann (Heat Flux)</span>
                      <span className="bg-white px-2 py-1 rounded text-xs font-mono">q·n = q₀</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div>
                        <div className="font-medium text-gray-600 mb-1">Real Examples:</div>
                        <ul className="text-gray-600 space-y-0.5">
                          <li>• Insulated walls (q = 0)</li>
                          <li>• Electric heaters (q &gt; 0)</li>
                          <li>• Solar radiation input</li>
                        </ul>
                      </div>
                      <div>
                        <div className="font-medium text-gray-600 mb-1">When to Use:</div>
                        <ul className="text-gray-600 space-y-0.5">
                          <li>• Known heat input/output rates</li>
                          <li>• Symmetry boundaries</li>
                          <li>• Perfect insulation</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Robin/Convective */}
                  <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-700">Robin (Convective)</span>
                      <span className="bg-white px-2 py-1 rounded text-xs font-mono">q·n = h(T - T&infin;)</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div>
                        <div className="font-medium text-gray-600 mb-1">Real Examples:</div>
                        <ul className="text-gray-600 space-y-0.5">
                          <li>• Air cooling (h = 5-50 W/m²K)</li>
                          <li>• Water cooling (h = 500-5000)</li>
                          <li>• Natural convection</li>
                        </ul>
                      </div>
                      <div>
                        <div className="font-medium text-gray-600 mb-1">When to Use:</div>
                        <ul className="text-gray-600 space-y-0.5">
                          <li>• Convective heat transfer</li>
                          <li>• Fluid cooling/heating</li>
                          <li>• Heat exchangers</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Engineering Decision Making */}
              <div>
                <h4 className="font-medium text-gray-700 mb-3 flex items-center">
                  <span className="text-primary mr-2">🔧</span>
                  Engineering Decision Making
                </h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                      <div className="font-medium text-gray-700 mb-2">Material Selection</div>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div><strong>High k:</strong> Heat spreaders (Cu: 400 W/mK)</div>
                        <div><strong>Low k:</strong> Insulators (Air: 0.025 W/mK)</div>
                        <div><strong>Optimize:</strong> Cost vs. performance trade-off</div>
                      </div>
                    </div>

                    <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                      <div className="font-medium text-gray-700 mb-2">Geometry Optimization</div>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div><strong>Fins:</strong> Increase surface area</div>
                        <div><strong>Thickness:</strong> Balance weight vs. performance</div>
                        <div><strong>Contact:</strong> Minimize thermal resistance</div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                      <div className="font-medium text-gray-700 mb-2">Thermal Management</div>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div><strong>Hot Spots:</strong> Add local cooling</div>
                        <div><strong>Heat Sinks:</strong> Place at high flux areas</div>
                        <div><strong>TIM:</strong> Use thermal interface materials</div>
                      </div>
                    </div>

                    <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                      <div className="font-medium text-gray-700 mb-2">Design Validation</div>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div><strong>Limits:</strong> Check max temperature specs</div>
                        <div><strong>Stress:</strong> High gradients cause expansion</div>
                        <div><strong>Safety:</strong> Apply appropriate margins</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Result Validation */}
              <div>
                <h4 className="font-medium text-gray-700 mb-3 flex items-center">
                  <span className="text-primary mr-2">✅</span>
                  Result Validation & Quality Checks
                </h4>
                
                <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <div className="font-medium text-gray-600 mb-2">Energy Balance Verification</div>
                      <ul className="text-gray-600 space-y-1">
                        <li>• Heat input = Heat output (steady state)</li>
                        <li>• Check boundary flux integrals</li>
                        <li>• Verify conservation laws</li>
                        <li>• Look for unphysical results</li>
                      </ul>
                    </div>
                    <div>
                      <div className="font-medium text-gray-600 mb-2">Physical Reasonableness</div>
                      <ul className="text-gray-600 space-y-1">
                        <li>• Heat flows hot &rarr; cold</li>
                        <li>• Temperature continuity</li>
                        <li>• Gradient directions correct</li>
                        <li>• Realistic temperature levels</li>
                      </ul>
                    </div>
                    <div>
                      <div className="font-medium text-gray-600 mb-2">Mesh Independence</div>
                      <ul className="text-gray-600 space-y-1">
                        <li>• Results shouldn't change with finer mesh</li>
                        <li>• Check convergence studies</li>
                        <li>• Monitor key quantities</li>
                        <li>• Ensure adequate resolution</li>
                      </ul>
                    </div>
                    <div>
                      <div className="font-medium text-gray-600 mb-2">Analytical Comparison</div>
                      <ul className="text-gray-600 space-y-1">
                        <li>• Simple cases: hand calculations</li>
                        <li>• 1D solutions for validation</li>
                        <li>• Known benchmark problems</li>
                        <li>• Literature comparisons</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Reference */}
              <div>
                <h4 className="font-medium text-gray-700 mb-3 flex items-center">
                  <span className="text-primary mr-2">📚</span>
                  Quick Reference
                </h4>
                
                <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div>
                      <div className="font-medium text-gray-600 mb-2">Typical k Values (W/mK)</div>
                      <div className="space-y-0.5 text-gray-600">
                        <div>Copper: 400</div>
                        <div>Aluminum: 200</div>
                        <div>Steel: 50</div>
                        <div>Concrete: 1.5</div>
                        <div>Air: 0.025</div>
                      </div>
                    </div>
                    <div>
                      <div className="font-medium text-gray-600 mb-2">Convection h (W/m²K)</div>
                      <div className="space-y-0.5 text-gray-600">
                        <div>Natural air: 5-25</div>
                        <div>Forced air: 25-250</div>
                        <div>Natural water: 50-1000</div>
                        <div>Forced water: 500-10000</div>
                        <div>Boiling/condensing: 2500+</div>
                      </div>
                    </div>
                    <div>
                      <div className="font-medium text-gray-600 mb-2">Temperature Limits (°C)</div>
                      <div className="space-y-0.5 text-gray-600">
                        <div>Electronics: 85</div>
                        <div>Plastics: 60-120</div>
                        <div>Aluminum: 660 (melt)</div>
                        <div>Steel: 1500+ (melt)</div>
                        <div>Human comfort: 20-25</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
      </div>
    </div>
  );
}

/**
 * Field selection controls component
 */
interface ViewControlsProps {
  selectedField: ViewMode;
  onFieldChange: (field: ViewMode) => void;
  availableFields: ViewMode[];
}

function ViewControls({ selectedField, onFieldChange, availableFields }: ViewControlsProps) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm font-medium text-gray-700">View:</label>
      <select
        value={selectedField}
        onChange={(e) => onFieldChange(e.target.value as ViewMode)}
        className="input-neumorphic px-3 py-2 text-sm min-w-[150px]"
      >
        {availableFields.map(field => (
          <option key={field} value={field}>
            {field === ViewMode.TEMPERATURE && 'Temperature'}
            {field === ViewMode.HEAT_FLUX && 'Heat Flux'}
            {field === ViewMode.GRADIENT && 'Temperature Gradient'}
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * Educational panel with statistics and explanations
 */
interface EducationalPanelProps {
  statistics: any;
  selectedField: ViewMode;
}

function EducationalPanel({ statistics, selectedField }: EducationalPanelProps) {
  const content = EDUCATIONAL_CONTENT[selectedField];

  // Safety check - if content is not found, return a fallback
  if (!content) {
    return (
      <div className="card-neumorphic h-full">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">Key Findings</h3>
        <p className="text-gray-500">Educational content not available for this field.</p>
      </div>
    );
  }

  return (
    <div className="card-neumorphic h-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-700">Key Findings</h3>
      </div>

       {/* Statistics */}
       {statistics && (
         <div className="space-y-3 mb-4">
           <div className="bg-neumorphic-bg shadow-neumorphic-inset rounded-lg p-3">
             <div className="flex items-center justify-between mb-3">
               <h4 className="font-medium text-gray-700 text-sm">Statistical Summary</h4>
               <span className="text-xs text-gray-500">{statistics.sampleSize} data points</span>
             </div>
             
             {/* Core Statistics */}
             <div className="grid grid-cols-2 gap-2 mb-3">
               <div className="text-xs">
                 <div className="flex justify-between">
                   <span className="text-gray-600">Min:</span>
                   <span className="font-mono font-medium">{statistics.min.toFixed(2)} {statistics.unit}</span>
                 </div>
                 <div className="flex justify-between">
                   <span className="text-gray-600">Max:</span>
                   <span className="font-mono font-medium">{statistics.max.toFixed(2)} {statistics.unit}</span>
                 </div>
               </div>
               <div className="text-xs">
                 <div className="flex justify-between">
                   <span className="text-gray-600">Mean:</span>
                   <span className="font-mono font-medium">{statistics.mean.toFixed(2)} {statistics.unit}</span>
                 </div>
                 <div className="flex justify-between">
                   <span className="text-gray-600">Median:</span>
                   <span className="font-mono font-medium">{statistics.median.toFixed(2)} {statistics.unit}</span>
                 </div>
               </div>
             </div>

             {/* Variability Metrics */}
             <div className="border-t border-gray-200 pt-2 mb-3">
               <div className="text-xs space-y-1">
                 <div className="flex justify-between">
                   <span className="text-gray-600">Std Dev:</span>
                   <span className="font-mono">{statistics.std.toFixed(2)} {statistics.unit}</span>
                 </div>
                 <div className="flex justify-between">
                   <span className="text-gray-600">Range:</span>
                   <span className="font-mono">{statistics.range.toFixed(2)} {statistics.unit}</span>
                 </div>
                 <div className="flex justify-between">
                   <span className="text-gray-600">CV:</span>
                   <span className="font-mono">{statistics.coefficientOfVariation.toFixed(1)}%</span>
                 </div>
               </div>
             </div>

             {/* Quartiles */}
             <div className="border-t border-gray-200 pt-2">
               <div className="text-xs">
                 <div className="flex justify-between items-center mb-1">
                   <span className="text-gray-600 font-medium">Quartiles:</span>
                 </div>
                 <div className="grid grid-cols-3 gap-1 text-xs">
                   <div className="text-center">
                     <div className="text-gray-500">Q1</div>
                     <div className="font-mono text-xs">{statistics.p25.toFixed(1)}</div>
                   </div>
                   <div className="text-center">
                     <div className="text-gray-500">Q2</div>
                     <div className="font-mono text-xs">{statistics.median.toFixed(1)}</div>
                   </div>
                   <div className="text-center">
                     <div className="text-gray-500">Q3</div>
                     <div className="font-mono text-xs">{statistics.p75.toFixed(1)}</div>
                   </div>
                 </div>
               </div>
             </div>

             {/* Field-Specific Insights */}
             <div className="border-t border-gray-200 pt-2 mt-2">
               <div className="text-xs">
                 <div className="text-gray-600 font-medium mb-1">Analysis:</div>
                 {getFieldSpecificInsights(statistics, selectedField).map((insight, index) => (
                   <div key={index} className="flex items-start mb-1">
                     <span className="text-primary mr-1 mt-0.5">•</span>
                     <span className="text-gray-600 leading-tight">{insight}</span>
                   </div>
                 ))}
               </div>
             </div>
           </div>
         </div>
       )}

      {/* Educational Content */}
      <div className="space-y-3">
        <div>
          <h4 className="font-medium text-gray-700 text-sm mb-2">{content.title}</h4>
          <p className="text-xs text-gray-600 leading-relaxed">{content.description}</p>
        </div>

        <div>
          <h4 className="font-medium text-gray-700 text-sm mb-2">Physical Meaning</h4>
          <p className="text-xs text-gray-600 leading-relaxed">{content.physicalMeaning}</p>
        </div>

                 <div>
           <h4 className="font-medium text-gray-700 text-sm mb-2">Key Insights</h4>
           <ul className="text-xs text-gray-600 space-y-1">
             {content.keyInsights?.map((insight, index) => (
               <li key={index} className="flex items-start">
                 <span className="text-primary mr-1">•</span>
                 <span className="leading-relaxed">{insight}</span>
               </li>
             )) || []}
           </ul>
         </div>
      </div>
    </div>
  );
}

/**
 * Convert VTU data structure to Plotly mesh3d format
 * Now handles hexahedron cells properly for cube visualization
 */
function convertVTUToPlotlyData(data: VTUData, fieldName: ViewMode): PlotlyMeshData[] {
  try {
    console.log('Converting VTU data:', { 
      points: data.points.length, 
      cells: Object.keys(data.cells),
      fieldName,
      pointDataFields: Object.keys(data.point_data || {})
    });

    // Extract coordinates
    const x = data.points.map(point => point[0]);
    const y = data.points.map(point => point[1]);
    const z = data.points.map(point => point[2]);

    // Extract triangular faces from different cell types
    let i: number[] = [];
    let j: number[] = [];
    let k: number[] = [];

    // Handle triangles directly
    if (data.cells.triangle) {
      data.cells.triangle.forEach(triangle => {
        i.push(triangle[0]);
        j.push(triangle[1]);
        k.push(triangle[2]);
      });
    }

    // Handle tetrahedra - extract surface triangles
    if (data.cells.tetra) {
      data.cells.tetra.forEach(tetra => {
        // Add the 4 triangular faces of each tetrahedron
        const faces = [
          [tetra[0], tetra[1], tetra[2]],
          [tetra[0], tetra[1], tetra[3]],
          [tetra[0], tetra[2], tetra[3]],
          [tetra[1], tetra[2], tetra[3]]
        ];
        
        faces.forEach(face => {
          i.push(face[0]);
          j.push(face[1]);
          k.push(face[2]);
        });
      });
    }

    // Handle hexahedra (cubes) - extract surface triangles
    if (data.cells.hexahedron) {
      data.cells.hexahedron.forEach(hex => {
        // Define the 6 faces of a hexahedron (cube)
        // Each face is split into 2 triangles
        const faces = [
          // Bottom face (z=0): vertices 0,1,2,3
          [hex[0], hex[1], hex[2]], [hex[0], hex[2], hex[3]],
          // Top face (z=1): vertices 4,5,6,7
          [hex[4], hex[7], hex[6]], [hex[4], hex[6], hex[5]],
          // Front face (y=0): vertices 0,1,5,4
          [hex[0], hex[4], hex[5]], [hex[0], hex[5], hex[1]],
          // Back face (y=1): vertices 2,3,7,6
          [hex[2], hex[6], hex[7]], [hex[2], hex[7], hex[3]],
          // Left face (x=0): vertices 0,3,7,4
          [hex[0], hex[3], hex[7]], [hex[0], hex[7], hex[4]],
          // Right face (x=1): vertices 1,2,6,5
          [hex[1], hex[5], hex[6]], [hex[1], hex[6], hex[2]]
        ];
        
        faces.forEach(face => {
          i.push(face[0]);
          j.push(face[1]);
          k.push(face[2]);
        });
      });
    }

    console.log(`Generated ${i.length} triangular faces from cells`);

    // Get intensity data for coloring
    let intensityData: number[] = [];
    
    if (fieldName === ViewMode.HEAT_FLUX || fieldName === ViewMode.GRADIENT) {
      // For vector fields, calculate magnitude
      const vectorField = data.point_data[fieldName.toString()] || data.point_data['Heat Flux'] || data.point_data['Temperature Gradient'];
      if (vectorField && Array.isArray(vectorField[0])) {
        intensityData = vectorField.map((vector: number[]) => {
          const [vx, vy, vz] = vector;
          return Math.sqrt(vx*vx + vy*vy + vz*vz);
        });
      }
    } else {
      // For scalar fields like temperature
      intensityData = data.point_data[fieldName.toString()] || data.point_data.Temperature || [];
    }
    
    if (intensityData.length === 0) {
      console.warn(`No data found for field ${fieldName}, using zero values`);
      intensityData = x.map(() => 0);
    }

    // Ensure we have the same number of intensity values as points
    const intensity = x.map((_, index) => intensityData[index] || 0);

    console.log('Intensity data:', { min: Math.min(...intensity), max: Math.max(...intensity), length: intensity.length });

    const plotData: PlotlyMeshData = {
      type: 'mesh3d',
      x,
      y,
      z,
      i,
      j,
      k,
      intensity,
      colorscale: fieldName === ViewMode.TEMPERATURE ? 'RdYlBu_r' : 'Viridis',
      showscale: true,
      colorbar: {
        title: getFieldUnit(fieldName),
        titleside: 'right',
        thickness: 20,
        len: 0.8,
      },
      lighting: {
        ambient: 0.4,
        diffuse: 0.8,
        specular: 0.2,
        roughness: 0.1,
      },
      flatshading: false,
    };

    return [plotData];
  } catch (error) {
    console.error('Error converting VTU data to Plotly format:', error);
    return [];
  }
}

/**
 * Get field-specific insights based on statistical analysis
 */
function getFieldSpecificInsights(statistics: any, fieldName: ViewMode): string[] {
  const insights: string[] = [];
  const cv = statistics.coefficientOfVariation;
  const range = statistics.range;
  const mean = statistics.mean;

  switch (fieldName) {
    case ViewMode.TEMPERATURE:
      // Temperature-specific insights
      if (cv < 10) {
        insights.push("Temperature distribution is very uniform across the geometry");
      } else if (cv < 25) {
        insights.push("Moderate temperature variation indicates good heat conduction");
      } else {
        insights.push("High temperature variation suggests thermal gradients or hot spots");
      }

      if (range > 50) {
        insights.push(`Large temperature range (${range.toFixed(1)}°C) indicates significant thermal driving force`);
      } else if (range < 10) {
        insights.push("Small temperature range suggests near-equilibrium conditions");
      }

      // Temperature level analysis
      if (mean > 80) {
        insights.push("High average temperature - consider thermal management strategies");
      } else if (mean < 20) {
        insights.push("Low temperature operation - good for thermal stability");
      }
      break;

    case ViewMode.HEAT_FLUX:
      // Heat flux specific insights
      if (cv < 15) {
        insights.push("Uniform heat flux distribution indicates balanced thermal design");
      } else if (cv > 50) {
        insights.push("High heat flux variation - check for thermal bottlenecks");
      }

      if (mean > 1000) {
        insights.push(`High heat flux (${mean.toFixed(0)} W/m²) - verify thermal limits`);
      } else if (mean < 100) {
        insights.push("Low heat flux indicates gentle thermal conditions");
      }

      // Hot spot analysis
      if (statistics.hotSpots && statistics.hotSpots.length > 0) {
        const maxFlux = statistics.max;
        if (maxFlux > mean * 2) {
          insights.push(`Peak heat flux is ${(maxFlux/mean).toFixed(1)}x higher than average - potential concern`);
        }
      }
      break;

    case ViewMode.GRADIENT:
      // Temperature gradient insights
      if (cv < 20) {
        insights.push("Consistent temperature gradients throughout the domain");
      } else {
        insights.push("Variable gradients - indicates complex thermal behavior");
      }

      if (mean > 50) {
        insights.push(`High average gradient (${mean.toFixed(1)} °C/m) drives strong heat transfer`);
      } else if (mean < 10) {
        insights.push("Low gradients suggest minimal thermal driving force");
      }

      // Stress implications
      if (statistics.max > 100) {
        insights.push("High temperature gradients may cause thermal stress");
      }
      break;
  }

  // General statistical insights
  if (Math.abs(statistics.mean - statistics.median) / statistics.mean > 0.1) {
    insights.push("Skewed distribution - values concentrated at one end");
  }

  // Quartile spread analysis
  const iqr = statistics.p75 - statistics.p25;
  if (iqr / statistics.mean < 0.1) {
    insights.push("Values tightly clustered around the median");
  }

  return insights.slice(0, 3); // Limit to 3 most relevant insights
}

/**
 * Get the unit string for a field
 */
function getFieldUnit(fieldName: ViewMode): string {
  switch (fieldName) {
    case ViewMode.TEMPERATURE:
      return 'Temperature (°C)';
    case ViewMode.HEAT_FLUX:
      return 'Heat Flux Magnitude (W/m²)';
    case ViewMode.GRADIENT:
      return 'Temperature Gradient Magnitude (°C/m)';
    default:
      return 'Value';
  }
} 