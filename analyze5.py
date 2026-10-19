"""Paper 5 analysis (protocol section 6). Reads results/*.json, writes results/summary5.json and paper/numbers5.tex.

Learned methods are summarised per object as the mean over seeds. Tests: paired two-sided Wilcoxon on per-object
differences against B0; hierarchical bootstrap (seeds, then objects) 95% CI of the mean difference; Holm within the
Q1-Q2 family (B5 vs B0, probes and overshoot, at each r, per task); Clopper-Pearson for rates.
"""
import json, os, re, numpy as np
from collections import defaultdict
from scipy import stats

R = "results"; OUT = {}
TOLS = {"pivot": 0.05, "slide": 0.005}


def cp(k, n, a=0.05):
    if n == 0: return (float("nan"), float("nan"))
    lo = stats.beta.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = stats.beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return (float(lo), float(hi))


def over(task, row):
    return (row["err"] < -TOLS[task]) if task == "pivot" else (row["err"] > TOLS[task])


def within(task, row):
    return abs(row["err"]) <= TOLS[task] and row["held"]


def family(name):
    return name.split("_s")[0]


def load(task, set_):
    p = f"{R}/{task}_{set_}.json"
    return json.load(open(p)) if os.path.exists(p) else None


def per_object(task, rows, fam, key):
    """dict object i -> mean over seeds of key(row) for method family fam."""
    d = defaultdict(list)
    for r in rows:
        if family(r["method"]) == fam: d[r["i"]].append(key(r))
    return {i: float(np.mean(v)) for i, v in d.items()}


def per_seed_object(rows, fam, key):
    d = defaultdict(dict)
    for r in rows:
        if family(r["method"]) == fam:
            s = int(r["method"].split("_s")[1]) if "_s" in r["method"] else 0
            d[s][r["i"]] = key(r)
    return d


def hboot(task, rows, fam, base, key, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    A = per_seed_object(rows, fam, key); B = per_object(task, rows, base, key)
    seeds = sorted(A); objs = sorted(B)
    arr = np.array([[A[s][i] - B[i] for i in objs] for s in seeds])
    draws = np.empty(n)
    for k in range(n):
        ss = rng.integers(0, len(seeds), len(seeds)); oo = rng.integers(0, len(objs), len(objs))
        draws[k] = arr[np.ix_(ss, oo)].mean()
    return float(arr.mean()), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def summarise(task, rows):
    fams = sorted({family(r["method"]) for r in rows}, key=lambda f: (f[0], f))
    S = {}
    for f in fams:
        X = [r for r in rows if family(r["method"]) == f]
        n = len(X); ov = sum(over(task, r) for r in X); cert = sum(r["n_cert"] for r in X); viol = sum(r["n_viol"] for r in X)
        S[f] = dict(n=n, within=float(np.mean([within(task, r) for r in X])), overshoot=ov / n, overshoot_ci=cp(ov, n),
                    drops=int(sum(not r["held"] for r in X)), declined=int(sum(bool(r.get("declined")) for r in X)),
                    probes=float(np.mean([r["probes"] for r in X])), t_min=float(np.mean([r["t_sim"] for r in X]) / 60),
                    abs_err=float(np.mean([abs(r["err"]) for r in X])), cert_steps=int(cert), violations=int(viol),
                    viol_ci=cp(viol, cert), deferrals=int(sum(r["n_defer"] for r in X)), clips=int(sum(r["n_clip"] for r in X)),
                    steps=int(sum(r["steps"] for r in X)),
                    cert_frac=float(cert / max(1, cert + sum(r["n_defer"] for r in X))))
    return S


def compare(task, rows, fam, base="B0"):
    out = {}
    for metric, key in (("probes", lambda r: r["probes"]), ("overshoot", lambda r: float(over(task, r))),
                        ("abs_err", lambda r: abs(r["err"])), ("within", lambda r: float(within(task, r)))):
        A = per_object(task, rows, fam, key); B = per_object(task, rows, base, key)
        objs = sorted(set(A) & set(B)); d = np.array([A[i] - B[i] for i in objs])
        p = float(stats.wilcoxon(d).pvalue) if np.any(d != 0) else 1.0
        if any("_s" in r["method"] for r in rows if family(r["method"]) == fam):
            m, lo, hi = hboot(task, rows, fam, base, key)
        else:
            m, lo, hi = float(d.mean()), float("nan"), float("nan")
        out[metric] = dict(diff=m, ci=(lo, hi), p=p)
    return out


def holm(ps):
    order = np.argsort(ps); adj = np.empty(len(ps)); run = 0.0
    for k, i in enumerate(order):
        run = max(run, (len(ps) - k) * ps[i]); adj[i] = min(1.0, run)
    return adj.tolist()


def main():
    for task in ("pivot", "slide"):
        T = load(task, "test")
        if T is None: continue
        rs = sorted({r["ratio"] for r in T})
        OUT[task] = {"test": {}}
        fam_tests = []
        for rv in rs:
            rows = [r for r in T if r["ratio"] == rv]
            S = summarise(task, rows)
            C = {f: compare(task, rows, f) for f in S if f != "B0"}
            OUT[task]["test"][str(rv)] = dict(summary=S, vsB0=C)
            for met in ("probes", "overshoot"):
                fam_tests.append((str(rv), met, C["B5"][met]["p"]))
        adj = holm([p for _, _, p in fam_tests])
        for (rv, met, _), a in zip(fam_tests, adj):
            OUT[task]["test"][rv]["vsB0"]["B5"][met]["p_holm"] = a
        M = load(task, "mismatch")
        if M:
            OUT[task]["mismatch"] = {}
            for rv in sorted({r["ratio"] for r in M}):
                for rm in sorted({r["rmax"] for r in M}):
                    rows = [r for r in M if r["ratio"] == rv and r["rmax"] == rm]
                    OUT[task]["mismatch"][f"r{rv}_rmax{rm}"] = summarise(task, rows)
        Cf = load(task, "confirm")
        if Cf:
            OUT[task]["confirm"] = dict(summary=summarise(task, Cf),
                                        vsB0={f: compare(task, Cf, f) for f in {family(r["method"]) for r in Cf} if f != "B0"})
    json.dump(OUT, open(f"{R}/summary5.json", "w"), indent=1)
    print(json.dumps({t: {rv: {f: (round(v["within"], 2), round(v["overshoot"], 2), round(v["probes"], 1), v["violations"], v["cert_steps"])
                               for f, v in d["summary"].items()} for rv, d in OUT[t]["test"].items()} for t in OUT}, indent=1))


if __name__ == "__main__":
    main()
