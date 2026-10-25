# Parameter verification (step 5 follow-up)

Goal: replace assumed process and power-system parameters with published values
from Norwegian sources. Every value in `config/base_case.yaml` carries its
source; this note summarises what changed and why.

## Sources used

1. **LEOGO reference platform** – Svendsen, H.G. et al. (2023), *The Low Emission
   Oil and Gas Open reference platform – An off-grid energy system for renewable
   integration studies*, IET Energy Systems Integration, doi:10.1049/esi2.12085.
   Dataset: Zenodo 7373223. Values were read from the machine-readable
   specification in the open-source Oogeso repository
   (`github.com/oogeso/oogeso`, `tests/test_data/leogo_reference_platform.yaml`,
   MIT licence, SINTEF Energi). LEOGO is a hypothetical platform built on
   Norwegian Continental Shelf practice with industry input, and is designed
   for exactly this kind of wind-integration study.
2. **Voldsund et al.** – exergy studies of a real North Sea oil platform,
   including Voldsund, Ertesvåg, He & Kjelstrup (2013), *Exergy analysis of the
   oil and gas processing on a North Sea oil platform a real production day*,
   Energy 55:716–727. Separator pressures as reported in the four-platform
   comparison by Nguyen, Voldsund et al. (2014).
3. **Johan Castberg PDO part II (impact assessment)** – electrical demand of about
   25 MW average and 50 MW peak (via search summary; to confirm in the PDF).
4. **Hywind Tampen** – 88 MW (11 × 8 MW) floating wind farm, expected to supply
   about 35 % of the annual power demand of Snorre A/B and Gullfaks A/B/C.

PDO impact assessments give total power demand and emissions, but not
separator pressures, machine efficiencies or minimum-flow limits. Those come
from LEOGO and the Voldsund/Nguyen papers instead.

**Caveat:** the network environment used to build this model could not open
the PDF documents directly. LEOGO values were read from its data file; all
other numbers came from search-engine summaries of the documents. Check each
one marked "verify in original" against the paper before submission.

## What changed

| Parameter | Before | Now | Source |
|---|---|---|---|
| Separator pressures | 3 stages, 60/10/2 bara | 4 stages, 70/29.2/7.9/1.8 bara | Voldsund et al. (verify in original) |
| Gas export pressure | 180 bara | 180 bara (kept) | about 175–180 bar, Nguyen/Voldsund et al. (2014); LEOGO 200 bar → sensitivity |
| Oil export pressure | 100 bara | 50 bara | LEOGO |
| Water injection pressure | 250 bara | 250 bara (confirmed) | LEOGO |
| WI pump suction | 5 bara | 7 bara | LEOGO |
| Seawater lift Δp | 8 bar | 10.4 bar | LEOGO (incl. 40 m lift) |
| Compressor efficiency | 0.75 polytropic | 0.75 isentropic | LEOGO |
| Water pump efficiency | 0.75 | 0.75 (confirmed) | LEOGO |
| Oil export pump efficiency | 0.75 | 0.60 | LEOGO |
| Motor + drive efficiency | 0.95 | 1.0 (included above) | LEOGO convention |
| Base electric load | 5.0 MW | 3.5 MW | LEOGO (2.5 general + 1.0 air compressors) |
| Heat demand | not modelled | 3.0 MW thermal | LEOGO |
| Gas turbine | LM2500 class, 32 MW, 38 %, a = 0.25 | 21.8 MW, 34.7 %, a = 0.184, min 3.5 MW, 3 units | LEOGO fuel model (A = 2.35, B = 0.53) |
| GT heat recovery | – | 0.5 | LEOGO |
| Spinning reserve | – | 5 MW | LEOGO |
| CO2 factor | 2.34 kg/Sm3 (recalled) | 2.34 kg/Sm3 | LEOGO, citing Statistics Norway (SSB) 2016 |
| Wind farm | 2 × 15 MW | 2 × 15 MW base, sensitivity 1–4 turbines | LEOGO uses 32 MW wind |

## Not verified (no public source found)

- **Fluid composition** – LEOGO excludes the reservoir fluid; PDOs do not publish
  compositions. Our generic black oil gives GOR 179 Sm3/Sm3 and fuel gas LHV
  39.0 MJ/Sm3 (LEOGO uses 40 MJ/Sm3).
- **Compressor and pump minimum-flow limits** (70 % / 30 %) – no public value
  found; keep in the sensitivity analysis.
- Production turndown limit, ramp rates, injection deficit limit (step 5).

## Benchmark of total demand

| Source | Electric demand |
|---|---|
| This model, design point | 20.3 MW (+ 3 MW heat) |
| Voldsund et al. (2013), real North Sea platform | 18–26 MW electrical |
| Nguyen et al. (2013), modelled North Sea platforms | 22.6–31.1 MW |
| Johan Castberg PDO | about 25 MW average, 50 MW peak |
| LEOGO (gas-lift platform, higher GOR) | about 47 MW |

Specific power per consumer agrees with LEOGO where the duties are comparable:
water injection 0.277 m3/s → 8.97 MW in LEOGO vs 0.289 m3/s → 9.19 MW here
(same pressures and efficiency).
