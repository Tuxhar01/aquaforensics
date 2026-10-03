'use client';

import React, { useState } from 'react';
import { AssessmentResponse } from '@/lib/types';
import { ACTION_DEFINITIONS } from '@/lib/constants';
import {
  Compass,
  Zap,
  Scale,
  AlertTriangle,
  ArrowRight,
  Clock,
  HelpCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  HelpCircle as QuestionIcon
} from 'lucide-react';

interface RecommendationCardProps {
  assessment: AssessmentResponse | null;
  onRecordAction: (actionId: string) => void;
}

export default function RecommendationCard({ assessment, onRecordAction }: RecommendationCardProps) {
  const [showEigHelp, setShowEigHelp] = useState(false);

  if (!assessment) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 animate-pulse">
        <div className="h-7 w-64 bg-slate-800 rounded mb-4" />
        <div className="h-24 bg-slate-800/60 rounded-xl" />
      </div>
    );
  }

  const { status, recommendation, reasons, candidates = [] } = assessment;

  // Lookup recommended action details if single action
  const recActionId = (recommendation?.action_id || (Array.isArray(recommendation?.actions) && recommendation.actions.length > 0 ? recommendation.actions[0] : undefined)) as string | undefined;
  const singleCandidate = candidates.find((c) => (c.action_id === recActionId || c.action === recActionId));
  const actionMeta = recActionId ? ACTION_DEFINITIONS[recActionId] : null;
  const singleEig = singleCandidate?.nominal_eig_bits ?? singleCandidate?.eig_bits ?? singleCandidate?.expected_info_gain ?? 0;

  // Badge config based on mathematical status
  const statusConfig = {
    ROBUST: {
      label: 'ROBUST RECOMMENDATION',
      sublabel: 'Decisive Expected Information Gain (EIG)',
      border: 'border-emerald-500/50',
      bg: 'bg-gradient-to-br from-emerald-950/40 via-slate-900/90 to-slate-950/90',
      badgeBg: 'bg-emerald-950/90 border-emerald-500/50 text-emerald-300',
      icon: Zap,
      iconColor: 'text-emerald-400'
    },
    NEAR_TIE: {
      label: 'NEAR-TIE CANDIDATE SET',
      sublabel: 'Multiple actions with comparable information value',
      border: 'border-amber-500/50',
      bg: 'bg-gradient-to-br from-amber-950/40 via-slate-900/90 to-slate-950/90',
      badgeBg: 'bg-amber-950/90 border-amber-500/50 text-amber-300',
      icon: Scale,
      iconColor: 'text-amber-400'
    },
    INSUFFICIENT_CONFIDENCE: {
      label: 'INSUFFICIENT CONFIDENCE',
      sublabel: 'Low information gain or high diffuse uncertainty',
      border: 'border-sky-500/50',
      bg: 'bg-gradient-to-br from-sky-950/40 via-slate-900/90 to-slate-950/90',
      badgeBg: 'bg-sky-950/90 border-sky-500/50 text-sky-300',
      icon: AlertTriangle,
      iconColor: 'text-sky-400'
    },
    NO_FEASIBLE_ACTIONS: {
      label: 'NO FEASIBLE ACTIONS',
      sublabel: 'All candidate investigation actions are currently excluded or completed',
      border: 'border-slate-700',
      bg: 'bg-slate-900/70',
      badgeBg: 'bg-slate-800 border-slate-700 text-slate-300',
      icon: AlertTriangle,
      iconColor: 'text-slate-400'
    }
  }[status] || {
    label: status,
    sublabel: 'Computed Bayesian Assessment',
    border: 'border-slate-700',
    bg: 'bg-slate-900/70',
    badgeBg: 'bg-slate-800 border-slate-700 text-slate-300',
    icon: Compass,
    iconColor: 'text-cyan-400'
  };

  const StatusIcon = statusConfig.icon;

  // Derive Evidence Gap explanation
  const getEvidenceGapText = (actId?: string) => {
    switch (actId) {
      case 'upstream_view':
        return 'We have observed turbidity at this site, but cannot yet tell if the anomaly originates further upstream across the wider river reach (W) or was introduced locally within this reach (L).';
      case 'recheck_60min':
        return 'We do not know whether this condition is brief/transient (N) or represents persistent environmental state.';
      case 'second_downstream':
        return 'We do not know whether the anomaly extends continuously along the downstream corridor (W) or remains strictly localized (L).';
      case 'inspect_pipes_works':
        return 'We do not know if direct infrastructure points, outfall pipes, or local works are actively discharging into this reach.';
      default:
        return 'Current evidence leaves competing spatial extent and persistence hypotheses unresolved.';
    }
  };

  return (
    <div className={`rounded-2xl border-2 ${statusConfig.border} ${statusConfig.bg} p-6 sm:p-7 backdrop-blur-xl shadow-2xl relative overflow-hidden ring-1 ring-cyan-500/20`}>
      {/* Background glow highlight */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-b from-cyan-500/10 via-emerald-500/5 to-transparent rounded-full blur-3xl pointer-events-none" />

      {/* Card Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-slate-800/80">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-slate-900 border border-slate-700 flex items-center justify-center shrink-0 shadow-inner">
            <StatusIcon className={`w-6 h-6 ${statusConfig.iconColor}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold tracking-widest text-cyan-400 uppercase">
                Next-Best-Evidence
              </span>
              <span className={`px-2.5 py-0.5 text-[10px] font-mono font-extrabold uppercase rounded-full border ${statusConfig.badgeBg}`}>
                {statusConfig.label}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">{statusConfig.sublabel}</p>
          </div>
        </div>

        {/* EIG Concept Explainer Toggle */}
        <button
          type="button"
          onClick={() => setShowEigHelp(!showEigHelp)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-850 border border-slate-700 text-xs font-mono text-cyan-300 transition-all self-start sm:self-auto cursor-pointer"
        >
          <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
          <span>What is EIG?</span>
          {showEigHelp ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* Expandable EIG Educational Drawer */}
      {showEigHelp && (
        <div className="mt-4 p-4 rounded-xl bg-slate-950/80 border border-cyan-800/60 text-xs text-slate-300 space-y-2.5 animate-in fade-in duration-200">
          <div className="flex items-center gap-2 font-bold text-cyan-300">
            <Zap className="w-4 h-4 text-cyan-400" />
            <span>Expected Information Gain (EIG) in AquaForensics</span>
          </div>
          <p className="leading-relaxed text-slate-300">
            <strong>Expected Information Gain (EIG)</strong> estimates how much mathematical uncertainty an observation is expected to remove across competing hypotheses.
          </p>
          <p className="leading-relaxed text-slate-400 border-l-2 border-cyan-500 pl-3">
            Rather than asking which observation sounds plausible to a human, AquaForensics evaluates which feasible observation will distinguish the competing explanations (W vs L vs N) most effectively.
          </p>
        </div>
      )}

      {/* Case 1: ROBUST SINGLE RECOMMENDATION */}
      {status === 'ROBUST' && recActionId && (
        <div className="mt-6 space-y-5">
          {/* Main Recommended Action Hero Box */}
          <div className="p-5 sm:p-6 rounded-2xl bg-slate-950/80 border border-emerald-500/40 shadow-xl space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
              <div className="space-y-2 flex-1">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-emerald-400 font-bold">
                    Recommended Observation:
                  </span>
                  <span className={`px-2.5 py-0.5 text-[11px] font-mono rounded-full border ${
                    (actionMeta?.source_class === 'extension' || singleCandidate?.source_class === 'extension')
                      ? 'bg-purple-950/80 border-purple-800/60 text-purple-300'
                      : 'bg-cyan-950/80 border-cyan-800/60 text-cyan-300'
                  }`}>
                    {actionMeta?.source_class === 'extension' ? 'AquaForensics Extension' : 'OAH-Aligned Survey Action'}
                  </span>
                </div>

                <h3 className="text-lg sm:text-xl font-extrabold text-white">
                  {(recommendation.label as string) || actionMeta?.label || recActionId}
                </h3>

                <p className="text-sm text-slate-300 leading-relaxed">
                  {actionMeta?.description || 'Execute this action to achieve maximal entropy reduction across competing latent states.'}
                </p>
              </div>

              {/* Human-in-the-Loop Primary Decision Button */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 shrink-0">
                <button
                  onClick={() => onRecordAction(recActionId)}
                  className="flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-black text-sm shadow-xl shadow-emerald-500/25 active:scale-95 transition-all cursor-pointer"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>I&apos;ll Collect This Evidence</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Evidence Gap & Why This Observation? */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3 border-t border-slate-800/80">
              <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-amber-300 uppercase">
                  <QuestionIcon className="w-3.5 h-3.5 text-amber-400" />
                  <span>What Don&apos;t We Know Yet? (Evidence Gap)</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {getEvidenceGapText(recActionId)}
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-300 uppercase">
                  <Zap className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Why This Observation?</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Expected Info Gain: <strong className="text-emerald-400 font-mono">{singleEig.toFixed(4)} bits</strong> of entropy reduction across competing latent states.
                </p>
              </div>
            </div>

            {/* Metrics Footer */}
            <div className="pt-2 flex flex-wrap items-center gap-5 text-xs font-mono text-slate-400">
              {singleCandidate && (
                <div className="flex items-center gap-1.5 text-emerald-400">
                  <span className="text-slate-400">EIG:</span>
                  <span className="font-bold">{singleEig.toFixed(4)} bits</span>
                </div>
              )}
              {singleCandidate?.effort && (
                <div className="flex items-center gap-1.5 text-slate-300">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-slate-400">Effort:</span>
                  <span>{singleCandidate.effort || singleCandidate.effort_label}</span>
                </div>
              )}
              {actionMeta?.field_status && (
                <div className="text-[11px] text-slate-500">
                  <span>Provenance: {actionMeta.field_status}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Case 2: NEAR_TIE (Multiple Comparable Actions) */}
      {status === 'NEAR_TIE' && (
        <div className="mt-6 space-y-4">
          <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/40 text-xs text-amber-200/90 leading-relaxed">
            <span className="font-bold text-amber-300">Scientifically Honest Near-Tie Protocol:</span>{' '}
            The mathematical reasoning engine detected candidate actions with nearly identical expected information gain. AquaForensics refuses to pick an arbitrary winner. Please select whichever candidate is physically feasible at your site.
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-2">
            {(
              (Array.isArray(recommendation?.actions) && recommendation.actions.length > 0 ? recommendation.actions : null) ||
              (Array.isArray(recommendation?.action_set) && recommendation.action_set.length > 0 ? recommendation.action_set : null) ||
              (Array.isArray(recommendation?.tie_actions) && recommendation.tie_actions.length > 0 ? recommendation.tie_actions : null) ||
              candidates.slice(0, 2).map(c => c.action_id || c.action || '').filter(Boolean)
            ).map((actId: string) => {
              const cand = candidates.find(c => c.action_id === actId || c.action === actId);
              const meta = ACTION_DEFINITIONS[actId];
              const candEig = cand?.nominal_eig_bits ?? cand?.eig_bits ?? cand?.expected_info_gain ?? 0;
              return (
                <div
                  key={actId}
                  className="p-5 rounded-2xl bg-slate-950/80 border border-amber-500/40 flex flex-col justify-between gap-4 hover:border-amber-400 transition-all shadow-lg"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-white">{meta?.label || cand?.label || actId}</span>
                      <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-amber-950 text-amber-300 border border-amber-800">
                        Candidate
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{meta?.description || cand?.label}</p>
                    <p className="text-[11px] text-slate-400 font-mono pt-1">
                      Evidence gap: {getEvidenceGapText(actId)}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs font-mono">
                    <span className="text-slate-400">EIG: <strong className="text-white">{candEig.toFixed(4)} bits</strong></span>
                    <button
                      onClick={() => onRecordAction(actId)}
                      className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 active:scale-95 transition-all cursor-pointer"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>I&apos;ll Collect This</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Case 3: INSUFFICIENT_CONFIDENCE */}
      {status === 'INSUFFICIENT_CONFIDENCE' && (
        <div className="mt-6 p-5 rounded-2xl bg-slate-950/80 border border-sky-500/40 space-y-4 shadow-xl">
          <div className="flex items-start gap-3 text-xs text-sky-200">
            <AlertTriangle className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              Expected information gain across remaining candidate actions is below the decisive threshold or current evidence indicates diffuse uncertainty. The system recommends continued passive observation or repeat checking.
            </p>
          </div>

          <div className="pt-2 flex flex-wrap gap-2.5">
            {candidates.map((cand, idx) => {
              const actId = cand.action_id || cand.action || `cand-${idx}`;
              return (
                <button
                  key={actId}
                  onClick={() => onRecordAction(actId)}
                  className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-2 transition-all cursor-pointer"
                >
                  <span>Record {cand.label || actId}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Case 4: NO FEASIBLE ACTIONS */}
      {status === 'NO_FEASIBLE_ACTIONS' && (
        <div className="mt-6 p-5 rounded-2xl bg-slate-950/80 border border-slate-700 text-xs text-slate-400 shadow-xl">
          All candidate investigation actions have either been completed or designated infeasible. You may review the investigation audit timeline or export findings to FHIR format.
        </div>
      )}

      {/* Engine Reasoning Diagnostics */}
      {reasons && reasons.length > 0 && (
        <div className="mt-5 pt-4 border-t border-slate-800/80">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Engine Reasoning Diagnostics:
          </span>
          <ul className="mt-2 space-y-1.5">
            {reasons.map((r, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-slate-300 font-mono">
                <span className="text-cyan-400 font-bold">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
