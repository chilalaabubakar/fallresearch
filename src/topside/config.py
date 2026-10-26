"""Load the YAML case configuration.

Physical parameters in the YAML are written as {value, unit, source}. The
helper `param()` returns only the value, but refuses to work if the unit or
source is missing, so every number used in the model stays traceable.
"""

import os
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "base_case.yaml"


def _deep_merge(base, override):
    """Recursively merge override into base (override wins).

    A dict containing `replace: true` replaces the inherited dict instead of
    being merged into it (e.g. a site with its own list of benchmarks).
    """
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and v.get("replace") is True:
            out[k] = {kk: vv for kk, vv in v.items() if kk != "replace"}
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path=None):
    """Load a case config.

    Path order: argument, environment variable TOPSIDE_CONFIG, base_case.yaml.
    A config with `extends: <file>` is merged on top of that file, so a site
    config only lists what differs from the base case.
    """
    path = Path(path or os.environ.get("TOPSIDE_CONFIG") or DEFAULT_CONFIG)
    if not path.is_absolute() and not path.exists():
        path = REPO_ROOT / path
    with open(path) as f:
        cfg = yaml.safe_load(f)
    parent = cfg.pop("extends", None)
    if parent:
        cfg = _deep_merge(load_config(path.parent / parent), cfg)
    return cfg


def parse_years(items):
    """['2014-2016', '2020'] -> [2014, 2015, 2016, 2020] (sorted, no duplicates)."""
    years = set()
    for item in items or []:
        for part in str(item).split(","):
            if "-" in part:
                first, last = (int(x) for x in part.split("-"))
                years.update(range(first, last + 1))
            elif part.strip():
                years.add(int(part))
    return sorted(years)


def with_year(cfg, year):
    """Copy of cfg for another weather year (site.year)."""
    import copy
    out = copy.deepcopy(cfg)
    out["site"]["year"]["value"] = int(year)
    return out


def results_path(cfg, relative=""):
    """Path inside this site's results folder (results/ for the base case)."""
    return REPO_ROOT / cfg["site"].get("results_dir", "results") / relative


def param(entry):
    """Return the value of a {value, unit, source} parameter."""
    missing = {"value", "unit", "source"} - set(entry)
    if missing:
        raise ValueError(f"Parameter {entry} is missing field(s): {sorted(missing)}")
    value = entry["value"]
    # PyYAML reads e.g. "15.0e6" (no sign in the exponent) as a string.
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            pass
    return value


# Field units allowed in the YAML, converted to SI on load: (factor, offset)
TO_SI = {
    "Sm3/d": (1 / 86400, 0.0),    # -> Sm3/s
    "bara": (1e5, 0.0),           # -> Pa
    "bar": (1e5, 0.0),            # -> Pa (pressure difference)
    "degC": (1.0, 273.15),        # -> K
    "MW": (1e6, 0.0),             # -> W
    "kJ/kg/K": (1e3, 0.0),        # -> J/kg/K
}


def param_si(entry):
    """Like param(), but converts field units listed in TO_SI to SI."""
    value = param(entry)
    factor, offset = TO_SI.get(entry["unit"], (1.0, 0.0))
    if isinstance(value, list):
        return [v * factor + offset for v in value]
    return value * factor + offset


def repo_path(relative):
    """Resolve a path from the config relative to the repository root."""
    return REPO_ROOT / relative
