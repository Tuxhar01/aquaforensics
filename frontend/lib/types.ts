export type AnomalyType = 'abnormal_water_aspect';

export type AssessmentStatus = 'ROBUST' | 'NEAR_TIE' | 'INSUFFICIENT_CONFIDENCE' | 'NO_FEASIBLE_ACTIONS';

export interface FeasibilityDetail {
  feasible: boolean;
  reason?: string;
}

export interface InvestigationCreatePayload {
  title?: string;
  anomaly_type?: string;
  latitude: number;
  longitude: number;
  initial_description?: string;
  observer_reliability?: number;
  feasibility?: Record<string, FeasibilityDetail>;
}

export interface ObservationCreatePayload {
  action_id: string;
  outcome: boolean | string;
  reliability?: number;
  claimed_source?: 'oah' | 'extension';
  notes?: string;
  timestamp_min?: number;
}

export interface ActionCompletePayload {
  outcome: boolean | string;
  reliability?: number;
  claimed_source?: 'oah' | 'extension';
  notes?: string;
  timestamp_min?: number;
}

export interface CandidateAction {
  action_id: string;
  action?: string;
  label?: string;
  eig_bits?: number;
  nominal_eig_bits?: number;
  expected_info_gain?: number;
  effort?: string;
  effort_label?: string;
  source_class?: string;
  p_best?: number;
  p_best_moderate?: number;
  p_best_diffuse?: number;
  rank?: number;
  robust_margin?: number;
  outcomes?: string[];
  field_status?: string;
  [key: string]: unknown;
}

export interface ExcludedAction {
  action_id: string;
  action?: string;
  reason: string;
  label?: string;
}

export interface RecommendationObject {
  action_id?: string;
  action?: string;
  actions?: string[];
  type?: string;
  label?: string;
  action_set?: string[];
  labels?: string[];
  reason?: string;
  eig_bits?: number;
  margin?: number;
  tie_actions?: string[];
  [key: string]: unknown;
}

export interface AssessmentResponse {
  id?: string;
  investigation_id?: string;
  status: AssessmentStatus;
  recommendation: RecommendationObject;
  reasons: string[];
  evidence_support: {
    W: number;
    L: number;
    N: number;
    [key: string]: number;
  };
  assumption_sensitivity_band: {
    W: [number, number];
    L: [number, number];
    N: [number, number];
    [key: string]: [number, number];
  };
  representativeness_support_N: number;
  extent_split_W_given_representative: number;
  labels_note: string;
  candidates: CandidateAction[];
  excluded_actions: ExcludedAction[];
  diagnostics: {
    entropy_bits?: number;
    regime_results?: Record<string, unknown>;
    validity_checks?: Record<string, unknown>;
    [key: string]: unknown;
  };
  belief_trace: Array<{
    step: number;
    action?: string;
    outcome?: unknown;
    support: { W: number; L: number; N: number };
  }>;
  evidence_provenance: {
    uses_extension_evidence: boolean;
    observations: Array<{
      action: string;
      source: string;
      claimed: string;
      warnings?: string[];
    }>;
  };
  provenance: {
    engine_version: string;
    config_version?: string;
    config_hash?: string;
    parameter_status: string;
    generated_at?: string;
  };
  created_at?: string;
}

export interface InvestigationResponse {
  id: string;
  title: string;
  anomaly_type: string;
  latitude: number;
  longitude: number;
  initial_description?: string | null;
  observer_reliability: number;
  status: string;
  created_at: string;
  updated_at: string;
  latest_assessment: AssessmentResponse | null;
  observations_count: number;
}

export interface TimelineEvent {
  event_type: 'investigation_created' | 'observation_recorded' | 'action_completed' | 'assessment_performed';
  timestamp: string;
  detail: Record<string, unknown>;
}

export interface ActionDefinition {
  id: string;
  label: string;
  outcomes: string[];
  effort: string;
  source_class: 'oah' | 'extension';
  field_status: string;
  description: string;
}
