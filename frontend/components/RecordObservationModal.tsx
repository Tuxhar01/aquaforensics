'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { ACTION_DEFINITIONS } from '@/lib/constants';
import {
  X,
  PlusCircle,
  AlertCircle,
  Sparkles,
  Loader2
} from 'lucide-react';

interface RecordObservationModalProps {
  isOpen: boolean;
  onClose: () => void;
  investigationId: string;
  defaultActionId?: string | null;
  defaultReliability?: number;
  onObservationAdded: () => void;
}

export default function RecordObservationModal({
  isOpen,
  onClose,
  investigationId,
  defaultActionId,
  defaultReliability = 0.90,
  onObservationAdded
}: RecordObservationModalProps) {
  const initialAction = defaultActionId || 'upstream_view';
  const initialMeta = ACTION_DEFINITIONS[initialAction];
  const initialOutcome = initialMeta && initialMeta.outcomes.length > 0 ? initialMeta.outcomes[0] : '';

  const [actionId, setActionId] = useState<string>(initialAction);
  const [outcome, setOutcome] = useState<string>(initialOutcome);
  const [reliability, setReliability] = useState<number>(defaultReliability);
  const [claimedSource, setClaimedSource] = useState<'oah' | 'extension'>('oah');
  const [notes, setNotes] = useState<string>('');
  const [timestampMin, setTimestampMin] = useState<string>('0');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const currentMeta = ACTION_DEFINITIONS[actionId];

  // Update outcome options when action selection changes
  const handleActionChange = (newAct: string) => {
    setActionId(newAct);
    const meta = ACTION_DEFINITIONS[newAct];
    if (meta && meta.outcomes.length > 0) {
      setOutcome(meta.outcomes[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.addObservation(investigationId, {
        action_id: actionId,
        outcome: outcome,
        reliability: Number(reliability),
        claimed_source: claimedSource,
        notes: notes.trim() || undefined,
        timestamp_min: timestampMin ? parseFloat(timestampMin) : 0
      });

      onObservationAdded();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to record observation';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center border border-cyan-500/30">
              <PlusCircle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Record Evidence Observation</h2>
              <p className="text-xs text-slate-400 font-mono">Updates Bayesian posterior beliefs</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4 flex-1">
          {error && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Action Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
              Investigation Action
            </label>
            <select
              value={actionId}
              onChange={(e) => handleActionChange(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              {Object.values(ACTION_DEFINITIONS).map((act) => (
                <option key={act.id} value={act.id}>
                  {act.label} ({act.source_class === 'extension' ? 'AquaForensics Extension' : 'OAH-Aligned'})
                </option>
              ))}
            </select>
            {currentMeta && (
              <p className="text-[11px] text-slate-400 mt-1">{currentMeta.description}</p>
            )}
          </div>

          {/* Outcome Choice */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
              Observed Outcome
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {currentMeta?.outcomes.map((opt) => (
                <label
                  key={opt}
                  className={`p-3 rounded-xl border flex items-center gap-2.5 cursor-pointer text-xs font-mono transition-all ${
                    outcome === opt
                      ? 'bg-cyan-950/60 border-cyan-500 text-cyan-200 shadow-sm shadow-cyan-500/10'
                      : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="outcome"
                    value={opt}
                    checked={outcome === opt}
                    onChange={() => setOutcome(opt)}
                    className="text-cyan-500 focus:ring-cyan-500"
                  />
                  <span className="font-semibold">{opt}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Reliability & Time Offset Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Reliability Slider */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-300 uppercase font-mono">
                  Observation Reliability
                </label>
                <span className="text-xs font-mono font-bold text-cyan-400">
                  {(reliability * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.10"
                max="1.0"
                step="0.05"
                value={reliability}
                onChange={(e) => setReliability(parseFloat(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500 font-mono">
                Default baseline: {(defaultReliability * 100).toFixed(0)}%
              </span>
            </div>

            {/* Time Offset */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
                Elapsed Minutes Since Initial Report
              </label>
              <input
                type="number"
                min="0"
                step="1"
                value={timestampMin}
                onChange={(e) => setTimestampMin(e.target.value)}
                placeholder="e.g. 15 or 60"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-sm focus:border-cyan-500 focus:outline-none font-mono"
              />
            </div>
          </div>

          {/* Claimed Source / Provenance */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
              Evidence Source Provenance Claim
            </label>
            <div className="flex gap-3">
              <label
                className={`flex-1 p-2.5 rounded-xl border flex items-center justify-between cursor-pointer text-xs font-mono ${
                  claimedSource === 'oah'
                    ? 'bg-slate-950 border-cyan-500 text-cyan-300'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400'
                }`}
              >
                <span>OAH-Aligned Survey Field</span>
                <input
                  type="radio"
                  name="source"
                  value="oah"
                  checked={claimedSource === 'oah'}
                  onChange={() => setClaimedSource('oah')}
                  className="text-cyan-500 focus:ring-cyan-500"
                />
              </label>

              <label
                className={`flex-1 p-2.5 rounded-xl border flex items-center justify-between cursor-pointer text-xs font-mono ${
                  claimedSource === 'extension'
                    ? 'bg-slate-950 border-purple-500 text-purple-300'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400'
                }`}
              >
                <span>AquaForensics Extension</span>
                <input
                  type="radio"
                  name="source"
                  value="extension"
                  checked={claimedSource === 'extension'}
                  onChange={() => setClaimedSource('extension')}
                  className="text-purple-500 focus:ring-purple-500"
                />
              </label>
            </div>
            {currentMeta?.source_class === 'extension' && claimedSource === 'oah' && (
              <p className="text-[11px] text-amber-400/90 mt-1 font-mono">
                * Note: Adapter rules will register this as AquaForensics extension evidence because {actionId} is not an official OAH native field.
              </p>
            )}
          </div>

          {/* Observer Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase font-mono">
              Observer Field Notes (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record any sensory notes, water color changes, weather shifts, or site context..."
              rows={2}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs focus:border-cyan-500 focus:outline-none"
            />
          </div>

          {/* Modal Footer */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={loading || !outcome}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 disabled:opacity-50 text-slate-950 text-xs font-black shadow-lg shadow-emerald-500/20 flex items-center gap-2 transition-all active:scale-95 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                  <span>Re-evaluating Evidence...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Update Investigation</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
