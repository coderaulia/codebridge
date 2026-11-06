import { create } from 'zustand';
import type { TranslationBreakdown } from '../types/translation';

type TranslationTab = 'all' | 'summary' | 'inputs' | 'outputs' | 'business' | 'diagram' | 'raw';

interface TranslationState {
  isTranslating: boolean;
  streamingText: string;
  translation: TranslationBreakdown | null;
  activeTab: TranslationTab;
  error: string | null;

  setActiveTab: (tab: TranslationTab) => void;
  clearTranslation: () => void;
  setFileOverview: (file: any) => void;
  translateSelection: (fileId: string, startLine: number, endLine: number, selectedCode: string, forceRefresh?: boolean) => Promise<void>;
}

export const useTranslationStore = create<TranslationState>((set) => ({
  isTranslating: false,
  streamingText: '',
  translation: null,
  activeTab: 'all',
  error: null,

  setActiveTab: (tab) => set({ activeTab: tab }),

  clearTranslation: () => set({ translation: null, streamingText: '', error: null }),

  setFileOverview: (file) => {
    if (!file) {
      set({ translation: null, streamingText: '', error: null });
      return;
    }
    const summaryText = file.plain_summary || '';
    const hasRealSummary =
      Boolean(summaryText) &&
      !summaryText.startsWith('Provides ') &&
      !summaryText.includes('logic for the application');
    const symbolsText =
      file.symbols && file.symbols.length > 0
        ? file.symbols.map((s: any) => `${s.symbol_type}: ${s.name}`).slice(0, 5).join(', ')
        : 'File components and operational definitions';

    set({
      streamingText: '',
      error: null,
      activeTab: 'all',
      translation: {
        plain_summary: hasRealSummary
          ? file.plain_summary
          : `Coordinates ${file.business_domain?.toLowerCase() || 'application'} capabilities in ${file.relative_path}. Highlight any section to translate line-by-line.`,
        inputs_and_parameters: `Components and exported symbols: ${symbolsText}`,
        outputs_and_effects: `Implements functional routines powering the '${file.business_domain || 'General'}' operational domain.`,
        business_rule_tie_in: `Core asset in the '${file.business_domain || 'General'}' business domain.`,
        mermaid_diagram: '',
        cached: Boolean(hasRealSummary),
      },
    });
  },

  translateSelection: async (fileId, startLine, endLine, selectedCode, forceRefresh = false) => {
    set({
      isTranslating: true,
      streamingText: '',
      translation: null,
      error: null,
      activeTab: 'all',
    });

    try {
      const response = await fetch('/api/translate/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_id: fileId,
          start_line: startLine,
          end_line: endLine,
          selected_code: selectedCode,
          force_refresh: forceRefresh,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Translation server error (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let pending = '';
      let flushScheduled = false;
      const flush = () => {
        flushScheduled = false;
        if (!pending) return;
        const text = pending;
        pending = '';
        set((state) => ({ streamingText: state.streamingText + text }));
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ')) continue;
          const dataStr = trimmed.slice(6);
          if (dataStr === '[DONE]') continue;

          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.event === 'chunk' && parsed.content) {
              pending += parsed.content;
              if (!flushScheduled) {
                flushScheduled = true;
                requestAnimationFrame(flush);
              }
            } else if (parsed.event === 'cached' && parsed.data) {
              set({
                translation: parsed.data,
                streamingText: '',
                isTranslating: false,
              });
            } else if (parsed.event === 'complete' && parsed.data) {
              set({
                translation: parsed.data,
                isTranslating: false,
              });
            } else if (parsed.error) {
              set({ error: parsed.error, isTranslating: false });
            }
          } catch {
            // Ignore malformed json chunks
          }
        }
      }

      flush();
      set({ isTranslating: false });
    } catch (err: any) {
      set({ error: err.message, isTranslating: false });
    }
  },
}));
