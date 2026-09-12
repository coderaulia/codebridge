import React, { useState } from 'react';
import {
  X,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  FolderOpen,
  GitBranch,
  Layers,
  Code2,
  Cpu,
  Play,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';
import { useSettingsStore } from '../../stores/useSettingsStore';
import { FolderBrowserDialog } from '../layout/FolderBrowserDialog';

interface OnboardingWizardProps {
  isOpen: boolean;
  onClose: () => void;
}

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({ isOpen, onClose }) => {
  const [step, setStep] = useState<number>(1);
  const { ingestLocal, ingestGithub, isLoading } = useProjectStore();
  const { settings, updateSettings, testConnection, isTesting, testResult } = useSettingsStore();

  const [isFolderBrowserOpen, setIsFolderBrowserOpen] = useState(false);
  const [localPathInput, setLocalPathInput] = useState('');
  const [githubUrlInput, setGithubUrlInput] = useState('');
  const [ingestError, setIngestError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFinish = () => {
    localStorage.setItem('codebridge_onboarding_completed', 'true');
    onClose();
  };

  const handleLoadDemo = async () => {
    setIngestError(null);
    try {
      await ingestLocal('examples/ecommerce-app', 'E-Commerce Platform Demo');
      handleFinish();
    } catch (err: any) {
      setIngestError(err.message || 'Failed to load demo repository');
    }
  };

  const handleLocalSubmit = async () => {
    if (!localPathInput.trim()) return;
    setIngestError(null);
    try {
      await ingestLocal(localPathInput.trim());
      handleFinish();
    } catch (err: any) {
      setIngestError(err.message || 'Failed to ingest local directory');
    }
  };

  const handleGithubSubmit = async () => {
    if (!githubUrlInput.trim()) return;
    setIngestError(null);
    try {
      await ingestGithub(githubUrlInput.trim());
      handleFinish();
    } catch (err: any) {
      setIngestError(err.message || 'Failed to ingest GitHub repo');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xs p-4 select-none">
      <div className="bg-[#161b22] border border-[#30363d] rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col min-h-[520px]">
        {/* Wizard Header */}
        <div className="px-6 py-4 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-gray-100">Welcome to CodeBridge</h2>
              <div className="text-[11px] text-gray-400">Local Codebase Analyzer by Vanaila • Step {step} of 4</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex gap-1.5">
              {[1, 2, 3, 4].map((s) => (
                <div
                  key={s}
                  onClick={() => setStep(s)}
                  className={`w-2.5 h-2.5 rounded-full cursor-pointer transition-all ${
                    step === s ? 'bg-purple-500 scale-125' : s < step ? 'bg-purple-800' : 'bg-[#30363d]'
                  }`}
                />
              ))}
            </div>
            <button onClick={handleFinish} className="text-gray-400 hover:text-gray-200 p-1 rounded-md ml-2">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 p-8 overflow-y-auto">
          {/* STEP 1: WELCOME & ARCHITECTURE */}
          {step === 1 && (
            <div className="space-y-5 animate-fade-in">
              <div className="text-center space-y-2 max-w-lg mx-auto">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  Built for Product Managers, Founders & Engineers
                </span>
                <h3 className="text-xl font-bold text-white tracking-tight">
                  Understand Any Codebase in Plain English
                </h3>
                <p className="text-xs text-gray-400 leading-relaxed">
                  CodeBridge pairs fast, deterministic static code parsers with autonomous LLM translation agents to
                  bridge the gap between complex software and business stakeholders.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3 pt-3">
                <div className="p-3.5 rounded-xl bg-[#0d1117] border border-[#30363d] text-center space-y-1.5">
                  <div className="w-8 h-8 rounded-lg bg-purple-950/60 border border-purple-800/50 flex items-center justify-center mx-auto text-purple-400">
                    <Layers className="w-4 h-4" />
                  </div>
                  <div className="text-xs font-bold text-gray-200">1. Business Domains</div>
                  <div className="text-[11px] text-gray-500 leading-normal">
                    Cryptic directories mapped to intuitive operational modules.
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#0d1117] border border-[#30363d] text-center space-y-1.5">
                  <div className="w-8 h-8 rounded-lg bg-indigo-950/60 border border-indigo-800/50 flex items-center justify-center mx-auto text-indigo-400">
                    <Code2 className="w-4 h-4" />
                  </div>
                  <div className="text-xs font-bold text-gray-200">2. Monaco Inspector</div>
                  <div className="text-[11px] text-gray-500 leading-normal">
                    Inspect code and schemas with quick symbol navigation.
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#0d1117] border border-[#30363d] text-center space-y-1.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-950/60 border border-emerald-800/50 flex items-center justify-center mx-auto text-emerald-400">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div className="text-xs font-bold text-gray-200">3. Plain Translation</div>
                  <div className="text-[11px] text-gray-500 leading-normal">
                    4-part structured breakdown & live Mermaid visual journeys.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: AI PROVIDER */}
          {step === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <h3 className="text-base font-bold text-white">Configure Your AI Model Engine</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  CodeBridge dynamically connects to any OpenAI-compatible provider. Local models (Ollama / LM Studio)
                  keep 100% of your code on your machine.
                </p>
              </div>

              {/* Provider selector */}
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'ollama', name: 'Local Ollama', url: 'http://localhost:11434/v1', model: 'llama3.2', desc: '100% local & private' },
                  { id: 'deepseek', name: 'DeepSeek API', url: 'https://api.deepseek.com/v1', model: 'deepseek-chat', desc: 'Fast & high-fidelity' },
                  { id: 'openai', name: 'Official OpenAI', url: 'https://api.openai.com/v1', model: 'gpt-4o-mini', desc: 'Cloud standard' },
                  { id: 'lmstudio', name: 'LM Studio', url: 'http://localhost:1234/v1', model: 'local-model', desc: 'Local desktop runner' },
                ].map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() =>
                      updateSettings({
                        provider_type: p.id,
                        base_url: p.url,
                        model_name: p.model,
                      })
                    }
                    className={`p-3 rounded-xl border text-left transition-all ${
                      settings.provider_type === p.id
                        ? 'bg-purple-950/40 border-purple-500 text-purple-200'
                        : 'bg-[#0d1117] border-[#30363d] text-gray-300 hover:bg-[#161b22]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold">{p.name}</span>
                      {settings.provider_type === p.id && <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" />}
                    </div>
                    <div className="text-[11px] text-gray-500 mt-1 font-mono">{p.model}</div>
                    <div className="text-[10px] text-purple-400 mt-0.5">{p.desc}</div>
                  </button>
                ))}
              </div>

              {/* API Key input if needed */}
              {['openai', 'deepseek', 'openrouter'].includes(settings.provider_type) && (
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    API Key for {settings.provider_type}
                  </label>
                  <input
                    type="password"
                    placeholder="sk-..."
                    value={settings.api_key}
                    onChange={(e) => updateSettings({ api_key: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 font-mono focus:outline-none focus:border-purple-500"
                  />
                </div>
              )}

              {/* Diagnostic Button */}
              <div className="pt-2 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => testConnection()}
                  disabled={isTesting}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#21262d] hover:bg-[#30363d] text-xs font-medium text-purple-300 border border-[#30363d] transition-colors"
                >
                  {isTesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Cpu className="w-3.5 h-3.5" />}
                  <span>Test Connection to {settings.base_url}</span>
                </button>

                {testResult && (
                  <span
                    className={`text-xs font-medium flex items-center gap-1 ${
                      testResult.success ? 'text-emerald-400' : 'text-amber-400'
                    }`}
                  >
                    {testResult.success ? `Connected (${testResult.latency_ms}ms)` : 'Endpoint offline (offline mode available)'}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* STEP 3: LOAD FIRST REPO */}
          {step === 3 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <h3 className="text-base font-bold text-white">Ingest Your First Codebase</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Try our instant built-in demo or connect a local directory / GitHub repository.
                </p>
              </div>

              {ingestError && (
                <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{ingestError}</span>
                </div>
              )}

              {/* Demo 1-Click Card */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-purple-950/40 to-indigo-950/40 border border-purple-800/50 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      Recommended for Quick Tour
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white mt-1">Built-in E-Commerce Demo</h4>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Includes Prisma schema, Stripe payment processor, auth service, and mailer.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleLoadDemo}
                  disabled={isLoading}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs shadow-md transition-colors shrink-0"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
                  <span>Load Demo App</span>
                </button>
              </div>

              {/* Local Folder Option */}
              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#30363d] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="w-4 h-4 text-purple-400" />
                    <span className="text-xs font-bold text-gray-200">Ingest Local Folder</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsFolderBrowserOpen(true)}
                    className="px-2.5 py-1 rounded bg-[#21262d] hover:bg-[#30363d] text-purple-300 text-xs border border-[#30363d]"
                  >
                    Open Folder Browser...
                  </button>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="/home/asw/Dev/... or Dev/myproject"
                    value={localPathInput}
                    onChange={(e) => setLocalPathInput(e.target.value)}
                    className="flex-1 px-3 py-1.5 text-xs rounded bg-[#161b22] border border-[#30363d] text-gray-200 font-mono focus:outline-none focus:border-purple-500"
                  />
                  <button
                    type="button"
                    onClick={handleLocalSubmit}
                    disabled={isLoading || !localPathInput.trim()}
                    className="px-3 py-1.5 text-xs font-medium rounded bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50"
                  >
                    Ingest
                  </button>
                </div>
              </div>

              {/* GitHub Option */}
              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#30363d] space-y-2">
                <div className="flex items-center gap-2">
                  <GitBranch className="w-4 h-4 text-purple-400" />
                  <span className="text-xs font-bold text-gray-200">Ingest from GitHub (Zipball API)</span>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="https://github.com/owner/repo"
                    value={githubUrlInput}
                    onChange={(e) => setGithubUrlInput(e.target.value)}
                    className="flex-1 px-3 py-1.5 text-xs rounded bg-[#161b22] border border-[#30363d] text-gray-200 font-mono focus:outline-none focus:border-purple-500"
                  />
                  <button
                    type="button"
                    onClick={handleGithubSubmit}
                    disabled={isLoading || !githubUrlInput.trim()}
                    className="px-3 py-1.5 text-xs font-medium rounded bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50"
                  >
                    Fetch
                  </button>
                </div>
              </div>

              <FolderBrowserDialog
                isOpen={isFolderBrowserOpen}
                onSelect={(path) => setLocalPathInput(path)}
                onClose={() => setIsFolderBrowserOpen(false)}
              />
            </div>
          )}

          {/* STEP 4: 3-CLICK QUICK TOUR */}
          {step === 4 && (
            <div className="space-y-4 animate-fade-in text-center max-w-lg mx-auto py-2">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center mx-auto shadow-lg">
                <CheckCircle2 className="w-7 h-7 text-white" />
              </div>

              <h3 className="text-xl font-bold text-white">You are Ready to Bridge Code!</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Here is the 3-step workflow non-technical stakeholders use in CodeBridge:
              </p>

              <div className="space-y-2.5 text-left pt-2">
                <div className="p-3 rounded-lg bg-[#0d1117] border border-[#30363d] flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-purple-900/60 text-purple-300 font-bold text-xs flex items-center justify-center shrink-0 border border-purple-700/50">
                    1
                  </span>
                  <span className="text-xs text-gray-300">
                    Select any file or database schema under the <strong>Business Domain Map</strong> on the left.
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-[#0d1117] border border-[#30363d] flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-indigo-900/60 text-indigo-300 font-bold text-xs flex items-center justify-center shrink-0 border border-indigo-700/50">
                    2
                  </span>
                  <span className="text-xs text-gray-300">
                    Highlight any function or table in the center <strong>Monaco Viewer</strong>.
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-[#0d1117] border border-[#30363d] flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-emerald-900/60 text-emerald-300 font-bold text-xs flex items-center justify-center shrink-0 border border-emerald-700/50">
                    3
                  </span>
                  <span className="text-xs text-gray-300">
                    Click <strong>"✨ Translate in Plain English"</strong> to receive the 4-part breakdown and interactive Mermaid visual diagram!
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Wizard Footer */}
        <div className="px-6 py-3.5 border-t border-[#30363d] flex items-center justify-between bg-[#161b22]">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s - 1)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-300 hover:text-white rounded bg-[#21262d] hover:bg-[#30363d]"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleFinish}
              className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200"
            >
              Skip Tour
            </button>

            {step < 4 ? (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-md bg-purple-600 hover:bg-purple-500 text-white shadow"
              >
                <span>Next Step</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleFinish}
                className="flex items-center gap-1.5 px-5 py-1.5 text-xs font-bold rounded-md bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg"
              >
                <span>Enter CodeBridge Studio</span>
                <Sparkles className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
