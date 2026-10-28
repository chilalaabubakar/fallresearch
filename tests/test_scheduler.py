import numpy as np
import pytest

from topside.config import load_config
from topside import consumers, scheduler

MW = 1e6


@pytest.fixture(scope="module")
def sys_():
    s = scheduler.build_system(load_config())
    # short windows keep the tests fast
    s.solver.update(window_hours=24, lookahead_hours=6)
    return s


@pytest.fixture(scope="module")
def wind():
    # 48 h: calm, then strong, then calm again (MW -> W)
    mw = np.concatenate([np.full(12, 0.0), np.full(16, 26.0), np.linspace(26, 0, 20)])
    return mw * MW


def run(sys_, wind, **kw):
    opt = scheduler.Options(fleet={"main": 3}, label="test", **kw)
    return scheduler.run(sys_, opt, wind, verbose=False)


@pytest.fixture(scope="module")
def flexible(sys_, wind):
    return run(sys_, wind, flexible=True)


@pytest.fixture(scope="module")
def fixed(sys_, wind):
    return run(sys_, wind, flexible=False)


def test_power_and_heat_balance(sys_, flexible):
    df = flexible
    supply = df["gt_total_W"] + df["wind_used_W"] + df["battery_dis_W"] - df["battery_ch_W"]
    assert np.allclose(supply, df["p_demand_W"] + df["p_heater_W"], atol=1e3)   # within 1 kW
    assert (df["wind_used_W"] <= df["wind_avail_W"] + 1).all()
    assert df["unserved_W"].max() < 1 and df["reserve_short_W"].max() < 1


def test_schedule_respects_consumer_limits(sys_, flexible):
    assert consumers.check_schedule(sys_.flex, flexible["f_p"], flexible["f_wi"], tol=1e-5) == []


def test_fuel_matches_gas_turbine_model(sys_, fixed):
    # Re-compute fuel from the GT model hour by hour and compare
    gt = sys_.units["main"].gt
    # only units that are on burn fuel (solver may leave ~1e-9 W on an off unit)
    fuel = sum(gt.fuel_power(fixed[f"gt{u}_W"].to_numpy() * fixed[f"gt{u}_on"].to_numpy())
               for u in range(3))
    fuel_sm3 = fuel * 3600 / sys_.fuel.lhv
    assert np.allclose(fuel_sm3, fixed["fuel_Sm3"], rtol=1e-4)


def test_fixed_demand_keeps_levers_fixed(sys_, fixed):
    assert np.allclose(fixed["f_p"], 1.0)
    assert np.allclose(fixed["f_wi"], sys_.flex.injection.target_fraction)


def test_flexibility_does_not_increase_fuel(fixed, flexible):
    # Flexible case can always copy the fixed schedule; allow the 0.5 % MIP gap
    assert flexible["fuel_Sm3"].sum() <= fixed["fuel_Sm3"].sum() * 1.006


def test_strong_wind_runs_minimum_gas_turbines(sys_, flexible):
    windy = flexible.iloc[14:26]
    assert (windy["gt_units_on"] == sys_.min_gt_online).all()
    assert np.allclose(windy["gt_total_W"], sys_.units["main"].gt.min_load
                       * sys_.units["main"].gt.rated_power, rtol=1e-4)


def test_battery_helps_or_is_neutral(sys_, wind, flexible):
    with_battery = run(sys_, wind, flexible=True, battery_power=4 * MW, battery_energy=4 * MW * 3600)
    assert with_battery["fuel_Sm3"].sum() <= flexible["fuel_Sm3"].sum() * 1.006


def test_low_load_uses_shared_load(sys_, fixed):
    # Low-load unit-hours follow the proportional (droop) load share of running units
    cap = fixed["gt_units_on"] * sys_.units["main"].gt.rated_power
    shared = fixed["gt_total_W"] / cap
    expected = np.where(shared < sys_.low_load_threshold, fixed["gt_units_on"], 0)
    assert np.array_equal(fixed["gt_low_load_units"].to_numpy(), expected)


def test_pump_start_cost_reduces_pump_starts(sys_, wind, flexible):
    import copy
    s = copy.copy(sys_)
    s.pump_start_cost = 1e6           # prohibitive: avoid starting pumps
    costly = run(s, wind, flexible=True)
    n, f0 = sys_.injection_trains, sys_.flex.injection.target_fraction
    assert scheduler.pump_starts(costly["f_wi"], n, f0) <= scheduler.pump_starts(flexible["f_wi"], n, f0)
    assert scheduler.pump_starts([0.85, 0.2, 0.9, 1.0], 3, 0.85) == 2


def test_wind_dependent_reserve_needs_more_gt_capacity(sys_, wind, fixed):
    import copy
    s = copy.copy(sys_)
    s.wind_reserve_share = 1.0        # cover the loss of all wind used
    strict = run(s, wind, flexible=False)
    assert strict["gt_units_on"].sum() >= fixed["gt_units_on"].sum()
    cap = strict["gt_units_on"] * sys_.units["main"].gt.rated_power - strict["gt_total_W"]
    need = sys_.reserve + strict["wind_used_W"]
    assert (cap + strict["reserve_short_W"] >= need - 1e3).all()


def test_persistence_forecast_repeats_current_hour():
    w = np.array([1.0, 5.0, 9.0, 2.0])
    assert list(scheduler.persistence_forecast(w, 1, 3)) == [5.0, 5.0, 5.0]
    assert len(scheduler.persistence_forecast(w, 3, 24)) == 1


def test_forecast_run_balances_power(sys_, wind):
    opt = scheduler.Options(fleet={"main": 3}, label="test", flexible=True)
    df = scheduler.run_forecast(sys_, opt, wind[:24], horizon=12, verbose=False)
    supply = df["gt_total_W"] + df["wind_used_W"] + df["battery_dis_W"] - df["battery_ch_W"]
    assert np.allclose(supply, df["p_demand_W"] + df["p_heater_W"], atol=1e3)
    assert (df["wind_used_W"] <= df["wind_avail_W"] + 1).all() and len(df) == 24
