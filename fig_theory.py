"""Analytic figures for Paper 5 (no simulation): mechanism figure and feasibility map."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Arc, Polygon
from scipy.optimize import brentq

BLUE, ORANGE, VIOLET, INK, INK2, GRID, RED, GREEN = "#2a78d6", "#eb6834", "#6250d6", "#0b0b0b", "#52514e", "#e4e3df", "#c8372d", "#2e8b57"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "font.size": 8,
                     "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "mathtext.fontset": "stix", "savefig.dpi": 300})


def S(p0, pl):
    return (np.sin(pl) - np.sin(p0)) / (pl - p0)


def stop(p0, k):
    if np.cos(p0) <= k: return p0
    f = lambda p: np.sin(p) - np.sin(p0) - k * (p - p0)
    return brentq(f, p0 + 1e-9, np.pi / 2) if f(np.pi / 2) < 0 else np.pi / 2


# ---------------- Figure: mechanism (3 panels, double column)
fig = plt.figure(figsize=(7.0, 2.15))
axA = fig.add_axes([0.0, 0.05, 0.27, 0.9]); axB = fig.add_axes([0.35, 0.2, 0.28, 0.72]); axC = fig.add_axes([0.71, 0.2, 0.27, 0.72])

# (a) schematic
ax = axA; ax.set_xlim(-0.75, 1.75); ax.set_ylim(-1.75, 0.95); ax.set_aspect("equal"); ax.axis("off")
ax.add_patch(Rectangle((-0.42, 0.22), 0.84, 0.6, fc="#e6e4df", ec=INK2, lw=0.8))
ax.text(0, 0.52, "parallel-jaw\ngripper", ha="center", va="center", fontsize=6.5, color=INK2)
ax.add_patch(Rectangle((-0.13, 0.1), 0.26, 0.14, fc="#9b9893", ec=INK2, lw=0.8))
ax.plot([0, 1.65], [0, 0], ls="--", color=INK2, lw=0.6); ax.text(1.66, 0.04, "horizontal", fontsize=5.5, color=INK2, ha="right", va="bottom")
for ang, col, lab, R in ((1.02, RED, r"$\varphi_{\lim}$", 1.6), (0.9, GREEN, r"$|\theta^*|$", 1.6)):
    e = np.array([np.cos(ang), -np.sin(ang)]) * R
    ax.plot([0, e[0]], [0, e[1]], color=col, lw=0.9, ls=(0, (3, 2)))
    ax.text(e[0] + (0.05 if col == GREEN else -0.32), e[1] - 0.02, lab, color=col, fontsize=7.5, va="top")
phi = 0.42; d = np.array([np.cos(phi), -np.sin(phi)])
ax.plot([-0.45 * d[0], 1.5 * d[0]], [-0.45 * d[1], 1.5 * d[1]], color=BLUE, lw=5.5, solid_capstyle="round", alpha=0.95, zorder=3)
ax.add_patch(Rectangle((-0.13, -0.24), 0.26, 0.14, fc="#9b9893", ec=INK2, lw=0.8, alpha=0.6, zorder=4))
com = 0.8 * d; ax.plot(*com, "o", ms=4.5, color="white", mec=INK, zorder=5)
ax.annotate("", xy=(com[0], com[1] - 0.45), xytext=com, arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8), zorder=5)
ax.text(com[0] + 0.06, com[1] - 0.42, r"$mg$", fontsize=7)
ax.text(com[0] - 0.02, com[1] + 0.14, r"$d$", fontsize=7, color=INK2)
ax.add_patch(Arc((0, 0), 1.0, 1.0, theta1=-np.degrees(phi), theta2=0, color=INK, lw=0.8))
ax.text(0.52, -0.16, r"$\varphi_0$", fontsize=8)
ax.add_patch(FancyArrowPatch((1.25 * np.cos(phi + 0.04), -1.25 * np.sin(phi + 0.04)), (1.25 * np.cos(1.25), -1.25 * np.sin(1.25)),
                             connectionstyle="arc3,rad=-0.3", arrowstyle="-|>", mutation_scale=8, color=ORANGE, lw=1.2, zorder=6))
ax.text(-0.72, -1.55, "first slip: $\\mu_s\\!\\rightarrow\\!\\mu_k$\nrod jumps past $\\varphi_{\\lim}$", fontsize=6.3, color=ORANGE)
ax.text(-0.75, 0.85, "(a)", fontsize=8, weight="bold")

# (b) energy curves
ax = axB; p0 = 0.0; ps = np.linspace(0, np.pi / 2, 400); pl = 0.7
ax.plot(ps, np.sin(ps) - np.sin(p0), color=INK, lw=1.4, label=r"gravity work $\sin\varphi-\sin\varphi_0$")
s = 0.94
for r, col in ((1.0, BLUE), (1.5, ORANGE)):
    k = s / r; ax.plot(ps, k * (ps - p0), color=col, lw=1.1, label=fr"friction work, $r={r}$")
    st = stop(p0, k); ax.plot([st], [np.sin(st)], "o", ms=3.5, color=col)
ax.plot([p0, pl], [0, np.sin(pl)], color=RED, lw=1.0, ls="--", label=r"chord to $\varphi_{\lim}$ (shield)")
ax.axvline(pl, color=RED, lw=0.6, ls=":")
ax.set_xlabel(r"depression $\varphi$ (rad)"); ax.set_ylabel(r"work $/\,mgd$")
ax.set_xlim(0, np.pi / 2); ax.set_ylim(0, 1.6); ax.grid(color=GRID, lw=0.5)
ax.legend(frameon=False, fontsize=6, loc="upper left", handlelength=1.5)
ax.text(-0.33, 1.62, "(b)", fontsize=8, weight="bold")

# (c) friction law with hysteresis
ax = axC; w = np.linspace(0, 0.15, 300)
ax.plot([0, 0.05], [1, 1], color=BLUE, lw=1.4); ax.plot([0.05, 0.05], [1, 1 / 1.25], color=BLUE, lw=0.8, ls=":")
ax.plot([0.01, 0.15], [1 / 1.25, 1 / 1.25], color=ORANGE, lw=1.4); ax.plot([0.01, 0.01], [1 / 1.25, 1], color=ORANGE, lw=0.8, ls=":")
ax.annotate("", xy=(0.05, 0.86), xytext=(0.05, 0.98), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.6))
ax.annotate("", xy=(0.01, 0.94), xytext=(0.01, 0.82), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.6))
ax.text(0.052, 0.93, r"$\omega_{\rm slip}$", fontsize=7); ax.text(0.013, 0.88, r"$\omega_{\rm stick}$", fontsize=7)
ax.text(0.075, 1.02, r"static $\mu_{t}$", color=BLUE, fontsize=7); ax.text(0.085, 0.73, r"kinetic $\mu_t/r$", color=ORANGE, fontsize=7)
ax.set_xlabel(r"relative angular speed $|\omega|$ (rad/s)"); ax.set_ylabel("torsional capacity (norm.)")
ax.set_ylim(0.6, 1.12); ax.set_xlim(0, 0.15); ax.grid(color=GRID, lw=0.5)
ax.text(-0.04, 1.13, "(c)", fontsize=8, weight="bold")
fig.savefig("paper/fig_mechanism.pdf"); plt.close(fig)

# ---------------- Figure: feasibility map (single column)
fig, ax = plt.subplots(figsize=(3.4, 2.4))
th = np.linspace(0.2, 1.4, 241); rr = np.linspace(1.0, 1.5, 201)
phil = th + 0.05 - 0.02
Z = np.array([[r * S(0.0, p) for p in phil] for r in rr])           # shield floor factor from rest
feas_phys = 1.0 / S(0.0, phil)
cs = ax.contourf(th, rr, np.where(Z < 0.995, Z, np.nan), levels=np.linspace(0.7, 1.0, 7), cmap="Blues_r")
ax.contourf(th, rr, np.where(Z >= 0.995, 1, np.nan), levels=[0.5, 1.5], colors=["#f3d6cc"])
ax.plot(th, feas_phys, color=ORANGE, lw=1.4, label=r"physical limit $r^\ast=\varphi_{\lim}/\sin\varphi_{\lim}$")
ax.plot(th, 0.995 / S(0.0, phil), color=INK, lw=0.8, ls="--", label="shield limit (step $\\geq$0.5%)")
for rv in (1.05, 1.1, 1.2): ax.axhline(rv, color=INK2, lw=0.4, ls=":")
ax.text(0.26, 1.42, "no certified release\nfrom rest (infeasible)", fontsize=6.5, color="#9a3b1e")
cb = fig.colorbar(cs, ax=ax, pad=0.02); cb.set_label(r"floor $F/F_{\rm last}$ (step size $=1-$floor)", fontsize=6.5); cb.ax.tick_params(labelsize=6)
ax.set_xlabel(r"target depression $|\theta^*|$ (rad)"); ax.set_ylabel(r"static/kinetic ratio $r$")
ax.legend(frameon=True, framealpha=0.9, edgecolor="none", fontsize=6, loc="upper left", bbox_to_anchor=(0.0, 0.8))
fig.tight_layout(); fig.savefig("paper/fig_feasibility.pdf"); plt.close(fig)
print("theory figures written")
