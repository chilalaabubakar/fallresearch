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
import ast
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, param_si, repo_path, results_path
from topside import cases, scheduler, style

CASE_ORDER = ["gt_only", "wind_fixed", "wind_flex", "wind_flex_battery"]
CASE_COLOR = cases.CASE_COLOR
INK, MUTED = style.PALETTE["ink"], style.PALETTE["grey"]


def set_style():
    style.apply_publication_style()


def save(fig, out_dir, name):
    """Save a figure as PNG (300 dpi) and vector PDF; returns the PNG path."""
    return style.finalize_figure(fig, out_dir, name)


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
        p = results_path(cfg, f"schedules/schedule_{k}{tag}.csv")
        if p.exists():
            sched[k] = pd.read_csv(p, index_col=0, parse_dates=True)
    out["schedules"] = sched
    for key, rel in (("summary", f"cases/cases_summary{tag}.csv"),
                     ("sensitivity", f"cases/sensitivity_summary{tag}.csv"),
                     ("validation", f"validation/validation_table{tag}.csv")):
        p = results_path(cfg, rel)
        out[key] = pd.read_csv(p) if p.exists() else None
    return out


def case_label(cfg, key):
    return cfg["cases"][key]["label"]


# --------------------------------------------------------------------------
# New figures
# --------------------------------------------------------------------------
CLASS_NAMES = {"must_run": "must-run", "flexible": "flexible (deferrable)",
               "sheddable": "sheddable", "mixed": "mixed"}


def _box(ax, x, y, w, h, text, face, edge=INK, fs=None, weight="normal", color=INK):
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=face, edgecolor=edge, linewidth=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs or style.FONT_SIZE - 3,
            weight=weight, color=color, linespacing=1.3)


def _arrow(ax, x0, y0, x1, y1, ls="-", color=INK):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", lw=1.4, ls=ls, color=color,
                                                        shrinkA=0, shrinkB=0))


def fig_system(cfg, dp, out_dir):
    """Schematic of the platform power system: supply, consumers by class, and the scheduler."""
    from topside import process
    w, g = cfg["wind"], cfg["gas_turbine"]
    n_wt, p_wt = param(w["farm"]["n_turbines"]), param(w["turbine"]["rated_power"]) / 1e6
    n_gt = int(cfg["cases"]["wind_flex"]["fleet"]["main"])
    p_gt = param(g["units"]["main"]["rated_power"]) / 1e6
    batt = cfg["cases"]["battery_size"]
    classes = cfg["flexibility"]["classes"]
    heat = param_si(cfg["process"]["heat_demand"]) / 1e6

    fig, ax = plt.subplots(figsize=(12, 5.9))
    ax.set_xlim(0, 12)
    ax.set_ylim(-0.3, 5.7)
    ax.axis("off")
    pal = style.PALETTE
    # supply side
    _box(ax, 0.2, 4.1, 2.9, 0.95, f"Wind farm\n{n_wt} × {p_wt:.0f} MW (IEA 15 MW)", pal["blue_secondary"], color="white")
    _box(ax, 0.2, 2.75, 2.9, 0.95, f"Gas turbines\n{n_gt} × {p_gt:.1f} MW (LEOGO)", pal["red_2"])
    bat_txt = f"Battery (case 4)\n{param(batt['power']):g} MW / {param(batt['energy']):g} MWh"
    _box(ax, 0.2, 1.4, 2.9, 0.95, bat_txt, pal["green_2"])
    ax.text(1.65, 5.35, "ERA5 hourly wind, 2023", ha="center", fontsize=style.FONT_SIZE - 4, color=MUTED)
    _arrow(ax, 1.65, 5.25, 1.65, 5.05, color=MUTED)
    # bus
    ax.add_patch(plt.Rectangle((3.9, 0.9), 0.16, 4.4, facecolor=INK))
    ax.text(3.98, 0.65, "platform\nAC bus", ha="center", va="top", fontsize=style.FONT_SIZE - 4)
    for y in (4.575, 3.225, 1.875):
        _arrow(ax, 3.1, y, 3.9, y)
    # consumers
    order = sorted(dp.power, key=lambda k: ["flexible", "sheddable", "mixed", "must_run"].index(classes[k]))
    y, ypos = 5.0, {}
    for k in order:
        c = classes[k]
        face = style.CLASS_COLOR[c]
        _box(ax, 5.0, y, 3.6, 0.62, f"{process.LABELS[k]}  {dp.power[k] / 1e6:.2f} MW", face, color="white")
        ypos[c] = ypos.get(c, []) + [y + 0.31]
        _arrow(ax, 4.06, y + 0.31, 5.0, y + 0.31)
        y -= 0.78
    # heat
    _box(ax, 5.0, 0.0, 3.6, 0.62, f"Heat {heat:.0f} MW: GT waste heat\n+ electric heater", pal["neutral"],
         fs=style.FONT_SIZE - 4)
    # class legend
    for i, c in enumerate(["flexible", "sheddable", "mixed", "must_run"]):
        ax.add_patch(plt.Rectangle((9.4, 4.95 - 0.42 * i), 0.3, 0.26, facecolor=style.CLASS_COLOR[c],
                                   edgecolor=INK))
        ax.text(9.8, 5.08 - 0.42 * i, CLASS_NAMES[c], va="center", fontsize=style.FONT_SIZE - 4)
    # scheduler
    _box(ax, 8.95, 1.05, 2.9, 1.95,
         "Scheduler (MILP)\nhourly, rolling 1-week\nwindows + 24 h look-ahead\n\ndecides: GT on/off and load,\n"
         "wind used, battery,\nproduction $f_p$, injection $f_{wi}$", "white", fs=style.FONT_SIZE - 5)
    ax.text(10.4, 3.1, "minimise fuel value + CO2 cost\n+ lost production + GT starts",
            ha="center", va="bottom", fontsize=style.FONT_SIZE - 5, color=MUTED)
    _arrow(ax, 8.95, 2.75, 8.6, ypos["flexible"][0], ls="--", color=pal["blue_main"])
    _arrow(ax, 8.95, 2.45, 8.6, ypos["sheddable"][1], ls="--", color=pal["red_strong"])
    ax.text(8.85, 4.3, "$f_{wi}$", color=pal["blue_main"], fontsize=style.FONT_SIZE - 2)
    ax.text(8.85, 3.05, "$f_p$", color=pal["red_strong"], fontsize=style.FONT_SIZE - 2)
    ax.plot([10.4, 10.4, 3.4], [1.05, 0.85, 0.85], ls="--", lw=1.2, color=MUTED)
    _arrow(ax, 3.4, 0.85, 3.4, 2.75, ls="--", color=MUTED)
    ax.text(3.3, 1.0, "GT on/off\nand load", fontsize=style.FONT_SIZE - 5, color=MUTED, va="bottom", ha="right")
    return save(fig, out_dir, "fig00_system")
def fig_wind_resource(cfg, wind_W, out_dir, note=""):
    """Monthly capacity factor and duration curve of wind farm power."""
    installed = param(cfg["wind"]["farm"]["n_turbines"]) * param(cfg["wind"]["turbine"]["rated_power"])
    cf = wind_W / installed
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6), constrained_layout=True)
    monthly = cf.groupby(cf.index.month).mean()
    a1.bar(monthly.index, monthly.values * 100, color=style.PALETTE["blue_secondary"], edgecolor="black", linewidth=1.2, width=0.65)
    a1.axhline(cf.mean() * 100, color=MUTED, lw=1, ls="--")
    a1.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    a1.set_ylim(0, max(monthly.max() * 100 * 1.12, cf.mean() * 100 + 8))
    a1.set_ylabel("Capacity factor [%]")
    a1.set_title(f"Monthly capacity factor (dashed: annual {cf.mean():.0%})", loc="left")
    if note:
        fig.suptitle(note.strip(" ()"), x=0.01, ha="left")
    exceed, v = np.linspace(0, 100, len(cf)), np.sort(wind_W.values)[::-1] / 1e6
    a2.plot(exceed, v, color=style.PALETTE["blue_main"])
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


LEVER_NAMES = {"production": "Production", "injection": "Water injection",
               "deficit": "Injection deficit", "postponed": "How much injection is postponed"}


def lever_names(cfg):
    """Short lever names for figures; a site config can rename them (flexibility.lever_names)."""
    return {**LEVER_NAMES, **cfg["flexibility"].get("lever_names", {})}


def fig_example_week(cfg, sched, out_dir, note=""):
    w = representative_week(sched["wind_fixed"], sched["wind_flex"])
    sl = slice(w * 168, (w + 1) * 168)
    results = {case_label(cfg, k): sched[k].iloc[sl] for k in ("wind_fixed", "wind_flex")}
    names = lever_names(cfg)
    flex = cfg["flexibility"]
    top = 100 * max(param(flex["production"]["max_fraction"]), param(flex["water_injection"]["max_fraction"]))
    kw = dict(lever_names=(names["injection"], names["production"]), rate_max=top + 5)
    path = scheduler.plot_schedule(results, out_dir / "fig05_example_week.png",
                                   f" - week {w + 1} (median fuel saving){note}", **kw)
    scheduler.plot_schedule(results, out_dir / "fig05_example_week.pdf",
                            f" - week {w + 1} (median fuel saving){note}", **kw)
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
    a1.text(98, thr - 2, f"low load (< {thr:.0f} %)", ha="right", va="top", fontsize=style.FONT_SIZE - 3, color=MUTED)
    a1.set_ylim(0, 100)
    a1.set_xlim(0, 100)
    a1.set_xlabel("Share of hours [%]")
    a1.set_ylabel("Load per running GT [% of rated]")
    a1.set_title("GT load duration", loc="left")
    if note:
        fig.suptitle(note.strip(" ()"), x=0.01, ha="left")
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
    ax.set_title(f"Monthly CO2 emissions{note}", loc="left", fontsize=style.FONT_SIZE - 1)
    ax.legend(frameon=False, ncol=2)
    ax.grid(axis="x", visible=False)
    return save(fig, out_dir, "fig08_monthly_co2")


def fig_injection_mechanism(cfg, sched, out_dir, note=""):
    """How the flexible case moves the second lever (water injection, or MEG regeneration) with the wind."""
    df = sched["wind_flex"]
    names = lever_names(cfg)
    target = param(cfg["flexibility"]["water_injection"]["target_fraction"]) * 100
    bins = np.arange(0, df["wind_avail_W"].max() / 1e6 + 2, 2)
    grp = pd.cut(df["wind_avail_W"] / 1e6, bins)
    stats = df.groupby(grp, observed=True)["f_wi"].agg(["mean", lambda s: s.quantile(0.1),
                                                        lambda s: s.quantile(0.9), "size"])
    stats.columns = ["mean", "p10", "p90", "n"]
    mids = np.array([iv.mid for iv in stats.index])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
    a1.fill_between(mids, stats["p10"] * 100, stats["p90"] * 100, color=style.PALETTE["blue_main"], alpha=0.15, lw=0,
                    label="10-90 % of hours")
    a1.plot(mids, stats["mean"] * 100, color=style.PALETTE["blue_main"], marker="o", ms=6, label="Mean")
    a1.axhline(target, color=MUTED, lw=1, ls="--")
    a1.text(mids.max(), target + 1.5, f"target {target:.0f} %", ha="right", fontsize=style.FONT_SIZE - 3, color=MUTED)
    a1.set_xlabel("Wind power available [MW]")
    a1.set_ylabel(f"{names['injection']} [% of capacity]")
    a1.set_ylim(0, 105)
    a1.set_title(f"{names['injection']} vs available wind (case 3)", loc="left")
    if note:
        fig.suptitle(note.strip(" ()"), x=0.01, ha="left")
    a1.legend(frameon=False, loc="lower right")
    a2.hist(df["deficit_h"], bins=40, color=style.PALETTE["blue_secondary"], edgecolor="black", linewidth=0.6)
    a2.axvline(param(cfg["flexibility"]["water_injection"]["max_deficit"]), color=MUTED, lw=1, ls="--")
    a2.set_xlabel(f"{names['deficit']} [h at full rate]")
    a2.set_ylabel("Hours")
    a2.set_title(names["postponed"], loc="left")
    return save(fig, out_dir, "fig07_injection_mechanism")


SENS_TITLES = {"wind_farm_size": "Wind farm size [turbines]", "co2_price": "CO2 price [NOK/kg]",
               "gas_price": "Gas price [NOK/Sm3]", "battery_size": "Battery [MW / MWh]",
               "injection_deficit": "Injection deficit limit [h]",
               "min_gt_online": "Min. GTs online (8 MW battery)", "gt_fleet": "GT fleet",
               "gt_operation_practice": "Keep 2 GTs online", "line_pack": "Line pack buffer [h]"}


UNSERVED_FLAG_MWH = 1.0   # runs with more unmet demand than this are marked as not feasible


def override_label(text):
    """Short x-label for one sensitivity run, e.g. "{'battery': [8, 16]}" -> "8/16"."""
    o = ast.literal_eval(text)
    if "min_gt_online" in o:
        return str(o["min_gt_online"])
    if "fleet" in o:
        return " + ".join(f"{n} {k}" for k, n in o["fleet"].items())
    if "battery" in o:
        return "/".join(str(v) for v in o["battery"])
    return str(next(iter(o.values())))


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
            ax.set_xticks(list(x), [override_label(o) for o in dd["overrides"]])
            bad = dd["unserved_MWh"].to_numpy() > UNSERVED_FLAG_MWH
            if bad.any():                                  # infeasible design: demand not met
                xb = np.arange(len(dd))[bad]
                ax.plot(xb, dd["co2_kt"].to_numpy()[bad], "o", ms=11, mfc="none", mec=style.PALETTE["red_strong"], mew=2)
                for xx, u in zip(xb, dd["unserved_MWh"].to_numpy()[bad]):
                    ax.annotate(f"unmet demand\n{u:,.0f} MWh", (xx, dd["co2_kt"].to_numpy()[xx]), xytext=(0, -38),
                                textcoords="offset points", ha="right", fontsize=style.FONT_SIZE - 4,
                                color=style.PALETTE["red_strong"])
        title = SENS_TITLES.get(g, g.replace("_", " "))
        if g == "injection_deficit":
            title = f"{lever_names(cfg)['deficit']} limit [h]"
        ax.set_title(title, loc="left")
        ax.set_ylim(0, d["co2_kt"].max() * 1.15)   # zero baseline: flat lines stay flat
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
    out = results_path(cfg, f"paper{tag}")
    tables = out / "tables"
    made = []

    def attempt(name, fn, *a):
        try:
            made.append(fn(*a))
        except (KeyError, ValueError, TypeError) as e:
            print(f"skip {name}: missing input ({e})")

    if "wind" in inp:
        attempt("fig01", fig_wind_resource, cfg, inp["wind"], out, note)

    # Figures 0 and 2-3 come from the model itself (needs NeqSim)
    from topside import consumers, gas_turbine, process
    dp = process.design_point(cfg)
    if not process.is_gas_platform(cfg):
        attempt("fig00", fig_system, cfg, dp, out)
    flex = consumers.build_flexibility(cfg, dp)
    tbl = consumers.classification_table(cfg, dp)
    for ext in ("pdf", "png"):
        p = consumers.plot_flexibility(tbl, flex, out / f"fig02_demand_map.{ext}",
                                       cfg["flexibility"].get("lever_labels"))
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
        attempt("fig07", fig_injection_mechanism, cfg, sched, out, note)
    if sched:
        attempt("fig06", fig_gt_load_duration, cfg, sched, out, note)
        attempt("fig08", fig_monthly_co2, cfg, sched, out, note)
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
