import numpy as np
import pytest

from topside.config import load_config
from topside import gas_turbine as gtm


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def gt(cfg):
    return gtm.gas_turbine_from_config(cfg, "main")


@pytest.fixture(scope="module")
def fuel(cfg):
    return gtm.fuel_gas_from_config(cfg)


def test_leogo_fuel_model(gt):
    # LEOGO: fuel_energy / P_max = B + A * P / P_max with A = 2.35, B = 0.53 (Svendsen et al., 2023)
    A, B = 2.35, 0.53
    for load in (0.2, 0.5, 1.0):
        p = load * gt.rated_power
        assert gt.fuel_power(p) / gt.rated_power == pytest.approx(B + A * load, rel=2e-3)


def test_willans_shape():
    rel = gtm.willans_relative_efficiency([0.0, 0.5, 1.0], a=0.25)
    assert rel[0] == 0
    assert rel[1] == pytest.approx(0.8)
    assert rel[2] == pytest.approx(1.0)
    assert np.all(np.diff(gtm.willans_relative_efficiency(np.linspace(0.05, 1, 50), 0.25)) > 0)


def test_fuel_power_is_linear_in_load(gt):
    # Willans line: equal steps in power give equal steps in fuel power
    p = np.array([0.4, 0.6, 0.8, 1.0]) * gt.rated_power
    q = gt.fuel_power(p)
    assert np.allclose(np.diff(q), np.diff(q)[0])
    assert q[-1] == pytest.approx(gt.rated_power / gt.rated_efficiency)
    assert gt.fuel_power(0.0) == 0          # unit switched off burns nothing


def test_overload_rejected(gt):
    with pytest.raises(ValueError):
        gt.fuel_power(1.1 * gt.rated_power)


def test_table_method_matches_willans(cfg):
    # The template table holds Willans values with the LEOGO shape (a = 0.184)
    cfg_t = {**cfg, "gas_turbine": {**cfg["gas_turbine"], "part_load_method": "table"}}
    t = gtm.gas_turbine_from_config(cfg_t, "main")
    w = gtm.gas_turbine_from_config(cfg, "main")
    p = np.array([0.3, 0.5, 0.8]) * w.rated_power
    assert np.allclose(t.efficiency(p), w.efficiency(p), atol=1e-3)


def test_pure_methane_properties(cfg):
    # ISO 6976 reference: methane LHV at 15 degC is about 34.0 MJ/m3 (real gas)
    lhv, density, molar_density = gtm._iso6976((("methane", 1.0),), 288.15)
    assert lhv == pytest.approx(34.0e6, rel=0.005)
    assert gtm.co2_factor_from_composition({"methane": 1.0}, molar_density) == pytest.approx(1.865, rel=0.005)


def test_config_co2_factor_close_to_composition(fuel):
    # The stored factor and the carbon-balance factor should agree within 15 %
    assert fuel.co2_factor == pytest.approx(fuel.co2_factor_composition, rel=0.15)


def test_baseline_dispatch_and_totals(gt, fuel):
    demand = np.array([10e6, 30e6, 40e6])
    n, p_unit = gtm.equal_sharing_dispatch(demand, gt, min_units=2)
    assert list(n) == [2, 2, 2]
    assert np.allclose(p_unit * n, demand)
    out = gtm.fuel_and_co2(p_unit, n, gt, fuel, low_load_threshold=0.5)
    # 5, 15 and 20 MW per 21.8 MW unit -> 23 %, 69 %, 92 % load
    assert list(out["low_load"]) == [True, False, False]
    assert np.allclose(out["co2_kg"], out["fuel_Sm3"] * fuel.co2_factor)
