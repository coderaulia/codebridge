import React, { useState } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useProjectStore } from '../../stores/useProjectStore';

export const BackendStatusBanner: React.FC = () => {
  const { isBackendConnected, checkBackendHealth } = useProjectStore();
  const [retrying, setRetrying] = useState(false);

  if (isBackendConnected) return null;

  const handleRetry = async () => {
    setRetrying(true);
    await checkBackendHealth();
    setRetrying(false);
  };

  return (
    <div className="bg-amber-950/80 border-b border-amber-600/40 text-amber-200 px-4 py-2.5 flex items-center justify-between text-xs animate-fade-in select-none">
      <div className="flex items-center gap-2.5">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        <div>
          <span className="font-semibold text-amber-100">Backend Disconnected (127.0.0.1:8000): </span>
          <span>
            The FastAPI server is not reachable. Run{' '}
            <code className="px-1.5 py-0.5 rounded bg-black/40 font-mono text-purple-300 font-bold">
              npm run dev
            </code>{' '}
            in your project directory or start{' '}
            <code className="px-1.5 py-0.5 rounded bg-black/40 font-mono text-purple-300 font-bold">
              npm run dev:backend
            </code>
            .
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={handleRetry}
          disabled={retrying}
          className="flex items-center gap-1.5 px-3 py-1 rounded bg-amber-800/60 hover:bg-amber-700/60 text-amber-100 font-medium border border-amber-600/50 transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${retrying ? 'animate-spin' : ''}`} />
          <span>{retrying ? 'Checking...' : 'Retry Connection'}</span>
        </button>
      </div>
    </div>
  );
};
