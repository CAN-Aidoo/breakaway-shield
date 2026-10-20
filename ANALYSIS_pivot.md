# Pivoting: test-set analysis (written before the confirmation set was run)

Data: results/pivot_test.json (4640 episodes), results/summary5.json. 40 objects × r ∈ {1.0, 1.05, 1.1, 1.2},
shield r_max = 1.1. Learned methods: 5 seeds, averaged per object; tests against B0 as in protocol §6.

## Headline
Pivoting is the opposite of sliding. At r_max = 1.1 half of the test targets admit no certified release at all,
so the shield cannot keep the residual's savings *and* stop overshoot: with the defer fallback it mostly reverts to
the model controller and still overshoots; with the decline fallback it stops overshoot (≤2.5% for r ≤ r_max) but
leaves most rods short of the target.

## Q1 efficiency
- Unshielded residual B2: 8.4, 8.3, 8.1, 7.4 probes vs B0 15.8, 15.5, 15.2, 14.4 (−7.0 to −7.4, CIs exclude 0).
- Shield-trained B5 uses *more* probes than B0: +2.5 (r=1.0, CI 0.8–4.5, Holm p=0.067), +2.3, +1.5, +1.0 (n.s.).
  Answer to Q1 for pivoting: **no**. The shield removes the whole saving.
- Shield at test only (B4) is indistinguishable from B5 at every r (probes within 0.2, overshoot within 3 points):
  unlike sliding, training under the shield bought nothing. About 44% of B5's steps were deferred, so the policy
  rarely acts.
- B3 (residual + earlier quasi-static guard): 10.5 probes, 6% overshoot, 94% within at r=1.0, the best trade-off at
  r=1. It does not help once r > 1 (52%, 73.5%, 92% overshoot).
- B1 (model + earlier guard) is identical to B0: that guard never binds on model steps.

## Q2 safety
- B0 overshoots 12.5, 57.5, 80, 92.5% at r = 1.0, 1.05, 1.1, 1.2.
- B2: 26% at r=1.0 (twice B0, +13.5 points, p=0.003), then the same as B0.
- Defer fallback: B0S 7.5, 47.5, 70, 80%; B5 7, 42, 63, 82.5%. B5 vs B0 −5.5, −15.5, −17, −10 points; none
  significant after Holm. Deferral returns control to the model step exactly where the model overshoots.
- Decline fallback: B0Sd 0, 2.5, 2.5, 30%; B5d 0, 1.5, 2.5, 32.5% overshoot (vs B0 p < 0.001 at r ≥ 1.05).
  But within-band is only 7.5–21.5%: declined rods stop short, mean |error| 0.33–0.37 rad.
- No method ends within 0.05 rad on more than 30% of episodes at r ≥ 1.1.
- Certificate violations, B5: 0/1743, 4/1664, 7/1443 certified steps at r ≤ r_max (≤0.5%); 68/1388 (4.9%) at
  r = 1.2 > r_max. B0S: 0, 1, 1, 13 (of 334–413).

## Q3 feasibility
- Eq. (2) with r_max = 1.1 predicts that 20 of the 40 test targets (50%) have no certified release from rest.
- Observed: B0Sd declined at the very first step on exactly 20 of 40 objects at r = 1.0 and at r = 1.1, a direct
  match. A further 14 (r=1.0) and 11 (r=1.1) declined later (after 5–28 steps), once the rod had moved and the
  remaining arc became uncertifiable. In total B0Sd declined on 85, 80, 77.5, 55% of objects.
- With the defer fallback, 53–61% of steps were certified (B0S, B4, B5).

## Q4
- At r = 1.2 > r_max, violations rise roughly tenfold (B5 4.9% of certified steps) and decline-overshoot rises to
  30–32.5%: the certificate fails where its assumption fails.
- At r ≤ r_max the violation rate (≤0.5%) is consistent with the model–simulator gap measured in V6 (D2).
- Mismatch (B0S, B5; defer fallback), r in {1.05, 1.1}:
  - r_max = 1.0 (under-assumed): every step is "certifiable" (0 deferrals), but certificates are violated on
    4.3% (r=1.05) and 6.6% (r=1.1) of B5 steps, 3.5% and 5.1% for B0S. B5 overshoot 37% and 58.5%; probes 14.2/13.8.
  - r_max = 1.2 (over-assumed): ~80% of B5 steps deferred, 0 violations, overshoot 48% and 73%; probes 16.3/15.8.
  - So in pivoting a smaller r_max issues wrong certificates, yet overshoots *less* than a larger one, because a
    larger r_max hands more steps back to the overshooting model step. With the defer fallback, a correct
    certificate does not imply a safe episode.

## Confirmation set (run once, after the analysis above was committed in 08b08c7)
40 fresh objects (seed 47), r ~ U[1.0, 1.1], r_max 1.1. B0: 37.5% overshoot, 15.2 probes. B5: 36% overshoot (n.s.),
17.8 probes (+2.6, CI 1.3–4.1, p<0.001). B2: 8.4 probes (−6.8), 42.5% overshoot. B0Sd: 0% overshoot, 15% within,
declined on 31/40. No B5 certificate violated (0/1709). The test-set conclusions replicate.
