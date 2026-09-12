import React, { useState } from 'react';
import { X, Folder, GitBranch, ArrowRight, Loader2, AlertCircle, FolderOpen } from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';
import { FolderBrowserDialog } from './FolderBrowserDialog';

interface IngestModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const IngestModal: React.FC<IngestModalProps> = ({ isOpen, onClose }) => {
  const [tab, setTab] = useState<'local' | 'github'>('local');
  const [localPath, setLocalPath] = useState('');
  const [projectName, setProjectName] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [githubToken, setGithubToken] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isBrowserOpen, setIsBrowserOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { ingestLocal, ingestGithub } = useProjectStore();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      if (tab === 'local') {
        if (!localPath.trim()) throw new Error('Please enter a valid local directory path.');
        await ingestLocal(localPath.trim(), projectName.trim() || undefined);
      } else {
        if (!githubUrl.trim()) throw new Error('Please enter a valid GitHub repository URL.');
        await ingestGithub(githubUrl.trim(), githubToken.trim() || undefined);
      }
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to ingest repository');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-100">Ingest Codebase into CodeBridge</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 p-1 rounded-md">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-[#30363d] bg-[#0d1117]">
          <button
            onClick={() => setTab('local')}
            className={`flex-1 py-3 text-xs font-medium flex items-center justify-center gap-2 border-b-2 transition-colors ${
              tab === 'local'
                ? 'border-purple-500 text-purple-400 bg-[#161b22]'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <Folder className="w-3.5 h-3.5" />
            <span>Local Directory</span>
          </button>
          <button
            onClick={() => setTab('github')}
            className={`flex-1 py-3 text-xs font-medium flex items-center justify-center gap-2 border-b-2 transition-colors ${
              tab === 'github'
                ? 'border-purple-500 text-purple-400 bg-[#161b22]'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>GitHub Repository (Zipball API)</span>
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {tab === 'local' ? (
            <>
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">
                  Local Directory Path
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="/home/asw/Dev/... or Dev/myproject"
                    value={localPath}
                    onChange={(e) => setLocalPath(e.target.value)}
                    className="flex-1 px-3 py-2 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 font-mono"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setIsBrowserOpen(true)}
                    className="px-3 py-2 text-xs font-medium rounded-md bg-[#21262d] hover:bg-[#30363d] text-purple-300 border border-[#30363d] flex items-center gap-1.5 transition-colors shrink-0 shadow-xs cursor-pointer"
                    title="Open Folder Browser"
                  >
                    <FolderOpen className="w-3.5 h-3.5 text-purple-400" />
                    <span>Browse...</span>
                  </button>
                </div>
                <p className="mt-1.5 text-[11px] text-gray-500">
                  Click <strong>Browse...</strong> to pick any folder on your machine, or enter a path.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">
                  Project Display Name (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. VanillaChat, Billing Service"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>

              <FolderBrowserDialog
                isOpen={isBrowserOpen}
                initialPath={localPath || undefined}
                onSelect={(selectedPath) => {
                  setLocalPath(selectedPath);
                  if (!projectName.trim()) {
                    const parts = selectedPath.split('/').filter(Boolean);
                    if (parts.length > 0) {
                      setProjectName(parts[parts.length - 1]);
                    }
                  }
                }}
                onClose={() => setIsBrowserOpen(false)}
              />
            </>
          ) : (
            <>
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">
                  GitHub Repository URL or Owner/Repo
                </label>
                <input
                  type="text"
                  placeholder="https://github.com/owner/repository"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500"
                  required
                />
                <p className="mt-1 text-[11px] text-gray-500">
                  Downloads source archive via GitHub REST API without requiring git CLI installed.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5">
                  Personal Access Token (Optional)
                </label>
                <input
                  type="password"
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx (for private repos or higher limits)"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
              </div>
            </>
          )}

          {/* Actions */}
          <div className="pt-3 border-t border-[#30363d] flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs text-gray-300 hover:text-white rounded-md bg-[#21262d] hover:bg-[#30363d] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-white rounded-md bg-purple-600 hover:bg-purple-500 disabled:opacity-50 transition-colors shadow"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Ingesting & Parsing...</span>
                </>
              ) : (
                <>
                  <span>Start Ingestion</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
