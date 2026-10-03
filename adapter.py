"""
Observation adapter.

Separates OAH-NATIVE evidence from AQUAFORENSICS-EXTENSION evidence.

Rules (enforced here, not left to callers):
  * An action whose field is registered as source_class == "extension" can NEVER be recorded
    as OAH-native, even if the caller claims it is (it is downgraded with a warning).
  * A caller may always declare native evidence as "extension" (conservative direction).
  * OAH answer codes are NOT mapped here: the real app has not been verified. Callers supply
    an already-coded boolean outcome (True = the action's first listed outcome) or the label.
"""
from __future__ import annotations

NATIVE = "oah_native"
EXTENSION = "extension"


def normalize_observation(raw: dict, cfg: dict, default_reliability: float) -> dict:
    action = raw.get("action")
    if action not in cfg["actions"]:
        raise ValueError(f"unknown action: {action!r}")
    spec = cfg["actions"][action]

    outcome = raw.get("outcome")
    if isinstance(outcome, str):
        labels = spec["outcomes"]
        if outcome not in labels:
            raise ValueError(f"outcome {outcome!r} not in {labels} for {action}")
        first = outcome == labels[0]
    elif isinstance(outcome, (bool, int)) and outcome in (0, 1):
        first = bool(outcome)
    else:
        raise ValueError(f"outcome for {action} must be a bool or one of {spec['outcomes']}")

    rel = raw.get("reliability", default_reliability)
    if not (isinstance(rel, (int, float)) and 0.0 <= rel <= 1.0):
        raise ValueError("observation reliability must be within [0, 1]")

    claimed = raw.get("claimed_source", "oah")
    if claimed not in ("oah", "extension"):
        raise ValueError("claimed_source must be 'oah' or 'extension'")

    warnings = []
    if spec["source_class"] == "extension":
        source = EXTENSION
        if claimed == "oah":
            warnings.append("SOURCE_DOWNGRADED_UNVERIFIED_OAH_FIELD")
    else:
        source = NATIVE if claimed == "oah" else EXTENSION

    return dict(action=action, first=first, reliability=float(rel), source=source,
                timestamp_min=raw.get("timestamp_min"), warnings=warnings)


def candidate_source(action: str, cfg: dict) -> str:
    """Provenance class that FUTURE evidence from this action would have."""
    return EXTENSION if cfg["actions"][action]["source_class"] == "extension" else NATIVE
