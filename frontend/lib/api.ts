import {
  InvestigationCreatePayload,
  InvestigationResponse,
  ObservationCreatePayload,
  ActionCompletePayload,
  AssessmentResponse,
  TimelineEvent
} from './types';
import { API_BASE_URL } from './constants';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<{ status: string; engine: string }> {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
    return handleResponse(res);
  },

  async listInvestigations(limit = 50): Promise<InvestigationResponse[]> {
    const res = await fetch(`${API_BASE_URL}/api/investigations?limit=${limit}`, { cache: 'no-store' });
    return handleResponse(res);
  },

  async getInvestigation(id: string): Promise<InvestigationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/${encodeURIComponent(id)}`, { cache: 'no-store' });
    return handleResponse(res);
  },

  async createInvestigation(payload: InvestigationCreatePayload): Promise<InvestigationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/investigations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async initDemoInvestigation(): Promise<InvestigationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/demo/init`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async resetDemoInvestigation(): Promise<InvestigationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/demo/reset`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async addObservation(investigationId: string, payload: ObservationCreatePayload): Promise<InvestigationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/${encodeURIComponent(investigationId)}/observations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  async completeAction(
    investigationId: string,
    actionId: string,
    payload: ActionCompletePayload
  ): Promise<{
    action_record_id: string;
    investigation_id: string;
    action_id: string;
    outcome: unknown;
    completed_at: string;
    observation_id: string;
    latest_assessment: AssessmentResponse;
  }> {
    const res = await fetch(
      `${API_BASE_URL}/api/investigations/${encodeURIComponent(investigationId)}/actions/${encodeURIComponent(actionId)}/complete`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    );
    return handleResponse(res);
  },

  async rerunAssessment(investigationId: string, seed = 0): Promise<AssessmentResponse> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/${encodeURIComponent(investigationId)}/assess?seed=${seed}`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async getRecommendation(investigationId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/${encodeURIComponent(investigationId)}/recommendation`, {
      cache: 'no-store'
    });
    return handleResponse(res);
  },

  async getTimeline(investigationId: string): Promise<TimelineEvent[]> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/${encodeURIComponent(investigationId)}/timeline`, {
      cache: 'no-store'
    });
    return handleResponse(res);
  },

  async getFhirExport(investigationId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${API_BASE_URL}/api/investigations/${encodeURIComponent(investigationId)}/fhir`, {
      cache: 'no-store'
    });
    return handleResponse(res);
  }
};
