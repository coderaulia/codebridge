import React, { useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import type { OnMount } from '@monaco-editor/react';
import { Sparkles, Code2, Tag, ArrowRight } from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';
import { useTranslationStore } from '../../stores/useTranslationStore';

export const MonacoViewer: React.FC = () => {
  const { currentFile, setSelectedRange } = useProjectStore();
  const { translateSelection, isTranslating } = useTranslationStore();
  const editorRef = useRef<any>(null);

  const [activeSelection, setActiveSelection] = useState<{
    startLine: number;
    endLine: number;
    code: string;
  } | null>(null);

  const handleEditorDidMount: OnMount = (editor) => {
    editorRef.current = editor;

    // Listen for text selections
    editor.onDidChangeCursorSelection(() => {
      const selection = editor.getSelection();
      if (!selection || selection.isEmpty()) {
        setActiveSelection(null);
        return;
      }

      const model = editor.getModel();
      if (!model) return;

      const selectedText = model.getValueInRange(selection);
      if (selectedText.trim().length > 0) {
        const range = {
          startLine: selection.startLineNumber,
          endLine: selection.endLineNumber,
          code: selectedText,
        };
        setActiveSelection(range);
        setSelectedRange(range);
      } else {
        setActiveSelection(null);
      }
    });
  };

  const handleSymbolSelect = (startLine: number, endLine: number) => {
    if (!editorRef.current || !currentFile) return;

    editorRef.current.revealLineInCenter(startLine);
    editorRef.current.setSelection({
      startLineNumber: startLine,
      startColumn: 1,
      endLineNumber: endLine,
      endColumn: 1000,
    });

    const lines = currentFile.content.split('\n');
    const selectedSnippet = lines.slice(startLine - 1, endLine).join('\n');
    const range = { startLine, endLine, code: selectedSnippet };
    setActiveSelection(range);
    setSelectedRange(range);
  };

  const triggerTranslation = () => {
    if (!currentFile || !activeSelection) return;
    translateSelection(
      currentFile.id,
      activeSelection.startLine,
      activeSelection.endLine,
      activeSelection.code
    );
  };

  if (!currentFile) {
    return (
      <div className="flex-1 bg-[#0d1117] flex flex-col items-center justify-center text-center p-8 select-none">
        <Code2 className="w-12 h-12 text-gray-600 mb-3" />
        <h3 className="text-sm font-semibold text-gray-300">Select a file to inspect</h3>
        <p className="text-xs text-gray-500 mt-1 max-w-sm">
          Browse through the business domains on the left and select any source code or database schema.
        </p>
      </div>
    );
  }

  const getMonacoLanguage = () => {
    if (!currentFile) return 'plaintext';
    if (currentFile.language === 'prisma') return 'graphql';
    if (currentFile.language === 'openapi') {
      return currentFile.relative_path.endsWith('.yaml') || currentFile.relative_path.endsWith('.yml')
        ? 'yaml'
        : 'json';
    }
    return currentFile.language;
  };

  return (
    <div className="flex-1 min-w-0 bg-[#0d1117] flex flex-col h-full relative overflow-hidden">
      {/* File Header / Toolbar */}
      <div className="h-10 bg-[#161b22] border-b border-[#30363d] px-4 flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 truncate">
          <span className="font-mono text-gray-200">{currentFile.relative_path}</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/50 flex items-center gap-1 font-sans">
            <Tag className="w-2.5 h-2.5" />
            {currentFile.business_domain}
          </span>
        </div>

        {/* Symbol Jump Dropdown */}
        {currentFile.symbols.length > 0 && (
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="text-[11px] text-gray-500">Jump to symbol:</span>
            <select
              onChange={(e) => {
                const sym = currentFile.symbols.find((s) => s.id === e.target.value);
                if (sym) handleSymbolSelect(sym.start_line, sym.end_line);
              }}
              defaultValue=""
              className="bg-[#0d1117] border border-[#30363d] text-gray-300 rounded px-2 py-0.5 text-xs focus:outline-none focus:border-purple-500"
            >
              <option value="" disabled>
                {currentFile.symbols.length} symbols extracted...
              </option>
              {currentFile.symbols.map((sym) => (
                <option key={sym.id} value={sym.id}>
                  [{sym.symbol_type}] {sym.name} (L{sym.start_line}-{sym.end_line})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 relative">
        <Editor
          height="100%"
          language={getMonacoLanguage()}
          value={currentFile.content}
          theme="vs-dark"
          options={{
            readOnly: true,
            fontSize: 12.5,
            lineHeight: 20,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            smoothScrolling: true,
            renderLineHighlight: 'all',
            padding: { top: 8, bottom: 8 },
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
          }}
          onMount={handleEditorDidMount}
        />

        {/* Floating Selection Toolbar */}
        {activeSelection && (
          <div className="absolute bottom-6 right-6 z-20 animate-fade-in shadow-2xl">
            <button
              onClick={triggerTranslation}
              disabled={isTranslating}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg transition-all transform hover:scale-[1.02] active:scale-[0.98] border border-white/20"
            >
              <Sparkles className="w-4 h-4 text-amber-300 animate-pulse" />
              <span>
                Translate in Plain English (Lines {activeSelection.startLine}–{activeSelection.endLine})
              </span>
              <ArrowRight className="w-3.5 h-3.5 opacity-80" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
