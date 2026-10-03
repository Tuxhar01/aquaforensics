'use client';

import React from 'react';
import { CandidateAction, ExcludedAction } from '@/lib/types';
import { ACTION_DEFINITIONS } from '@/lib/constants';
import { ListFilter, Ban, ArrowRight } from 'lucide-react';

interface CandidateActionsListProps {
  candidates: CandidateAction[];
  excludedActions: ExcludedAction[];
  onRecordAction: (actionId: string) => void;
}

export default function CandidateActionsList({
  candidates = [],
  excludedActions = [],
  onRecordAction
}: CandidateActionsListProps) {
  return (
    <div className="rounded-2xl border border-slate-800/80 bg-slate-900/70 p-5 sm:p-6 backdrop-blur-xl shadow-2xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <ListFilter className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-bold text-white tracking-wide">
            Candidate Actions Evaluation Matrix
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Ranked by Expected Information Gain (EIG)
        </span>
      </div>

      {/* Candidate Actions Table */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono">
              <th className="py-2.5 px-3">Action</th>
              <th className="py-2.5 px-3">Expected Info Gain</th>
              <th className="py-2.5 px-3">
                <div>Best-Action Support</div>
                <div className="text-[10px] text-slate-500 font-normal">Relative Decision Support</div>
              </th>
              <th className="py-2.5 px-3">Effort</th>
              <th className="py-2.5 px-3">Provenance</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {candidates.map((cand, idx) => {
              const actionId = (cand.action_id || cand.action || `action-${idx}`) as string;
              const meta = ACTION_DEFINITIONS[actionId];
              const eig = cand.nominal_eig_bits ?? cand.eig_bits ?? cand.expected_info_gain ?? 0;
              const pBest = cand.p_best_moderate ?? cand.p_best ?? 0;
              const effort = cand.effort_label ?? cand.effort ?? meta?.effort ?? 'medium';
              const isTop = idx === 0;

              return (
                <tr
                  key={actionId}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    isTop ? 'bg-cyan-950/20' : ''
                  }`}
                >
                  <td className="py-3 px-3">
                    <div className="font-semibold text-white">
                      {cand.label || meta?.label || actionId}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      id: {actionId}
                    </div>
                  </td>

                  <td className="py-3 px-3 font-mono font-bold text-cyan-300">
                    {eig.toFixed(4)} bits
                  </td>

                  <td className="py-3 px-3 font-mono text-slate-300">
                    <span title="Relative decision support under assumption-sensitivity perturbation">
                      {(pBest * 100).toFixed(1)}%
                    </span>
                    <span className="text-[10px] text-slate-500 block">rel. support</span>
                  </td>

                  <td className="py-3 px-3 text-slate-400 font-mono">
                    {effort}
                  </td>

                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                        cand.source_class === 'extension' || meta?.source_class === 'extension'
                          ? 'bg-purple-950/60 border-purple-800 text-purple-300'
                          : 'bg-cyan-950/60 border-cyan-800 text-cyan-300'
                      }`}
                      title={
                        cand.source_class === 'extension' || meta?.source_class === 'extension'
                          ? 'AquaForensics-specific extension observation'
                          : 'OAH-aligned (documented secondary survey field)'
                      }
                    >
                      {cand.source_class === 'extension' || meta?.source_class === 'extension'
                        ? 'AquaForensics Extension'
                        : 'OAH-Aligned'}
                    </span>
                  </td>

                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => onRecordAction(actionId)}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-cyan-600 text-slate-200 hover:text-white font-medium text-xs flex items-center gap-1 ml-auto transition-all active:scale-95 cursor-pointer"
                    >
                      <span>Record</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              );
            })}

            {candidates.length === 0 && (
              <tr>
                <td colSpan={6} className="py-4 text-center text-slate-500 font-mono">
                  No active candidate actions remaining in this cycle.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Excluded Actions Section */}
      {excludedActions.length > 0 && (
        <div className="mt-5 pt-4 border-t border-slate-800">
          <div className="flex items-center gap-2 mb-2 text-xs font-mono text-slate-400 font-semibold uppercase tracking-wider">
            <Ban className="w-3.5 h-3.5 text-slate-500" />
            <span>Excluded / Already Completed Actions</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {excludedActions.map((exc, idx) => {
              const actionId = (exc.action_id || exc.action || `exc-${idx}`) as string;
              const meta = ACTION_DEFINITIONS[actionId];
              return (
                <div
                  key={actionId}
                  className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/80 flex items-center justify-between text-xs"
                >
                  <div className="space-y-0.5">
                    <span className="font-medium text-slate-300">
                      {exc.label || meta?.label || actionId}
                    </span>
                    <div className="text-[11px] font-mono text-slate-500">
                      Reason: {exc.reason}
                    </div>
                  </div>
                  <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-900 border border-slate-800 text-slate-400">
                    Excluded
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
