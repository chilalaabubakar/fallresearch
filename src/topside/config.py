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


def repo_path(relative):
    """Resolve a path from the config relative to the repository root."""
    return REPO_ROOT / relative
