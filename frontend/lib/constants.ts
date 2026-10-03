import { ActionDefinition } from './types';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export const ACTION_DEFINITIONS: Record<string, ActionDefinition> = {
  upstream_view: {
    id: 'upstream_view',
    label: 'Look upstream (water clarity upstream of the report site)',
    outcomes: ['upstream_turbid', 'upstream_not_turbid'],
    effort: 'medium',
    source_class: 'extension',
    field_status: 'AquaForensics extension (Unverified: upstream vantage photo not in official OAH native app schema)',
    description: 'Check water clarity upstream of the reported anomaly location to determine if discoloration originates further up-reach.'
  },
  recheck_60min: {
    id: 'recheck_60min',
    label: 'Re-observe the same site after about 60 minutes',
    outcomes: ['still_abnormal', 'no_longer_abnormal'],
    effort: 'low (time wait)',
    source_class: 'oah',
    field_status: 'OAH-aligned (Documented secondary: repeat water aspect assessment interval)',
    description: 'Re-observe the site after approximately 1 hour to test if the anomaly is transient/non-representative (N) or persistent.'
  },
  second_downstream: {
    id: 'second_downstream',
    label: 'Assess a second nearby location',
    outcomes: ['abnormal_at_second_site', 'normal_at_second_site'],
    effort: 'low',
    source_class: 'oah',
    field_status: 'OAH-aligned (Documented secondary: secondary reach observation location)',
    description: 'Inspect water condition at a second nearby reach location to distinguish reach-wide extent (W) from isolated local condition (L).'
  },
  inspect_pipes_works: {
    id: 'inspect_pipes_works',
    label: 'Check the reach for pipes, sewage or works',
    outcomes: ['found', 'not_found'],
    effort: 'low',
    source_class: 'oah',
    field_status: 'OAH-aligned (Documented secondary: native outfall/works survey questions)',
    description: 'Inspect the immediate riverbank/channel for direct outfall pipes, construction works, or active discharge points.'
  }
};

export const PRESET_LOCATIONS = [
  {
    name: 'London - Thames Reach Scenario',
    lat: 51.5074,
    lng: -0.1278,
    description: '[DEMO / SYNTHETIC DATA] Simulated urban stream turbidity report near concrete culvert discharge'
  },
  {
    name: 'Paris - Seine Reach Scenario',
    lat: 48.8566,
    lng: 2.3522,
    description: '[DEMO / SYNTHETIC DATA] Simulated discoloration reported following intermittent drizzle'
  },
  {
    name: 'Berlin - Spree Reach Scenario',
    lat: 52.5200,
    lng: 13.4050,
    description: '[DEMO / SYNTHETIC DATA] Simulated brownish aspect observed near stormwater junction'
  },
  {
    name: 'Rome - Tiber Reach Scenario',
    lat: 41.9028,
    lng: 12.4964,
    description: '[DEMO / SYNTHETIC DATA] Simulated sediment plume observed near perimeter works'
  },
  {
    name: 'Tokyo - Sumida Reach Scenario',
    lat: 35.6762,
    lng: 139.6503,
    description: '[DEMO / SYNTHETIC DATA] Simulated surface opacity change reported by morning patrol'
  }
];

export const SCIENTIFIC_HONESTY_DECLARATION = {
  title: 'Scientifically Honest Environmental Reasoning',
  core_thesis: '"AquaForensics does not ask AI to decide what happened. It asks what evidence we need to find out."',
  disclaimer: 'All numeric model scores represent assumption-sensitivity model support under expert-elicited engineering parameters (EXPERT_ELICITED_UNCALIBRATED), NOT calibrated real-world probabilities. Investigation states represent candidate hypotheses for triage, not confirmed causes or diagnoses.',
  states: {
    W: {
      name: 'Reach-wide / Upstream-Originating Condition (W)',
      description: 'The anomaly condition spans the wider river reach or originates upstream of the report site.'
    },
    L: {
      name: 'Local Source Condition (L)',
      description: 'The anomaly origin lies locally between the upstream observation viewpoint and the citizen report site.'
    },
    N: {
      name: 'Transient / Non-Representative Condition (N)',
      description: 'The condition is brief, non-persistent, or an observational artefact. (Not an environmental cause or confirmed pollution).'
    }
  }
};
