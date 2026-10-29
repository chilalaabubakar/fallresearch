"""Economic indicators: cost per tonne of CO2 avoided and break-even investment.

Reads the annual results written by cases.py and the `investment` section of the
config. Two indicators, both in real NOK:

* Abatement cost of a measure with a known investment (the wind farm):
      (annualised investment + O&M - value of fuel saved) / CO2 avoided   [NOK/t]
  The CO2 price is not counted as a saving, because the abatement cost is what
  is compared with the CO2 price.
* Break-even investment of a measure whose cost is not known (flexibility,
  battery, small GT): present value, over the lifetime, of the annual saving.
  Given for the fuel saved alone and for fuel plus CO2 cost.

Run after cases.py:
    python -m topside.economics
Outputs: results/paper/tables/T5_economics.(csv|md)
"""

import ast

import pandas as pd

from topside.config import load_config, param, results_path


def capital_recovery_factor(rate, years):
    """Annual payment per unit of investment (annuity)."""
    return rate / (1 - (1 + rate) ** -years)


def present_value_factor(rate, years):
    """Present value of 1 per year for `years` years."""
    return 1 / capital_recovery_factor(rate, years)


def abatement_cost(investment_nok, om_nok_per_yr, fuel_saved_nok_per_yr, co2_avoided_t, rate, years):
    """NOK per tonne of CO2 avoided (negative = the measure saves money)."""
    annual = investment_nok * capital_recovery_factor(rate, years) + om_nok_per_yr - fuel_saved_nok_per_yr
    return annual / co2_avoided_t


def _row(results, key):
    group, case, overrides = key
    d = results[(results["group"] == group) & (results["case"] == case) & (results["overrides"] == overrides)]
    if d.empty:
        raise KeyError(f"no result for {key}")
    return d.iloc[0]


def comparisons(cfg):
    """Pairs (measure, without, with) of result rows to compare."""
    small = str({"fleet": {"main": 2, "small": 1}})
    return [
        ("Wind farm, fixed demand", ("base", "gt_only", "{}"), ("base", "wind_fixed", "{}"), True),
        ("Wind farm + flexibility", ("base", "gt_only", "{}"), ("base", "wind_flex", "{}"), True),
        ("Flexibility (case 3 vs 2)", ("base", "wind_fixed", "{}"), ("base", "wind_flex", "{}"), False),
        ("Battery 4 MW / 4 MWh (case 4 vs 3)", ("base", "wind_flex", "{}"), ("base", "wind_flex_battery", "{}"), False),
        ("Small GT replacing one main GT (flexible)", ("gt_fleet", "wind_flex", str({"fleet": {"main": 3}})),
         ("gt_fleet", "wind_flex", small), False),
    ]


def economics_table(cfg, results):
    inv = cfg["investment"]
    rates = (param(inv["discount_rate"]), param(inv["discount_rate_low"]))
    years = param(inv["lifetime"])
    installed_W = param(cfg["wind"]["farm"]["n_turbines"]) * param(cfg["wind"]["turbine"]["rated_power"])
    capex = param(inv["wind_capex"]) * installed_W
    om = [param(inv[k]) * param(inv["eur_nok"]) * installed_W / 1e3 for k in ("wind_om_low", "wind_om_high")]
    rows = []
    for name, without, with_, has_capex in comparisons(cfg):
        a, b = _row(results, without), _row(results, with_)
        co2_t = (a["co2_kt"] - b["co2_kt"]) * 1e3
        fuel = (a["fuel_value_MNOK"] - b["fuel_value_MNOK"]) * 1e6
        co2_cost = (a["co2_cost_MNOK"] - b["co2_cost_MNOK"]) * 1e6
        row = {"measure": name, "co2_avoided_kt_per_yr": co2_t / 1e3, "fuel_value_saved_MNOK_per_yr": fuel / 1e6,
               "co2_cost_saved_MNOK_per_yr": co2_cost / 1e6}
        if has_capex:
            row["investment_MNOK"] = capex / 1e6
            for r, label in zip(rates, ("", "_low_rate")):
                costs = [abatement_cost(capex, o, fuel, co2_t, r, years) for o in om]
                row[f"abatement_cost_NOK_per_t{label}"] = f"{min(costs):,.0f}–{max(costs):,.0f}"
        else:
            row["abatement_cost_NOK_per_t"] = f"{-fuel / co2_t:,.0f} (no investment)"
            pv = present_value_factor(rates[0], years)
            row["break_even_investment_fuel_MNOK"] = fuel * pv / 1e6
            row["break_even_investment_fuel_co2_MNOK"] = (fuel + co2_cost) * pv / 1e6
        rows.append(row)
    return pd.DataFrame(rows)


def load_results(cfg):
    frames = [pd.read_csv(results_path(cfg, "cases/cases_summary.csv"))]
    sens = results_path(cfg, "cases/sensitivity_summary.csv")
    if sens.exists():
        frames.append(pd.read_csv(sens))
    out = pd.concat(frames, ignore_index=True)
    out["overrides"] = [str(ast.literal_eval(o)) for o in out["overrides"]]   # normalise spacing
    return out


def paper_tables(table):
    """The two economics tables of the paper, one number per cell.

    Measures with a known investment (the wind farm) get an abatement cost; measures whose
    investment is not known get the fuel value saved per tonne of CO2 avoided and the
    largest investment that still breaks even."""
    wind = table[table["investment_MNOK"].notna()]
    names = {"Wind farm, fixed demand": "Fixed demand (Case 2 vs 1)",
             "Wind farm + flexibility": "Flexible demand (Case 3 vs 1)"}
    abatement = pd.DataFrame({
        "Wind farm operated with": wind["measure"].map(names).fillna(wind["measure"]),
        "CO2 avoided [kt/yr]": wind["co2_avoided_kt_per_yr"].round(1),
        "Fuel value saved [MNOK/yr]": wind["fuel_value_saved_MNOK_per_yr"].round(1),
        "Abatement cost at 7 % [NOK/t]": wind["abatement_cost_NOK_per_t"],
        "Abatement cost at 4 % [NOK/t]": wind["abatement_cost_NOK_per_t_low_rate"]})
    other = table[table["investment_MNOK"].isna()]
    names = {"Flexibility (case 3 vs 2)": "Flexibility (Case 3 vs 2)",
             "Battery 4 MW / 4 MWh (case 4 vs 3)": "Battery 4 MW / 4 MWh (Case 4 vs 3)",
             "Small GT replacing one main GT (flexible)": "Small GT replacing one main GT (flexible demand)"}
    break_even = pd.DataFrame({
        "Measure": other["measure"].map(names).fillna(other["measure"]),
        "CO2 avoided [kt/yr]": other["co2_avoided_kt_per_yr"].round(1),
        "Fuel value saved [MNOK/yr]": other["fuel_value_saved_MNOK_per_yr"].round(1),
        # minus the abatement cost without investment, i.e. from the unrounded results
        "Fuel value per t CO2 [NOK/t]": other["abatement_cost_NOK_per_t"].map(
            lambda v: f"{-float(str(v).split()[0].replace(',', '')):,.0f}"),
        "Break-even, fuel only [MNOK]": other["break_even_investment_fuel_MNOK"].round(0),
        "Break-even, fuel + CO2 [MNOK]": other["break_even_investment_fuel_co2_MNOK"].round(0)})
    return abatement, break_even


def main():
    cfg = load_config()
    table = economics_table(cfg, load_results(cfg))
    out = results_path(cfg, "paper/tables")
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "T5_economics.csv", index=False, float_format="%.4g")
    (out / "T5_economics.md").write_text(table.to_markdown(index=False, floatfmt=",.1f"))
    for name, t in zip(("T5a_abatement_cost", "T5b_break_even"), paper_tables(table)):
        t.to_csv(out / f"{name}.csv", index=False)
        (out / f"{name}.md").write_text(t.to_markdown(index=False))
    inv = cfg["investment"]
    print(f"Discount rate {param(inv['discount_rate']):.0%} (low {param(inv['discount_rate_low']):.0%}), "
          f"lifetime {param(inv['lifetime'])} yr; power from shore benchmark "
          f"{param(inv['power_from_shore_abatement_cost']):,.0f} NOK/t")
    print(table.to_string(index=False, float_format=lambda v: f"{v:,.1f}"))
    print(f"Saved {out / 'T5_economics.csv'}")
    return table


if __name__ == "__main__":
    main()
