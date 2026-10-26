"""Plausibility check of the assumed Tanzania gas-platform duties (not part of the model).

    python docs/verification/tanzania_process_check.py

Water contents come from NeqSim (CPA) for the process gas in config/tanzania.yaml.
The design rules below are textbook values used only for this order-of-magnitude
check; each is listed with its source in docs/verification/tanzania_assumptions.md.
"""
import math

from neqsim import jneqsim as J

from topside.config import load_config, param, param_si

cfg = load_config("config/tanzania.yaml")
gas = cfg["process"]["gas"]
COMP = param(gas["components"])
Q_SM3_D = param_si(gas["design_gas_rate"]) * 86400

# --- check inputs (textbook / assumed; see tanzania_assumptions.md) ---
M_WATER = 0.018015            # kg/mol
V_STD = 0.0236446             # m3/mol, ideal gas at 15 C and 1.01325 bar
H_VAP = 2.26e6                # J/kg, latent heat of water near 100 C
G = 9.81                      # m/s2
EXPORT_SPEC = 65.0            # mg/Sm3 water after TEG (about 4 lb/MMscf, common sales spec)
TEG_GAL_PER_LB = (3.0, 7.0)   # US gal TEG per lb water removed (Kimray 3-5; Cimarron 2-7)
TEG_DENSITY, TEG_CP, TEG_DT = 1120.0, 2500.0, 60.0   # kg/m3, J/kg/K, K heated in reboiler
REFLUX = 0.3                  # extra vapour boiled for reflux (fraction of water removed)
HEAT_LOSS = 0.1
MEG_CP, MEG_DT, RICH_MEG_WT, LEAN_MEG_WT = 3200.0, 90.0, 0.45, 0.90
MEG_DENSITY, PUMP_EFF = 1100.0, 0.6
RESERVOIR = [(60, 250), (80, 300), (100, 350)]       # (degC, bara): no published values
WATER_DEPTH, WELLHEAD_P, UMBILICAL_DP = 2400.0, 250e5, 80e5   # m, Pa, Pa


def water_mg_per_sm3(t_c, p_bara):
    f = J.thermo.system.SystemSrkCPAstatoil(273.15 + t_c, p_bara)
    for k, v in COMP.items():
        f.addComponent(k, float(v))
    f.addComponent("water", 50.0)
    f.setMixingRule(10)
    f.setMultiPhaseCheck(True)
    J.thermodynamicoperations.ThermodynamicOperations(f).TPflash()
    x = f.getPhase("gas").getComponent("water").getx()
    return x / (1 - x) * M_WATER / V_STD * 1e6


def main():
    t_arr, p_arr = param(gas["arrival_temperature"]), param(gas["arrival_pressure"])
    print(f"Design gas rate {Q_SM3_D / 1e6:.1f} MSm3/d")

    print("\nTEG dehydration (contactor at arrival pressure)")
    for t in (t_arr, 30.0):
        w = water_mg_per_sm3(t, p_arr)
        kg_s = (w - EXPORT_SPEC) * 1e-6 * Q_SM3_D / 86400
        for gal in TEG_GAL_PER_LB:
            teg_kg_per_kg = gal * 3.785e-3 * TEG_DENSITY / 0.4536
            q = kg_s * (H_VAP * (1 + REFLUX) + teg_kg_per_kg * TEG_CP * TEG_DT) * (1 + HEAT_LOSS)
            print(f"  {t:4.0f} C: water {w:5.0f} mg/Sm3, removed {kg_s * 3600:5.0f} kg/h, "
                  f"{gal:.0f} gal/lb -> reboiler {q / 1e6:.2f} MW")

    print("\nMEG loop (condensed water only; formation water adds to this)")
    w_arr = water_mg_per_sm3(t_arr, p_arr)
    for t_r, p_r in RESERVOIR:
        kg_s = (water_mg_per_sm3(t_r, p_r) - w_arr) * 1e-6 * Q_SM3_D / 86400
        rich = kg_s / (1 - RICH_MEG_WT)
        q = (kg_s * H_VAP * (1 + REFLUX) + rich * MEG_CP * MEG_DT) * (1 + HEAT_LOSS)
        lean = kg_s * RICH_MEG_WT / (LEAN_MEG_WT - RICH_MEG_WT)       # lean MEG mass flow
        dp = WELLHEAD_P + UMBILICAL_DP - MEG_DENSITY * G * WATER_DEPTH
        pump = lean / MEG_DENSITY * dp / PUMP_EFF
        print(f"  reservoir {t_r} C / {p_r} bara: condensed water {kg_s * 3600:5.0f} kg/h, "
              f"regeneration heat {q / 1e6:.2f} MW, lean MEG {lean * 3600:5.0f} kg/h, "
              f"injection pump {pump / 1e3:.0f} kW (dp {dp / 1e5:.0f} bar)")

    print("\nExport pipeline at design rate (inlet = export pressure)")
    pl = gas["pipeline"]
    d, length = param_si(pl["inner_diameter"]), param_si(pl["length"])
    f = J.thermo.system.SystemPrEos(param_si(pl["temperature"]), param(gas["export_pressure"]) - 15)
    for k, v in COMP.items():
        f.addComponent(k, float(v))
    f.setMixingRule("classic")
    J.thermodynamicoperations.ThermodynamicOperations(f).TPflash()
    f.initProperties()
    rho, mu = f.getDensity("kg/m3"), f.getViscosity("kg/msec")
    m_dot = Q_SM3_D / 86400 * f.getMolarMass() / V_STD
    v = m_dot / rho / (math.pi * d ** 2 / 4)
    re = rho * v * d / mu
    rough = 4.5e-5
    fd = 0.25 / math.log10(rough / d / 3.7 + 5.74 / re ** 0.9) ** 2       # Swamee-Jain
    dp_fric = fd * length / d * rho * v ** 2 / 2
    dp_elev = rho * G * WATER_DEPTH
    print(f"  velocity {v:.1f} m/s, Re {re:.2e}, friction {dp_fric / 1e5:.1f} bar, "
          f"elevation (seabed {WATER_DEPTH:.0f} m to shore) {dp_elev / 1e5:.1f} bar")
    for p_in in (param(pl["max_pressure"]), param(pl["min_pressure"])):
        print(f"  inlet {p_in:.0f} bara -> shore about {p_in - (dp_fric + dp_elev) / 1e5:.0f} bara")


if __name__ == "__main__":
    main()
