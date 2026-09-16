import { create } from 'zustand';
import axios from 'axios';
import type { Project, FileDetail, BusinessDomainGroup, ScanStatus } from '../types/project';
import { useTranslationStore } from './useTranslationStore';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  domains: BusinessDomainGroup[];
  totalFiles: number;
  totalSymbols: number;
  currentFile: FileDetail | null;
  selectedRange: { startLine: number; endLine: number; code: string } | null;
  macroDiagram: string | null;
  scanStatus: ScanStatus | null;
  isLoading: boolean;
  isBackendConnected: boolean;
  error: string | null;

  checkBackendHealth: () => Promise<boolean>;
  fetchProjects: () => Promise<void>;
  selectProject: (projectId: string) => Promise<void>;
  selectFile: (fileId: string) => Promise<void>;
  startProjectScan: (projectId: string) => Promise<void>;
  setSelectedRange: (range: { startLine: number; endLine: number; code: string } | null) => void;
  deleteProject: (projectId: string) => Promise<void>;
  ingestLocal: (directoryPath: string, name?: string) => Promise<string>;
  ingestGithub: (repoUrl: string, token?: string) => Promise<string>;
  generateSummaries: (projectId: string) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  domains: [],
  totalFiles: 0,
  totalSymbols: 0,
  currentFile: null,
  selectedRange: null,
  macroDiagram: null,
  scanStatus: null,
  isLoading: false,
  isBackendConnected: true,
  error: null,

  checkBackendHealth: async () => {
    try {
      const res = await axios.get('/api/health');
      if (res.data?.status === 'ok') {
        set({ isBackendConnected: true, error: null });
        await get().fetchProjects();
        return true;
      }
    } catch {
      set({ isBackendConnected: false });
    }
    return false;
  },

  fetchProjects: async () => {
    try {
      set({ isLoading: true, error: null });
      const res = await axios.get<Project[]>('/api/projects');
      set({ projects: res.data, isLoading: false, isBackendConnected: true });
      // If there are projects and none currently selected, auto-select the first one
      if (res.data.length > 0 && !get().currentProject) {
        await get().selectProject(res.data[0].id);
      }
    } catch (err: any) {
      const isConnectionError =
        err.code === 'ERR_NETWORK' ||
        err.response?.status === 502 ||
        err.message?.includes('Network Error') ||
        err.message?.includes('ECONNREFUSED');
      set({
        error: err.message,
        isLoading: false,
        isBackendConnected: isConnectionError ? false : get().isBackendConnected,
      });
    }
  },

  selectProject: async (projectId: string) => {
    try {
      set({ isLoading: true, error: null });
      const res = await axios.get(`/api/projects/${projectId}`);
      set({
        currentProject: res.data.project,
        domains: res.data.domains,
        totalFiles: res.data.total_files,
        totalSymbols: res.data.total_symbols,
        macroDiagram: res.data.macro_diagram || null,
        currentFile: null,
        selectedRange: null,
        isLoading: false,
      });

      // Auto-select first file if available
      if (res.data.domains.length > 0 && res.data.domains[0].files.length > 0) {
        await get().selectFile(res.data.domains[0].files[0].id);
      }

      // Automatically launch background translation pre-warmer/scanner on project open
      get().startProjectScan(projectId);
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  selectFile: async (fileId: string) => {
    try {
      const res = await axios.get<FileDetail>(`/api/files/${fileId}`);
      set({ currentFile: res.data, selectedRange: null });
      // Update translation column immediately with the picked file's overview & summary!
      useTranslationStore.getState().setFileOverview(res.data);
    } catch (err: any) {
      set({ error: err.message });
    }
  },

  startProjectScan: async (projectId: string) => {
    try {
      const res = await axios.post<ScanStatus>(`/api/projects/${projectId}/scan-translations`);
      set({ scanStatus: res.data });

      if (res.data.is_scanning) {
        let tick = 0;
        const interval = setInterval(async () => {
          try {
            tick++;
            const statusRes = await axios.get<ScanStatus>(`/api/projects/${projectId}/scan-status`);
            set({ scanStatus: statusRes.data });

            // Periodically refresh domain files to reflect newly explained files live
            if (tick % 2 === 0 || !statusRes.data.is_scanning) {
              const projRes = await axios.get(`/api/projects/${projectId}`);
              set({
                domains: projRes.data.domains,
                currentProject: projRes.data.project,
                macroDiagram: projRes.data.macro_diagram || null,
              });
            }

            if (!statusRes.data.is_scanning) {
              clearInterval(interval);
            }
          } catch {
            clearInterval(interval);
          }
        }, 2500);
      }
    } catch {
      // Non-fatal if scan trigger fails
    }
  },

  setSelectedRange: (range) => {
    set({ selectedRange: range });
  },

  deleteProject: async (projectId: string) => {
    try {
      await axios.delete(`/api/projects/${projectId}`);
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== projectId),
        currentProject: state.currentProject?.id === projectId ? null : state.currentProject,
        currentFile: state.currentProject?.id === projectId ? null : state.currentFile,
      }));
      if (get().projects.length > 0) {
        await get().selectProject(get().projects[0].id);
      }
    } catch (err: any) {
      set({ error: err.message });
    }
  },

  ingestLocal: async (directoryPath: string, name?: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await axios.post('/api/projects/local', {
        directory_path: directoryPath,
        project_name: name || '',
      });
      await get().fetchProjects();
      await get().selectProject(res.data.project_id);
      set({ isLoading: false });
      return res.data.project_id;
    } catch (err: any) {
      set({ error: err.response?.data?.detail || err.message, isLoading: false });
      throw err;
    }
  },

  ingestGithub: async (repoUrl: string, token?: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await axios.post('/api/projects/github', {
        repo_url: repoUrl,
        github_token: token || '',
      });
      await get().fetchProjects();
      await get().selectProject(res.data.project_id);
      set({ isLoading: false });
      return res.data.project_id;
    } catch (err: any) {
      set({ error: err.response?.data?.detail || err.message, isLoading: false });
      throw err;
    }
  },

  generateSummaries: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      await axios.post(`/api/projects/${projectId}/generate-summaries`);
      await get().selectProject(projectId);
      set({ isLoading: false });
    } catch (err: any) {
      set({ error: err.response?.data?.detail || err.message, isLoading: false });
    }
  },
}));
