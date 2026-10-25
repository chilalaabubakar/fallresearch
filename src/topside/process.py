"""Process module: NeqSim topside model -> electric power per consumer vs flow.

Flowsheet (steady state, hydrocarbons in NeqSim with Peng-Robinson), for N
separator stages (base case 4: 70 / 29.2 / 7.9 / 1.8 bara):

    well -> sep 1 -> valve -> sep 2 -> ... -> sep N -> oil export pump
              |                 |                |
              |                 |      gas N -> recompressor N-1 -> ...
              |                 +-- gas 2 --(mix)-> cooler -> scrubber -> recompressor 1
              +-- gas 1 ----------------------(mix)-> cooler -> scrubber -> export compressor

Each recompressor lifts the gas from one stage to the stage above, where it
mixes with that stage's gas. Compressors use an isentropic efficiency.

Water side (pure water, CPA equation of state, which gets liquid water right):
    water injection pumps:  suction -> injection pressure
    seawater lift pumps:    cooling water for the gas coolers + make-up for
                            water injection not covered by produced water

Simplifications: scrubber liquids are not recycled to the separators; fuel gas
take-off is not subtracted from export gas; heat demand (config heat_demand) is
not part of the electric load here, it is handled in the scheduler.

At fixed pressures, temperatures and efficiencies, steady-state power is
proportional to flow. So NeqSim is run at the design point and part-load power
comes from equipment limits per consumer (see consumer_power):
  * parallel trains, which can be switched off at low flow
  * a minimum flow per train (anti-surge recycle / pump minimum flow)

Run from the repository root:
    python -m topside.process
"""

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from topside.config import load_config, param, param_si, repo_path

# Categorical palette, fixed order (one colour per consumer)
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]

REFERENCE_WELL_FLOW = 100.0  # kg/s, only used to find the flow that gives the design oil rate


# --------------------------------------------------------------------------
# NeqSim models
# --------------------------------------------------------------------------
def _jneqsim():
    from neqsim import jneqsim
    return jneqsim


def build_reservoir_fluid(cfg):
    """Peng-Robinson fluid of the hydrocarbon well stream."""
    J = _jneqsim()
    rf = cfg["process"]["reservoir_fluid"]
    f = J.thermo.system.SystemPrEos(288.15, 1.01325)
    for name, moles in param(rf["components"]).items():
        f.addComponent(name, float(moles))
    for name, (moles, molar_mass, density) in param(rf["tbp_fractions"]).items():
        f.addTBPfraction(name, float(moles), float(molar_mass), float(density))
    f.setMixingRule("classic")
    f.setMultiPhaseCheck(True)
    return f


def _standard_oil_volume_rate(stream):
    """Stock-tank oil volume rate (m3/s) of a liquid stream flashed to 15 degC, 1 atm."""
    J = _jneqsim()
    f = stream.getFluid().clone()
    f.setTemperature(288.15)
    f.setPressure(1.01325)
    J.thermodynamicoperations.ThermodynamicOperations(f).TPflash()
    f.initProperties()
    return f.getPhase("oil").getFlowRate("m3/sec") if f.hasPhaseType("oil") else 0.0


def run_hydrocarbon_process(cfg, well_mass_flow):
    """Run the separation and compression train for a well stream mass flow (kg/s).

    Returns shaft powers (W), cooler duties (W) and export rates (SI).
    """
    J = _jneqsim()
    E = J.process.equipment
    pr, pc, eff = cfg["process"]["pressures"], cfg["process"], cfg["process"]["efficiencies"]
    p_sep = [p / 1e5 for p in param_si(pr["separators"])]   # NeqSim setters take bara
    eta_c = param(eff["compressor_isentropic"])
    t_cool = param_si(pc["cooling"]["gas_cooler_outlet"]) - 273.15
    units = []

    well = E.stream.Stream("well", build_reservoir_fluid(cfg))
    well.setFlowRate(float(well_mass_flow), "kg/sec")
    well.setTemperature(param_si(pc["design"]["well_temperature"]) - 273.15, "C")
    well.setPressure(p_sep[0], "bara")
    units.append(well)

    # Separation train: stage 1 at p_sep[0], ..., stage N at p_sep[-1]
    seps, liquid = [], well
    for i, p in enumerate(p_sep):
        if i > 0:
            valve = E.valve.ThrottlingValve(f"valve {i}-{i + 1}", liquid)
            valve.setOutletPressure(p)
            units.append(valve)
            liquid = valve.getOutletStream()
        sep = E.separator.Separator(f"separator {i + 1}", liquid)
        units.append(sep)
        seps.append(sep)
        liquid = sep.getLiquidOutStream()

    oil_pump = E.pump.Pump("oil export pump", liquid)
    oil_pump.setOutletPressure(param_si(pr["oil_export"]) / 1e5)
    oil_pump.setIsentropicEfficiency(param(eff["oil_export_pump"]))
    units.append(oil_pump)

    def compressor(name, inlet, p_out):
        c = E.compressor.Compressor(name, inlet)
        c.setOutletPressure(p_out)
        c.setIsentropicEfficiency(eta_c)
        units.append(c)
        return c

    # Recompression: lift gas from the last stage upwards, mixing at each level
    recompressors, coolers, gas = [], [], seps[-1].getGasOutStream()
    for i in range(len(seps) - 1, 0, -1):          # i = target stage index (0-based) + 1
        rc = compressor(f"recompressor {i}", gas, p_sep[i - 1])
        recompressors.append(rc)
        mix = E.mixer.Mixer(f"stage {i} gas mixer")
        mix.addStream(rc.getOutletStream())
        mix.addStream(seps[i - 1].getGasOutStream())
        cool = E.heatexchanger.Cooler(f"stage {i} gas cooler", mix.getOutletStream())
        cool.setOutTemperature(t_cool, "C")
        scrub = E.separator.Separator(f"stage {i} scrubber", cool.getOutletStream())
        units += [mix, cool, scrub]
        coolers.append(cool)
        gas = scrub.getGasOutStream()
    exp = compressor("export compressor", gas, param_si(pr["gas_export"]) / 1e5)

    ps = J.process.processmodel.ProcessSystem()
    for unit in units:
        ps.add(unit)
    ps.run()

    return {
        "recompression_shaft_W": sum(rc.getPower() for rc in recompressors),
        "export_compressor_shaft_W": exp.getPower(),
        "oil_export_pump_shaft_W": oil_pump.getPower(),
        "cooling_duty_W": -sum(c.getDuty() for c in coolers),
        "oil_rate_Sm3_s": _standard_oil_volume_rate(liquid),
        "gas_export_Sm3_s": exp.getOutletStream().getFlowRate("Sm3/sec"),
        "export_discharge_T_K": exp.getOutletStream().getTemperature("K"),
        "max_recompressor_T_K": max(rc.getOutletStream().getTemperature("K") for rc in recompressors),
    }


def water_pump_shaft_power(volume_rate, p_in, p_out, efficiency, temperature=283.15):
    """Shaft power (W) of a water pump, NeqSim CPA. Volume rate in m3/s, pressures in Pa."""
    J = _jneqsim()
    if volume_rate <= 0:
        return 0.0
    w = J.thermo.system.SystemSrkCPAstatoil(temperature, p_in / 1e5)
    w.addComponent("water", 1.0)
    w.setMixingRule(10)
    s = J.process.equipment.stream.Stream("water", w)
    s.setFlowRate(1.0, "kg/sec")
    s.run()
    rho = s.getFluid().getDensity("kg/m3")
    s.setFlowRate(float(volume_rate * rho), "kg/sec")
    s.run()
    pump = J.process.equipment.pump.Pump("water pump", s)
    pump.setOutletPressure(p_out / 1e5)
    pump.setIsentropicEfficiency(efficiency)
    pump.run()
    return pump.getPower()


# --------------------------------------------------------------------------
# Design point
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DesignPoint:
    """Electric power (W) of each consumer at design flow, plus key flows (SI)."""
    power: dict                   # consumer -> electric power at design flow (W)
    oil_rate: float               # Sm3/s
    gas_export_rate: float        # Sm3/s
    produced_water_rate: float    # m3/s
    water_injection_rate: float   # m3/s
    seawater_cooling_rate: float  # m3/s
    gor: float                    # Sm3 gas / Sm3 oil
    export_discharge_T: float     # K
    heat_per_production: float = 0.0    # W heat demand per unit production fraction
    heat_per_injection: float = 0.0     # W heat demand per unit second-lever fraction
    line_pack_hours: float | None = None  # gas platform: pipeline buffer (h at full rate)


def is_gas_platform(cfg):
    return cfg["process"].get("type", "oil") == "gas"


def design_point(cfg):
    if is_gas_platform(cfg):
        from topside import process_gas
        return process_gas.design_point(cfg)
    pc = cfg["process"]
    pr, eff, cool = pc["pressures"], pc["efficiencies"], pc["cooling"]
    eta_motor = param(eff["motor_and_drive"])
    eta_pump = param(eff["water_pump"])
    target_oil = param_si(pc["design"]["oil_rate"])

    # Find the well flow that gives the design oil rate (results scale linearly).
    ref = run_hydrocarbon_process(cfg, REFERENCE_WELL_FLOW)
    hc = run_hydrocarbon_process(cfg, REFERENCE_WELL_FLOW * target_oil / ref["oil_rate_Sm3_s"])

    wc = param(pc["design"]["water_cut"])
    produced_water = hc["oil_rate_Sm3_s"] * wc / (1 - wc)
    wi = param_si(pc["design"]["water_injection_rate"])
    seawater_cooling = hc["cooling_duty_W"] / (
        param_si(cool["seawater_cp"]) * param(cool["seawater_temperature_rise"])
        * param(cool["seawater_density"]))
    seawater_total = seawater_cooling + max(wi - produced_water, 0.0)

    shaft = {
        "recompression": hc["recompression_shaft_W"],
        "export_compressor": hc["export_compressor_shaft_W"],
        "oil_export_pump": hc["oil_export_pump_shaft_W"],
        "water_injection_pump": water_pump_shaft_power(
            wi, param_si(pr["wi_suction"]), param_si(pr["water_injection"]), eta_pump),
        "seawater_lift_pump": water_pump_shaft_power(
            seawater_total, 1.01325e5, 1.01325e5 + param_si(pr["seawater_lift"]), eta_pump),
    }
    power = {k: v / eta_motor for k, v in shaft.items()}
    power["base_load"] = param_si(pc["base_load"])
    return DesignPoint(
        power=power,
        oil_rate=hc["oil_rate_Sm3_s"],
        gas_export_rate=hc["gas_export_Sm3_s"],
        produced_water_rate=produced_water,
        water_injection_rate=wi,
        seawater_cooling_rate=seawater_cooling,
        gor=hc["gas_export_Sm3_s"] / hc["oil_rate_Sm3_s"],
        export_discharge_T=hc["export_discharge_T_K"],
    )


# --------------------------------------------------------------------------
# Part load
# --------------------------------------------------------------------------
def consumer_power(design_power, flow_fraction, n_trains, min_flow):
    """Electric power (W) of a consumer with n identical trains at a flow fraction.

    The fewest trains that can carry the flow are run. Each running train
    carries an equal share; below min_flow (fraction of its own design flow) it
    recycles, so its power stays at the min_flow level. Zero flow -> all off.
    Above design flow all trains run, slightly above their design flow.
    """
    f = np.asarray(flow_fraction, dtype=float)
    n_run = np.where(f > 0, np.clip(np.ceil(f * n_trains - 1e-9), 1, n_trains), 0)
    train_flow = np.divide(f * n_trains, n_run, out=np.zeros_like(f), where=n_run > 0)
    train_flow = np.where(n_run > 0, np.maximum(train_flow, min_flow), 0.0)
    return design_power / n_trains * n_run * train_flow


def platform_power(cfg, dp, production_fraction, injection_fraction):
    """Electric power per consumer (W) for production and water-injection fractions of design."""
    if is_gas_platform(cfg):
        from topside import process_gas
        return process_gas.platform_power(cfg, dp, production_fraction, injection_fraction)
    cons = cfg["process"]["consumers"]
    f_p = np.asarray(production_fraction, dtype=float)
    f_wi = np.asarray(injection_fraction, dtype=float)

    # Seawater: cooling scales with production, make-up = injection - produced water
    makeup = np.maximum(dp.water_injection_rate * f_wi - dp.produced_water_rate * f_p, 0.0)
    sw_design = dp.seawater_cooling_rate + max(dp.water_injection_rate - dp.produced_water_rate, 0.0)
    f_sw = (dp.seawater_cooling_rate * f_p + makeup) / sw_design

    drivers = {"recompression": f_p, "export_compressor": f_p, "oil_export_pump": f_p,
               "water_injection_pump": f_wi, "seawater_lift_pump": f_sw}
    out = {}
    for name, f in drivers.items():
        c = cons[name]
        out[name] = consumer_power(dp.power[name], f, c["n_trains"], param(c["min_flow"]))
    out["base_load"] = np.full(np.broadcast(f_p, f_wi).shape, dp.power["base_load"])
    return pd.DataFrame(out)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
LABELS = {"recompression": "Recompression", "export_compressor": "Gas export compression",
          "oil_export_pump": "Oil export pumps", "water_injection_pump": "Water injection pumps",
          "seawater_lift_pump": "Seawater lift pumps", "base_load": "Utilities and base load",
          "condensate_pump": "Condensate export pump", "meg_regeneration": "MEG regeneration",
          "meg_injection_pump": "MEG injection pumps"}


def plot_power_vs_rate(table, out_path):
    """Stacked electric power per consumer vs platform rate (production and injection together)."""
    x = table.index.to_numpy() * 100
    cols = [c for c in LABELS if c in table]
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    ys = [table[c].to_numpy() / 1e6 for c in cols]
    polys = ax.stackplot(x, ys, colors=COLORS[:len(cols)], labels=[LABELS[c] for c in cols],
                         edgecolor="white", linewidth=1.0)
    ax.set_xlabel("Production and water injection rate [% of design]")
    ax.set_ylabel("Electric power [MW]")
    ax.set_title("Topside power demand by consumer", loc="left")
    ax.set_xlim(x.min(), x.max())
    ax.grid(alpha=0.25, lw=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper left", frameon=False, fontsize=9)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    return out_path


def main():
    cfg = load_config()
    if is_gas_platform(cfg):
        from topside import process_gas
        return process_gas.main(cfg)
    dp = design_point(cfg)
    print("Design point")
    print(f"  oil rate            {dp.oil_rate * 86400:10.0f} Sm3/d")
    print(f"  gas export          {dp.gas_export_rate * 86400 / 1e6:10.2f} MSm3/d  (GOR {dp.gor:.0f} Sm3/Sm3)")
    print(f"  produced water      {dp.produced_water_rate * 86400:10.0f} m3/d")
    print(f"  water injection     {dp.water_injection_rate * 86400:10.0f} m3/d")
    print(f"  seawater cooling    {dp.seawater_cooling_rate * 86400:10.0f} m3/d")
    print(f"  export comp. outlet {dp.export_discharge_T - 273.15:10.0f} degC")
    print("Electric power at design")
    for k, v in dp.power.items():
        print(f"  {LABELS[k]:<26}{v / 1e6:7.2f} MW")
    print(f"  {'TOTAL':<26}{sum(dp.power.values()) / 1e6:7.2f} MW")

    fractions = np.round(np.arange(0.2, 1.1001, 0.01), 3)
    table = platform_power(cfg, dp, fractions, fractions)
    table.index = pd.Index(fractions, name="rate_fraction")
    table["total"] = table.sum(axis=1)
    out_csv = repo_path(cfg["process"]["output"]["table_file"])
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_csv, float_format="%.0f")
    out_fig = plot_power_vs_rate(table, repo_path(cfg["process"]["output"]["figure_file"]))
    print(f"Saved {out_csv}\nSaved {out_fig}")
    return dp, table


if __name__ == "__main__":
    main()
