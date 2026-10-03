'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { InvestigationResponse } from '@/lib/types';
import StateSupportCard from '@/components/StateSupportCard';
import RecommendationCard from '@/components/RecommendationCard';
import CandidateActionsList from '@/components/CandidateActionsList';
import RecordObservationModal from '@/components/RecordObservationModal';
import AuditTimelineModal from '@/components/AuditTimelineModal';
import FhirExportModal from '@/components/FhirExportModal';
import ScientificDisclaimer from '@/components/ScientificDisclaimer';
import {
  ArrowLeft,
  RefreshCw,
  PlusCircle,
  History,
  FileCode,
  MapPin,
  Clock,
  ShieldCheck,
  Droplets,
  AlertCircle,
  Loader2
} from 'lucide-react';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function InvestigationDashboard({ params }: PageProps) {
  const resolvedParams = use(params);
  const investigationId = resolvedParams.id;

  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [reassessing, setReassessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Modals
  const [recordModalOpen, setRecordModalOpen] = useState(false);
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const [timelineModalOpen, setTimelineModalOpen] = useState(false);
  const [fhirModalOpen, setFhirModalOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const loadInvestigation = async () => {
      try {
        setError(null);
        const data = await api.getInvestigation(investigationId);
        if (isMounted) setInvestigation(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to load investigation';
        if (isMounted) setError(msg);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    loadInvestigation();
    return () => {
      isMounted = false;
    };
  }, [investigationId, refreshTrigger]);

  const [resettingDemo, setResettingDemo] = useState(false);

  const handleResetDemo = async () => {
    if (!confirm('Reset this demo investigation to its clean initial baseline state?')) return;
    setResettingDemo(true);
    try {
      const resetInv = await api.resetDemoInvestigation();
      setInvestigation(resetInv);
      setRefreshTrigger(prev => prev + 1);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Demo reset failed';
      alert(`Demo reset failed: ${msg}`);
    } finally {
      setResettingDemo(false);
    }
  };

  const handleReassess = async () => {
    setReassessing(true);
    try {
      const updatedAsm = await api.rerunAssessment(investigationId);
      if (investigation) {
        setInvestigation({
          ...investigation,
          latest_assessment: updatedAsm
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Re-assessment failed';
      alert(`Re-assessment failed: ${msg}`);
    } finally {
      setReassessing(false);
    }
  };

  const handleOpenRecordObservation = (actionId?: string) => {
    setSelectedActionId(actionId || null);
    setRecordModalOpen(true);
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 flex flex-col items-center justify-center gap-4 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
        <p className="text-sm font-mono">Loading investigation assessment &amp; EIG state...</p>
      </div>
    );
  }

  if (error || !investigation) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-rose-950/60 border border-rose-500/40 text-rose-400 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold text-white">Investigation Not Found</h1>
        <p className="text-sm text-slate-400 font-mono">{error || 'Unknown error occurred'}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Investigations</span>
        </Link>
      </div>
    );
  }

  const assessment = investigation.latest_assessment;
  const status = assessment?.status || 'ROBUST';

  const statusBadge = {
    ROBUST: 'bg-emerald-950/80 border-emerald-500/40 text-emerald-300',
    NEAR_TIE: 'bg-amber-950/80 border-amber-500/40 text-amber-300',
    INSUFFICIENT_CONFIDENCE: 'bg-sky-950/80 border-sky-500/40 text-sky-300',
    NO_FEASIBLE_ACTIONS: 'bg-slate-800 border-slate-700 text-slate-300'
  }[status] || 'bg-slate-800 border-slate-700 text-slate-300';

  const isDemoCase = investigation.id === 'demo-thames-scenario' || investigation.title?.toUpperCase().includes('DEMO');

  // Determine which state has highest support
  const supportEntries: [string, number][] = assessment?.evidence_support
    ? (Object.entries(assessment.evidence_support) as [string, number][])
    : [];
  const topState: [string, number] = supportEntries.length > 0
    ? supportEntries.reduce((a, b) => (b[1] > a[1] ? b : a), ['W', 0])
    : ['W', 0];
  const topStateLabel = {
    W: 'Reach-wide / Upstream-Originating Condition (W)',
    L: 'Local Source Condition (L)',
    N: 'Transient / Non-Representative Condition (N)'
  }[topState[0]] || topState[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10 space-y-8">
      {/* 1. Header & Navigation Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="inline-flex items-center gap-1 text-xs font-mono text-cyan-400 hover:text-cyan-300 transition-colors mr-2"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Cases</span>
            </Link>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase border ${statusBadge}`}>
              {status}
            </span>
            {isDemoCase && (
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-950/80 text-purple-300 border border-purple-800/60">
                DEMO / SYNTHETIC DATA
              </span>
            )}
            <span className="text-xs font-mono text-slate-500">
              ID: {investigation.id.slice(0, 8)}...
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {investigation.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
            <div className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-cyan-400" />
              <span>
                {investigation.latitude.toFixed(4)}, {investigation.longitude.toFixed(4)}
              </span>
            </div>

            <div className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>Created {new Date(investigation.created_at).toLocaleDateString()}</span>
            </div>

            <div className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Observer Reliability: {(investigation.observer_reliability * 100).toFixed(0)}%</span>
            </div>

            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              <span className="font-bold text-white">{investigation.observations_count} Observations Recorded</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-center">
          {isDemoCase && (
            <button
              onClick={handleResetDemo}
              disabled={resettingDemo}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-purple-950/70 hover:bg-purple-900/80 border border-purple-700/60 text-purple-200 text-xs font-mono transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${resettingDemo ? 'animate-spin text-purple-300' : 'text-purple-400'}`} />
              <span>{resettingDemo ? 'Resetting...' : 'Reset Demo'}</span>
            </button>
          )}

          <button
            onClick={() => handleOpenRecordObservation()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs shadow-md shadow-cyan-600/20 active:scale-95 transition-all cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Record Observation</span>
          </button>

          <button
            onClick={handleReassess}
            disabled={reassessing}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reassessing ? 'animate-spin text-cyan-400' : ''}`} />
            <span>{reassessing ? 'Assessing...' : 'Re-assess'}</span>
          </button>

          <button
            onClick={() => setTimelineModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono transition-all active:scale-95 cursor-pointer"
          >
            <History className="w-3.5 h-3.5 text-cyan-400" />
            <span>Timeline</span>
          </button>

          <button
            onClick={() => setFhirModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-mono transition-all active:scale-95 cursor-pointer"
          >
            <FileCode className="w-3.5 h-3.5 text-emerald-400" />
            <span>FHIR Export</span>
          </button>
        </div>
      </div>

      {/* 2. Scientific Honesty Compact Banner */}
      <ScientificDisclaimer compact />

      {/* 3. Initial Anomaly Report Card */}
      {investigation.initial_description && (
        <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
          <Droplets className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Initial Citizen Observation Report:
            </span>
            <p className="text-sm text-slate-200 italic leading-relaxed">
              &ldquo;{investigation.initial_description}&rdquo;
            </p>
          </div>
        </div>
      )}

      {/* 4. Investigation Updated - What Changed? Callout (When Observations Recorded) */}
      {investigation.observations_count > 0 && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-cyan-950/60 via-slate-900/80 to-slate-950 border border-cyan-500/40 space-y-2 animate-in fade-in duration-300">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              INVESTIGATION UPDATED
            </span>
            <h3 className="text-sm font-bold text-white">
              What Changed After New Evidence?
            </h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {investigation.observations_count} observation(s) incorporated into the Bayesian reasoning engine. Current evidence increasingly supports <strong>{topStateLabel}</strong> (Model support: {topState[1].toFixed(2)}).
          </p>
          <p className="text-[11px] text-slate-400 font-mono italic border-l-2 border-cyan-500 pl-3 pt-0.5">
            Scientific boundary reminder: The specific environmental cause remains undetermined.
          </p>
        </div>
      )}

      {/* 5. Hero Section: Next-Best-Evidence Recommendation Card */}
      <RecommendationCard
        assessment={assessment}
        onRecordAction={(actionId) => handleOpenRecordObservation(actionId)}
      />

      {/* 6. Latent States & Competing Hypotheses Support Card */}
      <StateSupportCard assessment={assessment} />

      {/* 7. Candidate Actions Evaluation Matrix */}
      <CandidateActionsList
        candidates={assessment?.candidates || []}
        excludedActions={assessment?.excluded_actions || []}
        onRecordAction={(actionId) => handleOpenRecordObservation(actionId)}
      />

      {/* 7. Engine Provenance & Scientific Transparency Details */}
      {assessment?.provenance && (
        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-mono text-slate-400 font-semibold uppercase">
              Engine Provenance &amp; Mathematical Trace
            </span>
            <span className="text-[11px] font-mono text-cyan-400">
              {assessment.provenance.parameter_status}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono text-slate-400">
            <div>
              <span className="text-slate-500">Engine Version:</span>{' '}
              <strong className="text-slate-300">{assessment.provenance.engine_version}</strong>
            </div>
            <div>
              <span className="text-slate-500">Config Version:</span>{' '}
              <strong className="text-slate-300">{assessment.provenance.config_version || '0.1-dev'}</strong>
            </div>
            <div>
              <span className="text-slate-500">Uses Extension Evidence:</span>{' '}
              <strong className={assessment.evidence_provenance?.uses_extension_evidence ? 'text-purple-400' : 'text-emerald-400'}>
                {assessment.evidence_provenance?.uses_extension_evidence ? 'YES (AquaForensics extension evidence included)' : 'NO (100% OAH-Aligned)'}
              </strong>
            </div>
          </div>
        </div>
      )}

      {/* 8. Modals */}
      <RecordObservationModal
        isOpen={recordModalOpen}
        onClose={() => setRecordModalOpen(false)}
        investigationId={investigation.id}
        defaultActionId={selectedActionId}
        defaultReliability={investigation.observer_reliability}
        onObservationAdded={() => setRefreshTrigger(prev => prev + 1)}
      />

      <AuditTimelineModal
        isOpen={timelineModalOpen}
        onClose={() => setTimelineModalOpen(false)}
        investigationId={investigation.id}
      />

      <FhirExportModal
        isOpen={fhirModalOpen}
        onClose={() => setFhirModalOpen(false)}
        investigationId={investigation.id}
      />
    </div>
  );
}
