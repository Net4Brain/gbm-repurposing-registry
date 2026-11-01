# Calibration report, round 2 — coding manual v1.1

Date: 2026-11-01. The same 40 records as round 1 (`data/processed/calibration_set.csv`, seed 20261101) and the same batches were re-coded with manual v1.1 (`coding_manual_v1.1.md`), schema v1.1 and prompt v1.1. Coders: A = Claude Opus 5.5, B = Claude Sonnet 5.5 (D18), 4 batches of 10 each, in fresh independent contexts. Neither coder could read round-1 outputs.
Files: `coderA/`, `coderB/`, `adjudication_queue.csv` (39 rows), `agreement.csv`.
Command: `python3 scripts/07_compare_coders.py outputs/calibration_r2 schema/trial_coding.schema.v1.1.json`

## 1. Run integrity
- All 80 outputs were produced and all pass schema v1.1.
- No file was changed after it validated. Neither coder used a helper script; both round-1 deviations are gone.
- One Coder A file (NCT04712721) failed validation on its first write and was rewritten once, as the instructions allow.
- **Quotes:** 0 non-verbatim evidence quotes (round 1: 11).
- **Sonnet misreads the schema.** Two Coder B batches wrongly reported that `coder_notes` is not allowed (it is: tested), so 20 of 40 B files have no `coder_notes`. Those doubts went into the per-item `flag.reason` fields instead. No coded value is affected. Fix: one sentence in the prompt (R7).

## 2. Agreement before adjudication (n = 40), round 1 vs round 2

| Variable | κ round 1 | % agree round 2 | κ round 2 | PABAK | Gwet AC1 |
|---|---|---|---|---|---|
| gbm_population | 0.86 | 100.0 | 1.00 | 1.00 | 1.00 |
| has_eligible_candidate | 0.95 | 100.0 | 1.00 | 1.00 | 1.00 |
| candidate_exclusion_reason | 0.96 | 100.0 | 1.00 | 1.00 | 1.00 |
| cns5_terminology | 0.89 | 97.5 | 0.96 | 0.96 | 0.96 |
| treatment_setting | 0.88 | 97.5 | 0.96 | 0.97 | 0.97 |
| regimen | 0.92 | 92.5 | 0.88 | 0.89 | 0.89 |
| basket | 0.93 | 97.5 | 0.93 | 0.95 | 0.96 |
| candidate_set | 0.78 | 97.5 | 0.97 | 0.97 | 0.97 |
| candidate_matched_selection | 0.80 | 97.5 | 0.88 | 0.95 | 0.97 |
| any_molecular_selection | 0.75 | 97.5 | 0.95 | 0.95 | 0.95 |

**Uncertain flags:** 24 queue rows across 12 trials (round 1: 194 rows across 37 trials). The C9 rule worked.

The 40 records are the ones the manual was revised against, so these figures are an upper bound. Accuracy on new records comes from the blinded human validation sample (D15).

## 3. D19 rules in practice (both coders agreed on every item below)
- **C11 delivery-enabling agents:** perflutren (NCT04440358) and sulfur hexafluoride microbubbles (NCT07385846) were coded `delivery_enabling_agent`. Ritonavir in NCT06428045 was coded a candidate, because the record gives it no boosting purpose; that is correct under rule 2b.
- **C12 drug–device:** 5-ALA photodynamic/sonodynamic therapy (NCT04391062, NCT06665724) and focused-ultrasound carboplatin (NCT04440358) were coded as candidates with `device_dependent: true`.
- **C13 panel:** NCT05380349 was coded `unspecified_approved_panel`. Note: this trial is Early Phase 1, so it is excluded at S3 (D8) anyway; the rule still matters for the main pass.
- **C2 new roles:** all CAR-T/NK cells, vaccines and oncolytic viruses were coded `excluded_intervention_type`, and all tracers and contrast agents `diagnostic_agent`, by both coders.

## 4. Remaining disagreement patterns → proposed wording fixes (v1.2)
None of these changes a definition. None changes which agents are candidates, except R5, where both coders already agree.

| # | Pattern (trials) | Proposed wording |
|---|---|---|
| R1 | `regimen` for trials with no candidate: `not_applicable` vs `monotherapy` (NCT04467346, NCT05071846) | `regimen` = `not_applicable` whenever `has_eligible_candidate` is false |
| R2 | An established therapy given in every arm, with its schedule varied between arms: `soc_backbone` vs `established_therapy_experiment` (temozolomide NCT03914742, lomustine NCT05304663) | Rule 6 comes before C3: if the established therapy's own dose, schedule or route differs between arms or is named as the question, it is `established_therapy_experiment` |
| R3 | Components of one fixed-dose combination product: `experimental_combination` vs `experimental_monotherapy` (nabiximols, NCT05629702) | Components of one investigational product count as one agent for the role: each component is `experimental_monotherapy` if that product is the only investigational one |
| R4 | `device_dependent` for a drug given with focused-ultrasound BBB opening (pembrolizumab, NCT07385846: A true, B false) | `device_dependent: true` whenever the record pairs the drug with device-enabled delivery or activation, whether or not the antitumour need is stated |
| R5 | C3 vs C12 conflict (carboplatin NCT04440358: patients enter already planned for carboplatin) | When the trial's question is device-enabled delivery or activation of a drug, that drug is the candidate (C12 overrides C3) |
| R6 | Lymphodepleting chemotherapy before cell therapy (cyclophosphamide, NCT04489420: listed by A only) | Conditioning or lymphodepleting chemotherapy for a cell therapy = `supportive`, listed |
| R7 | Sonnet believes `coder_notes` is disallowed | Prompt: "`coder_notes` is a top-level field; use it." |
| R8 | `control_arm_from_other_arms` used inconsistently (coders' own reports; not compared by script) | `not_applicable` = single-arm; `no` = multi-arm with no OTHER-type control |
| R9 | Agents not registered as interventions but mentioned in the text (C-11 methionine PET, temozolomide implied by "Stupp") | List agents that are registered interventions or that the protocol text says every patient receives |

Single disagreements without a pattern: `basket` and the durvalumab role in NCT04521686 (excluded at S5 anyway); `cns5_terminology` NCT04962672; `treatment_setting` NCT05835687 (excluded at S6); SEZ6 as a biomarker for ABBV-706 (NCT05599984, link inferred, not stated). These go to adjudication as normal.

## 5. Recommendation
- Agreement on every screening variable and on candidate selection is ≥ 0.97 (κ).
- The primary outcome (`candidate_matched_selection`) reaches 97.5% agreement, κ 0.88, AC1 0.97.
- Non-verbatim quotes are eliminated, and uncertain flags dropped by 88%.

Recommend adding R1–R9 as a **v1.2 wording update** without a third calibration round, because none affects screening or candidate status. Then freeze v1.2, record its SHA-256 and register on OSF. Re-coding the same 40 records a third time would mostly measure overfitting to them; the D15 human sample is the real test.
