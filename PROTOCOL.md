# Protocol — Paper 5: Physics shields for residual policies at breakaway

Frozen 2026-10-19 before any test-set or confirmation-set evaluation. Every later change is added below as a
dated deviation (D1, D2, …) and committed before it is applied. Development used only the validation set
(object seed 123) and the Paper-2 weights.

## 1. Questions
- **Q1 (efficiency):** does a residual policy trained with the breakaway shield keep the measurement savings of
  an unshielded residual over the model controller?
- **Q2 (safety):** does the shield bound overshoot, and how often is its certificate violated in simulation?
- **Q3 (feasibility):** how much of the task admits a certified release, as a function of the static/kinetic ratio r?
- **Q4 (attribution and mismatch):** where violations or overshoots occur, are they explained by mismatch between
  the assumed r_max and the true r, by sensing error, or by simulator effects?

## 2. Simulator
MuJoCo 3.15.0, the Paper-1/2 rig (condim 4, elliptic cone, impratio 10, noslip 20, dt 1 ms). Stick-slip: the
torsional coefficient of all three contact geoms is mut (static) while the rod's angular speed relative to the
palm is below v_slip = 0.05 rad/s after re-sticking below v_stick = 0.01 rad/s, and mut/r (kinetic) while sliding.
r = 1 reproduces Paper 2 exactly (verified on three test objects to 1e-6 rad).

Validation checks reported in the paper (V1–V6):
- V1 breakaway-ramp force against the model F_h, for each r;
- V2 kinetic torque during steady sliding against mut/r;
- V3 creep rate in the stuck phase over the longest hold;
- V4 first-slip travel with dt halved;
- V5 sensitivity to v_slip and v_stick (each x0.5 and x2);
- V6 bound conformance: simulated first-slip stop against the undamped (certified) and quasi-static predictions.

## 3. Shield (pivoting)
Proposition 1: if the rod is stuck at depression phi0 under grip F_last, then F_h <= F_last / cos(phi0). After
breakaway under final grip F, the undamped energy balance stops the rod at or before phi_lim if
F >= F_last * (r_max / cos phi0) * S(phi0, phi_lim), where S is the chord slope of sin. Here
phi_lim = |target| + 0.05 - 0.02 (overshoot threshold minus a 2.5-sigma sensing margin).

Application at every decision step after the first: if floor < 0.995 * F_last, the step is **certified** and the
action is max(policy force, floor), a clip that never lowers grip. Otherwise the state is **infeasible**, with two
pre-specified fallbacks:
- **defer** (mode suffix S): drop the residual and take the model controller's step, uncertified;
- **decline** (suffix Sd): stop and hold.

The release rate is not constrained. A **certificate violation** is a certified step after which the true
depression exceeds phi_lim.

## 4. Training
Objects follow the Paper-2 distribution, plus r ~ U[1.0, 1.1] per object. Linear policies, antithetic ES as in
Paper 2 (6 pairs, 6 objects per iteration, sigma 0.1, Adam lr 0.06, 20 iterations = 1560 episodes per run).
Two trained methods, 5 seeds each (0–4):
- `residual`: unshielded;
- `residualS`: shield in the training loop with r_max = 1.1, defer fallback.

## 5. Evaluation
Test set: object seed 31, 40 objects, episode seeds 5000+i, evaluated once at each r in {1.0, 1.05, 1.1, 1.2},
with r_max = 1.1 unless stated. Methods:
- B0 model;
- B1 model + Paper-2 guard (modelG);
- B0S model + shield (defer) and B0Sd (decline);
- B2 residual;
- B3 residual + Paper-2 guard;
- B4 residual + shield at test only (defer);
- B5 shield-trained residual (defer) and B5d (decline).

Mismatch stress test: B0S and B5 with r_max in {1.0, 1.2} at r in {1.05, 1.1}.

Confirmation set: object seed 47, 40 objects, r ~ U[1.0, 1.1] drawn with the same seed. Methods B0, B1, B0S, B2,
B5. Run once, after the test analysis is written, with no changes in between.

Metrics:
- measurements (probes) per pivot and simulated time;
- final |error|, fraction within 0.05 rad, overshoot (theta_final < target - 0.05), drops, declines;
- certified steps, violations, deferrals and clips.

## 6. Statistics
- Learned methods are summarised per object as the mean over 5 seeds.
- Paired two-sided Wilcoxon signed-rank tests on per-object differences against B0.
- Hierarchical bootstrap 95% CIs (resample seeds, then objects; 10,000 draws) for mean differences.
- Holm correction within the Q1–Q2 family: probes and overshoot, B5 vs B0, at each r.
- Clopper–Pearson 95% intervals for violation and overshoot rates; rule of three when there are zero events.
- Infeasible region: analytic (physical and shield-induced) over (target, r), plus the empirical fraction of
  certified steps.

Pre-specified expectations, written down so they can be wrong:
- E1: at r = 1.0, B5 uses fewer probes than B0 and keeps at least 80% of B2's probe saving.
- E2: certificate violations are 0 when r <= r_max.
- E3: certified fraction falls as r rises; at r >= 1.1 most states from rest are infeasible.
- E4: B5 overshoots no more often than B0 at every r.

## 7. Controlled sliding
Specified in D1 below, before any sliding test data existed.

## Deviations
**D1 (2026-10-19): controlled-sliding protocol.** Written before any sliding test or confirmation data existed.
Development used validation objects (seed 123) only.

Task (slide_env.py): a vertical rod held at its centre of mass is lowered through the grasp by a target
x* ~ U[10, 50] mm using release pulses. Each pulse is: release in 0.1 s to F_p, hold for tau, re-clamp to 30 N in
0.3 s, measure (sensor sigma 0.5 mm, one probe each).

Stick-slip is applied to the sliding coefficient: mu while stuck, mu/r while sliding (v_slip 5 mm/s,
v_stick 1 mm/s).

Model controller:
- search: grip steps of x0.9 from the mu = 0.3 grip;
- after motion: F_p = 0.95 F_stuck, with hold from the Coulomb (r = 1) prediction, corrected by the ratio of
  observed to predicted travel.

Timing shield (Proposition 2): while sliding, a <= g(1 - F/(r F_b)) with r F_b <= r_max F_stuck. The worst-case
travel of the planned profile is integrated, and the hold is shortened (bisection) until the bound is within
x_lim = remaining + 5 mm - 1.5 mm. If even a zero hold violates the bound, the state is infeasible and the shield
defers to the model step. The decline fallback is omitted for sliding: infeasibility there comes from not yet
knowing F_b during search, not from the physics, so declining would stop every episode at its first step.

Training: r ~ U[1.0, 1.2], r_max = 1.2; same ES settings; 5 seeds x {residual, residualS}.

Evaluation:
- test set: object seed 31, 40 objects, at r in {1.0, 1.1, 1.2, 1.3}, r_max = 1.2;
- methods: B0 model, B0S model + shield, B2 residual, B4 residual + shield at test only, B5 shield-trained;
- mismatch: B0S and B5 with r_max in {1.0, 1.3} at r in {1.1, 1.2};
- confirmation set: seed 47, 40 objects, r ~ U[1.0, 1.2].

Metrics:
- within 5 mm;
- overshoot (slid > x* + 5 mm);
- drops, probes, certified steps, violations.

Statistics as in Section 6.

**D2 (2026-10-19): validation findings and revised V6.** Recorded before any test or confirmation data existed;
no method, parameter or training setting is changed.

- **V2, intrinsic ratio** (v2_intrinsic.py, 8 validation objects): the MuJoCo contact itself has a small
  static/kinetic gap. Breakaway happens at 0.988 of the nominal capacity and sliding at 0.980, an intrinsic ratio of
  1.008 (range 1.006–1.010). An emulated r = 1.2 gives an effective 1.206. The emulation is therefore faithful, but
  the effective ratio is about r × 1.008.
- **V6 revised** (v6_prop1.py): the original V6 compared travel against the bound computed from the *nominal* F_h.
  Near breakaway, a 1–2% capacity error moves the predicted stop by about 0.2 rad, so that comparison does not test
  Proposition 1, which only uses the grip at which the rod was observed stuck.
- The revised V6 finds breakaway by a slow ramp, holds the rod stuck at 1.01 F_brk, then releases to q·F_last.
  Over 128 releases (8 objects × r in {1.0, 1.05, 1.1, 1.2} × q in {0.99, 0.97, 0.94, 0.9}), simulated travel
  averaged 0.90–0.97 of the bound. However, 24 of 128 exceeded the matched-ratio bound, and 9 of 128 exceeded it with
  the intrinsic ratio, by at most 0.048 rad, spread across release depths.
- We attribute this to the soft-contact geometry (assumption A1: the contact point moves as the rod turns) and
  report it as a model–simulator gap. It exceeds the 0.02 rad sensing margin, so certificate violations are expected
  in the test runs. They will be reported, not tuned away; this is part of Q4.
- The original V1, V3, V4 and V5 results are reported as run (validation.json): breakaway within 0.3–2.7% of
  nominal; creep below 1e-5 rad/s; first-slip travel changed by less than 0.025 rad with dt halved and by less than
  0.01 rad with the stick/slip thresholds scaled ×0.5 or ×2.
