import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { ZoomIn, ZoomOut, RotateCcw, AlertCircle } from 'lucide-react';

interface MermaidViewerProps {
  chart: string;
}

export const MermaidViewer: React.FC<MermaidViewerProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [renderError, setRenderError] = useState<string | null>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      themeVariables: {
        darkMode: true,
        background: '#0d1117',
        primaryColor: '#8b5cf6',
        primaryTextColor: '#f3f4f6',
        primaryBorderColor: '#6d28d9',
        lineColor: '#9ca3af',
        secondaryColor: '#1e293b',
        tertiaryColor: '#0f172a',
      },
    });
  }, []);

  useEffect(() => {
    if (!chart || !chart.trim()) {
      setSvgContent('');
      return;
    }

    const renderChart = async () => {
      try {
        setRenderError(null);
        const uniqueId = `mermaid_${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(uniqueId, chart.trim());
        setSvgContent(svg);
      } catch (err: any) {
        setRenderError(err.message || 'Diagram syntax error');
      }
    };

    renderChart();
  }, [chart]);

  if (!chart || !chart.trim()) {
    return (
      <div className="p-8 text-center text-xs text-gray-500">
        No visual flowchart or ER diagram available for this selection.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#0d1117] rounded-lg border border-[#30363d] overflow-hidden">
      {/* Controls */}
      <div className="h-8 bg-[#161b22] px-3 border-b border-[#30363d] flex items-center justify-between text-xs">
        <span className="text-gray-400 font-medium text-[11px]">Mermaid Visual Journey</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setScale((s) => Math.max(0.6, s - 0.15))}
            className="p-1 hover:bg-[#21262d] rounded text-gray-400 hover:text-gray-200"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setScale(1)}
            className="p-1 hover:bg-[#21262d] rounded text-gray-400 hover:text-gray-200"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setScale((s) => Math.min(2.0, s + 0.15))}
            className="p-1 hover:bg-[#21262d] rounded text-gray-400 hover:text-gray-200"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="flex-1 overflow-auto p-4 flex items-center justify-center min-h-[300px]">
        {renderError ? (
          <div className="p-4 rounded-lg bg-red-950/30 border border-red-800/50 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>Could not render diagram: {renderError}</span>
          </div>
        ) : (
          <div
            ref={containerRef}
            style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}
            className="transition-transform duration-150"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        )}
      </div>
    </div>
  );
};
