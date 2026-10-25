import numpy as np
import pandas as pd
import pytest

from topside.config import load_config
from topside import process, validation


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def dp(cfg):
    return process.design_point(cfg)


def fake_summary():
    # 100 kt in case 1, 60 kt in case 2 with 80 GWh wind used -> 0.5 t/MWh avoided
    return pd.DataFrame({
        "case": ["gt_only", "wind_fixed"],
        "co2_kt": [100.0, 60.0],
        "wind_used_GWh": [0.0, 80.0],
        "co2_intensity_kg_per_Sm3oe": [62.898, 40.0],
    })


def test_model_metrics(cfg, dp):
    installed = 2 * 15e6
    wind = np.full(100, 0.5 * installed)
    m = validation.model_metrics(cfg, dp, wind, fake_summary())
    assert m["wind_capacity_factor"] == pytest.approx(0.5)
    assert m["co2_avoided_t_per_MWh"] == pytest.approx(0.5)
    assert m["co2_intensity_kg_per_boe"] == pytest.approx(10.0, rel=1e-3)   # 62.898 / 6.2898
    assert m["design_power_MW"] == pytest.approx(sum(dp.power.values()) / 1e6)


def test_two_gt_metric_from_sensitivity(cfg, dp):
    sens = pd.DataFrame({"group": ["gt_operation_practice"], "case": ["wind_fixed"],
                         "co2_kt": [74.0], "wind_used_GWh": [50.0]})
    m = validation.model_metrics(cfg, dp, np.zeros(10), fake_summary(), sens)
    assert m["co2_avoided_t_per_MWh_2gt"] == pytest.approx(0.52)   # (100 - 74) kt / 50 GWh


def test_metrics_without_case_results(cfg, dp):
    m = validation.model_metrics(cfg, dp, np.zeros(10), None)
    assert m["co2_avoided_t_per_MWh"] is None
    table = validation.compare(cfg, m)
    assert set(table.loc[table.metric == "co2_avoided_t_per_MWh", "status"]) == {"n/a"}


def test_compare_status_rules(cfg):
    metrics = {"design_power_MW": 20.0, "wind_capacity_factor": 0.30,
               "wi_specific_energy_kWh_per_m3": 9.0, "co2_avoided_t_per_MWh": 0.52,
               "co2_intensity_kg_per_boe": 7.3}
    t = validation.compare(cfg, metrics).set_index("benchmark")
    assert t.loc["platform_power_voldsund", "status"] == "within"          # 18-26 MW range
    assert t.loc["platform_power_nguyen", "status"] == "differs"           # 22.6-31.1 MW range
    assert t.loc["platform_power_castberg", "status"] == "agrees"          # 25 MW +/- 20 %
    assert t.loc["wind_capacity_factor_tampen_design", "status"] == "differs"
    assert t.loc["co2_avoided_per_wind_mwh", "status"] == "agrees"


def test_water_injection_matches_leogo(cfg, dp):
    # Same pressures and efficiency as LEOGO, so the specific energy should match closely
    m = validation.model_metrics(cfg, dp, np.zeros(10))
    assert m["wi_specific_energy_kWh_per_m3"] == pytest.approx(8.99, rel=0.05)


def test_field_data_intensity(cfg, tmp_path):
    f = tmp_path / "fields.csv"
    f.write_text("# comment\nfield,year,co2_t,co2_turbines_t,oil_Sm3,gas_Sm3,water_Sm3,electrified,source\n"
                 "A,2023,62898,50000,1000000,0,0,no,test\n")
    d = validation.load_field_data(cfg, f)
    # 1e6 Sm3 oil = 6.2898e6 boe; 62898 t -> 10 kg/boe
    assert d.loc[0, "co2_intensity_kg_per_boe"] == pytest.approx(10.0, rel=1e-4)
    assert d.loc[0, "co2_turbines_kg_per_boe"] == pytest.approx(50000e3 / 6.2898e6, rel=1e-4)


def test_template_is_empty_but_valid(cfg):
    assert validation.load_field_data(cfg).empty
