"""
FHIR Export Service for AquaForensics.
Generates FHIR-oriented structured export (HL7 FHIR R4 Bundle format)
preserving evidence provenance (OAH-native vs AquaForensics extension).

Note: This is a FHIR-oriented structured export format. It does NOT claim full
implementation-guide conformance without verified profiles.
"""
from typing import Dict, Any, List
import datetime

def export_investigation_to_fhir(
    investigation: Dict[str, Any],
    observations: List[Dict[str, Any]],
    latest_assessment: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Exports investigation, observations, and assessment state into a FHIR R4 Bundle.
    """
    bundle_id = f"bundle-{investigation['id']}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    
    entries = []

    # 1. Device resource representing AquaForensics Reasoning Engine
    engine_device = {
        "resourceType": "Device",
        "id": "aquaforensics-engine",
        "identifier": [
            {
                "system": "https://aquaforensics.org/device",
                "value": "aquaforensics-bayesian-eig-engine"
            }
        ],
        "deviceName": [
            {
                "name": "AquaForensics Evidence-Guided Reasoning Engine",
                "type": "user-friendly-name"
            }
        ],
        "version": [
            {
                "value": latest_assessment.get("provenance", {}).get("config_hash", "0.1-dev") if latest_assessment else "0.1-dev"
            }
        ]
    }
    entries.append({"fullUrl": f"urn:uuid:aquaforensics-engine", "resource": engine_device})

    # 2. Observation resources
    observation_refs = []
    for obs in observations:
        obs_id = f"obs-{obs['id']}"
        fhir_obs = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "environment",
                            "display": "Environmental Monitoring"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "https://oneaquahealth.org/codes",
                        "code": obs["action_id"],
                        "display": f"Observation Action: {obs['action_id']}"
                    }
                ],
                "text": obs["action_id"]
            },
            "effectiveDateTime": obs["observed_at"],
            "valueString": str(obs["outcome"]),
            "component": [
                {
                    "code": {"text": "observer_reliability"},
                    "valueQuantity": {"value": obs["reliability"], "unit": "score"}
                },
                {
                    "code": {"text": "source_class"},
                    "valueString": obs["source_class"]
                },
                {
                    "code": {"text": "claimed_source"},
                    "valueString": obs["claimed_source"]
                }
            ]
        }
        if obs.get("notes"):
            fhir_obs["note"] = [{"text": obs["notes"]}]
            
        entries.append({"fullUrl": f"urn:uuid:{obs_id}", "resource": fhir_obs})
        observation_refs.append({"reference": f"urn:uuid:{obs_id}", "display": f"Action {obs['action_id']}"})

    # 3. DiagnosticReport resource representing overall Investigation & Assessment
    diagnostic_report = {
        "resourceType": "DiagnosticReport",
        "id": f"report-{investigation['id']}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "ENV",
                        "display": "Environmental Anomaly Investigation"
                    }
                ]
            }
        ],
        "code": {
            "text": f"AquaForensics Anomaly Investigation: {investigation['anomaly_type']}"
        },
        "effectiveDateTime": investigation["created_at"],
        "issued": now,
        "result": observation_refs,
        "conclusion": (
            f"Investigation Status: {latest_assessment['status']}. "
            f"Recommendation: {latest_assessment.get('recommendation', {})}. "
            f"Disclaimer: Model-based evidence support under expert-elicited assumptions; NOT probabilities."
        ) if latest_assessment else f"Investigation status: {investigation['status']}",
        "extension": [
            {
                "url": "https://aquaforensics.org/fhir/StructureDefinition/evidence-support",
                "valueString": str(latest_assessment.get("evidence_support", {})) if latest_assessment else "{}"
            },
            {
                "url": "https://aquaforensics.org/fhir/StructureDefinition/provenance-notice",
                "valueString": "FHIR-oriented structured export. OAH-native vs AquaForensics extension provenance preserved."
            }
        ]
    }
    entries.append({"fullUrl": f"urn:uuid:report-{investigation['id']}", "resource": diagnostic_report})

    bundle = {
        "resourceType": "Bundle",
        "id": bundle_id,
        "meta": {
            "lastUpdated": now,
            "profile": ["https://aquaforensics.org/fhir/StructureDefinition/investigation-bundle"]
        },
        "type": "collection",
        "timestamp": now,
        "entry": entries
    }

    return bundle
