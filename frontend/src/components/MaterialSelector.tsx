import React, { useState } from 'react';
import { Material } from '../api';

interface MaterialSelectorProps {
  materials: Material[];
  value?: string;
  onChange: (value: string) => void;
  error?: any;
  name: string;
}

export const MaterialSelector: React.FC<MaterialSelectorProps> = ({
  materials,
  value,
  onChange,
  error,
  name
}) => {
  const [showModal, setShowModal] = useState(false);
  const selectedMaterial = materials.find(m => m.id === value);

  const formatScientific = (value: number): string => {
    if (value >= 1e6 || value <= 1e-3) {
      return value.toExponential(2);
    }
    return value.toLocaleString();
  };

  return (
    <>
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Select Material
        </label>
        <div className="flex gap-2">
          <select
            name={name}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="input-neumorphic flex-1"
          >
            <option value="">Select a material...</option>
            {materials.map(material => (
              <option key={material.id} value={material.id}>
                {material.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => setShowModal(true)}
            disabled={!selectedMaterial}
            className="btn-neumorphic px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            View Properties
          </button>
        </div>
        {error && (
          <p className="mt-1 text-sm text-red-600">{error.message}</p>
        )}
      </div>

      {/* Material Properties Modal */}
      {showModal && selectedMaterial && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-100 rounded-lg p-8 max-w-2xl w-full mx-4 shadow-2xl">
            <h2 className="text-2xl font-bold mb-4">{selectedMaterial.name} Properties</h2>
            
            {selectedMaterial.description && (
              <p className="text-gray-600 mb-6">{selectedMaterial.description}</p>
            )}

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Property
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unit
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Young's Modulus (E)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatScientific(selectedMaterial.E)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {selectedMaterial.units?.E || 'Pa'}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Poisson's Ratio (ν)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {selectedMaterial.nu}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {selectedMaterial.units?.nu || 'dimensionless'}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Thermal Conductivity (k)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatScientific(selectedMaterial.k)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {selectedMaterial.units?.k || 'W/(m·K)'}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Density (ρ)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatScientific(selectedMaterial.rho)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {selectedMaterial.units?.rho || 'kg/m³'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="btn-neumorphic px-6 py-2"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}; 