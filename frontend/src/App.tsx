import { useShallow } from 'zustand/react/shallow';
import { useEffect, useState, useRef, lazy, Suspense } from 'react';
import { Header } from './components/layout/Header';
import { BackendStatusBanner } from './components/layout/BackendStatusBanner';
import { DomainNavigator } from './components/explorer/DomainNavigator';
import { TranslationPanel } from './components/translation/TranslationPanel';
import { useProjectStore } from './stores/useProjectStore';
import { useSettingsStore } from './stores/useSettingsStore';
import { Code2, Sparkles } from 'lucide-react';

const IngestModal = lazy(() => import('./components/layout/IngestModal').then((m) => ({ default: m.IngestModal })));
const SettingsModal = lazy(() => import('./components/layout/SettingsModal').then((m) => ({ default: m.SettingsModal })));
const ProjectSummaryModal = lazy(() => import('./components/explorer/ProjectSummaryModal').then((m) => ({ default: m.ProjectSummaryModal })));
const OnboardingWizard = lazy(() => import('./components/onboarding/OnboardingWizard').then((m) => ({ default: m.OnboardingWizard })));
const DiffTranslatorModal = lazy(() => import('./components/diff/DiffTranslatorModal').then((m) => ({ default: m.DiffTranslatorModal })));
const ExportBriefingModal = lazy(() => import('./components/export/ExportBriefingModal').then((m) => ({ default: m.ExportBriefingModal })));
const MonacoViewer = lazy(() => import('./components/editor/MonacoViewer').then((m) => ({ default: m.MonacoViewer })));

export function App() {
  const { fetchProjects } = useProjectStore(useShallow((s) => ({ fetchProjects: s.fetchProjects })));
  const { loadSettings } = useSettingsStore(useShallow((s) => ({ loadSettings: s.loadSettings })));

  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isDiffOpen, setIsDiffOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

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
  const translationWidthRef = useRef(0);

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
      translationWidthRef.current = clamped;
      setTranslationWidth(clamped);
    };

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        setIsDragging(false);
        isDraggingRef.current = false;
        try {
          if (translationWidthRef.current > 0) localStorage.setItem('codebridge_translation_width', translationWidthRef.current.toString());
        } catch { /* ignore */ }
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
        onOpenDiff={() => setIsDiffOpen(true)}
        onOpenExport={() => setIsExportOpen(true)}
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
          <Suspense fallback={<div className="p-6 text-xs text-gray-500">Loading editor…</div>}>
            <MonacoViewer />
          </Suspense>
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
      <Suspense fallback={null}>
      <IngestModal isOpen={isIngestOpen} onClose={() => setIsIngestOpen(false)} />
      <SettingsModal />
      <ProjectSummaryModal isOpen={isSummaryOpen} onClose={() => setIsSummaryOpen(false)} />
      <OnboardingWizard isOpen={isOnboardingOpen} onClose={() => setIsOnboardingOpen(false)} />
      <DiffTranslatorModal isOpen={isDiffOpen} onClose={() => setIsDiffOpen(false)} />
      <ExportBriefingModal isOpen={isExportOpen} onClose={() => setIsExportOpen(false)} />
      </Suspense>
    </div>
  );
}

export default App;
