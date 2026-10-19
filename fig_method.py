"""Method (pipeline) diagram for Paper 5: model controller + residual policy -> breakaway shield -> gripper."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BLUE, ORANGE, VIOLET, INK, INK2, RED, GREEN = "#2a78d6", "#eb6834", "#6250d6", "#0b0b0b", "#52514e", "#c8372d", "#2e8b57"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "font.size": 7.5,
                     "mathtext.fontset": "stix", "savefig.dpi": 300})

fig = plt.figure(figsize=(7.0, 1.85)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 29); ax.axis("off")


def box(x, y, w, h, title, body, ec, fc="#ffffff"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc, ec=ec, lw=1.0))
    ax.text(x + w / 2, y + h - 1.6, title, ha="center", va="top", fontsize=7.8, weight="bold", color=INK)
    ax.text(x + w / 2, y + h - 5.0, body, ha="center", va="top", fontsize=6.4, color=INK2, linespacing=1.25)


def arrow(p, q, col=INK2, txt=None, off=(0, 1.0), rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8, color=col, lw=0.9, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}"))
    if txt: ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], txt, ha="center", va="bottom", fontsize=6.3, color=col)


box(1, 13.5, 17, 10.5, "Probe", "motor-current angle\n(pivot, 10 s) or\nposition (slide)", INK2, "#f4f3f0")
box(23, 14.5, 17, 9.5, "Model controller", "Coulomb search,\nquasi-static step\n$F_{\\rm model}$", BLUE)
box(23, 1.5, 17, 9.5, "Residual policy", "linear, ES-trained\n$\\Delta F$ or $\\Delta\\tau$", VIOLET)
box(47, 6.5, 22, 17.5, "Breakaway shield", "", RED, "#fdf3f0")
ax.text(58, 19.0, "pivot: grip floor (Prop. 1)\n$F\\geq F_{\\rm last}\\,r_{\\max}S/\\cos\\varphi_0$\n\nslide: hold bound (Prop. 2)\n"
        "$\\bar x(\\tau)\\leq x_{\\rm rem}+5-1.5$ mm", ha="center", va="top", fontsize=6.3, color=INK2, linespacing=1.3)
box(76, 13.5, 22, 10.5, "Gripper + object", "MuJoCo, stick-slip\n$\\mu_s/\\mu_k=r$ (unknown)", INK2, "#f4f3f0")

ax.add_patch(FancyBboxPatch((76, 1.5), 22, 9.0, boxstyle="round,pad=0.25,rounding_size=0.8", fc="#ffffff", ec=RED, lw=0.8, ls="--"))
ax.text(87, 9.3, "no certified action", ha="center", va="top", fontsize=6.8, weight="bold", color=RED)
ax.text(87, 6.4, "defer: model step (S)\ndecline: stop and hold (Sd)", ha="center", va="top", fontsize=6.3, color=INK2, linespacing=1.25)

arrow((18.6, 19), (22.6, 19)); arrow((18.6, 16), (22.6, 7), rad=0.15)
arrow((40.4, 19), (46.6, 17))
ax.text(43.5, 13.2, "sum $F_\\pi$", fontsize=6.3, color=INK2, ha="center")
arrow((40.4, 6), (46.6, 11))
arrow((69.4, 18.5), (75.6, 18.5), col=GREEN, txt="certified:\n$\\max(F_\\pi,$ floor$)$", off=(0, 0.6))
arrow((69.4, 10.0), (75.6, 6.5), col=RED, ls="--")
ax.plot([87, 87, 9.5], [24.4, 26.6, 26.6], color=INK2, lw=0.6, ls=":")
ax.add_patch(FancyArrowPatch((9.5, 26.6), (9.5, 24.5), arrowstyle="-|>", mutation_scale=7, color=INK2, lw=0.6))
ax.text(48, 26.9, "measured state: angle or position, last stuck grip $F_{\\rm last}$", fontsize=6.3, color=INK2, ha="center", va="bottom")
fig.savefig("paper/fig_method.pdf"); plt.close(fig)
print("method figure written")
