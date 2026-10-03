import copy
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import adapter  # noqa: E402
import engine as E  # noqa: E402

CFG = E.load_config()
N_TEST = 600  # ensemble size used inside tests (speed)


def base_input(mm=0.0, reports=1, rel=0.9, obs=None, feas=None, hours=None, weather="ok", anomaly="abnormal_water_aspect"):
    return dict(anomaly_type=anomaly, observer_reliability=rel,
                context=dict(rain_mm_24h=mm, hours_since_rain=hours, n_independent_reports=reports, weather_status=weather),
                observations=obs or [], feasibility=feas or {})


def H_ref(x):
    return -sum(v * math.log2(v) for v in x if v > 0)


def eig_ref(prior, p, r):
    """Independent plain-python reference implementation (no numpy, no shared code)."""
    q = [r * pi + (1 - r) * 0.5 for pi in p]
    py1 = sum(a * b for a, b in zip(prior, q))
    if py1 <= 1e-12 or py1 >= 1 - 1e-12:
        return 0.0
    post1 = [a * b / py1 for a, b in zip(prior, q)]
    post0 = [a * (1 - b) / (1 - py1) for a, b in zip(prior, q)]
    return H_ref(prior) - (py1 * H_ref(post1) + (1 - py1) * H_ref(post0))


def all_keys(d, acc=None):
    acc = [] if acc is None else acc
    if isinstance(d, dict):
        for k, v in d.items():
            acc.append(str(k)); all_keys(v, acc)
    elif isinstance(d, list):
        for v in d:
            all_keys(v, acc)
    return acc


class MathInvariants(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(42)

    def test_support_normalizes_and_bounded(self):
        for _ in range(300):
            prior = self.rng.dirichlet([2, 2, 2])
            tables = self.rng.uniform(0.01, 0.99, (4, 3))
            obs = [(int(self.rng.integers(4)), bool(self.rng.random() < .5), float(self.rng.uniform(0, 1))) for _ in range(3)]
            b, trace = E.nominal_belief(prior, tables, obs)
            for step in trace:
                self.assertAlmostEqual(float(step.sum()), 1.0, places=9)
                self.assertTrue(np.all(step >= 0) and np.all(step <= 1))
        post, _ = E.run_ensemble(prior, tables, np.full(4, .9), np.ones(4), obs, CFG["ensemble"]["regimes"]["high"], 500,
                                 np.random.default_rng(1), 0.1)
        self.assertTrue(np.allclose(post.sum(1), 1.0))
        self.assertTrue(np.all(post >= 0) and np.all(post <= 1))

    def test_entropy_nonnegative_and_bounded(self):
        for _ in range(500):
            x = self.rng.dirichlet([0.3, 0.3, 0.3])
            h = float(E.entropy_bits(x))
            self.assertGreaterEqual(h, 0.0)
            self.assertLessEqual(h, math.log2(3) + 1e-9)
        self.assertEqual(float(E.entropy_bits([1, 0, 0])), 0.0)

    def test_eig_within_zero_and_entropy(self):
        for _ in range(3000):
            prior = self.rng.dirichlet([1, 1, 1])
            p = self.rng.uniform(0, 1, 3)
            r = float(self.rng.uniform(0, 1))
            raw = float(E.eig_raw(prior, E.channel(p, r)))      # UNCLIPPED: the clip must not be hiding errors
            h = float(E.entropy_bits(prior))
            self.assertGreaterEqual(raw, -1e-9)
            self.assertLessEqual(raw, h + 1e-9)
            self.assertAlmostEqual(raw, eig_ref(list(prior), list(p), r), places=9)   # matches independent implementation

    def test_edge_cases_no_nan(self):
        priors = [[1, 0, 0], [.5, .5, 0], [0, 0, 1], [1 / 3] * 3, [1e-15, 1 - 2e-15, 1e-15]]
        ps = [[0, 0, 0], [1, 1, 1], [1, 0, 0.5], [.5, .5, .5], [1, 0, 1]]
        for pr in priors:
            for p in ps:
                for r in (0.0, 0.5, 1.0):
                    pe = E.channel(np.array(p, float), r)
                    for first in (True, False):
                        post = E.bayes_update(np.array(pr, float), pe, first)
                        self.assertTrue(np.all(np.isfinite(post)))
                        self.assertAlmostEqual(float(post.sum()), 1.0, places=9)
                    g = float(E.eig_bits(np.array(pr, float), pe))
                    self.assertTrue(math.isfinite(g) and g >= 0)
        # impossible evidence (p_first=0, observe first outcome, r=1) leaves belief unchanged
        pr = np.array([.2, .3, .5])
        self.assertTrue(np.allclose(E.bayes_update(pr, E.channel(np.zeros(3), 1.0), True), pr))

    def test_evidence_changes_posterior(self):
        pr = np.array([.4, .4, .2])
        informative = E.bayes_update(pr, E.channel(np.array([.9, .1, .1]), 0.9), True)
        self.assertGreater(float(np.abs(informative - pr).sum()), 0.1)
        uninformative = E.bayes_update(pr, E.channel(np.array([.5, .5, .5]), 0.9), True)
        self.assertTrue(np.allclose(uninformative, pr))

    def test_lower_reliability_weakens_update(self):
        pr = np.array([.4, .4, .2])
        p = np.array([.9, .1, .3])
        shifts = [float(np.abs(E.bayes_update(pr, E.channel(p, r), True) - pr).sum()) for r in np.linspace(1, 0, 11)]
        for a, b in zip(shifts[:-1], shifts[1:]):
            self.assertLessEqual(b, a + 1e-12)          # shift shrinks monotonically as reliability falls
        self.assertAlmostEqual(shifts[-1], 0.0, places=12)   # r = 0 -> pure noise -> no update


class EngineBehaviour(unittest.TestCase):
    def test_reproducible_and_seed_sensitive(self):
        inp = base_input(mm=25, reports=3)
        a, b = E.assess(inp, CFG, seed=7, n_draws=N_TEST), E.assess(inp, CFG, seed=7, n_draws=N_TEST)
        self.assertEqual(a, b)
        c = E.assess(inp, CFG, seed=8, n_draws=N_TEST)
        self.assertEqual(a["evidence_support"], c["evidence_support"])      # nominal part is seed-independent
        for x, y in zip(a["candidates"], c["candidates"]):
            self.assertEqual(x["nominal_eig_bits"], y["nominal_eig_bits"])
            self.assertLess(abs(x["p_best_moderate"] - y["p_best_moderate"]), 0.12)   # MC noise only

    def test_recommendation_is_computed_never_hardcoded(self):
        rng = np.random.default_rng(5)
        recommended, checked = set(), 0
        for _ in range(60):
            cfg = copy.deepcopy(CFG)
            for a in cfg["actions"].values():
                a["p_first"] = {"default": [float(x) for x in rng.uniform(0.05, 0.95, 3)]}
                a["base_reliability"] = float(rng.uniform(0.5, 0.95))
            out = E.assess(base_input(mm=0.0, reports=1), cfg, seed=1, n_draws=N_TEST)
            prior = list(E.context_prior(cfg, out and base_input()["context"])[0])
            r_eff = E.effective_reliability(cfg, 0.9)
            names = list(cfg["actions"])
            ref = {n: eig_ref(prior, cfg["actions"][n]["p_first"]["default"], float(r_eff[i])) for i, n in enumerate(names)}
            if out["status"] == E.ROBUST:
                self.assertEqual(out["recommendation"]["actions"][0], max(ref, key=ref.get))
                recommended.add(out["recommendation"]["actions"][0]); checked += 1
            elif out["status"] == E.NEAR_TIE:
                self.assertIn(max(ref, key=ref.get), out["recommendation"]["actions"])
        self.assertGreater(checked, 5)
        self.assertGreaterEqual(len(recommended), 3)      # different tables -> different actions: nothing hardcoded

    def test_swapping_tables_swaps_recommendation(self):
        cfg = copy.deepcopy(CFG)
        a, b = cfg["actions"]["upstream_view"], cfg["actions"]["inspect_pipes_works"]
        a["p_first"], b["p_first"] = b["p_first"], a["p_first"]
        a["base_reliability"], b["base_reliability"] = b["base_reliability"], a["base_reliability"]
        base = E.assess(base_input(mm=25, reports=3), CFG, seed=1, n_draws=N_TEST)["recommendation"]["actions"]
        swapped = E.assess(base_input(mm=25, reports=3), cfg, seed=1, n_draws=N_TEST)["recommendation"]["actions"]
        self.assertEqual(base, ["upstream_view"])
        self.assertNotEqual(swapped, base)

    def test_robust_single_recommendation(self):
        cfg = copy.deepcopy(CFG)
        cfg["actions"]["upstream_view"]["p_first"] = {"default": [0.97, 0.03, 0.03]}
        cfg["actions"]["upstream_view"]["base_reliability"] = 0.97
        out = E.assess(base_input(mm=0, reports=3), cfg, seed=2, n_draws=N_TEST)
        self.assertEqual(out["status"], E.ROBUST)
        self.assertEqual(out["recommendation"], {"type": "single", "actions": ["upstream_view"]})

    def test_near_tie_returns_set_not_single(self):
        cfg = copy.deepcopy(CFG)
        for k in ("p_first", "base_reliability", "sd_scale"):
            cfg["actions"]["second_downstream"][k] = copy.deepcopy(cfg["actions"]["recheck_60min"][k])
        cfg["actions"]["upstream_view"]["base_reliability"] = 0.3     # push the others out of contention
        cfg["actions"]["inspect_pipes_works"]["base_reliability"] = 0.3
        out = E.assess(base_input(mm=0, reports=1), cfg, seed=3, n_draws=N_TEST)
        self.assertEqual(out["status"], E.NEAR_TIE)
        self.assertEqual(out["recommendation"]["type"], "tie_set")
        self.assertGreaterEqual(len(out["recommendation"]["actions"]), 2)
        self.assertEqual(set(out["recommendation"]["actions"]), {"recheck_60min", "second_downstream"})

    def test_insufficient_returns_no_recommendation(self):
        cfg = copy.deepcopy(CFG)
        for a in cfg["actions"].values():
            a["p_first"] = {"default": [0.5, 0.5, 0.5]}
        out = E.assess(base_input(), cfg, seed=1, n_draws=N_TEST)
        self.assertEqual(out["status"], E.INSUFFICIENT)
        self.assertEqual(out["recommendation"], {"type": None, "actions": []})
        self.assertIn("TOP_EIG_BELOW_MIN_INFORMATIVE", out["reasons"])

    def test_validity_gates_refuse(self):
        for kwargs, code in [(dict(rel=0.58), "RELIABILITY_BELOW_MIN"),
                             (dict(weather="unavailable"), "NO_WEATHER_CONTEXT"),
                             (dict(anomaly="foam"), "OUT_OF_DOMAIN_ANOMALY")]:
            out = E.assess(base_input(**kwargs), CFG, seed=1, n_draws=N_TEST)
            self.assertEqual(out["status"], E.INSUFFICIENT)
            self.assertIn(code, out["reasons"])
            self.assertIsNone(out["recommendation"]["type"])

    def test_adversarial_scenario_refuses(self):
        out = E.assess(base_input(mm=25, hours=1.5, rel=0.58, reports=1), CFG, seed=1, n_draws=N_TEST)
        self.assertEqual(out["status"], E.INSUFFICIENT)
        self.assertEqual(out["recommendation"]["actions"], [])

    def test_contradictory_inputs_gate(self):
        obs = [dict(action="recheck_60min", outcome=True, timestamp_min=0), dict(action="recheck_60min", outcome=False, timestamp_min=5)]
        out = E.assess(base_input(obs=obs), CFG, seed=1, n_draws=N_TEST)
        self.assertIn("CONTRADICTORY_INPUTS", out["reasons"])

    def test_no_feasible_and_single_feasible(self):
        none = {a: {"feasible": False, "reason": "test"} for a in CFG["actions"]}
        out = E.assess(base_input(feas=none), CFG, seed=1, n_draws=N_TEST)
        self.assertEqual(out["status"], E.INSUFFICIENT)
        self.assertIn("NO_FEASIBLE_ACTION", out["reasons"])
        one = {a: {"feasible": False, "reason": "test"} for a in CFG["actions"] if a != "upstream_view"}
        out = E.assess(base_input(mm=0, reports=3, feas=one), CFG, seed=1, n_draws=N_TEST)
        self.assertEqual(out["status"], E.ROBUST)
        self.assertIn("ONLY_ONE_FEASIBLE_ACTION", out["reasons"])
        self.assertEqual(len(out["excluded_actions"]), 3)

    def test_completed_action_excluded_and_belief_updates(self):
        before = E.assess(base_input(mm=0, reports=3), CFG, seed=1, n_draws=N_TEST)
        after = E.assess(base_input(mm=0, reports=3, obs=[dict(action="upstream_view", outcome=False)]), CFG, seed=1, n_draws=N_TEST)
        self.assertNotIn("upstream_view", [c["action"] for c in after["candidates"]])
        self.assertIn({"action": "upstream_view", "reason": "ACTION_ALREADY_COMPLETED"}, after["excluded_actions"])
        self.assertNotEqual(before["evidence_support"], after["evidence_support"])
        self.assertEqual(len(after["belief_trace"]), 2)
        self.assertAlmostEqual(sum(after["evidence_support"].values()), 1.0, places=4)

    def test_classify_boundaries_are_pure_and_inclusive(self):
        thr = CFG["thresholds"]
        mk = lambda pbm, pbh, e, gap: dict(k=len(e), top=0, e_nom=np.array(e), e1=e[0], gap=gap,
                                           pbest_m=np.array(pbm), pbest_h=np.array(pbh), regret_m=np.zeros(len(e)))
        s = mk([0.70, 0.30], [0.50, 0.50], [0.3, 0.1], 0.25)
        self.assertEqual(E.classify(s, thr)[0], E.ROBUST)
        s = mk([0.69, 0.31], [0.50, 0.50], [0.3, 0.1], 0.67)
        self.assertEqual(E.classify(s, thr)[0], E.NEAR_TIE)           # P_best(m) < 0.70 and runner-up has P_best >= 0.25
        s = mk([0.5, 0.5], [0.5, 0.5], [0.04, 0.04], 0.0)
        self.assertEqual(E.classify(s, thr)[0], E.INSUFFICIENT)       # EIG below informative minimum
        s = mk([0.35, 0.33, 0.32], [0.3, 0.3, 0.4], [0.3, 0.1, 0.1], 0.67)
        self.assertEqual(E.classify(s, thr)[0], E.INSUFFICIENT)       # diffuse ranking

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            E.assess(base_input(rel=1.2), CFG)
        with self.assertRaises(ValueError):
            E.assess(base_input(obs=[dict(action="nope", outcome=True)]), CFG)
        with self.assertRaises(ValueError):
            E.assess(base_input(mm=-3), CFG)


class AdapterAndLabelling(unittest.TestCase):
    def test_extension_never_recorded_as_native(self):
        o = adapter.normalize_observation(dict(action="upstream_view", outcome=True, claimed_source="oah"), CFG, 0.9)
        self.assertEqual(o["source"], adapter.EXTENSION)
        self.assertIn("SOURCE_DOWNGRADED_UNVERIFIED_OAH_FIELD", o["warnings"])

    def test_native_and_conservative_declaration(self):
        o = adapter.normalize_observation(dict(action="recheck_60min", outcome="still_abnormal", claimed_source="oah"), CFG, 0.9)
        self.assertEqual((o["source"], o["first"]), (adapter.NATIVE, True))
        o = adapter.normalize_observation(dict(action="recheck_60min", outcome=False, claimed_source="extension"), CFG, 0.9)
        self.assertEqual(o["source"], adapter.EXTENSION)

    def test_output_flags_extension_evidence(self):
        out = E.assess(base_input(mm=0, reports=3, obs=[dict(action="upstream_view", outcome=False, claimed_source="oah")]), CFG, n_draws=N_TEST)
        self.assertTrue(out["evidence_provenance"]["uses_extension_evidence"])
        self.assertEqual(out["evidence_provenance"]["observations"][0]["source"], "extension")
        out = E.assess(base_input(mm=0, reports=1), CFG, n_draws=N_TEST)
        by = {c["action"]: c["future_evidence_source"] for c in out["candidates"]}
        self.assertEqual(by["upstream_view"], "extension")
        self.assertEqual(by["recheck_60min"], "oah_native")

    def test_labels_never_claim_probability_or_confidence_interval(self):
        out = E.assess(base_input(mm=25, reports=3), CFG, n_draws=N_TEST)
        keys = [k.lower() for k in all_keys(out)]
        self.assertIn("evidence_support", keys)
        self.assertIn("assumption_sensitivity_band", keys)
        self.assertFalse([k for k in keys if "probab" in k or "interval" in k or k.startswith("ci_")])
        lo_hi = out["assumption_sensitivity_band"]
        for s in ("W", "L", "N"):
            self.assertLessEqual(lo_hi[s][0], lo_hi[s][1])
            self.assertTrue(0 <= lo_hi[s][0] and lo_hi[s][1] <= 1)
        self.assertIn("NOT probabilities", out["labels_note"])
        self.assertIn("NOT confidence intervals", out["labels_note"])

    def test_config_marks_everything_uncalibrated_and_provisional(self):
        self.assertIn("UNCALIBRATED", CFG["parameter_status"])
        self.assertIn("PROVISIONAL", CFG["thresholds"]["_status"])
        self.assertIn("NOT a cause", CFG["states_doc"]["N"])
        self.assertIn("EXTENSION_UNVERIFIED", CFG["actions"]["upstream_view"]["field_status"])
        for a in CFG["actions"].values():
            self.assertTrue(a["field_status"])
        out = E.assess(base_input(), CFG, n_draws=N_TEST)
        self.assertIn("UNCALIBRATED", out["provenance"]["parameter_status"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
