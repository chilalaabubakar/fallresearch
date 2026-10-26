# Source checklist: claims to confirm in the original documents

**Status:** sections 1 and 2 checked against the original papers (see the
notes in each). Sections 4–6 are not needed any more: the Tanzania case was
dropped from the paper. Section 3 (Johan Castberg PDO) is still open.

These values were taken from search-result summaries because the originals
could not be opened from the cloud session. For each document: find the
statement, tick it, and write down the page, table or section. If the
original says something different, note the correct value; the config and
text listed under "Used in" then need updating.

## 1 Voldsund et al. (2013)

*Exergy analysis of the oil and gas processing on a North Sea oil platform a
real production day*, Energy 55, 716–727. doi:10.1016/j.energy.2013.03.017

| Claim to check | Value used | Used in |
|---|---|---|
| Separation train pressures, 4 stages | 70 / 29.2 / 7.9 / 1.8 bara (7 / 2.92 / 0.79 / 0.18 MPa) | `process.pressures.separators`; Methods §4 |
| Electric power demand of the platform | 18–26 MW | `validation.benchmarks.platform_power_voldsund`; Results §7 |
| Gas export pressure (if stated) | about 175–180 bar | `process.pressures.gas_export` |

**Checked.** The DOI is 10.1016/j.energy.2013.02.038. The real platform
has 3 stages at 70.4 / 8.50 / 2.80 bar (Table A), not 4 stages. Power:
about 34 MW for the whole platform and about 24 MW for processing (23.8 MW
electric). The 18–26 MW range was wrong. The benchmark is now 17–30 MW:
processing-plant power of the three oil platforms in Voldsund et al. (2014),
Table 5 (25, 30 and 17 MW). Platform A is the 2013 platform.

Notes:
* The pressures may be given in MPa or bar (gauge or absolute); record which.
* If the 18–26 MW is heat plus power, or gas turbine shaft power rather than
  electric power, note that. The benchmark compares electric demand.

## 2 Nguyen, Voldsund et al. (2013 and 2014)

* (a) Nguyen, T.-V. et al. (2013), *Exergetic assessment of energy systems on
  North Sea oil and gas platforms*, Energy. Volume and pages are missing in
  our reference list; please add them.
* (b) The 2014 four-platform comparison by Nguyen, Voldsund et al. (title,
  journal, volume and pages to add). Our separator pressures are cited
  "as reported in" this paper.

**Checked.** (a) is Energy 62, 23–36, doi:10.1016/j.energy.2013.03.011. Its
Table 1 gives the separation train at 7 / 2.9 / 0.72 / 0.18 MPa, which is the
real source of our 4-stage pressures; the config now uses 70 / 29 / 7.2 /
1.8 bara (design power changes by less than 0.01 %). Its gas export is
18.5 MPa. (b) is Voldsund et al. (2014), Energy 74, 45–58,
doi:10.1016/j.energy.2014.02.080. It confirms the last stage at 1.7–2.8 bar
and treated gas at 179 bar on platform D (Table 2).

| Claim to check | Value used | Used in |
|---|---|---|
| Platform power, six North Sea cases | 22.6–31.1 MW | `validation.benchmarks.platform_power_nguyen`; Results §7 |
| Last separation stage on all four platforms | 1.7–2.8 bar | source text of `process.pressures.separators` |
| Export / lift pressure on platform D | about 175–180 bar | `process.pressures.gas_export` |

## 3 Johan Castberg PDO, part II (impact assessment)

Equinor, *PUD Johan Castberg, del II: Konsekvensutredning* (2017).

| Claim to check | Value used | Used in |
|---|---|---|
| Average power demand | about 25 MW | `validation.benchmarks.platform_power_castberg`; Results §7 |
| Peak power demand | about 50 MW | same |

Note whether the figure is electric or total (heat plus power). Castberg is
an FPSO, so the comparison is only indicative.

## 4 Tanzania Finance Act, 2025

*The Finance Act, 2025* (Act No. 11 of 2025), TRA or Ministry of Finance PDF.

| Claim to check | Value used | Used in |
|---|---|---|
| Excise duty on carbon emissions: TZS 22,000 per tonne | NOK 0.09/kg CO2 (at 10.5 NOK/USD) | `economics.co2_price` (tanzania.yaml); Methods §10; comparison §4–5 |
| Applies to coal and natural gas | — | same |
| In force 1 July 2025 | — | same |
| **Per tonne of carbon or per tonne of CO2?** | read as CO2 | if per tonne of carbon, divide by 3.67, giving NOK 0.025/kg CO2 |
| **Who pays, and on what?** Gas supplied, gas burnt, or the emitter? | assumed to apply to fuel gas | if offshore fuel gas is exempt, the base should be 0 |
| Section number and schedule | — | for the citation |

CO2 results do not change in any of these cases, because the price does not
change the operation. Only the CO2 cost and total cost columns change.

## 5 Equinor (2014), Zafarani-2, and ESRF Discussion Paper 51

* Equinor (Statoil) press release, 3 March 2014, on the Zafarani-2 drill
  stem test.
* ESRF Discussion Paper 51, *Challenges ahead for Tanzania to build new
  capacities for gas*: the table of deepwater wells.

| Claim to check | Value used | Used in |
|---|---|---|
| Zafarani-2: 2,400 m water depth, 80 km from the mainland | site at 9.5° S, 40.5° E | `site.latitude/longitude` (tanzania.yaml); Methods §10 |
| Block 1 and 4 wells in 1,600–2,600 m water depth (Mzia about 1,620–1,640 m; Lavani, Zafarani, Tangawizi about 2,270–2,590 m) | "1000–3000 m" in the text | Methods §10 |
| Zafarani-2 tested at 66 MMscf/d (equipment-limited) | not used | optional context |
| Any gas composition, CO2/N2 content, reservoir pressure or temperature | not found; lean gas and 80 °C / 300 bara assumed | would replace assumptions in `process.gas` and `docs/verification/tanzania_process_check.py` |

The last row is the most valuable: any published value would turn an
assumption into a sourced number.

## 6 Coastal Tanzania wind study

*Wind patterns of coastal Tanzania* (University of Dar es Salaam repository,
<https://repository.udsm.ac.tz/items/2f0fb49f-1275-4710-b7f1-116e2bdf0264>).
It may also be published in the Western Indian Ocean Journal of Marine
Science (WIOJMS).

| Claim to check | Used in |
|---|---|
| Authors, year, journal, volume and pages | Methods references (currently "to be completed") |
| Mtwara is the windiest coastal station | Methods §10; comparison §1 |
| Wind maximum in June–July (south-east monsoon) | same |
| Weak winds from November to March | same |
| Measurement height and period (helps judge the ERA5 comparison) | optional |

## When done

Send the results (a marked-up copy of this file is fine), or upload the PDFs
in the chat, and the config, text and reference list will be updated to
match.
