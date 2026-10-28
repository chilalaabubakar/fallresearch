# Flexible top-side load scheduling on a wind-powered offshore oil platform: effects on gas turbine fuel use and CO~2~ emissions

Abubakar Juma Chilala^a,b^

^a^ *College of Engineering, Carnegie Mellon University Africa, Carnegie Mellon University, Pittsburgh, PA, 15213, USA*

^b^

Corresponding author: achilala@andrew.cmu.edu

## Abstract

Gas turbines on offshore oil and gas platforms are a major source of CO~2~
emissions, and the fuel saved by wind power integrated into these off-grid
systems is smaller than expected, since the turbines must remain online at
inefficient part load to provide reserve. Studies of wind-powered platforms
usually consider the topside load as fixed. Here, the electric demand of a
generic North Sea oil platform was mapped with a steady-state process model,
and each consumer was classified as must-run, flexible or sheddable. A
mixed-integer linear program was then used to schedule production rate, water
injection rate, gas turbine commitment, wind use and an optional battery for
one year at hourly resolution with ERA5 wind data, with postponed water
injection represented as a virtual storage. For a 20.3 MW platform supplied by
a 30 MW wind farm, wind with fixed demand reduces the annual CO~2~ emissions
by 49 %. Flexible scheduling cuts them by a further 11 % (7.2 kt/yr) without
lost production, mostly because a second gas turbine is avoided: the hours
with two turbines online fall from 1,702 to 28. Over ten weather years it
ranges from 10.5 to 11.7 %. About 24 h of deferrable injection captures it,
and a small added gas turbine is complementary, whereas operating rules that
keep two gas turbines online remove most of the gain. With two gas turbines
online, as the operator's estimate assumes, the model matches the CO~2~
avoided per MWh of wind expected for Hywind Tampen.

**Keywords:** offshore oil and gas platform; offshore wind; demand-side
flexibility; gas turbine part load; unit commitment; water injection

## 1 Introduction

The oil and gas extraction sector accounts for about a quarter of the
greenhouse gas emissions of Norway [@offshorenorge2024]. Most of these
emissions originate from the gas turbines (GTs) that generate power and drive
compressors on the offshore installations [@norskpetroleum_emissions]. Power
from shore eliminates them where a cable connection is feasible: the
electrification projects planned in 2020 had abatement costs below NOK 1,500
per tonne of CO~2~ [@sodir2020], and the CO~2~ cost paid by the operators has
since increased from about NOK 860 to NOK 1,860 per tonne [@sodir_pfs].
However, many installations are located too far from shore or are too small to
justify a cable, or they depend on onshore grid capacity that is required by
other users, and the operators have judged the alternatives to power from
shore to be more costly or less effective [@sodir_pfs]. For these
installations, the emissions are still determined by the efficiency of the
offshore power plant.

The integration of wind power into the platform grid has been studied for more
than a decade. He et al. [@he2010] assessed the potential of integrating wind
power with offshore oil and gas platforms, and Marvik et al. [@marvik2013]
studied the transient stability of a cluster of North Sea installations
connected to a wind farm. Riboldi and Nord [@riboldi2018] optimized an
offshore combined-cycle plant integrating a wind farm and found that its
economic performance depends on the gas and CO~2~ prices. The first large
application is Hywind Tampen, an 88 MW floating wind farm that supplies five
platforms and has been in operation since 2023; it is expected to cover about
35 % of their electricity demand and to avoid about 200 kt of CO~2~ per year
[@equinor2023].

The fuel saved per MWh of wind is, however, smaller on such a platform than in
a large grid. Since the wind turbines follow the grid frequency rather than
set it, at least one GT must remain online, and the running GTs must hold
sufficient spare capacity to cover the loss of the wind farm or of a
generator. When wind supplies part of the demand, the GTs therefore operate at
part load, where they are least efficient: the electric efficiency of the
LEOGO reference turbine decreases from about 35 % at full load to below 20 %
near its minimum stable load [@svendsen2023]. Exergy analyses of North Sea
platforms attribute 62–65 % of the exergy destroyed on a platform to the gas
turbines [@nguyen2013].

Part of this loss can be recovered by operational optimization. The
open-source tool Oogeso optimizes the GT commitment, the wind use and the
storage; with a battery providing reserve, one turbine can be switched off and
the remaining ones operated at higher load [@svendsen2022]. The LEOGO
reference platform provides a common data set for such studies
[@svendsen2023]. Zhang et al. [@zhang2022] planned investments in offshore
energy hubs under emission targets, and Khan et al. [@khan2022] showed that
relaxing the GT operating constraints allows a platform grid to absorb more
wind power. In all of these studies the platform load is an input. Svendsen
[@svendsen2022] pointed out demand-side flexibility as a means of reducing the
need for storage, but left it for future work.

In onshore industry, the shifting of loads in time is an established subject.
Zhang and Grossmann [@zhang_grossmann2016] reviewed how energy-intensive
production can be scheduled according to electricity prices, and Golmohamadi
[@golmohamadi2022] reviewed demand-side management in heavy industries such as
cement and aluminum production. These studies consider the response to price
signals in a large grid. An off-grid platform has no such price signal: the
value of moving a load arises only through the platform's own power plant, and
it is strongly non-linear, as it depends on whether the change allows a GT to
be stopped or avoids the start of one.

The platform loads are not fixed either. Water injection is one of the largest
consumers, and on the platforms studied by Nguyen et al. [@nguyen2013] only
gas compression required more power. Injection can be postponed for hours as
long as the cumulative volume meets the requirements of the reservoir, since
the reservoir pressure responds slowly. Production can also be reduced,
although at a large loss of revenue, whereas utilities and safety systems must
run at all times. The share of this flexibility that can actually be used
depends on details that a fixed load profile does not capture, such as
parallel trains, minimum-flow recycle on compressors and pumps, ramp limits
and the need to catch up postponed injection.

Water injection has already been proposed as a controllable load for
wind-powered platforms. Sanchez et al. [@sanchez2017] used variable-speed
injection pumps to smooth short-term wind power fluctuations and to damp
low-frequency oscillations of the platform grid, and Alves et al. [@alves2019]
combined such load management with energy storage to improve power quality.
The WIN WIN joint industry project found a stand-alone floating wind turbine
that drives water injection directly to be technically feasible [@dnvgl2016].
On the reservoir side, Nilsen et al. [@nilsen2025a; @nilsen2025b] optimized
the well controls of a field supplied by offshore wind, so that the power
demand follows the wind, and studied the trade-off between profit and
emissions. These studies address either the dynamics of the electrical system
over seconds to minutes or the response of the reservoir over months to years.
The hour-by-hour interaction between deferrable topside loads and the
commitment of the gas turbines, which determines how much fuel is actually
saved, has not been quantified over full years.

The goal of this study is to quantify this interaction: how much fuel and CO~2~
a wind-powered oil platform can save by scheduling its flexible loads, which
consumers provide the saving and through which mechanism, and which
assumptions determine its magnitude. To the authors' knowledge, it is the
first study that schedules deferrable topside loads together with gas turbine
unit commitment over full years at hourly resolution, with consumer power
curves derived from a process model. Four main steps were followed in this study:

1. development of a demand map of a generic North Sea oil platform with a
   steady-state process model, giving the power of each consumer as a function
   of its operating lever, including train switching and minimum-flow recycle;
2. classification of the consumers as must-run, flexible (deferrable) or
   sheddable, with postponed water injection represented as a virtual storage
   that must be emptied again;
3. formulation of a mixed-integer linear program that schedules the flexible
   consumers together with the GT commitment, the wind use and an optional
   battery, hour by hour over full years;
4. simulation of four cases and ten weather years, with sensitivity analysis,
   benchmark checks against Hywind Tampen and field data, and economic
   indicators.

The methodology and the models are described in Section 2. Section 3 reports
the results obtained for the four cases, which are discussed in Section 4.
Concluding remarks are outlined in Section 5. The code, the input data and all
parameters with their sources are openly available (see Data and Code
Availability).

## 2 Methods

### 2.1 System and cases

The electric power system of a generic oil platform in the northern North Sea
(Tampen area, 61.0° N, 2.0° E) was modeled for the year 2023 at hourly
resolution (Fig. 1), and Cases 1–4 were repeated for the weather years
2014–2022. The platform produces oil with associated gas, exports both and
injects water for pressure support. Power is supplied by three GTs and, in the
wind cases, by a nearby offshore wind farm of two turbines connected to the AC
system of the platform. Four cases were compared:

1. **GTs only**, fixed demand (baseline).
2. **Wind + GTs, fixed demand**: production and water injection at their
   design and target rates in every hour.
3. **Wind + GTs, flexible scheduling**: production and injection rates are
   decision variables.
4. **Case 3 + battery** of 4 MW / 4 MWh.

The platform keeps its three GTs in all cases, as a retrofit would; the
optimizer decides how many run in each hour. Case 2 corresponds to the
usual assumption in platform–wind studies, in which wind displaces GT power
but the load is unchanged. The difference between Cases 2 and 3 isolates
the value of demand flexibility, and Case 4 tests whether a small battery
adds to it.

The base case keeps the existing main turbines, as on the five platforms
supplied by Hywind Tampen [@equinor2023], for two reasons: load flexibility is
an operational measure, whereas a new GT is an investment, so a fixed fleet
isolates the value of flexibility; and the main turbine is a published
reference machine with a documented part-load curve [@svendsen2023]. A smaller
unit, an 11.35 MW Solar Turbines Mars 100 [@solar_mars100], is tested in the
sensitivity analysis, replacing one main unit or added to the three. Alone it
could not carry the 20 MW platform with 5 MW of reserve in calm periods.

Process behavior is represented by steady-state operating points with ramp
limits; transient process dynamics are outside the scope. The model is
written in Python with NeqSim for thermodynamics and process simulation
[@neqsim] and Pyomo with the HiGHS solver for optimization
[@bynum2021; @huangfu2018]. Every parameter is stored in a single
configuration file with its unit and source; 31 of 109 parameters are marked
as assumptions because no published value could be found (Table S1). 

> **Fig. 1.** The platform power system. Supply (left) and topside consumers
> colored by flexibility class (middle) are connected to one AC bus. The
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
17.7 % at minimum load, and the CO~2~ emitted per MWh of electricity rises from
623 kg to 737 kg and 1,220 kg (Fig. S2). A fraction $\phi = 0.5$ of the fuel
energy not converted to power is recovered as process heat.

The lower heating value of the fuel gas (38.96 MJ/Sm³) was computed with
NeqSim to ISO 6976 [@iso6976] from a generic North Sea fuel gas
composition. CO~2~ emissions use the Norwegian standard factor of
2.34 kg/Sm³ [@svendsen2023]. A carbon balance of the assumed composition
gives 2.27 kg/Sm³, and the factor reported for the Gullfaks field center lies
between 2.32 and 2.40 kg/Sm³ (Section 3.6).

### 2.4 Process model and demand map

The topside process was modeled in NeqSim with the Peng–Robinson equation
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
85 % of capacity. This is modeled as a virtual storage: postponing
injection builds a deficit, measured in hours of full-rate injection,

$$ D_t = D_{t-1} + \left(f_{wi}^{target} - f_{wi,t}\right)\Delta t, \qquad 0 \le D_t \le D_{max}, $$

with $\Delta t = 1$ h and $D_{max} = 72$ h. The lower bound prevents
injection from being brought forward, which the reservoir may not tolerate
either. The upper bound represents how much injection the reservoir
tolerates being postponed. It depends on the reservoir and is uncertain, so
it is varied from 0 to 168 h in the sensitivity analysis.

### 2.6 Scheduling model

The schedule is found with a mixed-integer linear program over each window
of hours $T$. The objective minimizes the operating cost in NOK,

$$ \min \sum_{t \in T} \Big[ (c_{gas} + c_{CO2}\,e_{CO2}) \sum_{g} \frac{Q_{g,t}}{LHV} + c_{prod}\,(1 - f_{p,t}) + c_{start} \sum_{g} s_{g,t} + c_{pen}\,(P^{u}_t + R^{u}_t) \Big]\Delta t , $$

where $c_{gas} = 4.19$ NOK/Sm³ is the value of fuel gas, which could
otherwise be sold, $c_{CO2} = 2.0$ NOK/kg is the Norwegian target for the
total CO~2~ price in 2030 [@klimaplan2021], $e_{CO2}$ is the emission factor,
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
start of the window, which prevents the optimizer from emptying the virtual
or real storage at the end of a window. Each window of 192 h has about 6,900
variables, of which 1,344 are binary, and 6,900 constraints, and HiGHS
solves it to within 0.5 % of the proven optimum. A full case-year takes 2–3 min on a
laptop-class processor.

Because fuel is linear in power, the split of load between identical
running GTs does not change total fuel, and the solver's split between them
is arbitrary. GT load is reported instead as shared in proportion to
rating, as with droop control in real operation, and an hour counts as a
low-load hour for a unit when this shared load is below 50 % of rating.

### 2.7 Weather years, sensitivity analysis and benchmark checks

To test whether 2023 is representative, Cases 1–4 were also run for each
weather year from 2014 to 2022 with ERA5 data at the same grid point and all
other inputs unchanged. The injection deficit limit was varied for 2016 and
2017 as well, the years in which the deficit reached its highest values.

For the base year 2023, Cases 2–4 were rerun with one input changed at a
time:

* wind farm size (1–4 turbines, 15–60 MW);
* CO~2~ price (0.5–3.0 NOK/kg) and gas price (2–8 NOK/Sm³);
* battery size (up to 8 MW / 16 MWh);
* injection deficit limit (0, 24, 72 and 168 h);
* minimum number of GTs online (1 or 0, with an 8 MW / 8 MWh battery that
  must then provide the reserve);
* GT fleet: three main units; two main units and one small unit, a Solar
  Turbines Mars 100 rated 11.35 MW with 32.9 % ISO efficiency
  [@solar_mars100] and the same relative part-load curve as the main units;
  or the three main units with one small unit added;
* an operating practice that keeps two GTs online whatever the wind, as
  some operators require for redundancy;
* GT minimum stable load (16, 30, 40 and 50 % of rating), since dry low-NOx
  combustors often cannot keep their emissions within limits far below about
  40–50 % load;
* a cost per injection pump start (0–20,000 NOK), with the number of running
  pumps $n_{run} = \lceil f_{wi}\, n \rceil$ of Section 2.4 as an integer
  variable;
* the reserve definition: a requirement that also covers 50 % or 100 % of the
  wind power used, $R_t = R + k\,P^{w}_t$, and running injection pumps counted
  as reserve because they can be tripped within seconds;
* the solver gap (0.1 % instead of 0.5 %), to check that the small battery
  effect is not an artefact of the solver tolerance.

To test how far the results carry over to other platforms, Cases 2 and 3 were
also run with every electric consumer scaled by 0.6–1.2 (mean demand 11.3–22.6
MW), combined with a spinning reserve of 3, 5, 7 and 9 MW, 28 platforms in
total. Finally, the assumption of perfect wind foresight within each window
was tested with a schedule that is re-planned every hour over the next 24 h.
Only the wind of the current hour is known; every later hour is assumed equal
to it (persistence forecast). The same hourly re-planning with the actual wind
isolates the effect of the forecast from that of the shorter horizon.

The results were compared with independent values:

* **platform power:** three real North Sea oil platforms
  [@voldsund2013; @voldsund2014], six modeled platforms [@nguyen2013], the
  Johan Castberg development plan [@castberg2017], and the average demand
  implied by Hywind Tampen [@equinor2023];
* **wind capacity factor:** Hywind Tampen [@equinor2023; @nowind2025];
* **CO~2~ avoided per MWh of wind:** Hywind Tampen [@equinor2023];
* **water injection specific energy:** LEOGO [@svendsen2023];
* **CO~2~ intensity:** the Norwegian shelf [@offshorenorge2024] and
  non-electrified hubs [@westwood2022];
* **field data** for the Gullfaks, Snorre and Statfjord field centers,
  2021–2024: CO~2~ to air, fuel gas and diesel use from Norskeutslipp
  [@norskeutslipp] and net production from the Norwegian Offshore
  Directorate [@sodir_factpages], summed over the fields processed at each
  center.

The model components were verified by automated tests against hand
calculations and published values (Supplementary material, S5).

The CO~2~ avoided per MWh of wind is computed as the difference in annual CO~2~
between Case 1 and a wind case, divided by the wind energy used in that
case. For the field data, the system boundary was checked by comparing the
reported oil volumes of the fields assigned to each center with the
center's processing; they agree within 2 %. A single published value counts
as agreeing when the model is within ±20 %, and a published range when the
model lies inside it.

### 2.8 Economic indicators

Two indicators are derived from the annual results, in real NOK. For the
wind farm, whose investment can be estimated, the abatement cost is

$$ c_{abate} = \frac{I\,\mathrm{CRF}(r, n) + C_{O\&M} - \Delta C_{fuel}}{\Delta m_{CO2}}, \qquad \mathrm{CRF}(r,n) = \frac{r}{1-(1+r)^{-n}}, $$

where $I$ is the investment, $C_{O\&M}$ the annual operation and maintenance
cost, $\Delta C_{fuel}$ the annual value of the fuel saved and
$\Delta m_{CO2}$ the CO~2~ avoided per year. The CO~2~ price is not counted as a
saving, because the abatement cost is what is compared with the CO~2~ price.
The investment is scaled from Hywind Tampen, about NOK 7.4 billion for 88 MW
before public support [@equinor2023], which gives 84 MNOK/MW for a
first-of-a-kind floating farm. Operation and maintenance cost 35–97 EUR/kW
per year, the range between the cheapest and the most expensive repair
strategy modeled for floating wind farms [@dighe2024]. The real discount
rate is 7 %, with 4 % as an alternative, the two rates used in Norwegian
abatement-cost analyses of power from shore [@npd_abatement], and the economic
life is 20 years. For flexibility, the battery and a small GT, whose
investment on an existing platform could not be estimated from published
data, the break-even investment is given instead: the present value over 20
years of the annual saving, for the fuel saved alone and for fuel plus CO~2~
cost.

## 3 Results

### 3.1 Demand map and wind resource

The process model was first used to obtain the electric power of each consumer
at the design point (Table 1) and its variation with the lever positions (Fig.
2). Water injection is the largest consumer, with 9.2 MW or 45 % of the design
demand, and the only large deferrable one. Stopping injection at full
production lowers the demand from 20.3 MW to 10.7 MW, a swing of 9.6 MW that
costs no production as long as the injection is caught up. The sheddable
consumers tied to production and the must-run base load account for 7.2 MW and
3.5 MW, respectively. Neither lever curve is proportional to the lever
position. The power of the injection lever jumps to 0.9 MW as soon as one pump
runs, since the pump recycles below 30 % of its flow, and increases linearly
from there. The production lever shows a step just above a rate of 50 %, where
the second export compressor train must start at its surge limit and adds 0.75
MW. Reducing production from 100 % to 50 % therefore saves only 3.2 MW, about
a third of the reduction offered by the injection lever.

> **Fig. 2.** Demand map. Left: electric power at design by consumer,
> colored by flexibility class. Right: power of the production (sheddable)
> and injection (flexible) levers against lever position.

The ERA5 data give a mean wind speed of 9.4 m/s at 100 m and 9.8 m/s at hub
height, and a capacity factor of 50.9 % for the 30 MW farm in 2023 (Fig. S1).
The output is seasonal, with monthly capacity factors of 63–68 % in January
and February and 36–37 % from June to August. The farm delivers its maximum of
26.5 MW in 40 % of the hours and nothing in 9.6 % of the hours, mainly during
calm periods, and the available wind power exceeds the design demand of 20.3
MW in 4,017 h. The farm can thus cover the whole platform demand for long
periods, but it also leaves frequent and sometimes long gaps that must be
filled by the GTs.

### 3.2 Comparison of the four cases

**Table 2.** Annual results for the four cases (2023).

| | 1 GTs only | 2 Wind, fixed | 3 Wind, flexible | 4 Flexible + battery |
|---|---|---|---|---|
| CO~2~ [kt/yr] | 127.7 | 64.7 | 57.5 | 57.2 |
| Reduction vs Case 1 | – | 49.4 % | 55.0 % | 55.2 % |
| Fuel gas [MSm³/yr] | 54.6 | 27.6 | 24.6 | 24.4 |
| GT running [unit-h/yr] | 17,520 | 10,462 | 8,788 | 8,760 |
| GT below 50 % load [unit-h/yr] | 17,520 | 9,005 | 5,932 | 6,242 |
| GT starts [–/yr] | 0 | 149 | 3 | 0 |
| Wind used [GWh/yr] | 0 | 89.3 | 95.1 | 95.7 |
| Wind curtailed [GWh/yr] | 0 | 44.5 | 38.7 | 38.1 |
| Lost production | 0 | 0 | 0 | 0 |
| Fuel value + CO~2~ cost [MNOK/yr] | 484.0 | 245.1 | 217.9 | 216.7 |

The annual results of the four cases are summarized in Table 2 and Fig. 3.
With GTs only (Case 1), two turbines run in every hour to carry the average
load of 18.8 MW and the 5 MW reserve, each at about 43 % load, so all 17,520
GT unit-hours are low-load hours. Even without wind, the reserve keeps the
turbines far from their best efficiency.

A 30 MW wind farm with fixed demand (Case 2) halves the emissions, to 64.7 kt
(−49.4 %). Wind covers 54 % of the demand, and one GT is sufficient in 7,058
h. Since the demand cannot follow the wind, 33 % of the available wind energy
is curtailed, and a second GT is still required in 1,702 h.

Flexible scheduling (Case 3) reduces the CO~2~ emissions by a further 7.2
kt/yr, or 11.1 % relative to Case 2, without any loss of production. The GT
running hours fall from 10,462 to 8,788 unit-h, the low-load unit-hours by 34
% and the GT starts from 149 to 3, and the curtailment decreases by 13 %. The
combined fuel value and CO~2~ cost is reduced by 27 MNOK/yr, of which 12.9
MNOK is the value of the fuel saved.

The 4 MW / 4 MWh battery (Case 4) adds only 0.3 kt (0.6 %). It removes the
last starts and hours with a second GT, but with one GT always online it
cannot remove the main remaining loss, one turbine idling near minimum load
whenever the wind covers the demand.

> **Fig. 3.** Annual CO~2~, fuel gas, GT hours below 50 % load and lost
> production for Cases 1–4.

### 3.3 How flexible scheduling saves fuel

The saving is obtained by deferring water injection out of the hours in which
a second GT would otherwise be needed. With fixed demand, a second turbine
must be started whenever the wind drops and one GT cannot carry the load while
holding 5 MW in reserve, i.e. whenever the wind supplies less than about 2 MW
at the average demand of 18.8 MW. Each such hour costs the no-load fuel of a
whole additional turbine, which amounts to 18.4 % of its full-load fuel. In
Case 3 the optimizer postpones water injection in exactly these hours, so that
a second GT runs in only 28 h of the year instead of 1,702 h (Fig. 4, Fig. 5).
Since fuel is linear in GT power, the saving splits exactly into two parts
(Table 3). The 1,674 avoided GT unit-hours, at a no-load fuel of 1,068 Sm³ per
unit-hour, save 1.79 MSm³ (58 % of the 3.07 MSm³ saved). The injection that is
moved out of these hours, 5.4 GWh, is caught up in windy hours and absorbs 5.8
GWh of wind that would otherwise be curtailed; at the marginal fuel use of 217
Sm³/MWh this saves the remaining 1.28 MSm³ (42 %). Both parts therefore result
from the same deferral of injection: the commitment part from the hours it
leaves, and the energy part from the hours it moves to.

**Table 3.** Split of the fuel saved by flexible scheduling (Case 2 to Case 3, 2023).

| Part | Driver | Fuel saved [MSm³/yr] | Share |
|---|---|---|---|
| Commitment | 1,674 GT unit-hours avoided × 1,068 Sm³ no-load fuel | 1.79 | 58 % |
| Energy shifting | 5.8 GWh more wind used × 217 Sm³/MWh marginal fuel | 1.28 | 42 % |
| **Total** | | **3.07** | |

> **Fig. 4.** Week 3 (15–21 January 2023), the week with the median fuel
> saving. Top and middle: power supplied by GTs and wind with fixed (Case 2)
> and flexible (Case 3) demand. Bottom: production and injection rates.

> **Fig. 5.** Left: duration curves of GT load per running unit (shaded:
> below 50 %). Right: hours per year with two and with one GT running.

The pattern is illustrated by the example week in Fig. 4, which is the week
with the median fuel saving. Whenever the wind drops, injection is reduced,
sometimes to zero, so that the demand follows the wind, and when the wind
returns, injection runs at full rate in order to catch up. Over the year, the
injection rate follows the available wind (Fig. 6): its mean increases from 57
% of capacity in the calmest hours to 98–100 % when more than 16 MW of wind
power is available, and the correlation coefficient between injection rate and
available wind is 0.61. Injection is below its 85 % target in 2,563 h, stopped
completely in 187 h and above the target in 6,129 h. Over the year it averages
84.9 % of capacity, and the voidage target is thus met.

The deficit remains small compared with the limit. It averages 9.0 h of
full-rate injection, never exceeds 27.5 h and is above 24 h in only 149 h of
the year, which is well within the 72 h allowed. At the end of the year, 8.2 h
of injection remain to be caught up, corresponding to less than 1 % of the
annual saving. The short duration of the deficits is a consequence of the
mechanism described above, since the hours in which a second GT would be
required occur in spells of a few hours to about a day, between periods of
sufficient wind.

Production is not reduced in any of the cases. One hour at a rate of 50 %
would lose oil and gas worth about 1.5 MNOK, whereas the fuel and CO~2~ saved in
that hour are worth a few thousand NOK, and the optimizer therefore always
prefers to defer injection. The saving from flexibility is obtained in every
month and ranges from 0.43 to 0.77 kt (Fig. S3). It is largest in June,
December and July, which are the months in which the wind often falls just
below the demand.

> **Fig. 6.** Left: water injection rate against available wind in Case 3
> (mean and 10–90 % range of hours). Right: distribution of the injection
> deficit (dashed: 72 h limit).

### 3.4 Sensitivity analysis

**Table 4.** Annual CO~2~ [kt/yr] in the sensitivity runs (2023).

| Varied input | Values | Case 2 | Case 3 | Case 4 |
|---|---|---|---|---|
| Wind farm size [turbines] | 1 / 2 / 3 / 4 | 77.6 / 64.7 / 60.2 / 57.6 | 71.9 / 57.5 / 53.4 / 50.9 | |
| Battery [MW / MWh] | 0 / 2/2 / 4/4 / 8/8 / 8/16 | | | 57.5 / 57.3 / 57.2 / 56.9 / 56.4 |
| Solver gap 0.1 % | | | 57.5 | 57.1 |
| Injection deficit limit [h] | 0 / 24 / 72 / 168 | | 64.7 / 57.5 / 57.5 / 57.5 | |
| Min. GTs online (8 MW battery) | 1 / 0 | | | 56.9 / 38.7 |
| GT fleet | 3 main / 2 main + 1 small / 3 main + 1 small | 64.7 / 53.9 / 53.9 | 57.5 / 47.8 / 47.7 | |
| Keep two GTs online | | 90.7 | 87.7 | |
| GT minimum load [% of rating] | 16 / 30 / 40 / 50 | 64.7 / 71.9 / 77.5 / 86.4 | 57.5 / 64.6 / 70.2 / 76.2 | |
| Pump start cost [kNOK] | 0 / 1 / 5 / 20 | | 57.5 / 57.6 / 57.6 / 57.6 | |
| Reserve covers wind used [%] | 0 / 50 / 100 | 64.7 / 66.2 / 90.7 | 57.5 / 57.7 / 78.2 | |
| Injection pumps as reserve | | 60.4 | 57.6 | |

The results of the sensitivity runs are given in Table 4 and Fig. 7. The CO~2~
and gas prices have almost no effect: across CO~2~ prices of 0.5–3 NOK/kg and
gas prices of 2–8 NOK/Sm³, the emissions change by less than 0.1 %. This is
expected, since the objective is dominated by fuel multiplied by a price, so
the prices scale the cost of every option alike and the cheapest schedule
remains the cheapest. Deferring injection saves fuel at any price, and
shedding production is never profitable, as the lost oil and gas are worth
about a hundred times more than the fuel saved.

The deferral capacity required is small. With no deferral allowed, Case 3 is
identical to Case 2 (64.7 kt). A limit of 24 h already gives the full saving,
with 5 GT starts instead of 3, and a limit of 168 h changes nothing. The
benefit would thus still be captured under a conservative reservoir
constraint.

A larger wind farm gives a smaller improvement than its size suggests.
Doubling the farm from 30 to 60 MW reduces the Case 3 emissions only from 57.5
to 50.9 kt, while the curtailment increases from 39 to 160 GWh, since one GT
must remain online and the platform cannot use more wind in windy hours. The
value of flexibility (Case 2 minus Case 3) is highest at the base-case size
(7.2 kt). It is 5.6 kt for a 15 MW farm, where the wind seldom covers the
demand, and 6.7–6.8 kt for 45–60 MW. Batteries add little as long as one GT
must remain online; the largest one tested, 8 MW / 16 MWh, saves 1.1 kt (2 %).
The effect of the 4 MW / 4 MWh battery, 0.3 kt or 0.5 %, is of the order of
the 0.5 % solver gap. With a gap of 0.1 % it is 0.4 kt (0.7 %), so it is small
but real.

Two assumptions on GT operation have a larger effect than any of these inputs.
If an 8 MW / 8 MWh battery could provide reserve and grid stability, so that
all GTs may be stopped, the emissions would decrease to 38.7 kt, which is 32 %
below the same case with one GT online. The GTs would then run only 3,798
unit-h and start 184 times a year, only 11 GWh of wind would be curtailed, and
the electric heater would supply 15 GWh of heat in the hours with no GT
running. The opposite rule, with two GTs online whatever the wind, increases
the emissions to 90.7 kt in Case 2 and 87.7 kt in Case 3. Flexibility then
saves only 3.1 kt, all of it from lower curtailment, since there is no second
GT left to avoid.

The composition of the GT fleet also matters. Replacing one main unit by a
Solar Mars 100 (11.35 MW) reduces the emissions from 64.7 to 53.9 kt with
fixed demand (−17 %) and from 57.5 to 47.8 kt with flexible demand. The small
unit runs alone in windy hours; its no-load fuel is about half that of a main
unit, and it can carry up to 6.35 MW while holding the 5 MW reserve.
Flexibility still saves 6.1 kt (11.3 %) with the small unit installed and
reduces the starts of the small unit from 465 to 262 per year. Combined, the
small unit and flexibility reduce the emissions by 26 % relative to Case 2.
When the small unit is instead added to the three main units, the emissions
are 47.7 kt, and the third main unit is never used.

The flexibility benefit is robust to the GT and pump assumptions. A higher GT
minimum load raises the emissions of both cases, by 34 % in Case 2 at 50 %
minimum load, because the running GT must then produce more power and more
wind is curtailed. The saving from flexibility stays between 7.2 and 10.2 kt,
or 9.5–11.8 %, and is largest at 50 % minimum load. In the base case the
injection pumps start 731 times a year, about twice a day, at no cost. A start
cost of only 1,000 NOK reduces this to 163 starts a year and the saving by
0.08 kt; at 20,000 NOK per start, 103 starts remain and 0.14 kt of the 7.2 kt
is lost. The optimizer then keeps injection at fixed pump steps for longer and
uses the deficit mainly in the spells that avoid a second GT.

The reserve definition has a larger effect. A reserve that must also cover
half of the wind power used changes Case 3 only slightly (57.7 kt), but raises
Case 2 to 66.2 kt, so that the benefit of flexibility increases to 8.5 kt
(12.8 %). If the reserve must cover the loss of all wind used, two GTs run in
every hour of Case 2 (90.7 kt), whereas flexible scheduling still avoids the
second GT in about 3,600 h and saves 12.5 kt (13.8 %). The opposite
assumption, that the running injection pumps count as reserve because they can
be tripped within seconds, reduces the emissions of Case 2 to 60.4 kt without
any scheduling. This captures about 60 % of the benefit of flexibility, since
a second GT is then never needed, and scheduling adds a further 2.8 kt (4.7
%), close to the energy part of the saving. Load shedding as reserve and load
scheduling are thus two routes to the same mechanism, and they do not add up:
with both, Case 3 emits 57.6 kt, as without tripping.

> **Fig. 7.** Sensitivity of annual CO~2~ emissions to wind farm size, battery
> size, injection deficit limit, minimum number of GTs online, GT fleet,
> operating practice, GT minimum load, pump start cost and reserve definition.

### 3.5 Platform demand and reserve

The base platform has a mean demand of 18.8 MW, just above what one GT can
carry while holding the reserve, 21.8 − 5 = 16.8 MW. The demand and reserve
map (Fig. 8) shows that this margin decides the size of the benefit. When one
GT can carry the mean demand plus the reserve (a positive margin), a second GT
is rarely needed even with fixed demand, and flexibility saves 4.4–4.8 % of
the Case 2 emissions, about the energy part alone. When the mean demand
exceeds the rating of one GT minus the reserve, the saving roughly doubles, to
8–12 %, because deferring injection then avoids the second GT in many hours.
The transition is sharp and occurs at a margin of about zero for all four
reserve sizes, so that the curves of Fig. 8 (right) nearly coincide when they
are plotted against the margin instead of the demand. Further above the
margin, the saving decreases slowly, to 10 % at 22.6 MW, since the deferrable
load is then more often too small to keep the second GT off.

The margin of one GT is therefore a simple screening criterion. With the LEOGO
turbines and a 30 MW wind farm, a platform whose mean demand lies about 2–8 MW
above the rating of one GT minus its reserve can expect about 10–12 % lower
emissions from scheduling its deferrable loads, and a platform with a positive
margin about 4–5 %.

> **Fig. 8.** Flexibility benefit (Case 2 − Case 3, % of Case 2 CO~2~) for 28
> platforms with all electric consumers scaled by 0.6–1.2 and a spinning
> reserve of 3–9 MW. Left: by mean demand and reserve. Right: the same points
> against the margin of one GT, its rating minus the reserve minus the mean
> demand.

### 3.6 Benchmark checks

**Table 5.** Model results against published benchmarks.

| Benchmark | Model | Published | Status |
|---|---|---|---|
| Platform power, three real oil platforms [@voldsund2013; @voldsund2014] | 20.3 MW | 17–30 MW | within |
| Platform power, six modeled platforms [@nguyen2013] | 20.3 MW | 22.6–31.1 MW | below range |
| Platform power, Johan Castberg [@castberg2017] | 20.3 MW | 25 MW | within 20 % |
| Platform power implied by Hywind Tampen [@equinor2023] | 20.3 MW | 25.1 MW | within 20 % |
| Wind capacity factor, Hywind Tampen design [@equinor2023] | 50.9 % | 49.8 % | agrees |
| Wind capacity factor, Hywind Tampen Q1 2025 [@nowind2025] | 50.9 % | 58.4 % (winter) | within 20 % |
| CO~2~ avoided per MWh wind, two GTs kept online [@equinor2023] | 0.51 t/MWh | 0.52 t/MWh | agrees |
| Water injection specific energy [@svendsen2023] | 8.8 kWh/m³ | 9.0 kWh/m³ | agrees |
| CO~2~ intensity, Norwegian shelf 2023 [@offshorenorge2024] | 3.1 kg/boe | 7.3 kg/boe | lower |

The model results are compared with the published benchmarks in Table 5 and
Fig. 9. The platform power, the wind resource and the pump energy agree with
the published values. The platform power lies within the range of
processing-plant power of three real oil platforms and within 20 % of the
other references. It is, however, below the range of the six platforms
modeled by Nguyen et al. [@nguyen2013], in which gas compression alone
accounts for 42–56 % of a demand of 22.6–31.1 MW, compared with 28 % of 20.3
MW in the present model. The capacity factor obtained with ERA5 is within 2 %
of the 49.8 % expected for Hywind Tampen, although that farm uses smaller
floating turbines.

The CO~2~ avoided per MWh of wind is the most demanding check, as it tests the
wind model, the part-load fuel model, the CO~2~ factor and the scheduling
together. When the model keeps two GTs online and only reduces their load, as
assumed in the Hywind Tampen estimate, it avoids 0.51 t/MWh, against the
published value of 0.52 t/MWh. When a GT may be stopped in windy hours, as in
Case 2, it avoids 0.71 t/MWh, since the no-load fuel of the stopped unit is
saved as well. The published value is derived from the expected annual figures of the wind
farm, about 200 kt of CO~2~ avoided per year [@equinor2023], and not from
measurements, so this comparison is a check of consistency rather than a
validation. The model agrees with it only when it is operated as assumed in
that estimate; with a GT allowed to stop, as in Case 2, the model value is 36
% higher. The difference shows to what extent the benefit of wind depends on
the operating practice rather than on the wind farm itself.

The field data support the fuel and emission model (Fig. 9, right). The
Gullfaks field center emitted 2.32–2.40 kg CO~2~ per Sm³ of fuel gas in
2021–2024, which is consistent with the 2.34 kg/Sm³ used here. After Hywind
Tampen started supplying power, the fuel gas use decreased by 30 % at Gullfaks
(2021–2023) and by 11 % at Snorre (2021–2024), and the diesel use at Snorre
fell from 15.6 kt to about 3 kt, whereas the fuel use was unchanged at
Statfjord, which receives no wind power. Since production also declined over
the period, not all of the reduction can be attributed to the wind farm. The
CO~2~ intensity of the model is lower than the shelf average and the field
values (9–14 kg/boe at Gullfaks and Snorre, 55–78 kg/boe at the late-life
Statfjord), as expected from the system boundary: the model covers only power
generation on an efficient platform at plateau rate, whereas the field values
include flaring, diesel, gas re-injection compression and the lower production
of mature fields. The like-for-like checks, i.e. the fuel gas factor and the
CO~2~ avoided per MWh, agree, which indicates that the difference originates
from the boundary and not from the power system model.

> **Fig. 9.** Left: model results divided by published benchmarks (1 =
> equal; shaded: ±20 %; gray bars: published ranges). Right: CO~2~ intensity of
> the Gullfaks, Snorre and Statfjord field centers (gray: GT-powered; teal:
> receiving Hywind Tampen power) with the model Case 1 value (dashed).

### 3.7 Economic indicators

**Table 6.** Economic indicators (real NOK, 20 years; abatement cost range
from the O&M range of floating wind).

| Measure | CO~2~ avoided [kt/yr] | Fuel value saved [MNOK/yr] | Abatement cost [NOK/t], 7 % / 4 % | Break-even investment [MNOK], fuel / fuel + CO~2~ |
|---|---|---|---|---|
| Wind farm, fixed demand (Case 2 vs 1) | 63.0 | 112.8 | 2,180–2,519 / 1,347–1,686 | – |
| Wind farm with flexibility (Case 3 vs 1) | 70.2 | 125.7 | 1,774–2,078 / 1,026–1,330 | – |
| Flexibility (Case 3 vs 2) | 7.2 | 12.9 | −1,799 before implementation cost | 137 / 288 |
| Battery 4 MW / 4 MWh (Case 4 vs 3) | 0.3 | 0.5 | −1,562 before battery cost | 5 / 13 |
| Small GT replacing one main GT (flexible) | 9.7 | 17.4 | −1,786 before GT cost | 184 / 391 |

The economic indicators are given in Table 6. With an investment of 2.5
billion NOK for 30 MW, the wind farm with fixed demand avoids CO~2~ at
2,180–2,519 NOK/t at a 7 % discount rate and at 1,347–1,686 NOK/t at 4 %.
These values are of the same order as the abatement cost of the
power-from-shore projects most recently approved on the Norwegian shelf, just
under 2,000 NOK/t [@sodir2025], and close to the CO~2~ price of 2,000 NOK/t
targeted for 2030 [@klimaplan2021]. Scheduling the flexible loads lowers the
abatement cost of the same wind farm by about 400 NOK/t, to 1,774–2,078 NOK/t
at 7 %, since 11 % more CO~2~ is avoided and 11 % more fuel is saved for the
same investment.

Flexibility on its own gives a net saving before any implementation cost, as
the fuel saved is worth about 1,800 NOK per tonne of CO~2~ avoided. An operator
could spend up to 137 MNOK on control systems and process modifications and
still break even on the fuel saved alone, or up to 288 MNOK when the avoided
CO~2~ cost is included. The 4 MW / 4 MWh battery breaks even only at an
investment below 5–13 MNOK, which is low for an offshore installation of that
size. A small GT replacing one main GT breaks even below 184–391 MNOK, before
its additional maintenance and its 262 starts per year are taken into account.

### 3.8 Weather years

**Table 7.** Results for ten weather years (ERA5, 2014–2023).

| | Mean | Range | 2023 |
|---|---|---|---|
| Wind capacity factor | 54.2 % | 50.3–59.8 % | 50.9 % |
| CO~2~ reduction, Case 2 vs 1 | 51.8 % | 48.5–55.6 % | 49.4 % |
| CO~2~ reduction, Case 3 vs 1 | 57.1 % | 54.5–60.3 % | 55.0 % |
| Flexibility benefit, Case 2 − 3 | 6.8 kt (11.0 %) | 5.9–7.7 kt (10.5–11.7 %) | 7.2 kt (11.1 %) |
| Hours with two GTs, Case 2 / Case 3 | | 1,082–1,889 / 4–66 | 1,702 / 28 |
| Battery benefit, Case 3 − 4 | 0.35 kt | 0.25–0.42 kt | 0.32 kt |
| Maximum injection deficit | | 25.8–59.3 h | 27.5 h |

The results for the ten weather years are summarized in Table 7 and Fig. 10.
The weather year affects the benefit of wind more than the benefit of
flexibility. Over the ten years, the capacity factor of the wind farm ranges
from 50.3 % to 59.8 %, and 2023 is one of the calmer years. The reduction with
fixed demand (Case 2) ranges from 48.5 % to 55.6 %, whereas the additional
saving from flexibility is remarkably stable at 10.5–11.7 % of the Case 2
emissions, or 5.9–7.7 kt/yr, with a mean of 11.0 %, almost exactly the 2023
value. In absolute terms, the saving is largest in the calm years 2016, 2021
and 2023, in which a second GT is needed most often with fixed demand, and
smallest in the windy year 2022. Flexibility removes 96–100 % of the hours
with two GTs online in every year, and in no year is production lost or demand
left unmet.

The injection deficit varies more between the years than the saving does. Its
maximum ranges from 26 to 59 h, which is below the 72 h limit in every year,
and up to 28 h remain to be caught up at the end of a year. In 2016 and 2017,
the years with the largest deficits, a limit of 24 h still captures 98 % of
the saving obtained with 72 h (58.4 against 58.3 kt in 2016 and 52.7 against
52.6 kt in 2017). The conclusion that about one day of deferral is sufficient
thus holds for all the weather years tested.

> **Fig. 10.** Flexibility benefit (Case 2 − Case 3, bars) and wind capacity
> factor (line) for the weather years 2014–2023.

## 4 Discussion

The results presented above show that the benefit of flexible scheduling is
obtained through the unit commitment of the GTs. This mechanism is discussed
in Section 4.1, and the results are compared with earlier studies in Section
4.2. The practical implementation, the robustness of the conclusions and the
limitations of the study are discussed in Sections 4.3–4.5.

### 4.1 Why load flexibility works

Flexible demand saves fuel through two linked effects. Deferring injection in
the hours in which the wind is just too weak for one turbine to carry the load
with 5 MW in reserve keeps the second turbine off, which saves its no-load
fuel, and the deferred injection then uses wind that would otherwise be
curtailed. The commitment effect is the larger one (58 % of the saving), and
it explains three of the results of Section 3: almost all of the 1,702 hours
with two GTs online are avoided; about one day of deficit capacity is
sufficient, since these hours occur in short spells between windy periods; and
the saving is reduced to the energy part alone under operating rules that keep
two GTs online in any case (3.1 kt instead of 7.2 kt).

The energy-shifting part is limited by the wind that can be absorbed. The
curtailment decreases by only 13 %, since one GT must remain online and a 30
MW farm often produces more power than the platform can use, even with
injection at full rate. For the same reason, the value of flexibility does not
increase with the size of the wind farm: a larger farm covers the demand more
often, so that a second GT is needed in fewer hours, and the additional wind
in windy hours cannot be absorbed. Flexibility is thus most valuable when the
wind farm capacity is of the same order as the platform demand, as in the base
case and at Hywind Tampen.

The small effect of the battery in Case 4 has the same cause. With one GT
always online, a battery cannot remove the main remaining loss, which is a
turbine idling near minimum load. The large saving (38.7 kt, −32 %) is
obtained only when the battery, or grid-forming wind turbines, can replace the
last running GT. Svendsen [@svendsen2022] found the same for a battery
providing reserve. The present results show in addition that process
flexibility gives much of this benefit without new equipment, since both
measures reduce the number of GTs that must be online.

A small GT acts on a different part of the loss: it does not reduce the number
of running units, but the no-load fuel of the unit that runs. Its saving
therefore adds almost fully to that of flexibility (Section 3.4). A retrofit
could thus proceed in stages, by first using the flexibility of the existing
process at no investment, and then considering the replacement of one main GT
by a smaller unit at its next major overhaul, provided that the small unit
tolerates about 260 starts a year.

### 4.2 Comparison with earlier studies

Most studies of wind-powered platforms report the benefit of wind at fixed
demand, which corresponds to Case 2 in the present study. This understates the
potential of the same wind farm, as the emissions with fixed demand are 12 %
higher than when the platform schedules its flexible loads. The CO~2~ avoided
per MWh of wind, which is the usual metric for wind integration, is 0.71 t/MWh
in Case 2, 0.74 t/MWh in Case 3 and 0.51 t/MWh if two GTs are kept online.
Values reported for different platforms can therefore only be compared if the
GT operating practice behind them is stated.

The economic performance of flexibility also differs from that of wind
integration. Riboldi and Nord [@riboldi2018] found that integrating wind is
profitable only with favorable gas and CO~2~ prices. Flexibility, in contrast,
requires no investment in power generation, its schedule does not depend on
prices, and the fuel it saves is worth about 1,800 NOK per tonne of CO~2~
avoided at the base-case gas price alone. It is thus profitable without any
carbon price, which is relevant in regions where emissions are not priced. The
wind farm, by comparison, requires about 1,800–2,500 NOK/t at a 7 % discount
rate to break even, which is of the same order as power from shore
[@sodir2020; @sodir2025], and flexibility lowers this value by about 400
NOK/t.

The comparison with onshore demand response is less direct than it may appear.
Industrial studies consider the response to electricity prices
[@zhang_grossmann2016; @golmohamadi2022], whereas on an off-grid platform the
value of a load shift arises from discrete decisions of the platform's own
power plant, i.e. whether a GT must be started or can be stopped. This value
depends on the state of the system hour by hour, and a model of energy
shifting alone, without unit commitment, would not capture most of it.

### 4.3 Practical implementation

This flexibility already exists on most oil platforms with water injection.
Its use requires no new equipment, but it requires a power management system
that coordinates the injection with the GTs and a wind forecast, whereas these
are usually controlled separately today.

The requirement on the reservoir is modest. A deferral of about 24 h, with an
average of 9.0 h, is short compared with the months over which voidage
replacement is normally managed. It must nevertheless be confirmed for each
field, since a reservoir close to its bubble point, for example, may not
accept even short pressure drops.

The schedule also changes the duty of the injection pumps. Without a cost,
they start 731 times a year in Case 3, about twice a day. A modest start cost
reduces this to 100–160 starts a year at a loss of only 1–2 % of the saving
(Section 3.4), so pump wear is not an obstacle; an operator can choose the
start frequency it accepts.

Operating practice deserves at least as much attention as hardware. The number
of GTs that must be online, and the definition of reserve, affect the
emissions more than any price or the battery size. Rules that keep two GTs
online for redundancy increase the emissions by 40 % with fixed demand and by
53 % with flexible demand and remove most of the value of flexibility. Such
rules exist for good reasons of safety and regularity. Two measures can relax
them without new generation. Running injection pumps can serve as reserve,
since tripping them is fast and costs no production; this alone captures about
60 % of the benefit of flexibility. Grid-forming batteries that provide
reserve and stability without a running GT would go further and are the
logical next step after demand flexibility.

The approach should be transferable to other installations. The demand and
reserve map (Section 3.5) gives a simple screening rule: a platform gains
most, about 10–12 %, when its mean demand exceeds the rating of one GT minus
the reserve, and about 4–5 % otherwise, provided it has a large deferrable
consumer and a wind supply of the same order as its demand. On other types of
installations, gas export compression, electric heating and the regeneration
of glycol or other process chemicals could be deferrable, but only where
buffer storage such as line pack or tank volume is available.

### 4.4 Robustness of the conclusions

The saving is determined by the number of hours in which, at fixed demand, the
platform runs one GT more than its load requires. The sensitivity runs confirm
the expected direction of the main assumptions: a larger reserve, a reserve
that covers the wind, a higher GT minimum load and a demand above the margin
of one GT all increase the value of flexibility, whereas a wind farm much
larger than the demand, or injection pumps that already count as reserve,
reduce it.

The assumptions on the flexible load have less effect than might be expected.
Since injection is reduced by stopping whole pumps, the assumed minimum pump
flow changes the cost of running one pump at low rate but hardly affects the
saving. The injection target has a larger effect: a lower target leaves more
room for catching up, and at a target of 100 % deferred injection could never
be caught up and the flexibility would vanish. The heat balance was never
binding in the base cases, since the waste heat of the running GT always
covered the heat demand of 3 MW. A platform with a larger heat demand, or one
that relies on the heat of the GTs to be stopped, would save less unless its
heat demand can be scheduled as well.

The result that production should never be shed is the most robust one, since
the lost oil and gas are worth about a hundred times more than the fuel saved,
and no plausible change in prices or efficiencies reverses this.

### 4.5 Limitations and future work

The platform is generic, and the fluid composition, the minimum-flow limits,
the injection target and the deficit limit were assumed, although the results
are insensitive to the deficit limit, the prices and the battery size. The
process is represented by steady states, and the transient compressor
behavior, the start-up times of pumps and GTs beyond a start cost, and the
reservoir response to deferred injection are not modeled. The GT part-load
curve is a Willans line derived from LEOGO, and the curve of a real machine,
including its emissions at very low load, may differ.

The scheduler knows the wind one week ahead, and the savings are therefore an
upper bound. Since the deficit limit is rarely reached, a forecast-based
schedule that keeps a margin on the deficit should retain most of them, but
this remains to be demonstrated. The ten weather years cover one site and one
platform, without power import or export. The economic indicators are based on
the cost of a single first-of-a-kind floating wind farm and exclude the cost
of implementing flexibility, the battery or the small GT, for which only
break-even values are given. The small GT uses the relative part-load curve of
the main units, since its manufacturer publishes only the full-load rating.

Several directions for further work follow from these limitations. Rolling
schedules with forecast errors would show how much of the saving is retained
without perfect foresight. Pump start costs and a simple reservoir pressure
model would test the injection schedule against operational limits. Data from
a platform with wind supply, such as those served by Hywind Tampen, would
allow the model to be calibrated. Finally, combining load flexibility with
grid-forming storage and the investment cost of the whole system would show to
what extent an off-grid platform can be decarbonized before power from shore
is required.

## 5 Conclusions

The electric demand of a generic North Sea oil platform was mapped with a
process model, the consumers were classified according to their flexibility,
and the flexible consumers were scheduled together with the gas turbines and a
30 MW wind farm, hour by hour, for ten weather years. Four cases were
investigated in order to separate the effect of the wind farm from that of
demand flexibility and of a battery, and the model was checked against published data for Hywind Tampen and three
North Sea field centers.

With fixed demand, the wind farm halves the CO~2~ emissions of the 20 MW
platform (−49 %). Scheduling the flexible consumers reduces the emissions by a
further 11 % (7.2 kt/yr) without lost production, and the saving remains
between 10.5 % and 11.7 % across the ten weather years. The GT low-load hours
decrease by 34 %, and the GT starts nearly disappear. All of the useful
flexibility is provided by water injection: shedding production is never
profitable, and a deferral of about 24 h is sufficient. The saving is obtained
by avoiding the operation of a second GT rather than by shifting energy.
Operating rules that keep two GTs online therefore remove most of it, whereas
allowing all GTs to stop, with a battery providing reserve, would reduce the
emissions by a further third. A small GT (11.35 MW) replacing one main unit
saves another 17 %, and flexibility still saves 11 % with this unit installed.

Prices and battery size alone have little effect on the results. Flexibility
pays for itself through fuel savings, breaks even for an implementation cost
of up to 137 MNOK and lowers the abatement cost of the wind farm from
2,180–2,519 to 1,774–2,078 NOK/t. With two GTs kept online, as assumed in the operator's estimate, the model
agrees with the CO~2~ avoided per MWh of wind expected for Hywind Tampen, and
it reproduces the fuel gas emission factor observed at Gullfaks. Although the exact values would differ
from one platform to another, it is suggested that the scheduling of topside
loads is a low-cost measure that should be considered together with any
integration of wind power on off-grid platforms. Three questions remain open:
how much of the saving is retained with realistic wind forecasts, which limits
the pump starts and the reservoir pressure place on the injection schedule,
and whether grid-forming storage can safely remove the last running GT.

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
