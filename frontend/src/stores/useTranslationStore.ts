import { create } from 'zustand';
import type { TranslationBreakdown } from '../types/translation';

type TranslationTab = 'summary' | 'inputs' | 'outputs' | 'business' | 'diagram' | 'raw';

interface TranslationState {
  isTranslating: boolean;
  streamingText: string;
  translation: TranslationBreakdown | null;
  activeTab: TranslationTab;
  error: string | null;

  setActiveTab: (tab: TranslationTab) => void;
  clearTranslation: () => void;
  translateSelection: (fileId: string, startLine: number, endLine: number, selectedCode: string) => Promise<void>;
}

export const useTranslationStore = create<TranslationState>((set) => ({
  isTranslating: false,
  streamingText: '',
  translation: null,
  activeTab: 'summary',
  error: null,

  setActiveTab: (tab) => set({ activeTab: tab }),

  clearTranslation: () => set({ translation: null, streamingText: '', error: null }),

  translateSelection: async (fileId, startLine, endLine, selectedCode) => {
    set({
      isTranslating: true,
      streamingText: '',
      translation: null,
      error: null,
      activeTab: 'summary',
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
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Translation server error (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

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
              set((state) => ({ streamingText: state.streamingText + parsed.content }));
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

      set({ isTranslating: false });
    } catch (err: any) {
      set({ error: err.message, isTranslating: false });
    }
  },
}));
