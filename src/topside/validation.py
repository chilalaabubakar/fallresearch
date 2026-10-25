"""Validation: compare model results with published benchmarks and field data.

Two layers:
  1. Benchmarks from the literature (config "validation.benchmarks"): platform
     power, wind capacity factor, CO2 avoided per MWh of wind, CO2 intensity
     and water-injection specific energy.
  2. Field data you download (data/validation/field_data.csv): CO2 and
     production per field and year -> CO2 intensity in kg CO2 per boe.

Model values come from process.design_point(), the wind series and the case
results written by cases.py (results/cases/cases_summary.csv), so run
`python -m topside.cases` first.

A benchmark given as [low, high] is "within" if the model value lies inside
it; a single value "agrees" if the model is within the configured tolerance.
Disagreement is not automatically a model error: the note on each benchmark
says what differs (e.g. national averages include flaring and late-life fields).

Run from the repository root:
    python -m topside.validation [--synthetic]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, repo_path
from topside import process, scheduler

STATUS_COLOR = {"within": "#1baf7a", "agrees": "#1baf7a", "differs": "#eb6834", "n/a": "#52514e"}


# --------------------------------------------------------------------------
# Model metrics
# --------------------------------------------------------------------------
def model_metrics(cfg, dp, wind_W, cases_summary=None):
    """Model values for every benchmark metric (None if not available)."""
    w = cfg["wind"]
    installed = param(w["farm"]["n_turbines"]) * param(w["turbine"]["rated_power"])
    bbl = param(cfg["validation"]["bbl_per_Sm3"])
    m = {
        "design_power_MW": sum(dp.power.values()) / 1e6,
        "wind_capacity_factor": float(np.mean(wind_W)) / installed,
        "wi_specific_energy_kWh_per_m3": dp.power["water_injection_pump"] / dp.water_injection_rate / 3.6e6,
        "co2_avoided_t_per_MWh": None,
        "co2_intensity_kg_per_boe": None,
    }
    if cases_summary is not None:
        c = cases_summary.set_index("case")
        if {"gt_only", "wind_fixed"} <= set(c.index):
            avoided_t = (c.loc["gt_only", "co2_kt"] - c.loc["wind_fixed", "co2_kt"]) * 1e3
            m["co2_avoided_t_per_MWh"] = avoided_t / (c.loc["wind_fixed", "wind_used_GWh"] * 1e3)
            m["co2_intensity_kg_per_boe"] = c.loc["gt_only", "co2_intensity_kg_per_Sm3oe"] / bbl
    return m


def compare(cfg, metrics):
    """One row per benchmark: model value, benchmark, status."""
    tol = param(cfg["validation"]["tolerance"])
    rows = []
    for name, b in cfg["validation"]["benchmarks"].items():
        model = metrics.get(b["metric"])
        ref = b["value"]
        lo, hi = (ref if isinstance(ref, list) else (ref, ref))
        mid = (lo + hi) / 2
        if model is None:
            status = "n/a"
        elif isinstance(ref, list):
            status = "within" if lo <= model <= hi else "differs"
        else:
            status = "agrees" if abs(model / ref - 1) <= tol else "differs"
        rows.append({"benchmark": name, "metric": b["metric"], "unit": b["unit"],
                     "model": model, "benchmark_low": lo, "benchmark_high": hi,
                     "model_to_benchmark": None if model is None else model / mid,
                     "status": status, "note": b.get("note", ""), "source": b["source"]})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Field data
# --------------------------------------------------------------------------
def load_field_data(cfg, path=None):
    """Field CSV with CO2 intensity (kg CO2/boe) added; empty frame if no rows."""
    path = Path(path) if path else repo_path(cfg["validation"]["field_data_file"])
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, comment="#")
    if df.empty:
        return df
    bbl = param(cfg["validation"]["bbl_per_Sm3"])
    gas_per_oe = param(cfg["economics"]["gas_per_oil_equivalent"])
    boe = (df["oil_Sm3"] + df["gas_Sm3"] / gas_per_oe) * bbl
    df["co2_intensity_kg_per_boe"] = df["co2_t"] * 1e3 / boe
    if "co2_turbines_t" in df:
        df["co2_turbines_kg_per_boe"] = df["co2_turbines_t"] * 1e3 / boe
    return df


# --------------------------------------------------------------------------
# Figure
# --------------------------------------------------------------------------
def plot_validation(table, fields, model_intensity, out_path, note=""):
    t = table[table["status"] != "n/a"].reset_index(drop=True)
    has_fields = len(fields) > 0
    fig, axes = plt.subplots(1, 2 if has_fields else 1, figsize=(13 if has_fields else 8, 0.5 * len(t) + 2),
                             constrained_layout=True, squeeze=False)
    ax = axes[0, 0]
    tol = 0.2
    ax.axvspan(1 - tol, 1 + tol, color="#1baf7a", alpha=0.08, lw=0)
    ax.axvline(1, color="#52514e", lw=0.8)
    for i, r in t.iterrows():
        mid = (r.benchmark_low + r.benchmark_high) / 2
        if r.benchmark_high > r.benchmark_low:     # range: draw it relative to its midpoint
            ax.plot([r.benchmark_low / mid, r.benchmark_high / mid], [i, i], color="#52514e", lw=3, alpha=0.4,
                    solid_capstyle="round")
        ax.plot(r.model_to_benchmark, i, "o", ms=9, color=STATUS_COLOR[r.status])
        ax.text(r.model_to_benchmark, i - 0.32, f"{r.model:.3g} vs {r.benchmark_low:.3g}"
                + (f"-{r.benchmark_high:.3g}" if r.benchmark_high > r.benchmark_low else "") + f" {r.unit}",
                ha="center", fontsize=7, color="#52514e")
    ax.set_yticks(range(len(t)), [b.replace("_", " ") for b in t["benchmark"]], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Model / benchmark (1 = equal; shaded = within ±20 %; grey bar = published range)")
    ax.set_title(f"Model vs published benchmarks{note}", loc="left")
    ax.grid(alpha=0.25, lw=0.5, axis="x")
    ax.spines[["top", "right"]].set_visible(False)

    if has_fields:
        ax2 = axes[0, 1]
        lab = fields["field"] + " " + fields["year"].astype(str)
        colors = ["#6250d6" if str(e).lower() == "yes" else "#2a78d6" for e in fields["electrified"]]
        ax2.barh(lab, fields["co2_intensity_kg_per_boe"], color=colors, height=0.6)
        if model_intensity is not None:
            ax2.axvline(model_intensity, color="#eb6834", lw=2, label=f"Model case 1: {model_intensity:.1f}")
        ax2.set_xlabel("CO2 intensity [kg CO2/boe]")
        ax2.set_title("Field data (blue: GT-powered, violet: electrified)", loc="left")
        ax2.invert_yaxis()
        ax2.legend(frameon=False, fontsize=8)
        ax2.grid(alpha=0.25, lw=0.5, axis="x")
        ax2.spines[["top", "right"]].set_visible(False)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate the model against public data")
    ap.add_argument("--synthetic", action="store_true", help="Use synthetic-wind case results (demo only)")
    args = ap.parse_args(argv)
    cfg = load_config()
    tag = "_synthetic" if args.synthetic else ""
    note = " (SYNTHETIC wind, demo only)" if args.synthetic else ""

    dp = process.design_point(cfg)
    wind_W, _ = scheduler.load_wind(cfg, args.synthetic)
    summary_path = repo_path(f"results/cases/cases_summary{tag}.csv")
    summary = pd.read_csv(summary_path) if summary_path.exists() else None
    if summary is None:
        print(f"Note: {summary_path} not found; run `python -m topside.cases` for the CO2 checks.")
    metrics = model_metrics(cfg, dp, wind_W.values, summary)
    table = compare(cfg, metrics)
    fields = load_field_data(cfg)

    out_dir = repo_path(cfg["validation"]["output"]["table_file"]).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    table_path = repo_path(cfg["validation"]["output"]["table_file"])
    table_path = table_path.with_name(table_path.stem + tag + ".csv")
    table.to_csv(table_path, index=False, float_format="%.4g")
    fig_path = repo_path(cfg["validation"]["output"]["figure_file"])
    fig_path = plot_validation(table, fields, metrics["co2_intensity_kg_per_boe"],
                               fig_path.with_name(fig_path.stem + tag + ".png"), note)

    show = table[["benchmark", "model", "benchmark_low", "benchmark_high", "unit", "status"]]
    print(show.to_string(index=False, float_format=lambda v: f"{v:.3g}"))
    if len(fields):
        print("\nField data:")
        print(fields[["field", "year", "co2_intensity_kg_per_boe", "electrified"]]
              .to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    else:
        print(f"\nNo field data yet: fill in {cfg['validation']['field_data_file']}")
    print(f"\nSaved {table_path}\nSaved {fig_path}")
    return table


if __name__ == "__main__":
    main()
