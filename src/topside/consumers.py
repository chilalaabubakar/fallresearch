"""Consumer classification and flexibility limits.

Every topside consumer is put in one class and tied to one operating lever:

    must_run   base load (utilities, living quarters, safety systems)
    flexible   water injection pumps   - lever: injection fraction f_wi
    sheddable  compression, oil pumps  - lever: production fraction f_p
    mixed      seawater lift pumps     - cooling part ~ f_p, make-up part ~ f_wi

Platform power then splits into three parts that the scheduler can handle
separately:

    P(f_p, f_wi) = P_base + P_prod(f_p) + P_inj(f_wi) + seawater(f_p, f_wi)

P_prod and P_inj are piecewise linear (trains switching on/off and minimum
flow make them kinked), so they are given to the scheduler as breakpoints.
The seawater lift pumps are small (well below 1 MW) and modelled as linear in
both levers, ignoring their train/minimum-flow effects.

Water injection works like a battery: postponing injection builds a deficit
D (hours of full-rate injection) that must be paid back later:

    D[t] = D[t-1] + (target - f_wi[t]) * dt,     0 <= D <= max_deficit

Run from the repository root:
    python -m topside.consumers
"""

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, repo_path
from topside import process

CLASS_COLORS = {"must_run": "#2a78d6", "flexible": "#1baf7a", "sheddable": "#eb6834",
                "mixed": "#6250d6"}
CLASS_LABELS = {"must_run": "Must-run", "flexible": "Flexible (deferrable)",
                "sheddable": "Sheddable (lost production)", "mixed": "Mixed"}
PRODUCTION_CONSUMERS = ("recompression", "export_compressor", "oil_export_pump")
INJECTION_CONSUMERS = ("water_injection_pump",)


@dataclass(frozen=True)
class LeverLimits:
    min_fraction: float
    max_fraction: float
    ramp_rate: float            # fraction of design per hour


@dataclass(frozen=True)
class InjectionLimits(LeverLimits):
    target_fraction: float
    max_deficit: float          # h of full-rate injection


@dataclass(frozen=True)
class PlatformFlexibility:
    """Everything the scheduler needs about the demand side (power in W)."""
    base_load: float
    production_curve: tuple     # (fractions, power W) breakpoints, sheddable consumers
    injection_curve: tuple      # (fractions, power W) breakpoints, flexible consumers
    seawater_per_production: float   # W per unit f_p
    seawater_per_injection: float    # W per unit f_wi
    production: LeverLimits
    injection: InjectionLimits

    def power(self, f_p, f_wi):
        """Total platform electric power (W) for lever settings."""
        return (self.base_load
                + np.interp(f_p, *self.production_curve)
                + np.interp(f_wi, *self.injection_curve)
                + self.seawater_per_production * np.asarray(f_p)
                + self.seawater_per_injection * np.asarray(f_wi))


# --------------------------------------------------------------------------
# Building the curves
# --------------------------------------------------------------------------
def simplify_breakpoints(x, y, tol=1.0):
    """Drop points that lie on a straight line between their neighbours (tol in W)."""
    keep = [0]
    for i in range(1, len(x) - 1):
        j = keep[-1]
        y_line = y[j] + (y[i + 1] - y[j]) * (x[i] - x[j]) / (x[i + 1] - x[j])
        if abs(y[i] - y_line) > tol:
            keep.append(i)
    keep.append(len(x) - 1)
    return x[keep], y[keep]


def lever_curve(cfg, dp, names, f_min, f_max, step=0.001):
    """Summed power (W) of the named consumers vs lever fraction, as breakpoints.

    Always includes 0 (lever fully off -> 0 W) so the scheduler can switch
    the whole group off when min_fraction allows it.
    """
    cons = cfg["process"]["consumers"]
    f = np.round(np.arange(max(f_min, step), f_max + step / 2, step), 6)
    p = sum(process.consumer_power(dp.power[n], f, cons[n]["n_trains"], param(cons[n]["min_flow"]))
            for n in names)
    x, y = simplify_breakpoints(f, p)
    if f_min <= 0:
        x, y = np.concatenate([[0.0], x]), np.concatenate([[0.0], y])
    return x, y


def seawater_coefficients(dp):
    """Linear split of seawater lift power into production- and injection-driven parts.

    Seawater flow = cooling * f_p + (injection * f_wi - produced water * f_p);
    lift power is proportional to flow.
    """
    sw_design = dp.seawater_cooling_rate + max(dp.water_injection_rate - dp.produced_water_rate, 0.0)
    w_per_m3s = dp.power["seawater_lift_pump"] / sw_design
    per_prod = w_per_m3s * (dp.seawater_cooling_rate - dp.produced_water_rate)
    per_inj = w_per_m3s * dp.water_injection_rate
    return per_prod, per_inj


def _limits(entry, cls=LeverLimits, **extra):
    return cls(min_fraction=param(entry["min_fraction"]), max_fraction=param(entry["max_fraction"]),
               ramp_rate=param(entry["ramp_rate"]), **extra)


def build_flexibility(cfg, dp=None):
    """Assemble PlatformFlexibility from the config (runs NeqSim if dp is not given)."""
    dp = dp or process.design_point(cfg)
    fx = cfg["flexibility"]
    prod = _limits(fx["production"])
    wi = fx["water_injection"]
    inj = _limits(wi, InjectionLimits, target_fraction=param(wi["target_fraction"]),
                  max_deficit=param(wi["max_deficit"]))
    sw_p, sw_i = seawater_coefficients(dp)
    return PlatformFlexibility(
        base_load=dp.power["base_load"],
        production_curve=lever_curve(cfg, dp, PRODUCTION_CONSUMERS, prod.min_fraction, prod.max_fraction),
        injection_curve=lever_curve(cfg, dp, INJECTION_CONSUMERS, inj.min_fraction, inj.max_fraction),
        seawater_per_production=sw_p,
        seawater_per_injection=sw_i,
        production=prod,
        injection=inj,
    )


# --------------------------------------------------------------------------
# Checking a schedule
# --------------------------------------------------------------------------
def injection_deficit(f_wi, target, dt=1.0, d0=0.0):
    """Cumulative injection deficit (h of full-rate injection) after each step."""
    return d0 + np.cumsum((target - np.asarray(f_wi, dtype=float)) * dt)


def check_schedule(flex, f_p, f_wi, dt=1.0, tol=1e-6):
    """List of rule violations for an hourly schedule (empty list = feasible)."""
    f_p, f_wi = np.asarray(f_p, dtype=float), np.asarray(f_wi, dtype=float)
    problems = []
    for name, f, lim in (("production", f_p, flex.production), ("injection", f_wi, flex.injection)):
        if f.min() < lim.min_fraction - tol or f.max() > lim.max_fraction + tol:
            problems.append(f"{name} outside [{lim.min_fraction}, {lim.max_fraction}]")
        if len(f) > 1 and np.abs(np.diff(f)).max() > lim.ramp_rate * dt + tol:
            problems.append(f"{name} ramp above {lim.ramp_rate}/h")
    d = injection_deficit(f_wi, flex.injection.target_fraction, dt)
    if d.min() < -tol:
        problems.append("injection deficit below zero (over-injection ahead of target)")
    if d.max() > flex.injection.max_deficit + tol:
        problems.append(f"injection deficit above {flex.injection.max_deficit} h")
    return problems


# --------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------
def classification_table(cfg, dp):
    classes = cfg["flexibility"]["classes"]
    lever = {**{n: "production fraction" for n in PRODUCTION_CONSUMERS},
             **{n: "injection fraction" for n in INJECTION_CONSUMERS},
             "seawater_lift_pump": "both", "base_load": "none"}
    rows = [{"consumer": n, "label": process.LABELS[n], "class": classes[n],
             "lever": lever[n], "design_power_MW": dp.power[n] / 1e6} for n in dp.power]
    t = pd.DataFrame(rows).sort_values("design_power_MW", ascending=False)
    t["share_of_total"] = t["design_power_MW"] / t["design_power_MW"].sum()
    return t


def plot_flexibility(table, flex, out_path):
    """Left: design power per consumer by class. Right: power vs lever position."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True,
                                   gridspec_kw={"width_ratios": [1, 1.1]})
    t = table.iloc[::-1]
    ax1.barh(t["label"], t["design_power_MW"], color=[CLASS_COLORS[c] for c in t["class"]],
             height=0.6)
    for y, (v, s) in enumerate(zip(t["design_power_MW"], t["share_of_total"])):
        ax1.text(v + 0.15, y, f"{v:.1f} MW ({s:.0%})", va="center", fontsize=8, color="#52514e")
    ax1.set_xlabel("Electric power at design [MW]")
    ax1.set_title("Demand map by flexibility class", loc="left")
    ax1.set_xlim(0, t["design_power_MW"].max() * 1.35)
    used = list(dict.fromkeys(table["class"]))
    ax1.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=CLASS_COLORS[c]) for c in used],
               labels=[CLASS_LABELS[c] for c in used], loc="lower right", frameon=False, fontsize=8)

    for (x, y), cls, label in ((flex.production_curve, "sheddable", "Production lever (sheddable)"),
                               (flex.injection_curve, "flexible", "Injection lever (flexible)")):
        ax2.plot(np.asarray(x) * 100, np.asarray(y) / 1e6, color=CLASS_COLORS[cls], lw=2, label=label)
    ax2.axvspan(0, flex.production.min_fraction * 100, color="#52514e", alpha=0.07, lw=0)
    ax2.text(flex.production.min_fraction * 50, 0.3, "below min.\nproduction", ha="center",
             fontsize=8, color="#52514e")
    ax2.set_xlabel("Lever position [% of design]")
    ax2.set_ylabel("Electric power [MW]")
    ax2.set_title("Power vs lever position", loc="left")
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, None)
    ax2.legend(loc="upper left", frameon=False, fontsize=9)
    for ax in (ax1, ax2):
        ax.grid(alpha=0.25, lw=0.5, axis="x" if ax is ax1 else "both")
        ax.spines[["top", "right"]].set_visible(False)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def main():
    cfg = load_config()
    dp = process.design_point(cfg)
    flex = build_flexibility(cfg, dp)
    table = classification_table(cfg, dp)
    print(table.to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    by_class = table.groupby("class")["design_power_MW"].sum()
    print("\nDesign power by class [MW]:", ", ".join(f"{k} {v:.1f}" for k, v in by_class.items()))
    p_full = flex.power(1.0, 1.0)
    p_min = flex.power(flex.production.min_fraction, flex.injection.min_fraction)
    p_target = flex.power(1.0, flex.injection.target_fraction)
    print(f"Power at full production, full injection:   {p_full / 1e6:6.2f} MW")
    print(f"Power at full production, target injection: {p_target / 1e6:6.2f} MW")
    print(f"Power at minimum production, no injection:  {p_min / 1e6:6.2f} MW")
    print(f"Flexible range without losing production:   {(p_full - flex.power(1.0, 0.0)) / 1e6:6.2f} MW")
    print(f"Production curve breakpoints: {len(flex.production_curve[0])}, "
          f"injection curve breakpoints: {len(flex.injection_curve[0])}")

    out_csv = repo_path(cfg["flexibility"]["output"]["table_file"])
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_csv, index=False, float_format="%.3f")
    out_fig = plot_flexibility(table, flex, repo_path(cfg["flexibility"]["output"]["figure_file"]))
    print(f"Saved {out_csv}\nSaved {out_fig}")
    return flex


if __name__ == "__main__":
    main()
