import React from 'react';
import { Loader2, FileText, Database, ShieldAlert, AlertTriangle } from 'lucide-react';

export default function Answer({ answer, sources = [], status, reason, isLoading = false }) {
  return (
    <section className="mb-8">
      <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-4">Grounded Answer</h3>
      <div className="bg-surface rounded-xl border border-borderMain p-6 min-h-[150px] flex flex-col">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-8 flex-1">
            <Loader2 size={24} className="text-primary animate-spin" />
            <span className="text-sm text-textMuted">Generating grounded answer...</span>
          </div>
        ) : (status === 'blocked' || status === 'abstained' || status === 'error') ? (
          <div className="flex flex-col items-center justify-center flex-1 h-full gap-4 text-center max-w-md mx-auto">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${status === 'blocked' ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'}`}>
              {status === 'blocked' ? <ShieldAlert size={24} /> : <AlertTriangle size={24} />}
            </div>
            <p className="text-textMain font-medium leading-relaxed">{answer}</p>
            {reason && (
              <p className="text-xs text-textMuted font-mono bg-background border border-borderMain px-3 py-1.5 rounded">
                Reason: {reason}
              </p>
            )}
          </div>
        ) : answer ? (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2 mb-1">
              <ShieldAlert size={14} className="text-emerald-500" />
              <span className="text-xs font-semibold text-emerald-500 tracking-wide uppercase">Grounding Verified</span>
            </div>
            <p className="text-textMain leading-relaxed whitespace-pre-wrap">{answer}</p>
            
            {sources && sources.length > 0 && (
              <div className="mt-4 pt-4 border-t border-borderMain">
                <h4 className="text-xs font-semibold text-textMuted uppercase mb-3">Sources Used</h4>
                <div className="flex flex-wrap gap-2">
                  {sources.map((source, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-background border border-borderMain text-xs text-textMuted">
                      <div className="w-4 h-4 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-[10px]">
                        {source.rank}
                      </div>
                      <Database size={12} className="opacity-70" />
                      <span className="font-mono text-[10px] truncate max-w-[120px]">{source.chunk_id}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center flex-1 h-full">
            <p className="text-textMuted text-sm text-center">
              The generated answer will appear here.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
