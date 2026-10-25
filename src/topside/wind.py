"""Wind module: ERA5 hourly wind -> hub-height wind speed -> wind farm power.

Steps
1. Download ERA5 100 m u/v wind components for one grid point (one file per
   month, so a failed request only needs that month repeated).
2. Combine u and v into wind speed at 100 m.
3. Extrapolate to hub height with the power law  v_hub = v_ref * (z_hub/z_ref)^alpha.
4. Look up turbine power on the IEA 15 MW power curve (linear interpolation).
5. Multiply by number of turbines and loss factors -> farm power in W.

Run from the repository root:
    python -m topside.wind --download   # fetch ERA5 (needs ~/.cdsapirc), then process
    python -m topside.wind              # process already-downloaded files
    python -m topside.wind --synthetic  # pipeline demo with fake wind, no download
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, repo_path

COLOR = "#2a78d6"
INK_MUTED = "#52514e"


# --------------------------------------------------------------------------
# 1. ERA5 download
# --------------------------------------------------------------------------
def download_era5(year, lat, lon, out_dir, variables,
                  dataset="reanalysis-era5-single-levels"):
    """Download hourly ERA5 data for one grid point, one NetCDF file per month.

    Files already on disk are skipped. Returns the list of file paths.
    """
    import cdsapi  # imported here so the rest of the module works without it

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client()
    paths = []
    for month in range(1, 13):
        target = out_dir / f"era5_wind100m_{lat:.2f}N_{lon:.2f}E_{year}_{month:02d}.nc"
        paths.append(target)
        if target.exists():
            continue
        request = {
            "product_type": ["reanalysis"],
            "variable": list(variables),
            "year": [str(year)],
            "month": [f"{month:02d}"],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": [f"{h:02d}:00" for h in range(24)],
            # Area is [North, West, South, East]; a zero-size box returns the
            # nearest grid point (ERA5 grid is 0.25 deg).
            "area": [lat, lon, lat, lon],
            "data_format": "netcdf",
            "download_format": "unarchived",
        }
        print(f"Requesting ERA5 {year}-{month:02d} ...")
        client.retrieve(dataset, request).download(str(target))
    return paths


def load_era5_wind(paths):
    """Read ERA5 NetCDF files and return hourly 100 m wind speed (m/s), UTC index."""
    import xarray as xr

    frames = []
    for p in sorted(paths):
        with xr.open_dataset(p) as ds:
            # The new CDS (2024+) calls the time axis "valid_time", the old one "time".
            time_name = "valid_time" if "valid_time" in ds.dims else "time"
            ds = ds.squeeze(drop=True)  # drop the 1x1 latitude/longitude dims
            if "expver" in ds.dims:     # near-real-time data can carry two versions
                ds = ds.max("expver")
            frames.append(pd.DataFrame({
                "u100": ds["u100"].values.ravel(),
                "v100": ds["v100"].values.ravel(),
            }, index=pd.DatetimeIndex(ds[time_name].values, name="time_utc")))
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated()]
    df["ws100"] = np.hypot(df["u100"], df["v100"])
    return df


def synthetic_wind_speed(year=2023, mean=10.0, seed=0):
    """Fake hourly wind speed for testing the pipeline. NOT real data.

    Weibull-like distribution with a winter-high seasonal cycle and hour-to-hour
    persistence. Only for demos and tests when ERA5 is not available.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h", name="time_utc")
    n = len(idx)
    # AR(1) Gaussian process -> uniform -> Weibull (k = 2.2)
    phi, z = 0.97, np.empty(n)
    z[0] = rng.standard_normal()
    for i in range(1, n):
        z[i] = phi * z[i - 1] + np.sqrt(1 - phi**2) * rng.standard_normal()
    from math import erf, gamma
    u = 0.5 * (1 + np.vectorize(erf)(z / np.sqrt(2)))
    k = 2.2
    season = 1 + 0.25 * np.cos(2 * np.pi * (idx.dayofyear - 15) / 365)
    scale = mean / gamma(1 + 1 / k) * season
    ws = scale * (-np.log(1 - np.clip(u, 1e-9, 1 - 1e-9))) ** (1 / k)
    return pd.DataFrame({"ws100": ws}, index=idx)


# --------------------------------------------------------------------------
# 2. Height correction and power curve
# --------------------------------------------------------------------------
def hub_height_speed(ws_ref, z_ref, z_hub, alpha):
    """Power-law extrapolation of wind speed from z_ref to z_hub (heights in m)."""
    return ws_ref * (z_hub / z_ref) ** alpha


def load_power_curve(path):
    """Return (wind speed in m/s, power in W) arrays from the power curve CSV."""
    curve = pd.read_csv(path, comment="#")
    return curve["wind_speed_m_s"].to_numpy(), curve["power_MW"].to_numpy() * 1e6


def turbine_power(ws_hub, curve_ws, curve_power, cut_in, cut_out):
    """Power of one turbine (W) for hub-height wind speed(s) (m/s)."""
    ws_hub = np.asarray(ws_hub, dtype=float)
    p = np.interp(ws_hub, curve_ws, curve_power)
    return np.where((ws_hub < cut_in) | (ws_hub > cut_out), 0.0, p)


def wind_farm_power(ws_hub, n_turbines, curve_ws, curve_power, cut_in, cut_out,
                    wake_loss=0.0, electrical_loss=0.0, availability=1.0):
    """Farm power delivered to the platform (W)."""
    p_one = turbine_power(ws_hub, curve_ws, curve_power, cut_in, cut_out)
    return n_turbines * p_one * (1 - wake_loss) * (1 - electrical_loss) * availability


def duration_curve(values):
    """Values sorted high -> low, with the share of time each is exceeded (0..1)."""
    v = np.sort(np.asarray(values, dtype=float))[::-1]
    exceed = np.arange(1, len(v) + 1) / len(v)
    return exceed, v


# --------------------------------------------------------------------------
# 3. Pipeline and figure
# --------------------------------------------------------------------------
def build_wind_power(cfg, ws100):
    """Turn a 100 m wind speed series (m/s) into a DataFrame with farm power."""
    w = cfg["wind"]
    hc, tb, fm = w["height_correction"], w["turbine"], w["farm"]
    curve_ws, curve_p = load_power_curve(repo_path(tb["power_curve_file"]))
    ws_hub = hub_height_speed(ws100, param(w["era5"]["reference_height"]),
                              param(hc["hub_height"]), param(hc["shear_exponent"]))
    p_farm = wind_farm_power(
        ws_hub, param(fm["n_turbines"]), curve_ws, curve_p,
        param(tb["cut_in_speed"]), param(tb["cut_out_speed"]),
        param(fm["wake_loss"]), param(fm["electrical_loss"]), param(fm["availability"]),
    )
    return pd.DataFrame({"ws100_m_s": ws100, "ws_hub_m_s": ws_hub, "p_wind_W": p_farm},
                        index=ws100.index)


def summarize(df, cfg):
    """Key numbers: mean power, capacity factor, annual energy, zero-output hours."""
    fm, tb = cfg["wind"]["farm"], cfg["wind"]["turbine"]
    installed = param(fm["n_turbines"]) * param(tb["rated_power"])
    p = df["p_wind_W"]
    return {
        "installed_MW": installed / 1e6,
        "mean_ws_hub_m_s": df["ws_hub_m_s"].mean(),
        "mean_power_MW": p.mean() / 1e6,
        "capacity_factor": p.mean() / installed,
        "annual_energy_GWh": p.sum() * 3600 / 3.6e12,  # hourly steps: W*h -> GWh
        "hours_zero_output": int((p <= 0).sum()),
        "hours": len(p),
    }


def plot_wind_power(df, installed_W, out_path, title_note=""):
    """Two panels: hourly farm power over the year, and its duration curve."""
    p_mw = df["p_wind_W"] / 1e6
    exceed, sorted_mw = duration_curve(p_mw)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)

    ax1.plot(p_mw.index, p_mw.values, color=COLOR, lw=0.4, alpha=0.5, label="Hourly")
    daily = p_mw.resample("D").mean()
    ax1.plot(daily.index, daily.values, color="#0d366b", lw=1.2, label="Daily mean")
    ax1.set_ylabel("Wind farm power [MW]")
    ax1.set_title(f"Hourly wind farm power{title_note}", loc="left")
    ax1.legend(loc="upper right", frameon=False)

    ax2.plot(exceed * 100, sorted_mw, color=COLOR, lw=2)
    ax2.set_xlabel("Share of hours power is equalled or exceeded [%]")
    ax2.set_ylabel("Wind farm power [MW]")
    ax2.set_title("Duration curve", loc="left")
    ax2.set_xlim(0, 100)

    for ax in (ax1, ax2):
        ax.set_ylim(0, installed_W / 1e6 * 1.05)
        ax.axhline(installed_W / 1e6, color=INK_MUTED, lw=0.8, ls="--")
        ax.grid(alpha=0.25, lw=0.5)
        ax.spines[["top", "right"]].set_visible(False)
    ax2.annotate(f"Installed {installed_W / 1e6:.0f} MW", (99, installed_W / 1e6),
                 ha="right", va="bottom", color=INK_MUTED, fontsize=9)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default=None, help="Path to case YAML")
    ap.add_argument("--download", action="store_true", help="Download ERA5 first")
    ap.add_argument("--synthetic", action="store_true",
                    help="Use fake wind data (pipeline demo only, not for results)")
    args = ap.parse_args(argv)

    cfg = load_config(args.config) if args.config else load_config()
    site, era5 = cfg["site"], cfg["wind"]["era5"]
    year, lat, lon = param(site["year"]), param(site["latitude"]), param(site["longitude"])
    out_csv = repo_path(cfg["wind"]["output"]["processed_file"].format(year=year))
    out_fig = repo_path(cfg["wind"]["output"]["figure_file"].format(year=year))

    if args.synthetic:
        ws100 = synthetic_wind_speed(year)["ws100"]
        out_csv = out_csv.with_name(out_csv.stem + "_synthetic.csv")
        out_fig = out_fig.with_name(out_fig.stem + "_synthetic.png")
        note = " (SYNTHETIC DEMO DATA, not ERA5)"
    else:
        raw_dir = repo_path(era5["raw_dir"])
        if args.download:
            paths = download_era5(year, lat, lon, raw_dir, era5["variables"], era5["dataset"])
        else:
            paths = sorted(raw_dir.glob(f"era5_wind100m_*_{year}_*.nc"))
            if not paths:
                raise SystemExit(f"No ERA5 files in {raw_dir}. Run with --download first.")
        ws100 = load_era5_wind(paths)["ws100"]
        note = f", ERA5 {lat:.0f}N {lon:.0f}E, {year}"

    df = build_wind_power(cfg, ws100)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv)
    installed = param(cfg["wind"]["farm"]["n_turbines"]) * param(cfg["wind"]["turbine"]["rated_power"])
    plot_wind_power(df, installed, out_fig, note)

    for k, v in summarize(df, cfg).items():
        print(f"{k:>20}: {v:.3f}" if isinstance(v, float) else f"{k:>20}: {v}")
    print(f"Saved {out_csv}\nSaved {out_fig}")
    return df


if __name__ == "__main__":
    main()
