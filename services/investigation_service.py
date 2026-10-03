"""
Core Investigation Service for AquaForensics.
Handles database operations, observation recording, engine assessments, audit timeline,
and FHIR exports.
"""
import uuid
import json
import datetime
from typing import Dict, Any, List, Optional

from database import get_db
from models import InvestigationCreate, ObservationCreate, ActionCompleteRequest
from services.weather_service import fetch_weather_context
from services.engine_service import run_investigation_assessment
from services.fhir_exporter import export_investigation_to_fhir
import engine

def _get_utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

def create_investigation(data: InvestigationCreate) -> Dict[str, Any]:
    inv_id = str(uuid.uuid4())
    now = _get_utc_now()
    title = data.title or f"Investigation at ({data.latitude:.4f}, {data.longitude:.4f})"
    
    # Fetch weather context
    weather_ctx = fetch_weather_context(data.latitude, data.longitude)
    
    # Run initial engine assessment
    engine_input, assessment_output = run_investigation_assessment(
        anomaly_type=data.anomaly_type,
        observer_reliability=data.observer_reliability,
        context=weather_ctx,
        observations=[],
        feasibility=data.feasibility.model_dump() if data.feasibility else None
    )

    assessment_id = str(uuid.uuid4())
    config_hash = assessment_output.get("provenance", {}).get("config_hash", "0.1-dev")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO investigations (
                id, title, anomaly_type, latitude, longitude, initial_description,
                observer_reliability, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """, (
            inv_id, title, data.anomaly_type, data.latitude, data.longitude,
            data.initial_description, data.observer_reliability, now, now
        ))

        cursor.execute("""
            INSERT INTO assessments (
                id, investigation_id, engine_version, config_version,
                input_snapshot, output_snapshot, created_at
            ) VALUES (?, ?, '0.1-dev', ?, ?, ?, ?)
        """, (
            assessment_id, inv_id, config_hash,
            json.dumps(engine_input), json.dumps(assessment_output), now
        ))

    assessment_output["id"] = assessment_id
    assessment_output["investigation_id"] = inv_id
    assessment_output["created_at"] = now

    return {
        "id": inv_id,
        "title": title,
        "anomaly_type": data.anomaly_type,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "initial_description": data.initial_description,
        "observer_reliability": data.observer_reliability,
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "latest_assessment": assessment_output,
        "observations_count": 0
    }

DEMO_SCENARIO_ID = "demo-thames-scenario"

def init_demo_investigation() -> Dict[str, Any]:
    """
    Initializes or resets the deterministic synthetic demo investigation.
    Wipes prior demo observation artifacts and computes fresh baseline assessment.
    """
    inv_id = DEMO_SCENARIO_ID
    now = _get_utc_now()
    title = "[DEMO / SYNTHETIC DATA] Thames Reach Turbidity Scenario"
    anomaly_type = "abnormal_water_aspect"
    lat = 51.5074
    lon = -0.1278
    desc = "[DEMO / SYNTHETIC DATA] Citizen observed brownish clouding and suspended turbidity near brick culvert discharge after dry conditions."
    reliability = 0.90

    weather_ctx = fetch_weather_context(lat, lon)

    # Compute baseline reasoning assessment from real engine
    engine_input, assessment_output = run_investigation_assessment(
        anomaly_type=anomaly_type,
        observer_reliability=reliability,
        context=weather_ctx,
        observations=[],
        feasibility=None
    )

    assessment_id = str(uuid.uuid4())
    config_hash = assessment_output.get("provenance", {}).get("config_hash", "0.1-dev")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM observations WHERE investigation_id = ?", (inv_id,))
        cursor.execute("DELETE FROM action_records WHERE investigation_id = ?", (inv_id,))
        cursor.execute("DELETE FROM assessments WHERE investigation_id = ?", (inv_id,))
        cursor.execute("DELETE FROM investigations WHERE id = ?", (inv_id,))

        cursor.execute("""
            INSERT INTO investigations (
                id, title, anomaly_type, latitude, longitude, initial_description,
                observer_reliability, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """, (
            inv_id, title, anomaly_type, lat, lon, desc, reliability, now, now
        ))

        cursor.execute("""
            INSERT INTO assessments (
                id, investigation_id, engine_version, config_version,
                input_snapshot, output_snapshot, created_at
            ) VALUES (?, ?, '0.1-dev', ?, ?, ?, ?)
        """, (
            assessment_id, inv_id, config_hash,
            json.dumps(engine_input), json.dumps(assessment_output), now
        ))

    assessment_output["id"] = assessment_id
    assessment_output["investigation_id"] = inv_id
    assessment_output["created_at"] = now

    return {
        "id": inv_id,
        "title": title,
        "anomaly_type": anomaly_type,
        "latitude": lat,
        "longitude": lon,
        "initial_description": desc,
        "observer_reliability": reliability,
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "latest_assessment": assessment_output,
        "observations_count": 0
    }

def get_investigation(investigation_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM investigations WHERE id = ?", (investigation_id,))
        inv_row = cursor.fetchone()
        if not inv_row:
            return None

        inv = dict(inv_row)
        
        # Get count of observations
        cursor.execute("SELECT COUNT(*) as cnt FROM observations WHERE investigation_id = ?", (investigation_id,))
        inv["observations_count"] = cursor.fetchone()["cnt"]

        # Get latest assessment
        cursor.execute("""
            SELECT * FROM assessments WHERE investigation_id = ? ORDER BY created_at DESC LIMIT 1
        """, (investigation_id,))
        asm_row = cursor.fetchone()
        if asm_row:
            asm_data = json.loads(asm_row["output_snapshot"])
            asm_data["id"] = asm_row["id"]
            asm_data["investigation_id"] = investigation_id
            asm_data["created_at"] = asm_row["created_at"]
            inv["latest_assessment"] = asm_data
        else:
            inv["latest_assessment"] = None

        return inv

def list_investigations(limit: int = 50) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM investigations ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            inv = dict(row)
            cursor.execute("SELECT COUNT(*) as cnt FROM observations WHERE investigation_id = ?", (inv["id"],))
            inv["observations_count"] = cursor.fetchone()["cnt"]

            cursor.execute("""
                SELECT * FROM assessments WHERE investigation_id = ? ORDER BY created_at DESC LIMIT 1
            """, (inv["id"],))
            asm_row = cursor.fetchone()
            if asm_row:
                asm_data = json.loads(asm_row["output_snapshot"])
                asm_data["id"] = asm_row["id"]
                asm_data["investigation_id"] = inv["id"]
                asm_data["created_at"] = asm_row["created_at"]
                inv["latest_assessment"] = asm_data
            else:
                inv["latest_assessment"] = None
            results.append(inv)
        return results

def _reassess_investigation(conn, investigation_id: str, seed: int = 0) -> Dict[str, Any]:
    """Helper to recalculate assessment for an investigation inside a DB session."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investigations WHERE id = ?", (investigation_id,))
    inv = dict(cursor.fetchone())

    # Get all recorded observations
    cursor.execute("""
        SELECT * FROM observations WHERE investigation_id = ? ORDER BY created_at ASC
    """, (investigation_id,))
    obs_rows = [dict(r) for r in cursor.fetchall()]

    weather_ctx = fetch_weather_context(inv["latitude"], inv["longitude"])
    
    engine_input, assessment_output = run_investigation_assessment(
        anomaly_type=inv["anomaly_type"],
        observer_reliability=inv["observer_reliability"],
        context=weather_ctx,
        observations=obs_rows,
        seed=seed
    )

    now = _get_utc_now()
    assessment_id = str(uuid.uuid4())
    config_hash = assessment_output.get("provenance", {}).get("config_hash", "0.1-dev")

    cursor.execute("""
        INSERT INTO assessments (
            id, investigation_id, engine_version, config_version,
            input_snapshot, output_snapshot, created_at
        ) VALUES (?, ?, '0.1-dev', ?, ?, ?, ?)
    """, (
        assessment_id, investigation_id, config_hash,
        json.dumps(engine_input), json.dumps(assessment_output), now
    ))

    cursor.execute("UPDATE investigations SET updated_at = ? WHERE id = ?", (now, investigation_id))

    assessment_output["id"] = assessment_id
    assessment_output["investigation_id"] = investigation_id
    assessment_output["created_at"] = now
    return assessment_output

def add_observation(investigation_id: str, data: ObservationCreate) -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM investigations WHERE id = ?", (investigation_id,))
        inv_row = cursor.fetchone()
        if not inv_row:
            raise ValueError(f"Investigation {investigation_id} not found")
        inv = dict(inv_row)

        obs_id = str(uuid.uuid4())
        now = _get_utc_now()
        reliability = data.reliability if data.reliability is not None else inv["observer_reliability"]
        
        # Verify action via engine adapter normalization
        cfg = engine.load_config()
        # Normalization check (raises ValueError if action or outcome invalid)
        raw_obs = {
            "action": data.action_id,
            "outcome": data.outcome,
            "reliability": reliability,
            "claimed_source": data.claimed_source,
            "timestamp_min": data.timestamp_min
        }
        normalized = engine.adapter.normalize_observation(raw_obs, cfg, inv["observer_reliability"])

        cursor.execute("""
            INSERT INTO observations (
                id, investigation_id, action_id, outcome, reliability,
                source_class, claimed_source, notes, timestamp_min, observed_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            obs_id, investigation_id, data.action_id, str(data.outcome), reliability,
            normalized["source"], data.claimed_source, data.notes, data.timestamp_min, now, now
        ))

        # Recalculate assessment
        latest_assessment = _reassess_investigation(conn, investigation_id)

    return get_investigation(investigation_id)

def complete_action(investigation_id: str, action_id: str, data: ActionCompleteRequest) -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM investigations WHERE id = ?", (investigation_id,))
        inv_row = cursor.fetchone()
        if not inv_row:
            raise ValueError(f"Investigation {investigation_id} not found")
        inv = dict(inv_row)

        now = _get_utc_now()
        obs_id = str(uuid.uuid4())
        act_rec_id = str(uuid.uuid4())
        reliability = data.reliability if data.reliability is not None else inv["observer_reliability"]

        cfg = engine.load_config()
        raw_obs = {
            "action": action_id,
            "outcome": data.outcome,
            "reliability": reliability,
            "claimed_source": data.claimed_source,
            "timestamp_min": data.timestamp_min
        }
        normalized = engine.adapter.normalize_observation(raw_obs, cfg, inv["observer_reliability"])

        # Create observation
        cursor.execute("""
            INSERT INTO observations (
                id, investigation_id, action_id, outcome, reliability,
                source_class, claimed_source, notes, timestamp_min, observed_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            obs_id, investigation_id, action_id, str(data.outcome), reliability,
            normalized["source"], data.claimed_source, data.notes, data.timestamp_min, now, now
        ))

        # Create action record
        cursor.execute("""
            INSERT INTO action_records (
                id, investigation_id, action_id, outcome, completed_at, observation_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            act_rec_id, investigation_id, action_id, str(data.outcome), now, obs_id
        ))

        # Recalculate assessment
        latest_assessment = _reassess_investigation(conn, investigation_id)

    return {
        "action_record_id": act_rec_id,
        "investigation_id": investigation_id,
        "action_id": action_id,
        "outcome": data.outcome,
        "completed_at": now,
        "observation_id": obs_id,
        "latest_assessment": latest_assessment
    }

def get_recommendation(investigation_id: str) -> Optional[Dict[str, Any]]:
    inv = get_investigation(investigation_id)
    if not inv or not inv.get("latest_assessment"):
        return None
    
    asm = inv["latest_assessment"]
    return {
        "investigation_id": investigation_id,
        "status": asm["status"],
        "recommendation": asm["recommendation"],
        "reasons": asm["reasons"],
        "candidates": asm["candidates"],
        "excluded_actions": asm["excluded_actions"],
        "diagnostics": asm["diagnostics"]
    }

def get_timeline(investigation_id: str) -> List[Dict[str, Any]]:
    timeline = []
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Investigation created
        cursor.execute("SELECT * FROM investigations WHERE id = ?", (investigation_id,))
        inv_row = cursor.fetchone()
        if not inv_row:
            return []
        inv = dict(inv_row)
        timeline.append({
            "event_type": "investigation_created",
            "timestamp": inv["created_at"],
            "detail": {
                "title": inv["title"],
                "anomaly_type": inv["anomaly_type"],
                "latitude": inv["latitude"],
                "longitude": inv["longitude"],
                "observer_reliability": inv["observer_reliability"]
            }
        })

        # 2. Observations
        cursor.execute("SELECT * FROM observations WHERE investigation_id = ? ORDER BY created_at ASC", (investigation_id,))
        for obs in cursor.fetchall():
            o = dict(obs)
            timeline.append({
                "event_type": "observation_recorded",
                "timestamp": o["created_at"],
                "detail": {
                    "observation_id": o["id"],
                    "action_id": o["action_id"],
                    "outcome": o["outcome"],
                    "reliability": o["reliability"],
                    "source_class": o["source_class"],
                    "claimed_source": o["claimed_source"]
                }
            })

        # 3. Action Records
        cursor.execute("SELECT * FROM action_records WHERE investigation_id = ? ORDER BY completed_at ASC", (investigation_id,))
        for act in cursor.fetchall():
            a = dict(act)
            timeline.append({
                "event_type": "action_completed",
                "timestamp": a["completed_at"],
                "detail": {
                    "action_record_id": a["id"],
                    "action_id": a["action_id"],
                    "outcome": a["outcome"],
                    "observation_id": a["observation_id"]
                }
            })

        # 4. Assessments
        cursor.execute("SELECT * FROM assessments WHERE investigation_id = ? ORDER BY created_at ASC", (investigation_id,))
        for asm in cursor.fetchall():
            a_data = json.loads(asm["output_snapshot"])
            timeline.append({
                "event_type": "assessment_performed",
                "timestamp": asm["created_at"],
                "detail": {
                    "assessment_id": asm["id"],
                    "status": a_data["status"],
                    "recommendation": a_data["recommendation"],
                    "evidence_support": a_data["evidence_support"],
                    "reasons": a_data["reasons"]
                }
            })

    # Sort timeline by timestamp ascending
    timeline.sort(key=lambda x: x["timestamp"])
    return timeline

def get_fhir_export(investigation_id: str) -> Optional[Dict[str, Any]]:
    inv = get_investigation(investigation_id)
    if not inv:
        return None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM observations WHERE investigation_id = ? ORDER BY created_at ASC", (investigation_id,))
        obs_rows = [dict(r) for r in cursor.fetchall()]

    return export_investigation_to_fhir(inv, obs_rows, inv.get("latest_assessment"))
