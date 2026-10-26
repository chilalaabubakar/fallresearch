# Verification of the Tanzania assumptions

Status after the review of the 50 parameters that `config/tanzania.yaml`
marked `ASSUMPTION` (including those inherited from `base_case.yaml`). Now
43 of 115 carry the tag:

| Group | Count |
|---|---|
| Inherited North Sea values the gas platform never uses | 10 |
| Shared with the North Sea case | 11 |
| Specific to Tanzania | 22 |

Sources had to be found through web search summaries; the original documents
(Finance Act text, KPMG brief, ESRF paper) could not be opened from this
environment, so the items marked *confirm* should be checked against them.

## 1 Verified or derived from published sources

| Parameter | Value | Basis |
|---|---|---|
| `site.latitude/longitude` | 9.5° S, 40.5° E | Zafarani-2 (Block 2) tested in 2,400 m water depth, 80 km from the mainland (Equinor, 2014); Block 1 and 4 wells lie in 1,600–2,600 m (ESRF Discussion Paper 51). The ERA5 point is about 80 km off Lindi. Exact well coordinates are not public. |
| `process.gas.design_gas_rate` | 10 MSm³/d | Tanzania LNG is planned at up to 10 Mtpa (Wikipedia; TanzaniaInvest). That needs about 40 MSm³/d of feed gas, so one platform supplying a quarter gives 10 MSm³/d. The split between platforms is a modelling choice. |
| `gas_turbine.ambient.power_derate_per_K` | 0.7 %/K | Literature range 0.5–0.9 %/K above ISO; a hot coastal site at 40 °C keeps 82–88 % of ISO output (USPE). |
| `economics.co2_price` | NOK 0.09/kg (base) | **Changed fact:** the Finance Act 2025 (in force 1 July 2025) added an excise duty of TZS 22,000 per tonne of carbon emissions from coal and natural gas, about US$8.4/t or NOK 0.09/kg (Bloomberg Tax; KPMG Budget Brief 2025/26). *Confirm* in the Act whether it applies to fuel gas burnt offshore and whether "tonne of carbon" means CO2. Used as the base case; zero to NOK 2/kg is tested as a sensitivity, which shows the price does not change the operation. The 10.5 NOK/USD rate is an assumption. |

## 2 Calculated (plausibility check with NeqSim)

The script is `docs/verification/tanzania_process_check.py`. It takes water
contents from NeqSim (CPA) for the process gas and uses textbook design rules
for the glycol units.

| Parameter | Before | Now | Check |
|---|---|---|---|
| `teg_heat` | 1.5 MW | **0.5 MW** | The gas holds 252 mg/Sm³ of water at 70 bara and 15 °C (590 mg/Sm³ at 30 °C), which agrees with the McKetta chart. Drying to 65 mg/Sm³ with 3–7 US gal TEG per lb of water (Kimray; Cimarron) needs a 0.17–0.85 MW reboiler. |
| `meg.regeneration_heat` | 3.0 MW | **1.0 MW** | Water condensed between the reservoir and the platform is 350–1,460 kg/h for a reservoir of 60–100 °C and 250–350 bara (no published values). Boiling it off with 30 % reflux and heating 45 wt % rich MEG needs 0.4–1.5 MW. Formation water would add about 1 MW per 25 m³/d; it is excluded (early life). |
| `meg.injection_pumps` | 0.5 MW | **0.05 MW** | 350–1,460 kg/h of 90 wt % lean MEG at about 330 bar head needs only 2–11 kW, even without credit for the 2,400 m hydrostatic column. 0.05 MW allows for minimum-flow recirculation. This is a must-run load, so it lowers platform demand in every hour. |

Checked but kept as assumptions:

* `pipeline.inner_diameter` 0.6 m: 2.4 m/s and 6.8 bar of friction over
  100 km at design rate, a normal design. The real pipeline size is not
  public.
* `pipeline.min_pressure` 110 bara: at full flow the gas still reaches shore
  at about 75 bara, after 6.8 bar of friction and 28.6 bar to lift the gas
  2,400 m from the seabed. The pressure the LNG plant needs is not public.
* `meg.regeneration_electric` 0.3 → 0.1 MW: pumps and air-cooler fans, about
  10 % of the new heat duty.
* `arrival_temperature` 15 °C: lies between seabed temperature (about
  2–4 °C, not verified) and a warmer arrival from a short tie-back. It
  depends on where the hypothetical platform sits.

## 3 No public data – remain assumptions

No published gas analysis, reservoir pressure or temperature, or facility
design exists for Blocks 1, 2 and 4. These are design choices for a
hypothetical platform:

* gas and fuel composition, and the condensate (TBP) fractions;
* arrival, stabiliser and export pressures, the maximum pipeline pressure,
  and the pipeline gas temperature;
* gas cooler outlet temperature, seawater temperature rise, and the 0.5 MW
  of utility heat;
* minimum flows of the condensate pump and the MEG regeneration unit;
* production limits (50–110 %), MEG regeneration target (80 %) and ramp
  rate, and the 48 h rich-MEG tank;
* gas turbine efficiency derating of 0.1 %/K (no source found).

## 4 Inherited from the North Sea case

* **Shared and used** (reviewed in `docs/parameter_verification.md`): wind
  farm wake loss, electrical loss and availability; GT low-load threshold;
  minimum flows of the export compressor and seawater lift pump; production
  ramp rate; at least one GT online; electric heater efficiency; and the
  small GT rating, which is used only in the fleet sensitivity.
* **Not used by the gas platform:**
  - North Sea reservoir fluid and heavy ends;
  - oil rate, water cut, water injection rate, well temperature;
  - minimum flows of recompression, the oil export pump and the water
    injection pump;
  - `gas_turbine.min_units_running`, which no code reads.

## Sources

* Equinor (2014), Zafarani-2 drill stem test; Offshore Source, *Statoil's
  Zafarani reservoir in Tanzania Block 2 successfully tested*.
  <https://offshoresource.com/news/oil-gas/statoil-s-zafarani-reservoir-in-tanzania-block-2-successfully-tested>
* ESRF Discussion Paper 51, *Challenges ahead for Tanzania to build new
  capacities for gas* (table of deepwater wells and water depths).
  <https://esrf.or.tz/docs/DiscussionPaper-51_final.pdf>
* Tanzania Liquefied Natural Gas Project (Wikipedia); TanzaniaInvest, *Gas in Tanzania*.
  <https://en.wikipedia.org/wiki/Tanzania_Liquefied_Natural_Gas_Project>,
  <https://www.tanzaniainvest.com/gas>
* The Finance Act, 2025 (Tanzania), carbon excise duty; Bloomberg Tax,
  *Tanzania Parliament considers 2025 Finance Bill*; KPMG, *Tanzania
  2025/2026 Budget Brief*.
  <https://www.tra.go.tz/images/uploads/acts/THE_FINANCE_ACT,_2025.pdf>,
  <https://news.bloombergtax.com/daily-tax-report-international/tanzania-parliament-considers-2025-finance-bill>,
  <https://assets.kpmg.com/content/dam/kpmg/ke/pdf/tax/2025/Tanzania_2025_2026_Budget_Brief.pdf>
* USPE, *Gas turbine derating: how heat and altitude slash power output*.
  <https://uspeglobal.com/?p=246577>
* Kimray, glycol circulation rate; Cimarron, *Dehydration design data form
  guidance* (2–7 gal TEG per lb water).
  <https://kimray.com/node/1355>,
  <https://cimarron.com/wp-content/uploads/2025/05/Dehydration-Design-Data-Form-Guidance-Cimarron-Rev-2.pdf>
