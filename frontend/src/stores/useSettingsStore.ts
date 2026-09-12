import { create } from 'zustand';
import axios from 'axios';
import type { ProviderSettings, ConnectionTestResponse } from '../types/settings';

interface SettingsState {
  settings: ProviderSettings;
  isSettingsOpen: boolean;
  isTesting: boolean;
  testResult: ConnectionTestResponse | null;
  error: string | null;

  setSettingsOpen: (open: boolean) => void;
  loadSettings: () => Promise<void>;
  updateSettings: (newSettings: Partial<ProviderSettings>) => Promise<void>;
  testConnection: (customSettings?: Partial<ProviderSettings>) => Promise<ConnectionTestResponse>;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: {
    id: 'active_config',
    provider_type: 'ollama',
    base_url: 'http://localhost:11434/v1',
    api_key: '',
    model_name: 'llama3.2',
    temperature: 0.2,
  },
  isSettingsOpen: false,
  isTesting: false,
  testResult: null,
  error: null,

  setSettingsOpen: (open) => set({ isSettingsOpen: open, testResult: null }),

  loadSettings: async () => {
    try {
      const res = await axios.get<ProviderSettings>('/api/settings');
      set({ settings: res.data });
    } catch (err: any) {
      set({ error: err.message });
    }
  },

  updateSettings: async (newSettings) => {
    try {
      const merged = { ...get().settings, ...newSettings };
      const res = await axios.post<ProviderSettings>('/api/settings', merged);
      set({ settings: res.data });
    } catch (err: any) {
      set({ error: err.message });
    }
  },

  testConnection: async (customSettings) => {
    const target = { ...get().settings, ...customSettings };
    set({ isTesting: true, testResult: null });
    try {
      const res = await axios.post<ConnectionTestResponse>('/api/settings/test-connection', {
        provider_type: target.provider_type,
        base_url: target.base_url,
        api_key: target.api_key,
        model_name: target.model_name,
      });
      set({ testResult: res.data, isTesting: false });
      return res.data;
    } catch (err: any) {
      const failure: ConnectionTestResponse = {
        success: false,
        latency_ms: null,
        message: err.response?.data?.detail || err.message,
      };
      set({ testResult: failure, isTesting: false });
      return failure;
    }
  },
}));
