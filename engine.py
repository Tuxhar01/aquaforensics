"""
AquaForensics engine (minimal).

Latent investigation states (NOT causal hypotheses):
  W, L : spatial-extent explanations, conditional on the anomaly being representative
  N    : representativeness/validity state (not persistent / not representative)

Everything numeric is an EXPERT-ELICITED, UNCALIBRATED assumption (see config.json).
Outputs are "model-based evidence support" and "assumption-sensitivity bands",
never probabilities or confidence intervals.

Pipeline:  context prior -> Bayesian updates from collected observations
           -> expected information gain (EIG, bits) for each feasible, not-yet-done action
           -> assumption-sensitivity ensembles (moderate + high) -> status
Status:    ROBUST | NEAR_TIE | INSUFFICIENT_CONFIDENCE   (no forced recommendation in the latter two)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

import adapter

STATES = ("W", "L", "N")
EPS = 1e-12
CONFIG_PATH = Path(__file__).with_name("config.json")

ROBUST, NEAR_TIE, INSUFFICIENT = "ROBUST", "NEAR_TIE", "INSUFFICIENT_CONFIDENCE"


# ----------------------------------------------------------------------------- config
def load_config(path=CONFIG_PATH) -> dict:
    raw = Path(path).read_text()
    cfg = json.loads(raw)
    cfg["_hash"] = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return cfg


# ----------------------------------------------------------------------------- math
def entropy_bits(x):
    x = np.clip(np.asarray(x, float), 0.0, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(x > 0, x * np.log2(x), 0.0)
    return -t.sum(axis=-1)


def channel(p, r):
    """Observer reliability folded in transparently: r=1 -> as modelled, r=0 -> pure noise."""
    return r * np.asarray(p, float) + (1.0 - r) * 0.5


def bayes_update(prior, p_eff, first):
    """Posterior over states after observing the action's first (True) or second outcome.
    If the evidence is impossible under the model, the belief is returned unchanged."""
    prior = np.asarray(prior, float)
    like = p_eff if first else 1.0 - p_eff
    un = prior * like
    z = un.sum(axis=-1, keepdims=True)
    ok = z > EPS
    return np.where(ok, un / np.where(ok, z, 1.0), prior)


def eig_raw(prior, p_eff):
    """H(prior) - E[H(posterior)] for a binary-outcome observation. Unclipped (for tests)."""
    prior = np.asarray(prior, float)
    p = np.asarray(p_eff, float)
    py1 = np.clip((prior * p).sum(-1), EPS, 1 - EPS)
    post1 = prior * p / py1[..., None]
    post0 = prior * (1 - p) / (1 - py1)[..., None]
    return entropy_bits(prior) - (py1 * entropy_bits(post1) + (1 - py1) * entropy_bits(post0))


def eig_bits(prior, p_eff):
    """EIG clipped to [0, H(prior)] -- only repairs floating-point noise (tests check eig_raw)."""
    h = entropy_bits(prior)
    return np.clip(eig_raw(prior, p_eff), 0.0, h)


def _logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def _expit(z):
    return 1.0 / (1.0 + np.exp(-z))


def nominal_belief(prior, tables, obs):
    """obs: list of (action_index, first_outcome: bool, reliability)."""
    post = np.asarray(prior, float)
    trace = [post.copy()]
    for a, first, r in obs:
        post = bayes_update(post, channel(tables[a], r), first)
        trace.append(post.copy())
    return post, trace


def run_ensemble(prior, tables, r_eff, sd_scale, obs, regime, n, rng, jitter):
    """Assumption-sensitivity ensemble. Each draw perturbs the context prior (Dirichlet),
    every likelihood (logit-normal; wider for lag-sensitive parameters via sd_scale) and
    reliabilities (uniform jitter), re-applies the collected observations, then computes
    EIG for every action. Returns (posteriors (n,3), EIG (n,A))."""
    prior = np.clip(np.asarray(prior, float), 1e-3, None)
    prior = prior / prior.sum()
    A = tables.shape[0]
    P0 = rng.dirichlet(regime["prior_conc"] * prior, size=n)
    noise = rng.normal(0.0, 1.0, (n, A, 3))
    P = _expit(_logit(np.asarray(tables, float))[None] + noise * (regime["logit_sd"] * np.asarray(sd_scale))[None, :, None])
    R = np.clip(np.asarray(r_eff)[None] + rng.uniform(-jitter, jitter, (n, A)), 0.0, 1.0)
    post = P0
    for a, first, r_obs in obs:
        r = np.clip(r_obs + rng.uniform(-jitter, jitter, n), 0.0, 1.0)
        post = bayes_update(post, channel(P[:, a, :], r[:, None]), first)
    E = eig_bits(post[:, None, :], channel(P, R[..., None]))
    return post, E


# ----------------------------------------------------------------------------- decision stats
def decision_stats(e_nom, E_m, E_h):
    """e_nom (k,), E_m/E_h (n,k) restricted to candidate actions."""
    k = len(e_nom)
    order = np.argsort(-e_nom, kind="stable")
    top = int(order[0])
    e1 = float(e_nom[top])
    if k == 1:
        gap = 1.0
    else:
        gap = float((e1 - e_nom[order[1]]) / e1) if e1 > EPS else 0.0
    pbm = np.bincount(E_m.argmax(1), minlength=k) / len(E_m)
    pbh = np.bincount(E_h.argmax(1), minlength=k) / len(E_h)
    regret_m = (E_m.max(1, keepdims=True) - E_m).mean(0)
    return dict(k=k, top=top, e_nom=np.asarray(e_nom, float), e1=e1, gap=gap,
                pbest_m=pbm, pbest_h=pbh, regret_m=regret_m)


def classify(stats, thr, gate_reasons=()):
    """Returns (status, tied_or_chosen_candidate_positions, reason_codes). Pure function."""
    reasons = list(gate_reasons)
    if reasons:
        return INSUFFICIENT, [], reasons
    if stats is None or stats["k"] == 0:
        return INSUFFICIENT, [], ["NO_FEASIBLE_ACTION"]
    k, a, e, e1 = stats["k"], stats["top"], stats["e_nom"], stats["e1"]
    pbm, pbh, gap = stats["pbest_m"], stats["pbest_h"], stats["gap"]
    if e1 < thr["eps_info_bits"]:
        return INSUFFICIENT, [], ["TOP_EIG_BELOW_MIN_INFORMATIVE"]
    if pbm.max() < thr["diffuse_pbest_floor"]:
        return INSUFFICIENT, [], ["RANKING_DIFFUSE_UNDER_ASSUMPTION_PERTURBATION"]
    c1 = pbm[a] >= thr["robust_pbest_moderate"]
    c2 = pbh[a] >= thr["robust_pbest_high"]
    c3 = gap >= thr["robust_rel_gap"]
    if c1 and c2 and c3:
        return ROBUST, [a], ["ONLY_ONE_FEASIBLE_ACTION"] if k == 1 else ["DOMINANT_ACTION"]
    # Tie membership is DERIVED from the robust gap so the rules have no hole:
    # any action within (1 - robust_rel_gap) of the top EIG is, by definition, what blocks ROBUST.
    tie_ratio = 1.0 - thr["robust_rel_gap"]
    tie = [i for i in range(k) if e[i] >= thr["eps_info_bits"]
           and (pbm[i] >= thr["tie_pbest"] or e[i] >= tie_ratio * e1)]
    if len(tie) >= 2:
        why = []
        if not c1: why.append("PBEST_MODERATE_BELOW_ROBUST_THRESHOLD")
        if not c2: why.append("PBEST_HIGH_BELOW_ROBUST_THRESHOLD")
        if not c3: why.append("GAP_BELOW_ROBUST_THRESHOLD")
        return NEAR_TIE, tie, why
    return INSUFFICIENT, [], ["NO_DOMINANT_OR_TIED_ACTION"]


# ----------------------------------------------------------------------------- context helpers
def context_prior(cfg, ctx):
    mm = ctx.get("rain_mm_24h")
    if mm is None:
        return np.array(cfg["priors"]["dry"]["single"], float), "FALLBACK_dry/single (weather unavailable)"
    rc = cfg["rain_class_mm"]
    cls = "dry" if mm < rc["dry_below"] else ("heavy" if mm >= rc["heavy_from"] else "moderate")
    rep = "corroborated" if ctx.get("n_independent_reports", 1) >= cfg["corroborated_from_reports"] else "single"
    return np.array(cfg["priors"][cls][rep], float), f"{cls}/{rep}"


def likelihood_tables(cfg, ctx):
    hs = ctx.get("hours_since_rain")
    recent = hs is not None and hs < cfg["recent_rain_hours"]
    names, rows = list(cfg["actions"]), []
    for n in names:
        pf = cfg["actions"][n]["p_first"]
        rows.append(pf["recent_rain"] if (recent and "recent_rain" in pf) else pf["default"])
    return names, np.array(rows, float)


def effective_reliability(cfg, observer_reliability):
    ref = cfg["reference_observer_reliability"]
    return np.clip(np.array([cfg["actions"][n]["base_reliability"] for n in cfg["actions"]]) * observer_reliability / ref, 0.0, 1.0)


def _validate(inp, cfg):
    rel = inp.get("observer_reliability")
    if not (isinstance(rel, (int, float)) and 0.0 <= rel <= 1.0):
        raise ValueError("observer_reliability must be within [0, 1]")
    ctx = inp.get("context", {})
    if ctx.get("rain_mm_24h") is not None and ctx["rain_mm_24h"] < 0:
        raise ValueError("rain_mm_24h must be >= 0")
    if ctx.get("n_independent_reports", 1) < 1:
        raise ValueError("n_independent_reports must be >= 1")
    for a in inp.get("feasibility", {}):
        if a not in cfg["actions"]:
            raise ValueError(f"unknown action in feasibility: {a!r}")


def _gates(inp, obs, cfg):
    thr, g = cfg["thresholds"], []
    if inp.get("anomaly_type") != "abnormal_water_aspect":
        g.append("OUT_OF_DOMAIN_ANOMALY")
    if inp["observer_reliability"] < thr["r_min"]:
        g.append("RELIABILITY_BELOW_MIN")
    ctx = inp.get("context", {})
    if ctx.get("weather_status") != "ok" or ctx.get("rain_mm_24h") is None:
        g.append("NO_WEATHER_CONTEXT")
    w = cfg["contradiction_window_min"]
    for i in range(len(obs)):
        for j in range(i + 1, len(obs)):
            a, b = obs[i], obs[j]
            if (a["action"] == b["action"] and a["first"] != b["first"]
                    and a["reliability"] >= thr["r_min"] and b["reliability"] >= thr["r_min"]
                    and a["timestamp_min"] is not None and b["timestamp_min"] is not None
                    and abs(a["timestamp_min"] - b["timestamp_min"]) <= w):
                g.append("CONTRADICTORY_INPUTS")
    return sorted(set(g))


# ----------------------------------------------------------------------------- assess
def assess(inp: dict, cfg: dict | None = None, seed: int = 0, n_draws: int | None = None) -> dict:
    """
    inp = {
      "anomaly_type": "abnormal_water_aspect",
      "observer_reliability": 0.9,
      "context": {"rain_mm_24h": 0.0, "hours_since_rain": None,
                  "n_independent_reports": 1, "weather_status": "ok"},
      "observations": [{"action": "...", "outcome": True|label, "reliability": 0.9,
                        "claimed_source": "oah"|"extension", "timestamp_min": None}],
      "feasibility": {"<action>": {"feasible": False, "reason": "..."}}
    }
    """
    cfg = cfg or load_config()
    _validate(inp, cfg)
    thr = cfg["thresholds"]
    ens = cfg["ensemble"]
    n = n_draws or ens["n_draws"]
    names, tables = likelihood_tables(cfg, inp.get("context", {}))
    A = len(names)
    r_eff = effective_reliability(cfg, inp["observer_reliability"])
    sd_scale = np.array([cfg["actions"][a]["sd_scale"] for a in names])
    prior, prior_class = context_prior(cfg, inp.get("context", {}))

    obs = [adapter.normalize_observation(o, cfg, inp["observer_reliability"]) for o in inp.get("observations", [])]
    obs_t = [(names.index(o["action"]), o["first"], o["reliability"]) for o in obs]
    gates = _gates(inp, obs, cfg)

    belief, trace = nominal_belief(prior, tables, obs_t)
    done = {o["action"] for o in obs}
    feas = inp.get("feasibility", {})
    excluded, idx = [], []
    for i, a in enumerate(names):
        if a in done:
            excluded.append({"action": a, "reason": "ACTION_ALREADY_COMPLETED"})
        elif not feas.get(a, {}).get("feasible", True):
            excluded.append({"action": a, "reason": "INFEASIBLE: " + feas[a].get("reason", "unspecified")})
        else:
            idx.append(i)

    ss = np.random.SeedSequence(seed)
    rng_m, rng_h = (np.random.default_rng(s) for s in ss.spawn(2))
    jit = ens["reliability_jitter"]
    post_m, E_m = run_ensemble(prior, tables, r_eff, sd_scale, obs_t, ens["regimes"]["moderate"], n, rng_m, jit)
    _, E_h = run_ensemble(prior, tables, r_eff, sd_scale, obs_t, ens["regimes"]["high"], n, rng_h, jit)
    e_all = eig_bits(belief[None, :], channel(tables, r_eff[:, None]))

    stats = None
    if idx:
        sub = np.array(idx)
        stats = decision_stats(e_all[sub], E_m[:, sub], E_h[:, sub])
    status, chosen, reasons = classify(stats, thr, gates)

    lo, hi = np.percentile(post_m, [5, 95], axis=0)
    split = post_m[:, 0] / np.maximum(post_m[:, 0] + post_m[:, 1], EPS)
    leader_stab = float((post_m.argmax(1) == int(np.argmax(belief))).mean())
    sup = {s: round(float(belief[i]), 6) for i, s in enumerate(STATES)}
    band = {s: [round(float(lo[i]), 6), round(float(hi[i]), 6)] for i, s in enumerate(STATES)}
    band["W_given_representative"] = [round(float(np.percentile(split, 5)), 6), round(float(np.percentile(split, 95)), 6)]

    cands = []
    for pos, i in enumerate(idx):
        a = names[i]
        cands.append({
            "action": a, "label": cfg["actions"][a]["label"],
            "nominal_eig_bits": round(float(stats["e_nom"][pos]), 6),
            "p_best_moderate": round(float(stats["pbest_m"][pos]), 4),
            "p_best_high": round(float(stats["pbest_h"][pos]), 4),
            "mean_regret_bits_moderate": round(float(stats["regret_m"][pos]), 6),
            "effort_label": cfg["actions"][a]["effort"],
            "oah_fields": cfg["actions"][a]["oah_fields"],
            "future_evidence_source": adapter.candidate_source(a, cfg),
            "field_status": cfg["actions"][a]["field_status"],
            "outcomes": cfg["actions"][a]["outcomes"],
        })

    if status == ROBUST:
        rec = {"type": "single", "actions": [names[idx[chosen[0]]]]}
    elif status == NEAR_TIE:
        rec = {"type": "tie_set", "actions": [names[idx[c]] for c in chosen]}  # unranked by information
    else:
        rec = {"type": None, "actions": []}

    uses_ext = any(o["source"] == adapter.EXTENSION for o in obs) or \
        any(adapter.candidate_source(names[idx[c]], cfg) == adapter.EXTENSION for c in chosen)

    return {
        "status": status,
        "recommendation": rec,
        "reasons": reasons,
        "evidence_support": sup,
        "assumption_sensitivity_band": band,
        "representativeness_support_N": sup["N"],
        "extent_split_W_given_representative": round(float(belief[0] / max(belief[0] + belief[1], EPS)), 6),
        "labels_note": ("Model-based evidence support under uncalibrated, expert-elicited assumptions; NOT probabilities. "
                        "Bands show sensitivity to assumption perturbation (5-95% of the moderate regime); NOT confidence intervals."),
        "candidates": cands,
        "excluded_actions": excluded,
        "diagnostics": {
            "prior_class": prior_class,
            "top_nominal_eig_bits": None if stats is None else round(stats["e1"], 6),
            "relative_gap_top_vs_second": None if stats is None else round(stats["gap"], 4),
            "leader_stability_display_only": round(leader_stab, 4),
            "validity_gates_triggered": gates,
            "state_entropy_bits": round(float(entropy_bits(belief)), 6),
        },
        "belief_trace": [{"step": i, **{s: round(float(b[j]), 6) for j, s in enumerate(STATES)}} for i, b in enumerate(trace)],
        "evidence_provenance": {
            "observations": [{"action": o["action"], "source": o["source"], "warnings": o["warnings"]} for o in obs],
            "uses_extension_evidence": bool(uses_ext),
        },
        "provenance": {
            "seed": seed, "n_draws": n, "regimes": ens["regimes"], "config_hash": cfg["_hash"],
            "parameter_status": "ALL EXPERT_ELICITED_UNCALIBRATED; thresholds PROVISIONAL",
        },
    }
