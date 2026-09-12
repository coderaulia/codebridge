import { Network, Settings, Plus, Layers } from 'lucide-react';
import { useSettingsStore } from '../../stores/useSettingsStore';
import { useProjectStore } from '../../stores/useProjectStore';

interface HeaderProps {
  onOpenIngest: () => void;
  onOpenExecutiveSummary: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenIngest, onOpenExecutiveSummary }) => {
  const { settings, setSettingsOpen } = useSettingsStore();
  const { currentProject, totalFiles, totalSymbols } = useProjectStore();

  return (
    <header className="h-14 bg-[#161b22] border-b border-[#30363d] px-4 flex items-center justify-between select-none">
      {/* Left: Brand & Active Project */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-md">
          <Network className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-gray-100 tracking-tight text-sm">CodeBridge</span>
            <span className="text-[11px] text-gray-400 hidden sm:inline">Local Codebase Analyzer</span>
            <span className="text-[10px] font-medium text-purple-300 bg-purple-950/60 px-1.5 py-0.5 rounded border border-purple-800/50">
              by Vanaila
            </span>
          </div>
          <div className="text-xs text-gray-400 truncate max-w-[280px]">
            {currentProject ? (
              <span className="flex items-center gap-1.5">
                <span className="font-medium text-gray-300">{currentProject.name}</span>
                <span className="text-gray-500">•</span>
                <span>{totalFiles} files</span>
                <span className="text-gray-500">•</span>
                <span>{totalSymbols} symbols</span>
              </span>
            ) : (
              'No repository loaded'
            )}
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {currentProject && (
          <button
            onClick={onOpenExecutiveSummary}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-[#21262d] hover:bg-[#30363d] text-gray-200 border border-[#30363d] transition-colors"
            title="Read Project Executive Briefing"
          >
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span>Executive Briefing</span>
          </button>
        )}

        <button
          onClick={onOpenIngest}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-purple-600 hover:bg-purple-500 text-white shadow transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Ingest Repository</span>
        </button>

        <button
          onClick={() => setSettingsOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 text-xs rounded-md bg-[#21262d] hover:bg-[#30363d] text-gray-300 border border-[#30363d] transition-colors"
          title="Configure AI Provider & Model"
        >
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="capitalize font-medium">{settings.provider_type}</span>
            <span className="text-gray-500 text-[11px]">({settings.model_name})</span>
          </div>
          <Settings className="w-3.5 h-3.5 text-gray-400" />
        </button>
      </div>
    </header>
  );
};
