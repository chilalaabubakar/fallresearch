"""Compare sites (North Sea base case vs Tanzania): one table and one figure.

Reads the results each site wrote with cases.py (results/ and results/tanzania/)
and the processed wind files. Run after both sites have been run:

    python -m topside.compare_sites

Outputs: results/comparison/site_comparison.(csv|md) and
         results/comparison/site_comparison.(png|pdf)
"""

import ast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, repo_path, results_path
from topside import gas_turbine, process, style

SITES = {"North Sea": "config/base_case.yaml", "Tanzania": "config/tanzania.yaml"}
SITE_COLOR = {"North Sea": style.PALETTE["blue_main"], "Tanzania": style.PALETTE["red_strong"]}
CASES = ["gt_only", "wind_fixed", "wind_flex", "wind_flex_battery"]
# Sensitivity group that varies each site's flexibility buffer (hours of postponable operation)
BUFFER_GROUP = {"North Sea": ("injection_deficit", "max_deficit"), "Tanzania": ("line_pack", "line_pack_hours")}


def load_site(name, path):
    cfg = load_config(path)
    year = param(cfg["site"]["year"])
    wind = pd.read_csv(repo_path(cfg["wind"]["output"]["processed_file"].format(year=year)),
                       index_col=0, parse_dates=True)
    summary = pd.read_csv(results_path(cfg, "cases/cases_summary.csv")).set_index("case")
    sens_path = results_path(cfg, "cases/sensitivity_summary.csv")
    sens = pd.read_csv(sens_path) if sens_path.exists() else None
    return {"cfg": cfg, "wind": wind, "summary": summary, "sens": sens}


def comparison_table(sites, design):
    rows = {}
    for name, s in sites.items():
        cfg, c, w = s["cfg"], s["summary"], s["wind"]
        installed = param(cfg["wind"]["farm"]["n_turbines"]) * param(cfg["wind"]["turbine"]["rated_power"])
        dp, gt, fuel = design[name]
        flex_benefit = c.loc["wind_fixed", "co2_kt"] - c.loc["wind_flex", "co2_kt"]
        rows[name] = {
            "Platform": "gas (export compression)" if process.is_gas_platform(cfg) else "oil (water injection)",
            "Design electric demand [MW]": sum(dp.power.values()) / 1e6,
            "Mean hub wind speed [m/s]": w["ws_hub_m_s"].mean(),
            "Wind capacity factor [%]": 100 * w["p_wind_W"].mean() / installed,
            "GT rating at site [MW]": gt.rated_power / 1e6,
            "Fuel CO2 factor [kg/Sm3]": fuel.co2_factor,
            "CO2 price [NOK/kg]": param(cfg["economics"]["co2_price"]),
            "Case 1 CO2 [kt/yr]": c.loc["gt_only", "co2_kt"],
            "Case 2 CO2 [kt/yr]": c.loc["wind_fixed", "co2_kt"],
            "Case 3 CO2 [kt/yr]": c.loc["wind_flex", "co2_kt"],
            "Case 4 CO2 [kt/yr]": c.loc["wind_flex_battery", "co2_kt"],
            "Wind reduction, case 2 vs 1 [%]": c.loc["wind_fixed", "co2_reduction_pct"],
            "Total reduction, case 3 vs 1 [%]": c.loc["wind_flex", "co2_reduction_pct"],
            "Flexibility benefit, case 2 - 3 [kt/yr]": flex_benefit,
            "Flexibility benefit vs case 2 [%]": 100 * flex_benefit / c.loc["wind_fixed", "co2_kt"],
            "GT low-load unit-h, case 2": c.loc["wind_fixed", "gt_low_load_unit_hours"],
            "GT low-load unit-h, case 3": c.loc["wind_flex", "gt_low_load_unit_hours"],
            "GT starts, case 2 / 3": f"{int(c.loc['wind_fixed', 'gt_starts'])} / {int(c.loc['wind_flex', 'gt_starts'])}",
            "Wind curtailed, case 3 [GWh/yr]": c.loc["wind_flex", "wind_curtailed_GWh"],
            "Lost production, case 3 [%]": c.loc["wind_flex", "lost_production_pct"],
        }
    return pd.DataFrame(rows)


def buffer_curve(site, name):
    """CO2 saving vs case 2 (%) against the size of the site's flexibility buffer (h)."""
    group, key = BUFFER_GROUP[name]
    sens = site["sens"]
    if sens is None or group not in set(sens["group"]):
        return None
    d = sens[sens["group"] == group].copy()
    d["hours"] = [ast.literal_eval(o)[key] for o in d["overrides"]]
    fixed = site["summary"].loc["wind_fixed", "co2_kt"]
    d["saving_pct"] = 100 * (fixed - d["co2_kt"]) / fixed
    return d.sort_values("hours")[["hours", "saving_pct"]]


def plot_comparison(sites, out_dir):
    style.apply_publication_style()
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    ax = axes[0]
    width = 0.38
    for i, (name, s) in enumerate(sites.items()):
        c = s["summary"]
        vals = [100 * c.loc[k, "co2_kt"] / c.loc["gt_only", "co2_kt"] for k in CASES]
        x = np.arange(len(CASES)) + (i - 0.5) * width
        ax.bar(x, vals, width=width * 0.95, color=SITE_COLOR[name], edgecolor="black", linewidth=1.0,
               label=name, hatch="" if i == 0 else "//")
        for xx, v in zip(x, vals):
            ax.text(xx, v + 1, f"{v:.0f}", ha="center", va="bottom", fontsize=style.FONT_SIZE - 4)
    ax.set_xticks(range(len(CASES)), ["1 GTs\nonly", "2 Wind\nfixed", "3 Wind\nflexible", "4 Flexible\n+ battery"])
    ax.set_ylabel("CO2 [% of case 1]")
    ax.set_ylim(0, 115)
    ax.set_title("CO2 relative to gas turbines only", loc="left")
    ax.legend()

    ax = axes[1]
    for name, s in sites.items():
        cfg, w = s["cfg"], s["wind"]
        installed = param(cfg["wind"]["farm"]["n_turbines"]) * param(cfg["wind"]["turbine"]["rated_power"])
        m = 100 * w["p_wind_W"].groupby(w.index.month).mean() / installed
        ax.plot(m.index, m.values, marker="o", ms=7, color=SITE_COLOR[name], label=name)
    ax.set_xticks(range(1, 13), list("JFMAMJJASOND"))
    ax.set_ylim(0, 100)
    ax.set_ylabel("Wind capacity factor [%]")
    ax.set_title("Monthly wind resource (ERA5 2023)", loc="left")
    ax.legend()

    ax = axes[2]
    for name, s in sites.items():
        d = buffer_curve(s, name)
        if d is not None:
            ax.plot(d["hours"], d["saving_pct"], marker="o", ms=7, color=SITE_COLOR[name],
                    label=f"{name} ({'line pack' if name == 'Tanzania' else 'injection deficit'})")
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlabel("Flexibility buffer [h of full-rate operation]")
    ax.set_ylabel("CO2 saving vs case 2 [%]")
    ax.set_ylim(0, None)
    ax.set_title("Value of the flexibility buffer", loc="left")
    ax.legend()
    fig.tight_layout(pad=1.0)
    return style.finalize_figure(fig, out_dir, "site_comparison")


def main():
    sites, design = {}, {}
    for name, path in SITES.items():
        sites[name] = load_site(name, path)
        cfg = sites[name]["cfg"]
        design[name] = (process.design_point(cfg), gas_turbine.gas_turbine_from_config(cfg, "main"),
                        gas_turbine.fuel_gas_from_config(cfg))
    table = comparison_table(sites, design)
    out = repo_path("results/comparison")
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "site_comparison.csv")
    with open(out / "site_comparison.md", "w") as f:
        f.write(table.to_markdown(floatfmt=".3g"))
    print(table.to_string(float_format=lambda v: f"{v:.3g}"))
    print("Saved", plot_comparison(sites, out))
    return table


if __name__ == "__main__":
    main()
