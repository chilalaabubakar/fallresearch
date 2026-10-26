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


def test_run_cache_resumes_and_tracks_config(tmp_path):
    import copy
    import json
    cfg = load_config()
    tasks = cases.build_tasks(cfg, ["co2_price"], "", tmp_path / "s", tmp_path / "runs")
    assert all(t[4] is not None for t in tasks)
    assert len({t[4] for t in tasks}) == len(tasks)                 # one file per run
    t = tasks[1]
    t[4].parent.mkdir(parents=True)
    t[4].write_text(json.dumps({"co2_kt": 1.0}))
    done, todo = cases.cached_rows(tasks)
    assert done == {1: {"co2_kt": 1.0}} and len(todo) == len(tasks) - 1
    changed = copy.deepcopy(cfg)
    changed["economics"]["gas_price"]["value"] *= 2                 # any parameter change -> new file
    assert cases.cache_file(changed, tmp_path, t) != cases.cache_file(cfg, tmp_path, t)
    more_runs = copy.deepcopy(cfg)
    more_runs["sensitivity"]["co2_price"]["runs"].append({"co2_price": 9.0})   # run list only
    assert cases.cache_file(more_runs, tmp_path, t) == cases.cache_file(cfg, tmp_path, t)
    new_source = copy.deepcopy(cfg)
    new_source["economics"]["gas_price"]["source"] += " (accessed today)"           # citation only
    assert cases.cache_file(new_source, tmp_path, t) == cases.cache_file(cfg, tmp_path, t)


def test_multi_year_summary_and_plot(tmp_path):
    import pandas as pd
    cfg = load_config()
    base = {y: pd.DataFrame({"case": cases.case_keys(cfg), "co2_kt": [100.0, 60.0, 54.0, 53.0]})
            for y in (2021, 2022)}
    s = cases.multi_year_summary(cfg, base, synthetic=True)
    years = s[pd.to_numeric(s["year"], errors="coerce").notna()]
    assert list(years["year"]) == [2021, 2022]
    assert years["flex_benefit_kt"].tolist() == [6.0, 6.0]
    assert abs(years["flex_benefit_pct"].iloc[0] - 10.0) < 1e-9
    assert set(s["year"]) >= {"mean", "min", "max"}
    assert cases.plot_multi_year(s, tmp_path / "multi.png").exists()
