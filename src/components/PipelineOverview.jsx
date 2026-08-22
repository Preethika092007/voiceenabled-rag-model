import React from 'react';
import { Mic, FileText, CheckCircle, Search, Layers, MessageSquare, ShieldCheck } from 'lucide-react';

const STAGES = [
  { id: 'voice', label: 'Voice Input', icon: Mic },
  { id: 'stt', label: 'Speech-to-Text', icon: FileText },
  { id: 'validation', label: 'Query Validation', icon: CheckCircle },
  { id: 'retrieval', label: 'Hybrid Retrieval', icon: Search },
  { id: 'reranking', label: 'Reranking', icon: Layers },
  { id: 'generation', label: 'Answer Generation', icon: MessageSquare },
  { id: 'grounding', label: 'Grounding Check', icon: ShieldCheck },
];

export default function PipelineOverview({ states = {} }) {
  return (
    <section className="mb-12">
      <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-6">Pipeline</h3>
      
      <div className="bg-surface rounded-xl border border-borderMain p-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 md:gap-2 overflow-x-auto pb-4 md:pb-0">
          {STAGES.map((stage, index) => {
            const Icon = stage.icon;
            const isLast = index === STAGES.length - 1;
            
            let currentStageState = states[stage.id] || 'waiting';
            
            let stageStatus = 'Waiting';
            let opacity = 'opacity-60';
            let statusColor = 'text-textMuted bg-background border-borderMain';
            let iconColor = 'text-textMuted bg-background border-borderMain';
            
            if (currentStageState === 'recording' || currentStageState === 'processing') {
              stageStatus = currentStageState === 'recording' ? 'Recording' : 'Processing';
              opacity = 'opacity-100';
              statusColor = 'text-primary bg-primary/10 border-primary/30';
              iconColor = 'text-primary bg-primary/10 border-primary/30 animate-pulse';
            } else if (currentStageState === 'complete') {
              stageStatus = 'Complete';
              opacity = 'opacity-100';
              statusColor = 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30';
              iconColor = 'text-emerald-500 bg-background border-emerald-500/30';
            } else if (currentStageState === 'error') {
              stageStatus = 'Error';
              opacity = 'opacity-100';
              statusColor = 'text-red-500 bg-red-500/10 border-red-500/30';
              iconColor = 'text-red-500 bg-background border-red-500/30';
            } else if (currentStageState === 'skipped') {
              stageStatus = 'Skipped';
              opacity = 'opacity-50';
              statusColor = 'text-amber-500 bg-amber-500/10 border-amber-500/30';
              iconColor = 'text-amber-500 bg-background border-amber-500/30';
            }

            
            return (
              <React.Fragment key={stage.id}>
                <div className={`flex flex-col items-center gap-2 min-w-[100px] ${opacity} transition-all duration-300`}>
                  <div className={`w-10 h-10 rounded-full border flex items-center justify-center transition-colors duration-300 ${iconColor}`}>
                    <Icon size={18} />
                  </div>
                  <span className="text-xs font-medium text-center">{stage.label}</span>
                  <span className={`text-[10px] uppercase tracking-wide border px-2 py-0.5 rounded-full transition-colors duration-300 ${statusColor}`}>
                    {stageStatus}
                  </span>
                </div>
                
                {!isLast && (
                  <div className="hidden md:block flex-1 h-px bg-borderMain min-w-[20px] max-w-[40px] mt-[-24px]"></div>
                )}
                {!isLast && (
                  <div className="md:hidden w-px h-6 bg-borderMain"></div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </section>
  );
}
