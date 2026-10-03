"""
Pydantic data models for AquaForensics API schemas.
Strict validation for environmental investigation inputs and structured outputs.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator

class FeasibilityDetail(BaseModel):
    feasible: bool = True
    reason: Optional[str] = None

class InvestigationCreate(BaseModel):
    title: Optional[str] = Field(default=None, description="Short human-readable title for the investigation")
    anomaly_type: str = Field(default="abnormal_water_aspect", description="Anomaly type, currently abnormal_water_aspect")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude")
    initial_description: Optional[str] = Field(default=None, description="Observer notes or visual description")
    observer_reliability: float = Field(default=0.90, ge=0.0, le=1.0, description="Observer reliability score (0.0 to 1.0)")
    feasibility: Optional[Dict[str, FeasibilityDetail]] = Field(default=None, description="Optional action feasibility overrides")

    @field_validator("anomaly_type")
    @classmethod
    def validate_anomaly_type(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("anomaly_type must be a non-empty string")
        return v

class ObservationCreate(BaseModel):
    action_id: str = Field(..., description="Action identifier (e.g., recheck_60min, upstream_view)")
    outcome: Union[bool, str] = Field(..., description="Observed outcome (boolean indicator or outcome label)")
    reliability: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Observation specific reliability (0.0-1.0)")
    claimed_source: str = Field(default="oah", description="Source claim: 'oah' or 'extension'")
    notes: Optional[str] = Field(default=None, description="Optional observer notes")
    timestamp_min: Optional[float] = Field(default=None, description="Minutes relative to initial report")

    @field_validator("claimed_source")
    @classmethod
    def validate_claimed_source(cls, v: str) -> str:
        if v not in ("oah", "extension"):
            raise ValueError("claimed_source must be 'oah' or 'extension'")
        return v

class ActionCompleteRequest(BaseModel):
    outcome: Union[bool, str] = Field(..., description="Outcome of completed candidate action")
    reliability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    claimed_source: str = Field(default="oah")
    notes: Optional[str] = Field(default=None)
    timestamp_min: Optional[float] = Field(default=None)

class ObservationResponse(BaseModel):
    id: str
    investigation_id: str
    action_id: str
    outcome: Union[bool, str]
    reliability: float
    source_class: str
    claimed_source: str
    notes: Optional[str] = None
    timestamp_min: Optional[float] = None
    observed_at: str
    created_at: str

class AssessmentResponse(BaseModel):
    id: Optional[str] = None
    investigation_id: Optional[str] = None
    status: str
    recommendation: Dict[str, Any]
    reasons: List[str]
    evidence_support: Dict[str, float]
    assumption_sensitivity_band: Dict[str, List[float]]
    representativeness_support_N: float
    extent_split_W_given_representative: float
    labels_note: str
    candidates: List[Dict[str, Any]]
    excluded_actions: List[Dict[str, Any]]
    diagnostics: Dict[str, Any]
    belief_trace: List[Dict[str, Any]]
    evidence_provenance: Dict[str, Any]
    provenance: Dict[str, Any]
    created_at: Optional[str] = None

class ActionRecordResponse(BaseModel):
    id: str
    investigation_id: str
    action_id: str
    outcome: Union[bool, str]
    completed_at: str
    observation_id: Optional[str] = None

class InvestigationResponse(BaseModel):
    id: str
    title: str
    anomaly_type: str
    latitude: float
    longitude: float
    initial_description: Optional[str] = None
    observer_reliability: float
    status: str
    created_at: str
    updated_at: str
    latest_assessment: Optional[AssessmentResponse] = None
    observations_count: int = 0

class TimelineEvent(BaseModel):
    event_type: str  # "investigation_created", "observation_added", "assessment_performed", "action_completed"
    timestamp: str
    detail: Dict[str, Any]
