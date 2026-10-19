"""V6 (revised, D2): direct test of Proposition 1 in the simulator.
Run A finds the breakaway grip F_brk by a slow ramp (0.1 N/s). Run B (fresh rig) holds the rod stuck at
F_last = 1.01 F_brk for 2 s (verified: no motion), then releases to q*F_last in 0.5 s and holds 4 s.
Prop. 1 bound (phi0 = 0, F_h <= F_last): undamped stop with k = q / r_max. Checked for r_max = r (matched) and
r_max = 1.008 r (simulator's intrinsic ratio, V2)."""
import os, json, numpy as np
os.environ.setdefault("PIVOT1_DIR", os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
from scipy.optimize import brentq
from mj_ctrl import Rig
from pivot_env import sample_object
G = 9.81

def stop(k):
    if k >= 1: return 0.0
    f = lambda p: np.sin(p) - k * p
    return brentq(f, 1e-9, np.pi / 2) if f(np.pi / 2) < 0 else np.pi / 2

def find_brk(o, r):
    Fh = o["m"] * G * o["d"] / (2 * o["mut"])
    R = Rig(o["m"], o["d"], o["mu"], o["mut"], ratio=r); R.ramp_grip(1.2 * Fh, secs=2.0, hold=1.0)
    th0 = R.com_dir(); F = R.grip; dt = R.model.opt.timestep
    while F > 0.5 * Fh:
        F -= 0.1 * dt; R.data.ctrl[1:] = F; R.mj1()
        if th0 - R.com_dir() > 0.003: return F
    return None

def run(args):
    i, o, r = args
    Fb = find_brk(o, r); Fl = 1.01 * Fb; out = []
    for q in (0.99, 0.97, 0.94, 0.9):
        R = Rig(o["m"], o["d"], o["mu"], o["mut"], ratio=r)
        R.ramp_grip(Fl, secs=2.0, hold=2.0); th0 = R.com_dir()
        R.ramp_grip(q * Fl, secs=0.5, hold=4.0)
        out.append(dict(i=i, r=r, q=q, sim=float(th0 - R.com_dir()), bound=stop(q / r), bound_eff=stop(q / (1.008 * r)),
                        quasistatic=float(np.arccos(q))))
    return out

if __name__ == "__main__":
    g = np.random.default_rng(123); objs = [sample_object(g) for _ in range(8)]
    with Pool(2) as p: res = sum(p.map(run, [(i, o, r) for i, o in enumerate(objs) for r in (1.0, 1.05, 1.1, 1.2)]), [])
    json.dump(res, open("results/v6_prop1.json", "w"), indent=1)
    v = [x for x in res if x["sim"] > x["bound"] + 1e-3]; ve = [x for x in res if x["sim"] > x["bound_eff"] + 1e-3]
    print(f"{len(res)} releases; above matched bound: {len(v)}; above bound with intrinsic ratio: {len(ve)}")
    for r in (1.0, 1.05, 1.1, 1.2):
        X = [x for x in res if x["r"] == r]
        print(f" r={r}: mean sim {np.mean([x['sim'] for x in X]):.3f}  mean bound {np.mean([x['bound'] for x in X]):.3f}  "
              f"max(sim-bound) {max(x['sim']-x['bound'] for x in X):+.3f}  quasistatic mean {np.mean([x['quasistatic'] for x in X]):.3f}")
