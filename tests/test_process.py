import numpy as np
import pytest

from topside.config import load_config, param_si
from topside import process


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def dp(cfg):
    return process.design_point(cfg)


def test_consumer_power_trains_and_min_flow():
    # 2 trains of 5 MW each, min flow 70 % per train
    p = process.consumer_power(10e6, [0.0, 0.2, 0.5, 0.6, 1.0, 1.05], n_trains=2, min_flow=0.7)
    assert p[0] == 0                              # off
    assert p[1] == pytest.approx(0.7 * 5e6)       # 1 train recycling at min flow
    assert p[2] == pytest.approx(5e6)             # 1 train at full flow
    assert p[3] == pytest.approx(2 * 0.7 * 5e6)   # 2 trains, each at 60 % -> recycle to 70 %
    assert p[4] == pytest.approx(10e6)
    assert p[5] == pytest.approx(10.5e6)          # above design: still 2 trains


def test_design_point_hits_targets(cfg, dp):
    assert dp.oil_rate == pytest.approx(param_si(cfg["process"]["design"]["oil_rate"]), rel=1e-3)
    assert 50 < dp.gor < 500
    assert all(v > 0 for v in dp.power.values())


def test_water_injection_pump_matches_hand_calculation(cfg, dp):
    # Hydraulic power Q * dp / (eta_pump * eta_motor), water nearly incompressible
    pr, eff = cfg["process"]["pressures"], cfg["process"]["efficiencies"]
    dp_pa = param_si(pr["water_injection"]) - param_si(pr["wi_suction"])
    hand = dp.water_injection_rate * dp_pa / (
        param_si(eff["water_pump"]) * param_si(eff["motor_and_drive"]))
    assert dp.power["water_injection_pump"] == pytest.approx(hand, rel=0.05)


def test_compression_power_scales_with_flow(cfg):
    # Steady state at fixed pressures: half the flow -> half the power
    full = process.run_hydrocarbon_process(cfg, 100.0)
    half = process.run_hydrocarbon_process(cfg, 50.0)
    for key in ("recompression_shaft_W", "export_compressor_shaft_W", "oil_export_pump_shaft_W"):
        assert half[key] == pytest.approx(full[key] / 2, rel=0.01)


def test_platform_power_at_design_equals_design_sum(cfg, dp):
    table = process.platform_power(cfg, dp, np.array([1.0]), np.array([1.0]))
    assert table.sum(axis=1).iloc[0] == pytest.approx(sum(dp.power.values()), rel=1e-6)
