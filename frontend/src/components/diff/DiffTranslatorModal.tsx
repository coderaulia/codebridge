import React, { useState } from 'react';
import {
  X,
  GitPullRequest,
  Sparkles,
  AlertTriangle,
  Database,
  FileCode,
  Copy,
  Check,
  Loader2,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';

interface DiffTranslatorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface DiffFileChange {
  file_path: string;
  change_type: string;
  lines_added: number;
  lines_deleted: number;
  is_schema: boolean;
}

interface DiffResult {
  summary: string;
  user_impact: string;
  database_impact: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  risk_notes: string;
  files_changed: DiffFileChange[];
}

export const DiffTranslatorModal: React.FC<DiffTranslatorModalProps> = ({ isOpen, onClose }) => {
  const { currentProject } = useProjectStore();
  const [diffText, setDiffText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingLocal, setIsFetchingLocal] = useState(false);
  const [result, setResult] = useState<DiffResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFetchLocal = async () => {
    if (!currentProject) return;
    setIsFetchingLocal(true);
    setError(null);
    try {
      const res = await fetch(`/api/diff/local/${currentProject.id}`);
      if (!res.ok) throw new Error('Could not read local git diff');
      const data = await res.json();
      if (data.diff_text) {
        setDiffText(data.diff_text);
      } else {
        setError(data.message || 'No uncommitted git changes found.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch local diff');
    } finally {
      setIsFetchingLocal(false);
    }
  };

  const handleAnalyze = async () => {
    if (!diffText.trim()) return;
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch('/api/diff/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          diff_text: diffText,
          project_id: currentProject?.id,
          project_name: currentProject?.name || '',
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Diff analysis failed');
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze diff');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyNotes = () => {
    if (!result) return;
    const notes = `# 🚀 Executive Release Notes: ${currentProject?.name || 'Release'}
**Risk Level**: ${result.risk_level}

### 1. Summary of Changes
${result.summary}

### 2. User-Facing Feature Impact
${result.user_impact}

### 3. Database & Schema Changes
${result.database_impact}

### 4. Risk & Compliance Notes
${result.risk_notes}
`;
    navigator.clipboard.writeText(notes);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const getRiskBadge = (level: string) => {
    if (level === 'HIGH') {
      return (
        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/40 flex items-center gap-1">
          <AlertTriangle className="w-3.5 h-3.5 text-red-400" /> High Business Risk
        </span>
      );
    }
    if (level === 'MEDIUM') {
      return (
        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Moderate Impact
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Low Risk
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs animate-fade-in select-none">
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden text-gray-200">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
              <GitPullRequest className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-100">PR & Git Diff Plain-English Translator</h2>
              <p className="text-[11px] text-gray-400">
                Translate code changes into executive release notes, user impact, and business risk assessments.
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-[#21262d]">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 select-text">
          {/* Action Bar */}
          <div className="flex items-center justify-between gap-3">
            <label className="text-xs font-medium text-gray-300">Paste Unified Git Diff / PR Patch:</label>
            {currentProject?.source_type === 'local' && (
              <button
                type="button"
                onClick={handleFetchLocal}
                disabled={isFetchingLocal || isLoading}
                className="text-xs px-2.5 py-1 rounded bg-[#21262d] hover:bg-[#30363d] text-gray-300 flex items-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3 h-3 ${isFetchingLocal ? 'animate-spin text-purple-400' : ''}`} />
                <span>Load Current Uncommitted Git Changes</span>
              </button>
            )}
          </div>

          {/* Diff Input */}
          <div className="relative">
            <textarea
              rows={6}
              value={diffText}
              onChange={(e) => setDiffText(e.target.value)}
              placeholder="Paste output of 'git diff' or PR changes here (e.g. diff --git a/... b/...)..."
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-3 text-xs font-mono text-gray-300 placeholder-gray-600 focus:outline-none focus:border-purple-500"
            />
          </div>

          {/* Action Button */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={isLoading || !diffText.trim()}
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Translating Release Changes...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-300" />
                  <span>Generate Plain-English Release Brief</span>
                </>
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/50 text-red-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Analysis Results */}
          {result && (
            <div className="space-y-4 pt-2 border-t border-[#30363d]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-gray-300">Executive Release Assessment:</span>
                  {getRiskBadge(result.risk_level)}
                </div>
                <button
                  type="button"
                  onClick={handleCopyNotes}
                  className="px-2.5 py-1 text-xs rounded bg-[#21262d] hover:bg-[#30363d] text-gray-300 flex items-center gap-1.5 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>Copy Notes</span>
                </button>
              </div>

              {/* 4 Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-lg bg-[#0d1117] border border-[#30363d]">
                  <h4 className="text-xs font-semibold text-purple-300 flex items-center gap-1.5 mb-1.5">
                    <FileCode className="w-3.5 h-3.5" /> 1. Summary of Changes
                  </h4>
                  <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">{result.summary}</p>
                </div>

                <div className="p-3.5 rounded-lg bg-[#0d1117] border border-[#30363d]">
                  <h4 className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5 mb-1.5">
                    <Sparkles className="w-3.5 h-3.5" /> 2. User-Facing Feature Impact
                  </h4>
                  <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">{result.user_impact}</p>
                </div>

                <div className="p-3.5 rounded-lg bg-[#0d1117] border border-[#30363d]">
                  <h4 className="text-xs font-semibold text-amber-300 flex items-center gap-1.5 mb-1.5">
                    <Database className="w-3.5 h-3.5" /> 3. Database & Schema Impact
                  </h4>
                  <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">{result.database_impact}</p>
                </div>

                <div className="p-3.5 rounded-lg bg-[#0d1117] border border-[#30363d]">
                  <h4 className="text-xs font-semibold text-red-300 flex items-center gap-1.5 mb-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" /> 4. Business & Security Risk Notes
                  </h4>
                  <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">{result.risk_notes}</p>
                </div>
              </div>

              {/* Files Touched Table */}
              {result.files_changed.length > 0 && (
                <div className="mt-3 p-3 rounded-lg bg-[#0d1117] border border-[#30363d]">
                  <h5 className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Files Touched ({result.files_changed.length})
                  </h5>
                  <div className="max-h-40 overflow-y-auto space-y-1 font-mono text-xs">
                    {result.files_changed.map((f, i) => (
                      <div key={i} className="flex items-center justify-between py-0.5 border-b border-[#21262d]/50">
                        <span className="truncate max-w-[70%] text-gray-300">{f.file_path}</span>
                        <div className="flex items-center gap-2 shrink-0 text-[11px]">
                          <span className="text-emerald-400">+{f.lines_added}</span>
                          <span className="text-red-400">-{f.lines_deleted}</span>
                          {f.is_schema && (
                            <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30">
                              schema
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
