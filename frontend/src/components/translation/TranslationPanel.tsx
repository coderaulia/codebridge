import React from 'react';
import {
  FileText,
  LogIn,
  LogOut,
  ShieldCheck,
  GitGraph,
  MessageSquare,
  Sparkles,
  Copy,
  Check,
  Zap,
} from 'lucide-react';
import { useTranslationStore } from '../../stores/useTranslationStore';
import { useProjectStore } from '../../stores/useProjectStore';
import { MermaidViewer } from './MermaidViewer';
import { PlainEnglishChat } from './PlainEnglishChat';

interface TranslationPanelProps {
  width?: number;
  className?: string;
}

export const TranslationPanel: React.FC<TranslationPanelProps> = ({ width, className = '' }) => {
  const { translation, streamingText, isTranslating, activeTab, setActiveTab } = useTranslationStore();
  const { selectedRange, currentFile } = useProjectStore();
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    const textToCopy =
      translation?.raw_markdown ||
      (translation
        ? `### 1. Plain-English Summary\n${translation.plain_summary}\n\n### 2. Inputs & Parameters\n${translation.inputs_and_parameters}\n\n### 3. Outputs & Effects\n${translation.outputs_and_effects}\n\n### 4. Business Rule\n${translation.business_rule_tie_in}`
        : streamingText);

    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <aside
      style={width ? { width: `${width}px` } : undefined}
      className={`bg-[#0d1117] flex flex-col h-full border-l border-[#30363d] select-none shrink-0 ${
        width ? '' : 'w-full md:w-96'
      } ${className}`}
    >
      {/* Panel Header */}
      <div className="h-10 bg-[#161b22] border-b border-[#30363d] px-3 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 font-semibold text-gray-200">
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>Plain-English Translation</span>
        </div>

        <div className="flex items-center gap-2">
          {translation?.cached && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-950/60 text-emerald-300 border border-emerald-800/50 flex items-center gap-1">
              <Zap className="w-2.5 h-2.5" /> Cached
            </span>
          )}
          <button
            onClick={handleCopy}
            className="p-1 hover:bg-[#21262d] rounded text-gray-400 hover:text-gray-200 transition-colors"
            title="Copy Translation to Clipboard"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#30363d] bg-[#161b22]/50 text-xs overflow-x-auto">
        <button
          onClick={() => setActiveTab('summary')}
          className={`flex items-center gap-1 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
            activeTab === 'summary'
              ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <FileText className="w-3 h-3" />
          <span>Summary</span>
        </button>

        <button
          onClick={() => setActiveTab('inputs')}
          className={`flex items-center gap-1 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
            activeTab === 'inputs'
              ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <LogIn className="w-3 h-3" />
          <span>Inputs</span>
        </button>

        <button
          onClick={() => setActiveTab('outputs')}
          className={`flex items-center gap-1 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
            activeTab === 'outputs'
              ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <LogOut className="w-3 h-3" />
          <span>Outputs</span>
        </button>

        <button
          onClick={() => setActiveTab('business')}
          className={`flex items-center gap-1 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
            activeTab === 'business'
              ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <ShieldCheck className="w-3 h-3" />
          <span>Business</span>
        </button>

        <button
          onClick={() => setActiveTab('diagram')}
          className={`flex items-center gap-1 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
            activeTab === 'diagram'
              ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <GitGraph className="w-3 h-3" />
          <span>Journey</span>
        </button>

        <button
          onClick={() => setActiveTab('raw')}
          className={`flex items-center gap-1 px-3 py-2 border-b-2 font-medium transition-colors whitespace-nowrap ${
            activeTab === 'raw'
              ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <MessageSquare className="w-3 h-3" />
          <span>Q&A</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4 select-text">
        {isTranslating ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs text-purple-400">
              <span className="w-2 h-2 rounded-full bg-purple-500 animate-ping" />
              <span>Translating code into plain English...</span>
            </div>
            {streamingText ? (
              <div className="p-3.5 rounded-lg bg-[#161b22] border border-[#30363d] text-xs text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
                {streamingText}
              </div>
            ) : (
              <div className="space-y-2 animate-pulse pt-2">
                <div className="h-3.5 bg-[#21262d] rounded w-3/4" />
                <div className="h-3.5 bg-[#21262d] rounded w-full" />
                <div className="h-3.5 bg-[#21262d] rounded w-5/6" />
              </div>
            )}
          </div>
        ) : !translation && !streamingText ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-xs text-gray-500">
            <div className="w-10 h-10 rounded-full bg-[#161b22] flex items-center justify-center mb-3">
              <Sparkles className="w-5 h-5 text-gray-500" />
            </div>
            <h4 className="font-semibold text-gray-300 mb-1">Highlight code to translate</h4>
            <p className="text-gray-500 leading-relaxed">
              Select any function, class, or database schema in the center Monaco viewer, then click "Translate in Plain English".
            </p>
          </div>
        ) : activeTab === 'diagram' ? (
          <MermaidViewer chart={translation?.mermaid_diagram || ''} />
        ) : activeTab === 'raw' ? (
          <PlainEnglishChat />
        ) : (
          <div className="space-y-4 text-xs leading-relaxed">
            {/* Context Badge */}
            {selectedRange && (
              <div className="p-2 rounded bg-[#161b22] border border-[#30363d] text-[11px] text-gray-400">
                Inspecting <span className="font-mono text-purple-300">{currentFile?.relative_path}</span> (Lines {selectedRange.startLine}–{selectedRange.endLine})
              </div>
            )}

            {/* Active Tab View */}
            {activeTab === 'summary' && (
              <div className="p-3.5 rounded-lg bg-[#161b22] border border-[#30363d]">
                <h4 className="font-semibold text-purple-300 uppercase tracking-wider text-[10px] mb-2 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5" /> Plain-English Summary
                </h4>
                <div className="whitespace-pre-line text-gray-200">
                  {translation?.plain_summary || streamingText}
                </div>
              </div>
            )}

            {activeTab === 'inputs' && (
              <div className="p-3.5 rounded-lg bg-[#161b22] border border-[#30363d]">
                <h4 className="font-semibold text-blue-300 uppercase tracking-wider text-[10px] mb-2 flex items-center gap-1.5">
                  <LogIn className="w-3.5 h-3.5" /> Inputs & Parameters (What goes in)
                </h4>
                <div className="whitespace-pre-line text-gray-200">
                  {translation?.inputs_and_parameters || 'Standard application data parameters.'}
                </div>
              </div>
            )}

            {activeTab === 'outputs' && (
              <div className="p-3.5 rounded-lg bg-[#161b22] border border-[#30363d]">
                <h4 className="font-semibold text-emerald-300 uppercase tracking-wider text-[10px] mb-2 flex items-center gap-1.5">
                  <LogOut className="w-3.5 h-3.5" /> Outputs & Effects (What happens)
                </h4>
                <div className="whitespace-pre-line text-gray-200">
                  {translation?.outputs_and_effects || 'Returns result or modifies database records.'}
                </div>
              </div>
            )}

            {activeTab === 'business' && (
              <div className="p-3.5 rounded-lg bg-[#161b22] border border-[#30363d]">
                <h4 className="font-semibold text-amber-300 uppercase tracking-wider text-[10px] mb-2 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5" /> Business Rule Tie-In (Why this matters)
                </h4>
                <div className="whitespace-pre-line text-gray-200">
                  {translation?.business_rule_tie_in || 'Essential to system reliability and business operations.'}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
