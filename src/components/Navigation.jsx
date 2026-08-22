import React from 'react';
import { Waves, Activity, Database } from 'lucide-react';

export default function Navigation({ systemStatus = 'Offline', datasetStatus = 'not_prepared' }) {
  const isOnline = systemStatus === 'Ready';
  const isKbReady = datasetStatus === 'ready';

  return (
    <nav className="w-full bg-surface border-b border-borderMain sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 p-2 rounded-lg text-primary">
            <Waves size={20} />
          </div>
          <span className="text-xl font-bold tracking-tight text-textMain">EchoRAG</span>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-background border border-borderMain text-xs font-medium">
            <Database size={14} className={isKbReady ? "text-emerald-500" : "text-amber-500"} />
            <span className={isKbReady ? "text-textMain" : "text-textMuted"}>
              {isKbReady ? 'KB Ready' : 'KB Not Prepared'}
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-background border border-borderMain text-xs font-medium">
            <Activity size={14} className={isOnline ? "text-emerald-500 animate-pulse" : "text-red-500"} />
            <span className={isOnline ? "text-textMain" : "text-red-400"}>
              {isOnline ? 'System Ready' : 'Backend Offline'}
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
}
