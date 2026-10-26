# Methods

*Draft for the thesis chapter. Numbers are taken from the model output in
`results/` (code version on `main`, ERA5 year 2023). Parameter values and their
sources are listed in full in Table T1 (`results/paper/tables/T1_parameters.md`).*

## 1 Study design

The study models the electric power system of a generic oil platform in the
northern North Sea (Tampen area, 61.0° N, 2.0° E) for one year at hourly
resolution. Power is supplied by gas turbines (GTs) and, in the wind cases, by
a nearby offshore wind farm. The novelty compared with earlier platform–wind
studies is that the topside demand is not treated as a fixed load: each
consumer is mapped to its process duty and classified by how far, and at what
cost, it can be moved in time or reduced. An optimisation model then schedules
the flexible consumers together with the GTs.

Four cases are compared:

1. **Gas turbines only** (baseline), fixed demand.
2. **Wind + GTs, fixed demand**: production and water injection at their
   design and target rates every hour.
3. **Wind + GTs, flexible scheduling**: production and water-injection rates
   are decision variables.
4. **Case 3 + battery** (4 MW / 4 MWh).

In all cases the platform keeps its three existing GTs (a retrofit, as on the
Snorre and Gullfaks platforms supplied by Hywind Tampen); the optimiser decides
how many run in each hour. Process behaviour is represented by steady-state
operating points with ramp limits; transient process dynamics are outside the
scope.

The model is written in Python. NeqSim is used for thermodynamics and process
simulation, Pyomo with the HiGHS solver for optimisation. Every parameter is
stored in one configuration file with its unit and source, and unverified
values are explicitly marked as assumptions (29 of 101 parameters). The code
has a test suite of 49 automated checks that compare model components with
hand calculations and published values.

## 2 Wind resource and wind farm power

Hourly wind components at 100 m for 2023 were taken from the ERA5 reanalysis
(Hersbach et al., 2020) at the grid point 61.0° N, 2.0° E. Wind speed was
extrapolated to the 150 m hub height with the power law

$$ v_{hub} = v_{100}\left(\frac{z_{hub}}{z_{100}}\right)^{\alpha},\qquad \alpha = 0.11, $$

the value recommended for near-neutral conditions at sea (Hsu et al., 1994).
Turbine power was interpolated on the power curve of the IEA 15 MW offshore
reference turbine (Gaertner et al., 2020): cut-in 3 m/s, rated power from
10.7 m/s, cut-out 25 m/s. The base-case farm has two turbines (30 MW
installed), of the same order as the 32 MW wind farm of the LEOGO reference
platform (Svendsen et al., 2023). Wake losses (5 %), electrical losses (2 %)
and availability (95 %) reduce the delivered power by a combined factor of
0.884, so the farm delivers at most 26.5 MW.

## 3 Gas turbines, fuel gas and CO2

The GTs follow the LEOGO reference turbine (Svendsen et al., 2023): rated
electric power 21.8 MW, minimum stable load 3.5 MW (16 %), three units
installed. Fuel use is linear in electric output (a Willans line):

$$ Q_{fuel} = \frac{P_{rated}}{\eta_{rated}}\left(a\,u + (1-a)\frac{P}{P_{rated}}\right), $$

where $u$ is 1 when the unit runs, $\eta_{rated} = 0.347$ and the no-load fuel
fraction $a = 0.184$ follow from the LEOGO fuel coefficients ($A = 2.35$,
$B = 0.53$; $\eta_{rated} = 1/(A+B)$, $a = B/(A+B)$). Efficiency therefore
falls from 34.7 % at full load to 29.3 % at half load and 17.7 % at minimum
load, and the specific CO2 emission rises from 623 to 737 and 1,220 kg/MWh.
Half of the heat in the exhaust that is not converted to electricity is
recovered as useful heat.

The lower heating value of the fuel gas, 38.96 MJ/Sm3, was computed with
NeqSim according to ISO 6976 from a generic North Sea fuel-gas composition.
CO2 emissions use the Norwegian standard factor of 2.34 kg CO2 per Sm3 fuel
gas (Statistics Norway, as used in LEOGO). A carbon balance of the assumed
composition gives 2.27 kg/Sm3, and reported Gullfaks data give 2.32–2.40
kg/Sm3 (Section 8), which supports the value used.

## 4 Topside process model and power per consumer

The process was modelled in NeqSim with the Peng–Robinson equation of state
for hydrocarbons and the CPA equation of state for water, which reproduces
liquid-water density and therefore pump power (SRK overestimated water-pump
power by about 30 % in a test). The flowsheet is:

* four-stage separation at 70 / 29 / 7.2 / 1.8 bara (Nguyen et al., 2013;
  the last stage lies within the 1.7–2.8 bar found on four real North Sea
  platforms by Voldsund et al., 2014);
* three recompression stages lifting gas from each separator to the next
  stage, each followed by a cooler (30 °C) and a scrubber;
* gas export compression to 180 bara (isentropic efficiency 0.75);
* oil export pumping to 50 bara (pump efficiency 0.60);
* water injection pumps from 7 to 250 bara (efficiency 0.75);
* seawater lift pumps supplying cooling water (10 K temperature rise) and
  make-up water for injection (10.4 bar lift);
* a fixed utility load of 3.5 MW and a heat demand of 3 MW.

Pressures, efficiencies and loads not referenced otherwise are from LEOGO.
The design point is 15,000 Sm3/d oil, a gas–oil ratio of 179 Sm3/Sm3
(2.68 MSm3/d gas export), a water cut of 40 % (10,000 m3/d produced water)
and 25,000 m3/d water injection. The resulting electric demand at design is
**20.3 MW** (Table 1).

**Table 1.** Electric power at the design point.

| Consumer | Power [MW] | Share |
|---|---|---|
| Water injection pumps | 9.19 | 45 % |
| Gas export compression | 3.73 | 18 % |
| Utilities and base load | 3.50 | 17 % |
| Recompression | 1.95 | 10 % |
| Oil export pumps | 1.48 | 7 % |
| Seawater lift pumps | 0.44 | 2 % |
| **Total** | **20.29** | |

At fixed pressures and efficiencies, steady-state power is proportional to
flow. Part-load behaviour was therefore represented by equipment limits: each
consumer has a number of identical parallel trains, which can be switched off
at low flow, and a minimum flow per train below which the train recycles
(anti-surge recycle for compressors, minimum-flow recirculation for pumps).
Gas export compression has 2 × 50 % trains, recompression one train, oil
export pumps 2 × 50 %, water injection and seawater lift pumps 3 × 33 %. The
minimum flow is 70 % for compressors and 30 % for pumps (assumed).

## 5 Consumer classification and flexibility

Each consumer was assigned to one class and one operating lever:

* **Must-run**: utilities and base load (3.5 MW), never reduced.
* **Flexible (deferrable)**: water injection pumps. The lever is the injection
  rate $f_{wi}$ (fraction of pump capacity). Postponed injection is not lost
  but must be caught up.
* **Sheddable**: recompression, gas export compression and oil export pumps.
  The lever is the production rate $f_p$; any reduction is lost production.
* **Mixed**: seawater lift pumps (cooling part follows $f_p$, make-up part
  follows $f_{wi}$).

The power of each lever group is a piecewise-linear function of the lever,
derived from the trains and minimum flows of Section 4. For production it
rises from 3.97 MW at 50 % rate to 4.72 MW just above 50 % (the second export
compressor train starts at its surge limit), 5.01 MW at 70 % and 7.16 MW at
100 %. For injection it is 0 when all pumps are stopped, 0.92 MW with one pump
on minimum-flow recycle (up to 10 % rate) and rises linearly to 9.19 MW at
full rate.

Production can be turned down to 50 % and changed by at most 10 % of design
per hour. Injection can vary between 0 and 100 % of pump capacity, by at most
34 % per hour (about one pump started or stopped). Its average must equal a
voidage-replacement target of 85 % of capacity. This is modelled as a
**virtual storage**: postponing injection builds a deficit $D$, measured in
hours of full-rate injection,

$$ D_t = D_{t-1} + (f_{wi}^{target} - f_{wi,t})\,\Delta t,\qquad 0 \le D_t \le D_{max} = 72\ \mathrm{h}. $$

The deficit limit represents how much injection the reservoir tolerates being
postponed and is treated as an uncertain assumption; it is varied from 0 to
168 h in the sensitivity analysis.

## 6 Scheduling model

The schedule is found with a mixed-integer linear program solved hourly over
the year. Decision variables are $f_p$, $f_{wi}$, the on/off state and power of
each GT, wind power used (the rest is curtailed), electric-heater power and,
in case 4, battery charge and discharge. The constraints are:

* **power balance**: GT power + wind used + battery discharge − charge =
  platform demand + electric heater;
* **heat balance**: recovered GT exhaust heat + electric heater (efficiency
  0.99) ≥ 3 MW heat demand;
* **GT limits**: minimum and rated load when running, the Willans fuel line,
  start-up indicators;
* **spinning reserve**: unused capacity of running GTs plus battery reserve
  ≥ 5 MW (LEOGO); a battery counts only if it can sustain the reserve for
  30 min;
* **at least one GT online**, because the wind turbines are grid-following
  and a GT is needed for frequency and voltage control (assumption, varied in
  the sensitivity analysis);
* the lever curves, ramp limits and injection deficit of Section 5, and the
  battery energy balance (round-trip efficiency 0.9).

The objective minimises, in NOK, the value of fuel gas burned (gas price
4.19 NOK/Sm3, since fuel gas could otherwise be exported), the CO2 cost
(2.0 NOK/kg, the Norwegian target for the total CO2 price in 2030), the value
of lost oil and gas (4,190 NOK/Sm3 oil) and a start-up cost of 2,000 NOK per
GT start (prices from LEOGO). Unserved energy and missing reserve are allowed
only with a penalty of 10⁶ NOK/MWh to keep the problem feasible; in all
reported runs they are zero apart from numerical rounding (< 0.03 MWh/yr).

The year is solved as 52 rolling windows of one week, each optimised with a
24 h look-ahead that is not committed. At the end of each window horizon the
injection deficit may not exceed, and the battery energy may not fall below,
their values at the window start. The solver stops within 0.5 % of the proven
optimum. One case-year takes about 2–3 minutes on a laptop-class CPU.

Because fuel is linear in power, the split of load between identical running
GTs does not change fuel use, and the solver's split is arbitrary. GT load is
therefore reported as shared in proportion to rating (droop sharing, as in
real operation), and an hour counts as a low-load hour when this shared load
is below 50 % of rating.

## 7 Sensitivity analysis

Cases 2–4 were re-run with one input changed at a time: wind farm size (1–4
turbines, 15–60 MW), CO2 price (0.5–3.0 NOK/kg), gas price (2–8 NOK/Sm3),
battery size (0–8 MW, 0–16 MWh), injection deficit limit (0–168 h), minimum
number of GTs online (1 or 0, with an 8 MW / 8 MWh battery), GT fleet (three
21.8 MW units, or two plus one smaller 19 MW unit with unverified data) and
an operating practice that keeps two GTs online regardless of wind.

## 8 Validation

Model results were compared with independent published values and field
data:

* **Platform power** against the processing-plant power of three real
  North Sea oil platforms (Voldsund et al., 2013, 2014) and six modelled
  platforms (Nguyen et al., 2013), the Johan Castberg plan for
  development and operation, and the average demand implied by Hywind Tampen
  (384 GWh/yr covering about 35 % of five platforms' electricity).
* **Wind capacity factor** against Hywind Tampen (expected 384 GWh/yr from
  88 MW; 58.4 % in Q1 2025).
* **CO2 avoided per MWh of wind** against Hywind Tampen (about 200 kt/yr for
  384 GWh/yr, 0.52 t/MWh).
* **Water-injection specific energy** against LEOGO.
* **CO2 intensity** against the Norwegian shelf average for 2023 (7.3 kg/boe,
  Offshore Norge, 2024) and non-electrified hubs (about 10.5 kg/boe,
  Westwood, 2022).
* **Field data** for the Gullfaks, Snorre and Statfjord field centres for
  2021, 2023 and 2024: CO2 to air, fuel gas and diesel use from the Norwegian
  Environment Agency (Norskeutslipp), and net production from the Norwegian
  Offshore Directorate (Sodir FactPages), summed over the fields processed at
  each centre. The boundary was checked by comparing oil volumes; they agree
  within 2 %.

A single published value counts as agreeing when the model is within ±20 %; a
published range when the model lies inside it.

## 9 Main limitations of the method

* Generic platform: fluid composition, minimum-flow limits, injection target
  and deficit limit are assumptions (Table T1).
* Steady-state process; no transient compressor or reservoir response.
* Perfect foresight of wind within each week (no forecast error).
* The model includes only power generation; flaring, diesel use and gas
  re-injection, which add to real field emissions, are outside the boundary.
* One weather year (2023).

## References

Gaertner, E. et al. (2020). *Definition of the IEA 15-Megawatt Offshore
Reference Wind Turbine*. NREL/TP-5000-75698.

Hersbach, H. et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of
the Royal Meteorological Society* 146, 1999–2049.

Hsu, S. A., Meindl, E. A. & Gilhousen, D. B. (1994). Determining the
power-law wind-profile exponent under near-neutral stability conditions at
sea. *Journal of Applied Meteorology* 33, 757–765.

Nguyen, T.-V., Pierobon, L., Elmegaard, B., Haglind, F., Breuhaus, P. &
Voldsund, M. (2013). Exergetic assessment of energy systems on North Sea oil
and gas platforms. *Energy* 62, 23–36. doi:10.1016/j.energy.2013.03.011.

Offshore Norge (2024). *Climate and environmental report 2024*.

Sharqawy, M. H., Lienhard, J. H. & Zubair, S. M. (2010). Thermophysical
properties of seawater. *Desalination and Water Treatment* 16, 354–380.

Svendsen, H. G. et al. (2023). The Low Emission Oil and Gas Open reference
platform – an off-grid energy system for renewable integration studies.
*IET Energy Systems Integration*. doi:10.1049/esi2.12085.

Voldsund, M., Ertesvåg, I. S., He, W. & Kjelstrup, S. (2013). Exergy analysis
of the oil and gas processing on a North Sea oil platform a real production
day. *Energy* 55, 716–727. doi:10.1016/j.energy.2013.02.038.

Voldsund, M., Nguyen, T.-V., Elmegaard, B., Ertesvåg, I. S., Røsjorde, A.,
Jøssang, K. & Kjelstrup, S. (2014). Exergy destruction and losses on four
North Sea offshore platforms: a comparative study of the oil and gas
processing plants. *Energy* 74, 45–58. doi:10.1016/j.energy.2014.02.080.

Westwood Global Energy (2022). Analysis of electrification and emissions on
the Norwegian continental shelf.

Data: Copernicus Climate Change Service (ERA5); Norwegian Environment Agency,
Norskeutslipp (CompanyID 22311, 16791, 16790); Norwegian Offshore Directorate,
FactPages (field production, yearly).

*Check before submission: Voldsund et al. (2013, 2014) and Nguyen et al.
(2013) have been checked against the original papers. The Johan Castberg
PDO and the other items marked "verify" in `docs/parameter_verification.md`
were obtained from search summaries and should still be confirmed.*
