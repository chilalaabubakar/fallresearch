from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from topside.config import load_config
from topside import compare_sites


def fake_site(cfg, co2, sens_hours=None):
    """Small stand-in for compare_sites.load_site, with made-up numbers."""
    idx = pd.date_range("2023-01-01", periods=24 * 365, freq="h")
    wind = pd.DataFrame({"ws_hub_m_s": 8.0, "p_wind_W": 15e6}, index=idx)
    summary = pd.DataFrame({
        "case": compare_sites.CASES, "co2_kt": co2,
        "co2_reduction_pct": [100 * (1 - c / co2[0]) for c in co2],
        "gt_low_load_unit_hours": [100, 80, 50, 40], "gt_starts": [0, 10, 5, 4],
        "wind_curtailed_GWh": [0, 5, 3, 2], "lost_production_pct": [0, 0, 0.1, 0.1],
    }).set_index("case")
    sens = None
    if sens_hours is not None:
        group, key = compare_sites.BUFFER_GROUP["North Sea"]
        sens = pd.DataFrame({"group": group, "case": "wind_flex",
                             "overrides": [str({key: h}) for h in sens_hours],
                             "co2_kt": [co2[1], co2[2]]})
    return {"cfg": cfg, "wind": wind, "summary": summary, "sens": sens}


def test_comparison_table_and_buffer_curve():
    cfg = load_config()
    site = fake_site(cfg, [100.0, 50.0, 40.0, 39.0], sens_hours=[0.0, 72.0])
    dp = SimpleNamespace(power={"a": 10e6, "b": 5e6})
    design = (dp, SimpleNamespace(rated_power=20e6), SimpleNamespace(co2_factor=2.34))
    t = compare_sites.comparison_table({"North Sea": site}, {"North Sea": design})
    col = t["North Sea"]
    assert col["Design electric demand [MW]"] == pytest.approx(15.0)
    assert col["Flexibility benefit, case 2 - 3 [kt/yr]"] == pytest.approx(10.0)
    assert col["Flexibility benefit vs case 2 [%]"] == pytest.approx(20.0)
    assert col["Wind capacity factor [%]"] == pytest.approx(50.0)      # 15 of 30 MW installed
    curve = compare_sites.buffer_curve(site, "North Sea")
    assert list(curve["hours"]) == [0.0, 72.0]
    assert np.allclose(curve["saving_pct"], [0.0, 20.0])
    assert compare_sites.buffer_curve(fake_site(cfg, [1, 1, 1, 1]), "North Sea") is None
