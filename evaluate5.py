"""Paper 5 evaluation (protocol sections 5 and 7 / D1). Run once per set after training.

Usage:
  python3 evaluate5.py pivot test        # seed 31, 40 objects, r in {1.0, 1.05, 1.1, 1.2}, r_max 1.1
  python3 evaluate5.py pivot mismatch    # B0S, B5 with r_max in {1.0, 1.2} at r in {1.05, 1.1}
  python3 evaluate5.py pivot confirm     # seed 47, 40 objects, r ~ U[1.0, 1.1]
  python3 evaluate5.py slide test|mismatch|confirm
Writes results/<task>_<set>.json (one row per episode).
"""
import sys, os, json, numpy as np
from multiprocessing import Pool

os.environ.setdefault("PIVOT1_DIR", os.path.dirname(os.path.abspath(__file__)))
TASK, SET = sys.argv[1], sys.argv[2]
if TASK == "pivot":
    import pivot_env as E
    Episode, sample, wpre, RMAX_DEF = E.PivotEpisode, E.sample_object, "w_", 1.1
    R_TEST, R_MIS, RM_MIS, R_CONF = (1.0, 1.05, 1.1, 1.2), (1.05, 1.1), (1.0, 1.2), (1.0, 1.1)
else:
    import slide_env as E
    Episode, sample, wpre, RMAX_DEF = E.SlideEpisode, E.sample_object, "w_slide_", 1.2
    R_TEST, R_MIS, RM_MIS, R_CONF = (1.0, 1.1, 1.2, 1.3), (1.1, 1.2), (1.0, 1.3), (1.0, 1.2)
SEEDS = range(5)


def W(kind, s):
    return np.load(f"{wpre}{kind}_s{s}.npy")


def methods(set_):
    """name -> (mode, weights or None)."""
    m = {}
    if set_ == "mismatch":
        m["B0S"] = ("modelS", None)
        for s in SEEDS: m[f"B5_s{s}"] = ("residualS", W("residualS", s))
        return m
    m["B0"] = ("model", None); m["B0S"] = ("modelS", None)
    if TASK == "pivot":
        m["B1"] = ("modelG", None); m["B0Sd"] = ("modelSd", None)
    for s in SEEDS:
        m[f"B2_s{s}"] = ("residual", W("residual", s))
        m[f"B5_s{s}"] = ("residualS", W("residualS", s))
        if set_ == "test":
            m[f"B4_s{s}"] = ("residualS", W("residual", s))
            if TASK == "pivot":
                m[f"B3_s{s}"] = ("residualG", W("residual", s))
                m[f"B5d_s{s}"] = ("residualSd", W("residualS", s))
    return m


def run(job):
    name, mode, w, obj, eseed = job
    res = Episode(obj, np.random.default_rng(eseed)).run(mode, E.LinearPolicy(w) if w is not None else None)
    keep = ("err", "held", "t_sim", "probes", "steps", "n_clip", "n_defer", "n_cert", "n_viol", "n_breakaway", "declined")
    return dict(method=name, **{k: (float(res[k]) if isinstance(res[k], (float, np.floating)) else res[k]) for k in keep},
                **{k: obj[k] for k in obj})


def main():
    """Resumable: test/mismatch sets are run one r value at a time into results/parts/ and merged at the end.
    Episodes and seeds are identical to a single pass."""
    os.makedirs("results/parts", exist_ok=True)
    if SET in ("test", "mismatch"):
        g = np.random.default_rng(31); objs = [dict(sample(g), i=i) for i in range(40)]
        rs = R_TEST if SET == "test" else R_MIS
        rms = [RMAX_DEF] if SET == "test" else list(RM_MIS)
        rows = []
        for r in rs:
            part = f"results/parts/{TASK}_{SET}_r{r}.json"
            if not os.path.exists(part):
                jobs = []
                for rm in rms:
                    for name, (mode, w) in methods(SET).items():
                        for o in objs:
                            jobs.append((name, mode, w, dict(o, ratio=r, rmax=rm), 5000 + o["i"]))
                with Pool(2) as p:
                    json.dump(p.map(run, jobs, chunksize=4), open(part, "w"))
                print(f"part r={r} done", flush=True)
            rows += json.load(open(part))
    elif SET == "confirm":
        g = np.random.default_rng(47); objs = [dict(sample(g), i=i) for i in range(40)]
        gr = np.random.default_rng(47 + 1000)
        objs = [dict(o, ratio=float(gr.uniform(*R_CONF)), rmax=RMAX_DEF) for o in objs]
        jobs = [(name, mode, w, o, 5000 + o["i"]) for name, (mode, w) in methods("confirm").items() for o in objs]
        with Pool(2) as p:
            rows = p.map(run, jobs, chunksize=4)
    json.dump(rows, open(f"results/{TASK}_{SET}.json", "w"))
    print(f"{len(rows)} episodes -> results/{TASK}_{SET}.json")

if __name__ == "__main__":
    main()
