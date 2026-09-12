import React, { useState, useEffect } from 'react';
import { X, CheckCircle2, XCircle, Loader2, Sparkles, Cpu } from 'lucide-react';
import { useSettingsStore } from '../../stores/useSettingsStore';
import type { ProviderSettings } from '../../types/settings';

const PRESETS = [
  {
    name: 'Local Ollama',
    provider_type: 'ollama',
    base_url: 'http://localhost:11434/v1',
    model_name: 'llama3.2',
    requires_key: false,
  },
  {
    name: 'LM Studio',
    provider_type: 'lmstudio',
    base_url: 'http://localhost:1234/v1',
    model_name: 'local-model',
    requires_key: false,
  },
  {
    name: 'DeepSeek API',
    provider_type: 'deepseek',
    base_url: 'https://api.deepseek.com/v1',
    model_name: 'deepseek-chat',
    requires_key: true,
  },
  {
    name: 'OpenRouter',
    provider_type: 'openrouter',
    base_url: 'https://openrouter.ai/api/v1',
    model_name: 'meta-llama/llama-3.1-70b-instruct',
    requires_key: true,
  },
  {
    name: 'OpenAI (Official)',
    provider_type: 'openai',
    base_url: 'https://api.openai.com/v1',
    model_name: 'gpt-4o-mini',
    requires_key: true,
  },
];

export const SettingsModal: React.FC = () => {
  const { settings, isSettingsOpen, isTesting, testResult, setSettingsOpen, updateSettings, testConnection, loadSettings } =
    useSettingsStore();

  const [formData, setFormData] = useState<ProviderSettings>(settings);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isSettingsOpen) {
      loadSettings();
      setFormData(settings);
      setSaveSuccess(false);
    }
  }, [isSettingsOpen]);

  if (!isSettingsOpen) return null;

  const handleApplyPreset = (preset: (typeof PRESETS)[0]) => {
    setFormData((prev) => ({
      ...prev,
      provider_type: preset.provider_type,
      base_url: preset.base_url,
      model_name: preset.model_name,
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateSettings(formData);
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
      setSettingsOpen(false);
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-purple-400" />
            <h2 className="text-base font-semibold text-gray-100">AI Provider & Model Settings</h2>
          </div>
          <button onClick={() => setSettingsOpen(false)} className="text-gray-400 hover:text-gray-200 p-1 rounded-md">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSave} className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Quick Presets */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">Quick Presets</label>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-1.5">
              {PRESETS.map((p) => (
                <button
                  type="button"
                  key={p.name}
                  onClick={() => handleApplyPreset(p)}
                  className={`px-2 py-1.5 text-[11px] font-medium rounded-md border text-center transition-all ${
                    formData.provider_type === p.provider_type
                      ? 'bg-purple-950/50 border-purple-500 text-purple-300'
                      : 'bg-[#21262d] border-[#30363d] text-gray-300 hover:bg-[#30363d]'
                  }`}
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          {/* Base URL */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">OpenAI-Compatible Base URL</label>
            <input
              type="text"
              value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 focus:outline-none focus:border-purple-500 font-mono"
              placeholder="http://localhost:11434/v1"
              required
            />
          </div>

          {/* API Key */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              API Key <span className="text-gray-500 font-normal">(Leave empty for local Ollama / LM Studio)</span>
            </label>
            <input
              type="password"
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 focus:outline-none focus:border-purple-500 font-mono"
              placeholder="sk-..."
            />
          </div>

          {/* Model Name */}
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Target Model Name</label>
            <input
              type="text"
              value={formData.model_name}
              onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 focus:outline-none focus:border-purple-500 font-mono"
              placeholder="llama3.2, deepseek-chat, gpt-4o-mini"
              required
            />
          </div>

          {/* Temperature Slider */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-xs font-medium text-gray-300">Temperature</label>
              <span className="text-xs font-mono text-purple-400">{formData.temperature}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={formData.temperature}
              onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
              className="w-full accent-purple-500 h-1.5 bg-[#21262d] rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
              <span>Deterministic & Accurate (0.0)</span>
              <span>Balanced (0.5)</span>
              <span>Creative (1.0)</span>
            </div>
          </div>

          {/* Diagnostic Test Result */}
          {testResult && (
            <div
              className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
                testResult.success
                  ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                  : 'bg-red-950/40 border-red-800/60 text-red-300'
              }`}
            >
              {testResult.success ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              )}
              <div>
                <div className="font-semibold">{testResult.message}</div>
                {testResult.available_models && testResult.available_models.length > 0 && (
                  <div className="mt-1 text-[11px] text-gray-400">
                    Discovered models: {testResult.available_models.slice(0, 5).join(', ')}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-3 border-t border-[#30363d] flex items-center justify-between">
            <button
              type="button"
              onClick={() => testConnection(formData)}
              disabled={isTesting}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-[#21262d] hover:bg-[#30363d] text-purple-300 border border-[#30363d] flex items-center gap-1.5 disabled:opacity-50 transition-colors"
            >
              {isTesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              <span>Test Connection</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setSettingsOpen(false)}
                className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 text-xs font-medium rounded-md bg-purple-600 hover:bg-purple-500 text-white shadow transition-colors"
              >
                {saveSuccess ? 'Saved!' : 'Save Settings'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
