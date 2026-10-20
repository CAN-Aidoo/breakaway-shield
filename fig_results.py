"""Result figures for Paper 5, from results/summary5.json and results/v6_prop1.json.

fig_teaser.pdf   : probes vs overshoot (Pareto) for both tasks at the hardest r in the training range
fig_vs_r.pdf     : overshoot and probes vs r, per task (2x2)
fig_bound.pdf    : Proposition 1 conformance (simulated travel vs bound)
fig_mismatch.pdf : overshoot and violation rate under r_max mismatch
"""
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
# fixed categorical order (entity -> colour never changes between panels)
COL = {"B0": "#52514e", "B0S": "#2a78d6", "B0Sd": "#7fb0ea", "B1": "#9b9893", "B2": "#eb6834", "B3": "#f2a37f",
       "B4": "#c8372d", "B5": "#6250d6", "B5d": "#a79cf0"}
MRK = {"B0": "s", "B0S": "s", "B0Sd": "D", "B1": "v", "B2": "o", "B3": "v", "B4": "^", "B5": "o", "B5d": "D"}
LAB = {"B0": "B0 model", "B0S": "B0S model+shield", "B0Sd": "B0Sd model+shield (decline)", "B1": "B1 model+old guard",
       "B2": "B2 residual", "B3": "B3 residual+old guard", "B4": "B4 residual, shield at test", "B5": "B5 shield-trained",
       "B5d": "B5d shield-trained (decline)"}
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "font.size": 7.5,
                     "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "mathtext.fontset": "stix", "savefig.dpi": 300})
D = json.load(open("results/summary5.json"))
TASKS = [t for t in ("pivot", "slide") if t in D]
TNAME = {"pivot": "Pivoting", "slide": "Sliding"}
HARD = {"pivot": "1.1", "slide": "1.2"}


def style(ax):
    ax.grid(color=GRID, lw=0.5); ax.set_axisbelow(True)


# ---- teaser: Pareto
fig, axs = plt.subplots(1, len(TASKS), figsize=(3.45, 1.75), squeeze=False); axs = axs[0]
for ax, t in zip(axs, TASKS):
    S = D[t]["test"][HARD[t]]["summary"]
    OFF = {"B4": (4, -7), "B5": (-11, 3), "B5d": (-17, 4), "B0Sd": (4, -6)}
    for f in ("B0", "B0S", "B0Sd", "B2", "B4", "B5", "B5d"):
        if f not in S: continue
        v = S[f]; lo, hi = v["overshoot_ci"]
        ax.errorbar(v["probes"], 100 * v["overshoot"], yerr=[[100 * (v["overshoot"] - lo)], [100 * (hi - v["overshoot"])]],
                    fmt=MRK[f], ms=5, color=COL[f], mec="white", mew=0.6, elinewidth=0.7, capsize=0, zorder=3)
        ax.annotate(f, (v["probes"], 100 * v["overshoot"]), xytext=OFF.get(f, (4, 2)), textcoords="offset points", fontsize=6.5, color=INK2)
    ax.set_ylim(bottom=-3)
    ax.set_title(f"{TNAME[t]}, $r={HARD[t]}$", fontsize=7.5, pad=3)
    ax.set_xlabel("probes per episode"); style(ax)
axs[0].set_ylabel("overshoot (%)")
fig.tight_layout(pad=0.3, w_pad=0.8); fig.savefig("paper/fig_teaser.pdf"); plt.close(fig)

# ---- vs r
fig, axs = plt.subplots(2, len(TASKS), figsize=(7.0, 3.3), squeeze=False)
for j, t in enumerate(TASKS):
    rs = sorted(D[t]["test"], key=float)
    fams = [f for f in COL if f in D[t]["test"][rs[0]]["summary"]]
    for f in fams:
        ov = [100 * D[t]["test"][r]["summary"][f]["overshoot"] for r in rs]
        pr = [D[t]["test"][r]["summary"][f]["probes"] for r in rs]
        x = [float(r) for r in rs]
        kw = dict(color=COL[f], marker=MRK[f], ms=3.5, lw=1.4 if f in ("B0", "B2", "B5", "B0S") else 0.9,
                  ls="-" if f in ("B0", "B2", "B5", "B0S", "B4") else (0, (3, 1.5)), label=LAB[f])
        axs[0, j].plot(x, ov, **kw); axs[1, j].plot(x, pr, **kw)
    axs[0, j].set_title(TNAME[t], fontsize=8, pad=3); axs[1, j].set_xlabel("true static/kinetic ratio $r$")
    for i in range(2):
        style(axs[i, j]); axs[i, j].set_xticks([float(r) for r in rs])
        axs[i, j].axvline(1.1 if t == "pivot" else 1.2, color=INK2, lw=0.5, ls=":")
axs[0, 0].set_ylabel("overshoot (%)"); axs[1, 0].set_ylabel("probes per episode")
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=3, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, 1.0), handlelength=2.2, columnspacing=1.2)
fig.tight_layout(rect=(0, 0, 1, 0.84), h_pad=0.4); fig.savefig("paper/fig_vs_r.pdf"); plt.close(fig)

# ---- bound conformance (V6)
V = json.load(open("results/v6_prop1.json"))
fig, ax = plt.subplots(figsize=(3.4, 2.1))
rc = {1.0: "#2a78d6", 1.05: "#6250d6", 1.1: "#eb6834", 1.2: "#c8372d"}
for rv in sorted({v["r"] for v in V}):
    X = [v for v in V if v["r"] == rv]
    ax.scatter([v["bound"] for v in X], [v["sim"] for v in X], s=9, color=rc.get(rv, INK2), edgecolor="white", lw=0.4,
               label=f"$r={rv}$", zorder=3)
m = max(max(v["bound"] for v in V), max(v["sim"] for v in V)) * 1.05
ax.plot([0, m], [0, m], color=INK, lw=0.8); ax.plot([0, m], [0.02, m + 0.02], color=INK2, lw=0.6, ls="--")
ax.text(0.62 * m, 0.55 * m, "travel = bound", fontsize=6.3, color=INK, rotation=0)
ax.text(0.10 * m, 0.30 * m, "dashed: bound + 0.02 rad\n(sensing margin)", fontsize=6.0, color=INK2)
ax.set_xlim(0, m); ax.set_ylim(0, m); ax.set_xlabel("Prop. 1 bound on first-slip travel (rad)")
ax.set_ylabel("simulated travel (rad)"); style(ax); ax.legend(frameon=False, fontsize=6.2, loc="upper left")
fig.tight_layout(pad=0.3); fig.savefig("paper/fig_bound.pdf"); plt.close(fig)

# ---- mismatch: B5 overshoot by true r, for under-assumed / matched / over-assumed r_max
RM = {"pivot": ("1.0", "1.1", "1.2"), "slide": ("1.0", "1.2", "1.3")}
SEQ = ("#a9c6ef", "#2a78d6", "#123f7a")
if any("mismatch" in D[t] for t in TASKS):
    fig, axs = plt.subplots(1, len(TASKS), figsize=(3.45, 1.75), squeeze=False); axs = axs[0]
    for ax, t in zip(axs, TASKS):
        M = D[t].get("mismatch", {}); rs = sorted({k.split("_")[0][1:] for k in M}, key=float); xs = np.arange(len(rs))
        for k, rm in enumerate(RM[t]):
            vals = []
            for r in rs:
                key = f"r{r}_rmax{rm}"
                v = M[key]["B5"] if key in M else D[t]["test"][r]["summary"]["B5"]
                vals.append(100 * v["overshoot"])
            lab = ("$r_{\\max}$ under-assumed", "$r_{\\max}$ as trained", "$r_{\\max}$ over-assumed")[k]
            ax.bar(xs + (k - 1) * 0.27, vals, 0.25, color=SEQ[k], label=lab, edgecolor="white", lw=0.5)
        ax.set_xticks(xs); ax.set_xticklabels([f"$r={r}$" for r in rs]); ax.set_title(TNAME[t], fontsize=7.5, pad=3); style(ax)
    axs[0].set_ylabel("B5 overshoot (%)")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, frameon=False, fontsize=6.0, bbox_to_anchor=(0.5, 1.0), handlelength=1.2)
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.86)); fig.savefig("paper/fig_mismatch.pdf"); plt.close(fig)
print("result figures written")
