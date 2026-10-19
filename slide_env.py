"""Controlled sliding through a parallel-jaw grasp (Paper 5, task 2).

A vertical rod hangs between two spherical pads (condim 4) at its centre of mass, so gravity acts along the rod
axis and produces no pivoting torque. The task: lower the rod through the grasp by a target distance x* (slide),
using release pulses: fast release to grip F_p, hold for tau, smooth re-clamp to 30 N, then measure the slid
distance (surrogate sensor, sigma 1 mm, one 'probe' per measurement as in the pivoting task).

Stick-slip: the sliding coefficient of all contact geoms is mu while the rod is stuck (|v_rel| < v_stick after
re-sticking) and mu/r while it slides (|v_rel| > v_slip). Breakaway grip F_b = m g / (2 mu_s).

Timing shield (Proposition 2): while the rod slides, its acceleration satisfies a(t) <= g (1 - F(t) / (r F_b)), and
r F_b <= r_max F_stuck, where F_stuck is the last grip at which the rod was observed stuck. Integrating
a_bar(t) = g (1 - F(t)/(r_max F_stuck)) over the planned force profile (velocity clipped at zero) bounds the travel
of a pulse. The shield shortens the hold tau (bisection) until the bound is within x_lim = remaining + OVER - margin.
"""
import numpy as np, mujoco

G = 9.81
DT = 0.001
OVER = 0.005          # overshoot threshold (m)
MARGIN = 0.0015       # 3 sigma sensing margin (m)
SIG = 0.0005          # surrogate position-sensor noise (m)
TOL = 0.003           # stop band (m)
REL_S, CLAMP_S = 0.1, 0.3   # release ramp and re-clamp ramp durations (s)
FMAX = 30.0
SEARCH = 0.9
MAX_STEPS = 40
RMAX = 1.1
TAU0 = 0.15           # model controller's initial hold (s)
SF, ST = 0.25, 1.0    # residual scales: F_p x[0.78,1.28], tau x[0.37,2.7]

XML = """
<mujoco>
  <option timestep="0.001" integrator="implicitfast" cone="elliptic" impratio="10" noslip_iterations="20" gravity="0 0 -9.81"/>
  <worldbody>
    <body name="palm" pos="0 0 0.5">
      <body name="lf"><joint name="lj" type="slide" axis="1 0 0" damping="300" range="0 0.03" limited="true"/>
        <geom name="lpad" type="sphere" size="0.006" pos="-0.0262 0 0" mass="0.02" condim="4" friction="{mu} 0.005 0.0001" solref="0.003 1" solimp="0.95 0.99 0.0005"/></body>
      <body name="rf"><joint name="rj" type="slide" axis="-1 0 0" damping="300" range="0 0.03" limited="true"/>
        <geom name="rpad" type="sphere" size="0.006" pos="0.0262 0 0" mass="0.02" condim="4" friction="{mu} 0.005 0.0001" solref="0.003 1" solimp="0.95 0.99 0.0005"/></body>
    </body>
    <body name="rod" pos="0 0 0.5"><freejoint/>
      <geom name="rodg" type="box" size="0.01 0.01 0.08" mass="{m}" condim="4" friction="{mu} 0.005 0.0001" solref="0.003 1" solimp="0.95 0.99 0.0005"/>
    </body>
  </worldbody>
  <actuator>
    <motor name="lgrip" joint="lj" gear="1" ctrlrange="0 40"/>
    <motor name="rgrip" joint="rj" gear="1" ctrlrange="0 40"/>
  </actuator>
</mujoco>
"""


def sample_object(rng):
    return dict(m=rng.uniform(0.05, 0.2), mu=rng.uniform(0.4, 0.8), target=rng.uniform(0.01, 0.05))


class SlideRig:
    def __init__(self, m, mu, ratio=1.0, v_slip=0.005, v_stick=0.001):
        self.model = mujoco.MjModel.from_xml_string(XML.format(m=m, mu=mu))
        self.data = mujoco.MjData(self.model)
        M = self.model
        self.mu_s, self.mu_k, self.ratio = mu, mu / ratio, ratio
        self.v_slip, self.v_stick = v_slip, v_stick
        self.sliding = False; self.n_breakaway = 0
        self._g = [M.geom(g).id for g in ("lpad", "rpad", "rodg")]
        self._rod = M.body("rod").id; self._vel = np.zeros(6)
        self.grip = FMAX; self.t_sim = 0.0
        for j in ("lj", "rj"):                       # start with pads touching the rod (as in the pivot rig)
            self.data.qpos[M.joint(j).qposadr[0]] = 0.0262 - 0.01 - 0.006 + 0.0002
        self.data.ctrl[:] = [FMAX, FMAX]
        self.z0 = None
        self.step(0.8); self.z0 = self.z()

    def z(self):
        return float(self.data.xpos[self._rod][2])

    def slid(self):
        return self.z0 - self.z()

    def held(self):
        return self.slid() < 0.07

    def mj1(self):
        if self.ratio != 1.0 and self.z0 is not None:
            mujoco.mj_objectVelocity(self.model, self.data, mujoco.mjtObj.mjOBJ_BODY, self._rod, self._vel, 0)
            v = abs(self._vel[5])
            if not self.sliding and v > self.v_slip:
                self.sliding = True; self.n_breakaway += 1
                self.model.geom_friction[self._g, 0] = self.mu_k
            elif self.sliding and v < self.v_stick:
                self.sliding = False
                self.model.geom_friction[self._g, 0] = self.mu_s
        mujoco.mj_step(self.model, self.data)

    def step(self, secs):
        for _ in range(int(round(secs / DT))): self.mj1()
        self.t_sim += secs

    def pulse(self, F_p, tau):
        """Fast release to F_p, hold tau, smooth re-clamp to FMAX, settle."""
        for F0, F1, T in ((self.grip, F_p, REL_S), (F_p, F_p, tau), (F_p, FMAX, CLAMP_S)):
            n = max(1, int(round(T / DT)))
            for k in range(n):
                self.data.ctrl[:] = F0 + (F1 - F0) * (k + 1) / n
                self.mj1()
            self.t_sim += T
        self.grip = FMAX
        self.step(0.5)


def profile(F_from, F_p, tau):
    """Planned grip profile (same as SlideRig.pulse), sampled at 1 ms."""
    a = np.linspace(F_from, F_p, int(round(REL_S / DT)) + 1)[1:]
    b = np.full(int(round(tau / DT)), F_p)
    c = np.linspace(F_p, FMAX, int(round(CLAMP_S / DT)) + 1)[1:]
    return np.concatenate([a, b, c])


def travel_bound(F_prof, F_stuck, r_max):
    """Proposition 2: undamped worst-case travel for a planned grip profile, rod initially at rest."""
    abar = G * (1.0 - F_prof / (r_max * F_stuck))
    v = 0.0; x = 0.0
    for a in abar:
        v = max(0.0, v + a * DT); x += v * DT
        if v == 0.0 and a <= 0: continue
    return x


def shield_tau(F_from, F_p, tau, F_stuck, r_max, x_lim):
    """Largest hold <= tau whose travel bound is <= x_lim; None if even tau = 0 violates (infeasible)."""
    if travel_bound(profile(F_from, F_p, 0.0), F_stuck, r_max) > x_lim:
        return None
    if travel_bound(profile(F_from, F_p, tau), F_stuck, r_max) <= x_lim:
        return tau
    lo, hi = 0.0, tau
    for _ in range(20):
        mid = 0.5 * (lo + hi)
        if travel_bound(profile(F_from, F_p, mid), F_stuck, r_max) <= x_lim: lo = mid
        else: hi = mid
    return lo


def features(x, target, F_last, F0, k, moved, tau_last):
    rem = target - x
    return np.array([rem / 0.05, x / 0.05, target / 0.05, np.log(max(F_last, 1e-3) / F0), k / MAX_STEPS,
                     float(moved), np.log(tau_last / TAU0), 1.0])


OBS_DIM = 8


class SlideEpisode:
    def __init__(self, obj, rng):
        self.o = obj; self.rng = rng
        self.r = SlideRig(obj["m"], obj["mu"], ratio=obj.get("ratio", 1.0))
        self.rmax = obj.get("rmax", RMAX)
        self.probes = 0

    def measure(self):
        self.probes += 1
        return self.r.slid() + self.rng.normal(0, SIG)

    def run(self, mode="model", policy=None):
        r, target = self.r, self.o["target"]
        x0 = self.measure(); x = x0
        m_est = self.o["m"] * self.rng.uniform(0.9, 1.1)          # weight from wrist sensing, +-10%
        F0 = min(FMAX, m_est * G / (2 * 0.3) / SEARCH)              # first pulse at the mu = 0.3 grip
        F_last = F0; F_stuck = FMAX; moved = False; tau = TAU0; last_dx = 0.0; k_corr = 1.0; pred_dx = None
        n_clip = n_defer = n_cert = n_viol = n_steps = 0; declined = False
        shielded = mode in ("modelS", "residualS", "modelSd", "residualSd")
        for k in range(MAX_STEPS):
            if not r.held() or target - x <= TOL: break
            rem = target - x
            # ---- model proposal (assumes r = 1, Coulomb, quasi-static breakaway, constant accel) ----
            if not moved:
                F_p, tau_m = F_last * SEARCH, TAU0
            else:
                F_p = F_stuck * 0.95          # release just below the last stuck grip
                # Coulomb (r = 1) prediction with F_b ~ F_stuck: dx = 0.5 g (1 - F_p/F_b) tau^2, corrected by the
                # ratio of observed to predicted travel on the previous pulse (k_corr)
                acc = G * (1 - F_p / F_stuck) * k_corr
                tau_m = float(np.clip(np.sqrt(2 * 0.7 * rem / max(acc, 1e-3)), 0.02, 1.0))
            if mode.startswith("residual"):
                a = np.clip(policy(features(x, target, F_last, F0, k, moved, tau)), -1, 1)
                F_pol = float(np.clip(F_p * np.exp(SF * a[0]), 0.3, F_stuck * 0.995))
                tau_pol = float(np.clip(tau_m * np.exp(ST * a[1]), 0.0, 1.5))
            else:
                F_pol, tau_pol = F_p, tau_m
            F_cmd, tau_cmd, cert = F_pol, tau_pol, None
            if shielded:
                x_lim = rem + OVER - MARGIN
                t_ok = shield_tau(FMAX, F_cmd, tau_cmd, F_stuck, self.rmax, x_lim)
                if t_ok is not None:
                    if t_ok < tau_cmd - 1e-9: n_clip += 1
                    tau_cmd = t_ok; cert = x_lim
                else:
                    n_defer += 1
                    if mode.endswith("Sd"):
                        declined = True; break
                    F_cmd, tau_cmd = F_p, tau_m
            xb = r.slid()
            r.pulse(F_cmd, tau_cmd)
            n_steps += 1
            dx_true = r.slid() - xb
            if cert is not None:
                n_cert += 1
                if dx_true > cert: n_viol += 1
            xn = self.measure()
            last_dx = xn - x
            if moved and pred_dx is not None and last_dx > 0:
                k_corr = float(np.clip(k_corr * last_dx / max(pred_dx, 1e-5), 0.1, 10.0))
            pred_dx = 0.5 * G * (1 - F_cmd / F_stuck) * k_corr * tau_cmd ** 2 if moved else None
            if not moved:
                if last_dx > 0.0025:
                    moved = True
                else:
                    F_stuck = min(F_stuck, F_cmd)   # search phase: no motion at F_cmd => F_b <= F_cmd
            elif last_dx < 0.0005 and tau_cmd >= 0.5:
                moved = False; k_corr = 1.0       # false detection: a long hold produced no motion; resume search
                F_stuck = min(F_stuck, F_cmd)
            F_last = F_cmd; tau = max(tau_cmd, 0.02); x = xn
        final = r.slid()
        return dict(final=final, err=final - target, held=r.held(), t_sim=r.t_sim, probes=self.probes,
                    steps=n_steps, n_clip=n_clip, n_defer=n_defer, n_cert=n_cert, n_viol=n_viol,
                    n_breakaway=r.n_breakaway, declined=declined)


def score(res, lam=0.5):
    if not res["held"]:
        return -10.0
    return -abs(res["err"]) / OVER - lam * res["probes"] / 10.0


class LinearPolicy:
    def __init__(self, w=None):
        self.w = np.zeros((2, OBS_DIM)) if w is None else w.reshape(2, OBS_DIM)

    def __call__(self, o):
        return np.tanh(self.w @ o)
