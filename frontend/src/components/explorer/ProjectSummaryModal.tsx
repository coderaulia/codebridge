import { useShallow } from 'zustand/react/shallow';
import React, { useState } from 'react';
import { X, Layers, Briefcase, FileCode, GitGraph, RefreshCw, Sparkles } from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';
import { lazy, Suspense } from 'react';
const MermaidViewer = lazy(() => import('../translation/MermaidViewer').then((m) => ({ default: m.MermaidViewer })));

interface ProjectSummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ProjectSummaryModal: React.FC<ProjectSummaryModalProps> = ({ isOpen, onClose }) => {
  const { currentProject, domains, totalFiles, totalSymbols, macroDiagram, generateSummaries, isLoading } = useProjectStore(useShallow((s) => ({ currentProject: s.currentProject, domains: s.domains, totalFiles: s.totalFiles, totalSymbols: s.totalSymbols, macroDiagram: s.macroDiagram, generateSummaries: s.generateSummaries, isLoading: s.isLoading })));
  const [activeTab, setActiveTab] = useState<'briefing' | 'architecture'>('briefing');

  if (!isOpen || !currentProject) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4">
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-800/50 text-purple-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-100">Executive Repository Studio</h2>
              <div className="text-xs text-gray-400">{currentProject.name}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => generateSummaries(currentProject.id)}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-xs font-medium text-purple-300 transition-colors disabled:opacity-50"
              title="Generate bottom-up AI summaries for all files and domains"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-purple-400' : ''}`} />
              <span>{isLoading ? 'Synthesizing...' : 'AI Re-Summarize'}</span>
            </button>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-200 p-1.5 rounded-md transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex border-b border-[#30363d] bg-[#161b22]/70 px-6 gap-2 text-xs">
          <button
            onClick={() => setActiveTab('briefing')}
            className={`py-2.5 px-3 border-b-2 font-medium flex items-center gap-1.5 transition-colors ${
              activeTab === 'briefing'
                ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Executive Briefing</span>
          </button>
          <button
            onClick={() => setActiveTab('architecture')}
            className={`py-2.5 px-3 border-b-2 font-medium flex items-center gap-1.5 transition-colors ${
              activeTab === 'architecture'
                ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <GitGraph className="w-3.5 h-3.5 text-purple-400" />
            <span>System Architecture Map</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm text-gray-300 leading-relaxed flex-1">
          {activeTab === 'briefing' ? (
            <>
              {/* Stats Bar */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 rounded-lg bg-[#0d1117] border border-[#30363d] text-center">
                  <div className="text-xs text-gray-500 font-medium">Business Domains</div>
                  <div className="text-lg font-bold text-purple-400 mt-0.5">{domains.length}</div>
                </div>
                <div className="p-3.5 rounded-lg bg-[#0d1117] border border-[#30363d] text-center">
                  <div className="text-xs text-gray-500 font-medium">Indexed Files</div>
                  <div className="text-lg font-bold text-indigo-400 mt-0.5">{totalFiles}</div>
                </div>
                <div className="p-3.5 rounded-lg bg-[#0d1117] border border-[#30363d] text-center">
                  <div className="text-xs text-gray-500 font-medium">Code Symbols</div>
                  <div className="text-lg font-bold text-emerald-400 mt-0.5">{totalSymbols}</div>
                </div>
              </div>

              {/* Executive Overview Body */}
              <div className="p-4 rounded-xl bg-[#0d1117] border border-[#30363d]">
                <h3 className="text-xs font-bold uppercase tracking-wider text-purple-300 mb-2.5 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>What This Repository Accomplishes</span>
                </h3>
                <div className="whitespace-pre-line text-xs leading-relaxed text-gray-300">
                  {currentProject.executive_summary ||
                    'Analysis in progress... This repository coordinates business services, API endpoints, and data storage.'}
                </div>
              </div>

              {/* Business Domain Breakdown */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">
                  Identified Operational Domains
                </h3>
                <div className="space-y-2">
                  {domains.map((d) => (
                    <div
                      key={d.domain_name}
                      className="p-3 rounded-lg bg-[#0d1117] border border-[#30363d] flex flex-col gap-1"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-purple-500" />
                          <span className="font-semibold text-xs text-gray-200">{d.domain_name}</span>
                        </div>
                        <div className="flex items-center gap-1 text-[11px] text-gray-400">
                          <FileCode className="w-3.5 h-3.5 text-gray-500" />
                          <span>{d.files.length} files</span>
                        </div>
                      </div>
                      {d.description && (
                        <p className="text-[11px] text-gray-400 pl-4">{d.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-[#0d1117] border border-[#30363d] text-xs text-gray-400 flex items-center justify-between">
                <span>Multi-tier macro architecture diagram mapping presentation, API ingress, services, and database persistence.</span>
                <span className="text-purple-400 font-mono text-[10px]">Tiered Topology</span>
              </div>
              <div className="h-[420px] rounded-xl overflow-hidden border border-[#30363d]">
                <Suspense fallback={<div className="p-8 text-center text-xs text-gray-500">Loading diagram…</div>}>
<MermaidViewer chart={macroDiagram || ''} />
</Suspense>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#30363d] flex justify-end bg-[#161b22]">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium rounded-md bg-[#21262d] hover:bg-[#30363d] text-gray-200 transition-colors"
          >
            Close Briefing
          </button>
        </div>
      </div>
    </div>
  );
};
