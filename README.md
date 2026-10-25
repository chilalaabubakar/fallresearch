# Flexible Topside Power with Offshore Wind

**Working title:** *Energy Demand Mapping and Flexible Operation of Offshore
Topside Systems under Variable Renewable Power Supply*

This project models the power system of an offshore oil & gas platform supplied
by an offshore wind farm plus a smaller gas turbine. It tests how scheduling
flexible topside consumers (turning them down or off) to follow the wind can
cut fuel gas use and CO2 emissions without large production losses.

## Cases
1. Gas turbines only (baseline)
2. Wind + small gas turbine, fixed demand
3. Wind + small gas turbine, flexible scheduling
4. Case 3 + battery storage

## Status
| Step | Module | Status |
|---|---|---|
| 1 | Repo setup, environment, config | done |
| 2 | `wind.py` – ERA5 → wind farm power | done (needs real ERA5 run) |
| 3 | `gas_turbine.py` – load → efficiency → fuel → CO2 | done (parameters to verify) |
| 4 | `process.py` – NeqSim topside model | done (parameters to verify) |
| 5 | `consumers.py` – flexibility classes | done (limits to verify) |
| 6 | `scheduler.py` – Pyomo optimisation | – |
| 7 | `cases.py` – cases 1–4, sensitivity | – |
| 8 | Validation against public field data | – |
| 9 | Figures and tables | – |

## Setup

Python 3.11 or newer.

```bash
git clone https://github.com/chilalaabubakar/fallresearch.git
cd fallresearch
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                              # should report all tests passed
```

`pip install -e .` installs the `topside` package in "editable" mode: you can
import it from anywhere (notebooks, tests) and edits to `src/topside/*.py` take
effect immediately.

NeqSim runs on Java behind the scenes. If `import neqsim` complains about Java,
install a Java runtime (for example Temurin 17+).

### ERA5 access (one-time)
1. Create a free account at <https://cds.climate.copernicus.eu>.
2. Open the dataset page *ERA5 hourly data on single levels from 1940 to present*,
   go to the **Download** tab and accept the licence (requests fail without this).
3. Copy your personal access token from your CDS profile page and create the
   file `~/.cdsapirc` (on Windows: `C:\Users\<you>\.cdsapirc`):
   ```
   url: https://cds.climate.copernicus.eu/api
   key: <your-personal-access-token>
   ```

## Usage

```bash
python -m topside.wind --download   # download ERA5 (12 monthly files) and process
python -m topside.wind              # re-process files already in data/raw/era5
python -m topside.wind --synthetic  # demo with fake wind, no download needed
python -m topside.gas_turbine       # fuel gas properties + part-load curves
python -m topside.process           # topside design point + power vs rate per consumer
python -m topside.consumers         # flexibility classes, lever power curves, demand map
```

Outputs:
- `data/processed/wind_farm_power_<year>.csv`: hourly 100 m and hub-height
  wind speed (m/s) and farm power (W)
- `results/figures/wind_farm_power_<year>.png`: time series and duration curve

Synthetic-data outputs get `_synthetic` in the filename and are git-ignored.
They are for checking the code only, never for results.

## Repository layout
```
config/base_case.yaml   all parameters with value, unit and source
data/raw/               downloaded data (NetCDF files git-ignored)
data/processed/         processed time series
data/turbines/          IEA 15 MW power curve
src/topside/            model code
tests/                  pytest tests
notebooks/              exploration
results/                figures and tables
```

## Data sources
- ERA5: Hersbach et al. (2020), *The ERA5 global reanalysis*, QJRMS 146:1999–2049.
  Copernicus Climate Change Service.
- IEA 15 MW turbine: Gaertner et al. (2020), *Definition of the IEA 15-Megawatt
  Offshore Reference Wind Turbine*, NREL/TP-5000-75698.
  <https://github.com/IEAWindTask37/IEA-15-240-RWT>
- Fuel gas heating value: computed with NeqSim to ISO 6976 from the composition in the config.
- Seawater properties: Sharqawy, Lienhard & Zubair (2010), Desalin. Water Treat. 16:354–380.
- Wind shear exponent at sea: Hsu, Meindl & Gilhousen (1994), J. Appl. Meteorol. 33:757–765.
