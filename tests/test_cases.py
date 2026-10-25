import numpy as np
import pytest

from topside.config import load_config
from topside import cases, scheduler


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def sys_(cfg):
    s = scheduler.build_system(cfg)
    s.solver.update(window_hours=24, lookahead_hours=6)
    return s


@pytest.fixture(scope="module")
def wind(cfg):
    w, _ = scheduler.load_wind(cfg, synthetic=True)
    return w.iloc[:72]


def test_config_cases_and_sensitivities_are_valid(cfg, sys_, wind):
    keys = cases.case_keys(cfg)
    assert keys == ["gt_only", "wind_fixed", "wind_flex", "wind_flex_battery"]
    for name, sens in cfg["sensitivity"].items():
        for case in sens["cases"]:
            for run in sens["runs"]:
                cases.apply_overrides(cfg, sys_, case, wind.values, run)   # raises if unknown key


def test_overrides(cfg, sys_, wind):
    s, opt, w = cases.apply_overrides(cfg, sys_, "wind_flex", wind.values, {"n_turbines": 4})
    assert np.allclose(w, wind.values * 2)                     # base case has 2 turbines
    s, opt, w = cases.apply_overrides(cfg, sys_, "gt_only", wind.values)
    assert not w.any() and not opt.flexible
    s, opt, w = cases.apply_overrides(cfg, sys_, "wind_flex", wind.values,
                                      {"max_deficit": 0, "co2_price": 3.0})
    assert s.flex.injection.max_deficit == 0 and s.prices["co2_price"] == 3.0
    assert sys_.flex.injection.max_deficit > 0                  # base system untouched
    assert sys_.prices["co2_price"] != 3.0
    with pytest.raises(ValueError):
        cases.apply_overrides(cfg, sys_, "wind_flex", wind.values, {"not_a_key": 1})


def run(cfg, sys_, wind, case, overrides=None):
    s, opt, w = cases.apply_overrides(cfg, sys_, case, wind.values, overrides)
    df = scheduler.run(s, opt, w, verbose=False)
    return cases.summarize_run(cfg, s, df)


def test_cases_are_ordered(cfg, sys_, wind):
    r = {k: run(cfg, sys_, wind, k) for k in cases.case_keys(cfg)}
    tol = 1.006   # 0.5 % MIP gap
    assert r["wind_fixed"]["co2_kt"] < r["gt_only"]["co2_kt"]
    assert r["wind_flex"]["co2_kt"] <= r["wind_fixed"]["co2_kt"] * tol
    assert r["wind_flex_battery"]["co2_kt"] <= r["wind_flex"]["co2_kt"] * tol
    assert r["gt_only"]["wind_used_GWh"] == 0


def test_zero_deficit_equals_fixed_injection(cfg, sys_, wind):
    # With no injection deficit allowed, injection must stay at target every hour
    s, opt, w = cases.apply_overrides(cfg, sys_, "wind_flex", wind.values, {"max_deficit": 0})
    df = scheduler.run(s, opt, w, verbose=False)
    assert np.allclose(df["f_wi"], s.flex.injection.target_fraction, atol=1e-6)
