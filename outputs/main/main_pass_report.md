# Main coding pass — report (manual v1.4)

Run: 2026-11-02 to 2026-11-03, after OSF registration (osf.io/gn8v5, D29).
- **Records:** 870 screening records (`manifest.txt`), in 87 batches of 10 (shuffled, seed 20261105).
- **Coders:** A = Claude Opus 5.5, B = Claude Sonnet 5.5. Each batch was coded in a fresh context, up to 10 at a time.
- **Comparison:** `07_compare_coders_v2.py`, checked against the manifest.
- **Prioritised queue:** `09_prioritise_queue.py`, a post-registration processing step that adds a priority and an escape-aware quote check without changing coded values.

## 1. Completeness and integrity
- 870/870 records from each coder. All 1,740 files validate against schema v1.4, and none is missing or unexpected.
- Interruptions: three usage-limit stops. Interrupted agents were resumed and told to keep validated files unchanged and code only the missing records.
  - Coder B batch 26: its report contradicted itself, so I checked the file timestamps. They confirmed nothing was overwritten.
- One skipped record: NCT05084430 (Coder B batch 45), coded on follow-up. Its run log holds an earlier wrong "ok" line as well as the correct line.
- Rewrites after a failed validation (allowed): a handful, mostly quotes over 300 characters.
- **Process deviations, none changing a coded value:**
  - Read-only quote checks with grep or inline Python, beyond the single allowed command: Coder A batches 2 and 3; Coder B batches 15, 31, 41, 43, 63, 64, 77, 79 and 81.
  - Edits before first validation: Coder B batches 4, 6, 83 and 85, and Coder A batch 72.
  - Malformed run-log blocks from zsh word-splitting: Coder A batches 22, 54 and 78. Each was followed by a correct block; drop the malformed lines when parsing.
  - Duplicate JSON key with the same value: NCT04608812 (Coder A).
  - Full arm text recorded instead of the arm label: NCT06161519, NCT07476794, NCT04766632 and NCT07067905 (Coder A); NCT06936046 (Coder B).
- **Quotes:**
  - 18 quotes are not word for word. 14 of them match once ClinicalTrials.gov backslash escapes are removed (733 of 870 inputs contain such escapes).
  - That leaves **4 genuinely non-verbatim quotes**.
- **Data quality:** NCT07480941 and NCT07551336 describe themselves as a "draft … example record" in their own registry text.

## 2. Agreement before adjudication (n = 870)

| Variable | % agree | κ | PABAK | AC1 |
|---|---|---|---|---|
| gbm_population | 93.9 | 0.91 | 0.93 | 0.93 |
| has_eligible_candidate | 98.3 | 0.97 | 0.97 | 0.97 |
| candidate_exclusion_reason | 96.2 | 0.94 | 0.95 | 0.95 |
| cns5_terminology | 90.0 | 0.84 | 0.85 | 0.85 |
| treatment_setting | 96.0 | 0.94 | 0.95 | 0.95 |
| regimen | 97.6 | 0.96 | 0.97 | 0.97 |
| basket | 96.7 | 0.85 | 0.93 | 0.96 |
| control_arm_from_other_arms | 93.4 | 0.88 | 0.90 | 0.91 |
| tumour_pk_planned | 95.2 | 0.80 | 0.93 | 0.95 |
| target_engagement_planned | 92.2 | 0.78 | 0.88 | 0.91 |
| candidate_set | 94.6 | 0.93 | 0.95 | 0.95 |
| **candidate_matched_selection (primary)** | **99.2** | **0.96** | 0.98 | 0.99 |
| any_molecular_selection | 96.8 | 0.93 | 0.94 | 0.94 |

**Inclusion (passing S1–S6 on the LLM-coded steps):**
- Coder A includes 367 trials and Coder B 363.
- Both include 355; they disagree on 20.
- These counts come before the structured-field steps (study type, start date, phase, age) are applied by code, so the analytic cohort will be smaller.

These are AI–AI agreement figures (reproducibility). Accuracy comes from the two-expert sample (D28).

## 3. Adjudication queue
`adjudication_queue_prioritised.csv` (2,749 rows) and `adjudication_summary.csv` (one row per trial):

| Priority | Meaning | Rows | Trials |
|---|---|---|---|
| 1 | Can change inclusion, candidate status or the primary outcome | 712 | 302 |
| 2 | Trial-level variable of a trial that either coder includes | 232 | 175 |
| 3 | Naming, regimen ID, arm labels, non-selection biomarker rows, or trials both coders exclude | 1,805 | 574 |

Many priority-3 rows are naming differences (for example brand vs INN) that the agent dictionary resolves. Priority-1 rows include every "uncertain" flag on screening, candidate status and primary-outcome biomarkers.

## 4. Recurring questions for one ruling each (they resolve many queue rows at once)
1. **Established GBM drug + focused-ultrasound BBB opening** (temozolomide, bevacizumab; e.g. NCT04614493, NCT06496971, NCT06329570, NCT04446416, NCT07179328): the coders split between device-dependent candidate (C12) and established-therapy experiment (rule 6).
2. **Imaging-assessed target expression as an entry requirement** (SSTR, GRPR, PSMA, CA IX or integrin PET paired with a matched radioligand; e.g. NCT05283330, NCT05739942, NCT06607692, NCT05278208): does it count as candidate-matched molecular selection (primary outcome)?
3. **Prodrugs of a gene or cell suicide therapy** (5-FC, valganciclovir, valaciclovir, Toca FC, DB107-FC): candidate, or part of the excluded therapy?
4. **Cytokines and adjuvants given with a cell therapy or vaccine** (IL-2, IL-15, GM-CSF/sargramostim, poly-ICLC, imiquimod, IL-12): candidate, or part of the excluded therapy?
5. **Botanical, supplement or medical-food products with an antitumour hypothesis** (IV liposomal curcumin, Salovum, elemene, oxaloacetate, silibinin, CBD extract, zinc/ascorbate): candidate or excluded type?
6. **Chemosensitiser / potentiator** (O6-benzylguanine with temozolomide): candidate in its own right?
7. **"WHO grade 3–4 glioma" / "high-grade glioma" with grade 4 allowed but glioblastoma not named**: D27C (historical glioblastoma) or high-grade glioma unspecified? The coders applied D27C inconsistently.
8. **Drug-screen or genomically assigned therapy with no drugs named** (ex vivo screens, ctDNA-guided panels): an unspecified approved panel (C13) or no candidate?
