# Scheduling flexible topside loads to reduce gas turbine emissions on a wind-powered offshore oil platform

[Author names and affiliations]

Corresponding author: [name, e-mail]

## Abstract

Gas turbines on offshore oil and gas platforms are a major source of CO2
emissions, and wind power integrated into these off-grid systems saves less
fuel than expected because the turbines must stay online at inefficient part
load. Studies of wind-powered platforms usually treat the topside load as
fixed. This paper maps the electric demand of a generic North Sea oil
platform from a process model, classifies each consumer as must-run,
flexible or sheddable, and schedules the flexible consumers together with
the gas turbines. A steady-state process model gives the power of each
consumer as a function of its operating lever. A mixed-integer linear
program then schedules production rate, water injection rate, gas turbine
commitment, wind use and an optional battery for one year hourly with ERA5
wind data. Postponed water injection is represented as a virtual storage
that must be caught up. For a 20.3 MW platform with a 30 MW wind farm, wind
with fixed demand reduces annual CO2 emissions by 49 %. Flexible scheduling
cuts them by a further 11 % (7.1 kt/yr) without any loss of production,
mainly because it avoids running a second gas turbine: the hours with two
turbines online fall from 1,702 to 30. About 24 h of deferrable injection
captures the full benefit; prices do not change the schedule. Operating
rules that keep two gas turbines online remove most of the gain. The model
reproduces the CO2 avoided per MWh of wind reported for Hywind Tampen within
2 %.

**Keywords:** offshore oil and gas platform; offshore wind; demand-side
flexibility; gas turbine part load; unit commitment; water injection

## Nomenclature

| Symbol | Description | Unit |
|---|---|---|
| *Sets and indices* | | |
| $t \in T$ | hours of a scheduling window | – |
| $g \in G$ | gas turbines | – |
| *Variables* | | |
| $f_{p,t}$ | production rate, fraction of design | – |
| $f_{wi,t}$ | water injection rate, fraction of pump capacity | – |
| $D_t$ | water injection deficit | h of full-rate injection |
| $u_{g,t}$ | on/off state of gas turbine $g$ | – |
| $s_{g,t}$ | start-up indicator of gas turbine $g$ | – |
| $P_{g,t}$ | electric power of gas turbine $g$ | W |
| $Q_{g,t}$ | fuel energy input of gas turbine $g$ (LHV) | W |
| $P^{w}_t$, $P^{c}_t$ | wind power used and curtailed | W |
| $P^{h}_t$ | electric heater power | W |
| $P^{ch}_t$, $P^{dis}_t$, $E_t$ | battery charge, discharge and stored energy | W, J |
| $P^{dem}_t$ | platform electric demand | W |
| *Parameters* | | |
| $P^{avail}_t$ | available wind farm power | W |
| $P_{rated}$, $P_{min}$ | rated and minimum stable gas turbine power | W |
| $\eta_{rated}$ | gas turbine electric efficiency at rated load | – |
| $a$ | no-load fuel fraction of the Willans line | – |
| $\phi$ | fraction of gas turbine waste heat recovered | – |
| $f_{wi}^{target}$ | voidage-replacement target for $f_{wi}$ | – |
| $D_{max}$ | maximum injection deficit | h |
| $R$ | spinning reserve requirement | W |
| $H$ | process heat demand | W |
| $v_{100}$, $v_{hub}$ | wind speed at 100 m and at hub height | m/s |
| $\alpha$ | wind shear exponent | – |
| *Abbreviations* | | |
| GT | gas turbine | |
| LHV | lower heating value | |
| MILP | mixed-integer linear program | |

## 1 Introduction

The petroleum industry accounts for about a quarter of Norway's greenhouse
gas emissions [@offshorenorge2024], and most of these emissions come from
gas turbines (GTs) that generate power and drive compressors on the offshore
installations [@norskpetroleum_emissions]. Power from shore removes them
where a grid connection is feasible. A Norwegian government study found that
the electrification projects then planned would cut emissions at less than
NOK 1,500 per tonne of CO2 [@sodir2020], and the CO2 cost faced by operators
has since risen from about NOK 860 per tonne in 2020 to NOK 1,860 in 2025
[@sodir_pfs]. Many installations, however, are far from shore, too small to
justify a cable, or connected to a grid whose capacity is needed onshore.
The operators' own assessments found the alternatives to power from shore
more costly or less effective [@sodir_pfs], which is why improving the
efficiency of the remaining offshore power plants matters.

Offshore wind connected directly to a platform's power system is the most
studied alternative. He et al. [@he2010] showed more than a decade ago that
wind could supply part of the demand of North Sea platforms and reduce
their emissions, and Marvik et al. [@marvik2013] found that a cluster of
platforms with an integrated wind farm can be operated with acceptable
transient stability. Riboldi and Nord [@riboldi2018] optimised the design of
an offshore combined-cycle plant with a wind farm and concluded that the
economic case depends on favourable gas and CO2 prices. The concept has now
been realised: Hywind Tampen, an 88 MW floating wind farm supplying five
platforms in the Norwegian North Sea, has operated since 2023 and is
expected to cover about 35 % of their electricity demand and avoid about
200 kt of CO2 per year [@equinor2023].

On an off-grid platform, wind power saves less fuel than its energy
suggests. The wind turbines are usually grid-following, so at least one GT
must stay online for frequency and voltage control, and enough GT capacity
must run to cover a sudden loss of wind or of a generator. When wind
supplies part of the demand, the GTs therefore run at low load, where their
efficiency falls steeply: the reference turbine of the LEOGO platform drops
from about 35 % electric efficiency at full load to below 20 % near minimum
stable load [@svendsen2023]. Exergy analyses of North Sea platforms have
found that the gas turbines account for 62–65 % of the exergy destroyed on a
platform, more than the whole processing plant [@nguyen2013]. The fuel saved
per MWh of wind is thus limited by how the remaining GT capacity must be
operated, and a large part of the wind energy is curtailed when it exceeds
what the platform can absorb.

Operational optimisation can recover part of this loss. The open-source
tool Oogeso optimises GT commitment, wind use and storage on platforms, and
shows that a battery that provides reserve lets one turbine be switched off
and the remaining turbines run more efficiently [@svendsen2022]. The Low
Emission Oil and Gas Open (LEOGO) reference platform provides a common data
set for such studies [@svendsen2023]. Planning models for offshore energy
hubs choose investments in wind, storage and cables to meet emission targets
[@zhang2022], and power-system studies have examined how relaxing GT
operating constraints lets the platform absorb more wind [@khan2022]. In
these studies, however, the platform load is a given time series or a fixed
demand. Svendsen [@svendsen2022] identifies demand-side flexibility as
important for reducing the need for costly storage, and leaves its
representation in operational optimisation to future work.

Demand-side flexibility is well established in onshore process industries.
Scheduling of energy-intensive production, such as steel, cement, aluminium
or air separation, around electricity prices has been studied extensively
[@zhang_grossmann2016; @golmohamadi2022]. Those studies exploit time-varying
prices in a large grid. An off-grid platform is different: there is no
price signal, and the value of moving a load lies in the fuel and emissions
of its own power plant. That value is strongly non-linear, because it
depends on whether a load change allows a GT to be stopped or avoids
starting one, and it is limited by process constraints that are specific
to oil and gas production.

The process plant on an oil platform is not a fixed load. Water injection
for pressure support is one of the largest electric consumers, second only
to gas compression on the platforms studied by Nguyen et al. [@nguyen2013].
It can be postponed for hours as long as the cumulative injection meets the
reservoir's needs, because reservoir pressure responds slowly. Production
can be reduced, at the cost of lost revenue. Other loads, such as utilities
and safety systems, must run at all times. How much flexibility these
consumers offer, and what it is worth, depends on equipment limits that a
fixed load profile hides: parallel trains, minimum-flow recycle on
compressors and pumps, ramp limits, and the requirement to catch up
postponed injection.

This paper therefore asks three questions. How much fuel and CO2 can be
saved by scheduling the flexible topside consumers of a wind-powered oil
platform, compared with operating the same platform at fixed demand? Which
consumers provide the flexibility, and through which mechanism does it save
fuel? And which technical and operational assumptions decide the size of the
saving? Its contributions are:

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
northern North Sea (Tampen area, 61.0° N, 2.0° E) for the year 2023 at
hourly resolution (Fig. 1). The platform produces oil with associated gas,
exports both, and injects water for pressure support. Power is supplied by
three GTs and, in the wind cases, by a nearby two-turbine offshore wind farm
connected to the platform's AC system. Four cases are compared:

1. **GTs only**, fixed demand (baseline).
2. **Wind + GTs, fixed demand**: production and water injection at their
   design and target rates in every hour.
3. **Wind + GTs, flexible scheduling**: production and injection rates are
   decision variables.
4. **Case 3 + battery** of 4 MW / 4 MWh.

The platform keeps its three GTs in all cases, as a retrofit would; the
optimiser decides how many run in each hour. Case 2 corresponds to the
usual assumption in platform–wind studies, in which wind displaces GT power
but the load is unchanged. The difference between cases 2 and 3 isolates
the value of demand flexibility, and case 4 tests whether a small battery
adds to it.

The base case uses the existing main turbines rather than a new, smaller
GT, for three reasons. First, wind is being added to existing platforms that
keep their installed turbines; the five platforms supplied by Hywind Tampen
are an example [@equinor2023]. Second, the mechanism studied here is the
number of GTs that must be online, which is set by the load, the reserve and
the wind rather than by the size of the units. Whether a smaller unit adds
to the saving is tested in the sensitivity analysis with an 11.35 MW Solar
Turbines Mars 100 [@solar_mars100], either replacing one main unit or added
to the three. Third, the main turbine is a published reference machine with
a documented part-load curve [@svendsen2023], whereas manufacturers publish
only full-load ratings for small units. A small unit alone could not carry
the 20 MW platform with 5 MW of reserve in calm periods, so it is meaningful
only as part of a mixed fleet.

Process behaviour is represented by steady-state operating points with ramp
limits; transient process dynamics are outside the scope. The model is
written in Python with NeqSim for thermodynamics and process simulation
[@neqsim] and Pyomo with the HiGHS solver for optimisation
[@bynum2021; @huangfu2018]. Every parameter is stored in a single
configuration file with its unit and source; 29 of 101 parameters are marked
as assumptions because no published value could be found (Table S1). An
automated test suite checks each model component against hand calculations
and published values.

> **Fig. 1.** The platform power system. Supply (left) and topside consumers
> coloured by flexibility class (middle) are connected to one AC bus. The
> scheduler sets the production rate $f_p$, the injection rate $f_{wi}$ and
> the GT commitment every hour.

### 2.2 Wind farm power

Hourly eastward and northward wind components at 100 m above sea level for
2023 were taken from the ERA5 reanalysis [@hersbach2020] at the grid point
nearest the site. Wind speed was extrapolated to the 150 m hub height with a
power law,

$$ v_{hub} = v_{100}\left(\frac{z_{hub}}{z_{100}}\right)^{\alpha}, \qquad \alpha = 0.11, $$

the exponent recommended for near-neutral conditions at sea [@hsu1994].
Turbine power was interpolated on the power curve of the IEA 15 MW offshore
reference turbine [@gaertner2020], with cut-in at 3 m/s, rated power from
10.7 m/s and cut-out at 25 m/s. The base-case farm of two turbines (30 MW)
is of the same order as the 32 MW farm of the LEOGO platform
[@svendsen2023]. Wake losses (5 %), electrical losses (2 %) and availability
(95 %) give a combined factor of 0.884, so the farm delivers at most
26.5 MW. Hourly resolution does not resolve wind variations within the hour;
these are covered by the spinning reserve (Section 2.6).

### 2.3 Gas turbines and emissions

The GTs follow the LEOGO reference turbine [@svendsen2023]: 21.8 MW rated
electric power and 3.5 MW minimum stable load (16 % of rating). Fuel input
is linear in electric output, a Willans line,

$$ Q_{g,t} = \frac{P_{rated}}{\eta_{rated}}\left(a\,u_{g,t} + (1-a)\frac{P_{g,t}}{P_{rated}}\right), $$

where $u_{g,t}$ is 1 when the unit runs. The rated efficiency
$\eta_{rated} = 0.347$ and no-load fuel fraction $a = 0.184$ follow from the
LEOGO fuel coefficients. A running GT thus burns 18.4 % of its full-load
fuel before it delivers any power, which is why low-load operation is
costly: efficiency falls from 34.7 % at full load to 29.3 % at half load and
17.7 % at minimum load, and the CO2 emitted per MWh of electricity rises from
623 kg to 737 kg and 1,220 kg (Fig. S2). A fraction $\phi = 0.5$ of the fuel
energy not converted to power is recovered as process heat.

The lower heating value of the fuel gas (38.96 MJ/Sm³) was computed with
NeqSim to ISO 6976 [@iso6976] from a generic North Sea fuel gas
composition. CO2 emissions use the Norwegian standard factor of
2.34 kg/Sm³ [@svendsen2023]. A carbon balance of the assumed composition
gives 2.27 kg/Sm³, and the factor reported for the Gullfaks field centre lies
between 2.32 and 2.40 kg/Sm³ (Section 3.5).

### 2.4 Process model and demand map

The topside process was modelled in NeqSim with the Peng–Robinson equation
of state for hydrocarbons and the CPA equation of state for water. CPA
reproduces the density of liquid water, and therefore pump power, more
accurately than a cubic equation without association terms. The flowsheet
comprises:

* four-stage separation at 70 / 29 / 7.2 / 1.8 bara [@nguyen2013], with the
  last stage within the 1.7–2.8 bar found on four real North Sea platforms
  [@voldsund2014];
* three recompression stages lifting the gas from each separator to the
  pressure of the previous one, each followed by a cooler to 30 °C and a
  scrubber;
* gas export compression from 70 to 180 bara, which agrees with the 179 bar
  reported for a real platform [@voldsund2014];
* oil export pumping to 50 bara;
* water injection pumps from 7 to 250 bara;
* seawater lift pumps that supply cooling water (10 K temperature rise) and
  make-up water for injection, with seawater properties from
  [@sharqawy2010];
* a fixed utility load of 3.5 MW and a process heat demand of 3 MW.

Compressor isentropic efficiency (0.75), pump efficiencies, the injection
pressure and the utility load follow LEOGO [@svendsen2023]. The design point
is 15,000 Sm³/d of oil with a gas–oil ratio of 179 Sm³/Sm³ (2.68 MSm³/d of
gas export), a water cut of 40 % (10,000 m³/d of produced water) and
25,000 m³/d of water injection capacity. The resulting electric demand is
20.3 MW at full injection (Table 1). At the injection target of 85 % of
capacity (Section 2.5) the demand is 18.8 MW.

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
flow, so a simple flow-scaled power curve would make every consumer
perfectly flexible. Real equipment is not. Each consumer is therefore
represented by $n$ identical parallel trains, of which the smallest number
that can carry the flow is running, and by a minimum flow per train,
$f_{min}$, below which the train recycles. For a flow fraction $f$ the
power is

$$ P(f) = P_{design}\,\frac{n_{run}}{n}\,\max\!\left(\frac{f\,n}{n_{run}},\, f_{min}\right), \qquad n_{run} = \left\lceil f\,n \right\rceil, $$

and zero when $f = 0$. Recycle represents anti-surge recycle for compressors
and minimum-flow recirculation for pumps. The minimum flow is 70 % for
compressors and 30 % for pumps. These values are assumptions; anti-surge
recycle rates between 4 % and 92 % of compressor flow have been reported on
real North Sea platforms [@voldsund2014], which shows that recycle is common
in practice.

### 2.5 Consumer classes and levers

Each consumer is assigned to one class and one operating lever (Fig. 1):

* **Must-run**: utilities and base load, never reduced.
* **Flexible (deferrable)**: water injection pumps. The lever is the
  injection rate $f_{wi}$. Postponed injection is not lost but must be
  caught up.
* **Sheddable**: recompression, gas export compression and oil export pumps.
  The lever is the production rate $f_p$; any reduction is lost production.
* **Mixed**: seawater lift pumps, whose cooling part follows $f_p$ and
  make-up part follows $f_{wi}$.

The power of each lever group is the sum of the train curves of its
consumers. It is a piecewise-linear function of the lever with steps where
a train starts at its minimum flow (Fig. 2), and it enters the scheduling
model through incremental binary variables, one per segment. Production can
be turned down to 50 % of design and changed by at most 10 % of design per
hour, which represents the speed at which well chokes and the separation
process can be adjusted. Injection can vary between 0 and 100 % of pump
capacity, by at most 34 % per hour, about one pump started or stopped.

The average injection must meet a voidage-replacement target, set here to
85 % of capacity. This is modelled as a virtual storage: postponing
injection builds a deficit, measured in hours of full-rate injection,

$$ D_t = D_{t-1} + \left(f_{wi}^{target} - f_{wi,t}\right)\Delta t, \qquad 0 \le D_t \le D_{max}, $$

with $\Delta t = 1$ h and $D_{max} = 72$ h. The lower bound prevents
injection from being brought forward, which the reservoir may not tolerate
either. The upper bound represents how much injection the reservoir
tolerates being postponed. It depends on the reservoir and is uncertain, so
it is varied from 0 to 168 h in the sensitivity analysis.

### 2.6 Scheduling model

The schedule is found with a mixed-integer linear program over each window
of hours $T$. The objective minimises the operating cost in NOK,

$$ \min \sum_{t \in T} \Big[ (c_{gas} + c_{CO2}\,e_{CO2}) \sum_{g} \frac{Q_{g,t}}{LHV} + c_{prod}\,(1 - f_{p,t}) + c_{start} \sum_{g} s_{g,t} + c_{pen}\,(P^{u}_t + R^{u}_t) \Big]\Delta t , $$

where $c_{gas} = 4.19$ NOK/Sm³ is the value of fuel gas, which could
otherwise be sold, $c_{CO2} = 2.0$ NOK/kg is the Norwegian target for the
total CO2 price in 2030 [@klimaplan2021], $e_{CO2}$ is the emission factor,
$c_{prod}$ is the hourly value of design production (oil at 4,190 NOK/Sm³
and gas at the gas price) and $c_{start} = 2,000$ NOK per GT start
[@svendsen2023]. Unserved energy $P^{u}_t$ and missing reserve $R^{u}_t$ are
allowed only at a penalty $c_{pen} = 10^6$ NOK/MWh to keep every window
feasible; in all reported runs they are below 0.03 MWh/yr.

The main constraints are:

$$ \sum_{g} P_{g,t} + P^{w}_t + P^{dis}_t + P^{u}_t = P^{dem}_t(f_{p,t}, f_{wi,t}) + P^{h}_t + P^{ch}_t, $$

$$ P^{w}_t + P^{c}_t = P^{avail}_t, $$

$$ \phi \sum_{g} \left(Q_{g,t} - P_{g,t}\right) + \eta_h P^{h}_t \ge H, $$

$$ P_{min}\,u_{g,t} \le P_{g,t} \le P_{rated}\,u_{g,t}, \qquad s_{g,t} \ge u_{g,t} - u_{g,t-1}, $$

$$ \sum_{g} \left(P_{rated}\,u_{g,t} - P_{g,t}\right) + P^{res}_t + R^{u}_t \ge R, \qquad \sum_{g} u_{g,t} \ge 1, $$

$$ E_t = E_{t-1} + \left(\eta_c P^{ch}_t - P^{dis}_t/\eta_d\right)\Delta t, $$

together with the deficit balance of Section 2.5, the ramp limits on
$f_{p,t}$ and $f_{wi,t}$, and the piecewise-linear demand $P^{dem}_t$ of the
lever groups. The first equation is the power balance and the second splits
the available wind into used and curtailed power. The heat balance requires
recovered exhaust heat plus electric heating, with heater efficiency
$\eta_h = 0.99$, to cover the heat demand $H = 3$ MW. The reserve
requirement $R = 5$ MW follows LEOGO [@svendsen2023]. A battery contributes
reserve $P^{res}_t$ only up to its unused discharge power and only if its
stored energy can sustain that power for 30 min. The round-trip efficiency
of the battery is 0.9. At least one GT must be online because the wind
turbines are grid-following and a synchronous machine is needed for
frequency and voltage control; this assumption is varied in the
sensitivity analysis.

The year is solved as 52 rolling one-week windows, each with an uncommitted
24 h look-ahead, so that each window ends with a realistic state for the
next. At the end of each look-ahead horizon the injection deficit may not
exceed, and the battery energy may not fall below, their values at the
start of the window, which prevents the optimiser from emptying the virtual
or real storage at the end of a window. Each window of 192 h has about 6,900
variables, of which 1,344 are binary, and 6,900 constraints, and HiGHS
solves it to within 0.5 % of the proven optimum. A full case-year takes 2–3 min on a
laptop-class processor.

Because fuel is linear in power, the split of load between identical
running GTs does not change total fuel, and the solver's split between them
is arbitrary. GT load is therefore reported as shared in proportion to
rating, as with droop control in real operation, and an hour counts as a
low-load hour for a unit when this shared load is below 50 % of rating.

### 2.7 Sensitivity analysis and validation

Cases 2–4 were rerun with one input changed at a time:

* wind farm size (1–4 turbines, 15–60 MW);
* CO2 price (0.5–3.0 NOK/kg) and gas price (2–8 NOK/Sm³);
* battery size (up to 8 MW / 16 MWh);
* injection deficit limit (0, 24, 72 and 168 h);
* minimum number of GTs online (1 or 0, with an 8 MW / 8 MWh battery that
  must then provide the reserve);
* GT fleet: three main units; two main units and one small unit, a Solar
  Turbines Mars 100 rated 11.35 MW with 32.9 % ISO efficiency
  [@solar_mars100] and the same relative part-load curve as the main units;
  or the three main units with one small unit added;
* an operating practice that keeps two GTs online whatever the wind, as
  some operators require for redundancy.

The results were compared with independent values:

* **platform power:** three real North Sea oil platforms
  [@voldsund2013; @voldsund2014], six modelled platforms [@nguyen2013], the
  Johan Castberg development plan [@castberg2017], and the average demand
  implied by Hywind Tampen [@equinor2023];
* **wind capacity factor:** Hywind Tampen [@equinor2023; @nowind2025];
* **CO2 avoided per MWh of wind:** Hywind Tampen [@equinor2023];
* **water injection specific energy:** LEOGO [@svendsen2023];
* **CO2 intensity:** the Norwegian shelf [@offshorenorge2024] and
  non-electrified hubs [@westwood2022];
* **field data** for the Gullfaks, Snorre and Statfjord field centres,
  2021–2024: CO2 to air, fuel gas and diesel use from Norskeutslipp
  [@norskeutslipp] and net production from the Norwegian Offshore
  Directorate [@sodir_factpages], summed over the fields processed at each
  centre.

The model components were verified by automated tests before the case
runs. The water injection pump power from NeqSim matches a hand calculation
of hydraulic power, the fuel model reproduces the LEOGO fuel coefficients,
and the piecewise-linear lever curves used by the scheduler match the
process model at every breakpoint. For the scheduler, the tests check on
short synthetic wind series that the power and heat balances close in every
hour, that the consumer limits and ramp rates are respected, that the fuel
reported equals the GT model applied to the scheduled loads, that a zero
deficit limit reproduces fixed injection, and that neither flexibility nor
a battery ever increases fuel use compared with fixed demand.

The CO2 avoided per MWh of wind is computed as the difference in annual CO2
between case 1 and a wind case, divided by the wind energy used in that
case. For the field data, the system boundary was checked by comparing the
reported oil volumes of the fields assigned to each centre with the
centre's processing; they agree within 2 %. A single published value counts
as agreeing when the model is within ±20 %, and a published range when the
model lies inside it.

## 3 Results

### 3.1 Demand map and wind resource

Water injection is the largest consumer (9.2 MW, 45 % of the design
demand) and the only large deferrable one (Table 1, Fig. 2). Stopping
injection at full production lowers the demand from 20.3 MW to 10.7 MW, a
swing of 9.6 MW that costs no production as long as the injection is caught
up. The sheddable consumers tied to production account for 7.2 MW and the
must-run base load for 3.5 MW. Both lever curves are far from proportional.
The injection lever jumps to 0.9 MW as soon as one pump runs, because the
pump recycles below 30 % of its flow, and rises linearly from there. The
production lever has a step just above 50 % rate, where the second export
compressor train must start at its surge limit and adds 0.75 MW. Reducing
production from 100 % to 50 % therefore saves only 3.2 MW, a third of what
the injection lever offers.

> **Fig. 2.** Demand map. Left: electric power at design by consumer,
> coloured by flexibility class. Right: power of the production (sheddable)
> and injection (flexible) levers against lever position.

ERA5 gives a mean wind speed of 9.4 m/s at 100 m and 9.8 m/s at hub height,
and a capacity factor of 50.9 % for the 30 MW farm in 2023 (Fig. S1). Output
is seasonal, with monthly capacity factors of 63–68 % in January and
February and 36–37 % from June to August. The farm delivers its maximum of
26.5 MW in 40 % of the hours and nothing in 9.6 % of the hours, mainly calm
periods, and available wind power exceeds the design demand of 20.3 MW in
4,017 h. The farm can therefore cover the whole platform for long periods,
but it also leaves frequent and sometimes long gaps that the GTs must fill.

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

With GTs only (case 1), two turbines run in every hour to carry the 18.8 MW
average load and the 5 MW reserve, each at about 43 % load. The platform
burns 54.6 MSm³ of fuel gas and emits 127.7 kt CO2 per year (Table 2,
Fig. 3), and all 17,520 GT unit-hours are low-load hours. This illustrates
the reserve problem of off-grid platforms: even without wind, the platform
operates its turbines far from their best efficiency.

A 30 MW wind farm with fixed demand (case 2) halves the emissions to
64.7 kt (−49.4 %). Wind covers 54 % of the electricity demand, and one GT
suffices in 7,058 h. Because demand cannot follow the wind, 44.5 GWh, or
33 % of the available wind energy, is curtailed, and the mean load of the
running GTs falls to 32 % of rating. A second GT is still needed in 1,702 h,
and it is started 149 times.

Flexible scheduling (case 3) reduces CO2 by a further 7.1 kt/yr, 11.0 %
relative to case 2, to 57.6 kt, without any loss of production. Fuel use
falls by the same 11 %. GT running hours fall from 10,462 to 8,790 unit-h,
the low-load unit-hours by 34 % and the GT starts from 149 to 6. Wind covers
57.6 % of the demand, curtailment falls by 13 % to 38.8 GWh, and the mean
load of the running GTs rises to 37 %. The combined fuel value and CO2 cost
falls by 27 MNOK/yr, of which 12.8 MNOK is the value of the fuel saved.

A 4 MW / 4 MWh battery (case 4) adds only 0.4 kt (−0.7 % relative to
case 3). It removes the remaining starts and the last hours with a second
GT, but its annual throughput is only 0.8 GWh. With one GT always online it
cannot remove the main remaining loss, one turbine idling near minimum load
whenever the wind covers the demand, and the low-load unit-hours even rise
slightly (5,928 to 6,235).

> **Fig. 3.** Annual CO2, fuel gas, GT hours below 50 % load and lost
> production for cases 1–4.

### 3.3 How flexible scheduling saves fuel

The saving comes almost entirely from avoiding a second GT. With fixed
demand, a second turbine must start whenever the wind drops and one GT
cannot carry the load while holding 5 MW in reserve, that is, whenever the
wind supplies less than about 2 MW at the average demand of 18.8 MW. Each
such hour costs the no-load fuel of a whole extra turbine, 18.4 % of its
full-load fuel. In case 3 the optimiser postpones water injection in
exactly these hours, so a second GT runs in only 30 h of the year instead
of 1,702 (Fig. 4, Fig. 5). The 1,672 avoided hours account for most of the
3.0 MSm³ of fuel saved.

> **Fig. 4.** Week 29 (16–22 July 2023), the week with the median fuel
> saving. Top and middle: power supplied by GTs and wind with fixed (case 2)
> and flexible (case 3) demand. Bottom: production and injection rates.

> **Fig. 5.** Duration curves of GT load per running unit (left; shaded:
> below 50 %) and of the number of GTs running (right).

The example week in Fig. 4, the week with the median fuel saving, shows the
pattern. Whenever the wind drops, injection is cut, sometimes to zero, and
the demand follows the wind; when the wind returns, injection runs at full
rate to catch up. Over the year, injection follows the available wind
(Fig. 6). Its mean rises from 59 % of capacity in the calmest hours to
98–99 % when more than 16 MW of wind is available, with a correlation
coefficient of 0.61 between injection rate and available wind. Injection is
below its 85 % target in 2,597 h, stopped completely in 178 h and above the
target in 6,048 h, and over the year it averages 84.9 % of capacity, so the
voidage target is met.

The deficit remains small compared with the limit. It averages 7.5 h of
full-rate injection, never exceeds 25.2 h and is below 24 h in all but a few
hours, well within the 72 h allowed. At the end of the year 6.3 h of
injection remain to be caught up, which corresponds to less than 1 % of the
annual saving. The short duration of the deficits reflects the mechanism:
the hours in which a second GT would be needed occur in spells of a few
hours to about a day, between periods of sufficient wind.

Production is never reduced in any case. One hour at 50 % rate would lose
oil and gas worth about 1.5 MNOK, while the fuel and CO2 saved in that hour
are worth a few thousand NOK, so the optimiser always prefers to defer
injection. The saving from flexibility is present in every month, between
0.42 and 0.76 kt (Fig. S3). It is largest in June, December and July, months
in which the wind often falls just below the demand.

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

Table 3 and Fig. 7 show which inputs matter.

**Prices do not change the schedule.** Across CO2 prices of 0.5–3 NOK/kg and
gas prices of 2–8 NOK/Sm³, emissions change by less than 0.1 %. Prices change
the cost of every option in proportion, so the cheapest schedule stays the
cheapest. The injection schedule is driven by fuel savings that are
worthwhile at any price, and production is never shed, because its value is
two orders of magnitude higher than the fuel saved.

**A small deferral capacity is enough.** With no deferral allowed, case 3 is
identical to case 2 (64.7 kt). A deficit limit of 24 h already gives the
full saving, with 12 GT starts instead of 6, and allowing 168 h changes
nothing more. Even a conservative reservoir constraint would therefore
capture the benefit.

**Wind farm size has diminishing returns.** Doubling the farm from 30 to
60 MW lowers case 3 emissions only from 57.6 to 50.9 kt, while curtailment
grows from 39 to 160 GWh, because one GT must stay online and the platform
cannot absorb more wind in windy hours. The value of flexibility (case 2
minus case 3) is largest for the base-case farm (7.1 kt) and smaller for a
15 MW farm (5.5 kt), where the wind seldom covers the demand, and for a
45–60 MW farm (6.6–6.9 kt).

**Batteries add little on their own.** The largest battery tested
(8 MW / 16 MWh) reduces case 3 emissions by 1.1 kt, or 2 %, as long as one
GT must remain online.

**The minimum number of GTs online dominates.** If an 8 MW / 8 MWh battery
can provide the reserve and grid stability so that all GTs may stop,
emissions fall to 38.7 kt, 32 % below the same case with one GT online. The
GTs then run only 3,809 unit-h, wind covers a much larger share of the
demand with only 11 GWh curtailed, and 15 GWh of heat is supplied by the
electric heater when no GT runs. The price is 184 GT starts per year.

**Operating practice matters as much as hardware.** If two GTs are kept
online whatever the wind, emissions rise to 90.7 kt in case 2 and 87.7 kt in
case 3. Flexibility then saves only 3.1 kt, because its main mechanism,
avoiding the second GT, is no longer available; the remaining saving comes
from lower curtailment.

**A smaller third GT** lowers case 3 emissions by 3.4 % to 55.6 kt, but needs
121 starts per year, and the data for the small unit are not verified.

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
values (Table 4, Fig. 8). The platform power lies within the processing-plant
power of three real oil platforms and within 20 % of the other references.
It is below the range of the six modelled platforms of Nguyen et al.
[@nguyen2013], in which gas compression alone takes 42–56 % of a 22.6–31.1 MW
demand, compared with 28 % of 20.3 MW here. The ERA5 capacity factor is within 2 % of the 49.8 % expected for
Hywind Tampen, although that farm uses smaller floating turbines.

The strongest check is the CO2 avoided per MWh of wind, because it tests the
wind, the part-load fuel model, the CO2 factor and the scheduling together.
When the model keeps two GTs online and only lowers their load, as assumed
in the Hywind Tampen estimate, it avoids 0.51 t/MWh against the published
0.52 t/MWh. When a GT may stop in windy hours, as in case 2, it avoids
0.71 t/MWh, because the no-load fuel of the stopped unit is saved as well.
The difference shows how much of the benefit of wind depends on operating
practice rather than on the wind farm itself.

The field data support the fuel and emission model (Fig. 8, right). The
Gullfaks field centre emits 2.32–2.40 kg CO2 per Sm³ of fuel gas in
2021–2024, consistent with the 2.34 kg/Sm³ used here. After Hywind Tampen
started supplying power, fuel gas use fell by 30 % at Gullfaks (2021–2023)
and by 11 % at Snorre (2021–2024), and Snorre's diesel use fell from 15.6 kt
to about 3 kt. At Statfjord, which receives no wind power, fuel use was
unchanged. Production also declined over the period, so not all of the
reduction can be attributed to the wind farm. The model's CO2 intensity is
lower than the shelf average and the field values (9–14 kg/boe at Gullfaks
and Snorre, 55–78 kg/boe at late-life Statfjord), as expected from the
system boundary: the model covers only power generation on an efficient
platform at plateau rate, whereas the field values include flaring, diesel,
gas re-injection compression and the lower production of mature fields.
The like-for-like checks, the fuel gas factor and the CO2 avoided per MWh,
agree, which indicates that the difference stems from the boundary and not
from the power system model.

> **Fig. 8.** Left: model results divided by published benchmarks (1 =
> equal; shaded: ±20 %; grey bars: published ranges). Right: CO2 intensity of
> the Gullfaks, Snorre and Statfjord field centres (grey: GT-powered; teal:
> receiving Hywind Tampen power) with the model case 1 value (dashed).

## 4 Discussion

### 4.1 Why load flexibility works

The value of flexible demand on a wind-powered platform lies in unit
commitment, not in energy shifting. A GT that runs at low load to provide
reserve burns a large share of its full-load fuel, so the expensive hours
are those in which the wind is just too weak for one turbine to carry the
load with reserve. Deferring water injection in these hours keeps the
second turbine off. This explains three results of Section 3. Most of the
saving comes from 1,672 avoided hours with two GTs online. A deficit
capacity of about one day captures it all, because these hours occur in
short spells between windy periods. And the saving largely disappears when
operating rules keep two GTs online anyway.

Energy shifting alone, by contrast, achieves little. Curtailment falls by
only 13 %, because one GT must stay online and a 30 MW wind farm often
exceeds what the platform can use even with injection at full rate. This
also explains why the value of flexibility does not grow with the wind farm:
a larger farm covers the demand more often, which reduces the number of
hours in which a second GT is needed, while the additional wind in windy
hours cannot be used. The flexibility is most valuable when the wind farm is
of the same order as the platform demand, as in the base case and at Hywind
Tampen.

The same reasoning explains why a battery adds little in case 4. With at
least one GT online, the battery cannot remove the main remaining loss, one
turbine idling near minimum load. A large saving appears only when the
battery, or grid-forming wind turbines, can take over the role of the last
running GT (38.7 kt, −32 %). This agrees with the finding that a battery
providing reserve lets platform GTs be switched off [@svendsen2022]. The
present results add that process flexibility gives much of the same benefit
without new equipment, and that both measures act on the same mechanism:
they reduce the number of GTs that must be online.

### 4.2 Comparison with earlier studies

Studies of wind-powered platforms usually report the benefit of wind with
fixed demand, which corresponds to case 2. The present results show that
this case underestimates what the same wind farm can achieve: with fixed
demand, the emissions of the wind-powered platform are 12 % higher than when
the same platform schedules its flexible loads. The CO2 avoided per MWh of wind, a
common metric for wind integration, rises from 0.71 t/MWh in case 2 to
0.74 t/MWh in case 3 and is 0.51 t/MWh if two GTs are kept online. Published
values for different platforms are therefore comparable only if the
operating practice of the GTs is stated.

Riboldi and Nord [@riboldi2018] found that the economic case for integrating
wind depends on gas and CO2 prices. Demand flexibility behaves differently:
it requires no investment in power generation, its schedule does not depend
on prices, and the fuel it saves is worth about 1,800 NOK per tonne of CO2
avoided at the base-case gas price alone. It therefore pays for itself
without a carbon price, which makes it attractive also in regions where
emissions are not priced. The value of the fuel saved is of the same order
as the abatement cost threshold used for power-from-shore projects in
Norway [@sodir2020], but power from shore requires large investments while
the flexibility studied here requires mainly a change in operation.

Demand-side management in onshore industry is usually motivated by
electricity prices [@zhang_grossmann2016; @golmohamadi2022]. On an off-grid
platform, the value of moving a load comes instead from the discrete
decisions of the platform's own power plant: whether a GT must be started
or can be stopped. This makes the value of flexibility strongly
state-dependent, and it is why an hourly unit commitment model, rather than
a model of energy shifting alone, is needed to estimate it.

### 4.3 Practical implementation

Three implications follow for operators. First, the flexibility already
exists on most oil platforms with water injection and can be used without
new equipment. It does, however, require the power management system to
coordinate injection with the GTs and the wind forecast, which today are
usually controlled separately. Second, the reservoir requirement is modest:
about 24 h of injection deferral, averaging 7.5 h, is small compared with the
time scale of reservoir pressure support, which is managed on the basis of
cumulative voidage replacement over months. It should nevertheless be
confirmed with reservoir engineers for each field, because some reservoirs,
for example those close to the bubble point, may be sensitive to short
pressure drops. Third, the schedule changes the duty of the injection pumps.
In case 3 the number of running injection pumps changes about 720 times per
year, or about two pump starts per day. The model does not penalise pump
starts; a start cost or a minimum run time for the pumps could be added at
little cost to the saving, since the deficit limit is rarely active.

The result does not depend on the carbon price, because the fuel saved has
value on its own. Operating practice, and in particular how many GTs must be
online and what counts as reserve, has a larger effect on emissions than any
price or the battery size. Rules that keep two GTs online for redundancy
increase emissions by 40–50 % compared with the optimised schedules, and
they remove most of the value of flexibility. Such rules are set for good
reasons of safety and regularity, but the results suggest that they deserve
the same attention as the choice of wind farm when emissions are to be
reduced, and that technologies that can provide reserve and stability
without a running GT, such as grid-forming batteries, are the next step after
demand flexibility.

The approach can be transferred to other installations. A platform benefits
most from load flexibility when it has a large deferrable consumer, when its
average demand lies close to the capacity of one GT minus the reserve, and
when its wind supply is of the same order as its demand. Gas compression on
gas export platforms, electric heating, and the regeneration of glycol or
other process chemicals are candidates for deferrable loads on other types
of installation, provided that buffer storage, such as line pack or tank
volume, is available.

### 4.4 Robustness of the conclusions

The size of the saving depends on assumptions that were not all varied, and
it is useful to consider how they act through the mechanism identified
above. The decisive quantity is the number of hours in which, with fixed
demand, the platform needs one GT more than its load requires. This number
grows with the reserve requirement, with the average demand relative to
the capacity of one GT, and with the time the wind spends just below the
demand. A larger reserve than the 5 MW used here, or a platform whose
demand lies closer to the rating of one GT, would therefore increase the
value of flexibility, while a platform with much spare GT capacity, or a
wind farm much larger than the demand, would reduce it, as the wind farm
sensitivity confirms.

The flexible load itself matters less than its size suggests. Injection is
deferred by stopping whole pumps, so the assumed minimum flow of the pumps
affects the cost of running one pump at low rate but hardly the saving,
which comes from the hours in which injection is cut. A lower injection
target would leave more room above the target for catching up, and a higher
target less; at the extreme of a 100 % target, deferred injection could
never be caught up and flexibility would be lost. The heat balance was never
binding in the base cases: the electric heater was not used, because the
waste heat of the running GT always covered the 3 MW demand. Platforms with
a higher heat demand, or with heat supplied by the GTs that are to be
stopped, would see a smaller saving unless the heat can also be scheduled.

The conclusion that production should never be shed is robust. The value of
lost oil and gas exceeds the value of the fuel saved by about two orders of
magnitude, so even large changes in prices or efficiencies would not change
it.

### 4.5 Limitations and future work

The platform is generic. Its fluid composition, minimum-flow limits,
injection target and deficit limit are assumptions, although the
sensitivity analysis shows that the result is robust to the deficit limit,
the prices and the battery size. The process is represented by steady
states: transient compressor behaviour, the start-up times of pumps and GTs
beyond the start cost, and the reservoir response to deferred injection are
not modelled. The scheduler has perfect foresight of wind within each week,
so the savings are an upper bound for real operation with forecast errors;
because the deficit limit is rarely active, a forecast-based schedule with a
safety margin on the deficit is expected to retain most of the saving. The
analysis covers one weather year and a single platform without power import
or export. Investment and operating costs of the wind farm and battery are
outside the scope, so the results show the operational value of flexibility
but not the cost of CO2 abatement of the whole system. Finally, the small GT
in the fleet sensitivity is given the same relative part-load curve as the
main units, because its manufacturer publishes only the full-load rating.

Future work should test the approach with wind forecast errors and several
weather years, add pump start costs and a reservoir model for the injection
deficit, and apply it to real platform data. Combining load flexibility with
grid-forming storage, and evaluating the investment cost of the whole system,
would show how far an off-grid platform can be decarbonised before power from
shore becomes necessary.

## 5 Conclusions

This paper mapped the electric demand of a generic North Sea oil platform
from a process model, classified the consumers by flexibility, and scheduled
them together with the gas turbines and a wind farm for one year at hourly
resolution. The main conclusions are:

1. A 30 MW wind farm halves the CO2 emissions of the 20 MW platform (−49 %)
   with fixed demand.
2. Scheduling flexible topside consumers reduces emissions by a further 11 %
   (7.1 kt/yr) without lost production. GT low-load hours fall by 34 % and
   GT starts nearly disappear.
3. Water injection provides all of the useful flexibility; shedding
   production is never worthwhile. A deferral capacity of about 24 h of
   injection is enough.
4. The saving comes from avoiding a second running gas turbine, not from
   shifting energy. It therefore depends on operating practice: keeping two
   GTs online removes most of it, while allowing all GTs to stop, with a
   battery providing reserve, would reduce emissions by a further third.
5. Carbon price, gas price and battery size alone have little effect, and
   the fuel saved pays for the measure without a carbon price.
6. The model reproduces the CO2 avoided per MWh of wind reported for Hywind
   Tampen within 2 %, and the fuel gas emission factor observed at Gullfaks.

Load flexibility is thus a low-cost first step for reducing emissions from
wind-powered platforms, which can be implemented on existing installations
and which complements storage and grid-forming technologies.

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
