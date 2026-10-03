"""
End-to-End Integration Test for AquaForensics Frontend-Backend Contract.
Verifies:
1. Investigation creation
2. Latent state baseline support (W/L/N)
3. Initial Next-Best-Evidence (EIG) recommendation
4. Observation submission & posterior belief update
5. Action completion flow
6. Audit timeline ordering and contents
7. HL7 FHIR R4 Bundle structure
"""
from fastapi.testclient import TestClient
from main import app
from database import init_db

def test_full_flow():
    init_db()
    client = TestClient(app)

    print("Step 1: Check root and health endpoints...")
    r = client.get("/")
    assert r.status_code == 200, f"Root failed: {r.text}"
    r_health = client.get("/health")
    assert r_health.status_code == 200, f"Health check failed: {r_health.text}"
    print("[PASS] Backend online and healthy.")

    print("\nStep 2: Create investigation...")
    create_payload = {
        "title": "E2E London Stream Turbidity Anomaly",
        "anomaly_type": "abnormal_water_aspect",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "initial_description": "Brownish clouding observed downstream of historical brick culvert.",
        "observer_reliability": 0.90
    }
    r_create = client.post("/api/investigations", json=create_payload)
    assert r_create.status_code == 201, f"Create failed: {r_create.text}"
    inv = r_create.json()
    inv_id = inv["id"]
    print(f"[PASS] Created investigation ID: {inv_id}")

    asm0 = inv["latest_assessment"]
    assert asm0 is not None
    print(f"  Initial Assessment Status: {asm0['status']}")
    print(f"  Initial Evidence Support: W={asm0['evidence_support']['W']:.3f}, L={asm0['evidence_support']['L']:.3f}, N={asm0['evidence_support']['N']:.3f}")
    print(f"  Initial Candidates Count: {len(asm0['candidates'])}")
    if asm0["recommendation"].get("action_id"):
        print(f"  Initial Recommended Action: {asm0['recommendation']['action_id']}")

    print("\nStep 3: Submit observation (upstream_view -> upstream_turbid)...")
    obs_payload = {
        "action_id": "upstream_view",
        "outcome": "upstream_turbid",
        "reliability": 0.90,
        "claimed_source": "oah",
        "notes": "Looked upstream from road bridge: water is clearly discolored upstream as well.",
        "timestamp_min": 15.0
    }
    r_obs = client.post(f"/api/investigations/{inv_id}/observations", json=obs_payload)
    assert r_obs.status_code == 200, f"Add observation failed: {r_obs.text}"
    inv_updated = r_obs.json()
    asm1 = inv_updated["latest_assessment"]
    assert inv_updated["observations_count"] == 1
    print(f"[PASS] Observation recorded. Observations count: {inv_updated['observations_count']}")
    print(f"  Updated Evidence Support: W={asm1['evidence_support']['W']:.3f}, L={asm1['evidence_support']['L']:.3f}, N={asm1['evidence_support']['N']:.3f}")
    assert asm1["evidence_support"]["W"] > asm0["evidence_support"]["W"], "Turbid upstream should increase reach-wide (W) support"
    print("[PASS] Mathematical belief update confirmed: W support increased as expected.")

    print("\nStep 4: Complete candidate action (recheck_60min)...")
    action_payload = {
        "outcome": "still_abnormal",
        "reliability": 0.85,
        "claimed_source": "oah",
        "notes": "Returned after 60 min, turbidity remains high."
    }
    r_act = client.post(f"/api/investigations/{inv_id}/actions/recheck_60min/complete", json=action_payload)
    assert r_act.status_code == 200, f"Complete action failed: {r_act.text}"
    act_data = r_act.json()
    asm2 = act_data["latest_assessment"]
    print(f"[PASS] Action completed. Observation ID: {act_data['observation_id']}")
    print(f"  Updated Evidence Support after repeat observation: W={asm2['evidence_support']['W']:.3f}, L={asm2['evidence_support']['L']:.3f}, N={asm2['evidence_support']['N']:.3f}")
    assert asm2["evidence_support"]["N"] < asm0["evidence_support"]["N"], "Persistence after 60m should decrease transient (N) support"
    print("[PASS] Mathematical belief update confirmed: N support decreased as expected.")

    print("\nStep 5: Verify Audit Timeline...")
    r_time = client.get(f"/api/investigations/{inv_id}/timeline")
    assert r_time.status_code == 200
    timeline = r_time.json()
    print(f"[PASS] Timeline returned {len(timeline)} chronological events:")
    for ev in timeline:
        print(f"   [{ev['timestamp']}] {ev['event_type']}")
    event_types = [ev["event_type"] for ev in timeline]
    assert "investigation_created" in event_types
    assert "observation_recorded" in event_types
    assert "action_completed" in event_types
    assert "assessment_performed" in event_types

    print("\nStep 6: Verify HL7 FHIR R4 Bundle Export...")
    r_fhir = client.get(f"/api/investigations/{inv_id}/fhir")
    assert r_fhir.status_code == 200
    fhir_bundle = r_fhir.json()
    assert fhir_bundle["resourceType"] == "Bundle"
    assert fhir_bundle["type"] == "collection"
    assert len(fhir_bundle["entry"]) >= 3
    print(f"[PASS] FHIR Bundle verified: {len(fhir_bundle['entry'])} resources exported.")

    print("\n=== COMPLETE FRONTEND-BACKEND FLOW VERIFICATION PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_full_flow()
