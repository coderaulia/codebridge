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
    selectProject,
    selectFile,
    deleteProject,
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
                    {domain.files.map((file) => {
                      const isSelected = currentFile?.id === file.id;
                      return (
                        <button
                          key={file.id}
                          onClick={() => selectFile(file.id)}
                          className={`w-full px-2.5 py-1.5 rounded text-left flex items-center justify-between gap-2 transition-all ${
                            isSelected
                              ? 'bg-purple-950/60 border border-purple-800/60 text-purple-200 font-medium'
                              : 'text-gray-400 hover:bg-[#21262d] hover:text-gray-200'
                          }`}
                          title={file.plain_summary || file.relative_path}
                        >
                          <div className="truncate text-xs flex-1">{file.relative_path}</div>
                          {getFileBadge(file)}
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
