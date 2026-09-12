import React, { useState, useEffect } from 'react';
import {
  X,
  Folder,
  FolderUp,
  ChevronRight,
  Check,
  Loader2,
  HardDrive,
  Compass,
} from 'lucide-react';
import axios from 'axios';

interface FolderItem {
  name: string;
  path: string;
}

interface QuickLocation {
  name: string;
  path: string;
}

interface BrowseDirectoryResponse {
  current_path: string;
  parent_path: string | null;
  folders: FolderItem[];
  quick_locations: QuickLocation[];
}

interface FolderBrowserDialogProps {
  isOpen: boolean;
  initialPath?: string;
  onSelect: (selectedPath: string) => void;
  onClose: () => void;
}

export const FolderBrowserDialog: React.FC<FolderBrowserDialogProps> = ({
  isOpen,
  initialPath,
  onSelect,
  onClose,
}) => {
  const [currentPath, setCurrentPath] = useState<string>('');
  const [parentPath, setParentPath] = useState<string | null>(null);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [quickLocations, setQuickLocations] = useState<QuickLocation[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDirectory = async (path?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get<BrowseDirectoryResponse>('/api/system/browse-directories', {
        params: path ? { path } : {},
      });
      setCurrentPath(res.data.current_path);
      setParentPath(res.data.parent_path);
      setFolders(res.data.folders);
      setQuickLocations(res.data.quick_locations);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to read directory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDirectory(initialPath || undefined);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const pathParts = currentPath.split('/').filter(Boolean);

  const handleBreadcrumbClick = (index: number) => {
    const target = '/' + pathParts.slice(0, index + 1).join('/');
    fetchDirectory(target);
  };

  return (
    <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/80 backdrop-blur-xs p-4 select-none">
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
        {/* Modal Header */}
        <div className="px-5 py-3.5 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-gray-100">Folder Opener — Select Codebase</h3>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 p-1 rounded-md">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Quick Locations Bar */}
        {quickLocations.length > 0 && (
          <div className="px-5 py-2.5 bg-[#0d1117] border-b border-[#30363d] flex items-center gap-1.5 overflow-x-auto text-[11px]">
            <span className="text-gray-500 font-medium mr-1 flex items-center gap-1">
              <HardDrive className="w-3 h-3" /> Quick:
            </span>
            {quickLocations.map((loc) => (
              <button
                key={loc.name}
                type="button"
                onClick={() => fetchDirectory(loc.path)}
                className={`px-2.5 py-1 rounded-md border transition-colors whitespace-nowrap ${
                  currentPath === loc.path
                    ? 'bg-purple-950/60 border-purple-600 text-purple-200'
                    : 'bg-[#21262d] border-[#30363d] text-gray-300 hover:bg-[#30363d]'
                }`}
              >
                {loc.name}
              </button>
            ))}
          </div>
        )}

        {/* Breadcrumbs & Navigation */}
        <div className="px-5 py-2.5 bg-[#161b22] border-b border-[#30363d] flex items-center gap-2 text-xs">
          {parentPath ? (
            <button
              onClick={() => fetchDirectory(parentPath)}
              className="p-1 rounded bg-[#21262d] hover:bg-[#30363d] text-gray-300 transition-colors shrink-0"
              title="Go to parent directory"
            >
              <FolderUp className="w-4 h-4 text-purple-400" />
            </button>
          ) : (
            <div className="w-6 shrink-0" />
          )}

          <div className="flex-1 flex items-center gap-1 overflow-x-auto text-gray-300 font-mono text-[11px]">
            <button
              onClick={() => fetchDirectory('/')}
              className="hover:text-purple-300 text-gray-500 transition-colors"
            >
              /
            </button>
            {pathParts.map((part, idx) => (
              <React.Fragment key={idx}>
                <ChevronRight className="w-3 h-3 text-gray-600 shrink-0" />
                <button
                  onClick={() => handleBreadcrumbClick(idx)}
                  className={`hover:text-purple-300 transition-colors truncate max-w-[120px] ${
                    idx === pathParts.length - 1 ? 'font-bold text-gray-100' : 'text-gray-400'
                  }`}
                >
                  {part}
                </button>
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Directory Listing Body */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1 min-h-[260px] bg-[#0d1117]">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center text-xs text-gray-400 py-12">
              <Loader2 className="w-6 h-6 animate-spin text-purple-400 mb-2" />
              <span>Scanning directories...</span>
            </div>
          ) : error ? (
            <div className="p-4 rounded bg-red-950/30 border border-red-800/50 text-red-300 text-xs text-center">
              {error}
            </div>
          ) : folders.length === 0 ? (
            <div className="text-center py-12 text-xs text-gray-500">
              No subdirectories found in this folder.
            </div>
          ) : (
            folders.map((folder) => (
              <div
                key={folder.path}
                onDoubleClick={() => fetchDirectory(folder.path)}
                className="group px-3 py-2 rounded-lg flex items-center justify-between hover:bg-[#161b22] border border-transparent hover:border-[#30363d] cursor-pointer transition-all"
              >
                <div
                  onClick={() => fetchDirectory(folder.path)}
                  className="flex items-center gap-2.5 flex-1 min-w-0"
                >
                  <Folder className="w-4 h-4 text-purple-400 shrink-0 group-hover:text-purple-300" />
                  <span className="text-xs font-medium text-gray-200 truncate">{folder.name}</span>
                </div>

                <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelect(folder.path);
                      onClose();
                    }}
                    className="px-2 py-1 text-[11px] font-medium rounded bg-purple-600 hover:bg-purple-500 text-white shadow-xs"
                  >
                    Select
                  </button>
                  <button
                    type="button"
                    onClick={() => fetchDirectory(folder.path)}
                    className="px-2 py-1 text-[11px] rounded bg-[#21262d] hover:bg-[#30363d] text-gray-300"
                  >
                    Open
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-[#30363d] flex items-center justify-between bg-[#161b22]">
          <div className="text-[11px] text-gray-400 truncate max-w-[340px]">
            Selected: <span className="font-mono text-purple-300">{currentPath}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => {
                onSelect(currentPath);
                onClose();
              }}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-md bg-purple-600 hover:bg-purple-500 text-white shadow transition-colors"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Select Current Folder</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
