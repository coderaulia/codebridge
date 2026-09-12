import { useEffect, useState } from 'react';
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

export function App() {
  const { fetchProjects } = useProjectStore();
  const { loadSettings } = useSettingsStore();

  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);

  useEffect(() => {
    fetchProjects();
    loadSettings();

    // Check if user is on first-use visit
    const hasCompletedOnboarding = localStorage.getItem('codebridge_onboarding_completed');
    if (!hasCompletedOnboarding) {
      setIsOnboardingOpen(true);
    }
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0d1117] overflow-hidden text-gray-100 font-sans">
      {/* Studio Header */}
      <Header
        onOpenIngest={() => setIsIngestOpen(true)}
        onOpenExecutiveSummary={() => setIsSummaryOpen(true)}
        onOpenTour={() => setIsOnboardingOpen(true)}
      />

      {/* Backend Status Warning (appears if FastAPI server on port 8000 is down) */}
      <BackendStatusBanner />

      {/* 3-Column Architect Studio */}
      <main className="flex-1 flex overflow-hidden">
        {/* Column 1: Business Domain Explorer */}
        <DomainNavigator />

        {/* Column 2: Interactive Monaco Code & Schema Viewer */}
        <MonacoViewer />

        {/* Column 3: Plain-English Translation & Visual Journey */}
        <TranslationPanel />
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
