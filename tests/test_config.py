import pytest

from topside.config import load_config, param, param_si, results_path


def test_site_config_inherits_and_overrides():
    base = load_config()
    tz = load_config("config/tanzania.yaml")
    assert param(tz["site"]["latitude"]) < 0 < param(base["site"]["latitude"])
    assert tz["wind"]["turbine"] == base["wind"]["turbine"]          # inherited
    assert param(tz["economics"]["co2_price"]) == 0.0                # overridden
    assert param(tz["economics"]["gas_price"]) == param(base["economics"]["gas_price"])
    assert "extends" not in tz


def test_results_path_per_site():
    assert results_path(load_config(), "cases").as_posix().endswith("results/cases")
    assert results_path(load_config("config/tanzania.yaml"), "cases").as_posix().endswith("results/tanzania/cases")


def test_env_var_selects_config(monkeypatch):
    monkeypatch.setenv("TOPSIDE_CONFIG", "config/tanzania.yaml")
    assert param(load_config()["site"]["latitude"]) == -9.5


def test_param_requires_unit_and_source():
    with pytest.raises(ValueError):
        param({"value": 1.0})
    assert param_si({"value": 10.0, "unit": "bara", "source": "x"}) == pytest.approx(1e6)
