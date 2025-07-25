import { useState, useEffect } from 'react';

export interface UserSettings {
  defaultMeshDensity: number;
  autoDownloadResults: boolean;
  showAdvancedOptions: boolean;
  theme: 'light' | 'dark';
}

const defaultSettings: UserSettings = {
  defaultMeshDensity: 1.0,
  autoDownloadResults: false,
  showAdvancedOptions: false,
  theme: 'light',
};

const STORAGE_KEY = 'elmerfem_settings';

export function useSettings() {
  const [settings, setSettings] = useState<UserSettings>(defaultSettings);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setSettings({ ...defaultSettings, ...parsed });
      } catch (error) {
        console.error('Failed to parse settings:', error);
      }
    }
  }, []);

  const updateSettings = (updates: Partial<UserSettings>) => {
    const newSettings = { ...settings, ...updates };
    setSettings(newSettings);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
    localStorage.removeItem(STORAGE_KEY);
  };

  return {
    settings,
    updateSettings,
    resetSettings,
  };
} 