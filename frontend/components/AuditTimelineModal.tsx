'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { TimelineEvent } from '@/lib/types';
import {
  X,
  History,
  FileCheck,
  Eye,
  CheckCircle,
  Activity,
  ChevronDown,
  ChevronUp,
  Loader2
} from 'lucide-react';

interface AuditTimelineModalProps {
  isOpen: boolean;
  onClose: () => void;
  investigationId: string;
}

export default function AuditTimelineModal({
  isOpen,
  onClose,
  investigationId
}: AuditTimelineModalProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    let isMounted = true;
    const fetchTimeline = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getTimeline(investigationId);
        if (isMounted) setEvents(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to load timeline';
        if (isMounted) setError(msg);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchTimeline();
    return () => {
      isMounted = false;
    };
  }, [isOpen, investigationId]);

  if (!isOpen) return null;

  const getEventMeta = (type: string) => {
    switch (type) {
      case 'investigation_created':
        return {
          label: 'Investigation Created',
          color: 'text-cyan-400',
          bg: 'bg-cyan-950/80 border-cyan-800 text-cyan-300',
          icon: FileCheck
        };
      case 'observation_recorded':
        return {
          label: 'Observation Recorded',
          color: 'text-blue-400',
          bg: 'bg-blue-950/80 border-blue-800 text-blue-300',
          icon: Eye
        };
      case 'action_completed':
        return {
          label: 'Action Completed',
          color: 'text-emerald-400',
          bg: 'bg-emerald-950/80 border-emerald-800 text-emerald-300',
          icon: CheckCircle
        };
      case 'assessment_performed':
        return {
          label: 'Assessment Computed',
          color: 'text-purple-400',
          bg: 'bg-purple-950/80 border-purple-800 text-purple-300',
          icon: Activity
        };
      default:
        return {
          label: type,
          color: 'text-slate-400',
          bg: 'bg-slate-900 border-slate-700 text-slate-300',
          icon: History
        };
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center border border-cyan-500/30">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Investigation Audit Timeline</h2>
              <p className="text-xs text-slate-400 font-mono">Immutable chronological event stream</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Timeline Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {loading && (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
              <span className="text-xs font-mono">Loading investigation history...</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs">
              {error}
            </div>
          )}

          {!loading && !error && events.length === 0 && (
            <div className="text-center py-10 text-slate-500 text-xs font-mono">
              No timeline events recorded yet.
            </div>
          )}

          {!loading && !error && events.length > 0 && (
            <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {events.map((ev, idx) => {
                const meta = getEventMeta(ev.event_type);
                const Icon = meta.icon;
                const isExpanded = expandedIndex === idx;
                const detail = ev.detail as Record<string, unknown>;

                return (
                  <div key={idx} className="relative group">
                    {/* Node Dot */}
                    <div className="absolute -left-[27px] top-1.5 w-6 h-6 rounded-full bg-slate-950 border border-slate-700 flex items-center justify-center">
                      <Icon className={`w-3.5 h-3.5 ${meta.color}`} />
                    </div>

                    {/* Event Card */}
                    <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${meta.bg}`}>
                            {meta.label}
                          </span>
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">
                          {new Date(ev.timestamp).toLocaleString()}
                        </span>
                      </div>

                      {/* Detail summary preview */}
                      <div className="text-xs text-slate-300 space-y-1">
                        {ev.event_type === 'investigation_created' && (
                          <div>
                            <span className="text-slate-400">Location:</span> ({Number(detail.latitude)?.toFixed(4)}, {Number(detail.longitude)?.toFixed(4)}) |{' '}
                            <span className="text-slate-400">Observer Reliability:</span> {(Number(detail.observer_reliability) * 100).toFixed(0)}%
                          </div>
                        )}

                        {ev.event_type === 'observation_recorded' && (
                          <div>
                            <span className="text-slate-400">Action:</span> <strong className="text-cyan-300">{String(detail.action_id)}</strong> → Outcome:{' '}
                            <strong className="text-white">{String(detail.outcome)}</strong> ({String(detail.source_class)})
                          </div>
                        )}

                        {ev.event_type === 'assessment_performed' && (
                          <div>
                            <span className="text-slate-400">Status:</span> <strong className="text-purple-300">{String(detail.status)}</strong>
                          </div>
                        )}
                      </div>

                      {/* Expandable JSON Detail */}
                      <div className="mt-3 pt-2 border-t border-slate-900 flex justify-end">
                        <button
                          onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                          className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
                        >
                          <span>{isExpanded ? 'Hide Raw Payload' : 'Inspect Raw Payload'}</span>
                          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </button>
                      </div>

                      {isExpanded && (
                        <pre className="mt-2 p-3 rounded-lg bg-slate-950 text-[11px] font-mono text-slate-300 overflow-x-auto border border-slate-800">
                          {JSON.stringify(ev.detail, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 flex justify-end bg-slate-950/60">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
