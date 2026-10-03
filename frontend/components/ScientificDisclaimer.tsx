'use client';

import React, { useState } from 'react';
import { ShieldAlert, ChevronDown, ChevronUp } from 'lucide-react';
import { SCIENTIFIC_HONESTY_DECLARATION } from '@/lib/constants';

interface ScientificDisclaimerProps {
  compact?: boolean;
}

export default function ScientificDisclaimer({ compact = false }: ScientificDisclaimerProps) {
  const [expanded, setExpanded] = useState(false);

  if (compact) {
    return (
      <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3 text-xs text-amber-200/90 flex items-start gap-2.5 backdrop-blur-sm">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <span className="font-semibold text-amber-300">Scientific Honesty Notice:</span>{' '}
          Model support values represent assumption-sensitivity scores under expert-elicited parameters (
          <code className="text-[11px] bg-amber-950/60 px-1 py-0.5 rounded text-amber-300">EXPERT_ELICITED_UNCALIBRATED</code>
          ). They are not calibrated real-world probabilities.
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-b from-amber-950/25 to-slate-950/60 p-4 sm:p-5 backdrop-blur-md shadow-xl transition-all">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center shrink-0 text-amber-400 mt-0.5">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-amber-300 tracking-wide uppercase">
                {SCIENTIFIC_HONESTY_DECLARATION.title}
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded">
                EXPERT_ELICITED_UNCALIBRATED
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 italic leading-relaxed">
              {SCIENTIFIC_HONESTY_DECLARATION.core_thesis}
            </p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-amber-400 hover:text-amber-300 px-2.5 py-1 rounded-lg bg-amber-950/40 hover:bg-amber-900/40 border border-amber-500/20 transition-all shrink-0"
        >
          <span>{expanded ? 'Less info' : 'Methodology Details'}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      <p className="text-xs text-slate-300/90 mt-3 leading-relaxed">
        {SCIENTIFIC_HONESTY_DECLARATION.disclaimer}
      </p>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-amber-500/20 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-cyan-300">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              State W: Reach-wide / Upstream
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Anomaly spatial extent is distributed across the entire river reach or originates upstream.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-300">
              <span className="w-2 h-2 rounded-full bg-blue-400" />
              State L: Local Source Anomaly
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Anomaly source lies locally between upstream vantage point and the citizen report site.
            </p>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-purple-300">
              <span className="w-2 h-2 rounded-full bg-purple-400" />
              State N: Transient / Artefact
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Validity/representativeness state indicating brief or non-persistent condition. Not a root cause.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
