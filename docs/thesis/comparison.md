# Comparison with a tropical gas platform (Tanzania)

*Draft for the thesis chapter (or a section of the results chapter). The site
and platform are described in Methods, Section 10. All values are for the
ERA5 weather year 2023. Tanzania results are in `results/tanzania/`, the
side-by-side table and figure in `results/comparison/`.*

## 1 The two settings

The two sites differ in almost every input that matters for the result
(Table C1). The Tanzanian platform is smaller and dominated by one large
consumer, the export compressor. Its wind resource is much weaker: the mean
hub-height wind speed is 6.7 m/s against 9.8 m/s, and the capacity factor of
the same 30 MW wind farm is 29.6 % against 50.9 %. The seasons are opposite
(Figure 11, middle). Tanzanian wind peaks in the south-east monsoon (July
63 %) and almost disappears in December (10 %), the pattern reported from
measurements at coastal Tanzanian stations. The North Sea is windiest in winter.
The hot climate costs the gas turbines 8 % of their power, and the lean
fuel gas emits 17 % less CO2 per Sm³ than Norwegian fuel gas.

**Table C1.** Main inputs and results for the two sites (case numbers as in
Chapter 3; CO2 in kt per year).

| | North Sea (Tampen) | Tanzania (Blocks 1, 2, 4) |
|---|---|---|
| Platform | oil, water injection | gas, export compression |
| Design electric demand | 20.3 MW | 15.4 MW |
| Largest consumer | water injection, 9.2 MW (45 %) | export compressor, 11.2 MW (73 %) |
| Mean hub wind speed | 9.8 m/s | 6.7 m/s |
| Wind capacity factor (2 × 15 MW) | 50.9 % | 29.6 % |
| GT rating at site (LEOGO) | 21.8 MW, 34.7 % | 20.0 MW, 34.3 % (26.8 °C) |
| Fuel CO2 factor | 2.34 kg/Sm³ | 1.95 kg/Sm³ |
| CO2 price | NOK 2.0/kg | zero in the base case |
| Flexibility buffer | 72 h of water injection | 3.6 h line pack + 48 h MEG tank |
| Case 1 – GTs only | 127.7 | 101.7 |
| Case 2 – wind, fixed demand | 64.7 (−49.4 %) | 57.8 (−43.2 %) |
| Case 3 – wind, flexible | 57.5 (−54.9 %) | 55.2 (−45.7 %) |
| Case 4 – case 3 + battery | 57.1 (−55.2 %) | 55.0 (−45.9 %) |
| Flexibility benefit (case 2 − 3) | 7.1 kt (11.0 %) | 2.6 kt (4.5 %) |
| Hours with a second GT, case 2 → 3 | 1,702 → 30 | 895 → 13 |
| GT starts, case 2 → 3 | 149 → 6 | 121 → 2 |
| GT low-load unit-hours, case 2 → 3 | 9,005 → 5,928 (−34 %) | 6,403 → 4,800 (−25 %) |
| Lost production, case 3 | 0 | 0 |

## 2 Results of the four cases

Wind cuts emissions substantially at both sites, but less in Tanzania:
−43.2 % against −49.4 % with fixed demand (Figure 11, left). The weaker wind
delivers 57 GWh to the platform instead of 89 GWh, covering 42 % of the
annual demand against 54 % in the North Sea. Because the Tanzanian platform
needs less power, the gap is smaller than the capacity factors (29.6 % against
50.9 %) suggest.

Flexible scheduling adds a further 2.6 kt/yr (4.5 % of case 2) in Tanzania.
That is about a third of the North Sea benefit in absolute terms and less than
half in relative terms, but still clearly positive, and again with **no lost
production**: the gas
delivered to shore over the year equals the sales rate, and the line pack
always returns to full by the end of the horizon. A 4 MW / 4 MWh battery
adds only 0.2 kt in Tanzania and 0.4 kt in the North Sea.

The case 1 emissions differ more than the fuel use does (52.3 against
54.6 MSm³/yr). Tanzania needs less power, but its turbines are derated by the
heat and its fuel has a lower heating value. The CO2 difference therefore
comes mainly from the lower carbon content of the lean gas.

> **Figure 11.** North Sea vs Tanzania. Left: CO2 of cases 2–4 relative to
> case 1 at each site. Middle: monthly capacity factor of the same 30 MW wind
> farm (ERA5 2023). Right: CO2 saving of case 3 relative to case 2 against the
> size of the flexibility buffer (water injection deficit limit in the North
> Sea, line pack in Tanzania).

## 3 Same mechanism, less to gain

The flexibility saving comes from the same mechanism at both sites.
Postponing flexible load lets one gas turbine carry the platform in hours when
the wind is just too weak, instead of starting a second turbine that idles at
low load. In Tanzania, the hours with two GTs online fall from 895 to 13, the
starts from 121 to 2, and the GT low-load hours by 25 % (Table C1). The example
week (Figure 12) shows how this works on a gas platform. When the wind drops,
the platform lowers its gas production to about 70 % and pauses MEG
regeneration. When the wind returns, it produces at 110 % to refill the
pipeline. Production was above the sales rate in 4,192 hours and below it in
2,691 hours.

The saving is smaller for two reasons.

* **Less to avoid.** The Tanzanian design demand (15.4 MW) is only just
  above what one derated GT can carry while holding 5 MW in reserve
  (15.0 MW). Even with fixed demand, a second GT is therefore needed in
  only 895 hours of the year, about half as often as in the North Sea
  (1,702 h). Flexibility removes almost all of these hours at both sites,
  but in Tanzania there are fewer to remove.
* **A much smaller energy buffer.** Cutting production to its minimum lowers
  the Tanzanian demand by 6.0 MW (North Sea injection lever: 9.6 MW). But
  the line pack holds only 3.6 h of full-rate production, so only about
  45 MWh of electricity can be postponed. The 48 h MEG tank adds about
  5 MWh, because regeneration uses only 0.1 MW of electricity; its 1 MW of
  heat comes from turbine waste heat, which is always in surplus. The North
  Sea injection buffer of 72 h holds about 660 MWh. Tanzanian flexibility
  can bridge short lulls of a few hours, but it cannot move much wind energy
  from windy to calm periods. Wind curtailment therefore falls by only
  1.6 GWh (North Sea: 5.7 GWh).

The line-pack sensitivity confirms this (Figure 11, right; Figure 13).

| Line pack | 0 h | 1.8 h | 3.6 h | 7.2 h |
|---|---|---|---|---|
| Saving vs case 2 | 0.3 % | 4.2 % | 4.5 % | 4.9 % |

With no line pack, only MEG regeneration can be moved, and the benefit almost
disappears: 121 GT starts remain, as with fixed demand. The first 1.8 h of
line pack gives most of the benefit. In the North Sea, likewise, 24 h of
injection deficit gave the full result. Allowing a wider pipeline pressure
swing would raise the Tanzanian benefit only slowly.

> **Figure 12.** Tanzania, example week (week with the median fuel saving).
> Top two panels: power supply with fixed and with flexible demand. Bottom:
> gas production and MEG regeneration as % of design. Production above 100 %
> refills the pipeline line pack.

## 4 Sensitivities in Tanzania

The other sensitivities behave as in the North Sea (Figure 13):

* **Wind farm size.** Each extra 15 MW turbine saves less: case 3 emissions
  are 64.5, 55.2, 50.3 and 47.3 kt/yr for one to four turbines. The
  flexibility benefit stays at about 2.6–2.8 kt whatever the farm size,
  because it is limited by the line pack, not by the wind.
* **CO2 price and gas price** have no effect (55.2 kt in all runs, including
  the Tanzanian carbon excise duty of 2025, about NOK 0.09/kg). The
  scheduler already minimises fuel, so a carbon price changes the cost but
  not the operation. A carbon price is therefore not needed for this
  flexibility to pay off: it saves fuel that can be sold as LNG.
* **Operating practice** dominates. Keeping two GTs online removes almost
  all of the benefit of wind (79.2 kt in case 2, 78.4 kt in case 3).
* **No GT online.** Unlike the North Sea, allowing all GTs to stop with an
  8 MW / 8 MWh battery is **not feasible** in Tanzania: it leaves 27 MWh of
  demand unmet over the year and needs 215 GT starts. Long calms and a weak
  resource mean that a battery of this size cannot always bridge the start
  of a gas turbine. The result (46.4 kt) is marked in Figure 13 and is not a
  valid design.
* **Gas turbine fleet.** Replacing one main GT by a smaller unit saves
  1.1 kt more but needs 45 starts instead of 2.

Results that differ only by solver tolerance (for example the base case
repeated within a sensitivity group) agree within 0.1 kt.

> **Figure 13.** Tanzania, sensitivity of annual CO2 (cases 2–4). A red ring
> marks a run with unmet demand.

## 5 What the comparison shows

1. The main finding holds at a tropical gas platform with a much weaker wind
   resource and a different process. Scheduling flexible consumers cuts CO2
   further without lost production, mainly by avoiding a second running gas
   turbine.
2. The size of the benefit depends on how many hours of load the platform
   can postpone, not on how many megawatts it can shed. An oil platform with
   water injection has a buffer of days. A gas platform has only the line
   pack of its export pipeline, a few hours. Because this platform also
   needs a second turbine less often in the first place, the benefit is less
   than half as large (4.5 % against 11 % of case 2 emissions).
3. Wind alone reduces emissions less in Tanzania (−43 % against −49 %), and
   its strong seasonal pattern leaves December almost without wind.
4. With no carbon price, or with the small Tanzanian excise duty of 2025,
   wind and flexibility are justified in Tanzania by the gas they save for
   sale, not by avoided CO2 cost.

**Limitations specific to this case.** The processing platform is
hypothetical: the planned development is subsea-to-shore. The gas composition,
pipeline size and pressures, and the production limits are assumptions. 43 of
115 parameters remain assumptions, 22 of them specific to Tanzania
(`docs/verification/tanzania_assumptions.md`). The TEG and MEG duties were
checked with NeqSim water-content calculations. No operating data are available for
validation; the wind input is checked only qualitatively against coastal
station measurements and the ESMAP offshore-wind maps. ESMAP counts technical
potential only where the mean wind speed is at least 7 m/s, slightly above
the 6.4 m/s at 100 m that ERA5 gives here. Reanalysis data may underestimate
offshore wind speeds, so the Tanzanian wind results are likely conservative.
