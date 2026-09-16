import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Database,
  FileCode,
  FileText,
  Trash2,
  FolderTree,
  Search,
  Sparkles,
  Loader2,
} from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';
import type { FileRecord } from '../../types/project';

interface DomainNavigatorProps {
  onClose?: () => void;
  className?: string;
}

export const DomainNavigator: React.FC<DomainNavigatorProps> = ({ onClose, className = '' }) => {
  const {
    projects,
    currentProject,
    domains,
    currentFile,
    scanStatus,
    selectProject,
    selectFile,
    deleteProject,
    startProjectScan,
  } = useProjectStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedDomains, setCollapsedDomains] = useState<Record<string, boolean>>({});

  const toggleDomain = (domainName: string) => {
    setCollapsedDomains((prev) => ({ ...prev, [domainName]: !prev[domainName] }));
  };

  const getFileBadge = (file: FileRecord) => {
    if (file.file_type === 'schema' || file.language === 'prisma' || file.language === 'sql' || file.language === 'openapi') {
      return (
        <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 font-mono">
          <Database className="w-2.5 h-2.5" /> {file.language === 'openapi' ? 'openapi' : 'schema'}
        </span>
      );
    }
    if (file.file_type === 'doc') {
      return (
        <span className="px-1.5 py-0.2 rounded text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/30 flex items-center gap-1 font-mono">
          <FileText className="w-2.5 h-2.5" /> doc
        </span>
      );
    }
    if (file.language === 'go') {
      return (
        <span className="px-1.5 py-0.2 rounded text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-1 font-mono">
          <FileCode className="w-2.5 h-2.5" /> go
        </span>
      );
    }
    if (file.language === 'rust') {
      return (
        <span className="px-1.5 py-0.2 rounded text-[10px] bg-orange-500/20 text-orange-300 border border-orange-500/30 flex items-center gap-1 font-mono">
          <FileCode className="w-2.5 h-2.5" /> rust
        </span>
      );
    }
    if (file.language === 'java') {
      return (
        <span className="px-1.5 py-0.2 rounded text-[10px] bg-red-500/20 text-red-300 border border-red-500/30 flex items-center gap-1 font-mono">
          <FileCode className="w-2.5 h-2.5" /> java
        </span>
      );
    }
    return (
      <span className="px-1.5 py-0.2 rounded text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1 font-mono">
        <FileCode className="w-2.5 h-2.5" /> {file.language}
      </span>
    );
  };

  const filteredDomains = domains
    .map((d) => ({
      ...d,
      files: d.files.filter(
        (f) =>
          f.relative_path.toLowerCase().includes(searchQuery.toLowerCase()) ||
          d.domain_name.toLowerCase().includes(searchQuery.toLowerCase())
      ),
    }))
    .filter((d) => d.files.length > 0);

  return (
    <aside
      className={`shrink-0 w-72 lg:w-80 min-w-[280px] max-w-[320px] bg-[#0d1117] border-r border-[#30363d] flex flex-col h-full select-none ${className}`}
    >
      {/* Project Switcher Bar */}
      <div className="p-3 border-b border-[#30363d] bg-[#161b22]">
        <div className="flex items-center justify-between gap-2 mb-2">
          <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
            <FolderTree className="w-3.5 h-3.5 text-purple-400" />
            <span>Repository Domain Map</span>
          </label>
          <div className="flex items-center gap-1">
            {currentProject && (
              <button
                onClick={() => {
                  if (confirm(`Remove project '${currentProject.name}' from CodeBridge?`)) {
                    deleteProject(currentProject.id);
                  }
                }}
                className="text-gray-500 hover:text-red-400 p-1 rounded transition-colors"
                title="Delete project"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-200 p-1 rounded transition-colors lg:hidden"
                title="Close Domain Explorer"
              >
                <ChevronRight className="w-3.5 h-3.5 rotate-180" />
              </button>
            )}
          </div>
        </div>

        {(() => {
          const uniqueProjects = projects.filter(
            (p, idx, arr) => arr.findIndex((item) => item.id === p.id || (item.name === p.name && item.source_type === p.source_type)) === idx
          );
          if (uniqueProjects.length <= 1) return null;
          return (
            <select
              value={currentProject?.id || ''}
              onChange={(e) => selectProject(e.target.value)}
              className="w-full px-2.5 py-1 text-xs rounded bg-[#0d1117] border border-[#30363d] text-gray-200 focus:outline-none focus:border-purple-500"
            >
              {uniqueProjects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.source_type})
                </option>
              ))}
            </select>
          );
        })()}

        {/* Filter Input */}
        <div className="relative mt-2">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-gray-500" />
          <input
            type="text"
            placeholder="Filter domains or files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1 text-xs rounded-md bg-[#0d1117] border border-[#30363d] text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500"
          />
        </div>

        {/* Background Translation Scanner Banner */}
        {currentProject && (
          <div className="mt-2.5 pt-2 border-t border-[#30363d]/60">
            {scanStatus?.is_scanning ? (
              <div className="p-2 rounded-md bg-purple-950/40 border border-purple-800/50 text-[11px] space-y-1.5">
                <div className="flex items-center justify-between text-purple-300 font-medium">
                  <span className="flex items-center gap-1.5">
                    <Loader2 className="w-3 h-3 animate-spin text-purple-400" />
                    <span>AI Pre-warming...</span>
                  </span>
                  <span className="font-mono text-[10px]">
                    {scanStatus.completed}/{scanStatus.total} ({scanStatus.total > 0 ? Math.round((scanStatus.completed / scanStatus.total) * 100) : 0}%)
                  </span>
                </div>
                <div className="w-full bg-[#21262d] rounded-full h-1 overflow-hidden">
                  <div
                    className="bg-purple-500 h-1 rounded-full transition-all duration-300"
                    style={{
                      width: `${scanStatus.total > 0 ? Math.min(100, Math.round((scanStatus.completed / scanStatus.total) * 100)) : 0}%`,
                    }}
                  />
                </div>
                {scanStatus.current_file && (
                  <div className="text-[10px] text-gray-400 truncate font-mono" title={scanStatus.current_file}>
                    {scanStatus.current_file}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-between text-[10px] px-1 text-gray-400">
                <span className="flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-emerald-400" />
                  <span>
                    {scanStatus ? `${scanStatus.completed}/${scanStatus.total} files explained` : 'AI Explanations'}
                  </span>
                </span>
                {scanStatus && scanStatus.completed < scanStatus.total && (
                  <button
                    onClick={() => startProjectScan(currentProject.id)}
                    className="text-purple-400 hover:text-purple-300 font-medium hover:underline flex items-center gap-0.5"
                    title="Translate all remaining files in background"
                  >
                    <span>Explain all</span>
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Domain Accordions */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredDomains.length === 0 ? (
          <div className="p-4 text-center text-xs text-gray-500">
            {currentProject ? 'No matching domains or files found.' : 'Ingest a repository to view domains.'}
          </div>
        ) : (
          filteredDomains.map((domain) => {
            const isCollapsed = collapsedDomains[domain.domain_name];
            return (
              <div key={domain.domain_name} className="rounded-md overflow-hidden bg-[#161b22]/40">
                {/* Domain Accordion Header */}
                <button
                  onClick={() => toggleDomain(domain.domain_name)}
                  className="w-full px-2.5 py-2 flex items-center justify-between text-left hover:bg-[#161b22] transition-colors border-b border-[#30363d]/30"
                >
                  <div className="flex items-center gap-1.5 min-w-0">
                    {isCollapsed ? (
                      <ChevronRight className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                    )}
                    <span className="text-xs font-semibold text-gray-200 truncate" title={domain.domain_name}>
                      {domain.domain_name}
                    </span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#30363d]/60 text-gray-400 font-mono">
                    {domain.files.length}
                  </span>
                </button>

                {/* File List */}
                {!isCollapsed && (
                  <div className="py-1 px-1 space-y-0.5">
                    {domain.description && (
                      <div className="px-2.5 py-1 text-[10px] text-gray-400 italic bg-[#0d1117]/60 rounded mb-1 border border-[#30363d]/20">
                        {domain.description}
                      </div>
                    )}
                    {domain.files.map((file) => {
                      const isSelected = currentFile?.id === file.id;
                      const summaryText = file.plain_summary || '';
                      const hasRealSummary =
                        Boolean(summaryText) &&
                        !summaryText.startsWith('Provides ') &&
                        !summaryText.includes('logic for the application');
                      const isExplained = Boolean(file.has_explanation || hasRealSummary);

                      return (
                        <button
                          key={file.id}
                          onClick={() => selectFile(file.id)}
                          className={`w-full px-2.5 py-1.5 rounded text-left flex flex-col gap-1 transition-all ${
                            isSelected
                              ? 'bg-purple-950/60 border border-purple-800/60 text-purple-200 font-medium'
                              : 'text-gray-400 hover:bg-[#21262d] hover:text-gray-200'
                          }`}
                          title={file.plain_summary || file.relative_path}
                        >
                          <div className="flex items-center justify-between gap-1.5 w-full">
                            <div className="flex items-center gap-1.5 min-w-0">
                              <span
                                className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                                  isExplained ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]' : 'bg-gray-600'
                                }`}
                                title={isExplained ? 'AI Explained' : 'Pending Translation'}
                              />
                              <span className={`truncate text-xs font-mono ${isExplained ? 'text-gray-200' : 'text-gray-400'}`}>
                                {file.relative_path}
                              </span>
                            </div>
                            <div className="flex items-center gap-1 shrink-0">
                              {isExplained && (
                                <span className="px-1 py-0.2 rounded text-[9px] bg-emerald-950/70 text-emerald-300 border border-emerald-800/50 flex items-center gap-0.5">
                                  <Sparkles className="w-2.5 h-2.5" />
                                  <span>Explained</span>
                                </span>
                              )}
                              {getFileBadge(file)}
                            </div>
                          </div>
                          {hasRealSummary && (
                            <span className="text-[10px] text-gray-400 line-clamp-1 w-full font-sans pl-3 opacity-80">
                              {file.plain_summary}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
