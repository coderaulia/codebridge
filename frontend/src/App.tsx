import { useEffect, useState, useRef } from 'react';
import { Header } from './components/layout/Header';
import { BackendStatusBanner } from './components/layout/BackendStatusBanner';
import { DomainNavigator } from './components/explorer/DomainNavigator';
import { MonacoViewer } from './components/editor/MonacoViewer';
import { TranslationPanel } from './components/translation/TranslationPanel';
import { IngestModal } from './components/layout/IngestModal';
import { SettingsModal } from './components/layout/SettingsModal';
import { ProjectSummaryModal } from './components/explorer/ProjectSummaryModal';
import { OnboardingWizard } from './components/onboarding/OnboardingWizard';
import { useProjectStore } from './stores/useProjectStore';
import { useSettingsStore } from './stores/useSettingsStore';
import { Code2, Sparkles } from 'lucide-react';

export function App() {
  const { fetchProjects } = useProjectStore();
  const { loadSettings } = useSettingsStore();

  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);

  // Column 1 fixed sidebar visibility
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(() => {
    return typeof window !== 'undefined' ? window.innerWidth >= 1024 : true;
  });

  // Column 2 & 3 Resizability
  const [translationWidth, setTranslationWidth] = useState<number>(() => {
    const saved = localStorage.getItem('codebridge_translation_width');
    return saved ? parseInt(saved, 10) : 420;
  });
  const [isDragging, setIsDragging] = useState(false);
  const isDraggingRef = useRef(false);

  // Mobile mode tab switch (for screens < 768px)
  const [mobileTab, setMobileTab] = useState<'editor' | 'translation'>('editor');

  useEffect(() => {
    fetchProjects();
    loadSettings();

    // Check if user is on first-use visit
    const hasCompletedOnboarding = localStorage.getItem('codebridge_onboarding_completed');
    if (!hasCompletedOnboarding) {
      setIsOnboardingOpen(true);
    }

    // Auto-collapse sidebar on smaller viewports on resize
    const handleResize = () => {
      if (window.innerWidth < 1024 && isSidebarOpen) {
        setIsSidebarOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Splitter Drag Handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    isDraggingRef.current = true;
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const newWidth = window.innerWidth - e.clientX;
      // Clamp width between 300px and window width minus room for sidebar & editor
      const minWidth = 280;
      const maxWidth = Math.max(minWidth, window.innerWidth - (isSidebarOpen ? 340 : 100) - 260);
      const clamped = Math.max(minWidth, Math.min(newWidth, maxWidth));
      setTranslationWidth(clamped);
      localStorage.setItem('codebridge_translation_width', clamped.toString());
    };

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        setIsDragging(false);
        isDraggingRef.current = false;
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isSidebarOpen]);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0d1117] overflow-hidden text-gray-100 font-sans">
      {/* Studio Header */}
      <Header
        onOpenIngest={() => setIsIngestOpen(true)}
        onOpenExecutiveSummary={() => setIsSummaryOpen(true)}
        onOpenTour={() => setIsOnboardingOpen(true)}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
      />

      {/* Backend Status Warning */}
      <BackendStatusBanner />

      {/* Mobile Tab Switcher (Visible only on viewports < 768px) */}
      <div className="md:hidden flex border-b border-[#30363d] bg-[#161b22] text-xs">
        <button
          onClick={() => setMobileTab('editor')}
          className={`flex-1 py-2 flex items-center justify-center gap-1.5 border-b-2 font-medium ${
            mobileTab === 'editor'
              ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
              : 'border-transparent text-gray-400'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Code & Schema</span>
        </button>
        <button
          onClick={() => setMobileTab('translation')}
          className={`flex-1 py-2 flex items-center justify-center gap-1.5 border-b-2 font-medium ${
            mobileTab === 'translation'
              ? 'border-purple-500 text-purple-300 bg-[#0d1117]'
              : 'border-transparent text-gray-400'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>Translation & Diagrams</span>
        </button>
      </div>

      {/* 3-Column Studio Layout */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Column 1: Fixed Size Domain Explorer (Desktop: Inline, Mobile/Tablet: Drawer) */}
        {isSidebarOpen && (
          <>
            {/* Mobile / Tablet Backdrop */}
            <div
              onClick={() => setIsSidebarOpen(false)}
              className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-xs transition-opacity"
            />
            {/* Sidebar Container */}
            <div className="lg:static fixed inset-y-0 left-0 z-40 lg:z-auto shadow-2xl lg:shadow-none animate-slide-in">
              <DomainNavigator onClose={() => setIsSidebarOpen(false)} />
            </div>
          </>
        )}

        {/* Column 2: Interactive Monaco Code & Schema Viewer (Takes remaining flex space) */}
        <div className={`flex-1 min-w-0 h-full flex flex-col ${mobileTab === 'translation' ? 'hidden md:flex' : 'flex'}`}>
          <MonacoViewer />
        </div>

        {/* Resizable Splitter Handle between Column 2 and Column 3 (Desktop/Tablet) */}
        <div
          onMouseDown={handleMouseDown}
          className={`hidden md:flex w-2 -ml-1 z-30 cursor-col-resize relative group items-center justify-center transition-colors ${
            isDragging ? 'bg-purple-600' : 'hover:bg-purple-600/70 bg-[#30363d]/40'
          }`}
          title="Drag to resize Editor and Translation panels"
        >
          <div className="h-8 w-1 rounded-full bg-gray-500 group-hover:bg-purple-200 transition-colors" />
        </div>

        {/* Column 3: Plain-English Translation & Visual Journey (Resizable width on desktop) */}
        <div
          className={`h-full ${
            mobileTab === 'editor' ? 'hidden md:flex' : 'flex w-full md:w-auto'
          }`}
        >
          <TranslationPanel width={window.innerWidth >= 768 ? translationWidth : undefined} />
        </div>

        {/* Transparent Drag Overlay to prevent iframe / Monaco event capturing while dragging */}
        {isDragging && <div className="fixed inset-0 z-50 cursor-col-resize select-none" />}
      </main>

      {/* Modals & Dialogs */}
      <IngestModal isOpen={isIngestOpen} onClose={() => setIsIngestOpen(false)} />
      <SettingsModal />
      <ProjectSummaryModal isOpen={isSummaryOpen} onClose={() => setIsSummaryOpen(false)} />
      <OnboardingWizard isOpen={isOnboardingOpen} onClose={() => setIsOnboardingOpen(false)} />
    </div>
  );
}

export default App;
