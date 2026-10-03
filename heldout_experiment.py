"""
Held-out random-context experiment for the status thresholds.

Usage: python3 heldout_experiment.py <seed> <label> [thresholds_override.json]

WHAT THIS TESTS: how the ROBUST / NEAR_TIE / INSUFFICIENT_CONFIDENCE rules behave across many
random contexts (random priors, jittered likelihood tables, random completed observation,
random feasibility). Regret is measured on FRESH high-regime draws that are independent of the
draws used to classify.
WHAT THIS DOES NOT TEST: scientific validity of the likelihood model. All likelihoods remain
expert-elicited and uncalibrated; "regret" is regret inside the assumed model family.

ACCEPTANCE CRITERIA (fixed BEFORE running; do not edit after seeing results):
  C1 status carries information : mean regret(ROBUST) <= 0.5 * mean regret(non-ROBUST nominal top)
  C2 ROBUST regret is small     : 90th percentile (across contexts) of per-context mean regret <= 0.10 bits
  C3 no degenerate distribution : each status share within [0.05, 0.80]
  C4 no threshold cliffs        : one grid step on any single threshold moves ROBUST share by <= 0.15
  C5 reliability sweep (gate off): ROBUST share non-decreasing in reliability (3pp tolerance) and
                                   ROBUST p90 regret <= 0.10 bits at every reliability level
"""
import json
import sys

import numpy as np

import engine as E

ACCEPT = dict(c1_ratio=0.5, c2_p90_bits=0.10, c3_lo=0.05, c3_hi=0.80, c4_step=0.15, c5_tol=0.03)
GRID = {
    "eps_info_bits":         [0.02, 0.035, 0.05, 0.07, 0.10],
    "diffuse_pbest_floor":   [0.30, 0.35, 0.40, 0.45, 0.50],
    "robust_pbest_moderate": [0.60, 0.65, 0.70, 0.75, 0.80],
    "robust_pbest_high":     [0.40, 0.45, 0.50, 0.55, 0.60],
    "robust_rel_gap":        [0.15, 0.20, 0.25, 0.30, 0.35],
    "tie_pbest":             [0.15, 0.20, 0.25, 0.30, 0.35],
}
SWEEP = [0.55, 0.60, 0.65, 0.70, 0.75]


def make_contexts(n, rng, cfg):
    names = list(cfg["actions"])
    base = np.array([cfg["actions"][a]["p_first"]["default"] for a in names])
    A = len(names)
    out = []
    for _ in range(n):
        prior = rng.dirichlet([4, 4, 3])
        tables = E._expit(E._logit(base) + rng.normal(0, 0.6, base.shape))   # held-out: tables differ from config
        obs = []
        if rng.random() < 0.5:
            obs = [(int(rng.integers(A)), bool(rng.random() < 0.5))]
        while True:
            feas = rng.random(A) < 0.85
            idx = [i for i in range(A) if feas[i] and not (obs and obs[0][0] == i)]
            if len(idx) >= 2:
                break
        out.append(dict(prior=prior, tables=tables, obs=obs, idx=idx, obs_rel=float(rng.uniform(0.70, 0.98))))
    return out


def compute(ctx, cfg, obs_rel, seed):
    ens, names = cfg["ensemble"], list(cfg["actions"])
    r_eff = E.effective_reliability(cfg, obs_rel)
    sd = np.array([cfg["actions"][a]["sd_scale"] for a in names])
    obs_t = [(a, f, obs_rel) for a, f in ctx["obs"]]
    belief, _ = E.nominal_belief(ctx["prior"], ctx["tables"], obs_t)
    ss = np.random.SeedSequence(seed)
    rm, rh, re, rx = (np.random.default_rng(s) for s in ss.spawn(4))
    n, j = ens["n_draws"], ens["reliability_jitter"]
    _, Em = E.run_ensemble(ctx["prior"], ctx["tables"], r_eff, sd, obs_t, ens["regimes"]["moderate"], n, rm, j)
    _, Eh = E.run_ensemble(ctx["prior"], ctx["tables"], r_eff, sd, obs_t, ens["regimes"]["high"], n, rh, j)
    _, Ee = E.run_ensemble(ctx["prior"], ctx["tables"], r_eff, sd, obs_t, ens["regimes"]["high"], n, re, j)  # evaluation only
    _, Ex = E.run_ensemble(ctx["prior"], ctx["tables"], r_eff, sd, obs_t, ens["regimes"]["extreme"], n, rx, j)  # stress only
    e_all = E.eig_bits(belief[None, :], E.channel(ctx["tables"], r_eff[:, None]))
    sub = np.array(ctx["idx"])
    st = E.decision_stats(e_all[sub], Em[:, sub], Eh[:, sub])
    Es = Ee[:, sub]
    reg = (Es.max(1, keepdims=True) - Es).mean(0)          # mean regret per candidate on fresh draws
    emax = max(float(Es.max(1).mean()), 1e-9)
    Xs = Ex[:, sub]
    reg_x = (Xs.max(1, keepdims=True) - Xs).mean(0)
    return dict(stats=st, reg=reg, rel=reg / emax, reg_x=reg_x)


def status_of(c, thr, gate=()):
    s, chosen, _ = E.classify(c["stats"], thr, gate)
    return s, chosen


def summarize(cs, thr, gate_fn=None):
    rows = {E.ROBUST: [], E.NEAR_TIE: [], E.INSUFFICIENT: []}
    for c in cs:
        g = gate_fn(c) if gate_fn else ()
        s, ch = status_of(c, thr, g)
        top = c["stats"]["top"]
        rows[s].append(dict(reg_top=float(c["reg"][top]), rel_top=float(c["rel"][top]), x_top=float(c["reg_x"][top]),
                            reg_tie=float(np.mean([c["reg"][i] for i in ch])) if ch else None,
                            e1=c["stats"]["e1"], gated=bool(g)))
    n = len(cs)
    share = {k: len(v) / n for k, v in rows.items()}
    rob = [r["reg_top"] for r in rows[E.ROBUST]]
    return share, rows, (float(np.percentile(rob, 90)) if rob else float("nan")), (float(np.mean(rob)) if rob else float("nan"))


def main(seed, label, override=None):
    cfg = E.load_config()
    thr = dict(cfg["thresholds"])
    if override:
        thr.update({k: v for k, v in json.load(open(override)).items() if not k.startswith("_")})
    rng = np.random.default_rng(seed)
    ctxs = make_contexts(1000, rng, cfg)
    res = dict(label=label, seed=seed, thresholds=thr, accept=ACCEPT, n_contexts=len(ctxs))

    base = [compute(c, cfg, c["obs_rel"], seed * 7 + i) for i, c in enumerate(ctxs)]
    share, rows, p90, mean_rob = summarize(base, thr)
    nonrob = [r["reg_top"] for k in (E.NEAR_TIE, E.INSUFFICIENT) for r in rows[k]]
    near_tie_member = [r["reg_tie"] for r in rows[E.NEAR_TIE]]
    res["status_share"] = share
    rr = [r["rel_top"] for r in rows[E.ROBUST]]; xx = [r["x_top"] for r in rows[E.ROBUST]]
    res["robust_relative_regret"] = dict(mean=float(np.mean(rr)), p90=float(np.percentile(rr, 90)))
    res["robust_regret_under_EXTREME_stress_bits"] = dict(mean=float(np.mean(xx)), p90=float(np.percentile(xx, 90)))
    res["nonrobust_relative_regret_mean"] = float(np.mean([r["rel_top"] for k in (E.NEAR_TIE, E.INSUFFICIENT) for r in rows[k]]))
    res["robust_regret_bits"] = dict(mean=mean_rob, p90_across_contexts=p90)
    res["nonrobust_top_regret_mean_bits"] = float(np.mean(nonrob)) if nonrob else None
    res["near_tie_mean_regret_of_tie_members_bits"] = float(np.mean(near_tie_member)) if near_tie_member else None
    res["near_tie_mean_regret_of_nominal_top_bits"] = float(np.mean([r["reg_top"] for r in rows[E.NEAR_TIE]])) if rows[E.NEAR_TIE] else None
    res["insufficient_mean_regret_of_nominal_top_bits"] = float(np.mean([r["reg_top"] for r in rows[E.INSUFFICIENT]])) if rows[E.INSUFFICIENT] else None
    reasons = {}
    for c in base:
        _, _, rs = E.classify(c["stats"], thr)
        for r in rs:
            reasons[r] = reasons.get(r, 0) + 1
    res["reason_counts"] = reasons

    sens = {}
    for name, vals in GRID.items():
        sens[name] = []
        for v in vals:
            t = dict(thr); t[name] = v
            sh, _, p9, _ = summarize(base, t)
            sens[name].append(dict(value=v, robust=round(sh[E.ROBUST], 3), near_tie=round(sh[E.NEAR_TIE], 3),
                                   insufficient=round(sh[E.INSUFFICIENT], 3), robust_p90_regret=round(p9, 4)))
    res["sensitivity"] = sens

    sweep = []
    for r in SWEEP:
        cs = [compute(c, cfg, r, seed * 11 + i) for i, c in enumerate(ctxs)]
        t_off = dict(thr); t_off["r_min"] = 0.0
        sh_off, rows_off, p9_off, _ = summarize(cs, t_off)
        gate = (lambda c, r=r: ["RELIABILITY_BELOW_MIN"] if r < thr["r_min"] else ())
        sh_on, _, _, _ = summarize(cs, thr, gate)
        sweep.append(dict(reliability=r,
                          robust_rel_regret_mean=round(float(np.mean([r["rel_top"] for r in rows_off[E.ROBUST]])), 3),
                          gate_off=dict(robust=round(sh_off[E.ROBUST], 3), near_tie=round(sh_off[E.NEAR_TIE], 3),
                                        insufficient=round(sh_off[E.INSUFFICIENT], 3), robust_p90_regret=round(p9_off, 4),
                                        mean_top_eig=round(float(np.mean([c["stats"]["e1"] for c in cs])), 4)),
                          gate_on=dict(robust=round(sh_on[E.ROBUST], 3), near_tie=round(sh_on[E.NEAR_TIE], 3),
                                       insufficient=round(sh_on[E.INSUFFICIENT], 3))))
    res["reliability_sweep"] = sweep

    # ---- acceptance
    acc = {}
    mr = res["robust_regret_bits"]["mean"]; nr = res["nonrobust_top_regret_mean_bits"]
    acc["C1"] = bool(nr is not None and mr <= ACCEPT["c1_ratio"] * nr)
    acc["C2"] = bool(p90 <= ACCEPT["c2_p90_bits"])
    acc["C3"] = bool(all(ACCEPT["c3_lo"] <= v <= ACCEPT["c3_hi"] for v in share.values()))
    worst = 0.0
    for name, rowsv in sens.items():
        for a, b in zip(rowsv[:-1], rowsv[1:]):
            worst = max(worst, abs(a["robust"] - b["robust"]))
    res["c4_max_one_step_robust_shift"] = round(worst, 3)
    acc["C4"] = bool(worst <= ACCEPT["c4_step"])
    rs = [s["gate_off"]["robust"] for s in sweep]
    acc["C5"] = bool(all(b >= a - ACCEPT["c5_tol"] for a, b in zip(rs[:-1], rs[1:]))
                     and all(s["gate_off"]["robust_p90_regret"] <= ACCEPT["c2_p90_bits"] for s in sweep))
    res["acceptance"] = acc
    json.dump(res, open(f"heldout_results_{label}.json", "w"), indent=2, default=float)

    print(f"\n=== {label} seed={seed} contexts={len(ctxs)} thresholds={thr}")
    print("status share:", {k: round(v, 3) for k, v in share.items()})
    print("reasons:", reasons)
    print(f"ROBUST regret (fresh HIGH-regime draws): mean={mr:.4f}  p90-across-contexts={p90:.4f} bits")
    print(f"non-ROBUST nominal-top regret mean={nr:.4f}; NEAR_TIE tie-member mean={res['near_tie_mean_regret_of_tie_members_bits']}; "
          f"INSUFFICIENT mean={res['insufficient_mean_regret_of_nominal_top_bits']}")
    rrg, xs = res["robust_relative_regret"], res["robust_regret_under_EXTREME_stress_bits"]
    print(f"ROBUST relative regret: mean={rrg['mean']:.3f} p90={rrg['p90']:.3f}; non-ROBUST relative regret mean={res['nonrobust_relative_regret_mean']:.3f}")
    print(f"ROBUST regret under EXTREME stress (sd 1.5): mean={xs['mean']:.4f} p90={xs['p90']:.4f} bits")
    print("sensitivity (robust share / near_tie / insufficient | robust p90 regret):")
    for name, rowsv in sens.items():
        print(f"  {name}:", "  ".join(f"{x['value']}->{x['robust']}/{x['near_tie']}/{x['insufficient']}|{x['robust_p90_regret']}" for x in rowsv))
    print("max one-step ROBUST shift:", res["c4_max_one_step_robust_shift"])
    print("reliability sweep (gate OFF robust/tie/insuff | p90 regret | mean top EIG ;  gate ON robust/tie/insuff):")
    for s in sweep:
        g, o = s["gate_off"], s["gate_on"]
        print(f"  r={s['reliability']} (ROBUST rel.regret {s['robust_rel_regret_mean']}): {g['robust']}/{g['near_tie']}/{g['insufficient']} | {g['robust_p90_regret']} | {g['mean_top_eig']} ;  {o['robust']}/{o['near_tie']}/{o['insufficient']}")
    print("ACCEPTANCE:", {k: ("PASS" if v else "FAIL") for k, v in acc.items()})


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
