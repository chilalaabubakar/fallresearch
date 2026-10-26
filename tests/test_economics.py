import pandas as pd
import pytest

from topside.config import load_config
from topside import economics


def test_annuity_factors():
    assert economics.capital_recovery_factor(0.07, 20) == pytest.approx(0.09439, abs=1e-5)
    assert economics.present_value_factor(0.07, 20) == pytest.approx(10.594, abs=1e-3)


def test_abatement_cost_sign_and_value():
    # 100 MNOK investment over 20 y at 7 %, no O&M, saves 5 MNOK fuel and 1 kt CO2 per year
    c = economics.abatement_cost(100e6, 0.0, 5e6, 1e3, 0.07, 20)
    assert c == pytest.approx((100e6 * 0.094393 - 5e6) / 1e3, rel=1e-4)
    assert economics.abatement_cost(0.0, 0.0, 5e6, 1e3, 0.07, 20) < 0        # no investment: saves money


def test_economics_table_on_fake_results():
    cfg = load_config()
    rows = []
    for group, case, ov, co2, fuel in [
            ("base", "gt_only", "{}", 100.0, 200.0), ("base", "wind_fixed", "{}", 50.0, 100.0),
            ("base", "wind_flex", "{}", 45.0, 90.0), ("base", "wind_flex_battery", "{}", 44.0, 88.0),
            ("gt_fleet", "wind_flex", str({"fleet": {"main": 3}}), 45.0, 90.0),
            ("gt_fleet", "wind_flex", str({"fleet": {"main": 2, "small": 1}}), 40.0, 80.0)]:
        rows.append({"group": group, "case": case, "overrides": ov, "co2_kt": co2,
                     "fuel_value_MNOK": fuel, "co2_cost_MNOK": co2 * 2})
    t = economics.economics_table(cfg, pd.DataFrame(rows)).set_index("measure")
    flex = t.loc["Flexibility (case 3 vs 2)"]
    assert flex["co2_avoided_kt_per_yr"] == pytest.approx(5.0)
    assert flex["break_even_investment_fuel_MNOK"] == pytest.approx(10.0 * economics.present_value_factor(0.07, 20))
    wind = t.loc["Wind farm, fixed demand"]
    assert wind["investment_MNOK"] == pytest.approx(84.1 * 30, rel=1e-6)
    low, high = (float(x.replace(",", "")) for x in wind["abatement_cost_NOK_per_t"].split("–"))
    assert low < high
