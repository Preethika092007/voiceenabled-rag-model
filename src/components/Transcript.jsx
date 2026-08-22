import React from 'react';

export default function Transcript({ text }) {
  return (
    <section className="mb-8">
      <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-4">Transcript</h3>
      <div className="bg-surface rounded-xl border border-borderMain p-6 min-h-[100px] flex items-center justify-center">
        {text ? (
          <p className="text-textMain text-sm text-center leading-relaxed">
            "{text}"
          </p>
        ) : (
          <p className="text-textMuted text-sm italic">
            Your transcribed question will appear here.
          </p>
        )}
      </div>
    </section>
  );
}
