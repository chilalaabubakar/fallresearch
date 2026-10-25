"""Gas platform process model (Tanzania comparison case).

Flowsheet (steady state, Peng-Robinson):

    wells (subsea, MEG-inhibited) -> inlet separator -> gas --------------------+
                                          |                                     |
                                          +-> condensate -> valve -> stabiliser -+-> flash gas -> recompressor
                                                                   |            |
                                                                   +-> condensate export pump
    gas (+ recompressed flash gas) -> export compressor -> aftercooler -> pipeline to shore

Energy that is not simulated in NeqSim but taken from the config (all marked
ASSUMPTION there): TEG dehydration reboiler heat (scales with gas rate), MEG
regeneration heat and electric power, MEG injection pumps, utilities.

Two operating levers, matching the oil platform so the same scheduler applies:
  production fraction f_p : wells, compression, cooling, TEG. Flexible within the
                            line pack of the export pipeline (virtual storage);
                            capacity above the sales rate allows catching up.
  "injection" fraction    : MEG regeneration (deferrable within the rich-MEG tank).

The line pack is the gas that can be drawn from the export pipeline while its
inlet pressure falls from p_max to p_min, from NeqSim densities.
"""

import math

import numpy as np
import pandas as pd

from topside.config import param, param_si, repo_path
from topside import process


def build_gas_fluid(cfg):
    J = process._jneqsim()
    g = cfg["process"]["gas"]
    f = J.thermo.system.SystemPrEos(288.15, 1.01325)
    for name, moles in param(g["components"]).items():
        f.addComponent(name, float(moles))
    for name, (moles, molar_mass, density) in param(g["tbp_fractions"]).items():
        f.addTBPfraction(name, float(moles), float(molar_mass), float(density))
    f.setMixingRule("classic")
    f.setMultiPhaseCheck(True)
    return f


def run_gas_process(cfg, gas_rate):
    """Run the gas train for a well-stream gas rate (Sm3/s). Returns powers (W), duties and rates."""
    J = process._jneqsim()
    E = J.process.equipment
    g, eff = cfg["process"]["gas"], cfg["process"]["efficiencies"]
    bar = lambda key: param_si(g[key]) / 1e5
    eta_c = param(eff["compressor_isentropic"])

    well = E.stream.Stream("well", build_gas_fluid(cfg))
    well.setFlowRate(float(gas_rate * 86400 / 1e6), "MSm3/day")
    well.setTemperature(param_si(g["arrival_temperature"]) - 273.15, "C")
    well.setPressure(bar("arrival_pressure"), "bara")
    inlet = E.separator.Separator("inlet separator", well)
    valve = E.valve.ThrottlingValve("stabiliser valve", inlet.getLiquidOutStream())
    valve.setOutletPressure(bar("stabiliser_pressure"))
    stab = E.separator.Separator("condensate stabiliser", valve.getOutletStream())
    recomp = E.compressor.Compressor("flash gas recompressor", stab.getGasOutStream())
    recomp.setOutletPressure(bar("arrival_pressure"))
    recomp.setIsentropicEfficiency(eta_c)
    mix = E.mixer.Mixer("export gas mixer")
    mix.addStream(inlet.getGasOutStream())
    mix.addStream(recomp.getOutletStream())
    export = E.compressor.Compressor("export compressor", mix.getOutletStream())
    export.setOutletPressure(bar("export_pressure"))
    export.setIsentropicEfficiency(eta_c)
    cooler = E.heatexchanger.Cooler("export aftercooler", export.getOutletStream())
    cooler.setOutTemperature(param_si(cfg["process"]["cooling"]["gas_cooler_outlet"]) - 273.15, "C")
    pump = E.pump.Pump("condensate export pump", stab.getLiquidOutStream())
    pump.setOutletPressure(bar("export_pressure"))
    pump.setIsentropicEfficiency(param(eff["oil_export_pump"]))

    ps = J.process.processmodel.ProcessSystem()
    for u in (well, inlet, valve, stab, recomp, mix, export, cooler, pump):
        ps.add(u)
    ps.run()
    return {
        "export_compressor_shaft_W": export.getPower() + recomp.getPower(),
        "condensate_pump_shaft_W": pump.getPower(),
        "cooling_duty_W": -cooler.getDuty(),
        "gas_export_Sm3_s": cooler.getOutletStream().getFlowRate("Sm3/sec"),
        "condensate_Sm3_s": process._standard_oil_volume_rate(stab.getLiquidOutStream()),
        "export_discharge_T_K": export.getOutletStream().getTemperature("K"),
        "export_fluid": cooler.getOutletStream().getFluid(),
    }


def line_pack_hours(cfg, export_fluid, gas_rate):
    """Hours of full-rate production that the export pipeline can buffer (NeqSim densities)."""
    J = process._jneqsim()
    pl = cfg["process"]["gas"]["pipeline"]
    volume = math.pi / 4 * param(pl["inner_diameter"]) ** 2 * param(pl["length"])
    t = param_si(pl["temperature"])

    def density(p_pa, temp):
        f = export_fluid.clone()
        f.setPressure(p_pa / 1e5)
        f.setTemperature(temp)
        J.thermodynamicoperations.ThermodynamicOperations(f).TPflash()
        f.initProperties()
        return f.getDensity("kg/m3")

    rho_std = density(1.01325e5, 288.15)
    swing_sm3 = volume * (density(param_si(pl["max_pressure"]), t) - density(param_si(pl["min_pressure"]), t)) / rho_std
    return swing_sm3 / (gas_rate * 3600), swing_sm3, volume


def design_point(cfg):
    pc = cfg["process"]
    g, cool, eff = pc["gas"], pc["cooling"], pc["efficiencies"]
    eta_motor = param(eff["motor_and_drive"])
    rate = param_si(g["design_gas_rate"])
    hc = run_gas_process(cfg, rate)

    seawater = hc["cooling_duty_W"] / (param_si(cool["seawater_cp"]) * param(cool["seawater_temperature_rise"])
                                       * param(cool["seawater_density"]))
    sw_pressure = param_si(pc["pressures"]["seawater_lift"])
    shaft = {
        "export_compressor": hc["export_compressor_shaft_W"],
        "condensate_pump": hc["condensate_pump_shaft_W"],
        "seawater_lift_pump": process.water_pump_shaft_power(
            seawater, 1.01325e5, 1.01325e5 + sw_pressure, param(eff["water_pump"]),
            temperature=param_si(cool["seawater_inlet_temperature"])),
    }
    power = {k: v / eta_motor for k, v in shaft.items()}
    power["meg_regeneration"] = param_si(g["meg"]["regeneration_electric"])
    power["meg_injection_pump"] = param_si(g["meg"]["injection_pumps"])
    power["base_load"] = param_si(pc["base_load"])
    hours, _, _ = line_pack_hours(cfg, hc["export_fluid"], rate)
    return process.DesignPoint(
        power=power,
        oil_rate=hc["condensate_Sm3_s"],
        gas_export_rate=hc["gas_export_Sm3_s"],
        produced_water_rate=0.0,
        water_injection_rate=0.0,
        seawater_cooling_rate=seawater,
        gor=hc["gas_export_Sm3_s"] / max(hc["condensate_Sm3_s"], 1e-12),
        export_discharge_T=hc["export_discharge_T_K"],
        heat_per_production=param_si(g["teg_heat"]),
        heat_per_injection=param_si(g["meg"]["regeneration_heat"]),
        line_pack_hours=hours,
    )


def platform_power(cfg, dp, production_fraction, injection_fraction):
    """Electric power per consumer (W) for production and MEG-regeneration fractions of design."""
    cons = cfg["process"]["consumers"]
    f_p = np.asarray(production_fraction, dtype=float)
    f_m = np.asarray(injection_fraction, dtype=float)
    drivers = {"export_compressor": f_p, "condensate_pump": f_p, "seawater_lift_pump": f_p,
               "meg_regeneration": f_m}
    out = {name: process.consumer_power(dp.power[name], f, cons[name]["n_trains"], param(cons[name]["min_flow"]))
           for name, f in drivers.items()}
    shape = np.broadcast(f_p, f_m).shape
    out["meg_injection_pump"] = np.full(shape, dp.power["meg_injection_pump"])
    out["base_load"] = np.full(shape, dp.power["base_load"])
    return pd.DataFrame(out)


def main(cfg):
    dp = design_point(cfg)
    print("Gas platform design point")
    print(f"  sales gas          {dp.gas_export_rate * 86400 / 1e6:8.2f} MSm3/d")
    print(f"  condensate         {dp.oil_rate * 86400:8.0f} Sm3/d")
    print(f"  seawater cooling   {dp.seawater_cooling_rate * 86400:8.0f} m3/d")
    print(f"  export comp. outlet{dp.export_discharge_T - 273.15:8.0f} degC")
    print(f"  line pack buffer   {dp.line_pack_hours:8.2f} h of full-rate production")
    print(f"  TEG heat {dp.heat_per_production / 1e6:.2f} MW, MEG regeneration heat {dp.heat_per_injection / 1e6:.2f} MW")
    print("Electric power at design")
    for k, v in dp.power.items():
        print(f"  {process.LABELS[k]:<26}{v / 1e6:7.2f} MW")
    print(f"  {'TOTAL':<26}{sum(dp.power.values()) / 1e6:7.2f} MW")
    fractions = np.round(np.arange(0.5, 1.1001, 0.01), 3)
    table = platform_power(cfg, dp, fractions, np.full_like(fractions, 1.0))
    table.index = pd.Index(fractions, name="rate_fraction")
    table["total"] = table.sum(axis=1)
    out_csv = repo_path(cfg["process"]["output"]["table_file"])
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_csv, float_format="%.0f")
    out_fig = process.plot_power_vs_rate(table, repo_path(cfg["process"]["output"]["figure_file"]))
    print(f"Saved {out_csv}\nSaved {out_fig}")
    return dp, table
