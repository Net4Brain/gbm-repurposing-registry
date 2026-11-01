# Calibration report — coding manual v1.0

Date: 2026-11-01. Records: 40 (`data/processed/calibration_set.csv`, seed 20261101). Coders: A = Claude Opus 5.5, B = Claude Sonnet 5.5 (D18), 4 batches of 10 each, independent contexts.
Files: `coderA/`, `coderB/`, `adjudication_queue.csv` (246 rows), `agreement.csv`.

## 1. Run integrity
- All 80 outputs were produced and all pass the schema.
- Two process deviations, both by Coder B:
  - **Batch 3** edited one of its own outputs after it had validated (NCT02546102, `industry_support_in_text`). The instructions allow re-writes only to fix validation errors.
  - **Batch 1** used a helper script, and corrected one non-verbatim quote in its own file.
- Neither deviation crossed coders. Both are logged here.
- **Quotes:** 11 evidence quotes are not word for word. Most join text with "..." or rewrite list formatting. Fix: the prompt must forbid ellipses and paraphrase.

## 2. Agreement before adjudication (n = 40)

| Variable | % agree | Cohen's κ | PABAK | Gwet AC1 |
|---|---|---|---|---|
| gbm_population | 90.0 | 0.86 | 0.88 | 0.88 |
| has_eligible_candidate | 97.5 | 0.95 | 0.95 | 0.95 |
| candidate_exclusion_reason | 97.5 | 0.96 | 0.97 | 0.97 |
| cns5_terminology | 92.5 | 0.89 | 0.89 | 0.89 |
| treatment_setting | 92.5 | 0.88 | 0.90 | 0.91 |
| regimen | 95.0 | 0.92 | 0.93 | 0.93 |
| basket | 97.5 | 0.93 | 0.95 | 0.96 |
| candidate_set | 80.0 | 0.78 | 0.79 | 0.79 |
| candidate_matched_selection | 95.0 | 0.80 | 0.90 | 0.93 |
| any_molecular_selection | 87.5 | 0.75 | 0.75 | 0.75 |

**Uncertain flags:** 97 from each coder, across 37 of the 40 trials. That is too many to adjudicate at full scale, so the flag rule needs tightening (C9).

## 3. Disagreement patterns and proposed clarifications (manual v1.1)
These clarify how existing rules are applied (allowed at calibration). Items marked **DECISION** change scope and need XL's decision.

| # | Pattern (examples) | Proposed clarification |
|---|---|---|
| C1 | Monotherapy vs combination when the candidate is added to Stupp/TMZ (chloroquine, pamiparib, sintilimab, onfekafusp alfa, TNG456) | Agent `role` counts **investigational** agents only: one investigational agent = `experimental_monotherapy`, even on a standard backbone. Trial-level `regimen` counts all antitumour therapy, including the backbone. Worked examples added. |
| C2 | Non-drug interventions put in `agents` as candidates (CAR-T, NK cells, vaccines, PET tracer, MRI contrast) | Add two roles: `excluded_intervention_type` (cell/gene therapy, oncolytic virus, vaccine) and `diagnostic_agent` (tracers, contrast agents). They are listed for transparency and are never candidates. **Schema change.** |
| C3 | Partner drugs that patients already receive, or receive in every arm (dabrafenib + trametinib with hydroxychloroquine) | A drug patients were already on, or that every arm receives, is `soc_backbone`, even if it is not GBM standard of care. The trial's own investigational question decides the candidate. |
| C4 | Fixed-dose combinations not split (nabiximols) | Restate with an example: nabiximols → dronabinol + cannabidiol, each with `fixed_dose_combination: true`. |
| C5 | Name variants for the same agent (186RNL vs rhenium-186 nanoliposome; personalised vs personalized) | `active_moiety` = INN if one exists; otherwise the development code exactly as first registered, with the full name in `drug_class_hint`. American spelling. Names are mapped to moieties by script after coding. |
| C6 | Germline safety markers and prior-therapy mentions counted as molecular selection (HLA-B*5701, MGMT as prior-therapy history) | Record only **tumour** molecular biomarkers. Germline pharmacogenomic or safety markers (HLA, G6PD, DPYD) are not recorded. A biomarker counts as eligibility only if it is an entry requirement, not a description of history. |
| C7 | GBM named only in exclusions, keywords or outcomes; IDH-mutant-only "GBM" arms | Glioblastoma counts as "named" only in conditions, title or **inclusion** criteria (as in D17). A record enrolling only IDH-mutant tumours is `not_glioblastoma`, even if it has a "GBM" arm (historical label). |
| C8 | `cns5_terminology` historical vs unclear | `cns5` = requires IDH-wildtype or cites WHO 2021; `historical` = cites WHO 2016 or earlier, says "multiforme", or explicitly allows IDH-mutant GBM; otherwise `unclear`. |
| C9 | Too many uncertain flags | Flag `uncertain` only when the doubt could change screening (S5/S6), a candidate's role, or the primary biomarker outcome. Other doubts go in `coder_notes`. |
| C10 | Treatment setting for "advanced/refractory" basket trials | "After standard therapy", "refractory" or "progressive" = `recurrent`. |
| C11 | **DECISION — delivery-enabling agents.** Perflutren microbubbles for focused-ultrasound opening; ritonavir as a booster | v3 Methods counts these as candidate agents flagged delivery-enabling, so perflutren would count as **2a repurposing**, inflating the headline. **Recommend:** they are *not* candidates; they are reported separately, like established therapies. Needs a v3 amendment. |
| C12 | **DECISION — drug–device therapies.** 5-ALA photodynamic/sonodynamic therapy; focused ultrasound + carboplatin | **Recommend:** the drug is a candidate when the trial tests its antitumour effect, with a new flag `device_dependent`, plus a sensitivity analysis excluding these trials. Carboplatin delivered via focused ultrasound → candidate (2b) with `device_dependent`. |
| C13 | **DECISION — unspecified per-patient drug panels** (NCT05380349: up to 3 FDA-approved drugs chosen by a stem-cell drug screen) | **Recommend:** keep the trial; record one agent `unspecified_approved_panel`. Count it at trial level as repurposing-containing; exclude it from agent-level counts (no moiety). Report it separately. |

## 4. Lookup layer
v1.1 of `05_lookup_drugs.py` produced two errors on calibration agents, both fixed in v1.2:
- **Loose FDA ingredient matching:** "B7-H3 CAR-T cells" matched unrelated products, and aminolevulinic acid got a 1946 date.
- **Oncology flag from label wording:** dronabinol (chemotherapy-induced nausea) was flagged as an oncology drug, which would make it 2b instead of 2a.

v1.2 uses quoted ingredient matching and decides oncology status by ATC L01/L02; label wording alone triggers a human check. Earlier cache files are kept in `data/lookup/` and `data/lookup/v1.1/`.

## 5. Next steps
1. XL decides C11–C13.
2. Update the manual (v1.1), schema, prompt and the v3 Methods amendment.
3. Re-code the 40 calibration records with v1.1 to confirm the fixes.
4. Freeze v1.1, record its SHA-256, and register on OSF.
