import numpy as np
import pandas as pd
import pytest

from topside.config import load_config
from topside import figures


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def fake_schedule(fuel, hours=24 * 7 * 3, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", periods=hours, freq="h")
    return pd.DataFrame({
        "fuel_Sm3": fuel, "co2_kg": np.asarray(fuel) * 2.34,
        "gt_load_fraction": rng.uniform(0.16, 0.9, hours), "gt_units_on": rng.integers(1, 3, hours),
        "f_wi": rng.uniform(0, 1, hours), "deficit_h": rng.uniform(0, 72, hours),
        "wind_avail_W": rng.uniform(0, 26e6, hours),
    }, index=idx)


def test_parameter_table_covers_config(cfg):
    t = figures.parameter_table(cfg)
    assert {"parameter", "value", "unit", "source", "assumption"} <= set(t.columns)
    assert "fuel_gas.co2_emission_factor" in set(t["parameter"])
    assert t["assumption"].any() and not t["assumption"].all()
    assert t["source"].str.len().min() > 0


def test_representative_week_is_the_median_week():
    hours = 168 * 3
    fixed = pd.DataFrame({"fuel_Sm3": np.ones(hours)})
    # weekly savings 168 * (0.1, 0.5, 0.9) -> median is week index 1
    saving = np.repeat([0.1, 0.5, 0.9], 168)
    flexible = pd.DataFrame({"fuel_Sm3": 1 - saving})
    assert figures.representative_week(fixed, flexible) == 1


def test_new_figures_render(cfg, tmp_path):
    figures.set_style()
    hours = 168 * 3
    sched = {"wind_fixed": fake_schedule(np.full(hours, 1000.0)),
             "wind_flex": fake_schedule(np.full(hours, 900.0), seed=1)}
    for fn in (figures.fig_gt_load_duration, figures.fig_monthly_co2, figures.fig_injection_mechanism):
        p = fn(cfg, sched, tmp_path)
        assert p.exists() and p.with_suffix(".pdf").exists()
    wind = pd.Series(np.full(hours, 15e6), index=sched["wind_fixed"].index)
    assert figures.fig_wind_resource(cfg, wind, tmp_path).exists()


def test_write_table(tmp_path):
    p = figures.write_table(pd.DataFrame({"a": [1.23456, 2.0]}), tmp_path, "T")
    assert p.exists() and (tmp_path / "T.md").read_text().startswith("|")
