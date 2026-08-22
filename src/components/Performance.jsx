import React from 'react';
import { Clock, Activity, Zap } from 'lucide-react';

export default function Performance({ timings = {}, benchmark = null }) {
  const hasTimings = timings && Object.keys(timings).length > 0;
  
  const formatMs = (ms) => {
    if (ms === undefined || ms === null) return '-';
    return `${ms.toFixed(1)} ms`;
  };

  return (
    <section className="mb-12">
      <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-4">Performance Profiling</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Current Request Timings */}
        <div className="bg-surface rounded-xl border border-borderMain p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock size={16} className="text-primary" />
            <h4 className="text-xs font-semibold text-textMuted">Current Request Latency</h4>
          </div>
          
          {hasTimings ? (
            <div className="space-y-3 mt-4">
              <TimingRow label="Validation Guardrail" ms={timings.validation_ms} />
              <TimingRow label="FAISS Vector Search" ms={timings.faiss_ms} />
              <TimingRow label="BM25 Keyword Search" ms={timings.bm25_ms} />
              <TimingRow label="RRF Fusion" ms={timings.rrf_ms} />
              <TimingRow label="Total Hybrid Retrieval" ms={timings.hybrid_retrieval_ms} isSubTotal />
              <TimingRow label="Cross-Encoder Reranking" ms={timings.reranking_ms} />
              <TimingRow label="LLM Generation" ms={timings.generation_ms} />
              <TimingRow label="Grounding Verification" ms={timings.grounding_ms} />
              
              <div className="pt-3 mt-3 border-t border-borderMain flex items-center justify-between">
                <span className="text-sm font-bold text-textMain">Total E2E Pipeline</span>
                <span className="text-sm font-bold text-primary">{formatMs(timings.total_pipeline_ms)}</span>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center min-h-[150px] border border-dashed border-borderMain rounded-lg bg-background/50">
              <span className="text-sm font-medium text-textMuted text-center px-4">
                Execute a query to capture real-time latency profile.
              </span>
            </div>
          )}
        </div>
        
        {/* Benchmark Results */}
        <div className="bg-surface rounded-xl border border-borderMain p-6 flex flex-col">
          <div className="flex items-center gap-2 mb-4">
            <Activity size={16} className="text-emerald-500" />
            <h4 className="text-xs font-semibold text-textMuted">Aggregated Benchmarks (Local Pipeline)</h4>
          </div>
          
          {benchmark && benchmark.percentiles ? (
            <div className="flex flex-col flex-1">
              <div className="flex items-center gap-4 mb-4 text-xs text-textMuted">
                <span className="bg-background px-2 py-1 rounded border border-borderMain">
                  Samples: {benchmark.samples}
                </span>
                <span className="bg-background px-2 py-1 rounded border border-borderMain">
                  Success Rate: {Math.round((benchmark.successful_requests / benchmark.samples) * 100)}%
                </span>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-borderMain text-xs font-semibold text-textMuted">
                      <th className="pb-2 font-medium">Stage</th>
                      <th className="pb-2 font-medium text-right">P50</th>
                      <th className="pb-2 font-medium text-right">P70</th>
                      <th className="pb-2 font-medium text-right">P100 (Max)</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    <BenchmarkRow label="Retrieval" data={benchmark.percentiles.hybrid_retrieval_ms} />
                    <BenchmarkRow label="Reranking" data={benchmark.percentiles.reranking_ms} />
                    <BenchmarkRow label="Generation" data={benchmark.percentiles.generation_ms} />
                    <BenchmarkRow label="Grounding" data={benchmark.percentiles.grounding_ms} />
                    <tr className="border-t border-borderMain font-semibold">
                      <td className="py-3 text-textMain">Total</td>
                      <td className="py-3 text-right text-primary">{benchmark.percentiles.total_pipeline_ms?.p50}ms</td>
                      <td className="py-3 text-right text-primary">{benchmark.percentiles.total_pipeline_ms?.p70}ms</td>
                      <td className="py-3 text-right text-primary">{benchmark.percentiles.total_pipeline_ms?.p100}ms</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center flex-1 min-h-[150px] border border-dashed border-borderMain rounded-lg bg-background/50">
              <Zap size={24} className="text-amber-500/50 mb-2" />
              <span className="text-sm font-medium text-textMuted text-center px-4 max-w-[250px]">
                No benchmark results available yet. Run the CLI benchmark script.
              </span>
            </div>
          )}
        </div>
        
      </div>
    </section>
  );
}

function TimingRow({ label, ms, isSubTotal = false }) {
  if (ms === undefined) return null;
  
  return (
    <div className={`flex items-center justify-between ${isSubTotal ? 'pl-0 font-medium text-textMain' : 'pl-4 text-textMuted'}`}>
      <span className="text-sm">{label}</span>
      <span className="text-sm font-mono">{ms.toFixed(1)} ms</span>
    </div>
  );
}

function BenchmarkRow({ label, data }) {
  if (!data) return null;
  return (
    <tr className="border-b border-borderMain/50 last:border-0">
      <td className="py-2.5 text-textMuted">{label}</td>
      <td className="py-2.5 text-right font-mono text-textMain">{data.p50}</td>
      <td className="py-2.5 text-right font-mono text-textMain">{data.p70}</td>
      <td className="py-2.5 text-right font-mono text-textMain">{data.p100}</td>
    </tr>
  );
}
