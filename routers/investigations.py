"""
FastAPI Router for AquaForensics Investigation Endpoints.
"""
from fastapi import APIRouter, HTTPException, Path, Query, status
from typing import List, Dict, Any

from models import (
    InvestigationCreate,
    ObservationCreate,
    ActionCompleteRequest,
    InvestigationResponse,
    AssessmentResponse,
    TimelineEvent
)
from services import investigation_service

router = APIRouter(prefix="/api/investigations", tags=["Investigations"])

@router.get("", response_model=List[InvestigationResponse])
def list_investigations(limit: int = Query(default=50, ge=1, le=100)):
    """
    List recent investigations with their latest assessment and observation count.
    """
    return investigation_service.list_investigations(limit=limit)

@router.post("", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
def create_investigation(payload: InvestigationCreate):
    """
    Create a new AquaForensics environmental anomaly investigation.
    Fetches initial weather context and computes the baseline reasoning assessment.
    """
    try:
        return investigation_service.create_investigation(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create investigation: {str(e)}")

@router.post("/demo/init", response_model=InvestigationResponse)
@router.post("/demo/reset", response_model=InvestigationResponse)
def init_or_reset_demo():
    """
    Initializes or resets the deterministic synthetic demo investigation scenario.
    """
    try:
        return investigation_service.init_demo_investigation()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to init demo scenario: {str(e)}")

@router.get("/{id}", response_model=InvestigationResponse)
def get_investigation(id: str = Path(..., description="Investigation UUID")):
    """
    Retrieve an investigation by ID, including latest evidence state and assessment.
    """
    inv = investigation_service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation '{id}' not found")
    return inv

@router.post("/{id}/observations", response_model=InvestigationResponse)
def add_observation(payload: ObservationCreate, id: str = Path(..., description="Investigation UUID")):
    """
    Record a new evidence observation for an ongoing investigation and recalculate engine assessment.
    """
    try:
        return investigation_service.add_observation(id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add observation: {str(e)}")

@router.post("/{id}/assess", response_model=AssessmentResponse)
def rerun_assessment(id: str = Path(..., description="Investigation UUID"), seed: int = Query(default=0, description="RNG seed for sensitivity analysis")):
    """
    Re-run the Bayesian EIG reasoning assessment for an investigation.
    """
    inv = investigation_service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation '{id}' not found")
    
    with investigation_service.get_db() as conn:
        asm = investigation_service._reassess_investigation(conn, id, seed=seed)
    return asm

@router.get("/{id}/recommendation")
def get_recommendation(id: str = Path(..., description="Investigation UUID")):
    """
    Retrieve the current computed Next-Best-Evidence recommendation for an investigation.
    """
    rec = investigation_service.get_recommendation(id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation or recommendation for '{id}' not found")
    return rec

@router.post("/{id}/actions/{action_id}/complete")
def complete_action(
    payload: ActionCompleteRequest,
    id: str = Path(..., description="Investigation UUID"),
    action_id: str = Path(..., description="Candidate action ID to complete")
):
    """
    Complete a recommended candidate evidence action, recording the observation and triggering engine recalculation.
    """
    try:
        return investigation_service.complete_action(id, action_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to complete action: {str(e)}")

@router.get("/{id}/timeline", response_model=List[TimelineEvent])
def get_timeline(id: str = Path(..., description="Investigation UUID")):
    """
    Retrieve the complete chronological audit timeline for an investigation.
    """
    inv = investigation_service.get_investigation(id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation '{id}' not found")
    return investigation_service.get_timeline(id)

@router.get("/{id}/fhir")
def get_fhir_export(id: str = Path(..., description="Investigation UUID")):
    """
    Retrieve a FHIR-oriented structured export (HL7 FHIR R4 Bundle format) of the investigation.
    """
    fhir_bundle = investigation_service.get_fhir_export(id)
    if not fhir_bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation '{id}' not found")
    return fhir_bundle
