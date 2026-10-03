"""
AquaForensics Integration and API Test Suite.
Tests full lifecycle: Creation -> Observation -> Rerun Assessment -> Action Completion -> Timeline -> FHIR.
Uses FastAPI TestClient and an in-memory or temporary SQLite database.
"""
import os
import tempfile
import unittest
import numpy as np
from fastapi.testclient import TestClient

# Use a temporary database for testing
db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
db_file.close()
os.environ["AQUAFORENSICS_DB_PATH"] = db_file.name

from main import app
from database import init_db

class AquaForensicsBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(db_file.name):
            try:
                os.remove(db_file.name)
            except Exception:
                pass

    def test_01_root_and_health(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["project"], "AquaForensics")

        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")

    def test_02_create_investigation(self):
        payload = {
            "title": "Stream Turbidity Site A",
            "anomaly_type": "abnormal_water_aspect",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "initial_description": "Water looks unusually brownish and turbid after no rain.",
            "observer_reliability": 0.90
        }
        resp = self.client.post("/api/investigations", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], payload["title"])
        self.assertEqual(data["anomaly_type"], payload["anomaly_type"])
        self.assertIsNotNone(data["latest_assessment"])
        
        # Verify initial assessment status & structure
        asm = data["latest_assessment"]
        self.assertIn(asm["status"], ["ROBUST", "NEAR_TIE", "INSUFFICIENT_CONFIDENCE"])
        self.assertIn("evidence_support", asm)
        self.assertIn("assumption_sensitivity_band", asm)
        self.assertIn("candidates", asm)

    def test_03_get_investigation(self):
        # Create investigation
        payload = {"latitude": 48.8566, "longitude": 2.3522, "observer_reliability": 0.85}
        create_resp = self.client.post("/api/investigations", json=payload)
        inv_id = create_resp.json()["id"]

        # Retrieve investigation
        get_resp = self.client.get(f"/api/investigations/{inv_id}")
        self.assertEqual(get_resp.status_code, 200)
        data = get_resp.json()
        self.assertEqual(data["id"], inv_id)
        self.assertEqual(data["observer_reliability"], 0.85)

    def test_04_add_observation_and_reassess(self):
        # Create investigation
        create_resp = self.client.post("/api/investigations", json={"latitude": 40.7128, "longitude": -74.0060})
        inv_id = create_resp.json()["id"]
        initial_support = create_resp.json()["latest_assessment"]["evidence_support"]

        # Add an observation: upstream_view turbid
        obs_payload = {
            "action_id": "upstream_view",
            "outcome": True,
            "reliability": 0.90,
            "claimed_source": "oah",
            "notes": "Upstream photo shows brownish turbid water",
            "timestamp_min": 10.0
        }
        obs_resp = self.client.post(f"/api/investigations/{inv_id}/observations", json=obs_payload)
        self.assertEqual(obs_resp.status_code, 200)
        updated_inv = obs_resp.json()
        self.assertEqual(updated_inv["observations_count"], 1)

        # Evidence support should have updated
        updated_support = updated_inv["latest_assessment"]["evidence_support"]
        self.assertNotEqual(initial_support, updated_support)

        # Check adapter provenance downgrade for upstream_view claimed as oah
        prov = updated_inv["latest_assessment"]["evidence_provenance"]
        self.assertTrue(prov["uses_extension_evidence"])
        self.assertEqual(prov["observations"][0]["source"], "extension")

    def test_05_complete_action_flow(self):
        # Create investigation
        create_resp = self.client.post("/api/investigations", json={"latitude": 52.5200, "longitude": 13.4050})
        inv_id = create_resp.json()["id"]

        # Complete candidate action: recheck_60min
        action_payload = {
            "outcome": "still_abnormal",
            "reliability": 0.85,
            "claimed_source": "oah",
            "notes": "Rechecked after 60 min, water remains discolored"
        }
        action_resp = self.client.post(f"/api/investigations/{inv_id}/actions/recheck_60min/complete", json=action_payload)
        self.assertEqual(action_resp.status_code, 200)
        data = action_resp.json()
        self.assertEqual(data["action_id"], "recheck_60min")
        self.assertIn("latest_assessment", data)

    def test_06_recommendation_endpoint(self):
        create_resp = self.client.post("/api/investigations", json={"latitude": 41.9028, "longitude": 12.4964})
        inv_id = create_resp.json()["id"]

        rec_resp = self.client.get(f"/api/investigations/{inv_id}/recommendation")
        self.assertEqual(rec_resp.status_code, 200)
        data = rec_resp.json()
        self.assertIn("status", data)
        self.assertIn("recommendation", data)
        self.assertIn("candidates", data)

    def test_07_timeline_endpoint(self):
        create_resp = self.client.post("/api/investigations", json={"latitude": 37.7749, "longitude": -122.4194})
        inv_id = create_resp.json()["id"]

        # Add observation
        self.client.post(f"/api/investigations/{inv_id}/observations", json={
            "action_id": "second_downstream",
            "outcome": "normal_at_second_site"
        })

        timeline_resp = self.client.get(f"/api/investigations/{inv_id}/timeline")
        self.assertEqual(timeline_resp.status_code, 200)
        timeline = timeline_resp.json()
        self.assertGreaterEqual(len(timeline), 3) # created, assessment, observation, assessment
        event_types = [e["event_type"] for e in timeline]
        self.assertIn("investigation_created", event_types)
        self.assertIn("observation_recorded", event_types)
        self.assertIn("assessment_performed", event_types)

    def test_08_fhir_export(self):
        create_resp = self.client.post("/api/investigations", json={"latitude": 51.5074, "longitude": -0.1278})
        inv_id = create_resp.json()["id"]

        self.client.post(f"/api/investigations/{inv_id}/observations", json={
            "action_id": "inspect_pipes_works",
            "outcome": "not_found"
        })

        fhir_resp = self.client.get(f"/api/investigations/{inv_id}/fhir")
        self.assertEqual(fhir_resp.status_code, 200)
        bundle = fhir_resp.json()
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "collection")
        self.assertTrue(len(bundle["entry"]) >= 3)
        resource_types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        self.assertIn("DiagnosticReport", resource_types)
        self.assertIn("Observation", resource_types)
        self.assertIn("Device", resource_types)

    def test_09_invalid_inputs(self):
        # Invalid latitude
        resp = self.client.post("/api/investigations", json={"latitude": 150.0, "longitude": 0.0})
        self.assertEqual(resp.status_code, 422)

        # Invalid observer reliability
        resp = self.client.post("/api/investigations", json={"latitude": 0.0, "longitude": 0.0, "observer_reliability": 1.5})
        self.assertEqual(resp.status_code, 422)

        # Non-existent investigation
        resp = self.client.get("/api/investigations/non-existent-id")
        self.assertEqual(resp.status_code, 404)

        # Unknown action observation
        create_resp = self.client.post("/api/investigations", json={"latitude": 0.0, "longitude": 0.0})
        inv_id = create_resp.json()["id"]
        obs_resp = self.client.post(f"/api/investigations/{inv_id}/observations", json={
            "action_id": "invalid_action_name",
            "outcome": True
        })
        self.assertEqual(obs_resp.status_code, 400)

    def test_10_list_investigations(self):
        resp = self.client.get("/api/investigations")
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertIsInstance(items, list)
        self.assertGreaterEqual(len(items), 1)

    def test_11_rerun_assessment(self):
        create_resp = self.client.post("/api/investigations", json={"latitude": 45.0, "longitude": 9.0})
        inv_id = create_resp.json()["id"]
        assess_resp = self.client.post(f"/api/investigations/{inv_id}/assess?seed=42")
        self.assertEqual(assess_resp.status_code, 200)
        asm = assess_resp.json()
        self.assertIn("status", asm)
        self.assertIn("evidence_support", asm)
        self.assertIn("recommendation", asm)

    def test_12_demo_init_and_reset(self):
        # 1. Initialize demo
        init_resp = self.client.post("/api/investigations/demo/init")
        self.assertEqual(init_resp.status_code, 200)
        demo_inv = init_resp.json()
        self.assertEqual(demo_inv["id"], "demo-thames-scenario")
        self.assertEqual(demo_inv["observations_count"], 0)
        self.assertIn("latest_assessment", demo_inv)
        self.assertIn(demo_inv["latest_assessment"]["status"], ["ROBUST", "NEAR_TIE", "INSUFFICIENT_CONFIDENCE"])

        # 2. Add an observation
        obs_resp = self.client.post("/api/investigations/demo-thames-scenario/observations", json={
            "action_id": "upstream_view",
            "outcome": "upstream_turbid",
            "reliability": 0.90
        })
        self.assertEqual(obs_resp.status_code, 200)
        self.assertEqual(obs_resp.json()["observations_count"], 1)

        # 3. Reset demo
        reset_resp = self.client.post("/api/investigations/demo/reset")
        self.assertEqual(reset_resp.status_code, 200)
        reset_inv = reset_resp.json()
        self.assertEqual(reset_inv["id"], "demo-thames-scenario")
        self.assertEqual(reset_inv["observations_count"], 0)

    def test_13_candidate_and_recommendation_field_consistency(self):
        """Verify that candidates, excluded actions, and recommendation have consistent action_id and non-zero EIG values."""
        init_resp = self.client.post("/api/investigations/demo/init")
        self.assertEqual(init_resp.status_code, 200)
        asm = init_resp.json()["latest_assessment"]

        # 1. Candidates must have non-empty action_id and action
        candidates = asm.get("candidates", [])
        self.assertGreater(len(candidates), 0)
        for cand in candidates:
            self.assertIn("action_id", cand)
            self.assertIn("action", cand)
            self.assertTrue(bool(cand["action_id"]))
            self.assertEqual(cand["action_id"], cand["action"])
            # EIG should be populated and non-negative
            self.assertIn("eig_bits", cand)
            self.assertIn("nominal_eig_bits", cand)
            self.assertGreaterEqual(cand["eig_bits"], 0.0)
            self.assertEqual(cand["eig_bits"], cand["nominal_eig_bits"])
        
        # Verify top candidates have strictly positive EIG
        self.assertGreater(candidates[0]["eig_bits"], 0.0)

        # 2. Recommendation must have action identifiers
        rec = asm.get("recommendation", {})
        if asm["status"] == "ROBUST":
            self.assertIn("action_id", rec)
            self.assertTrue(bool(rec["action_id"]))
        elif asm["status"] == "NEAR_TIE":
            self.assertTrue("actions" in rec or "tie_actions" in rec or "action_set" in rec)
            action_list = rec.get("actions") or rec.get("tie_actions") or rec.get("action_set")
            self.assertIsInstance(action_list, list)
            self.assertGreaterEqual(len(action_list), 2)
            for act in action_list:
                self.assertIsInstance(act, str)
                self.assertTrue(bool(act))

if __name__ == "__main__":
    unittest.main(verbosity=2)
