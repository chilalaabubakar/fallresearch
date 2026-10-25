"""Scheduler: hourly unit commitment and flexible-load scheduling (Pyomo + HiGHS).

Every hour the model chooses
    f_p      production fraction (sheddable consumers)
    f_wi     water injection fraction (flexible consumers)
    on, P    which gas turbines run and at what electric power
    w        wind power used (the rest is curtailed)
    P_heat   electric heater power (heat not covered by GT waste heat)
    ch, dis  battery charge / discharge (case 4)
to minimise, in NOK,
    fuel gas value + CO2 cost + value of lost production + GT start costs
    (+ large penalties on unserved energy or missing reserve, which should stay 0).

Constraints (power in MW and energy in MWh inside the solver, for good numerics):
    power balance   sum P + w + dis - ch = P_demand(f_p, f_wi) + P_heat
    heat balance    sum eta_h (Q - P) + eta_eh P_heat >= heat demand
    GT limits       P_min on <= P <= P_max on,  fuel Q = P_max/eta (a on) + (1-a)/eta P
    reserve         sum (P_max on - P) + battery reserve >= spinning reserve
    at least min_gt_online turbines on
    consumer curves piecewise linear (train switching), ramp limits on f_p and f_wi
    injection deficit D[t] = D[t-1] + target - f_wi[t], 0 <= D <= D_max
    battery         E[t] = E[t-1] + eta ch - dis / eta, 0 <= E <= E_max

A year is solved as rolling weekly windows with one extra day of look-ahead.
At the end of each window's horizon the injection deficit may not exceed, and
the battery energy may not fall below, their values at the window start, so
no window "borrows" from the future without paying back.

Run from the repository root (demo, two weeks, fixed vs flexible demand):
    python -m topside.scheduler [--synthetic] [--weeks 2]
"""

import argparse
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyomo.environ as pyo

from topside.config import load_config, param, param_si, repo_path
from topside import consumers, gas_turbine, process, style

MW = 1e6
SECONDS_PER_HOUR = 3600.0


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------
@dataclass
class Unit:
    key: str
    gt: gas_turbine.GasTurbine
    heat_recovery: float


@dataclass
class Options:
    """What distinguishes the cases."""
    fleet: dict                      # unit key in config -> number of units
    flexible: bool = True            # False: f_p = 1 and f_wi = target every hour
    battery_power: float = 0.0       # W
    battery_energy: float = 0.0      # J
    label: str = "case"


@dataclass
class System:
    """Everything that does not change between cases."""
    flex: consumers.PlatformFlexibility
    fuel: gas_turbine.FuelGas
    units: dict                      # key -> Unit
    oil_rate: float                  # Sm3/s at design
    gas_export_rate: float           # Sm3/s at design
    heat_demand: float               # W
    reserve: float                   # W
    min_gt_online: int
    heater_eff: float
    heater_tiebreak: float           # NOK/MWh
    low_load_threshold: float
    battery_eff: float               # round trip
    battery_reserve_duration: float  # s
    prices: dict = field(default_factory=dict)
    solver: dict = field(default_factory=dict)


def build_system(cfg, dp=None):
    dp = dp or process.design_point(cfg)
    g, s, e = cfg["gas_turbine"], cfg["scheduler"], cfg["economics"]
    units = {k: Unit(k, gas_turbine.gas_turbine_from_config(cfg, k),
                     param(g["units"][k]["heat_recovery_efficiency"])) for k in g["units"]}
    return System(
        flex=consumers.build_flexibility(cfg, dp),
        fuel=gas_turbine.fuel_gas_from_config(cfg),
        units=units,
        oil_rate=dp.oil_rate,
        gas_export_rate=dp.gas_export_rate,
        heat_demand=param_si(cfg["process"]["heat_demand"]),
        reserve=param(g["spinning_reserve"]),
        min_gt_online=param(s["min_gt_online"]),
        heater_eff=param(s["electric_heater_efficiency"]),
        heater_tiebreak=param(s["heater_tiebreak_cost"]),
        low_load_threshold=param(g["low_load_threshold"]),
        battery_eff=param(s["battery"]["round_trip_efficiency"]),
        battery_reserve_duration=param(s["battery"]["reserve_duration"]),
        prices={k: param(e[k]) for k in ("oil_price", "gas_price", "co2_price", "gt_start_cost",
                                           "unserved_energy_cost", "reserve_shortfall_cost")},
        solver={k: param(s[k]) for k in ("window_hours", "lookahead_hours", "mip_gap", "time_limit")},
    )


# --------------------------------------------------------------------------
# One window
# --------------------------------------------------------------------------
@dataclass
class State:
    """Carried from one window to the next."""
    f_p: float
    f_wi: float
    deficit: float                   # h of full-rate injection
    energy: float                    # battery, MWh
    on: dict                         # unit index -> 0/1


def build_model(sys, opt, wind_mw, state):
    """Pyomo model for one window. wind_mw: available wind power per hour (MW)."""
    fx, fuel, pr = sys.flex, sys.fuel, sys.prices
    T = range(len(wind_mw))
    unit_list = [sys.units[k] for k, n in opt.fleet.items() for _ in range(n)]
    U = range(len(unit_list))
    m = pyo.ConcreteModel()

    # --- levers and consumer power (MW)
    m.f_p = pyo.Var(T, bounds=(fx.production.min_fraction, fx.production.max_fraction))
    m.f_wi = pyo.Var(T, bounds=(fx.injection.min_fraction, fx.injection.max_fraction))
    m.p_prod = pyo.Var(T, bounds=(0, None))
    m.p_inj = pyo.Var(T, bounds=(0, None))
    px, py = fx.production_curve
    ix, iy = fx.injection_curve
    m.pw_prod = pyo.Piecewise(T, m.p_prod, m.f_p, pw_pts=[float(v) for v in px], pw_constr_type="EQ",
                              f_rule=[float(v) / MW for v in py], pw_repn="INC")
    m.pw_inj = pyo.Piecewise(T, m.p_inj, m.f_wi, pw_pts=[float(v) for v in ix], pw_constr_type="EQ",
                             f_rule=[float(v) / MW for v in iy], pw_repn="INC")
    if not opt.flexible:
        for t in T:
            m.f_p[t].fix(1.0)
            m.f_wi[t].fix(fx.injection.target_fraction)

    def demand(t):
        return (fx.base_load / MW + m.p_prod[t] + m.p_inj[t]
                + fx.seawater_per_production / MW * m.f_p[t]
                + fx.seawater_per_injection / MW * m.f_wi[t])

    # ramps (fraction per hour)
    def prev(var, t, init):
        return init if t == 0 else var[t - 1]
    m.ramp_p = pyo.ConstraintList()
    m.ramp_wi = pyo.ConstraintList()
    for t in T:
        dp_ = m.f_p[t] - prev(m.f_p, t, state.f_p)
        dw_ = m.f_wi[t] - prev(m.f_wi, t, state.f_wi)
        m.ramp_p.add((-fx.production.ramp_rate, dp_, fx.production.ramp_rate))
        m.ramp_wi.add((-fx.injection.ramp_rate, dw_, fx.injection.ramp_rate))

    # injection deficit (virtual storage), 1 h steps
    m.deficit = pyo.Var(T, bounds=(0, fx.injection.max_deficit))
    m.deficit_balance = pyo.Constraint(T, rule=lambda m, t: m.deficit[t] == prev(
        m.deficit, t, state.deficit) + fx.injection.target_fraction - m.f_wi[t])
    m.deficit_end = pyo.Constraint(expr=m.deficit[T[-1]] <= state.deficit + 1e-6)

    # --- gas turbines (MW)
    m.on = pyo.Var(U, T, domain=pyo.Binary)
    m.start = pyo.Var(U, T, bounds=(0, 1))
    m.p_gt = pyo.Var(U, T, bounds=(0, None))
    m.q_gt = pyo.Var(U, T, bounds=(0, None))     # fuel power, MW (LHV)
    m.gt = pyo.ConstraintList()
    for u, unit in enumerate(unit_list):
        g = unit.gt
        pmax, a, eta = g.rated_power / MW, g.no_load_fuel_fraction, g.rated_efficiency
        for t in T:
            m.gt.add(m.p_gt[u, t] <= pmax * m.on[u, t])
            m.gt.add(m.p_gt[u, t] >= g.min_load * pmax * m.on[u, t])
            m.gt.add(m.q_gt[u, t] == pmax / eta * a * m.on[u, t] + (1 - a) / eta * m.p_gt[u, t])
            on_before = m.on[u, t - 1] if t > 0 else state.on.get(u, 1)
            m.gt.add(m.start[u, t] >= m.on[u, t] - on_before)
            # identical units: use them in order (removes symmetric solutions)
            if u > 0 and unit_list[u - 1].key == unit.key:
                m.gt.add(m.on[u, t] <= m.on[u - 1, t])
    m.min_online = pyo.Constraint(T, rule=lambda m, t: sum(m.on[u, t] for u in U)
                                  >= min(sys.min_gt_online, len(unit_list)))

    # --- wind, heater, battery, slacks (MW / MWh)
    m.w = pyo.Var(T, bounds=lambda m, t: (0, float(wind_mw[t])))
    m.p_heat = pyo.Var(T, bounds=(0, None))
    m.unserved = pyo.Var(T, bounds=(0, None))
    m.res_short = pyo.Var(T, bounds=(0, None))
    pb, eb = opt.battery_power / MW, opt.battery_energy / MW / SECONDS_PER_HOUR
    eta_b = math.sqrt(sys.battery_eff)
    m.ch = pyo.Var(T, bounds=(0, pb))
    m.dis = pyo.Var(T, bounds=(0, pb))
    m.energy = pyo.Var(T, bounds=(0, eb))
    m.r_bat = pyo.Var(T, bounds=(0, pb))
    m.battery = pyo.Constraint(T, rule=lambda m, t: m.energy[t] == prev(m.energy, t, state.energy)
                               + eta_b * m.ch[t] - m.dis[t] / eta_b)
    m.battery_end = pyo.Constraint(expr=m.energy[T[-1]] >= state.energy - 1e-6)
    m.r_bat_power = pyo.Constraint(T, rule=lambda m, t: m.r_bat[t] <= pb - m.dis[t])
    m.r_bat_energy = pyo.Constraint(T, rule=lambda m, t: m.r_bat[t] * sys.battery_reserve_duration
                                    / SECONDS_PER_HOUR <= m.energy[t])

    m.power_balance = pyo.Constraint(T, rule=lambda m, t: sum(m.p_gt[u, t] for u in U) + m.w[t]
                                     + m.dis[t] - m.ch[t] + m.unserved[t] == demand(t) + m.p_heat[t])
    m.heat_balance = pyo.Constraint(T, rule=lambda m, t: sum(
        unit_list[u].heat_recovery * (m.q_gt[u, t] - m.p_gt[u, t]) for u in U)
        + sys.heater_eff * m.p_heat[t] >= sys.heat_demand / MW)
    m.reserve = pyo.Constraint(T, rule=lambda m, t: sum(
        unit_list[u].gt.rated_power / MW * m.on[u, t] - m.p_gt[u, t] for u in U)
        + m.r_bat[t] + m.res_short[t] >= sys.reserve / MW)

    # --- objective (NOK)
    sm3_per_mwh = MW * SECONDS_PER_HOUR / fuel.lhv
    fuel_cost_per_sm3 = pr["gas_price"] + fuel.co2_factor * pr["co2_price"]
    lost_value_per_h = (sys.oil_rate * pr["oil_price"] + sys.gas_export_rate * pr["gas_price"]) * SECONDS_PER_HOUR
    m.cost = pyo.Objective(expr=sum(
        sum(m.q_gt[u, t] for u in U) * sm3_per_mwh * fuel_cost_per_sm3
        + (1 - m.f_p[t]) * lost_value_per_h
        + pr["gt_start_cost"] * sum(m.start[u, t] for u in U)
        + sys.heater_tiebreak * m.p_heat[t]
        + (pr["unserved_energy_cost"] * m.unserved[t] + pr["reserve_shortfall_cost"] * m.res_short[t])
        for t in T))
    m.unit_list = unit_list
    return m


def solve(m, sys):
    solver = pyo.SolverFactory("appsi_highs")
    solver.options["mip_rel_gap"] = sys.solver["mip_gap"]
    solver.options["time_limit"] = float(sys.solver["time_limit"])
    res = solver.solve(m, load_solutions=False)
    tc = res.solver.termination_condition
    if tc not in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.maxTimeLimit):
        raise RuntimeError(f"Solver ended with {tc}")
    m.solutions.load_from(res)
    return str(tc)


def extract(m, sys, hours):
    """Hourly results (SI units) for the first `hours` steps of a solved window."""
    v = pyo.value
    T, U = range(hours), range(len(m.unit_list))
    rows = []
    for t in T:
        r = {
            "f_p": v(m.f_p[t]), "f_wi": v(m.f_wi[t]), "deficit_h": v(m.deficit[t]),
            "p_demand_W": (v(m.p_prod[t]) + v(m.p_inj[t])) * MW + sys.flex.base_load
            + sys.flex.seawater_per_production * v(m.f_p[t]) + sys.flex.seawater_per_injection * v(m.f_wi[t]),
            "p_heater_W": v(m.p_heat[t]) * MW,
            "wind_avail_W": m.w[t].ub * MW, "wind_used_W": v(m.w[t]) * MW,
            "battery_ch_W": v(m.ch[t]) * MW, "battery_dis_W": v(m.dis[t]) * MW,
            "battery_energy_J": v(m.energy[t]) * MW * SECONDS_PER_HOUR,
            "unserved_W": v(m.unserved[t]) * MW, "reserve_short_W": v(m.res_short[t]) * MW,
        }
        p_gt, q_gt, n_on, cap_on, starts = 0.0, 0.0, 0, 0.0, 0
        for u in U:
            on = round(v(m.on[u, t]))
            p, q = v(m.p_gt[u, t]) * MW, v(m.q_gt[u, t]) * MW
            r[f"gt{u}_on"], r[f"gt{u}_W"] = on, p
            p_gt, q_gt, n_on = p_gt + p, q_gt + q, n_on + on
            cap_on += on * m.unit_list[u].gt.rated_power
            starts += round(v(m.start[u, t]))
        # Fuel is linear in power, so for identical units the split between them does
        # not change fuel and the solver's split is arbitrary. Load is therefore reported
        # as shared in proportion to rating (droop sharing, as in real operation).
        load = p_gt / cap_on if cap_on > 0 else 0.0
        low = n_on if (n_on and load < sys.low_load_threshold) else 0
        r["gt_load_fraction"] = load
        fuel_sm3 = q_gt * SECONDS_PER_HOUR / sys.fuel.lhv
        r.update({"gt_total_W": p_gt, "gt_units_on": n_on, "gt_low_load_units": low, "gt_starts": starts,
                  "fuel_Sm3": fuel_sm3, "co2_kg": fuel_sm3 * sys.fuel.co2_factor,
                  "lost_oil_Sm3": (1 - r["f_p"]) * sys.oil_rate * SECONDS_PER_HOUR,
                  "lost_gas_Sm3": (1 - r["f_p"]) * sys.gas_export_rate * SECONDS_PER_HOUR})
        rows.append(r)
    return rows


# --------------------------------------------------------------------------
# Rolling horizon over the whole series
# --------------------------------------------------------------------------
def run(sys, opt, wind_W, index=None, verbose=True):
    """Schedule a whole wind series (W, hourly). Returns an hourly DataFrame."""
    wind_mw = np.asarray(wind_W, dtype=float) / MW
    n = len(wind_mw)
    window, look = int(sys.solver["window_hours"]), int(sys.solver["lookahead_hours"])
    n_units = sum(opt.fleet.values())
    state = State(f_p=1.0, f_wi=sys.flex.injection.target_fraction, deficit=0.0,
                  energy=0.5 * opt.battery_energy / MW / SECONDS_PER_HOUR,
                  on={u: 1 for u in range(n_units)})
    rows, t0 = [], time.time()
    for start in range(0, n, window):
        stop = min(start + window + look, n)
        commit = min(window, n - start)
        m = build_model(sys, opt, wind_mw[start:stop], state)
        status = solve(m, sys)
        rows += extract(m, sys, commit)
        last = rows[-1]
        state = State(f_p=last["f_p"], f_wi=last["f_wi"], deficit=last["deficit_h"],
                      energy=last["battery_energy_J"] / MW / SECONDS_PER_HOUR,
                      on={u: last[f"gt{u}_on"] for u in range(n_units)})
        if verbose:
            print(f"  [{opt.label}] hours {start:5d}-{start + commit - 1:5d}: {status}, "
                  f"{time.time() - t0:5.1f} s")
    df = pd.DataFrame(rows)
    if index is not None:
        df.index = index[:n]
    return df


def summarize(df, sys):
    """Annual (or period) totals in reporting units."""
    h = SECONDS_PER_HOUR
    return {
        "hours": len(df),
        "fuel_MSm3": df["fuel_Sm3"].sum() / 1e6,
        "co2_kt": df["co2_kg"].sum() / 1e6,
        "lost_oil_kSm3": df["lost_oil_Sm3"].sum() / 1e3,
        "lost_production_pct": 100 * (1 - df["f_p"].mean()),
        "gt_unit_hours": int(df["gt_units_on"].sum()),
        "gt_low_load_unit_hours": int(df["gt_low_load_units"].sum()),
        "gt_starts": int(df["gt_starts"].sum()),
        "wind_used_GWh": df["wind_used_W"].sum() * h / 3.6e12,
        "wind_curtailed_GWh": (df["wind_avail_W"] - df["wind_used_W"]).sum() * h / 3.6e12,
        "heater_GWh": df["p_heater_W"].sum() * h / 3.6e12,
        "mean_injection_fraction": df["f_wi"].mean(),
        "end_deficit_h": df["deficit_h"].iloc[-1],
        "unserved_MWh": df["unserved_W"].sum() / MW,
        "reserve_short_MWh": df["reserve_short_W"].sum() / MW,
    }


# --------------------------------------------------------------------------
# Figure and demo
# --------------------------------------------------------------------------
def plot_schedule(results, out_path, title_note=""):
    """Compare schedules (dict label -> DataFrame) over the same period."""
    labels = list(results)
    fig, axes = plt.subplots(len(labels) + 1, 1, figsize=(11, 3 * (len(labels) + 1)),
                             sharex=True, constrained_layout=True)
    for ax, lab in zip(axes, labels):
        df = results[lab]
        x = df.index
        ax.stackplot(x, df["gt_total_W"] / MW, df["wind_used_W"] / MW,
                     colors=[style.SOURCE_COLOR["gt"], style.SOURCE_COLOR["wind"]], labels=["Gas turbines", "Wind used"], lw=0)
        ax.plot(x, (df["p_demand_W"] + df["p_heater_W"]) / MW, color=style.PALETTE["ink"], lw=1.8,
                label="Demand incl. heater")
        ax.plot(x, df["wind_avail_W"] / MW, color=style.PALETTE["blue_main"], lw=1.2, ls=":", label="Wind available")
        ax.set_ylabel("Power [MW]")
        ax.set_title(f"{lab}{title_note}", loc="left")
        ax.set_ylim(0, max(df["wind_avail_W"].max(), (df["p_demand_W"] + df["p_heater_W"]).max()) / MW * 1.3)
        ax.legend(loc="upper left", frameon=False, fontsize=style.FONT_SIZE - 3, ncol=4)
    ax = axes[-1]
    for lab, color in zip(labels, [style.CASE_COLOR["wind_fixed"], style.CASE_COLOR["wind_flex"],
                                   style.CASE_COLOR["wind_flex_battery"], style.CASE_COLOR["gt_only"]]):
        ax.plot(results[lab].index, results[lab]["f_wi"] * 100, color=color, lw=1.2,
                label=f"Injection, {lab}")
        ax.plot(results[lab].index, results[lab]["f_p"] * 100, color=color, lw=1.2, ls="--",
                label=f"Production, {lab}")
    ax.set_ylabel("Rate [% of design]")
    ax.set_ylim(0, 105)
    ax.set_title("Lever positions", loc="left")
    ax.legend(loc="lower right", frameon=False, fontsize=style.FONT_SIZE - 3, ncol=2)
    for a in axes:
        a.grid(alpha=0.25, lw=0.5)
        a.spines[["top", "right"]].set_visible(False)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    return out_path


def load_wind(cfg, synthetic=False):
    """Hourly wind farm power (W) from wind.py output, or the synthetic demo series."""
    from topside import wind
    year = param(cfg["site"]["year"])
    path = repo_path(cfg["wind"]["output"]["processed_file"].format(year=year))
    if synthetic:
        return wind.build_wind_power(cfg, wind.synthetic_wind_speed(year)["ws100"])["p_wind_W"], True
    if not path.exists():
        raise SystemExit(f"{path} not found. Run `python -m topside.wind` first, or use --synthetic.")
    return pd.read_csv(path, index_col=0, parse_dates=True)["p_wind_W"], False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Demo: fixed vs flexible demand with wind")
    ap.add_argument("--synthetic", action="store_true", help="Use synthetic wind (demo only)")
    ap.add_argument("--weeks", type=int, default=2)
    args = ap.parse_args(argv)

    cfg = load_config()
    sys_ = build_system(cfg)
    wind_W, synthetic = load_wind(cfg, args.synthetic)
    wind_W = wind_W.iloc[: args.weeks * 168]
    fleet = {"main": param(cfg["gas_turbine"]["units"]["main"]["n_installed"])}
    tag = "_synthetic" if synthetic else ""
    note = " (SYNTHETIC wind, demo only)" if synthetic else ""

    results = {}
    for label, flexible in (("Fixed demand", False), ("Flexible demand", True)):
        df = run(sys_, Options(fleet=fleet, flexible=flexible, label=label), wind_W.values,
                 index=wind_W.index)
        results[label] = df
        print(f"\n{label}:")
        for k, v in summarize(df, sys_).items():
            print(f"  {k:>24}: {v:.3f}" if isinstance(v, float) else f"  {k:>24}: {v}")
    out = plot_schedule(results, repo_path(f"results/figures/schedule_demo{tag}.png"), note)
    print(f"Saved {out}")
    return results


if __name__ == "__main__":
    main()
