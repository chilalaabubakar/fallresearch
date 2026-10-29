"""Paper figures and tables, regenerated from saved results in one consistent style.

Inputs (written by the other modules):
    data/processed/wind_farm_power_<year>.csv       wind.py
    results/schedules/schedule_<case>.csv           cases.py (hourly, cases 1-4)
    results/cases/cases_summary.csv                 cases.py
    results/cases/sensitivity_summary.csv           cases.py --sensitivity all
    results/validation/validation_table.csv         validation.py
Figures whose inputs are missing are skipped with a message.

Outputs go to results/paper/ (results/paper_synthetic/ for synthetic wind):
    figXX_<name>.png and .pdf      (PDF is vector, for the journal)
    tables/T1_parameters.(csv|md)  every config parameter with unit and source
    tables/T2_cases, T3_sensitivity, T4_validation, T6_multi_year,
    T7_fuel_saving_split, T8_demand_reserve_map   (T5_economics: economics.py)

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
# Paper figures
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
    bat_txt = f"Battery (Case 4)\n{param(batt['power']):g} MW / {param(batt['energy']):g} MWh"
    _box(ax, 0.2, 1.4, 2.9, 0.95, bat_txt, pal["green_2"])
    ax.text(1.65, 5.35, "ERA5 hourly wind, 2023", ha="center", fontsize=style.FONT_SIZE - 4, color=style.TEXT_COLOR)
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
    ax.text(10.4, 0.72, "minimize fuel value + CO2 cost\n+ lost production + GT starts",
            ha="center", va="top", fontsize=style.FONT_SIZE - 5, color=style.TEXT_COLOR)
    _arrow(ax, 8.95, 2.75, 8.6, ypos["flexible"][0], ls="--", color=pal["blue_main"])
    _arrow(ax, 8.95, 2.45, 8.6, ypos["sheddable"][1], ls="--", color=pal["red_strong"])
    ax.text(8.85, 4.3, "$f_{wi}$", color=pal["blue_main"], fontsize=style.FONT_SIZE - 2)
    ax.text(8.85, 3.05, "$f_p$", color=pal["red_strong"], fontsize=style.FONT_SIZE - 2)
    ax.plot([10.4, 10.4, 3.4], [1.05, 0.85, 0.85], ls="--", lw=1.2, color=MUTED)
    _arrow(ax, 3.4, 0.85, 3.4, 2.75, ls="--", color=MUTED)
    ax.text(3.3, 0.78, "GT on/off and load", fontsize=style.FONT_SIZE - 5, color=style.TEXT_COLOR, va="top", ha="right")
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
    """Duration curves of GT load (proportional sharing) and hours with each number of running units."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
    thr = param(cfg["gas_turbine"]["low_load_threshold"]) * 100
    for k, df in sched.items():
        load = np.sort(df["gt_load_fraction"].to_numpy())[::-1] * 100
        x = np.linspace(0, 100, len(load))
        a1.plot(x, load, lw=2.2, label=case_label(cfg, k), **style.line_kwargs(k))
    a1.axhspan(0, thr, color=MUTED, alpha=0.07, lw=0)
    a1.text(98, 30, f"low load (< {thr:.0f} %)", ha="right", va="center", fontsize=style.FONT_SIZE - 3, color=style.TEXT_COLOR)
    a1.set_ylim(0, 100)
    a1.set_xlim(0, 100)
    a1.set_xlabel("Share of hours [%]")
    a1.set_ylabel("Load per running GT [% of rated]")
    a1.set_title("GT load duration", loc="left")
    if note:
        fig.suptitle(note.strip(" ()"), x=0.01, ha="left")
    a1.legend(loc="upper right", frameon=False)
    # Hours per year by number of running units: one stacked bar per case, most units first
    n_max = int(max(d["gt_units_on"].max() for d in sched.values()))
    shades = {0: "white", 1: style.PALETTE["neutral"], 2: style.PALETTE["dark"], 3: "black"}
    keys = list(sched)
    for i, k in enumerate(keys):
        units = sched[k]["gt_units_on"].round().astype(int)
        left = 0
        for n in range(n_max, -1, -1):
            h = int((units == n).sum())
            if h:
                a2.barh(i, h, left=left, height=0.6, color=shades.get(n, "black"), edgecolor="black", lw=1)
            left += h
        top = int((units == n_max).sum())       # label the hours with the most units running
        inside = top > 2500
        a2.text(top - 150 if inside else top + 150, i, f"{top:,} h", va="center", ha="right" if inside else "left",
                color="white" if inside else style.TEXT_COLOR, fontsize=style.FONT_SIZE - 2)
    a2.set_yticks(range(len(keys)), [f"Case {case_label(cfg, k).split()[0]}" for k in keys])
    a2.invert_yaxis()
    a2.set_xlim(0, 8760)
    a2.set_xticks([0, 2000, 4000, 6000, 8000])
    a2.set_xlabel("Hours per year [h]")
    a2.set_title("Hours by number of GTs running", loc="left")
    a2.legend(handles=[plt.Rectangle((0, 0), 1, 1, facecolor=shades.get(n, "black"), edgecolor="black")
                       for n in range(n_max, 0, -1)],
              labels=[f"{n} GT" + ("s" if n > 1 else "") + " running" for n in range(n_max, 0, -1)],
              loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=n_max, frameon=False)
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
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
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
    a1.text(mids.max(), target + 1.5, f"target {target:.0f} %", ha="right", fontsize=style.FONT_SIZE - 3, color=style.TEXT_COLOR)
    a1.set_xlabel("Wind power available [MW]")
    a1.set_ylabel(f"{names['injection']} [% of capacity]")
    a1.set_ylim(0, 105)
    a1.set_title(f"{names['injection']} vs available wind (Case 3)", loc="left")
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
               "gt_operation_practice": "Keep 2 GTs online", "line_pack": "Line pack buffer [h]",
               "gt_min_load": "GT minimum load [% of rated]", "pump_start_cost": "Pump start cost [kNOK]",
               "reserve_definition": "Reserve definition"}

# Panels of the sensitivity overview (prices change CO2 by < 0.1 % and are reported in the text)
OVERVIEW_GROUPS = ("wind_farm_size", "battery_size", "injection_deficit", "min_gt_online", "gt_fleet",
                   "gt_operation_practice", "gt_min_load", "pump_start_cost", "reserve_definition", "line_pack")


UNSERVED_FLAG_MWH = 1.0   # runs with more unmet demand than this are marked as not feasible


def override_label(text):
    """Short x-label for one sensitivity run, e.g. "{'battery': [8, 16]}" -> "8/16"."""
    o = ast.literal_eval(text)
    if not o:
        return "base"
    if "wind_reserve_share" in o or "injection_reserve" in o:
        if o.get("wind_reserve_share") and o.get("injection_reserve"):
            return "both"
        if o.get("wind_reserve_share"):
            return f"+{100 * o['wind_reserve_share']:.0f} %\nwind"
        return "pump\ntrip"
    if "gt_min_load" in o:
        return f"{o['gt_min_load']:.0%}"
    if "pump_start_cost" in o:
        return f"{o['pump_start_cost'] / 1000:g}"
    if "min_gt_online" in o:
        return str(o["min_gt_online"])
    if "fleet" in o:
        return "\n+ ".join(f"{n} {k}" for k, n in o["fleet"].items())
    if "battery" in o:
        return "/".join(str(v) for v in o["battery"])
    return str(next(iter(o.values())))


def fig_sensitivity_overview(cfg, sens, out_dir, note="", base=None):
    groups = [g for g in dict.fromkeys(sens["group"]) if g in OVERVIEW_GROUPS]
    if base is not None and "reserve_definition" in groups:       # base case as the first point
        ref = base[base["case"].isin(sens.loc[sens["group"] == "reserve_definition", "case"])].copy()
        ref["group"], ref["overrides"] = "reserve_definition", "{}"
        sens = pd.concat([ref[sens.columns.intersection(ref.columns)], sens], ignore_index=True)
    ncol = 3
    nrow = int(np.ceil(len(groups) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(11, 3.1 * nrow), constrained_layout=True, squeeze=False)
    for ax, g in zip(axes.flat, groups):
        d = sens[sens["group"] == g]
        for case, dd in d.groupby("case", sort=False):
            x = range(len(dd))
            ax.plot(x, dd["co2_kt"], marker="o", ms=5, lw=2, **style.line_kwargs(case),
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


def demand_reserve_table(cfg, sens, mean_demand_mw):
    """Flexibility benefit (Case 2 - Case 3) for every demand scale and reserve of the map."""
    d = sens[sens["group"] == "demand_reserve_map"].copy()
    o = d["overrides"].map(ast.literal_eval)
    d["demand_scale"], d["reserve_MW"] = o.map(lambda x: x["demand_scale"]), o.map(lambda x: x["reserve"])
    t = d.pivot_table(index=["demand_scale", "reserve_MW"], columns="case", values="co2_kt").reset_index()
    t["mean_demand_MW"] = t["demand_scale"] * mean_demand_mw
    t["benefit_kt"] = t["wind_fixed"] - t["wind_flex"]
    t["benefit_pct"] = 100 * t["benefit_kt"] / t["wind_fixed"]
    rated = cfg["gas_turbine"]["units"]["main"]["rated_power"]["value"] / 1e6
    t["margin_MW"] = rated - t["reserve_MW"] - t["mean_demand_MW"]   # one GT's headroom over the load
    return t.rename(columns={"wind_fixed": "co2_case2_kt", "wind_flex": "co2_case3_kt"})


def fig_demand_reserve_map(cfg, t, out_dir, note=""):
    """Left: benefit over demand and reserve. Right: the same points against one GT's margin."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True,
                                 gridspec_kw={"width_ratios": [1.1, 1]})
    piv = t.pivot(index="reserve_MW", columns="mean_demand_MW", values="benefit_pct")
    im = a1.imshow(piv.values, origin="lower", aspect="auto", cmap="Blues",
                   extent=[-0.5, len(piv.columns) - 0.5, -0.5, len(piv.index) - 0.5], vmin=0)
    for i, r in enumerate(piv.index):
        for j, c in enumerate(piv.columns):
            v = piv.loc[r, c]
            a1.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=style.FONT_SIZE - 3,
                    color="white" if v > 0.6 * np.nanmax(piv.values) else "black")
    a1.set_xticks(range(len(piv.columns)), [f"{c:.1f}" for c in piv.columns])
    a1.set_yticks(range(len(piv.index)), [f"{r:g}" for r in piv.index])
    a1.set_xlabel("Mean platform demand [MW]")
    a1.set_ylabel("Spinning reserve [MW]")
    a1.set_title("Flexibility benefit [% of Case 2 CO2]", loc="left")
    fig.colorbar(im, ax=a1, shrink=0.85, label="[%]")
    markers = dict(zip(sorted(t["reserve_MW"].unique()), "osD^v"))
    for r, d in t.groupby("reserve_MW"):
        a2.plot(d["margin_MW"], d["benefit_pct"], marker=markers[r], ls="-", lw=1.5, ms=7,
                color=style.PALETTE["blue_main"], alpha=0.35 + 0.65 * (r / t["reserve_MW"].max()),
                label=f"{r:g} MW reserve")
    a2.axvline(0, color=style.PALETTE["dark"], lw=1, ls="--")
    a2.set_xlabel("One GT's margin: rating − reserve − mean demand [MW]")
    a2.set_ylabel("Flexibility benefit [%]")
    a2.set_title("Benefit against the margin of one GT", loc="left")
    a2.set_ylim(0, None)
    a2.legend(frameon=False, fontsize=style.FONT_SIZE - 3)
    return save(fig, out_dir, "fig12_demand_reserve_map")


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


def sensitivity_paper_tables(sens, base, forecast=None, catch_up_co2_kt_per_h=0.0):
    """Tables 4 and 5 of the paper: one row per setting, base settings marked.

    Table 4 compares fixed (Case 2) and flexible (Case 3) demand and gives the saving from
    flexibility; Table 5 gives the battery runs (Case 4) against Case 3 without a battery.
    Forecast runs include the CO2 of catching up the injection deficit left at the end."""
    def co2(group, case, overrides=None):
        if group == "base":
            return float(base.loc[base["case"] == case, "co2_kt"].iloc[0])
        d = sens[(sens["group"] == group) & (sens["case"] == case)]
        hit = d[d["overrides"].map(ast.literal_eval) == overrides]
        return float(hit["co2_kt"].iloc[0]) if len(hit) else np.nan

    def fc(case, mode, overrides=None):
        d = forecast[(forecast["case"] == case) & (forecast["forecast"] == mode)]
        d = d[d["overrides"].fillna("{}").map(ast.literal_eval) == (overrides or {})]
        r = d.iloc[0]
        return float(r["co2_kt"] + r["end_deficit_h"] * catch_up_co2_kt_per_h)

    b2, b3 = co2("base", "wind_fixed"), co2("base", "wind_flex")
    rows = []

    def add(inp, setting, c2, c3):
        rows.append({"Varied input": inp, "Setting": setting, "Case 2 [kt/yr]": c2, "Case 3 [kt/yr]": c3})

    for n, mw in ((1, 15), (2, 30), (3, 45), (4, 60)):
        g = ("base",) if n == 2 else ("wind_farm_size",)
        o = None if n == 2 else {"n_turbines": n}
        add("Wind farm size", f"{mw} MW" + (" (base)" if n == 2 else ""),
            co2(*g, "wind_fixed", o) if o else b2, co2(*g, "wind_flex", o) if o else b3)
    for h in (0, 24, 72, 168):
        add("Injection deficit limit", f"{h} h" + (" (base)" if h == 72 else ""), b2,
            b3 if h == 72 else co2("injection_deficit", "wind_flex", {"max_deficit": h}))
    add("GT fleet", "3 main (base)", b2, b3)
    for label, fl in (("2 main + 1 small", {"main": 2, "small": 1}), ("3 main + 1 small", {"main": 3, "small": 1})):
        add("GT fleet", label, co2("gt_fleet", "wind_fixed", {"fleet": fl}), co2("gt_fleet", "wind_flex", {"fleet": fl}))
    add("GT operating practice", "at least 1 GT online (base)", b2, b3)
    add("GT operating practice", "2 GTs always online", co2("gt_operation_practice", "wind_fixed", {"min_gt_online": 2}),
        co2("gt_operation_practice", "wind_flex", {"min_gt_online": 2}))
    for ml in (0.161, 0.3, 0.4, 0.5):
        o = {"gt_min_load": ml}
        add("GT minimum load", f"{ml:.0%}".replace("%", " %") + (" (base)" if ml == 0.161 else ""),
            b2 if ml == 0.161 else co2("gt_min_load", "wind_fixed", o), b3 if ml == 0.161 else co2("gt_min_load", "wind_flex", o))
    for c in (0, 1000, 5000, 20000):
        add("Pump start cost", f"{c:,} NOK" + (" (base)" if c == 0 else ""), b2,
            b3 if c == 0 else co2("pump_start_cost", "wind_flex", {"pump_start_cost": c}))
    add("Reserve definition", "5 MW (base)", b2, b3)
    for label, o in (("5 MW + 50 % of wind used", {"wind_reserve_share": 0.5}),
                     ("5 MW + 100 % of wind used", {"wind_reserve_share": 1.0}),
                     ("injection pumps count as reserve", {"injection_reserve": True})):
        add("Reserve definition", label, co2("reserve_definition", "wind_fixed", o), co2("reserve_definition", "wind_flex", o))
    if forecast is not None:
        add("Wind forecast (hourly re-planning)", "actual wind, deficit repaid in each plan",
            fc("wind_fixed", "perfect"), fc("wind_flex", "perfect"))
        add("Wind forecast (hourly re-planning)", "persistence, deficit repaid in each plan",
            fc("wind_fixed", "persistence"), fc("wind_flex", "persistence"))
        for share in (0.25, 0.5):
            add("Wind forecast (hourly re-planning)", f"persistence, deficit valued at {share:.0%}".replace("%", " %"),
                fc("wind_fixed", "persistence"), fc("wind_flex", "persistence", {"deficit_terminal_share": share}))
    t4 = pd.DataFrame(rows)
    t4["Saving [kt/yr]"] = t4["Case 2 [kt/yr]"] - t4["Case 3 [kt/yr]"]
    t4["Saving [%]"] = 100 * t4["Saving [kt/yr]"] / t4["Case 2 [kt/yr]"]

    rows = []
    for pw, en in ((0, 0), (2, 2), (4, 4), (8, 8), (8, 16)):
        c4 = co2("battery_size", "wind_flex_battery", {"battery": [pw, en]})
        rows.append({"Battery": "none" if pw == 0 else f"{pw} MW / {en} MWh" + (" (base)" if pw == 4 else ""),
                     "Min. GTs online": 1, "Case 4 [kt/yr]": c4})
    rows.append({"Battery": "8 MW / 8 MWh", "Min. GTs online": 0,
                 "Case 4 [kt/yr]": co2("min_gt_online", "wind_flex_battery", {"min_gt_online": 0, "battery": [8, 8]})})
    t5 = pd.DataFrame(rows)
    t5["Saving vs Case 3 [kt/yr]"] = b3 - t5["Case 4 [kt/yr]"]
    t5["Saving vs Case 3 [%]"] = 100 * t5["Saving vs Case 3 [kt/yr]"] / b3
    return t4, t5


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
    if {"wind_fixed", "wind_flex"} <= set(sched):
        from topside import gas_turbine as _gt
        dec = cases.fuel_saving_decomposition(sched["wind_fixed"], sched["wind_flex"],
                                              _gt.gas_turbine_from_config(cfg, "main"),
                                              _gt.fuel_gas_from_config(cfg).lhv)
        write_table(pd.DataFrame([{"comparison": "Case 2 -> Case 3", **dec}]), tables, "T7_fuel_saving_split")
    if sched:
        attempt("fig06", fig_gt_load_duration, cfg, sched, out, note)
        attempt("fig08", fig_monthly_co2, cfg, sched, out, note)
    else:
        print("skip fig05-08: no hourly schedules; run `python -m topside.cases` first")

    if inp["sensitivity"] is not None:
        attempt("fig09", fig_sensitivity_overview, cfg, inp["sensitivity"], out, note, inp["summary"])
        if (inp["sensitivity"]["group"] == "demand_reserve_map").any() and inp["summary"] is not None:
            sched_flex = inp["schedules"].get("wind_fixed")
            mean_mw = sched_flex["p_demand_W"].mean() / 1e6 if sched_flex is not None else 18.8
            drm = demand_reserve_table(cfg, inp["sensitivity"], mean_mw)
            write_table(drm, tables, "T8_demand_reserve_map")
            attempt("fig12", fig_demand_reserve_map, cfg, drm, out, note)
        fpath = results_path(cfg, f"cases/forecast_summary{tag}.csv")
        from topside import scheduler as _sch
        _s = _sch.build_system(cfg, dp)
        t4, t5 = sensitivity_paper_tables(inp["sensitivity"], inp["summary"],
                                          pd.read_csv(fpath) if fpath.exists() else None,
                                          _sch.catch_up_fuel(_s) * _s.fuel.co2_factor / 1e6)
        write_table(t4, tables, "T4_sensitivity_flexibility")
        write_table(t5, tables, "T5_sensitivity_battery")
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

    multi = results_path(cfg, f"cases/multi_year_summary{tag}.csv")
    if multi.exists():
        summary = pd.read_csv(multi)
        for ext in ("pdf", "png"):
            p = cases.plot_multi_year(summary, out / f"fig11_multi_year.{ext}", note)
        made.append(p)
        write_table(summary, tables, "T6_multi_year")
    else:
        print("skip fig11: run `python -m topside.cases --year 2014-2023` first")

    params = parameter_table(cfg)
    write_table(params, tables, "T1_parameters")
    print(f"\n{len(made)} figures and tables in {out}")
    print(f"Parameters: {len(params)} total, {int(params['assumption'].sum())} still marked ASSUMPTION")
    return made


if __name__ == "__main__":
    main()
