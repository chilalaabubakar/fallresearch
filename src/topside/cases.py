"""Cases 1-4 and sensitivity analysis.

    1 gt_only            gas turbines only, fixed demand (baseline)
    2 wind_fixed         wind + gas turbines, fixed demand
    3 wind_flex          wind + gas turbines, flexible scheduling
    4 wind_flex_battery  case 3 + battery

Every case is a full-year run of scheduler.run(); the case definitions and the
sensitivity runs live in config/base_case.yaml (sections "cases" and
"sensitivity"). A sensitivity run is a base case with a few values overridden,
e.g. {n_turbines: 3} or {co2_price: 1.0}.

Runs are independent, so they can go in parallel (--jobs). Each worker starts
its own NeqSim/Java process once and then solves its runs.

Run from the repository root:
    python -m topside.cases                         # cases 1-4 (real ERA5 wind)
    python -m topside.cases --sensitivity all       # plus every sensitivity
    python -m topside.cases --synthetic --hours 336 # quick demo
"""

import argparse
import copy
import dataclasses
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, repo_path
from topside import scheduler, style

MW = 1e6
CASE_COLOR = style.CASE_COLOR


def case_keys(cfg):
    return [k for k, v in cfg["cases"].items() if isinstance(v, dict) and "label" in v]


# --------------------------------------------------------------------------
# Building one run
# --------------------------------------------------------------------------
def apply_overrides(cfg, sys_, case_key, wind_W, overrides=None):
    """System, Options and wind series (W) for one case with optional overrides."""
    overrides = dict(overrides or {})
    case = cfg["cases"][case_key]
    s = copy.copy(sys_)
    s.prices = dict(sys_.prices)

    bs = cfg["cases"]["battery_size"]
    battery = [param(bs["power"]), param(bs["energy"])] if case["battery"] else [0.0, 0.0]
    if "battery" in overrides:
        battery = overrides.pop("battery")
    fleet = dict(overrides.pop("fleet", case["fleet"]))

    n_base = param(cfg["wind"]["farm"]["n_turbines"])
    n = overrides.pop("n_turbines", n_base)
    wind = np.asarray(wind_W, dtype=float) * (n / n_base) if case["wind"] else np.zeros(len(wind_W))

    for key in ("co2_price", "gas_price"):
        if key in overrides:
            s.prices[key] = float(overrides.pop(key))
    if "min_gt_online" in overrides:
        s.min_gt_online = int(overrides.pop("min_gt_online"))
    if "max_deficit" in overrides:
        inj = dataclasses.replace(s.flex.injection, max_deficit=float(overrides.pop("max_deficit")))
        s.flex = dataclasses.replace(s.flex, injection=inj)
    if overrides:
        raise ValueError(f"Unknown override(s): {sorted(overrides)}")

    opt = scheduler.Options(fleet=fleet, flexible=case["flexible"],
                            battery_power=battery[0] * MW, battery_energy=battery[1] * MW * 3600,
                            label=case["label"])
    return s, opt, wind


def summarize_run(cfg, s, df):
    """scheduler.summarize plus costs and CO2 intensity."""
    out = scheduler.summarize(df, s)
    pr = s.prices
    produced_oil = (df["f_p"] * s.oil_rate * 3600).sum()            # Sm3
    produced_gas = (df["f_p"] * s.gas_export_rate * 3600).sum()     # Sm3
    oe = produced_oil + produced_gas / param(cfg["economics"]["gas_per_oil_equivalent"])
    fuel = df["fuel_Sm3"].sum()
    out.update({
        "fuel_value_MNOK": fuel * pr["gas_price"] / 1e6,
        "co2_cost_MNOK": df["co2_kg"].sum() * pr["co2_price"] / 1e6,
        "lost_production_MNOK": (df["lost_oil_Sm3"].sum() * pr["oil_price"]
                                 + df["lost_gas_Sm3"].sum() * pr["gas_price"]) / 1e6,
        "co2_intensity_kg_per_Sm3oe": df["co2_kg"].sum() / oe,
    })
    out["total_cost_MNOK"] = out["fuel_value_MNOK"] + out["co2_cost_MNOK"] + out["lost_production_MNOK"]
    return out


# --------------------------------------------------------------------------
# Workers (one NeqSim/Java process each)
# --------------------------------------------------------------------------
_W = {}


def _init_worker(synthetic, hours, window):
    cfg = load_config()
    sys_ = scheduler.build_system(cfg)
    if window:
        sys_.solver.update(window_hours=window[0], lookahead_hours=window[1])
    wind_W, _ = scheduler.load_wind(cfg, synthetic)
    if hours:
        wind_W = wind_W.iloc[:hours]
    _W.update(cfg=cfg, sys=sys_, wind=wind_W)


def _run_one(task):
    """task = (group, case_key, overrides, save_schedule_path or None) -> summary row."""
    group, case_key, overrides, save_path = task
    cfg, sys_, wind_W = _W["cfg"], _W["sys"], _W["wind"]
    t0 = time.time()
    s, opt, wind = apply_overrides(cfg, sys_, case_key, wind_W.values, overrides)
    df = scheduler.run(s, opt, wind, index=wind_W.index, verbose=False)
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(save_path, float_format="%.6g")
    row = {"group": group, "case": case_key, "label": cfg["cases"][case_key]["label"],
           "overrides": str(overrides or {}), **summarize_run(cfg, s, df),
           "runtime_s": round(time.time() - t0, 1)}
    print(f"  done: {group:<18} {case_key:<18} {row['overrides']:<40} {row['runtime_s']:6.1f} s", flush=True)
    return row


def run_tasks(tasks, synthetic, hours, jobs, window=None):
    if jobs <= 1:
        _init_worker(synthetic, hours, window)
        return [_run_one(t) for t in tasks]
    with ProcessPoolExecutor(max_workers=jobs, initializer=_init_worker,
                             initargs=(synthetic, hours, window)) as ex:
        return list(ex.map(_run_one, tasks))


def build_tasks(cfg, sensitivities, tag, schedules_dir):
    tasks = [("base", k, None, schedules_dir / f"schedule_{k}{tag}.csv") for k in case_keys(cfg)]
    names = list(cfg["sensitivity"]) if sensitivities == ["all"] else sensitivities
    for name in names:
        sens = cfg["sensitivity"][name]
        tasks += [(name, k, dict(r), None) for k in sens["cases"] for r in sens["runs"]]
    return tasks


# --------------------------------------------------------------------------
# Tables and figures
# --------------------------------------------------------------------------
def add_reductions(base):
    """CO2 and fuel change vs case 1 (in %)."""
    ref = base.loc[base["case"] == "gt_only"].iloc[0]
    base = base.copy()
    base["co2_reduction_pct"] = 100 * (1 - base["co2_kt"] / ref["co2_kt"])
    base["fuel_reduction_pct"] = 100 * (1 - base["fuel_MSm3"] / ref["fuel_MSm3"])
    return base


def plot_base(base, out_path, note="", period="yr"):
    """2 x 2 bars (CO2, fuel, low-load hours, lost production) + legend row; publication style."""
    style.apply_publication_style()
    metrics = [("co2_kt", f"CO2 emitted [kt/{period}]"), ("fuel_MSm3", f"Fuel gas [MSm3/{period}]"),
               ("gt_low_load_unit_hours", f"GT hours < 50 % load [unit-h/{period}]"),
               ("lost_production_pct", "Lost production [%]")]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    keys = base["case"].tolist()
    for ax, (col, title) in zip(axes.flat, metrics):
        vals = base[col].to_numpy()
        for i, (k, v) in enumerate(zip(keys, vals)):
            ax.bar(i, v, width=0.65, **style.bar_kwargs(k))
            ax.text(i, v, f"{v:,.2f}" if abs(v) < 10 else f"{v:,.0f}", ha="center", va="bottom",
                    fontsize=style.FONT_SIZE - 3, color=style.PALETTE["ink"])
        ax.set_xticks(range(len(vals)), [str(i + 1) for i in range(len(vals))])
        ax.set_title(title, loc="left")
        ax.set_ylim(0, vals.max() * 1.18 if vals.max() > 0 else 1.0)   # bars always start at zero
    handles = [plt.Rectangle((0, 0), 1, 1, **style.bar_kwargs(k)) for k in keys]
    fig.legend(handles, base["label"].tolist(), loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.06))
    if note:
        fig.suptitle(f"Cases 1-4{note}", x=0.01, ha="left")
    fig.tight_layout(pad=1.0)
    out_path = Path(out_path)
    return style.finalize_figure(fig, out_path.parent, out_path.stem, formats=(out_path.suffix.lstrip("."),))


def plot_sensitivity(sens, name, out_path, note="", period="yr"):
    """CO2 per run of one sensitivity, one line per case."""
    style.apply_publication_style()
    d = sens[sens["group"] == name]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for case, g in d.groupby("case", sort=False):
        x = range(len(g))
        ax.plot(x, g["co2_kt"], marker="o", ms=8, color=CASE_COLOR[case], label=g["label"].iloc[0])
        ax.set_xticks(list(x), [o.strip("{}").replace("'", "") for o in g["overrides"]],
                      rotation=20, ha="right")
    ax.set_ylabel(f"CO2 emitted [kt/{period}]")
    ax.set_title(f"Sensitivity: {name.replace('_', ' ')}{note}", loc="left")
    lo, hi = d["co2_kt"].min(), d["co2_kt"].max()
    pad = max((hi - lo) * 0.15, hi * 0.02)
    ax.set_ylim(max(lo - pad, 0), hi + pad)                            # line plot: tightened range
    ax.legend()
    fig.tight_layout(pad=1.0)
    out_path = Path(out_path)
    return style.finalize_figure(fig, out_path.parent, out_path.stem, formats=(out_path.suffix.lstrip("."),))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run cases 1-4 and sensitivities")
    ap.add_argument("--sensitivity", nargs="*", default=[],
                    help="Sensitivity names from the config, or 'all'")
    ap.add_argument("--synthetic", action="store_true", help="Synthetic wind (demo only)")
    ap.add_argument("--hours", type=int, default=None, help="Only the first N hours (quick test)")
    ap.add_argument("--jobs", type=int, default=4, help="Parallel worker processes")
    args = ap.parse_args(argv)

    cfg = load_config()
    tag = "_synthetic" if args.synthetic else ""
    tag += f"_{args.hours}h" if args.hours else ""
    note = " (SYNTHETIC wind, demo only)" if args.synthetic else ""
    period = f"{args.hours} h" if args.hours else "yr"
    out_dir = repo_path("results/cases")
    tasks = build_tasks(cfg, args.sensitivity, tag, repo_path("results/schedules"))
    print(f"{len(tasks)} runs on {args.jobs} worker(s)")
    t0 = time.time()
    rows = pd.DataFrame(run_tasks(tasks, args.synthetic, args.hours, args.jobs))
    print(f"All runs finished in {(time.time() - t0) / 60:.1f} min")

    base = add_reductions(rows[rows["group"] == "base"])
    out_dir.mkdir(parents=True, exist_ok=True)
    base.to_csv(out_dir / f"cases_summary{tag}.csv", index=False, float_format="%.4g")
    plot_base(base, repo_path(f"results/figures/cases_comparison{tag}.png"), note, period)
    cols = ["label", "co2_kt", "co2_reduction_pct", "fuel_MSm3", "gt_low_load_unit_hours",
            "lost_production_pct", "wind_curtailed_GWh", "co2_intensity_kg_per_Sm3oe", "total_cost_MNOK"]
    print("\n" + base[cols].to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

    sens = rows[rows["group"] != "base"]
    if len(sens):
        sens.to_csv(out_dir / f"sensitivity_summary{tag}.csv", index=False, float_format="%.4g")
        for name in sens["group"].unique():
            plot_sensitivity(sens, name, repo_path(f"results/figures/sensitivity_{name}{tag}.png"), note, period)
        print("\n" + sens[["group", "case", "overrides", "co2_kt", "fuel_MSm3", "lost_production_pct"]]
              .to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print(f"\nSaved tables in {out_dir} and figures in {repo_path('results/figures')}")
    return rows


if __name__ == "__main__":
    main()
