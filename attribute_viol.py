"""Q4 attribution of certificate violations (exploratory, run after the test analysis; not part of the frozen tests).

Re-runs every test episode that had n_viol > 0 (episodes are deterministic given object, ratio and seed) with the
diagnostic step log, and classifies each violating step:
  A  mismatch:        true r exceeds the assumed r_max
  B  stuck-grip error: r_max * F_stuck < r * F_b, i.e. the grip recorded as 'stuck' was below the true arrest
                       requirement (the rod had in fact been slipping, below the 2.5 mm motion threshold)
  C  model/simulator: neither; the travel exceeded a bound whose assumptions held
F_b = m g / (2 mu_s) is the nominal static breakaway grip (the simulated contact sits within ~1% of it, D2).
Usage: python3 attribute_viol.py slide test   ->  results/attrib_slide_test.json
"""
import sys, os, json, numpy as np
os.environ.setdefault("PIVOT1_DIR", os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
TASK, SET = sys.argv[1], sys.argv[2]
assert TASK == "slide", "pivot attribution uses the pivot log (see attribute_pivot in pivot_env)"
import slide_env as E

MODE = {"B0S": "modelS", "B4": "residualS", "B5": "residualS", "B0Sd": "modelSd", "B5d": "residualSd"}


def weights(name):
    fam, s = name.split("_s")
    kind = "residual" if fam == "B4" else "residualS"
    return np.load(f"w_slide_{kind}_s{s}.npy")


def job(row):
    name = row["method"]; fam = name.split("_s")[0]
    obj = {k: row[k] for k in ("m", "mu", "target", "i", "ratio", "rmax")}
    pol = E.LinearPolicy(weights(name)) if "_s" in name else None
    ep = E.SlideEpisode(obj, np.random.default_rng(5000 + row["i"]))
    res = ep.run(MODE[fam], pol)
    assert res["n_viol"] == row["n_viol"], "replay mismatch"
    Fb = obj["m"] * E.G / (2 * obj["mu"])
    out = []
    for st in ep.log:
        if st["cert"] is None or st["dx"] <= st["cert"]: continue
        if obj["ratio"] > obj["rmax"] + 1e-9: cls = "A"
        elif obj["rmax"] * st["F_stuck"] < obj["ratio"] * Fb: cls = "B"
        else: cls = "C"
        out.append(dict(method=name, i=row["i"], ratio=obj["ratio"], rmax=obj["rmax"], cls=cls, k=st["k"],
                        excess_mm=1000 * (st["dx"] - st["cert"]), Fstuck_over_Fb=st["F_stuck"] / Fb))
    return out


if __name__ == "__main__":
    rows = [r for r in json.load(open(f"results/{TASK}_{SET}.json")) if r["n_viol"] > 0]
    with Pool(2) as p:
        V = [v for o in p.map(job, rows) for v in o]
    json.dump(V, open(f"results/attrib_{TASK}_{SET}.json", "w"), indent=1)
    from collections import Counter
    print(len(rows), "episodes,", len(V), "violating steps;", Counter(v["cls"] for v in V))
    for v in V: print(v)
