import React from 'react';
import { Loader2, Database, AlignLeft } from 'lucide-react';

export default function RetrievedContext({ results = [], isLoading = false }) {
  return (
    <section className="mb-8 flex flex-col h-full">
      <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-4">Retrieved Context</h3>
      <div className={`bg-surface rounded-xl border border-borderMain p-4 flex-1 flex flex-col ${results.length === 0 ? 'justify-center items-center min-h-[120px]' : 'gap-4'}`}>
        
        {isLoading && (
          <div className="flex flex-col items-center gap-3 py-8">
            <Loader2 size={24} className="text-primary animate-spin" />
            <span className="text-sm text-textMuted">Retrieving and reranking context...</span>
          </div>
        )}

        {!isLoading && results.length === 0 && (
          <p className="text-textMuted text-sm text-center">
            Relevant sources will appear here after retrieval.
          </p>
        )}

        {!isLoading && results.length > 0 && (
          <div className="flex flex-col gap-4 overflow-y-auto max-h-[500px] pr-2 custom-scrollbar">
            {results.map((result, idx) => (
              <div key={idx} className="bg-background rounded-lg border border-borderMain p-4 flex flex-col gap-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-textMuted">
                    <div className="w-5 h-5 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold">
                      {result.final_rank || idx + 1}
                    </div>
                    <Database size={14} className="text-primary/70" />
                    <span>ID: {result.chunk_id.substring(0, 15)}...</span>
                  </div>
                  
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {result.retrieval_sources?.map(source => (
                      <span key={source} className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-surface border border-borderMain text-textMuted">
                        {source}
                      </span>
                    ))}
                    {result.reranker_score !== undefined && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-accent/20 text-accent border border-accent/30">
                        Rerank Score: {result.reranker_score.toFixed(3)}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <AlignLeft size={16} className="text-textMuted shrink-0 mt-0.5" />
                  <p className="text-sm text-textMain leading-relaxed">
                    {result.text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
