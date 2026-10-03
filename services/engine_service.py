"""
Engine Service Wrapper for AquaForensics.
Integrates the existing mathematical reasoning engine (engine.py) with database state.
"""
from typing import Dict, Any, List
import engine
import json

def run_investigation_assessment(
    anomaly_type: str,
    observer_reliability: float,
    context: Dict[str, Any],
    observations: List[Dict[str, Any]],
    feasibility: Dict[str, Any] = None,
    seed: int = 0
) -> Dict[str, Any]:
    """
    Constructs engine input payload and invokes engine.assess().
    
    observations format expected by engine:
    [
        {
            "action": "upstream_view",
            "outcome": True | "upstream_turbid",
            "reliability": 0.9,
            "claimed_source": "oah" | "extension",
            "timestamp_min": 10.0
        }
    ]
    """
    formatted_obs = []
    for o in observations:
        # Convert string outcome representation to boolean or label as expected by adapter
        outcome_val = o["outcome"]
        if outcome_val == "true" or outcome_val == "True":
            outcome_val = True
        elif outcome_val == "false" or outcome_val == "False":
            outcome_val = False

        formatted_obs.append({
            "action": o["action_id"],
            "outcome": outcome_val,
            "reliability": float(o.get("reliability", observer_reliability)),
            "claimed_source": o.get("claimed_source", "oah"),
            "timestamp_min": o.get("timestamp_min")
        })

    engine_input = {
        "anomaly_type": anomaly_type,
        "observer_reliability": float(observer_reliability),
        "context": context,
        "observations": formatted_obs,
        "feasibility": feasibility or {}
    }

    # Run actual mathematical engine
    result = engine.assess(engine_input, seed=seed)

    # Normalize candidate & recommendation aliases for API consumers while preserving engine invariants
    for c in result.get("candidates", []):
        if "action" in c and "action_id" not in c:
            c["action_id"] = c["action"]
        if "nominal_eig_bits" in c and "eig_bits" not in c:
            c["eig_bits"] = c["nominal_eig_bits"]
            c["expected_info_gain"] = c["nominal_eig_bits"]
        if "effort_label" in c and "effort" not in c:
            c["effort"] = c["effort_label"]
        if "p_best_moderate" in c and "p_best" not in c:
            c["p_best"] = c["p_best_moderate"]

    for exc in result.get("excluded_actions", []):
        if "action" in exc and "action_id" not in exc:
            exc["action_id"] = exc["action"]

    rec = result.get("recommendation", {})
    if isinstance(rec, dict):
        actions = rec.get("actions", [])
        if actions:
            if result.get("status") == "ROBUST":
                rec["action_id"] = actions[0]
            elif result.get("status") == "NEAR_TIE":
                rec["tie_actions"] = actions
                rec["action_set"] = actions

    return engine_input, result
