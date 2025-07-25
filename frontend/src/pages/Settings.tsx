import { useState, useEffect } from 'react';

interface Settings {
  defaultMeshDensity: number;
  autoDownloadResults: boolean;
  showAdvancedOptions: boolean;
  theme: 'light' | 'dark';
}

const defaultSettings: Settings = {
  defaultMeshDensity: 1.0,
  autoDownloadResults: false,
  showAdvancedOptions: false,
  theme: 'light',
};

function Settings() {
  const [settings, setSettings] = useState<Settings>(defaultSettings);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load settings from localStorage
    const stored = localStorage.getItem('elmerfem_settings');
    if (stored) {
      try {
        setSettings(JSON.parse(stored));
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem('elmerfem_settings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    localStorage.removeItem('elmerfem_settings');
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-4xl font-bold mb-8">Settings</h1>

      <div className="space-y-6">
        {/* Simulation Defaults */}
        <section className="card-neumorphic">
          <h2 className="text-xl font-bold mb-4">Simulation Defaults</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block mb-2">
                <span className="text-gray-700 font-medium">Default Mesh Density</span>
                <p className="text-sm text-gray-500">Applied to new simulations</p>
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0.1"
                  max="2.0"
                  step="0.1"
                  value={settings.defaultMeshDensity}
                  onChange={(e) => updateSetting('defaultMeshDensity', parseFloat(e.target.value))}
                  className="flex-1"
                />
                <span className="w-12 text-center font-mono">{settings.defaultMeshDensity.toFixed(1)}</span>
              </div>
            </div>

            <div>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings.autoDownloadResults}
                  onChange={(e) => updateSetting('autoDownloadResults', e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300"
                />
                <div>
                  <span className="text-gray-700 font-medium">Auto-download Results</span>
                  <p className="text-sm text-gray-500">Automatically download result files when simulation completes</p>
                </div>
              </label>
            </div>

            <div>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings.showAdvancedOptions}
                  onChange={(e) => updateSetting('showAdvancedOptions', e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300"
                />
                <div>
                  <span className="text-gray-700 font-medium">Show Advanced Options</span>
                  <p className="text-sm text-gray-500">Display advanced solver settings in parameter forms</p>
                </div>
              </label>
            </div>
          </div>
        </section>

        {/* Display Preferences */}
        <section className="card-neumorphic">
          <h2 className="text-xl font-bold mb-4">Display Preferences</h2>
          
          <div>
            <label className="block mb-2">
              <span className="text-gray-700 font-medium">Theme</span>
              <p className="text-sm text-gray-500">Visual appearance (coming soon)</p>
            </label>
            <select
              value={settings.theme}
              onChange={(e) => updateSetting('theme', e.target.value as 'light' | 'dark')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled
            >
              <option value="light">Light</option>
              <option value="dark">Dark (Coming Soon)</option>
            </select>
          </div>
        </section>

        {/* About Section */}
        <section className="card-neumorphic">
          <h2 className="text-xl font-bold mb-4">About</h2>
          <div className="space-y-2 text-sm">
            <p><strong>ElmerFEM Educational Platform</strong></p>
            <p>Version: 1.0.0</p>
            <p>Built for high school students learning FEA</p>
            <p className="pt-2">
              <a 
                href="https://www.elmerfem.org" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700"
              >
                Visit ElmerFEM Website
              </a>
            </p>
          </div>
        </section>

        {/* Data Management */}
        <section className="card-neumorphic">
          <h2 className="text-xl font-bold mb-4">Data Management</h2>
          <p className="text-sm text-gray-600 mb-4">
            All data is stored locally in your browser. No information is sent to external servers.
          </p>
          <div className="space-y-3">
            <button
              onClick={() => {
                localStorage.removeItem('elmerfem_recent_simulations');
                window.location.reload();
              }}
              className="w-full btn-neumorphic text-red-600 hover:text-red-700"
            >
              Clear Simulation History
            </button>
            <button
              onClick={() => {
                if (confirm('This will clear all local data. Are you sure?')) {
                  localStorage.clear();
                  window.location.reload();
                }
              }}
              className="w-full btn-neumorphic text-red-600 hover:text-red-700"
            >
              Clear All Local Data
            </button>
          </div>
        </section>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleSave}
            className="flex-1 btn-neumorphic-primary py-3"
            disabled={saved}
          >
            {saved ? 'Saved!' : 'Save Settings'}
          </button>
          <button
            onClick={handleReset}
            className="btn-neumorphic py-3 px-6"
          >
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  );
}

export default Settings; 