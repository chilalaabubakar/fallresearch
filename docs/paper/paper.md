# Scheduling flexible topside loads to reduce gas turbine emissions on a wind-powered offshore oil platform

[Author names and affiliations]

Corresponding author: [name, e-mail]

## Abstract

Gas turbines on offshore oil and gas platforms are a major source of CO2
emissions, and wind power integrated into these off-grid systems saves less
fuel than expected because the turbines must stay online at inefficient part
load. Studies of wind-powered platforms usually treat the
topside load as fixed. This paper maps the electric demand of a generic North
Sea oil platform from a process model, classifies each consumer as must-run,
flexible or sheddable, and schedules the flexible consumers together with the
gas turbines. A steady-state process model gives the power of each consumer
as a function of its operating lever. A mixed-integer linear program then schedules production rate, water
injection rate, gas turbine commitment, wind use and an optional battery for
one year hourly with ERA5 wind data. Postponed water injection
is represented as a virtual storage that must be caught up. For a 20.3 MW
platform with a 30 MW wind farm, wind with fixed demand reduces annual CO2
emissions by 49 %. Flexible scheduling cuts them by a further 11 %
(7.1 kt/yr) without any loss of production, mainly because it avoids running
a second gas turbine: the hours with two turbines online fall from 1,702 to
30. About 24 h of deferrable injection captures the full benefit; prices do
not change the schedule. Operating rules that keep two gas turbines online
remove most of the gain. The model reproduces the CO2 avoided per MWh of wind
reported for Hywind Tampen within 2 %.

**Keywords:** offshore oil and gas platform; offshore wind; demand-side
flexibility; gas turbine part load; unit commitment; water injection

## Nomenclature

| Symbol | Description | Unit |
|---|---|---|
| $D_t$ | water injection deficit at hour $t$ | h of full-rate injection |
| $D_{max}$ | maximum injection deficit | h |
| $f_p$ | production rate, fraction of design | – |
| $f_{wi}$ | water injection rate, fraction of pump capacity | – |
| $f_{wi}^{target}$ | voidage-replacement target for $f_{wi}$ | – |
| $P$ | electric power of a gas turbine | W |
| $P_{rated}$ | rated electric power of a gas turbine | W |
| $Q_{fuel}$ | fuel energy input of a gas turbine (LHV) | W |
| $u$ | on/off state of a gas turbine | – |
| $a$ | no-load fuel fraction of the Willans line | – |
| $\eta_{rated}$ | electric efficiency at rated load | – |
| $v_{100}$, $v_{hub}$ | wind speed at 100 m and at hub height | m/s |
| $\alpha$ | wind shear exponent | – |
| GT | gas turbine | |
| MILP | mixed-integer linear program | |

## 1 Introduction

The petroleum industry accounts for about a quarter of Norway's greenhouse gas
emissions [@offshorenorge2024], and most of these emissions come from gas
turbines (GTs) that generate power and drive compressors on the offshore
installations [@norskpetroleum_emissions]. Power from shore removes them where
a grid connection is feasible, but many installations are far from shore or
too small to justify a cable. For these, offshore wind connected to the
platform's own power system is an alternative. The potential of this
combination was shown more than a decade ago [@he2010; @marvik2013], and
techno-economic studies have optimised the size of the wind farm and gas
turbine plant [@riboldi2018]. Hywind Tampen, an 88 MW floating wind farm
supplying five platforms in the Norwegian North Sea, has operated since 2023
and is expected to cover about 35 % of their electricity demand and avoid
about 200 kt of CO2 per year [@equinor2023].

On an off-grid platform, wind power saves less fuel than its energy suggests.
The wind turbines are usually grid-following, so at least one GT must stay
online for frequency and voltage control, and enough GT capacity must run to
cover a sudden loss of wind and the largest single load. When wind supplies
part of the demand, the GTs run at low load, where their efficiency falls
steeply: the efficiency of a typical aeroderivative turbine drops from about
35 % at full load to below 20 % near minimum stable load [@svendsen2023]. The
fuel saved per MWh of wind is therefore limited by how the remaining GT
capacity has to be operated, and much of the wind energy is curtailed when it
exceeds what the platform can absorb.

Operational optimisation can recover part of this loss. The open-source tool
Oogeso optimises GT commitment, wind use and storage on platforms, and shows
that a battery that provides reserve lets one turbine be switched off and the
remaining turbines run more efficiently [@svendsen2022]. The Low Emission Oil
and Gas Open (LEOGO) reference platform provides a common data set for such
studies [@svendsen2023]. Planning models for offshore energy hubs choose
investments in wind, storage and cables to meet emission targets
[@zhang2022], and power-system studies have examined how relaxing GT
operating constraints lets the platform absorb more wind [@khan2022]. In
these studies, however, the platform load is a given time series or a fixed
demand. Svendsen [@svendsen2022] identifies demand-side flexibility as
important for reducing the need for costly storage, and leaves its
representation in operational optimisation to future work.

The process plant on an oil platform is not a fixed load. Water injection
for pressure support is one of the largest electric consumers, second only
to gas compression on the platforms studied by Nguyen et al. [@nguyen2013].
It can be postponed for hours as long as the average injection meets the
reservoir's needs. Production can be reduced, at the cost of lost revenue. Other loads,
such as utilities and safety systems, must run at all times. How much
flexibility these consumers offer, and what it is worth, depends on
equipment limits that a fixed load profile hides: parallel trains,
minimum-flow recycle on compressors and pumps, ramp limits, and the
requirement to catch up postponed injection.

This paper quantifies the value of scheduling flexible topside consumers on
a wind-powered oil platform. Its contributions are:

1. A demand map of a generic North Sea oil platform derived from a
   steady-state process model, which gives the power of each consumer as a
   function of its operating lever, including train switching and
   minimum-flow recycle.
2. A classification of the consumers as must-run, flexible (deferrable) or
   sheddable, with water injection represented as a virtual storage that must
   be caught up.
3. A mixed-integer linear scheduling model that optimises the flexible
   consumers together with GT commitment, wind use and an optional battery
   for a full year at hourly resolution.
4. A comparison of four cases, from GTs only to wind with flexible demand and
   a battery, with sensitivity analysis on the assumptions that drive the
   result, and validation against Hywind Tampen and reported field data.

Section 2 describes the platform, models and cases. Section 3 presents the
results, Section 4 discusses the mechanism, implications and limitations,
and Section 5 concludes. The model code, input data and all parameters with
their sources are openly available (see Data availability).

## 2 Methods

### 2.1 System and cases

The study models the electric power system of a generic oil platform in the
northern North Sea (Tampen area, 61.0° N, 2.0° E) for the year 2023 at hourly
resolution (Fig. 1). Power is supplied by three GTs and, in the wind cases,
by a nearby two-turbine offshore wind farm. Four cases are compared:

1. **GTs only**, fixed demand (baseline).
2. **Wind + GTs, fixed demand**: production and water injection at their
   design and target rates in every hour.
3. **Wind + GTs, flexible scheduling**: production and injection rates are
   decision variables.
4. **Case 3 + battery** of 4 MW / 4 MWh.

The platform keeps its three GTs in all cases, as a retrofit would; the
optimiser decides how many run in each hour. Process behaviour is represented
by steady-state operating points with ramp limits; transient process
dynamics are outside the scope. The model is written in Python with NeqSim
for thermodynamics and process simulation [@neqsim] and Pyomo with the HiGHS
solver for optimisation [@bynum2021; @huangfu2018]. Every parameter is stored
in a single configuration file with its unit and source; 29 of 101 parameters
are marked as assumptions (Table S1).

> **Fig. 1.** The platform power system. Supply (left) and topside consumers
> coloured by flexibility class (middle) are connected to one AC bus. The
> scheduler sets the production rate $f_p$, the injection rate $f_{wi}$ and
> the GT commitment every hour.

### 2.2 Wind farm power

Hourly wind components at 100 m were taken from the ERA5 reanalysis
[@hersbach2020] and extrapolated to the 150 m hub height with a power law,

$$ v_{hub} = v_{100}\left(\frac{z_{hub}}{z_{100}}\right)^{\alpha}, \qquad \alpha = 0.11, $$

the exponent recommended for near-neutral conditions at sea [@hsu1994].
Turbine power follows the IEA 15 MW reference turbine [@gaertner2020]. The
base-case farm of two turbines (30 MW) is of the same order as the 32 MW farm
of the LEOGO platform [@svendsen2023]. Wake losses (5 %), electrical losses
(2 %) and availability (95 %) give a combined factor of 0.884, so the farm
delivers at most 26.5 MW.

### 2.3 Gas turbines and emissions

The GTs follow the LEOGO reference turbine [@svendsen2023]: 21.8 MW rated
electric power and 3.5 MW minimum stable load. Fuel input is linear in
electric output (a Willans line),

$$ Q_{fuel} = \frac{P_{rated}}{\eta_{rated}}\left(a\,u + (1-a)\frac{P}{P_{rated}}\right), $$

with $\eta_{rated} = 0.347$ and $a = 0.184$ derived from the LEOGO fuel
coefficients. Efficiency therefore falls from 34.7 % at full load to 29.3 %
at half load and 17.7 % at minimum load (Fig. S2). Half of the exhaust heat
not converted to power is recovered for process heating. The lower heating
value of the fuel gas (38.96 MJ/Sm³) was computed with NeqSim to ISO 6976
[@iso6976]. CO2 emissions use the Norwegian standard factor of 2.34 kg/Sm³
[@svendsen2023].

### 2.4 Process model and demand map

The topside process was modelled in NeqSim with the Peng–Robinson equation
of state for hydrocarbons and the CPA equation of state for water. The
flowsheet comprises four-stage separation at 70 / 29 / 7.2 / 1.8 bara
[@nguyen2013], with the last stage within the 1.7–2.8 bar found on four real
North Sea platforms [@voldsund2014]. It also includes recompression with
intercooling, gas export compression to 180 bara, oil export pumping, water
injection from 7 to 250 bara, seawater lift for cooling and injection make-up
(seawater properties from [@sharqawy2010]), and a fixed utility load of
3.5 MW. Gas export pressure agrees with the 179 bar reported for a real
platform [@voldsund2014]. At the design point of 15,000 Sm³/d oil, a
gas–oil ratio of 179 Sm³/Sm³, a water cut of 40 % and 25,000 m³/d water
injection, the electric demand is 20.3 MW (Table 1).

**Table 1.** Electric power at the design point.

| Consumer | Class | Trains | Power [MW] | Share |
|---|---|---|---|---|
| Water injection pumps | flexible | 3 × 33 % | 9.19 | 45 % |
| Gas export compression | sheddable | 2 × 50 % | 3.73 | 18 % |
| Utilities and base load | must-run | – | 3.50 | 17 % |
| Recompression | sheddable | 1 × 100 % | 1.95 | 10 % |
| Oil export pumps | sheddable | 2 × 50 % | 1.48 | 7 % |
| Seawater lift pumps | mixed | 3 × 33 % | 0.44 | 2 % |
| **Total** | | | **20.29** | |

At fixed pressures and efficiencies, steady-state power is proportional to
flow. Part-load behaviour is therefore set by equipment limits: each
consumer has parallel trains that can be switched off at low flow, and a
minimum flow per train below which it recycles (anti-surge recycle for
compressors, minimum-flow recirculation for pumps). The minimum flow is 70 %
for compressors and 30 % for pumps. Anti-surge recycle rates of 4–92 % have
been reported on real North Sea compressor trains [@voldsund2014].

### 2.5 Consumer classes and levers

Each consumer is assigned to one class and one operating lever (Fig. 1):

* **Must-run**: utilities and base load, never reduced.
* **Flexible (deferrable)**: water injection pumps. The lever is the
  injection rate $f_{wi}$. Postponed injection is not lost but must be caught
  up.
* **Sheddable**: recompression, gas export compression and oil export pumps.
  The lever is the production rate $f_p$; any reduction is lost production.
* **Mixed**: seawater lift pumps, whose cooling part follows $f_p$ and
  make-up part follows $f_{wi}$.

The power of each lever group is a piecewise-linear function of the lever,
built from the trains and minimum flows (Fig. 2). Production can be turned
down to 50 % and changed by at most 10 % of design per hour. Injection can
vary between 0 and 100 % of pump capacity, by at most 34 % per hour (about
one pump), and its average must meet a voidage-replacement target of 85 % of
capacity. This is modelled as a virtual storage: postponing injection builds
a deficit measured in hours of full-rate injection,

$$ D_t = D_{t-1} + \left(f_{wi}^{target} - f_{wi,t}\right)\Delta t, \qquad 0 \le D_t \le D_{max}, $$

with $D_{max} = 72$ h. The deficit limit represents how much injection the
reservoir tolerates being postponed. It is uncertain and is varied from 0 to
168 h in the sensitivity analysis.

### 2.6 Scheduling model

The schedule is a mixed-integer linear program. Its decision variables are
$f_p$, $f_{wi}$, the on/off state and power of each GT, the wind power used
(the rest is curtailed), electric heater power and, in case 4, battery
charge and discharge. The constraints are:

* power balance: GT power, wind used and battery discharge equal platform
  demand, electric heater and battery charge;
* heat balance: recovered exhaust heat plus electric heating covers the
  3 MW heat demand;
* GT limits: minimum and rated load when running, the Willans fuel line and
  start-up indicators;
* spinning reserve: unused capacity of running GTs plus battery reserve of
  at least 5 MW [@svendsen2023]; a battery counts only if it can sustain the
  reserve for 30 min;
* at least one GT online, because the wind turbines are grid-following;
* the lever power curves, ramp limits and injection deficit of Section 2.5,
  and the battery energy balance (round-trip efficiency 0.9).

The objective minimises, in NOK, the value of fuel gas burned
(4.19 NOK/Sm³, since fuel gas could otherwise be sold), the CO2 cost
(2.0 NOK/kg, the Norwegian target for the total CO2 price in 2030
[@klimaplan2021]), the value of lost oil and gas (4,190 NOK/Sm³ oil) and a
start-up cost of 2,000 NOK per GT start [@svendsen2023]. Unserved energy and
missing reserve are allowed only with a penalty of 10⁶ NOK/MWh, to keep the
problem feasible; in all reported runs they are below 0.03 MWh/yr.

The year is solved as 52 rolling one-week windows, each with an uncommitted
24 h look-ahead. At the end of each look-ahead horizon the injection deficit
may not exceed, and the battery energy may not fall below, their values at
the window start. The solver stops within 0.5 % of the proven optimum, and a
case-year takes 2–3 min on a laptop-class processor. Because fuel is linear
in power, the split of load between identical running GTs does not change
fuel use. GT load is therefore reported as shared in proportion to rating,
as in droop control, and an hour counts as low-load when this shared load is
below 50 % of rating.

### 2.7 Sensitivity analysis and validation

Cases 2–4 were rerun with one input changed at a time:

* wind farm size (1–4 turbines);
* CO2 price (0.5–3.0 NOK/kg) and gas price (2–8 NOK/Sm³);
* battery size (up to 8 MW / 16 MWh);
* injection deficit limit (0–168 h);
* minimum number of GTs online (1 or 0, with an 8 MW / 8 MWh battery);
* GT fleet (two of the three main units plus one smaller unit);
* an operating practice that keeps two GTs online whatever the wind.

The results were compared with independent values:

* **platform power:** three real North Sea oil platforms
  [@voldsund2013; @voldsund2014], six modelled platforms [@nguyen2013], the
  Johan Castberg development plan [@castberg2017], and the demand implied by
  Hywind Tampen [@equinor2023];
* **wind capacity factor:** Hywind Tampen [@equinor2023; @nowind2025];
* **CO2 avoided per MWh of wind:** Hywind Tampen [@equinor2023];
* **water-injection specific energy:** LEOGO [@svendsen2023];
* **CO2 intensity:** the Norwegian shelf [@offshorenorge2024] and
  non-electrified hubs [@westwood2022];
* **field data** for the Gullfaks, Snorre and Statfjord field centres,
  2021–2024: emissions and fuel use from Norskeutslipp [@norskeutslipp] and
  production from the Norwegian Offshore Directorate [@sodir_factpages].

A single value counts as agreeing when the model is within ±20 %; a range
when the model lies inside it.

## 3 Results

### 3.1 Demand map and wind resource

Water injection is the largest consumer (9.2 MW, 45 % of the design demand)
and the only large deferrable one (Table 1, Fig. 2). Stopping injection at
full production lowers demand from 20.3 MW to 10.7 MW, a swing of 9.6 MW that
costs no production as long as the injection is caught up. The production
lever has a step just above 50 % rate, where the second export compressor
train must start at its surge limit.

> **Fig. 2.** Demand map. Left: electric power at design by consumer,
> coloured by flexibility class. Right: power of the production (sheddable)
> and injection (flexible) levers against lever position.

ERA5 gives a mean wind speed of 9.8 m/s at hub height and a capacity factor
of 50.9 % for the 30 MW farm in 2023 (Fig. S1). Output is seasonal (63–68 %
in January–February, 36–37 % in June–August). The farm delivers its maximum
in 40 % of the hours and nothing in 9.6 %, and available wind exceeds the
design demand in 4,017 h.

### 3.2 Comparison of the four cases

**Table 2.** Annual results for the four cases (2023).

| | 1 GTs only | 2 Wind, fixed | 3 Wind, flexible | 4 Flexible + battery |
|---|---|---|---|---|
| CO2 [kt/yr] | 127.7 | 64.7 | 57.6 | 57.2 |
| Reduction vs case 1 | – | 49.4 % | 54.9 % | 55.2 % |
| Fuel gas [MSm³/yr] | 54.6 | 27.6 | 24.6 | 24.4 |
| GT running [unit-h/yr] | 17,520 | 10,462 | 8,790 | 8,760 |
| GT below 50 % load [unit-h/yr] | 17,520 | 9,005 | 5,928 | 6,235 |
| GT starts [–/yr] | 0 | 149 | 6 | 0 |
| Wind used [GWh/yr] | 0 | 89.3 | 95.0 | 95.8 |
| Wind curtailed [GWh/yr] | 0 | 44.5 | 38.8 | 38.0 |
| Lost production | 0 | 0 | 0 | 0 |
| Fuel value + CO2 cost [MNOK/yr] | 484.0 | 245.1 | 218.1 | 216.6 |

With GTs only, two turbines run in every hour to carry the load and the
5 MW reserve, each at about 43 % load. The platform burns 54.6 MSm³ of fuel
gas and emits 127.7 kt CO2 per year (Table 2, Fig. 3). A 30 MW wind farm
with fixed demand halves the emissions to 64.7 kt (−49.4 %). Because demand
cannot follow the wind, 44.5 GWh (33 % of the available wind energy) is
curtailed, and a second GT is still needed in 1,702 h, with 149 starts.

Flexible scheduling (case 3) reduces CO2 by a further 7.1 kt/yr, 11.0 %
relative to case 2, without any loss of production. GT low-load unit-hours
fall by 34 %, GT starts from 149 to 6 and curtailment by 13 %, and the
combined fuel value and CO2 cost falls by 27 MNOK/yr. A 4 MW / 4 MWh battery
(case 4) adds only 0.4 kt: it removes the remaining starts, but with one GT
always online it cannot remove the main remaining loss, one turbine idling
near minimum load whenever the wind covers the demand.

> **Fig. 3.** Annual CO2, fuel gas, GT hours below 50 % load and lost
> production for cases 1–4.

### 3.3 How flexible scheduling saves fuel

The saving comes almost entirely from avoiding a second GT. With fixed
demand, a second turbine must start whenever the wind drops and one GT
cannot carry the load while holding 5 MW in reserve, and each such hour
costs the no-load fuel of a whole extra turbine. In case 3 the optimiser
postpones water injection in exactly these hours, so a second GT runs in
only 30 h of the year (Fig. 4, Fig. 5).

> **Fig. 4.** Week 29 (16–22 July 2023), the week with the median fuel
> saving. Top and middle: power supplied by GTs and wind with fixed (case 2)
> and flexible (case 3) demand. Bottom: production and injection rates.

> **Fig. 5.** Duration curves of GT load per running unit (left; shaded:
> below 50 %) and of the number of GTs running (right).

Injection follows the wind (Fig. 6). Its mean rises from 59 % of capacity in
the calmest hours to 98–99 % when more than 16 MW of wind is available
(r = 0.61). It is below its 85 % target in 2,597 h and stopped in 178 h, and
over the year it averages 84.9 %, so the voidage target is met. The deficit
averages 7.5 h of full-rate injection and never exceeds 25.2 h, well within
the 72 h allowed; 6.3 h remain to be caught up at the end of the year.
Production is never reduced. One hour at 50 % rate would lose oil and gas
worth about 1.5 MNOK, while the fuel and CO2 saved are worth a few thousand
NOK. The saving from flexibility is present in every month
(0.42–0.76 kt/month, Fig. S3).

> **Fig. 6.** Left: water injection rate against available wind in case 3
> (mean and 10–90 % range of hours). Right: distribution of the injection
> deficit (dashed: 72 h limit).

### 3.4 Sensitivity analysis

**Table 3.** Annual CO2 [kt/yr] in the sensitivity runs.

| Varied input | Values | Case 2 | Case 3 | Case 4 |
|---|---|---|---|---|
| Wind farm size [turbines] | 1 / 2 / 3 / 4 | 77.6 / 64.7 / 60.2 / 57.6 | 72.0 / 57.6 / 53.3 / 50.9 | |
| CO2 price [NOK/kg] | 0.5 / 1 / 2 / 3 | | 57.5 / 57.5 / 57.6 / 57.5 | |
| Gas price [NOK/Sm³] | 2 / 4.19 / 8 | | 57.5 / 57.6 / 57.5 | |
| Battery [MW / MWh] | 0 / 2/2 / 4/4 / 8/8 / 8/16 | | | 57.6 / 57.3 / 57.2 / 56.9 / 56.4 |
| Injection deficit limit [h] | 0 / 24 / 72 / 168 | | 64.7 / 57.6 / 57.6 / 57.5 | |
| Min. GTs online (8 MW battery) | 1 / 0 | | | 56.9 / 38.7 |
| GT fleet | 3 main / 2 main + 1 small | | 57.6 / 55.6 | |
| Keep two GTs online | | 90.7 | 87.7 | |

Table 3 and Fig. 7 show which inputs matter:

* **Prices do not change the schedule.** Across CO2 prices of 0.5–3 NOK/kg
  and gas prices of 2–8 NOK/Sm³, emissions change by less than 0.1 %. The
  injection schedule is driven by fuel savings that are worthwhile at any
  price, and production is never shed.
* **A small deferral capacity is enough.** With no deferral allowed, case 3
  equals case 2. A deficit limit of 24 h already gives the full saving.
* **Wind farm size has diminishing returns.** Doubling the farm to 60 MW
  lowers case 3 emissions only from 57.6 to 50.9 kt, because one GT must stay
  online. The value of flexibility is largest for the base-case farm
  (7.1 kt) and smaller for a 15 MW farm (5.5 kt).
* **Batteries add little on their own**, at most 2 % (8 MW / 16 MWh).
* **The minimum number of GTs online dominates.** If an 8 MW / 8 MWh battery
  can provide reserve and grid stability so that all GTs may stop, emissions
  fall to 38.7 kt, 32 % below the same case with one GT online.
* **Operating practice matters as much as hardware.** If two GTs are kept
  online whatever the wind, emissions rise to 90.7 kt (case 2) and 87.7 kt
  (case 3), and flexibility saves only 3.1 kt.

> **Fig. 7.** Sensitivity of annual CO2 emissions to wind farm size, CO2 and
> gas price, battery size, injection deficit limit, minimum number of GTs
> online, GT fleet and operating practice.

### 3.5 Validation

**Table 4.** Model results against published benchmarks.

| Benchmark | Model | Published | Status |
|---|---|---|---|
| Platform power, three real oil platforms [@voldsund2013; @voldsund2014] | 20.3 MW | 17–30 MW | within |
| Platform power, six modelled platforms [@nguyen2013] | 20.3 MW | 22.6–31.1 MW | below range |
| Platform power, Johan Castberg [@castberg2017] | 20.3 MW | 25 MW | within 20 % |
| Platform power implied by Hywind Tampen [@equinor2023] | 20.3 MW | 25.1 MW | within 20 % |
| Wind capacity factor, Hywind Tampen design [@equinor2023] | 50.9 % | 49.8 % | agrees |
| Wind capacity factor, Hywind Tampen Q1 2025 [@nowind2025] | 50.9 % | 58.4 % (winter) | within 20 % |
| CO2 avoided per MWh wind, two GTs kept online [@equinor2023] | 0.51 t/MWh | 0.52 t/MWh | agrees |
| Water injection specific energy [@svendsen2023] | 8.8 kWh/m³ | 9.0 kWh/m³ | agrees |
| CO2 intensity, Norwegian shelf 2023 [@offshorenorge2024] | 3.1 kg/boe | 7.3 kg/boe | lower |

Platform power, wind resource and pump energy agree with the published
values (Table 4, Fig. 8). The strongest check is the CO2 avoided per MWh of
wind, because it tests the wind, part-load fuel, CO2 factor and scheduling
together. When the model keeps two GTs online and only lowers their load, as
assumed in the Hywind Tampen estimate, it avoids 0.51 t/MWh against the
published 0.52 t/MWh. When a GT may stop in windy hours, it avoids
0.71 t/MWh, because the no-load fuel of the stopped unit is saved as well.

The field data support the fuel and emission model (Fig. 8, right). Gullfaks
emits 2.32–2.40 kg CO2 per Sm³ of fuel gas, consistent with the 2.34 kg/Sm³
used here. After Hywind Tampen started supplying power, fuel gas use fell by
30 % at Gullfaks (2021–2023) and 11 % at Snorre (2021–2024), while it was
unchanged at Statfjord, which receives no wind power; production also
declined, so not all of this is due to the wind farm. The model's CO2
intensity is lower than the field and shelf values because it covers only
power generation on an efficient platform at plateau rate, whereas the field
values include flaring, diesel, gas re-injection and the lower production of
mature fields.

> **Fig. 8.** Left: model results divided by published benchmarks (1 =
> equal; shaded: ±20 %; grey bars: published ranges). Right: CO2 intensity of
> the Gullfaks, Snorre and Statfjord field centres (grey: GT-powered; teal:
> receiving Hywind Tampen power) with the model case 1 value (dashed).

## 4 Discussion

### 4.1 Why load flexibility works

The value of flexible demand on a wind-powered platform lies in unit
commitment, not in energy shifting. A GT that runs at low load to provide
reserve costs a large share of its full-load fuel, so the expensive hours are
those in which the wind is just too weak for one turbine to carry the load
with reserve. Deferring water injection in these hours keeps the second
turbine off. This explains three results: most of the saving comes from
1,672 avoided hours with two GTs online; a deficit capacity of about one day
captures it all, because these hours occur in short spells; and the saving
disappears when operating rules keep two GTs online anyway. Energy shifting
alone, by contrast, is limited: curtailment falls by only 13 %, because one
GT must stay online and a 30 MW wind farm often exceeds what the platform
can use.

The same reasoning explains why a battery adds little in case 4. With at
least one GT online, the battery cannot remove the main remaining loss, one
turbine idling near minimum load. The large saving appears only when the
battery, or grid-forming wind turbines, can take over the role of the last
running GT (38.7 kt, −32 %). This agrees with the finding that a battery
providing reserve lets platform GTs be switched off [@svendsen2022]. The
present results add that process flexibility gives much of the same benefit
without new equipment, and that both measures act on the same mechanism.

### 4.2 Implications for operators

Three implications follow. First, the flexibility already exists on most oil
platforms with water injection and can be used without investment, although
the control system must coordinate injection with the power plant. Second,
the reservoir requirement is modest: about 24 h of injection deferral,
averaging 7.5 h, is a small change compared with the time scale of
reservoir pressure support. It should nevertheless be confirmed with
reservoir engineers for each field. Third, the result does not depend on the
carbon price, because the fuel saved has value on its own. Operating
practice, notably how many GTs must be online and what counts as reserve,
has a larger effect on emissions than any price or the battery size, and
deserves the same attention as the choice of wind farm.

### 4.3 Limitations

The platform is generic. Its fluid composition, minimum-flow limits,
injection target and deficit limit are assumptions, although the sensitivity
analysis shows that the result is robust to the deficit limit. The process is
represented by steady states; transient compressor behaviour, start-up
times of pumps and GTs beyond the start cost, and the reservoir response to
deferred injection are not modelled. The scheduler has perfect foresight of
wind within each week, so the savings are an upper bound for real operation
with forecast errors. The analysis covers one weather year and a single
platform without power import or export. Investment costs are outside the
scope, so the results show the operational value of flexibility but not the
cost per tonne of CO2 avoided. Finally, the small GT in the fleet
sensitivity relies on unverified performance data.

## 5 Conclusions

This paper mapped the electric demand of a generic North Sea oil platform
from a process model, classified the consumers by flexibility, and scheduled
them together with the gas turbines and a wind farm for one year. The main
conclusions are:

1. A 30 MW wind farm halves the CO2 emissions of the 20 MW platform (−49 %)
   with fixed demand.
2. Scheduling flexible topside consumers reduces emissions by a further 11 %
   (7.1 kt/yr) without lost production. GT low-load hours fall by 34 % and GT
   starts nearly disappear.
3. Water injection provides all of the useful flexibility; shedding
   production is never worthwhile. A deferral capacity of about 24 h of
   injection is enough.
4. The saving comes from avoiding a second running gas turbine. It therefore
   depends on operating practice: keeping two GTs online removes most of it,
   while allowing all GTs to stop, with a battery providing reserve, would
   reduce emissions by a further third.
5. Carbon price, gas price and battery size alone have little effect.
6. The model reproduces the CO2 avoided per MWh of wind reported for Hywind
   Tampen within 2 %.

Future work should test the approach with wind forecast errors, several
weather years and real platform data, and add investment costs to evaluate
the cost of CO2 abatement.

## Declarations

**CRediT authorship contribution statement.** [Author 1]: Conceptualization,
Methodology, Software, Formal analysis, Writing – original draft. [Author 2]:
Supervision, Writing – review & editing.

**Declaration of competing interest.** The authors declare that they have no
known competing financial interests or personal relationships that could
have appeared to influence the work reported in this paper.

**Declaration of generative AI and AI-assisted technologies in the
manuscript preparation process.** During the preparation of this work the
author(s) used [tool name] in order to [purpose]. After using this tool, the
author(s) reviewed and edited the content as needed and take(s) full
responsibility for the content of the published article.

**Data availability.** The model code, configuration with all parameters and
sources, and the processed results are available at [repository URL]. ERA5
data are available from the Copernicus Climate Change Service.

**Acknowledgements.** This work contains modified Copernicus Climate Change
Service information (2023). [Funding.]

## References

{{REFERENCES}}
