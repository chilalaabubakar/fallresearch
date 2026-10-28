# Scheduling flexible topside loads to reduce gas turbine emissions on a wind-powered offshore oil platform

[Author 1]^a^, [Author 2]^b^

^a^ *[Affiliation a]*

^b^ *[Affiliation b]*

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
wind data, with postponed water injection as a virtual storage. For a 20.3 MW platform with a 30 MW wind farm, wind
with fixed demand reduces annual CO2 emissions by 49 %. Flexible scheduling
cuts them by a further 11 % (7.2 kt/yr) without lost production,
mainly because it avoids running a second gas turbine: the hours with two
turbines online fall from 1,702 to 28. Over ten weather years the benefit
is 10.5–11.7 %. About 24 h of deferrable injection captures it, and a
small added gas turbine is complementary. Operating
rules that keep two gas turbines online remove most of the gain. The model
reproduces Hywind Tampen's reported CO2 avoided per MWh of wind within 2 %.

**Keywords:** offshore oil and gas platform; offshore wind; demand-side
flexibility; gas turbine part load; unit commitment; water injection

## 1 Introduction

Petroleum activities account for about a quarter of Norway's greenhouse gas
emissions [@offshorenorge2024]. Most of these emissions come from gas
turbines (GTs) that generate power and drive compressors offshore
[@norskpetroleum_emissions]. Power from shore removes them where a cable is
feasible; the electrification projects planned in 2020 had abatement costs
below NOK 1,500 per tonne of CO2 [@sodir2020], and the CO2 cost paid by
operators has since risen from about NOK 860 to NOK 1,860 per tonne
[@sodir_pfs]. Many installations are too far from shore or too small for a
cable, however, or depend on onshore grid capacity that is needed elsewhere.
Operators have judged the alternatives to power from shore to be more costly
or less effective [@sodir_pfs]. For those installations, the efficiency of
the offshore power plant still decides the emissions.

Wind power connected directly to the platform grid has been studied for more
than a decade. He et al. [@he2010] assessed the potential of integrating wind
power with offshore oil and gas platforms, and Marvik et al. [@marvik2013]
studied the transient stability of a cluster of North Sea installations with
an integrated wind farm. Riboldi and Nord [@riboldi2018] optimised an
offshore combined-cycle plant with a wind farm and found that its economics
depend on gas and CO2 prices. Hywind Tampen, an 88 MW floating wind farm that
supplies five platforms, has operated since 2023; it is expected to cover
about 35 % of their electricity demand and to avoid about 200 kt of CO2 per
year [@equinor2023].

The fuel saved per MWh of wind is smaller on such a platform than on a large
grid. The wind turbines follow the grid frequency rather than set it, so at
least one GT must stay online, and the running GTs must hold enough spare
capacity to cover the loss of wind or of a generator. When wind supplies part
of the demand, the GTs run at part load. That is where they are least
efficient: the LEOGO reference turbine falls from about 35 % electric
efficiency at full load to below 20 % near its minimum stable load
[@svendsen2023]. Exergy analyses of North Sea platforms attribute 62–65 % of
the exergy destroyed on a platform to the gas turbines [@nguyen2013].

Operational optimisation recovers part of this loss. The open-source tool
Oogeso optimises GT commitment, wind use and storage; with a battery
providing reserve, one turbine can be switched off and the others run at
higher load [@svendsen2022]. The LEOGO reference platform gives a common data
set for such studies [@svendsen2023]. Zhang et al. [@zhang2022] plan
investments in offshore energy hubs under emission targets, and Khan et al.
[@khan2022] show that relaxing GT operating constraints lets a platform grid
absorb more wind. In all of these, the platform load is an input. Svendsen
[@svendsen2022] names demand-side flexibility as a way to reduce the need for
storage but leaves it for future work.

Onshore, moving industrial loads in time is an established subject. Zhang and
Grossmann [@zhang_grossmann2016] review how energy-intensive production can
be scheduled around electricity prices, and Golmohamadi [@golmohamadi2022]
reviews demand-side management in heavy industries such as cement and
aluminium. These studies respond to price signals in a large grid. An
off-grid platform has no price signal. Moving a load is worth something only
through the platform's own power plant, and the value is highly non-linear:
it depends on whether the change lets a GT stop, or avoids starting one.

Platform loads are not fixed either. Water injection is one of the largest
consumers; on the platforms studied by Nguyen et al. [@nguyen2013] only gas
compression used more power. Injection can be postponed for hours as long as
the cumulative volume meets the reservoir's needs, because reservoir pressure
responds slowly. Production can also be cut, but the lost revenue is large.
Utilities and safety systems must run at all times. How much of this
flexibility is usable depends on details that a fixed load profile hides:
parallel trains, minimum-flow recycle on compressors and pumps, ramp limits,
and the need to catch up postponed injection.

This paper asks how much fuel and CO2 a wind-powered oil platform can save by
scheduling these loads, which consumers provide the saving and through which
mechanism, and which assumptions decide its size. It contributes:

1. a demand map of a generic North Sea oil platform from a steady-state
   process model, with the power of each consumer as a function of its
   operating lever, including train switching and minimum-flow recycle;
2. a classification of the consumers as must-run, flexible (deferrable) or
   sheddable, in which postponed water injection is a virtual storage that
   must be emptied again;
3. a mixed-integer linear program that schedules the flexible consumers
   together with GT commitment, wind use and an optional battery, hour by hour
   over full years;
4. results for four cases and ten weather years, with sensitivity analysis,
   validation against Hywind Tampen and field data, and economic indicators.

Section 2 describes the platform, models and cases, and Section 3 the
results. Section 4 discusses the mechanism, its practical use and the
limitations, and Section 5 concludes. The code, input data and all
parameters with their sources are openly available (see Data availability).

## 2 Methods

### 2.1 System and cases

The study models the electric power system of a generic oil platform in the
northern North Sea (Tampen area, 61.0° N, 2.0° E) for the year 2023 at
hourly resolution (Fig. 1), with cases 1–4 repeated for the weather years
2014–2022. The platform produces oil with associated gas,
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
are an example [@equinor2023]. Second, load flexibility is an operational
measure, whereas a new GT is an investment; keeping the fleet fixed isolates
the value of flexibility. The effect of a smaller unit is quantified
separately in the sensitivity analysis with an 11.35 MW Solar Turbines
Mars 100 [@solar_mars100], either replacing one main unit or added to the
three, with both fixed and flexible demand. Third, the main turbine is a published reference machine with
a documented part-load curve [@svendsen2023], whereas manufacturers publish
only full-load ratings for small units. A small unit alone could not carry
the 20 MW platform with 5 MW of reserve in calm periods, so it is meaningful
only as part of a mixed fleet.

Process behaviour is represented by steady-state operating points with ramp
limits; transient process dynamics are outside the scope. The model is
written in Python with NeqSim for thermodynamics and process simulation
[@neqsim] and Pyomo with the HiGHS solver for optimisation
[@bynum2021; @huangfu2018]. Every parameter is stored in a single
configuration file with its unit and source; 31 of 109 parameters are marked
as assumptions because no published value could be found (Table S1). An
automated test suite checks each model component against hand calculations
and published values.

> **Fig. 1.** The platform power system. Supply (left) and topside consumers
> coloured by flexibility class (middle) are connected to one AC bus. The
> scheduler sets the production rate $f_p$, the injection rate $f_{wi}$ and
> the GT commitment every hour.

### 2.2 Wind farm power

Hourly eastward and northward wind components at 100 m above sea level for
2014–2023 were taken from the ERA5 reanalysis [@hersbach2020] at the grid point
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
LEOGO fuel coefficients. A running GT burns 18.4 % of its full-load
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
perfectly flexible. Real equipment is not, so each consumer is
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
is arbitrary. GT load is reported instead as shared in proportion to
rating, as with droop control in real operation, and an hour counts as a
low-load hour for a unit when this shared load is below 50 % of rating.

### 2.7 Weather years, sensitivity analysis and validation

To test whether 2023 is representative, cases 1–4 were also run for each
weather year from 2014 to 2022 with ERA5 data at the same grid point and all
other inputs unchanged. The injection deficit limit was varied for 2016 and
2017 as well, the years in which the deficit reached its highest values.

For the base year 2023, cases 2–4 were rerun with one input changed at a
time:

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

### 2.8 Economic indicators

Two indicators are derived from the annual results, in real NOK. For the
wind farm, whose investment can be estimated, the abatement cost is

$$ c_{abate} = \frac{I\,\mathrm{CRF}(r, n) + C_{O\&M} - \Delta C_{fuel}}{\Delta m_{CO2}}, \qquad \mathrm{CRF}(r,n) = \frac{r}{1-(1+r)^{-n}}, $$

where $I$ is the investment, $C_{O\&M}$ the annual operation and maintenance
cost, $\Delta C_{fuel}$ the annual value of the fuel saved and
$\Delta m_{CO2}$ the CO2 avoided per year. The CO2 price is not counted as a
saving, because the abatement cost is what is compared with the CO2 price.
The investment is scaled from Hywind Tampen, about NOK 7.4 billion for 88 MW
before public support [@equinor2023], which gives 84 MNOK/MW for a
first-of-a-kind floating farm. Operation and maintenance cost 35–97 EUR/kW
per year, the range between the cheapest and the most expensive repair
strategy modelled for floating wind farms [@dighe2024]. The real discount
rate is 7 %, with 4 % as an alternative, the two rates used in Norwegian
abatement-cost analyses of power from shore [@npd_abatement], and the economic
life is 20 years. For flexibility, the battery and a small GT, whose
investment on an existing platform could not be estimated from published
data, the break-even investment is given instead: the present value over 20
years of the annual saving, for the fuel saved alone and for fuel plus CO2
cost.

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
4,017 h. The farm can cover the whole platform for long periods,
but it also leaves frequent and sometimes long gaps that the GTs must fill.

### 3.2 Comparison of the four cases

**Table 2.** Annual results for the four cases (2023).

| | 1 GTs only | 2 Wind, fixed | 3 Wind, flexible | 4 Flexible + battery |
|---|---|---|---|---|
| CO2 [kt/yr] | 127.7 | 64.7 | 57.5 | 57.2 |
| Reduction vs case 1 | – | 49.4 % | 55.0 % | 55.2 % |
| Fuel gas [MSm³/yr] | 54.6 | 27.6 | 24.6 | 24.4 |
| GT running [unit-h/yr] | 17,520 | 10,462 | 8,788 | 8,760 |
| GT below 50 % load [unit-h/yr] | 17,520 | 9,005 | 5,932 | 6,242 |
| GT starts [–/yr] | 0 | 149 | 3 | 0 |
| Wind used [GWh/yr] | 0 | 89.3 | 95.1 | 95.7 |
| Wind curtailed [GWh/yr] | 0 | 44.5 | 38.7 | 38.1 |
| Lost production | 0 | 0 | 0 | 0 |
| Fuel value + CO2 cost [MNOK/yr] | 484.0 | 245.1 | 217.9 | 216.7 |

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

Flexible scheduling (case 3) reduces CO2 by a further 7.2 kt/yr, 11.1 %
relative to case 2, to 57.5 kt, without any loss of production. Fuel use
falls by the same 11 %. GT running hours fall from 10,462 to 8,788 unit-h,
the low-load unit-hours by 34 % and the GT starts from 149 to 3. Wind covers
57.6 % of the demand, curtailment falls by 13 % to 38.7 GWh, and the mean
load of the running GTs rises to 36 %. The combined fuel value and CO2 cost
falls by 27 MNOK/yr, of which 12.9 MNOK is the value of the fuel saved.

A 4 MW / 4 MWh battery (case 4) adds only 0.3 kt (−0.6 % relative to
case 3). It removes the remaining starts and the last hours with a second
GT, but its annual throughput is only 0.8 GWh. With one GT always online it
cannot remove the main remaining loss, one turbine idling near minimum load
whenever the wind covers the demand, and the low-load unit-hours even rise
slightly (5,932 to 6,242).

> **Fig. 3.** Annual CO2, fuel gas, GT hours below 50 % load and lost
> production for cases 1–4.

### 3.3 How flexible scheduling saves fuel

The saving comes almost entirely from avoiding a second GT. With fixed
demand, a second turbine must start whenever the wind drops and one GT
cannot carry the load while holding 5 MW in reserve, that is, whenever the
wind supplies less than about 2 MW at the average demand of 18.8 MW. Each
such hour costs the no-load fuel of a whole extra turbine, 18.4 % of its
full-load fuel. In case 3 the optimiser postpones water injection in
exactly these hours, so a second GT runs in only 28 h of the year instead
of 1,702 (Fig. 4, Fig. 5). The 1,674 avoided hours account for most of the
3.0 MSm³ of fuel saved.

> **Fig. 4.** Week 3 (15–21 January 2023), the week with the median fuel
> saving. Top and middle: power supplied by GTs and wind with fixed (case 2)
> and flexible (case 3) demand. Bottom: production and injection rates.

> **Fig. 5.** Duration curves of GT load per running unit (left; shaded:
> below 50 %) and of the number of GTs running (right).

The example week in Fig. 4, the week with the median fuel saving, shows the
pattern. Whenever the wind drops, injection is cut, sometimes to zero, and
the demand follows the wind; when the wind returns, injection runs at full
rate to catch up. Over the year, injection follows the available wind
(Fig. 6). Its mean rises from 57 % of capacity in the calmest hours to
98–100 % when more than 16 MW of wind is available, with a correlation
coefficient of 0.61 between injection rate and available wind. Injection is
below its 85 % target in 2,563 h, stopped completely in 187 h and above the
target in 6,129 h, and over the year it averages 84.9 % of capacity, so the
voidage target is met.

The deficit remains small compared with the limit. It averages 9.0 h of
full-rate injection, never exceeds 27.5 h and is above 24 h in only 149 h of
the year, well within the 72 h allowed. At the end of the year 8.2 h of
injection remain to be caught up, which corresponds to less than 1 % of the
annual saving. The short duration of the deficits reflects the mechanism:
the hours in which a second GT would be needed occur in spells of a few
hours to about a day, between periods of sufficient wind.

Production is never reduced in any case. One hour at 50 % rate would lose
oil and gas worth about 1.5 MNOK, while the fuel and CO2 saved in that hour
are worth a few thousand NOK, so the optimiser always prefers to defer
injection. The saving from flexibility is present in every month, between
0.43 and 0.77 kt (Fig. S3). It is largest in June, December and July, months
in which the wind often falls just below the demand.

> **Fig. 6.** Left: water injection rate against available wind in case 3
> (mean and 10–90 % range of hours). Right: distribution of the injection
> deficit (dashed: 72 h limit).

### 3.4 Sensitivity analysis

**Table 3.** Annual CO2 [kt/yr] in the sensitivity runs.

| Varied input | Values | Case 2 | Case 3 | Case 4 |
|---|---|---|---|---|
| Wind farm size [turbines] | 1 / 2 / 3 / 4 | 77.6 / 64.7 / 60.2 / 57.6 | 71.9 / 57.5 / 53.4 / 50.9 | |
| CO2 price [NOK/kg] | 0.5 / 1 / 2 / 3 | | 57.5 / 57.5 / 57.5 / 57.6 | |
| Gas price [NOK/Sm³] | 2 / 4.19 / 8 | | 57.5 / 57.5 / 57.5 | |
| Battery [MW / MWh] | 0 / 2/2 / 4/4 / 8/8 / 8/16 | | | 57.5 / 57.3 / 57.2 / 56.9 / 56.4 |
| Injection deficit limit [h] | 0 / 24 / 72 / 168 | | 64.7 / 57.5 / 57.5 / 57.5 | |
| Min. GTs online (8 MW battery) | 1 / 0 | | | 56.9 / 38.7 |
| GT fleet | 3 main / 2 main + 1 small / 3 main + 1 small | 64.7 / 53.9 / 53.9 | 57.5 / 47.8 / 47.7 | |
| Keep two GTs online | | 90.7 | 87.7 | |

Table 3 and Fig. 7 show which inputs matter, and several do not. Across CO2
prices of 0.5–3 NOK/kg and gas prices of 2–8 NOK/Sm³, emissions change by less
than 0.1 %. Prices scale the cost of every option alike, so the cheapest
schedule stays the cheapest. Deferring injection saves fuel at any price, and
shedding production never pays: lost oil and gas are worth about a hundred
times more than the fuel saved.

The deferral capacity needed is small. With no deferral allowed, case 3 is
identical to case 2 (64.7 kt). A limit of 24 h already gives the full saving,
with 5 GT starts instead of 3; 168 h changes nothing. A conservative reservoir
constraint would still capture the benefit.

A larger wind farm helps less than its size suggests. Doubling the farm from
30 to 60 MW lowers case 3 emissions only from 57.5 to 50.9 kt, while
curtailment grows from 39 to 160 GWh: one GT must stay online, and in windy
hours the platform cannot use more wind. The value of flexibility (case 2
minus case 3) peaks at the base-case size (7.2 kt). It is 5.6 kt for a 15 MW
farm, where the wind seldom covers the demand, and 6.7–6.8 kt for 45–60 MW.
Batteries add little as long as one GT must stay online. The largest one
tested, 8 MW / 16 MWh, saves 1.1 kt (2 %).

Two assumptions about GT operation matter more than any of these. If an
8 MW / 8 MWh battery could provide reserve and grid stability, so that all
GTs may stop, emissions would fall to 38.7 kt, 32 % below the same case with
one GT online. The GTs would then run only 3,798 unit-h and start 184 times a
year; only 11 GWh of wind would be curtailed, and the electric heater would
supply 15 GWh of heat in hours with no GT running. The opposite rule, two GTs
online whatever the wind, raises emissions to 90.7 kt in case 2 and 87.7 kt
in case 3. Flexibility then saves only 3.1 kt, all of it from lower
curtailment, because there is no second GT left to avoid.

The fleet itself matters too. Replacing one main unit by a Solar Mars 100
(11.35 MW) lowers emissions from 64.7 to 53.9 kt with fixed demand (−17 %)
and from 57.5 to 47.8 kt with flexible demand. In windy hours the small unit
runs alone. Its no-load fuel is about half that of a main unit, and it can
carry up to 6.35 MW while holding the 5 MW reserve. Flexibility still saves
6.1 kt (11.3 %) with the small unit installed, and it cuts the small unit's
starts from 465 to 262 per year. Combined, the small unit and flexibility
reduce emissions by 26 % relative to case 2. Adding the small unit to all
three main units instead gives 47.7 kt; the third main unit is never used.

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

### 3.6 Economic indicators

**Table 5.** Economic indicators (real NOK, 20 years; abatement cost range
from the O&M range of floating wind).

| Measure | CO2 avoided [kt/yr] | Fuel value saved [MNOK/yr] | Abatement cost [NOK/t], 7 % / 4 % | Break-even investment [MNOK], fuel / fuel + CO2 |
|---|---|---|---|---|
| Wind farm, fixed demand (case 2 vs 1) | 63.0 | 112.8 | 2,180–2,519 / 1,347–1,686 | – |
| Wind farm with flexibility (case 3 vs 1) | 70.2 | 125.7 | 1,774–2,078 / 1,026–1,330 | – |
| Flexibility (case 3 vs 2) | 7.2 | 12.9 | −1,799 before implementation cost | 137 / 288 |
| Battery 4 MW / 4 MWh (case 4 vs 3) | 0.3 | 0.5 | −1,562 before battery cost | 5 / 13 |
| Small GT replacing one main GT (flexible) | 9.7 | 17.4 | −1,786 before GT cost | 184 / 391 |

With an investment of 2.5 billion NOK for 30 MW, the wind farm with fixed
demand avoids CO2 at 2,180–2,519 NOK/t at a 7 % discount rate and
1,347–1,686 NOK/t at 4 % (Table 5). This is of the same order as the
abatement cost of the power-from-shore projects most recently approved on
the Norwegian shelf, just under 2,000 NOK/t [@sodir2025], and close to the
2,000 NOK/t CO2 price targeted for 2030 [@klimaplan2021]. Scheduling the
flexible loads lowers the abatement cost of the same wind farm by about
400 NOK/t, to 1,774–2,078 NOK/t at 7 %, because it avoids 11 % more CO2 and
saves 11 % more fuel for the same investment.

Flexibility on its own saves money before any implementation cost: the fuel
saved is worth about 1,800 NOK per tonne of CO2 avoided. An operator could
spend up to 137 MNOK on control systems and process changes and still break
even on the fuel saved alone, or 288 MNOK when the avoided CO2 cost is
included. A 4 MW / 4 MWh battery breaks even only below 5–13 MNOK, which is
low for an offshore installation of that size. A small GT that replaces one
main GT breaks even below 184–391 MNOK, before its additional maintenance and
its 262 starts per year are accounted for.

### 3.7 Weather years

**Table 6.** Results for ten weather years (ERA5, 2014–2023).

| | Mean | Range | 2023 |
|---|---|---|---|
| Wind capacity factor | 54.2 % | 50.3–59.8 % | 50.9 % |
| CO2 reduction, case 2 vs 1 | 51.8 % | 48.5–55.6 % | 49.4 % |
| CO2 reduction, case 3 vs 1 | 57.1 % | 54.5–60.3 % | 55.0 % |
| Flexibility benefit, case 2 − 3 | 6.8 kt (11.0 %) | 5.9–7.7 kt (10.5–11.7 %) | 7.2 kt (11.1 %) |
| Hours with two GTs, case 2 / case 3 | | 1,082–1,889 / 4–66 | 1,702 / 28 |
| Battery benefit, case 3 − 4 | 0.35 kt | 0.25–0.42 kt | 0.32 kt |
| Maximum injection deficit | | 25.8–59.3 h | 27.5 h |

The weather year changes the benefit of wind more than the benefit of
flexibility (Table 6, Fig. 9). Over the ten years the capacity factor of the
wind farm ranges from 50.3 % to 59.8 %, and 2023 is one of the calmer years.
The reduction with fixed demand (case 2) ranges from 48.5 % to 55.6 %. The
additional saving from flexibility is remarkably stable at 10.5–11.7 % of
case 2 emissions, or 5.9–7.7 kt/yr, and averages 11.0 %, almost exactly the
2023 value. In absolute terms it is largest in the calm years 2016, 2021 and
2023, in which a second GT is needed most often with fixed demand, and
smallest in the windy year 2022. Flexibility removes 96–100 % of the hours
with two GTs online in every year, and no year loses production or leaves
demand unmet.

The injection deficit varies more between years than the saving does. Its
maximum ranges from 26 to 59 h, below the 72 h limit in every year, and up
to 28 h remain to be caught up at the end of a year. In 2016 and 2017, the
years with the largest deficits, a limit of 24 h still captures 98 % of the
saving obtained with 72 h (58.4 against 58.3 kt in 2016, 52.7 against
52.6 kt in 2017). The conclusion that about one day of deferral is enough
holds for all weather years tested.

> **Fig. 9.** Flexibility benefit (case 2 − case 3, bars) and wind capacity
> factor (line) for the weather years 2014–2023.

## 4 Discussion

### 4.1 Why load flexibility works

Flexible demand saves fuel through unit commitment, not through energy
shifting. A GT held at low load for reserve still burns a large share of its
full-load fuel, so the costly hours are those in which the wind is just too
weak for one turbine to carry the load with 5 MW in reserve. Deferring
injection in those hours keeps the second turbine off. Three results of
Section 3 follow from this. Most of the saving comes from the 1,674 avoided
hours with two GTs online. About one day of deficit capacity captures almost
all of it, since these hours come in short spells between windy periods. And
the saving largely disappears under rules that keep two GTs online anyway.

Shifting energy alone does little. Curtailment falls by only 13 %: one GT
must stay online, and a 30 MW farm often produces more than the platform can
use even with injection at full rate. The same reason explains why the value
of flexibility does not grow with the wind farm. A larger farm covers the
demand more often, so a second GT is needed in fewer hours, and the extra
wind in windy hours cannot be absorbed. Flexibility is worth most when the
wind farm is of the same order as the platform demand, as in the base case
and at Hywind Tampen.

The small effect of the battery in case 4 has the same cause. With one GT
always online, a battery cannot remove the main remaining loss, a turbine
idling near minimum load. The large saving (38.7 kt, −32 %) appears only
when the battery, or grid-forming wind turbines, can replace the last running
GT. Svendsen [@svendsen2022] found the same for a battery that provides
reserve. What the present results add is that process flexibility gives much
of this benefit without new equipment, because both measures reduce the
number of GTs that must be online.

A small GT works on a different part of the loss. It does not reduce the
number of running units; it reduces the no-load fuel of the one that runs.
That is why its saving adds almost fully to that of flexibility (Section 3.4).
A retrofit could proceed in stages: use the flexibility of the existing
process first, at no investment, and consider replacing one main GT by a
smaller unit at its next major overhaul, if the small unit tolerates about
260 starts a year.

### 4.2 Comparison with earlier studies

Most studies of wind-powered platforms report the benefit of wind at fixed
demand, which is case 2 here. That understates what the same wind farm can
do: with fixed demand, emissions are 12 % higher than when the platform
schedules its flexible loads. The CO2 avoided per MWh of wind, the usual
metric for wind integration, is 0.71 t/MWh in case 2, 0.74 t/MWh in case 3,
and 0.51 t/MWh if two GTs are kept online. Values reported for different
platforms can only be compared if the GT operating practice behind them is
stated.

The economics also differ from those of wind. Riboldi and Nord
[@riboldi2018] found that integrating wind pays only with favourable gas and
CO2 prices. Flexibility needs no investment in power generation, its schedule
does not depend on prices, and the fuel it saves is worth about 1,800 NOK per
tonne of CO2 avoided at the base-case gas price alone. It pays without any
carbon price, which matters in regions where emissions are not priced. The
wind farm, by comparison, needs about 1,800–2,500 NOK/t at a 7 % discount
rate to break even, the same order as power from shore
[@sodir2020; @sodir2025]; flexibility lowers this by about 400 NOK/t.

The comparison with onshore demand response is less direct than it may seem.
Industrial studies respond to electricity prices
[@zhang_grossmann2016; @golmohamadi2022]. On an off-grid platform the value of
a load shift comes from discrete decisions of the platform's own power
plant, whether a GT must start or can stop. The value therefore depends on
the state of the system hour by hour, and a model of energy shifting alone,
without unit commitment, would miss most of it.

### 4.3 Practical implementation

For operators, the first point is that this flexibility already exists on
most oil platforms with water injection. Using it needs no new equipment, but
it does need a power management system that coordinates injection with the
GTs and a wind forecast; today these are usually controlled separately.

The reservoir requirement is modest. About 24 h of deferral, averaging 9.0 h,
is short compared with the months over which voidage replacement is normally
managed. It still has to be confirmed for each field. A reservoir close to
its bubble point, for example, may not accept even short pressure drops.

The schedule also changes the duty of the injection pumps. In case 3 the
number of running pumps changes about 730 times a year, roughly two starts
per day, and the model does not penalise this. A start cost or a minimum run
time would probably cost little of the saving, because the deficit limit is
rarely reached; this has not been tested.

Operating practice deserves at least as much attention as hardware. How many
GTs must be online, and what counts as reserve, affects emissions more than
any price or the battery size. Rules that keep two GTs online for redundancy
raise emissions by 40 % with fixed demand and by 53 % with flexible demand,
and they remove most of the value of flexibility. Such rules exist for good
reasons of safety and regularity. Changing them requires a technical case,
for instance grid-forming batteries that can provide reserve and stability
without a running GT, and that is the logical next step after demand
flexibility.

The approach should transfer to other installations, with caveats. A
platform gains most when it has a large deferrable consumer, an average
demand close to the capacity of one GT minus the reserve, and a wind supply
of the same order as its demand. On other installation types, gas export
compression, electric heating and the regeneration of glycol or other
process chemicals could be deferrable, but only where buffer storage such as
line pack or tank volume exists.

### 4.4 Robustness of the conclusions

Not every assumption was varied, so it helps to trace how the untested ones
act through the mechanism above. What decides the saving is the number of
hours in which, at fixed demand, the platform runs one GT more than its load
requires. That number rises with the reserve requirement, with the demand
relative to the capacity of one GT, and with the time the wind spends just
below the demand. A reserve larger than 5 MW, or a platform whose demand is
closer to one GT's rating, should make flexibility more valuable. Much spare
GT capacity, or a wind farm far larger than the demand, should make it less
valuable; the wind farm sensitivity shows the latter.

The flexible load matters less than its size suggests. Injection is cut by
stopping whole pumps, so the assumed minimum pump flow changes the cost of
running one pump at low rate but hardly the saving. The injection target
matters more. A lower target leaves more room for catching up; at a 100 %
target, deferred injection could never be caught up and the flexibility
would vanish. The heat balance never bound in the base cases, since the waste
heat of the running GT always covered the 3 MW demand. A platform with a
larger heat demand, or one that relies on the heat of the GTs to be stopped,
would save less unless its heat can be scheduled too.

That production should never be shed is the most robust result. Lost oil and
gas are worth about a hundred times more than the fuel saved; no plausible
change in prices or efficiencies reverses that.

### 4.5 Limitations and future work

The platform is generic: fluid composition, minimum-flow limits, injection
target and deficit limit are assumed, although the result is insensitive to
the deficit limit, the prices and the battery size. The process is
represented by steady states. Transient compressor behaviour, start-up times
of pumps and GTs beyond a start cost, and the reservoir response to deferred
injection are not modelled. The GT part-load curve is a Willans line from
LEOGO; a real machine's curve, including its emissions at very low load, may
differ.

The scheduler knows the wind a week ahead, so the savings are an upper bound.
Because the deficit limit is rarely reached, a forecast-based schedule that
keeps a margin on the deficit should retain most of them, but that remains
to be shown. The ten weather years cover one site and one platform, without
power import or export. The economic indicators rest on the cost of a single
first-of-a-kind floating wind farm and leave out the cost of implementing
flexibility, the battery or the small GT, for which only break-even values
are given. The small GT uses the main units' relative part-load curve,
because its manufacturer publishes only the full-load rating.

The next steps are concrete. Rolling schedules with forecast errors would
show how much of the saving survives without perfect foresight. Pump start
costs and a simple reservoir pressure model would test the injection
schedule against operational limits. Data from a platform with wind supply,
such as those served by Hywind Tampen, would allow the model to be
calibrated. Finally, combining load flexibility with grid-forming storage and
the investment cost of the whole system would show how far an off-grid
platform can be decarbonised before power from shore is needed.

## 5 Conclusions

The electric demand of a generic North Sea oil platform was mapped from a
process model, the consumers were classified by flexibility, and the
flexible ones were scheduled together with the gas turbines and a 30 MW wind
farm, hour by hour, for ten weather years. The main conclusions are:

1. With fixed demand, the wind farm halves the CO2 emissions of the 20 MW
   platform (−49 %).
2. Scheduling the flexible consumers cuts emissions by a further 11 %
   (7.2 kt/yr), without lost production. Across the ten weather years the
   saving stays between 10.5 % and 11.7 %. GT low-load hours fall by 34 %,
   and GT starts nearly disappear.
3. All of the useful flexibility comes from water injection. Shedding
   production never pays, and about 24 h of deferral is enough.
4. The saving comes from avoiding a second running GT, not from shifting
   energy. Rules that keep two GTs online remove most of it; allowing all GTs
   to stop, with a battery for reserve, would cut emissions by a further
   third.
5. A small GT (11.35 MW) replacing one main unit saves another 17 %, and
   flexibility still saves 11 % with it installed.
6. Prices and battery size alone change little. Flexibility pays for itself
   from fuel savings, breaks even for an implementation cost of up to
   137 MNOK, and lowers the abatement cost of the wind farm from 2,180–2,519
   to 1,774–2,078 NOK/t.
7. The model reproduces the CO2 avoided per MWh of wind reported for Hywind
   Tampen within 2 %, and the fuel gas emission factor observed at Gullfaks.

Three questions remain open: how much of the saving survives realistic wind
forecasts, what limits pump starts and reservoir pressure place on the
injection schedule, and whether grid-forming storage can remove the last
running GT safely.

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

## List of Acronyms

| Acronym | Meaning |
|---|---|
| GT | gas turbine |
| LHV | lower heating value |
| MILP | mixed-integer linear program |

## Funding

[Funding.]

## Acknowledgements

This work contains modified Copernicus Climate Change Service information (2014–2023).

## Declaration of generative AI use

During the preparation of this work the author(s) used [tool name] in order to [purpose]. After using this tool, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the published article.

## Data and Code Availability

The model code, configuration with all parameters and sources, and the processed results are available at [repository URL]. ERA5 data are available from the Copernicus Climate Change Service.

## Conflict of interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## CRediT authorship contribution statement

[Author 1]: Conceptualization, Methodology, Software, Formal analysis, Writing – original draft. [Author 2]: Supervision, Writing – review & editing.

## References

{{REFERENCES}}
