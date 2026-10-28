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
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, parse_years, repo_path, results_path, with_year
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
    if "line_pack_hours" in overrides:
        prod = dataclasses.replace(s.flex.production, max_deficit=float(overrides.pop("line_pack_hours")))
        s.flex = dataclasses.replace(s.flex, production=prod)
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


def _init_worker(synthetic, hours, window, year=None):
    cfg = load_config() if year is None else with_year(load_config(), year)
    sys_ = scheduler.build_system(cfg)
    if window:
        sys_.solver.update(window_hours=window[0], lookahead_hours=window[1])
    wind_W, _ = scheduler.load_wind(cfg, synthetic)
    if hours:
        wind_W = wind_W.iloc[:hours]
    _W.update(cfg=cfg, sys=sys_, wind=wind_W)


def _run_one(task):
    """task = (group, case_key, overrides, save_schedule_path or None, cache_path or None) -> summary row.

    The row is also written to cache_path as soon as the run finishes, so finished runs
    survive if the batch is stopped before the end (see cached_rows)."""
    group, case_key, overrides, save_path, cache_path = task
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
    if cache_path:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        Path(cache_path).write_text(json.dumps(row, default=float))
    print(f"  done: {group:<18} {case_key:<18} {row['overrides']:<40} {row['runtime_s']:6.1f} s", flush=True)
    return row


def run_tasks(tasks, synthetic, hours, jobs, window=None, year=None):
    if jobs <= 1:
        _init_worker(synthetic, hours, window, year)
        return [_run_one(t) for t in tasks]
    with ProcessPoolExecutor(max_workers=jobs, initializer=_init_worker,
                             initargs=(synthetic, hours, window, year)) as ex:
        return list(ex.map(_run_one, tasks))


def build_tasks(cfg, sensitivities, tag, schedules_dir, cache_dir=None):
    tasks = [("base", k, None, schedules_dir / f"schedule_{k}{tag}.csv") for k in case_keys(cfg)]
    names = list(cfg["sensitivity"]) if sensitivities == ["all"] else sensitivities
    for name in names:
        sens = cfg["sensitivity"][name]
        tasks += [(name, k, dict(r), None) for k in sens["cases"] for r in sens["runs"]]
    return [t + (cache_file(cfg, cache_dir, t) if cache_dir else None,) for t in tasks]


# Config sections that do not change a single run (lists of runs, benchmarks)
CACHE_IGNORED_SECTIONS = ("sensitivity", "validation", "investment")


def _strip_sources(node):
    """Drop 'source' texts: editing a citation must not invalidate finished runs."""
    if isinstance(node, dict):
        return {k: _strip_sources(v) for k, v in node.items() if k != "source"}
    if isinstance(node, list):
        return [_strip_sources(v) for v in node]
    return node


def cache_file(cfg, cache_dir, task):
    """One file per run. The name hashes the config and the overrides, so a changed
    parameter never reuses an old result; editing the list of sensitivity runs or the
    benchmarks does not invalidate finished runs."""
    group, case_key, overrides = task[:3]
    relevant = _strip_sources({k: v for k, v in cfg.items() if k not in CACHE_IGNORED_SECTIONS})
    key = json.dumps([relevant, overrides], sort_keys=True, default=str)
    return Path(cache_dir) / f"{group}__{case_key}__{hashlib.sha1(key.encode()).hexdigest()[:12]}.json"


def cached_rows(tasks):
    """Split tasks into rows already on disk and tasks still to run."""
    done, todo = {}, []
    for i, t in enumerate(tasks):
        if t[4] and Path(t[4]).exists():
            done[i] = json.loads(Path(t[4]).read_text())
        else:
            todo.append((i, t))
    return done, todo


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
        if col == "lost_production_pct" and abs(vals).max() < 0.005:
            ax.set_title(title, loc="left")
            ax.text(0.5, 0.5, "No production lost\nin any case", ha="center", va="center",
                    transform=ax.transAxes, color=style.PALETTE["dark"])
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines[["left", "bottom"]].set_visible(False)
            continue
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


def multi_year_summary(cfg, base_by_year, synthetic=False):
    """One row per weather year: capacity factor, CO2 per case and the flexibility benefit."""
    from topside import wind
    installed = param(cfg["wind"]["farm"]["n_turbines"]) * param(cfg["wind"]["turbine"]["rated_power"])
    rows = []
    for year, base in sorted(base_by_year.items()):
        w, _ = scheduler.load_wind(with_year(cfg, year), synthetic)
        co2 = base.set_index("case")["co2_kt"]
        row = {"year": year, "capacity_factor_pct": 100 * w.mean() / installed}
        row.update({f"co2_kt_{k}": co2.get(k, np.nan) for k in case_keys(cfg)})
        row["flex_benefit_kt"] = co2["wind_fixed"] - co2["wind_flex"]
        row["flex_benefit_pct"] = 100 * row["flex_benefit_kt"] / co2["wind_fixed"]
        rows.append(row)
    df = pd.DataFrame(rows)
    stats = df.drop(columns="year").agg(["mean", "min", "max"])
    stats.insert(0, "year", stats.index)
    return pd.concat([df, stats], ignore_index=True)


def plot_multi_year(summary, out_path, note=""):
    """Flexibility benefit (bars) and wind capacity factor (line) per weather year."""
    style.apply_publication_style()
    d = summary[pd.to_numeric(summary["year"], errors="coerce").notna()]
    years = d["year"].astype(int).astype(str)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(years, d["flex_benefit_pct"], color=CASE_COLOR["wind_flex"], edgecolor="black", width=0.6,
           label="Flexibility benefit (case 2 - case 3)")
    ax.set_ylabel("CO2 saving vs case 2 [%]")
    ax.set_ylim(0, max(d["flex_benefit_pct"].max() * 1.3, 1))
    ax2 = ax.twinx()
    ax2.plot(years, d["capacity_factor_pct"], color=style.PALETTE["dark"], marker="o", lw=2,
             label="Wind capacity factor")
    ax2.set_ylabel("Capacity factor [%]")
    ax2.set_ylim(0, 100)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False)
    ax.set_title(f"Weather years{note}", loc="left")
    fig.tight_layout(pad=1.0)
    out_path = Path(out_path)
    return style.finalize_figure(fig, out_path.parent, out_path.stem, formats=(out_path.suffix.lstrip("."),))


def merge_years(old, new):
    """Keep the years of an earlier summary that are not in the new one; recompute mean/min/max."""
    is_year = lambda d: pd.to_numeric(d["year"], errors="coerce").notna()
    old_y, new_y = old[is_year(old)].copy(), new[is_year(new)].copy()
    for d in (old_y, new_y):
        d["year"] = d["year"].astype(float).astype(int)
    years = pd.concat([old_y[~old_y["year"].isin(new_y["year"])], new_y]).sort_values("year")
    stats = years.drop(columns="year").agg(["mean", "min", "max"])
    stats.insert(0, "year", stats.index)
    return pd.concat([years, stats], ignore_index=True)


def multi_year_report(cfg, base_by_year, synthetic=False):
    tag = "_synthetic" if synthetic else ""
    summary = multi_year_summary(cfg, base_by_year, synthetic)
    out = results_path(cfg, f"cases/multi_year_summary{tag}.csv")
    if out.exists():                       # a run for some years must not drop the others
        summary = merge_years(pd.read_csv(out), summary)
    summary.to_csv(out, index=False, float_format="%.4g")
    plot_multi_year(summary, results_path(cfg, f"figures/multi_year{tag}.png"),
                    " (SYNTHETIC wind, demo only)" if synthetic else "")
    print("\n" + summary.to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print(f"Saved {out}")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run cases 1-4 and sensitivities")
    ap.add_argument("--sensitivity", nargs="*", default=[],
                    help="Sensitivity names from the config, or 'all'")
    ap.add_argument("--synthetic", action="store_true", help="Synthetic wind (demo only)")
    ap.add_argument("--hours", type=int, default=None, help="Only the first N hours (quick test)")
    ap.add_argument("--jobs", type=int, default=4, help="Parallel worker processes")
    ap.add_argument("--fresh", action="store_true", help="Ignore finished runs saved by an earlier, stopped batch")
    ap.add_argument("--year", nargs="+", default=None,
                    help="Weather year(s) instead of site.year, e.g. 2019 or 2014-2023 (outputs tagged _<year>)")
    args = ap.parse_args(argv)

    cfg = load_config()
    default_year = param(cfg["site"]["year"])
    years = parse_years(args.year) or [default_year]
    results = {}
    for year in years:
        if len(years) > 1:
            print(f"\n=== weather year {year} ===")
        results[year] = run_year(with_year(cfg, year), args, year if year != default_year else None)
    if len(years) > 1:
        multi_year_report(cfg, {y: r[r["group"] == "base"] for y, r in results.items()}, args.synthetic)
    return results[years[-1]] if len(years) == 1 else results


def run_year(cfg, args, year_tag=None):
    """All runs of one weather year; outputs tagged _<year> unless it is the config year."""
    tag = "_synthetic" if args.synthetic else ""
    tag += f"_{year_tag}" if year_tag else ""
    tag += f"_{args.hours}h" if args.hours else ""
    note = " (SYNTHETIC wind, demo only)" if args.synthetic else ""
    period = f"{args.hours} h" if args.hours else "yr"
    out_dir = results_path(cfg, "cases")
    cache_dir = out_dir / f"runs{tag}"
    tasks = build_tasks(cfg, args.sensitivity, tag, results_path(cfg, "schedules"), cache_dir)
    done, todo = ({}, list(enumerate(tasks))) if args.fresh else cached_rows(tasks)
    print(f"{len(tasks)} runs ({len(done)} already finished) on {args.jobs} worker(s)")
    t0 = time.time()
    new = run_tasks([t for _, t in todo], args.synthetic, args.hours, args.jobs,
                    year=param(cfg["site"]["year"])) if todo else []
    done.update({i: r for (i, _), r in zip(todo, new)})
    rows = pd.DataFrame([done[i] for i in range(len(tasks))])
    print(f"All runs finished in {(time.time() - t0) / 60:.1f} min")

    base = add_reductions(rows[rows["group"] == "base"])
    out_dir.mkdir(parents=True, exist_ok=True)
    base.to_csv(out_dir / f"cases_summary{tag}.csv", index=False, float_format="%.4g")
    plot_base(base, results_path(cfg, f"figures/cases_comparison{tag}.png"), note, period)
    cols = ["label", "co2_kt", "co2_reduction_pct", "fuel_MSm3", "gt_low_load_unit_hours",
            "lost_production_pct", "wind_curtailed_GWh", "co2_intensity_kg_per_Sm3oe", "total_cost_MNOK"]
    print("\n" + base[cols].to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

    sens = rows[rows["group"] != "base"]
    if len(sens):
        sens.to_csv(out_dir / f"sensitivity_summary{tag}.csv", index=False, float_format="%.4g")
        for name in sens["group"].unique():
            plot_sensitivity(sens, name, results_path(cfg, f"figures/sensitivity_{name}{tag}.png"), note, period)
        print("\n" + sens[["group", "case", "overrides", "co2_kt", "fuel_MSm3", "lost_production_pct"]]
              .to_string(index=False, float_format=lambda v: f"{v:,.2f}"))
    print(f"\nSaved tables in {out_dir} and figures in {results_path(cfg, 'figures')}")
    return rows


if __name__ == "__main__":
    main()
