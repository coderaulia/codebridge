import { Network, Settings, Plus, Layers, HelpCircle, PanelLeft } from 'lucide-react';
import { useSettingsStore } from '../../stores/useSettingsStore';
import { useProjectStore } from '../../stores/useProjectStore';

interface HeaderProps {
  onOpenIngest: () => void;
  onOpenExecutiveSummary: () => void;
  onOpenTour: () => void;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenIngest,
  onOpenExecutiveSummary,
  onOpenTour,
  isSidebarOpen,
  onToggleSidebar,
}) => {
  const { settings, setSettingsOpen } = useSettingsStore();
  const { currentProject, totalFiles } = useProjectStore();

  return (
    <header className="h-14 bg-[#161b22] border-b border-[#30363d] px-3 sm:px-4 flex items-center justify-between select-none gap-2">
      {/* Left: Sidebar Toggle & Brand */}
      <div className="flex items-center gap-2 sm:gap-3 min-w-0">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className={`p-1.5 rounded-md border transition-colors ${
              isSidebarOpen
                ? 'bg-purple-950/50 border-purple-600/50 text-purple-300'
                : 'bg-[#21262d] border-[#30363d] text-gray-400 hover:text-gray-200'
            }`}
            title="Toggle Business Domain Explorer"
          >
            <PanelLeft className="w-4 h-4" />
          </button>
        )}

        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-md shrink-0">
          <Network className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 sm:gap-2">
            <span className="font-bold text-gray-100 tracking-tight text-xs sm:text-sm">CodeBridge</span>
            <span className="text-[10px] text-gray-400 hidden md:inline">Local Codebase Analyzer</span>
            <span className="text-[9px] sm:text-[10px] font-medium text-purple-300 bg-purple-950/60 px-1.5 py-0.5 rounded border border-purple-800/50">
              by Vanaila
            </span>
          </div>
          <div className="text-[11px] text-gray-400 truncate max-w-[180px] sm:max-w-[280px]">
            {currentProject ? (
              <span className="flex items-center gap-1.5">
                <span className="font-medium text-gray-300">{currentProject.name}</span>
                <span className="text-gray-500 hidden sm:inline">•</span>
                <span className="hidden sm:inline">{totalFiles} files</span>
              </span>
            ) : (
              'No repository loaded'
            )}
          </div>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
        <button
          onClick={onOpenTour}
          className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-[#21262d] hover:bg-[#30363d] text-gray-300 border border-[#30363d] transition-colors"
          title="Open Onboarding Guide & Tour"
        >
          <HelpCircle className="w-3.5 h-3.5 text-purple-400" />
          <span className="hidden sm:inline">Tour</span>
        </button>

        {currentProject && (
          <button
            onClick={onOpenExecutiveSummary}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md bg-[#21262d] hover:bg-[#30363d] text-gray-200 border border-[#30363d] transition-colors"
            title="Read Project Executive Briefing"
          >
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span className="hidden md:inline">Briefing</span>
          </button>
        )}

        <button
          onClick={onOpenIngest}
          className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs font-medium rounded-md bg-purple-600 hover:bg-purple-500 text-white shadow transition-colors"
          title="Ingest local or remote repository"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Ingest<span className="hidden sm:inline"> Repo</span></span>
        </button>

        <button
          onClick={() => setSettingsOpen(true)}
          className="flex items-center gap-1.5 px-2 sm:px-3 py-1.5 text-xs rounded-md bg-[#21262d] hover:bg-[#30363d] text-gray-300 border border-[#30363d] transition-colors"
          title="Configure AI Provider & Model"
        >
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="capitalize font-medium hidden sm:inline">{settings.provider_type}</span>
          </div>
          <Settings className="w-3.5 h-3.5 text-gray-400" />
        </button>
      </div>
    </header>
  );
};
