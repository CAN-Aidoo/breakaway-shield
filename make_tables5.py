"""Tables for Paper 5 from results/summary5.json -> paper/tab_<task>.tex"""
import json

D = json.load(open("results/summary5.json"))
ORDER = {"pivot": ["B0", "B1", "B0S", "B0Sd", "B2", "B3", "B4", "B5", "B5d"], "slide": ["B0", "B0S", "B2", "B4", "B5"]}
DESC = {"B0": "model", "B1": "model + quasi-static guard", "B0S": "model + shield", "B0Sd": "model + shield (decline)",
        "B2": "residual", "B3": "residual + quasi-static guard", "B4": "residual, shield at test", "B5": "shield-trained residual",
        "B5d": "shield-trained (decline)"}
CAP = {"pivot": "Pivoting test set (40 objects; learned methods: 5 seeds, 200 episodes per cell). Within: final error "
                "$\\le$0.05\\,rad and held. Over: overshoot past the target by more than 0.05\\,rad. Probes: angle "
                "measurements per pivot. Shield $r_{\\max}=1.1$.",
       "slide": "Sliding test set (40 objects; learned methods: 5 seeds, 200 episodes per cell). Within: final error "
                "$\\le$5\\,mm and held. Over: travel past the target by more than 5\\,mm. Probes: position "
                "measurements per episode. Shield $r_{\\max}=1.2$."}

for task in D:
    T = D[task]["test"]; rs = sorted(T, key=float)
    fams = [f for f in ORDER[task] if f in T[rs[0]]["summary"]]
    L = [r"\begin{table*}[t]\centering\footnotesize", r"\caption{%s}\label{tab:%s}" % (CAP[task], task),
         r"\setlength{\tabcolsep}{3.2pt}",
         r"\begin{tabular}{ll" + "rrr" * len(rs) + "}", r"\toprule",
         " & & " + " & ".join(r"\multicolumn{3}{c}{$r=%s$}" % r for r in rs) + r"\\",
         "".join(r"\cmidrule(lr){%d-%d}" % (3 + 3 * k, 5 + 3 * k) for k in range(len(rs))),
         r"ID & method & " + " & ".join(["within & over & probes"] * len(rs)) + r"\\", r"\midrule"]
    for f in fams:
        cells = []
        best_over = {r: min(T[r]["summary"][g]["overshoot"] for g in fams) for r in rs}
        for r in rs:
            v = T[r]["summary"][f]
            ov = f"{100 * v['overshoot']:.0f}"
            if abs(v["overshoot"] - best_over[r]) < 1e-12: ov = r"\textbf{" + ov + "}"
            cells += [f"{100 * v['within']:.0f}", ov, f"{v['probes']:.1f}"]
        L.append(f"{f} & {DESC[f]} & " + " & ".join(cells) + r"\\")
        if f in ("B0Sd", "B0S") and task == "slide" or f == "B0Sd": L.append(r"\midrule")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    open(f"paper/tab_{task}.tex", "w").write("\n".join(L) + "\n")
print("tables written")
