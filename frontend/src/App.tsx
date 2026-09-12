import { useEffect, useState } from 'react';
import { Header } from './components/layout/Header';
import { DomainNavigator } from './components/explorer/DomainNavigator';
import { MonacoViewer } from './components/editor/MonacoViewer';
import { TranslationPanel } from './components/translation/TranslationPanel';
import { IngestModal } from './components/layout/IngestModal';
import { SettingsModal } from './components/layout/SettingsModal';
import { ProjectSummaryModal } from './components/explorer/ProjectSummaryModal';
import { useProjectStore } from './stores/useProjectStore';
import { useSettingsStore } from './stores/useSettingsStore';

export function App() {
  const { fetchProjects } = useProjectStore();
  const { loadSettings } = useSettingsStore();

  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);

  useEffect(() => {
    fetchProjects();
    loadSettings();
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0d1117] overflow-hidden text-gray-100 font-sans">
      {/* Header */}
      <Header
        onOpenIngest={() => setIsIngestOpen(true)}
        onOpenExecutiveSummary={() => setIsSummaryOpen(true)}
      />

      {/* 3-Column Architect Studio */}
      <main className="flex-1 flex overflow-hidden">
        {/* Column 1: Business Domain Explorer */}
        <DomainNavigator />

        {/* Column 2: Interactive Monaco Code & Schema Viewer */}
        <MonacoViewer />

        {/* Column 3: Plain-English Translation & Visual Journey */}
        <TranslationPanel />
      </main>

      {/* Modals */}
      <IngestModal isOpen={isIngestOpen} onClose={() => setIsIngestOpen(false)} />
      <SettingsModal />
      <ProjectSummaryModal isOpen={isSummaryOpen} onClose={() => setIsSummaryOpen(false)} />
    </div>
  );
}

export default App;
