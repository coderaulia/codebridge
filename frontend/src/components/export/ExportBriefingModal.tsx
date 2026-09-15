import React, { useEffect, useState } from 'react';
import {
  X,
  FileDown,
  Printer,
  Copy,
  Check,
  Loader2,
  FileText,
  ExternalLink,
} from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';

interface ExportBriefingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ExportBriefingModal: React.FC<ExportBriefingModalProps> = ({ isOpen, onClose }) => {
  const { currentProject } = useProjectStore();
  const [markdownContent, setMarkdownContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && currentProject) {
      loadExport();
    }
  }, [isOpen, currentProject]);

  if (!isOpen || !currentProject) return null;

  const loadExport = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${currentProject.id}/export?format=markdown`);
      if (!res.ok) throw new Error('Failed to load export report');
      const text = await res.text();
      setMarkdownContent(text);
    } catch (err: any) {
      setError(err.message || 'Error generating export report');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadMarkdown = () => {
    const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${currentProject.name.replace(/[^a-zA-Z0-9_-]/g, '_')}_architecture_briefing.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(markdownContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleOpenPrintHtml = () => {
    window.open(`/api/projects/${currentProject.id}/export?format=html`, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs animate-fade-in select-none">
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden text-gray-200">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-100">Export Executive Architecture Briefing</h2>
              <p className="text-[11px] text-gray-400">
                Share full-system architecture, domain maps, and database schemas with PMs and stakeholders.
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-[#21262d]">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="px-5 py-2.5 bg-[#0d1117] border-b border-[#30363d] flex flex-wrap items-center justify-between gap-3 text-xs">
          <span className="text-gray-400 font-mono text-[11px]">{currentProject.name} Architecture Report</span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              disabled={isLoading || !markdownContent}
              className="px-2.5 py-1.5 rounded bg-[#21262d] hover:bg-[#30363d] text-gray-300 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>Copy Markdown</span>
            </button>
            <button
              onClick={handleDownloadMarkdown}
              disabled={isLoading || !markdownContent}
              className="px-3 py-1.5 rounded bg-[#21262d] hover:bg-[#30363d] text-gray-200 flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <FileDown className="w-3.5 h-3.5 text-purple-400" />
              <span>Download .md</span>
            </button>
            <button
              onClick={handleOpenPrintHtml}
              disabled={isLoading}
              className="px-3 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / Save as PDF</span>
              <ExternalLink className="w-3 h-3 opacity-80" />
            </button>
          </div>
        </div>

        {/* Body Preview */}
        <div className="flex-1 overflow-y-auto p-5 select-text">
          {isLoading ? (
            <div className="h-64 flex flex-col items-center justify-center gap-2 text-xs text-gray-400">
              <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
              <span>Compiling Architecture Briefing...</span>
            </div>
          ) : error ? (
            <div className="p-4 rounded-lg bg-red-950/30 border border-red-800/50 text-red-300 text-xs">
              {error}
            </div>
          ) : (
            <pre className="text-xs font-mono text-gray-300 whitespace-pre-wrap leading-relaxed bg-[#0d1117] p-4 rounded-lg border border-[#30363d]">
              {markdownContent}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
