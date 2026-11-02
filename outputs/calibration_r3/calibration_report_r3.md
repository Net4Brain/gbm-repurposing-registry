# Calibration report, round 3 — coding manual v1.3 (fresh records)

Date: 2026-11-02.
- **Records:** 20, never used in rounds 1–2 (`data/processed/calibration_set_r3.csv`, seed 20261102). These comprise:
  - 4 Early Phase 1;
  - 6 chosen for PK/PD wording;
  - 10 spread over phase and sponsor class.
- **Coders:** A = Claude Opus 5.5, B = Claude Sonnet 5.5; 2 batches of 10 each; fresh contexts.
- **Comparison:** `scripts/07_compare_coders_v2.py` checks every field against the 20-record manifest.

Files: `coderA/`, `coderB/`, `run_log.tsv` (one per coder), `adjudication_queue.csv` (81 rows, including 2 outcome-relevant biomarker rows added by the W6 check), `agreement.csv`.

## 1. Run integrity
- All 40 outputs were produced and validate against schema v1.3, and both run logs are complete (20 lines each).
- One Coder A file was rewritten after failing validation, which is allowed.
- **Deviation (Coder B, NCT07648823):** one quote was edited in place, rather than the file being rewritten, before the file validated. This is logged; it had no effect on coded values.
- **Quotes:** 2 non-verbatim quotes, both Coder B, both in NCT06613841. The schema caught no ellipses.
- **Registry data-quality note:** NCT07480941 describes itself in its own summary as "a draft, ClinicalTrials.gov-style example record". It is a CAR-NK trial and excluded at S6 either way, but the record is listed for the data-quality appendix.

## 2. Agreement before adjudication (n = 20, fresh records)

| Variable | % agree | κ | PABAK | AC1 |
|---|---|---|---|---|
| gbm_population | 90.0 | 0.85 | 0.88 | 0.88 |
| has_eligible_candidate | 100 | 1.00 | 1.00 | 1.00 |
| candidate_exclusion_reason | 100 | 1.00 | 1.00 | 1.00 |
| cns5_terminology | 100 | 1.00 | 1.00 | 1.00 |
| treatment_setting | 100 | 1.00 | 1.00 | 1.00 |
| regimen | 100 | 1.00 | 1.00 | 1.00 |
| basket | 100 | 1.00 | 1.00 | 1.00 |
| control_arm_from_other_arms | 85.0 | 0.72 | 0.78 | 0.80 |
| industry_support_in_text | **45.0** | 0.07 | −0.10 | 0.02 |
| tumour_pk_planned (new) | 95.0 | 0.84 | 0.93 | 0.94 |
| target_engagement_planned (new) | 95.0 | 0.91 | 0.93 | 0.93 |
| candidate_set | 95.0 | 0.94 | 0.95 | 0.95 |
| candidate_matched_selection | 100 | 1.00 | 1.00 | 1.00 |
| any_molecular_selection | 100 | 1.00 | 1.00 | 1.00 |

These are the first agreement figures on records the manual was **not** revised against. n = 20 is small, so they show that the manual transfers; they are not a precise estimate.

**Hidden disagreements in round 2.** The full-field comparison, run on the archived round-2 outputs, shows what the old script did not compare:
- `control_arm_from_other_arms` agreed in only 22.5% of round-2 records, before R8 defined it. In round 3 it reaches 85%.
- There were 40 biomarker-row and 12 agent-row differences. The methods review was right on this point.

## 3. Disagreement patterns in round 3

| # | Pattern (trials) | Effect on outcomes | Proposed fix |
|---|---|---|---|
| W1 | Radiopharmaceutical naming: `xt771` vs `[177lu]lu-xt771` (+ `[68ga]ga-xt771`) (NCT07648823) | Changes `candidate_set` text only; the same drug | Therapeutic radiopharmaceutical: `active_moiety` = INN if one exists, else ligand code without isotope; isotope goes in `drug_class_hint`. A paired diagnostic tracer form is listed separately as `diagnostic_agent`. |
| W2 | INN vs American name: phytomenadione vs phytonadione (NCT04752813); brand vs generic vaccine names (NCT07183371, NCT04201873) | None (supportive or excluded agents) | `active_moiety` uses the **INN spelling** (American spelling only for words that are not INNs). Excluded intervention types get a short generic name. The agent dictionary normalises names after coding in any case. |
| W3 | `industry_support_in_text`: 45% agreement | Descriptive variable only | **Decision A:** drop the LLM addition. `industry_involvement` uses only the structured sponsor and collaborator classes ([CODE]). |
| W4 | Glioblastoma named only as an expansion cohort in the summary (NCT05892653): A included, B excluded. The manual contradicts itself: the 1.1 table allows "a cohort", but C7 limits naming to conditions, title and inclusion criteria. | **Screening** | **Decision B:** glioblastoma counts if named in conditions, title, inclusion criteria **or a registered arm/group label**, but not if only in summary, description or keywords. NCT05892653 is then excluded unless an arm label names GBM. |
| W5 | "Grade 4 astrocytoma" without IDH status (NCT04430842): A coded HGG-unspecified, B not_glioblastoma; both exclude. The supplementary filter (D17) treats this phrase as a glioblastoma term. | **Screening** | **Decision C:** "grade 4/IV astrocytoma" or "grade 4/IV glioma" with no IDH requirement is the historical (WHO 2016) name for glioblastoma. Code it `gbm_only` or the mixed category, with `cns5_terminology: historical`. This matches D17, and the CNS5-only sensitivity analysis removes these trials. |
| W6 | Biomarker rows: eligibility vs enrichment for the same requirement (NCT05187624, NCT07480941); free-text `other` wording; pharmacodynamic vs exploratory roles | None for outcomes (eligibility and enrichment count the same; PD and exploratory roles don't count) | The comparison script should also report an **outcome-relevant** biomarker comparison, treating eligibility = enrichment and ignoring non-selection rows. The full comparison stays for transparency. |
| W7 | `tumour_pk_planned` and `target_engagement_planned`: unclear vs no/yes (2 trials) | Translational variables | Wording: `unclear` only when PK is planned and the sample type is not stated; a stated PD objective with paired biopsies = `yes`. |

## 4. Recommendation
- Apply W1, W2, W6 and W7 as wording and script fixes. Decide A–C. Then freeze **v1.4**, with a new freeze checksum file.
- A fourth calibration round is not needed:
  - none of W1–W7 changes candidate status or the primary outcome;
  - B and C each affected a single record;
  - the main-pass adjudication catches any remaining cases.
