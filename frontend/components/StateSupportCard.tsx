'use client';

import React from 'react';
import { AssessmentResponse } from '@/lib/types';
import { Activity, Split, Sparkles, Layers } from 'lucide-react';

interface StateSupportCardProps {
  assessment: AssessmentResponse | null;
}

export default function StateSupportCard({ assessment }: StateSupportCardProps) {
  if (!assessment) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 animate-pulse">
        <div className="h-6 w-48 bg-slate-800 rounded mb-4" />
        <div className="space-y-3">
          <div className="h-14 bg-slate-800/60 rounded-xl" />
          <div className="h-14 bg-slate-800/60 rounded-xl" />
          <div className="h-14 bg-slate-800/60 rounded-xl" />
        </div>
      </div>
    );
  }

  const {
    evidence_support = { W: 0.33, L: 0.33, N: 0.34 },
    assumption_sensitivity_band = { W: [0.3, 0.4], L: [0.3, 0.4], N: [0.3, 0.4] },
    representativeness_support_N = 0.34,
    extent_split_W_given_representative = 0.5
  } = assessment;

  const states = [
    {
      key: 'W',
      label: 'Reach-wide / Upstream Condition (W)',
      value: evidence_support.W ?? 0,
      band: assumption_sensitivity_band.W || [0, 0],
      color: 'from-cyan-500 to-blue-500',
      borderColor: 'border-cyan-500/30',
      badgeBg: 'bg-cyan-950/60 border-cyan-800/60 text-cyan-300',
      description: 'Anomaly condition spans the wider reach or originates upstream of the report site.'
    },
    {
      key: 'L',
      label: 'Local Source Condition (L)',
      value: evidence_support.L ?? 0,
      band: assumption_sensitivity_band.L || [0, 0],
      color: 'from-blue-500 to-indigo-500',
      borderColor: 'border-blue-500/30',
      badgeBg: 'bg-blue-950/60 border-blue-800/60 text-blue-300',
      description: 'Anomaly origin lies locally between upstream observation viewpoint and report site.'
    },
    {
      key: 'N',
      label: 'Transient / Non-Representative (N)',
      value: evidence_support.N ?? 0,
      band: assumption_sensitivity_band.N || [0, 0],
      color: 'from-purple-500 to-pink-500',
      borderColor: 'border-purple-500/30',
      badgeBg: 'bg-purple-950/60 border-purple-800/60 text-purple-300',
      description: 'Brief or non-representative condition / observational artefact (not confirmed pollution or a cause).'
    }
  ];

  return (
    <div className="rounded-2xl border border-slate-800/80 bg-slate-900/70 p-5 sm:p-6 backdrop-blur-xl shadow-2xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-bold text-white tracking-wide">
              Competing Latent Investigation States
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Model-based support across spatial extent and representativeness hypotheses
          </p>
        </div>

        <div className="flex items-center gap-1.5 self-start sm:self-auto px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-[11px] font-mono text-slate-300">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span>Model Support (Sum = 1.00)</span>
        </div>
      </div>

      {/* State Bars List */}
      <div className="space-y-4 my-5">
        {states.map((st) => {
          const percentage = Math.round(st.value * 100);
          const minBand = Math.round((st.band[0] ?? 0) * 100);
          const maxBand = Math.round((st.band[1] ?? 0) * 100);

          return (
            <div
              key={st.key}
              className={`p-4 rounded-xl bg-slate-950/60 border ${st.borderColor} transition-all hover:border-slate-600`}
            >
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono border ${st.badgeBg}`}>
                    {st.key}
                  </span>
                  <span className="text-sm font-semibold text-white">{st.label}</span>
                </div>

                <div className="text-right">
                  <div className="flex items-baseline gap-1.5 justify-end">
                    <span className="text-xs text-slate-500 font-mono">Support:</span>
                    <span className="text-lg font-black font-mono text-white tracking-tight">
                      {st.value.toFixed(2)}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">({percentage}% relative share)</span>
                  </div>
                </div>
              </div>

              {/* Progress Bar with Gradient */}
              <div className="w-full h-3 rounded-full bg-slate-800/80 overflow-hidden relative p-0.5">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${st.color} transition-all duration-700 shadow-lg`}
                  style={{ width: `${Math.max(percentage, 2)}%` }}
                />
              </div>

              {/* Sensitivity Band & Description */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 mt-2.5 text-xs text-slate-400">
                <p className="text-[11px] text-slate-400 leading-snug">{st.description}</p>
                <div className="shrink-0 flex items-center gap-1.5 font-mono text-[11px] text-slate-400">
                  <span className="text-slate-500">Assumption Sensitivity Band:</span>
                  <span className="text-slate-300 font-medium bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                    [{minBand}%, {maxBand}%]
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Diagnostics / Decomposition Split */}
      <div className="pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/70 flex items-start gap-2.5">
          <Split className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider font-mono font-semibold">
              Spatial Extent Split (W | Representative)
            </span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-sm font-bold text-white font-mono">
                {extent_split_W_given_representative.toFixed(3)}
              </span>
              <span className="text-[11px] text-slate-400">
                ({Math.round(extent_split_W_given_representative * 100)}% W vs {Math.round((1 - extent_split_W_given_representative) * 100)}% L)
              </span>
            </div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/70 flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-[11px] text-slate-400 uppercase tracking-wider font-mono font-semibold">
              Representativeness Support (N)
            </span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-sm font-bold text-white font-mono">
                {representativeness_support_N.toFixed(3)}
              </span>
              <span className="text-[11px] text-slate-400">
                ({Math.round(representativeness_support_N * 100)}% transient/non-representative support)
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800/60 text-[11px] font-mono text-slate-500">
        * Model support scores reflect assumption-sensitivity estimates under expert-elicited parameters; NOT calibrated real-world probabilities.
      </div>
    </div>
  );
}
