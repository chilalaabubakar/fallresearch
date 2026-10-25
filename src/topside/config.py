"""Load the YAML case configuration.

Physical parameters in the YAML are written as {value, unit, source}. The
helper `param()` returns only the value, but refuses to work if the unit or
source is missing, so every number used in the model stays traceable.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "base_case.yaml"


def load_config(path=DEFAULT_CONFIG):
    with open(path) as f:
        return yaml.safe_load(f)


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
    return value * factor + offset


def repo_path(relative):
    """Resolve a path from the config relative to the repository root."""
    return REPO_ROOT / relative
