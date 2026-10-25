import numpy as np
import pandas as pd
import pytest
import xarray as xr

from topside.config import load_config, param, repo_path
from topside import wind


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def curve(cfg):
    return wind.load_power_curve(repo_path(cfg["wind"]["turbine"]["power_curve_file"]))


def test_power_curve_limits(cfg, curve):
    ws, p = curve
    tb = cfg["wind"]["turbine"]
    cut_in, cut_out = param(tb["cut_in_speed"]), param(tb["cut_out_speed"])
    out = wind.turbine_power([0.0, 2.9, 12.0, 20.0, 25.1], ws, p, cut_in, cut_out)
    assert out[0] == 0 and out[1] == 0 and out[4] == 0     # below cut-in, above cut-out
    assert out[2] == pytest.approx(15e6, rel=1e-3)          # rated above ~10.7 m/s
    assert out[3] == pytest.approx(15e6, rel=1e-3)
    assert np.all(np.diff(wind.turbine_power(np.linspace(3, 10.6, 50), ws, p, cut_in, cut_out)) >= 0)


def test_hub_height_power_law():
    # Same height -> unchanged; doubling height with alpha=0.11 -> factor 2**0.11
    assert wind.hub_height_speed(10.0, 100, 100, 0.11) == pytest.approx(10.0)
    assert wind.hub_height_speed(10.0, 100, 200, 0.11) == pytest.approx(10.0 * 2**0.11)


def test_farm_power_losses(curve):
    ws, p = curve
    farm = wind.wind_farm_power(15.0, 3, ws, p, 3, 25,
                                wake_loss=0.05, electrical_loss=0.02, availability=0.95)
    assert farm == pytest.approx(3 * 15e6 * 0.95 * 0.98 * 0.95, rel=1e-3)


def test_duration_curve_sorted():
    exceed, v = wind.duration_curve([1, 5, 3])
    assert list(v) == [5, 3, 1]
    assert exceed[-1] == 1.0


def test_load_era5_new_cds_format(tmp_path):
    # Mimic a new-CDS NetCDF: time axis "valid_time" and 1x1 lat/lon
    t = pd.date_range("2023-01-01", periods=4, freq="h")
    ds = xr.Dataset(
        {"u100": (("valid_time", "latitude", "longitude"), np.full((4, 1, 1), 3.0)),
         "v100": (("valid_time", "latitude", "longitude"), np.full((4, 1, 1), 4.0))},
        coords={"valid_time": t, "latitude": [61.0], "longitude": [2.0]},
    )
    f = tmp_path / "era5_test.nc"
    ds.to_netcdf(f)
    df = wind.load_era5_wind([f])
    assert len(df) == 4
    assert np.allclose(df["ws100"], 5.0)   # sqrt(3^2 + 4^2)


def test_pipeline_synthetic(cfg):
    ws100 = wind.synthetic_wind_speed(2023)["ws100"]
    df = wind.build_wind_power(cfg, ws100)
    assert len(df) == 8760
    s = wind.summarize(df, cfg)
    assert 0 < s["capacity_factor"] < 1
    assert df["p_wind_W"].max() <= s["installed_MW"] * 1e6
