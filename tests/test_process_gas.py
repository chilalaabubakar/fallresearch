import copy

import numpy as np
import pytest

from topside.config import load_config, param_si
from topside import cases, consumers, gas_turbine, process, process_gas, scheduler, validation


@pytest.fixture(scope="module")
def cfg():
    return load_config("config/tanzania.yaml")


@pytest.fixture(scope="module")
def dp(cfg):
    return process.design_point(cfg)


def test_gas_design_point(cfg, dp):
    assert process.is_gas_platform(cfg)
    assert dp.gas_export_rate * 86400 == pytest.approx(10e6, rel=0.01)
    assert set(dp.power) == {"export_compressor", "condensate_pump", "seawater_lift_pump",
                             "meg_regeneration", "meg_injection_pump", "base_load"}
    total = sum(dp.power.values())
    assert dp.power["export_compressor"] > 0.5 * total      # compression dominates a gas platform
    assert dp.water_injection_rate == 0


def test_platform_power_at_design_equals_design_sum(cfg, dp):
    t = process.platform_power(cfg, dp, np.array([1.0]), np.array([1.0]))
    assert t.sum(axis=1).iloc[0] == pytest.approx(sum(dp.power.values()), rel=1e-6)


def test_line_pack_scales_with_pipeline(cfg, dp):
    hc = process_gas.run_gas_process(cfg, param_si(cfg["process"]["gas"]["design_gas_rate"]))
    rate = param_si(cfg["process"]["gas"]["design_gas_rate"])
    h1, _, v1 = process_gas.line_pack_hours(cfg, hc["export_fluid"], rate)
    assert h1 == pytest.approx(dp.line_pack_hours, rel=1e-6)
    long = copy.deepcopy(cfg)
    long["process"]["gas"]["pipeline"]["length"]["value"] *= 2
    h2, _, v2 = process_gas.line_pack_hours(long, hc["export_fluid"], rate)
    assert v2 == pytest.approx(2 * v1) and h2 == pytest.approx(2 * h1, rel=1e-6)
    flat = copy.deepcopy(cfg)
    flat["process"]["gas"]["pipeline"]["min_pressure"] = dict(flat["process"]["gas"]["pipeline"]["max_pressure"])
    assert process_gas.line_pack_hours(flat, hc["export_fluid"], rate)[0] == pytest.approx(0, abs=1e-9)


def test_lean_gas_co2_factor_and_hot_air(cfg):
    fuel = gas_turbine.fuel_gas_from_config(cfg)
    assert fuel.co2_factor == pytest.approx(fuel.co2_factor_composition)
    assert 1.8 < fuel.co2_factor < 2.1                      # lean gas: well below Norway's 2.34
    p, e = gas_turbine.ambient_factors(cfg)
    amb = cfg["gas_turbine"]["ambient"]
    dT = param_si(amb["temperature"]) - param_si(amb["iso_temperature"])
    assert dT > 10                                          # tropical site, hotter than ISO 15 degC
    assert p == pytest.approx(1 - 0.007 * dT) and e == pytest.approx(1 - 0.001 * dT)
    assert gas_turbine.ambient_factors(load_config()) == (1.0, 1.0)


def test_flexibility_uses_line_pack(cfg, dp):
    flex = consumers.build_flexibility(cfg, dp)
    assert flex.production.max_deficit == pytest.approx(dp.line_pack_hours)
    assert flex.production.max_fraction > 1.0
    assert flex.base_load == pytest.approx(dp.power["base_load"] + dp.power["meg_injection_pump"])
    assert flex.heat_per_injection > 0 and flex.heat_per_production > 0


def test_scheduler_respects_line_pack(cfg):
    s = scheduler.build_system(cfg)
    s.solver.update(window_hours=24, lookahead_hours=6)
    wind = np.concatenate([np.full(12, 0.0), np.full(12, 26e6), np.full(24, 5e6)])
    ss, opt, w = cases.apply_overrides(cfg, s, "wind_flex", wind)
    df = scheduler.run(ss, opt, w, verbose=False)
    assert df["prod_deficit_h"].max() <= ss.flex.production.max_deficit + 1e-6
    assert df["prod_deficit_h"].iloc[-1] <= 1e-6 + 1e-3
    assert consumers.check_schedule(ss.flex, df["f_p"], df["f_wi"], tol=1e-5) == []
    no_buffer = cases.apply_overrides(cfg, s, "wind_flex", wind, {"line_pack_hours": 0.0})[0]
    assert no_buffer.flex.production.max_deficit == 0.0


def test_validation_without_water_injection(cfg, dp):
    m = validation.model_metrics(cfg, dp, np.zeros(10))
    assert m["wi_specific_energy_kWh_per_m3"] is None
    assert validation.compare(cfg, m).empty                # Tanzania replaces the North Sea benchmarks
