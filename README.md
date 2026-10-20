# Physics Guards for Residual Policies at Breakaway

Code, data and pre-registered protocol for the paper *Physics Guards for Residual Policies at Breakaway: When Learned
Corrections Should Defer to a Friction Model* (Clement Aidoo, CANLABS). All results are from MuJoCo simulation.

**Question.** A residual policy on top of a physics controller can save costly measurements, but in friction-limited
manipulation its worst errors happen at breakaway, when friction drops from static to kinetic. When should the learned
correction defer to a friction model?

**Answer in one line.** A breakaway shield helps where the physics leaves room for a certified action (controlled
sliding: overshoot 30% → 2% at r = 1.2), and where it does not (pivoting: half the targets have no certified release
from rest, exactly as the feasibility condition r < φ/sin φ predicts), it makes that limit explicit.

## Layout
| File | What it does |
|---|---|
| `PROTOCOL.md` | Frozen protocol (questions, sets, metrics, tests) and dated deviations D1–D2, committed before testing |
| `mj_ctrl.py`, `pivot_env.py` | Pivoting rig (MuJoCo 3.15.0), stick–slip emulation, Proposition 1 shield |
| `slide_env.py` | Sliding rig, Proposition 2 timing shield |
| `train_es.py`, `train_slide.py`, `run_train*.sh` | Evolution-strategies training (5 seeds × 2 methods per task) |
| `evaluate5.py` | Test, mismatch and confirmation sets (resumable) |
| `analyze5.py`, `make_tables5.py`, `fig_*.py` | Statistics, `paper/numbers5.tex`, tables and figures |
| `validate_sim.py`, `v2_intrinsic.py`, `v6_prop1.py` | Simulator validation V1–V6 |
| `attribute_viol.py` | Exploratory replay that classifies certificate violations (Q4) |
| `ANALYSIS_slide.md`, `ANALYSIS_pivot.md` | Test-set analyses, each committed before its confirmation set was run |
| `results/` | Every evaluated episode (JSON) and `summary5.json` |
| `paper/` | LaTeX source; every number in the results text is a macro generated from `results/` |

## Reproduce
```bash
pip install mujoco==3.15.0 numpy scipy matplotlib
./run_train_slide.sh && ./run_train.sh            # ~2 h sliding, ~10 h pivoting on 2 cores
python3 evaluate5.py slide test && python3 evaluate5.py slide mismatch
python3 evaluate5.py pivot test && python3 evaluate5.py pivot mismatch
python3 evaluate5.py slide confirm && python3 evaluate5.py pivot confirm
python3 analyze5.py && python3 make_tables5.py && python3 fig_results.py
cd paper && pdflatex main.tex && pdflatex main.tex
```

## Disclosure
Simulation code, analysis and drafting were carried out with the assistance of an AI model (Claude, Anthropic) under
the author's direction. The author takes responsibility for the content.
