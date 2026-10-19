"""Simulator validation checks V1-V6 (protocol section 2). Writes results/validation.json.

All checks use validation-style objects (seed 123) and the true F_h = m g d / (2 mu_t), which the controllers never see.
"""
import os, json, numpy as np
os.environ.setdefault("PIVOT1_DIR", os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
from scipy.optimize import brentq
from mj_ctrl import Rig
from pivot_env import sample_object

G = 9.81


def Fh(o):
    return o["m"] * G * o["d"] / (2 * o["mut"])


def first_slip(o, r, s, dt=None, v_slip=0.05, v_stick=0.01, hold=3.0):
    """Rod at rest, horizontal, under 1.05 F_h; ramp grip to s F_h in 0.5 s, hold; return travel (rad, positive down)."""
    R = Rig(o["m"], o["d"], o["mu"], o["mut"], ratio=r, v_slip=v_slip, v_stick=v_stick)
    if dt: R.model.opt.timestep = dt
    R.ramp_grip(1.05 * Fh(o), secs=2.0, hold=1.0)
    th0 = R.com_dir()
    R.ramp_grip(s * Fh(o), secs=0.5, hold=hold)
    return th0 - R.com_dir(), R.n_breakaway


def undamped_stop(s, r):
    k = s / r
    if k >= 1: return 0.0
    f = lambda p: np.sin(p) - k * p
    return brentq(f, 1e-9, np.pi / 2) if f(np.pi / 2) < 0 else np.pi / 2


def v1(o):
    """Breakaway force: ramp down slowly at 0.1 N/s from 1.2 F_h; record grip when the rod has moved 0.01 rad."""
    out = []
    for r in (1.0, 1.2):
        R = Rig(o["m"], o["d"], o["mu"], o["mut"], ratio=r)
        R.ramp_grip(1.2 * Fh(o), secs=2.0, hold=1.0)
        th0 = R.com_dir(); F = R.grip; dt = R.model.opt.timestep; Fb = None
        while F > 0.3 * Fh(o):
            F -= 0.1 * dt; R.data.ctrl[1:] = F; R.mj1()
            if th0 - R.com_dir() > 0.01: Fb = F; break
        out.append(dict(r=r, Fb_over_Fh=(Fb / Fh(o)) if Fb else None))
    return out


def v3(o):
    """Creep: hold at 1.05 F_h for 10 s; drift rate (rad/s)."""
    R = Rig(o["m"], o["d"], o["mu"], o["mut"], ratio=1.2)
    R.ramp_grip(1.05 * Fh(o), secs=2.0, hold=1.0)
    a = R.com_dir(); R.step(10.0)
    return (a - R.com_dir()) / 10.0


def job(args):
    kind, o, extra = args
    if kind == "V1": return kind, extra, v1(o)
    if kind == "V3": return kind, extra, v3(o)
    if kind == "V4": return kind, extra, [first_slip(o, extra["r"], 0.95, dt=d)[0] for d in (0.001, 0.0005)]
    if kind == "V5": return kind, extra, [first_slip(o, extra["r"], 0.95, v_slip=0.05 * f, v_stick=0.01 * f)[0] for f in (0.5, 1.0, 2.0)]
    if kind == "V6":
        trav, nb = first_slip(o, extra["r"], extra["s"])
        return kind, extra, dict(sim=trav, undamped=undamped_stop(extra["s"], extra["r"]),
                                 quasistatic=float(np.arccos(min(1.0, extra["s"]))), n_breakaway=nb)


def main():
    g = np.random.default_rng(123); objs = [sample_object(g) for _ in range(8)]
    jobs = [("V1", o, dict(i=i)) for i, o in enumerate(objs[:4])]
    jobs += [("V3", o, dict(i=i)) for i, o in enumerate(objs[:4])]
    jobs += [("V4", o, dict(i=i, r=r)) for i, o in enumerate(objs[:3]) for r in (1.0, 1.2)]
    jobs += [("V5", o, dict(i=i, r=r)) for i, o in enumerate(objs[:3]) for r in (1.0, 1.2)]
    jobs += [("V6", o, dict(i=i, r=r, s=s)) for i, o in enumerate(objs) for r in (1.0, 1.05, 1.1, 1.2, 1.3, 1.5)
             for s in (0.98, 0.95, 0.9)]
    with Pool(2) as p:
        res = p.map(job, jobs)
    out = {}
    for kind, extra, val in res:
        out.setdefault(kind, []).append(dict(extra, value=val))
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/validation.json", "w"), indent=1)
    v6 = out["V6"]
    print("V6 violations of undamped bound:", sum(x["value"]["sim"] > x["value"]["undamped"] + 1e-3 for x in v6), "of", len(v6))


if __name__ == "__main__":
    main()
