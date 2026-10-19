"""V2: intrinsic static/kinetic ratio of the MuJoCo contact (pivoting), r0 = (breakaway capacity)/(sliding capacity),
both normalised by 2*mu_t*N. Measured at emulated r in {1.0, 1.2} on 8 validation objects."""
import os, json, numpy as np, mujoco
os.environ.setdefault("PIVOT1_DIR", os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
from mj_ctrl import Rig
from pivot_env import sample_object
G = 9.81

def measure(args):
    o, r = args
    Fh = o["m"] * G * o["d"] / (2 * o["mut"])
    R = Rig(o["m"], o["d"], o["mu"], o["mut"], ratio=r); M, D = R.model, R.data
    R.ramp_grip(1.05 * Fh, secs=2.0, hold=1.0)
    th0 = R.com_dir(); f6 = np.zeros(6); F0 = R.grip; brk = None; slide = []
    for k in range(4000):
        F = F0 + (0.97 * Fh - F0) * min(1, (k + 1) / 1500); D.ctrl[1:] = F; R.mj1()
        N = 0.0; T = 0.0
        for c in range(D.ncon):
            mujoco.mj_contactForce(M, D, c, f6); N += f6[0]; T += abs(f6[3])
        if N < 1e-6: break
        cap = 2 * o["mut"] * (N / 2)
        w = abs(R.rel_omega()); grav = o["m"] * G * o["d"] * np.cos(th0 - R.com_dir())
        if brk is None and w > 0.05: brk = grav / cap            # gravity torque at breakaway / nominal static capacity
        if brk is not None and w > 0.2: slide.append(T / cap)      # transmitted torque while clearly sliding
    kin = float(np.median(slide)) if slide else float("nan")
    return dict(r=r, static=brk, kinetic=kin, r0=(brk / kin) if brk else None)

if __name__ == "__main__":
    g = np.random.default_rng(123); objs = [sample_object(g) for _ in range(8)]
    with Pool(2) as p: res = p.map(measure, [(o, r) for o in objs for r in (1.0, 1.2)])
    json.dump(res, open("results/v2_intrinsic.json", "w"), indent=1)
    for r in (1.0, 1.2):
        X = [x for x in res if x["r"] == r]
        print(f"emulated r={r}: static {np.mean([x['static'] for x in X]):.3f}  kinetic {np.mean([x['kinetic'] for x in X]):.3f}  "
              f"effective ratio {np.mean([x['r0'] for x in X]):.3f} (range {min(x['r0'] for x in X):.3f}-{max(x['r0'] for x in X):.3f})")
