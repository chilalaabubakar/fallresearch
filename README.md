# Flexible Topside Power with Offshore Wind

**Working title:** *Energy Demand Mapping and Flexible Operation of Offshore
Topside Systems under Variable Renewable Power Supply*

This project models the power system of an offshore oil & gas platform supplied
by an offshore wind farm plus its existing gas turbines. It tests how scheduling
flexible topside consumers (turning them down or off) to follow the wind can
cut fuel gas use and CO2 emissions without large production losses.

## Cases
1. Gas turbines only (baseline)
2. Wind + existing gas turbines, fixed demand
3. Wind + existing gas turbines, flexible scheduling
   (a small gas turbine, Solar Mars 100, is tested as a fleet sensitivity)
4. Case 3 + battery storage

## Status
| Step | Module | Status |
|---|---|---|
| 1 | Repo setup, environment, config | done |
| 2 | `wind.py` – ERA5 → wind farm power | done (ERA5 2023, CF 50.9 %) |
| 3 | `gas_turbine.py` – load → efficiency → fuel → CO2 | done (parameters to verify) |
| 4 | `process.py` – NeqSim topside model | done (parameters to verify) |
| 5 | `consumers.py` – flexibility classes | done (limits to verify) |
| 6 | `scheduler.py` – Pyomo optimisation | done |
| 7 | `cases.py` – cases 1–4, sensitivity | done (real ERA5 results in results/cases) |
| 8 | `validation.py` – benchmarks + field data | done (Gullfaks, Snorre, Statfjord) |
| 9 | `figures.py` – paper figures and tables | done (results/paper) |
| 10 | Tanzania site + `compare_sites.py` – North Sea vs Tanzania | done, but not used in the paper (archived draft: docs/tanzania/comparison.md) |
| 11 | Manuscript for Applied Energy (`docs/paper/`) | draft: paper, supplementary, highlights |

## Sites
The North Sea case (`config/base_case.yaml`) is the default. A site config lists
only what differs and is selected with the `TOPSIDE_CONFIG` environment variable
(or `--config` for `topside.wind`); its results go to its own folder.

| Site | Config | Platform | Results |
|---|---|---|---|
| North Sea, Tampen (61 N, 2 E) | `config/base_case.yaml` | oil (NeqSim, 4-stage separation, water injection) | `results/` |
| Tanzania deepwater (9.5 S, 40.5 E) | `config/tanzania.yaml` | gas (NeqSim, export compression, TEG, MEG, line pack) | `results/tanzania/` |

```bash
python -m topside.wind --config config/tanzania.yaml --download
export TOPSIDE_CONFIG=config/tanzania.yaml     # PowerShell: $env:TOPSIDE_CONFIG="config/tanzania.yaml"
python -m topside.cases --sensitivity all && python -m topside.validation && python -m topside.figures
unset TOPSIDE_CONFIG                           # PowerShell: Remove-Item Env:TOPSIDE_CONFIG
python -m topside.compare_sites                # both sites side by side -> results/comparison/
```

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
python -m topside.scheduler [--synthetic] [--weeks 2]  # demo: fixed vs flexible demand
python -m topside.cases [--sensitivity all] [--jobs 4]  # cases 1-4 (+ sensitivities), full year
python -m topside.validation        # compare with published benchmarks and data/validation/field_data.csv
python -m topside.figures           # all paper figures (PNG + PDF) and tables -> results/paper/
python docs/paper/build.py          # Applied Energy manuscript, supplementary and highlights (Word)
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
docs/paper/             manuscript sources (Markdown, references.yaml) and build.py -> Word
```

## Data sources
- ERA5: Hersbach et al. (2020), *The ERA5 global reanalysis*, QJRMS 146:1999–2049.
  Copernicus Climate Change Service.
- IEA 15 MW turbine: Gaertner et al. (2020), *Definition of the IEA 15-Megawatt
  Offshore Reference Wind Turbine*, NREL/TP-5000-75698.
  <https://github.com/IEAWindTask37/IEA-15-240-RWT>
- Fuel gas heating value: computed with NeqSim to ISO 6976 from the composition in the config.
- LEOGO reference platform: Svendsen et al. (2023), IET Energy Syst. Integr., doi:10.1049/esi2.12085
  (gas turbines, efficiencies, export/injection pressures, base load, CO2 factor).
- Separator pressures: Nguyen et al. (2013), Energy 62:23–36; real-platform checks from Voldsund et al. (2013), Energy 55:716–727, and (2014), Energy 74:45–58.
- See `docs/parameter_verification.md` for what was verified and what is still assumed.
- Seawater properties: Sharqawy, Lienhard & Zubair (2010), Desalin. Water Treat. 16:354–380.
- Wind shear exponent at sea: Hsu, Meindl & Gilhousen (1994), J. Appl. Meteorol. 33:757–765.
