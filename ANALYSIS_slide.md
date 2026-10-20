# Sliding: test-set analysis (written before the confirmation set was run)

Data: results/slide_test.json (2720 episodes), results/slide_mismatch.json (960), results/summary5.json,
results/attrib_slide_test.json. Learned methods: 5 seeds, averaged per object; tests against B0 as in protocol §6.

## Q1 efficiency
- The unshielded residual (B2) cuts probes against B0 at every r: 9.3 vs 14.7 (r=1.0), 8.2 vs 13.5, 7.4 vs 11.4,
  7.9 vs 11.5 (bootstrap CIs exclude 0 at all r).
- The shield-trained residual (B5) keeps only part of that saving: −2.6 probes at r=1.0 (CI −4.8 to −0.6, Holm
  p=0.020) and −1.6 at r=1.1 (CI −4.0 to 0.7, n.s.); at r=1.2 and 1.3 it uses the same number of probes as B0
  (+0.1 and −0.7, n.s.). Answer to Q1: **partly**. Safety costs most of the residual's measurement saving.
- Shield at test only (B4) costs more probes than B5 (13.1–15.0 vs 10.8–12.1 at every r): training under the shield
  recovers about 2–3.5 probes per episode.
- Model + shield (B0S) almost doubles the probes of B0 (21–27) and lowers the within-band rate at r ≤ 1.1, because
  shortened holds leave the rod short of the target (mean |error| 6.4–10.2 mm vs 2.7–4.9 mm for B0).

## Q2 safety
- B0 overshoots 15, 8, 30 and 28% at r = 1.0, 1.1, 1.2, 1.3; B2 8–13%.
- B5 overshoots 1–2.5% at all r, with 96–98% within band; vs B0 at r=1.2 −28 points (CI −42 to −15, Holm p=0.008),
  r=1.3 −25 (Holm p=0.015). At r=1.0/1.1 the reduction is −13/−6.5 points, not significant after Holm.
- B5 vs B0 within-band: +15.5, +8.5, +26.5, +23.5 points.
- Certificate violations (true pulse travel > certified limit): B5 4/2020, 3/1984, 5/1886, 6/1752 certified steps
  (0.15–0.35%); B4 4/2382, 3/2507, 1/2597, 2/2222; B0S 0/887, 1/982, 1/761, 2/765.

## Q3 feasibility (sliding)
- Every shielded episode deferred exactly once, on its first pulse (F_stuck still unknown); no other pulse was
  infeasible (B0S 160/160 episodes, B4 800/800, B5 800/800). Sliding has no r-caused infeasible region, as predicted.

## Q4 attribution and mismatch
- Attribution (exploratory replay, attribute_viol.py) of the 32 violating steps in the test set:
  A (r > r_max, only at r=1.3) 10; B (recorded stuck grip below the true arrest requirement) 1;
  C (bound assumptions held) 21. All 21 class-C steps are on three objects (i = 10, 33, 35), all heavy
  (m = 0.178–0.192 kg). A direct probe on these objects (scratch bndchk.py) found simulated travel up to 1.8×
  the bound for short pulses released close to the stuck grip, where the bound is small; we attribute this to
  MuJoCo's regularised (soft) friction, which lets a loaded contact creep, i.e. a simulator effect. Light objects
  stayed at 0.01–0.8× the bound.
- Mismatch (B5 and B0S only):
  - r_max = 1.0 (under-assumed): B5 overshoot rises to 5.5% (r=1.1) and 6.5% (r=1.2), violations to 14/1367 and
    17/1309 (≈1%); probes fall to 8.5–8.8, i.e. B2's level. B0S at r=1.2: 12.5% overshoot.
  - r_max = 1.3 (over-assumed): B5 overshoot 1.5% and 0.5%, probes 13.3–13.9.
  - So r_max trades measurements against overshoot monotonically; the shield degrades gracefully, not abruptly.

## Confirmation set (run once, after the analysis above was committed in c620686)
40 fresh objects (seed 47), r ~ U[1.0, 1.2], r_max 1.2. B5 vs B0: overshoot 0.5% vs 17.5% (−17 points, CI −30 to −6,
p=0.010); within 98.5% vs 82.5% (p=0.017); probes 11.9 vs 14.0 (−2.1, CI −5.0 to 0.3, n.s.). B2: 8.7 probes, 10%
overshoot. B5 violations 2/1977 certified steps. The test-set conclusions replicate.
