import numpy as np
import pytest

from topside.config import load_config
from topside import consumers, process


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def dp(cfg):
    return process.design_point(cfg)


@pytest.fixture(scope="module")
def flex(cfg, dp):
    return consumers.build_flexibility(cfg, dp)


def test_every_consumer_has_a_class(cfg, dp):
    classes = cfg["flexibility"]["classes"]
    assert set(dp.power) == set(classes)
    assert set(classes.values()) <= {"must_run", "flexible", "sheddable", "mixed"}


def test_flexibility_power_matches_process_model(cfg, dp, flex):
    # The split into levers must reproduce process.platform_power wherever the
    # seawater make-up is positive (the only place the linear split is exact)
    for f_p, f_wi in [(1.0, 1.0), (0.8, 0.9), (0.6, 0.5), (0.5, 0.85)]:
        ref = process.platform_power(cfg, dp, np.array([f_p]), np.array([f_wi]))
        ref = ref.drop(columns="seawater_lift_pump").sum(axis=1).iloc[0]
        sw_p, sw_i = flex.seawater_per_production * f_p, flex.seawater_per_injection * f_wi
        assert flex.power(f_p, f_wi) - sw_p - sw_i == pytest.approx(ref, rel=1e-6)


def test_simplify_breakpoints_keeps_kinks():
    x = np.linspace(0, 2, 21)
    y = np.where(x < 1, x, 1 + 3 * (x - 1))
    xs, ys = consumers.simplify_breakpoints(x, y, tol=1e-9)
    assert list(xs) == [0.0, 1.0, 2.0]
    assert np.allclose(np.interp(x, xs, ys), y)


def test_injection_curve_can_switch_off(flex):
    x, y = flex.injection_curve
    assert x[0] == 0 and y[0] == 0


def test_injection_deficit_as_virtual_storage():
    # Target 0.5: stop injection for 4 h, then inject at 1.0 for 4 h -> back to zero
    f = [0, 0, 0, 0, 1, 1, 1, 1]
    d = consumers.injection_deficit(f, target=0.5)
    assert list(d) == [0.5, 1.0, 1.5, 2.0, 1.5, 1.0, 0.5, 0.0]


def test_check_schedule(flex):
    n = 24
    tgt = flex.injection.target_fraction
    ok = consumers.check_schedule(flex, np.ones(n), np.full(n, tgt))
    assert ok == []
    too_fast = np.ones(n)
    too_fast[5] = flex.production.min_fraction   # 50 % drop in one hour
    assert any("ramp" in p for p in consumers.check_schedule(flex, too_fast, np.full(n, tgt)))
    long_stop = np.zeros(200)                      # 200 h without injection
    assert any("deficit above" in p for p in consumers.check_schedule(
        flex, np.ones(200), long_stop))
