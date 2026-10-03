'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { InvestigationResponse, FeasibilityDetail, InvestigationCreatePayload } from '@/lib/types';
import { PRESET_LOCATIONS, ACTION_DEFINITIONS } from '@/lib/constants';
import ScientificDisclaimer from '@/components/ScientificDisclaimer';
import {
  Plus,
  ArrowRight,
  Zap,
  Activity,
  MapPin,
  Sparkles,
  ChevronRight,
  Sliders,
  AlertTriangle,
  Loader2
} from 'lucide-react';

export default function LandingPage() {
  const router = useRouter();

  // Investigation form state
  const [title, setTitle] = useState('');
  const [anomalyType, setAnomalyType] = useState('abnormal_water_aspect');
  const [latitude, setLatitude] = useState('51.5074');
  const [longitude, setLongitude] = useState('-0.1278');
  const [initialDescription, setInitialDescription] = useState(
    '[DEMO / SYNTHETIC DATA] Water observed with unusual brownish turbidity and suspended sediment after light rainfall.'
  );
  const [observerReliability, setObserverReliability] = useState(0.90);
  const [feasibilityOverrides, setFeasibilityOverrides] = useState<Record<string, FeasibilityDetail>>({});
  const [showFeasibility, setShowFeasibility] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Recent investigations state
  const [investigations, setInvestigations] = useState<InvestigationResponse[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      setLoadingList(true);
      try {
        const data = await api.listInvestigations(20);
        if (isMounted) setInvestigations(data);
      } catch {
        // ignore
      } finally {
        if (isMounted) setLoadingList(false);
      }
    };
    loadData();
    return () => {
      isMounted = false;
    };
  }, [refreshTrigger]);

  const handleApplyPreset = (preset: typeof PRESET_LOCATIONS[0]) => {
    setTitle(`[DEMO / SYNTHETIC DATA] ${preset.name}`);
    setLatitude(preset.lat.toString());
    setLongitude(preset.lng.toString());
    setInitialDescription(preset.description);
  };

  const [runningDemo, setRunningDemo] = useState(false);

  const handleRunDemo = async () => {
    setRunningDemo(true);
    setFormError(null);
    try {
      const demoInv = await api.initDemoInvestigation();
      router.push(`/investigations/${demoInv.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to launch demo scenario';
      setFormError(msg);
      setRunningDemo(false);
    }
  };

  const handleToggleFeasibility = (actionId: string, isFeasible: boolean, reason?: string) => {
    setFeasibilityOverrides(prev => ({
      ...prev,
      [actionId]: { feasible: isFeasible, reason: reason || 'Infeasible at this location' }
    }));
  };

  const handleCreateInvestigation = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);

    const lat = parseFloat(latitude);
    const lon = parseFloat(longitude);

    if (isNaN(lat) || lat < -90 || lat > 90) {
      setFormError('Latitude must be a valid number between -90 and 90');
      setSubmitting(false);
      return;
    }
    if (isNaN(lon) || lon < -180 || lon > 180) {
      setFormError('Longitude must be a valid number between -180 and 180');
      setSubmitting(false);
      return;
    }

    try {
      const payload: InvestigationCreatePayload = {
        title: title.trim() || undefined,
        anomaly_type: anomalyType,
        latitude: lat,
        longitude: lon,
        initial_description: initialDescription.trim() || undefined,
        observer_reliability: Number(observerReliability)
      };

      if (Object.keys(feasibilityOverrides).length > 0) {
        payload.feasibility = feasibilityOverrides;
      }

      const res = await api.createInvestigation(payload);
      router.push(`/investigations/${res.id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to initialize investigation';
      setFormError(msg);
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-12">
      {/* 1. Hero Section */}
      <section className="relative rounded-3xl border border-cyan-900/40 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-950 p-6 sm:p-10 shadow-2xl overflow-hidden">
        {/* Ambient background blur */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-b from-cyan-500/10 to-blue-600/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-4xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800/60 text-cyan-400 text-xs font-mono font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            <span>OneAquaHealth IEEE Global Hackathon 2026</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Evidence-Guided <br />
            <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">
              Environmental Reasoning
            </span>
          </h1>

          <blockquote className="text-base sm:text-lg text-slate-300 font-medium italic border-l-2 border-cyan-500 pl-4 py-1">
            &ldquo;AquaForensics doesn’t ask AI to decide what happened. <br />
            It asks what evidence we need to find out.&rdquo;
          </blockquote>

          <p className="text-sm text-slate-400 leading-relaxed max-w-3xl">
            Turn citizen science observations of urban water anomalies into structured investigations, competing latent hypotheses (Reach-wide vs Local vs Transient), uncertainty estimates, and mathematically computed <strong>Next-Best-Evidence (EIG)</strong> recommendations.
          </p>

          {/* Dedicated 3-Minute Demo CTA Banner */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-cyan-950/80 via-slate-900/90 to-slate-950 border-2 border-cyan-500/40 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-950/80 text-purple-300 border border-purple-800/60">
                  DEMO / SYNTHETIC DATA
                </span>
                <span className="text-xs font-mono font-semibold text-cyan-300">
                  3–5 Minute Hackathon Walkthrough
                </span>
              </div>
              <h3 className="text-base font-bold text-white">
                Deterministic Investigation Scenario
              </h3>
              <p className="text-xs text-slate-400">
                Explore a synthetic AquaForensics investigation from first observation to updated evidence.
              </p>
            </div>

            <button
              onClick={handleRunDemo}
              disabled={runningDemo}
              className="flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 via-teal-400 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-slate-950 font-black text-sm shadow-xl shadow-cyan-500/25 active:scale-95 transition-all cursor-pointer shrink-0 disabled:opacity-50"
            >
              {runningDemo ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                  <span>Initializing Engine...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Run Demo Investigation</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Citizen Science Evolution Diagram */}
          <div className="pt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 space-y-2">
              <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider font-semibold">
                Traditional Citizen Science
              </span>
              <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
                <span className="bg-slate-900 px-2 py-1 rounded border border-slate-800">OBSERVE</span>
                <span>→</span>
                <span className="bg-slate-900 px-2 py-1 rounded border border-slate-800">RECORD</span>
                <span>→</span>
                <span className="bg-slate-900 px-2 py-1 rounded border border-slate-800">SUBMIT</span>
              </div>
              <p className="text-[11px] text-slate-500">Static single-point capture without active investigative guidance.</p>
            </div>

            <div className="p-4 rounded-2xl bg-gradient-to-br from-cyan-950/40 to-slate-950/70 border border-cyan-800/50 space-y-2">
              <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider font-semibold flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5" />
                AquaForensics Reasoning Loop
              </span>
              <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono text-cyan-300">
                <span className="bg-cyan-950/80 px-2 py-1 rounded border border-cyan-800">Observe</span>
                <span>→</span>
                <span className="bg-cyan-950/80 px-2 py-1 rounded border border-cyan-800">Hypotheses (W/L/N)</span>
                <span>→</span>
                <span className="bg-cyan-950/80 px-2 py-1 rounded border border-cyan-800 font-bold text-white shadow-sm shadow-cyan-500/20">Compute EIG</span>
                <span>→</span>
                <span className="bg-cyan-950/80 px-2 py-1 rounded border border-cyan-800">Next Evidence</span>
              </div>
              <p className="text-[11px] text-slate-400">Active entropy reduction guiding citizen observers where to look next.</p>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Scientific Disclaimer Banner */}
      <ScientificDisclaimer />

      {/* 3. Main Action Grid: Create Investigation & Live Investigations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8" id="new-investigation">
        {/* Left Column: Create Investigation Form (7 cols) */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 sm:p-8 backdrop-blur-xl shadow-2xl">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center border border-cyan-500/30">
                <Plus className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Initialize New Investigation</h2>
                <p className="text-xs text-slate-400 font-mono">Create evidence-guided investigation container</p>
              </div>
            </div>

            <span className="px-2.5 py-1 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60 text-[11px] font-mono">
              Bayesian v0.1
            </span>
          </div>

          {/* Quick Presets */}
          <div className="mt-5 space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-mono text-slate-300 uppercase font-semibold">
                Demo / Synthetic Location Presets (Simulated Scenarios):
              </label>
              <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-purple-950/80 text-purple-300 border border-purple-800/60">
                DEMO / SYNTHETIC
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {PRESET_LOCATIONS.map((preset) => (
                <button
                  key={preset.name}
                  type="button"
                  onClick={() => handleApplyPreset(preset)}
                  className="px-3 py-1.5 rounded-lg bg-slate-950 hover:bg-cyan-950/60 border border-slate-800 hover:border-cyan-700 text-xs text-slate-300 hover:text-cyan-300 font-mono transition-all flex items-center gap-1.5 group cursor-pointer"
                >
                  <MapPin className="w-3 h-3 text-cyan-400" />
                  <span>{preset.name.split(' - ')[0]}</span>
                  <span className="text-[9px] text-purple-400/80 group-hover:text-purple-300 font-sans ml-1">(Synthetic)</span>
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleCreateInvestigation} className="mt-6 space-y-4">
            {formError && (
              <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{formError}</span>
              </div>
            )}

            {/* Title */}
            <div>
              <label className="block text-xs font-mono font-semibold text-slate-300 uppercase mb-1">
                Investigation Title (Optional)
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. [DEMO] Thames Reach Turbidity Scenario"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white text-sm focus:border-cyan-500 focus:outline-none"
              />
            </div>

            {/* Anomaly Type & Reliability */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono font-semibold text-slate-300 uppercase mb-1">
                  Anomaly Type
                </label>
                <select
                  value={anomalyType}
                  onChange={(e) => setAnomalyType(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white text-sm focus:border-cyan-500 focus:outline-none"
                >
                  <option value="abnormal_water_aspect">abnormal_water_aspect</option>
                </select>
                <span className="text-[10px] text-slate-500 font-mono">
                  Primary OAH citizen science trigger
                </span>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-mono font-semibold text-slate-300 uppercase">
                    Observer Reliability
                  </label>
                  <span className="text-xs font-mono font-bold text-cyan-400">
                    {(observerReliability * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.50"
                  max="1.0"
                  step="0.05"
                  value={observerReliability}
                  onChange={(e) => setObserverReliability(parseFloat(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer mt-2"
                />
                <span className="text-[10px] text-slate-500 font-mono">
                  Reference reliability baseline
                </span>
              </div>
            </div>

            {/* Lat / Long Coordinates */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono font-semibold text-slate-300 uppercase mb-1">
                  Latitude (WGS84)
                </label>
                <input
                  type="text"
                  required
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  placeholder="51.5074"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-sm font-mono focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-semibold text-slate-300 uppercase mb-1">
                  Longitude (WGS84)
                </label>
                <input
                  type="text"
                  required
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  placeholder="-0.1278"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-sm font-mono focus:border-cyan-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Initial Observation Description */}
            <div>
              <label className="block text-xs font-mono font-semibold text-slate-300 uppercase mb-1">
                Initial Observation Notes
              </label>
              <textarea
                value={initialDescription}
                onChange={(e) => setInitialDescription(e.target.value)}
                rows={2}
                placeholder="Describe visual appearance, smell, flow state, or site context..."
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs focus:border-cyan-500 focus:outline-none"
              />
            </div>

            {/* Action Feasibility Overrides Toggle */}
            <div className="pt-2">
              <button
                type="button"
                onClick={() => setShowFeasibility(!showFeasibility)}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 font-mono transition-colors"
              >
                <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                <span>{showFeasibility ? 'Hide Feasibility Overrides' : 'Configure Action Feasibility (Advanced)'}</span>
              </button>

              {showFeasibility && (
                <div className="mt-3 p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
                  <p className="text-[11px] text-slate-400 font-mono">
                    Mark candidate actions infeasible (e.g. inaccessible upstream bridge) to test automatic EIG rerouting:
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                    {Object.values(ACTION_DEFINITIONS).map((act) => {
                      const isOverridden = feasibilityOverrides[act.id]?.feasible === false;
                      return (
                        <div
                          key={act.id}
                          className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between"
                        >
                          <span className="text-slate-300 text-[11px]">{act.id}</span>
                          <button
                            type="button"
                            onClick={() => handleToggleFeasibility(act.id, isOverridden, 'Physical access restricted')}
                            className={`px-2 py-0.5 rounded text-[10px] ${
                              isOverridden
                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            }`}
                          >
                            {isOverridden ? 'Infeasible' : 'Feasible'}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button
                type="submit"
                disabled={submitting}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-teal-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-slate-950 font-bold text-sm shadow-xl shadow-cyan-500/20 flex items-center justify-center gap-2 transition-all active:scale-95 cursor-pointer"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                    <span>Computing Baseline EIG Assessment...</span>
                  </>
                ) : (
                  <>
                    <span>Launch Investigation</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Recent Investigations Feed (5 cols) */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-xl shadow-2xl flex flex-col">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              <h2 className="text-base font-bold text-white">Recent Investigations</h2>
            </div>
            <button
              onClick={() => setRefreshTrigger(prev => prev + 1)}
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300"
            >
              Refresh
            </button>
          </div>

          <div className="mt-4 space-y-3 overflow-y-auto max-h-[580px] flex-1 pr-1">
            {loadingList && (
              <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
                <Loader2 className="w-5 h-5 animate-spin text-cyan-400" />
                <span className="text-xs font-mono">Loading cases...</span>
              </div>
            )}

            {!loadingList && investigations.length === 0 && (
              <div className="text-center py-12 text-slate-500 text-xs font-mono">
                No active investigations recorded. Create your first case on the left!
              </div>
            )}

            {!loadingList &&
              investigations.map((inv) => {
                const status = inv.latest_assessment?.status || 'ROBUST';
                const statusBadge = {
                  ROBUST: 'bg-emerald-950/80 border-emerald-500/40 text-emerald-300',
                  NEAR_TIE: 'bg-amber-950/80 border-amber-500/40 text-amber-300',
                  INSUFFICIENT_CONFIDENCE: 'bg-sky-950/80 border-sky-500/40 text-sky-300',
                  NO_FEASIBLE_ACTIONS: 'bg-slate-800 border-slate-700 text-slate-300'
                }[status] || 'bg-slate-800 border-slate-700 text-slate-300';

                return (
                  <Link
                    key={inv.id}
                    href={`/investigations/${inv.id}`}
                    className="block p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-cyan-600/60 hover:bg-slate-950/90 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-1.5 flex-1 min-w-0">
                        {inv.title?.toUpperCase().includes('DEMO') || inv.title?.toUpperCase().includes('SYNTHETIC') ? (
                          <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold rounded bg-purple-950/80 text-purple-300 border border-purple-800/60 shrink-0">
                            DEMO
                          </span>
                        ) : null}
                        <h3 className="text-sm font-semibold text-white group-hover:text-cyan-300 transition-colors truncate">
                          {inv.title}
                        </h3>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold shrink-0 border ${statusBadge}`}>
                        {status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                      <div className="flex items-center gap-1 text-[11px]">
                        <MapPin className="w-3 h-3 text-slate-500" />
                        <span>
                          {inv.latitude.toFixed(2)}, {inv.longitude.toFixed(2)}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-[11px]">
                        <span>{inv.observations_count} obs</span>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                      </div>
                    </div>
                  </Link>
                );
              })}
          </div>
        </div>
      </div>
    </div>
  );
}
