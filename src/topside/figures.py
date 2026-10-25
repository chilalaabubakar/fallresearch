"""Paper figures and tables, regenerated from saved results in one consistent style.

Inputs (written by the other modules):
    data/processed/wind_farm_power_<year>.csv       wind.py
    results/schedules/schedule_<case>.csv           cases.py (hourly, cases 1-4)
    results/cases/cases_summary.csv                 cases.py
    results/cases/sensitivity_summary.csv           cases.py --sensitivity all
    results/validation/validation_table.csv         validation.py
Figures whose inputs are missing are skipped with a message.

Outputs go to results/paper/ (results/paper_synthetic/ for synthetic wind):
    figXX_<name>.png and .pdf      (PDF is vector, for the thesis/journal)
    tables/T1_parameters.(csv|md)  every config parameter with unit and source
    tables/T2_cases.(csv|md), T3_sensitivity, T4_validation

Run from the repository root:
    python -m topside.figures [--synthetic]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, repo_path
from topside import cases, scheduler

CASE_ORDER = ["gt_only", "wind_fixed", "wind_flex", "wind_flex_battery"]
CASE_COLOR = cases.CASE_COLOR
INK, MUTED = "#0b0b0b", "#52514e"


def set_style():
    plt.rcParams.update({
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.alpha": 0.25, "grid.linewidth": 0.5, "savefig.dpi": 300, "figure.dpi": 100,
    })


def save(fig, out_dir, name):
    """Save a figure as PNG and PDF; returns the PNG path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out_dir / f"{name}.{ext}")
    plt.close(fig)
    return out_dir / f"{name}.png"


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------
def load_inputs(cfg, synthetic):
    tag = "_synthetic" if synthetic else ""
    out = {"tag": tag, "note": " (SYNTHETIC wind, demo only)" if synthetic else ""}
    try:
        out["wind"], _ = scheduler.load_wind(cfg, synthetic)
    except SystemExit as e:
        print(f"skip wind: {e}")
    sched = {}
    for k in CASE_ORDER:
        p = repo_path(f"results/schedules/schedule_{k}{tag}.csv")
        if p.exists():
            sched[k] = pd.read_csv(p, index_col=0, parse_dates=True)
    out["schedules"] = sched
    for key, rel in (("summary", f"results/cases/cases_summary{tag}.csv"),
                     ("sensitivity", f"results/cases/sensitivity_summary{tag}.csv"),
                     ("validation", f"results/validation/validation_table{tag}.csv")):
        p = repo_path(rel)
        out[key] = pd.read_csv(p) if p.exists() else None
    return out


def case_label(cfg, key):
    return cfg["cases"][key]["label"]


# --------------------------------------------------------------------------
# New figures
# --------------------------------------------------------------------------
def fig_wind_resource(cfg, wind_W, out_dir, note=""):
    """Monthly capacity factor and duration curve of wind farm power."""
    installed = param(cfg["wind"]["farm"]["n_turbines"]) * param(cfg["wind"]["turbine"]["rated_power"])
    cf = wind_W / installed
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
    monthly = cf.groupby(cf.index.month).mean()
    a1.bar(monthly.index, monthly.values * 100, color="#2a78d6", width=0.6)
    a1.axhline(cf.mean() * 100, color=MUTED, lw=1, ls="--")
    a1.text(12.4, cf.mean() * 100, f"annual {cf.mean():.0%}", va="bottom", ha="right", color=MUTED, fontsize=8)
    a1.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    a1.set_ylabel("Capacity factor [%]")
    a1.set_title(f"Monthly capacity factor{note}", loc="left")
    exceed, v = np.linspace(0, 100, len(cf)), np.sort(wind_W.values)[::-1] / 1e6
    a2.plot(exceed, v, color="#2a78d6", lw=2)
    a2.axhline(installed / 1e6, color=MUTED, lw=0.8, ls="--")
    a2.set_xlabel("Share of hours power is equalled or exceeded [%]")
    a2.set_ylabel("Wind farm power [MW]")
    a2.set_title(f"Duration curve, {installed / 1e6:.0f} MW installed", loc="left")
    a2.set_xlim(0, 100)
    a2.set_ylim(0, installed / 1e6 * 1.08)
    return save(fig, out_dir, "fig01_wind_resource")


def representative_week(fixed, flexible):
    """Index of the full week whose fuel saving (fixed - flexible) is closest to the median."""
    saving = (fixed["fuel_Sm3"] - flexible["fuel_Sm3"]).to_numpy()
    n_weeks = len(saving) // 168
    weekly = saving[: n_weeks * 168].reshape(n_weeks, 168).sum(axis=1)
    return int(np.argmin(np.abs(weekly - np.median(weekly))))


def fig_example_week(cfg, sched, out_dir, note=""):
    w = representative_week(sched["wind_fixed"], sched["wind_flex"])
    sl = slice(w * 168, (w + 1) * 168)
    results = {case_label(cfg, k): sched[k].iloc[sl] for k in ("wind_fixed", "wind_flex")}
    path = scheduler.plot_schedule(results, out_dir / "fig05_example_week.png",
                                   f" - week {w + 1} (median fuel saving){note}")
    scheduler.plot_schedule(results, out_dir / "fig05_example_week.pdf",
                            f" - week {w + 1} (median fuel saving){note}")
    return path


def fig_gt_load_duration(cfg, sched, out_dir, note=""):
    """Duration curves of GT load (proportional sharing) and number of running units."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
    thr = param(cfg["gas_turbine"]["low_load_threshold"]) * 100
    for k, df in sched.items():
        load = np.sort(df["gt_load_fraction"].to_numpy())[::-1] * 100
        x = np.linspace(0, 100, len(load))
        a1.plot(x, load, color=CASE_COLOR[k], lw=2, label=case_label(cfg, k))
        units = np.sort(df["gt_units_on"].to_numpy())[::-1]
        a2.step(x, units, color=CASE_COLOR[k], lw=2, where="post", label=case_label(cfg, k))
    a1.axhspan(0, thr, color=MUTED, alpha=0.07, lw=0)
    a1.text(98, thr - 2, f"low load (< {thr:.0f} %)", ha="right", va="top", fontsize=8, color=MUTED)
    a1.set_ylim(0, 100)
    a1.set_xlim(0, 100)
    a1.set_xlabel("Share of hours [%]")
    a1.set_ylabel("Load per running GT [% of rated]")
    a1.set_title(f"GT load duration{note}", loc="left")
    a1.legend(loc="upper right", frameon=False)
    a2.set_xlim(0, 100)
    a2.set_xlabel("Share of hours [%]")
    a2.set_ylabel("GTs running")
    a2.set_yticks(range(0, int(max(d["gt_units_on"].max() for d in sched.values())) + 1))
    a2.set_title("Number of GTs running", loc="left")
    return save(fig, out_dir, "fig06_gt_load_duration")


def fig_monthly_co2(cfg, sched, out_dir, note=""):
    fig, ax = plt.subplots(figsize=(8, 3.8), constrained_layout=True)
    keys = [k for k in CASE_ORDER if k in sched]
    width = 0.8 / len(keys)
    for i, k in enumerate(keys):
        m = sched[k]["co2_kg"].groupby(sched[k].index.month).sum() / 1e6
        ax.bar(m.index + (i - (len(keys) - 1) / 2) * width, m.values, width=width * 0.92,
               color=CASE_COLOR[k], label=case_label(cfg, k))
    ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    ax.set_ylabel("CO2 emitted [kt/month]")
    ax.set_title(f"Monthly CO2 emissions{note}", loc="left")
    ax.legend(frameon=False, ncol=2)
    ax.grid(axis="x", visible=False)
    return save(fig, out_dir, "fig07_monthly_co2")


def fig_injection_mechanism(cfg, sched, out_dir, note=""):
    """How the flexible case moves water injection with the wind."""
    df = sched["wind_flex"]
    target = param(cfg["flexibility"]["water_injection"]["target_fraction"]) * 100
    bins = np.arange(0, df["wind_avail_W"].max() / 1e6 + 2, 2)
    grp = pd.cut(df["wind_avail_W"] / 1e6, bins)
    stats = df.groupby(grp, observed=True)["f_wi"].agg(["mean", lambda s: s.quantile(0.1),
                                                        lambda s: s.quantile(0.9), "size"])
    stats.columns = ["mean", "p10", "p90", "n"]
    mids = np.array([iv.mid for iv in stats.index])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
    a1.fill_between(mids, stats["p10"] * 100, stats["p90"] * 100, color="#1baf7a", alpha=0.18, lw=0,
                    label="10-90 % of hours")
    a1.plot(mids, stats["mean"] * 100, color="#1baf7a", lw=2, marker="o", ms=4, label="Mean")
    a1.axhline(target, color=MUTED, lw=1, ls="--")
    a1.text(mids.max(), target + 1.5, f"target {target:.0f} %", ha="right", fontsize=8, color=MUTED)
    a1.set_xlabel("Wind power available [MW]")
    a1.set_ylabel("Water injection [% of capacity]")
    a1.set_ylim(0, 105)
    a1.set_title(f"Injection follows the wind (case 3){note}", loc="left")
    a1.legend(frameon=False, loc="lower right")
    a2.hist(df["deficit_h"], bins=40, color="#1baf7a", alpha=0.8)
    a2.axvline(param(cfg["flexibility"]["water_injection"]["max_deficit"]), color=MUTED, lw=1, ls="--")
    a2.set_xlabel("Injection deficit [h of full-rate injection]")
    a2.set_ylabel("Hours")
    a2.set_title("How much injection is postponed", loc="left")
    return save(fig, out_dir, "fig08_injection_mechanism")


def fig_sensitivity_overview(cfg, sens, out_dir, note=""):
    groups = list(dict.fromkeys(sens["group"]))
    ncol = 3
    nrow = int(np.ceil(len(groups) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(11, 3.1 * nrow), constrained_layout=True, squeeze=False)
    for ax, g in zip(axes.flat, groups):
        d = sens[sens["group"] == g]
        for case, dd in d.groupby("case", sort=False):
            x = range(len(dd))
            ax.plot(x, dd["co2_kt"], marker="o", ms=5, lw=2, color=CASE_COLOR[case],
                    label=case_label(cfg, case))
            ax.set_xticks(list(x), [o.strip("{}").replace("'", "").split(": ", 1)[-1] for o in dd["overrides"]],
                          fontsize=7)
        ax.set_title(g.replace("_", " "), loc="left")
        ax.set_ylim(0, None)
        ax.set_ylabel("CO2 [kt/yr]")
    for ax in axes.flat[len(groups):]:
        ax.set_visible(False)
    handles, labels = {}, {}
    for ax in axes.flat[:len(groups)]:
        for h, l in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(l, h)
    fig.legend(handles.values(), handles.keys(), loc="outside lower center", ncol=3, frameon=False)
    fig.suptitle(f"Sensitivity of annual CO2{note}", x=0.01, ha="left")
    return save(fig, out_dir, "fig09_sensitivity_overview")


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------
def parameter_table(cfg):
    """Every {value, unit, source} entry in the config, flattened with its path."""
    rows = []

    def walk(node, path):
        if isinstance(node, dict):
            if {"value", "unit", "source"} <= set(node):
                src = str(node["source"])
                rows.append({"parameter": ".".join(path), "value": node["value"], "unit": node["unit"],
                             "source": src, "assumption": src.upper().startswith("ASSUMPTION")})
                return
            for k, v in node.items():
                walk(v, path + [str(k)])
    walk(cfg, [])
    return pd.DataFrame(rows)


def write_table(df, out_dir, name, float_fmt="%.4g"):
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / f"{name}.csv", index=False, float_format=float_fmt)
    with open(out_dir / f"{name}.md", "w") as f:
        f.write(df.to_markdown(index=False, floatfmt=".4g"))
    return out_dir / f"{name}.csv"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Regenerate paper figures and tables")
    ap.add_argument("--synthetic", action="store_true", help="Use synthetic-wind results (demo only)")
    args = ap.parse_args(argv)
    set_style()
    cfg = load_config()
    inp = load_inputs(cfg, args.synthetic)
    tag, note = inp["tag"], inp["note"]
    out = repo_path(f"results/paper{tag}")
    tables = out / "tables"
    made = []

    def attempt(name, fn, *a):
        try:
            made.append(fn(*a))
        except (KeyError, ValueError, TypeError) as e:
            print(f"skip {name}: missing input ({e})")

    if "wind" in inp:
        attempt("fig01", fig_wind_resource, cfg, inp["wind"], out, note)

    # Figures 2-3 come from the model itself (needs NeqSim)
    from topside import consumers, gas_turbine, process
    dp = process.design_point(cfg)
    flex = consumers.build_flexibility(cfg, dp)
    tbl = consumers.classification_table(cfg, dp)
    for ext in ("pdf", "png"):
        p = consumers.plot_flexibility(tbl, flex, out / f"fig02_demand_map.{ext}")
    made.append(p)
    fuel = gas_turbine.fuel_gas_from_config(cfg)
    gts = [gas_turbine.gas_turbine_from_config(cfg, k) for k in cfg["gas_turbine"]["units"]]
    for ext in ("pdf", "png"):
        p = gas_turbine.plot_part_load(gts, fuel, out / f"fig03_gt_part_load.{ext}")
    made.append(p)

    if inp["summary"] is not None:
        base = inp["summary"]
        for ext in ("pdf", "png"):
            p = cases.plot_base(base, out / f"fig04_cases.{ext}", note)
        made.append(p)
        cols = ["label", "co2_kt", "co2_reduction_pct", "fuel_MSm3", "gt_unit_hours", "gt_low_load_unit_hours",
                "gt_starts", "lost_production_pct", "wind_used_GWh", "wind_curtailed_GWh",
                "co2_intensity_kg_per_Sm3oe", "total_cost_MNOK"]
        write_table(base[[c for c in cols if c in base]], tables, "T2_cases")
    else:
        print("skip fig04/T2: run `python -m topside.cases` first")

    sched = inp["schedules"]
    if {"wind_fixed", "wind_flex"} <= set(sched):
        attempt("fig05", fig_example_week, cfg, sched, out, note)
        attempt("fig08", fig_injection_mechanism, cfg, sched, out, note)
    if sched:
        attempt("fig06", fig_gt_load_duration, cfg, sched, out, note)
        attempt("fig07", fig_monthly_co2, cfg, sched, out, note)
    else:
        print("skip fig05-08: no hourly schedules; run `python -m topside.cases` first")

    if inp["sensitivity"] is not None:
        attempt("fig09", fig_sensitivity_overview, cfg, inp["sensitivity"], out, note)
        write_table(inp["sensitivity"][["group", "case", "overrides", "co2_kt", "fuel_MSm3",
                                        "gt_low_load_unit_hours", "lost_production_pct",
                                        "wind_curtailed_GWh"]], tables, "T3_sensitivity")
    else:
        print("skip fig09/T3: run `python -m topside.cases --sensitivity all` first")

    if inp["validation"] is not None:
        from topside import validation
        v = inp["validation"]
        fields = validation.load_field_data(cfg)
        intensity = v.loc[v["metric"] == "co2_intensity_kg_per_boe", "model"].dropna()
        for ext in ("pdf", "png"):
            p = validation.plot_validation(v, fields, intensity.iloc[0] if len(intensity) else None,
                                           out / f"fig10_validation.{ext}", note)
        made.append(p)
        write_table(v[["benchmark", "model", "benchmark_low", "benchmark_high", "unit", "status", "source"]],
                    tables, "T4_validation")
    else:
        print("skip fig10/T4: run `python -m topside.validation` first")

    params = parameter_table(cfg)
    write_table(params, tables, "T1_parameters")
    print(f"\n{len(made)} figures and tables in {out}")
    print(f"Parameters: {len(params)} total, {int(params['assumption'].sum())} still marked ASSUMPTION")
    return made


if __name__ == "__main__":
    main()
