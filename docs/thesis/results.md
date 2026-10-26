# Results

*Draft for the thesis chapter. All values are for the ERA5 weather year 2023
and the base-case parameters in Table T1. Figures and tables are in
`results/paper/` (figure files `figXX_*.png/.pdf`, tables `tables/T2–T4`).*

## 1 Wind resource

The ERA5 wind speed at the site averages 9.4 m/s at 100 m and 9.8 m/s at the
150 m hub height. The 30 MW wind farm would deliver 133.8 GWh in 2023, a
capacity factor of **50.9 %** (Figure 1). Output is strongly seasonal: the
monthly capacity factor is 63–68 % in January and February and 36–37 % from
June to August. The farm delivers its maximum 26.5 MW in 40 % of the hours
(3,511 h) and nothing in 9.6 % of the hours (839 h, calm periods and a few
hours above cut-out). Available wind power exceeds the platform's design
demand of 20.3 MW in 4,017 hours.

> **Figure 1.** Wind resource at 61° N, 2° E in 2023 (ERA5). Left: monthly
> capacity factor of the 30 MW wind farm (dashed: annual mean). Right:
> duration curve of wind farm power.

## 2 Demand map and gas-turbine efficiency

At design the platform needs 20.3 MW (Table 1, Figure 2). Water injection is
the largest single consumer (9.2 MW, 45 %) and the only large deferrable one.
The sheddable consumers tied to production account for 7.2 MW (35 %) and the
must-run base load for 3.5 MW (17 %). Stopping injection at full production
lowers the demand from 20.3 MW to 10.7 MW, a swing of 9.6 MW that costs no
production as long as the injection is caught up. The production lever has a
characteristic step: just above 50 % rate the second export compressor train
must start at its surge limit, raising power by 0.75 MW.

> **Figure 2.** Demand map. Left: electric power at design by consumer,
> coloured by flexibility class. Right: power of the production (sheddable)
> and injection (flexible) levers against lever position.

GT efficiency falls steeply at part load (Figure 3): from 34.7 % at full load
to 29.3 % at half load and 17.7 % at the 3.5 MW minimum load, so the CO2 per
MWh of electricity almost doubles (623 → 1,220 kg/MWh). Running GTs at low
load is therefore costly, and avoiding it is the main lever for savings.

> **Figure 3.** Part-load electric efficiency (left) and specific CO2 emission
> (right) of the gas turbines. Shaded: below minimum stable load.

## 3 Comparison of the four cases

**Table 2.** Annual results for the four cases (2023).

| | 1 GTs only | 2 Wind, fixed | 3 Wind, flexible | 4 Flexible + battery |
|---|---|---|---|---|
| CO2 [kt/yr] | 127.7 | 64.7 | 57.6 | 57.2 |
| Reduction vs case 1 | – | 49.4 % | 54.9 % | 55.2 % |
| Fuel gas [MSm3/yr] | 54.6 | 27.6 | 24.6 | 24.4 |
| GT running [unit-h/yr] | 17,520 | 10,462 | 8,790 | 8,760 |
| GT below 50 % load [unit-h/yr] | 17,520 | 9,005 | 5,928 | 6,235 |
| GT starts [-/yr] | 0 | 149 | 6 | 0 |
| Wind used [GWh/yr] | 0 | 89.3 | 95.0 | 95.8 |
| Wind curtailed [GWh/yr] | 0 | 44.5 | 38.8 | 38.0 |
| Lost production | 0 | 0 | 0 | 0 |
| Fuel value + CO2 cost [MNOK/yr] | 484.0 | 245.1 | 218.1 | 216.6 |

With gas turbines only, the platform burns 54.6 MSm3 of fuel gas and emits
127.7 kt CO2 per year (Table 2, Figure 4). Two GTs run in every hour to
carry the load and the 5 MW reserve, each at about 43 % load, so all 17,520
unit-hours are low-load hours.

Adding the 30 MW wind farm with fixed demand (case 2) halves the emissions to
64.7 kt (−49.4 %). Because demand cannot follow the wind, 44.5 GWh of wind
(33 % of the available energy) is curtailed, and a second GT is still needed
in 1,702 hours, with 149 starts.

Flexible scheduling (case 3) reduces CO2 by a further **7.1 kt/yr (−11.0 %
relative to case 2)** to 57.6 kt, **without any loss of production**. Fuel use
falls by the same 11 %, GT low-load unit-hours by 34 % (9,005 → 5,928), GT
starts from 149 to 6, and wind curtailment by 13 % (44.5 → 38.8 GWh). The
combined fuel value and CO2 cost falls by 27 MNOK/yr compared with case 2.

A 4 MW / 4 MWh battery (case 4) adds only 0.4 kt (−0.7 %). It removes the
remaining GT starts and the last hours with a second GT, but with one GT
always online it cannot remove the main remaining loss: one GT idling near
minimum load whenever the wind covers the demand.

> **Figure 4.** Annual CO2, fuel gas, GT hours below 50 % load and lost
> production for cases 1–4.

## 4 How flexible scheduling saves fuel

The savings in case 3 come almost entirely from **avoiding a second gas
turbine**. With fixed demand, a second GT is needed whenever the wind drops
and one GT cannot carry the load while keeping 5 MW in reserve (1,702 h in
case 2). Each such hour costs the no-load fuel of a whole extra GT. In case 3,
the optimiser postpones water injection in exactly these hours, so one GT
suffices; a second GT runs in only 30 hours of the year (Figure 6).

The example week in Figure 5 (week 29, the week with the median fuel saving)
shows the pattern: whenever wind drops, injection is cut, sometimes to zero,
and the demand line follows the wind; when wind returns, injection runs at
100 % to catch up. Over the year, injection is below its 85 % target in
2,597 hours, stopped completely in 178 hours, and above target in 6,048 hours.
The mean injection rate stays at 84.9 % of capacity, so the voidage target is
met (Figure 7). Injection rate and available wind are clearly correlated
(r = 0.61): mean injection rises from 59 % in the calmest hours to 98–99 %
when more than 16 MW of wind is available.

The injection deficit stays small. It averages 7.5 h of full-rate injection
and never exceeds 25.2 h, well below the 72 h allowed (Figure 7, right). The
year ends with 6.3 h of injection still to be caught up, equivalent to less
than 1 % of the annual saving.

Production is never reduced in any case. Shedding production is not
economic: one hour at 50 % rate loses oil and gas worth about 1.5 MNOK,
while the CO2 and fuel saved are worth a few thousand NOK.

> **Figure 5.** Week 29 (16–22 July 2023), the week with the median fuel
> saving. Top and middle: power supplied by GTs and wind for fixed (case 2)
> and flexible (case 3) demand. Bottom: production and injection rates.

> **Figure 6.** Duration curves of GT load per running unit (left, shaded:
> below 50 %) and of the number of GTs running (right).

> **Figure 7.** Left: water-injection rate against available wind in case 3
> (mean and 10–90 % range of hours). Right: distribution of the injection
> deficit (dashed: 72 h limit).

## 5 Seasonal pattern

Monthly emissions follow the wind (Figure 8). In case 2 they range from
3.8 kt in February to 6.4 kt in June and July. The saving from flexibility is
present in every month (0.42–0.76 kt/month). It is largest in June (0.76 kt),
December and July, months in which the wind often falls below the demand and
a second GT would otherwise be needed.

> **Figure 8.** Monthly CO2 emissions for cases 1–4.

## 6 Sensitivity analysis

**Table 3.** Annual CO2 [kt/yr] in the sensitivity runs (selected).

| Varied input | Values | Case 2 (fixed) | Case 3 (flexible) | Case 4 (battery) |
|---|---|---|---|---|
| Wind farm size [turbines] | 1 / 2 / 3 / 4 | 77.6 / 64.7 / 60.2 / 57.6 | 72.0 / 57.6 / 53.3 / 50.9 | |
| CO2 price [NOK/kg] | 0.5 / 1 / 2 / 3 | | 57.5 / 57.5 / 57.6 / 57.5 | |
| Gas price [NOK/Sm3] | 2 / 4.19 / 8 | | 57.5 / 57.6 / 57.5 | |
| Battery [MW / MWh] | 0 / 2/2 / 4/4 / 8/8 / 8/16 | | | 57.6 / 57.3 / 57.2 / 56.9 / 56.4 |
| Injection deficit limit [h] | 0 / 24 / 72 / 168 | | 64.7 / 57.6 / 57.6 / 57.5 | |
| Min. GTs online (8 MW battery) | 1 / 0 | | | 56.9 / 38.7 |
| GT fleet | 3 main / 2 main + 1 small | | 57.6 / 55.6 | |
| Keep 2 GTs online | | 90.7 | 87.7 | |

The results (Table 3, Figure 9) show which inputs matter:

* **Prices do not change the schedule.** Across CO2 prices of 0.5–3 NOK/kg
  and gas prices of 2–8 NOK/Sm3, emissions change by less than 0.1 %.
  Production is never shed, and the injection schedule is driven by fuel
  savings that are worthwhile at any price.
* **A small injection deficit is enough.** With no deferral allowed (0 h)
  case 3 is identical to case 2 (64.7 kt). A limit of 24 h already gives the
  full saving; allowing 168 h changes nothing more. Even a conservative
  reservoir constraint would therefore capture the benefit.
* **Wind farm size has diminishing returns.** Doubling the farm from 30 to
  60 MW lowers case 3 emissions only from 57.6 to 50.9 kt, while curtailment
  grows to 160 GWh, because one GT must stay online. The value of flexibility
  (case 2 minus case 3) is largest for the base-case farm (7.1 kt) and
  smaller for a 15 MW farm (5.5 kt), where wind seldom exceeds the demand.
* **Batteries add little on their own:** about 2 % at most (8 MW / 16 MWh).
* **The minimum number of GTs online is the dominant assumption.** If an
  8 MW / 8 MWh battery can provide the reserve and grid stability so that all
  GTs may stop, emissions fall to 38.7 kt, 32 % below the same case with one
  GT online. GTs then run only 3,809 unit-hours, and 15 GWh of heat is
  supplied by the electric heater.
* **Operating practice matters as much as hardware.** If operators keep two
  GTs online whatever the wind, emissions rise to 90.7 kt (case 2) and
  87.7 kt (case 3). Flexibility then saves only 3.1 kt, because its main
  mechanism, avoiding the second GT, is no longer available.
* Replacing one GT by a smaller unit lowers case 3 emissions by 3.4 %, but
  the data for the small unit are not verified.

> **Figure 9.** Sensitivity of annual CO2 emissions to wind farm size, CO2
> and gas price, battery size, injection deficit limit, minimum number of GTs
> online and GT fleet.

## 7 Validation

**Table 4.** Model results against published benchmarks.

| Benchmark | Model | Published | Status |
|---|---|---|---|
| Platform power, three real North Sea oil platforms (Voldsund et al., 2013, 2014) | 20.3 MW | 17–30 MW | within |
| Platform power, modelled platforms (Nguyen et al., 2013) | 20.3 MW | 22.6–31.1 MW | below range |
| Platform power, Johan Castberg PDO | 20.3 MW | 25 MW | within 20 % |
| Platform power implied by Hywind Tampen | 20.3 MW | 25.1 MW | within 20 % |
| Wind capacity factor, Hywind Tampen design | 50.9 % | 49.8 % | agrees |
| Wind capacity factor, Hywind Tampen Q1 2025 | 50.9 % | 58.4 % (winter) | within 20 % |
| CO2 avoided per MWh wind, two GTs kept online | 0.51 t/MWh | 0.52 t/MWh | agrees |
| CO2 avoided per MWh wind, GTs may stop | 0.71 t/MWh | 0.52 t/MWh | higher (see text) |
| Water-injection specific energy (LEOGO) | 8.8 kWh/m3 | 9.0 kWh/m3 | agrees |
| CO2 intensity, Norwegian shelf 2023 | 3.1 kg/boe | 7.3 kg/boe | lower (see text) |
| CO2 intensity, non-electrified hubs | 3.1 kg/boe | ~10.5 kg/boe | lower (see text) |

The platform power, wind resource and pump calculation agree with the
published values (Table 4, Figure 10). The ERA5-based capacity factor of
50.9 % is within 2 % of the 49.8 % expected for Hywind Tampen, although that
farm uses different (8 MW, floating) turbines.

The strongest check is the **CO2 avoided per MWh of wind**, because it tests
the wind, GT part-load fuel, CO2 factor and scheduling together. When the
model keeps two GTs online and only lowers their load, as assumed in the
Hywind Tampen estimate, it gives 0.51 t/MWh against the published 0.52 t/MWh
(−2 %). When a GT may stop in windy hours, the model avoids 0.71 t/MWh,
because the no-load fuel of the stopped unit is saved as well. The
difference indicates how much additional reduction depends on operating
practice rather than on the wind farm itself.

The field data (Figure 10, right) support the fuel and emission model. The
Gullfaks field centre emits 2.32–2.40 kg CO2 per Sm3 of fuel gas in 2021–2024,
consistent with the 2.34 kg/Sm3 used in the model. After Hywind Tampen started
supplying power, fuel gas use fell by 30 % at Gullfaks (2021 → 2023) and by
11 % at Snorre (2021 → 2024), and Snorre's diesel use fell from 15.6 kt to
2.7–3.2 kt. At Statfjord, which has no wind supply, fuel use was unchanged
(+2 %). Production also declined over the period, so not all of the
reduction can be attributed to the wind farm.

The model's CO2 intensity (3.1 kg/boe in case 1) is lower than the shelf
average and the field values (9–14 kg/boe at Gullfaks and Snorre, 55–78 kg/boe
at late-life Statfjord). This is expected from the system boundary: the model
covers only power generation for an efficient platform at plateau rate,
whereas the field values include flaring, diesel, gas re-injection
compression (Snorre re-injects all its gas) and the lower production of
mature fields. The like-for-like checks (fuel-gas factor and CO2 avoided per
MWh) agree, which indicates that the difference stems from the boundary and
not from the power-system model.

> **Figure 10.** Left: model results divided by published benchmarks (1 =
> equal; shaded: ±20 %; grey bars: published ranges). Right: CO2 intensity of
> the Gullfaks, Snorre and Statfjord field centres (grey: GT-powered; teal:
> receiving Hywind Tampen power) with the model case 1 value (dashed).

## 8 Summary of findings

1. A 30 MW wind farm halves the CO2 emissions of the 20 MW platform
   (−49 %), even with fixed demand.
2. Scheduling flexible topside consumers cuts emissions by a further 11 %
   (7.1 kt/yr), with **no lost production**, fewer GT low-load hours (−34 %),
   almost no GT starts and less wind curtailment.
3. Water injection provides all of the flexibility; shedding production is
   never worthwhile. A deferral capacity of about 24 h of injection is
   enough.
4. The saving comes mainly from avoiding a second running GT. It therefore
   depends strongly on operating practice: rules that keep two GTs online
   remove most of it, and allowing all GTs to stop (with a battery providing
   reserve) would cut emissions by a further third.
5. Batteries alone, CO2 price and gas price have little effect on the
   result.
6. The model reproduces the CO2 avoided per MWh of wind reported for Hywind
   Tampen within 2 % and the fuel-gas emission factor observed at Gullfaks.
