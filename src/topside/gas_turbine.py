"""Gas turbine module: electric load -> efficiency -> fuel gas -> CO2.

Part-load model (default "willans"): fuel power is a straight line in electric
power, starting from a no-load fuel use a*Q_rated at zero load:

    Q_fuel = P_rated / eta_rated * (a + (1 - a) * L),      L = P / P_rated
    eta(L) = eta_rated * L / (a + (1 - a) * L)

So efficiency falls off as load drops, which is why running gas turbines at
low load is costly. Alternative "table": relative efficiency eta/eta_rated vs
load from a CSV (e.g. digitised from a published curve).

Fuel volume uses the lower heating value (LHV) of the fuel gas, computed with
NeqSim to ISO 6976 from the composition in the config.

Run from the repository root to print fuel gas properties and plot the curves:
    python -m topside.gas_turbine
"""

import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, param_si, repo_path
from topside import style

COLORS = [style.PALETTE["blue_main"], style.PALETTE["red_strong"]]
INK_MUTED = style.PALETTE["grey"]

# Chemistry, not model parameters: carbon atoms per molecule and molar mass of CO2.
CARBON_ATOMS = {"methane": 1, "ethane": 2, "propane": 3, "i-butane": 4, "n-butane": 4,
                "i-pentane": 5, "n-pentane": 5, "n-hexane": 6, "CO2": 1,
                "nitrogen": 0, "water": 0, "H2S": 0, "oxygen": 0, "argon": 0, "helium": 0}
M_CO2 = 44.0095e-3  # kg/mol


# --------------------------------------------------------------------------
# Fuel gas
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class FuelGas:
    lhv: float                  # J/Sm3
    density: float              # kg/Sm3
    co2_factor: float           # kg CO2/Sm3 used in the model (from config)
    co2_factor_composition: float  # kg CO2/Sm3 from carbon balance (cross-check)


@lru_cache(maxsize=8)
def _iso6976(composition_items, t_std_K):
    """LHV (J/Sm3), real density (kg/Sm3) and molar density (mol/Sm3) via NeqSim."""
    from neqsim import jneqsim
    from neqsim.thermo import fluid, TPflash

    f = fluid("srk")
    for name, x in composition_items:
        f.addComponent(name, x)
    f.setMixingRule("classic")
    f.setTemperature(t_std_K)
    f.setPressure(1.01325)
    TPflash(f)
    f.init(0)
    t_c = t_std_K - 273.15
    iso = jneqsim.standards.gasquality.Standard_ISO6976(f, t_c, t_c, "volume")
    iso.setReferenceState("real")
    iso.calculate()
    missing = list(iso.getComponentsNotDefinedByStandard())
    if missing:
        raise ValueError(f"Components not covered by ISO 6976: {missing}")
    lhv = iso.getValue("InferiorCalorificValue") * 1e3   # kJ/m3 -> J/m3
    density = iso.getValue("DensityReal")                 # kg/m3
    molar_mass = iso.getValue("MolarMass") * 1e-3         # g/mol -> kg/mol
    return lhv, density, density / molar_mass


def co2_factor_from_composition(composition, molar_density):
    """kg CO2 per Sm3 if all carbon in the gas (incl. CO2 already present) leaves as CO2."""
    carbon_per_mol = sum(x * CARBON_ATOMS[name] for name, x in composition.items())
    return carbon_per_mol * molar_density * M_CO2


def fuel_gas_from_config(cfg):
    fg = cfg["fuel_gas"]
    comp = param(fg["composition"])
    total = sum(comp.values())
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        raise ValueError(f"Fuel gas mole fractions sum to {total}, not 1")
    lhv, density, molar_density = _iso6976(tuple(sorted(comp.items())),
                                           param(fg["standard_temperature"]))
    from_composition = co2_factor_from_composition(comp, molar_density)
    # "composition": use the carbon balance of this gas instead of a reported factor
    used = from_composition if fg.get("co2_factor_method") == "composition" else param(fg["co2_emission_factor"])
    return FuelGas(lhv=lhv, density=density, co2_factor=used, co2_factor_composition=from_composition)


# --------------------------------------------------------------------------
# Gas turbine
# --------------------------------------------------------------------------
def willans_relative_efficiency(load, a):
    """eta(L) / eta_rated for the Willans line; zero at zero load."""
    load = np.asarray(load, dtype=float)
    return np.where(load > 0, load / (a + (1 - a) * load), 0.0)


@dataclass(frozen=True)
class GasTurbine:
    name: str
    rated_power: float          # W
    rated_efficiency: float     # -, LHV basis
    no_load_fuel_fraction: float
    min_load: float             # fraction of rated
    table: tuple | None = None  # (load, relative efficiency) for method "table"

    def relative_efficiency(self, load):
        if self.table is None:
            return willans_relative_efficiency(load, self.no_load_fuel_fraction)
        load = np.asarray(load, dtype=float)
        return np.where(load > 0, np.interp(load, *self.table), 0.0)

    def efficiency(self, power):
        """Electric efficiency (LHV) at electric output power (W)."""
        load = np.asarray(power, dtype=float) / self.rated_power
        return self.rated_efficiency * self.relative_efficiency(load)

    def fuel_power(self, power):
        """Fuel energy input rate (W, LHV basis). Zero when the unit is off (P = 0)."""
        power = np.asarray(power, dtype=float)
        if np.any(power > self.rated_power * (1 + 1e-9)):
            raise ValueError(f"{self.name}: power above rated {self.rated_power / 1e6:.1f} MW")
        eta = self.efficiency(power)
        return np.divide(power, eta, out=np.zeros_like(power), where=eta > 0)


def ambient_factors(cfg):
    """Multipliers on rated power and efficiency for air warmer than ISO (1, 1 if not set).

    Linear rule of thumb: each kelvin above the ISO temperature lowers rated
    power and efficiency by the configured fractions. The minimum load stays
    the same fraction of the (derated) rated power.
    """
    amb = cfg["gas_turbine"].get("ambient")
    if not amb:
        return 1.0, 1.0
    dT = max(param_si(amb["temperature"]) - param_si(amb["iso_temperature"]), 0.0)
    return 1 - param(amb["power_derate_per_K"]) * dT, 1 - param(amb["efficiency_derate_per_K"]) * dT


def gas_turbine_from_config(cfg, unit_key):
    g = cfg["gas_turbine"]
    u = g["units"][unit_key]
    table = None
    if g["part_load_method"] == "table":
        t = pd.read_csv(repo_path(g["part_load_table_file"]), comment="#")
        table = (tuple(t["load_fraction"]), tuple(t["relative_efficiency"]))
    elif g["part_load_method"] != "willans":
        raise ValueError(f"Unknown part_load_method {g['part_load_method']!r}")
    power_factor, eff_factor = ambient_factors(cfg)
    return GasTurbine(name=u["name"], rated_power=param(u["rated_power"]) * power_factor,
                      rated_efficiency=param(u["rated_efficiency"]) * eff_factor,
                      no_load_fuel_fraction=param(u["no_load_fuel_fraction"]),
                      min_load=param(u["min_load"]), table=table)


# --------------------------------------------------------------------------
# Fuel and CO2 for a power time series
# --------------------------------------------------------------------------
def equal_sharing_dispatch(power_demand, gt, min_units=1, max_units=None):
    """Number of identical units running and load per unit (W), equal load sharing.

    Simple rule for the gas-turbine-only baseline: run the fewest units that can
    cover demand, but never fewer than min_units (redundancy). The optimiser
    (scheduler.py) replaces this rule for the wind cases.
    """
    p = np.asarray(power_demand, dtype=float)
    n = np.maximum(np.ceil(p / gt.rated_power - 1e-9), min_units).astype(int)
    if max_units is not None and np.any(n > max_units):
        raise ValueError("Demand exceeds installed gas turbine capacity")
    return n, p / n


def fuel_and_co2(power_per_unit, n_units, gt, fuel, dt=3600.0, low_load_threshold=0.5):
    """Fuel gas (Sm3), CO2 (kg) and low-load flag per time step of length dt (s)."""
    q = gt.fuel_power(power_per_unit) * n_units          # W of fuel
    fuel_sm3 = q * dt / fuel.lhv
    load = np.asarray(power_per_unit) / gt.rated_power
    return pd.DataFrame({
        "n_units": n_units,
        "load_fraction": load,
        "efficiency": gt.efficiency(power_per_unit),
        "fuel_Sm3": fuel_sm3,
        "co2_kg": fuel_sm3 * fuel.co2_factor,
        "low_load": (n_units > 0) & (load < low_load_threshold),
    })


# --------------------------------------------------------------------------
# Figure
# --------------------------------------------------------------------------
def plot_part_load(gts, fuel, out_path):
    """Efficiency and specific CO2 (kg/MWh) vs load for each turbine."""
    load = np.linspace(0.1, 1.0, 200)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for gt, c in zip(gts, COLORS):
        p = load * gt.rated_power
        eta = gt.efficiency(p)
        co2_kg_per_MWh = 3.6e9 / eta / fuel.lhv * fuel.co2_factor
        label = f"{gt.name} ({gt.rated_power / 1e6:.0f} MW)"
        ax1.plot(load * 100, eta * 100, color=c, lw=2, label=label)
        ax2.plot(load * 100, co2_kg_per_MWh, color=c, lw=2, label=label)
    ax1.set_ylabel("Electric efficiency, LHV [%]")
    ax1.set_title("Part-load efficiency", loc="left")
    ax2.set_ylabel("CO2 per electricity [kg/MWh]")
    ax2.set_title("Specific CO2 emissions", loc="left")
    min_load = min(gt.min_load for gt in gts)
    for ax in (ax1, ax2):
        ax.set_xlabel("Load [% of rated]")
        ax.set_xlim(0, 100)
        ax.axvspan(0, min_load * 100, color=INK_MUTED, alpha=0.08, lw=0)
        ax.spines[["top", "right"]].set_visible(False)
    ax1.set_ylim(0, None)
    ax2.set_ylim(0, None)
    ax1.text(min_load * 50, 2, "below\nmin. load", ha="center", va="bottom",
             color=style.TEXT_COLOR, fontsize=style.FONT_SIZE - 3)
    ax2.legend(loc="upper right", frameon=False, fontsize=style.FONT_SIZE - 2)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    style.enforce_min_text_size(fig)
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    return out_path


def main():
    cfg = load_config()
    fuel = fuel_gas_from_config(cfg)
    print(f"Fuel gas LHV (ISO 6976, real gas): {fuel.lhv / 1e6:.2f} MJ/Sm3")
    print(f"Fuel gas density:                  {fuel.density:.3f} kg/Sm3")
    print(f"CO2 factor used (config):          {fuel.co2_factor:.3f} kg/Sm3")
    print(f"CO2 factor from composition:       {fuel.co2_factor_composition:.3f} kg/Sm3")
    gts = [gas_turbine_from_config(cfg, k) for k in cfg["gas_turbine"]["units"]]
    for gt in gts:
        for load in (1.0, 0.75, 0.5, 0.3):
            p = load * gt.rated_power
            fuel_rate = gt.fuel_power(p) / fuel.lhv  # Sm3/s
            print(f"  {gt.name:<38} {load:4.0%}: eta {gt.efficiency(p):.3f}, "
                  f"fuel {fuel_rate * 3600:7.0f} Sm3/h, CO2 {fuel_rate * 3600 * fuel.co2_factor / 1e3:5.2f} t/h")
    out = plot_part_load(gts, fuel, repo_path(cfg["gas_turbine"]["output"]["figure_file"]))
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
