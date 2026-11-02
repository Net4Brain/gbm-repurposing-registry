# OSF preregistration — draft text, version 2

Supersedes `OSF_preregistration_draft.md` (kept for the record), following the methods review of 2026-11-02 (decisions D20–D27, coding manual v1.4).

**Template:** OSF "Preregistration Template for Secondary Data Analysis" (Van den Akker et al., *Meta-Psychology* 2021). Paste each section into the field with the same heading; if your form's wording differs, match by meaning.
**Embargo:** private, embargo up to 4 years.
**Frozen materials:** GitHub `Net4Brain/gbm-repurposing-registry`, commit **`903dc98fe435219759e6e49a0c0e01ce7c3e3555`** (2026-11-02), uploaded to the OSF project as `gbm-repurposing-registry_903dc98.zip`. The freeze checksums are in `FROZEN_v1.4.sha256`, listed under Codebook below.

---

## Study information

### Title
Repurposed drugs in the contemporary glioblastoma clinical trial landscape: a registry-based cross-sectional analysis

### Authors / contributors
Xinzhong Li (Teesside University) — *[add co-authors only if they agree to be listed now]*

### Description
- **Design.** A registry-based cross-sectional study of interventional adult glioblastoma drug trials on ClinicalTrials.gov that started between 1 January 2020 and 31 July 2026, **as documented in the 1 November 2026 registry snapshot**.
- **Classification.** Each candidate agent in an experimental role is classified by origin relative to the start date of its trial, from a human-reviewed table of **dated** FDA/EMA approval events and dated prior development:
  - approved-drug repurposing, split into non-oncology (2a) and oncology (2b);
  - investigational repositioning;
  - operational de novo development.
- **Measures.** The study measures:
  - the share of the pipeline that is repurposing;
  - how candidate-matched molecular selection and planned translational measurements (tumour drug exposure, target engagement) differ between repurposing-containing and de novo-only trials.
- **Interpretation.** Comparisons describe registered development practice; they do not estimate treatment effectiveness or causal effects of drug origin.

### Hypotheses
- **H1 (prespecified comparison).** Repurposing-containing trials use candidate-matched molecular selection less often than de novo-only trials.
  - **Estimand:** the trial-level risk difference (de novo-only minus repurposing-containing), one row per trial.
  - **Reporting:** the estimate with its 95% CI.
  - **Practical importance:** a difference of **≥ 10 percentage points** is prespecified as practically important. The paper will state whether the CI excludes 0 (direction) and whether it excludes 10 (magnitude).
  - No supported/qualified/not-supported label is used (D22).
- **Descriptive aim (no test).** The proportion of unique candidate agents that are approved-drug repurposing, overall and for 2a/2b, with the dated tumour-agnostic flag. A headline estimate that changes by more than 5 percentage points across the prespecified sensitivity analyses is reported as definition-dependent.

---

## Data description

### Datasets used
1. **ClinicalTrials.gov full records**, API v2, retrieved 2026-11-01 as frozen JSON:
   - main `ctgov_raw_20261101T130137Z.json` (SHA-256 `f09ed81bd69918c7560209c341fe9201325fa9ab894ff65f453036ae960c3e7e`, 834 records);
   - supplementary `ctgov_supp_raw_20261101T150223Z.json` (SHA-256 `8665982d6e81c0897ef3c1e3b64a6cef0dc37c282fb6edffd33ef1507b87d7b9`).
2. **EMA medicines report** `EMA_medicines_report_20261101.xlsx` (SHA-256 `4756d6fac5904e9dc1d6a0880d4e494aa1ef46d52a8972b17d8a22fb52eb678b`).
3. **Dated regulatory events** (`data/reference/regulatory_events.csv`). One row per FDA/EMA approval event, from:
   - Drugs@FDA approval history and letters;
   - FDA label history;
   - EMA EPAR procedural steps.

   Each row records: indication, oncology / tumour-agnostic / glioma flags, approval date (with interval when only month or year is known) and source. Every row that affects a classification is human-reviewed. Current openFDA, EMA and ChEMBL data are discovery aids only.
4. **Dated prior development** (`data/reference/development_events.csv`). Earliest non-glioblastoma Phase 1/2/3 trials or publications per agent, with dates and sources, human-reviewed.
5. **ReDO_Trials_DB** (Pantziarka et al., 2021). Frozen copy (SHA-256 `00b3113d0fb0fd0ffd24b6c5323b25307002b3cc5c2945a80f47f25aa208197d`), used for external validation only.
6. **AACT archive** dated **on or before** 2026-07-31. Used only to reconstruct recruitment status on the index date for the active subset.

### Availability and access
- **Public domain:** ClinicalTrials.gov and openFDA.
- **ChEMBL:** CC BY-SA 3.0.
- **EMA:** reusable with acknowledgement.
- **ReDO_Trials_DB:** no licence is stated, so it is not redistributed; a script fetches it and verifies the checksum, and it is required for calibration sampling.
- **AACT:** free registration.

### Data collection procedures
- **Main search.** Union of a condition-field search and a free-text search, using the terms glioblastoma, GBM, glioblastoma multiforme, gliosarcoma, malignant glioma, high-grade glioma, grade 4 glioma. Restricted to interventional studies with start date 2020-01-01 to 2026-07-31. Result: 834 records.
- **Supplementary search.** CNS5 terms, brain-tumour condition terms, and glioblastoma in the eligibility criteria. It returned 833 records not in the main pull.
  - A scripted rule (`scripts/02b_filter_supplementary.py`) admits a record if a glioblastoma term appears in the title, conditions or inclusion criteria. This admitted 36 records.
  - An audit of the 797 rejected records found none naming glioblastoma or a synonym in those fields.
- **Screening set:** 870 **screening records** (not eligible trials).

### Codebook
- **Coding manual v1.4 (frozen):** `coding_manual_v1.4.md`. **Schema:** `schema/trial_coding.schema.v1.4.json`. **Decision log:** `protocol_decisions.md` (D1–D27).
- **`FROZEN_v1.4.sha256`:**
  - manual `ec273702f60e655ebe16dae72b2099fd64cf1649aa38bb23d874963cfdfa69fd`
  - schema `07f70d11fc7146734b4b696f3520c6edc99bccb93de7c72b7f2058d9a9b1b9df`
  - coder prompt `e0ffef6ed67e747311527f27e189e0c92d7359e309eb49349a6c25f14c9f2cd1`
  - agent instructions `ee9c9a10e03d9c2967c89ba10dec10d8e34357f65aef111cec54feb2384df8dc`
  - decision log `9af59c4a8ca2c2adcb76381946ca2e570d2b6bb1ad1996d2ca5deaa7c8c5e67e`
  - origin rules `06_derive_origin_v2.py` `bb35f764176f7edaf3dcc3340b6bb55b10c174f676aead300377e0dab297dc2c`
  - comparison `07_compare_coders_v2.py` `9b1cb159763ae811cc2efa5a1dda2bf42913dfa0e97f1151d3bd028ea1c07b5c`
  - validation sampling `08_draw_validation_sample.py` `540d92fcdfeacda401266ff55a97318a259cb479a46298cc194d0acf4528ddfb`
  - plus scripts 02b, 03, 04b, 05 and the origin-rule tests (in the file).

---

## Variables

### Eligibility (screening, in order; first failure = exclusion reason)
1. **Study type:** interventional.
2. **Start date:** 2020-01-01 to 2026-07-31, actual or anticipated.
3. **Phase:** Phase 1, 1/2, 2, 2/3 or 3. Early Phase 1 (Phase 0), Phase 4 and "not applicable" are excluded from the primary estimand. Early Phase 1 records are coded and reported separately as a **translational subset**.
4. **Age:** adults eligible. Paediatric-only trials are excluded; mixed-age trials are flagged.
5. **Population:** adult glioblastoma is a target population.
   - **Where it must be named:** in the conditions, title, inclusion criteria or a registered arm/group label. A mention only in the summary, description, keywords, outcomes or exclusions does not count.
   - **Historical naming:** "grade 4/IV astrocytoma/glioma" without an IDH requirement counts as historical glioblastoma terminology.
   - **Included and flagged:** mixed-glioma and basket trials that name glioblastoma.
   - **Excluded:**
     - "high-grade/malignant glioma" without naming glioblastoma;
     - IDH-mutant-only trials;
     - anti-GBM (renal) disease.
6. **Candidate:** at least one pharmacological antitumour candidate in an experimental role.
   - Included: small molecules, biologics and radiopharmaceuticals.
   - Excluded: cell and gene therapy, oncolytic viruses, vaccines, devices alone, radiotherapy, surgery, diets and unlicensed supplements.
7. **Withdrawn trials** are reported separately.

### Intervention role (per drug–trial pair, with registered arm labels)
Roles:
- experimental monotherapy;
- experimental combination;
- standard-of-care backbone;
- control/comparator;
- supportive;
- established-therapy experiment;
- delivery-enabling agent;
- excluded intervention type;
- diagnostic agent.

**Candidates** are the experimental monotherapy and combination agents only. The flags are delivery-enabling, device-dependent, radiopharmaceutical, formulation and fixed-dose combination.

### Drug origin (per candidate; T = trial start date; only events dated on or before T count)
- **ESTABLISHED** (temozolomide, carmustine, lomustine, bevacizumab): reported separately.
- **GLIOMA_DEVELOPED:** the earliest FDA/EMA approval event is a glioma treatment indication. Reported separately.
- **2a:** approved at T, no oncology approval at T.
- **2b:** approved at T, with an oncology approval at T.
- **3:** unapproved at T, but Phase ≥ 2 in a non-glioblastoma indication before T.
- **1 (operational de novo):** unapproved at T and no Phase ≥ 2 non-glioblastoma development before T.
- **UNRESOLVED:** evidence missing or unreviewed. The analysis does not run while any remain.

**Dated flags on category 2:**
- `tumour_agnostic_at_T`;
- `population_within_label` (the trial population and regimen already fall within an approved indication at T; a human decision);
- `glioma_label_at_T`.

**Date intervals.** Month- or year-only dates are intervals. Classifications that change within an interval are flagged `date_sensitive`, and the conservative result is used.

**Two axes reported per candidate:** regulatory status at T, and highest prior non-glioblastoma phase at T.

**Unspecified approved-drug panels** count as category 2 at trial level only.

### Trial-origin groups
- **Repurposing-containing:** ≥ 1 category-2 candidate.
- **Repurposing-2a-containing.**
- **De novo-only:** only category-1 candidates.
- **Repositioning-only.**
- **Mixed-origin:** category 2 plus category 1.

### Outcomes
- **Primary:** candidate-matched molecular selection.
  - Qualifying biomarker: a tumour biomarker required for eligibility or enrichment and mechanistically linked to a candidate. The coders record the matched agent.
  - Not qualifying: IDH-wildtype status and MGMT status (unless the candidate targets MGMT); germline markers are not recorded.
- **Secondary:**
  - any molecular eligibility/enrichment requirement;
  - molecularly informed design;
  - `tumour_pk_planned` (candidate concentration measured in tumour tissue or CSF);
  - `target_engagement_planned` (a pharmacodynamic/target-modulation measurement).

  There is no composite score.
- **Descriptive:**
  - phase group;
  - lead sponsor class and industry involvement (structured fields only);
  - enrolment;
  - countries and region;
  - treatment setting;
  - regimen;
  - randomisation and control arm;
  - CNS5 vs historical terminology;
  - primary mechanism category;
  - the flags above.

---

## Knowledge of data (full disclosure)

Before this registration, the following were seen:
- **Record counts:** 834 main; 833 supplementary, of which 36 were added; 870 screening records.
- **ReDO overlap:** 85 CNS-tumour trials in ReDO, 28 of them in the main pull.
- **Calibration** (manual development; records are re-coded in the main pass under v1.4):
  - Round 1 (v1.0) and round 2 (v1.1): the same 40 stratified records (seed 20261101), coded by both LLM coders.
  - Round 3 (v1.3): 20 different records (seed 20261102).
  - Inter-coder agreement was examined for all coded variables, including the outcome variables. Disagreements were used to revise the manual wording.
  - Scope decisions are recorded as D19 and D27.
- **Drug lookups:** current FDA/EMA/ChEMBL lookups for the 56 candidate moieties named in the round-1/2 calibration records, used to debug the lookup script.
- **Supplementary audit:** the rejected supplementary records were text-screened for glioblastoma terms (see the filter audit).
- **Independent review:** a methods and reproducibility review (2026-11-02) of the protocol and code; its recommendations were adopted as D20–D26.

The following has **not** been done:
- No drug-origin category has been assigned to any trial.
- No regulatory event table entries exist yet.
- No cross-tabulation of drug origin against any outcome, or any comparison relevant to H1, has been computed.

---

## Analyses

### Extraction, adjudication and human review
**Coders.**
- Coder A = Claude Opus 5.5 (`claude-opus-5-5`); Coder B = Claude Sonnet 5.5 (`claude-sonnet-5-5`).
- Each codes every record independently, in fresh contexts of 10 records, using the identical frozen prompt.
- Each batch writes a run log (model, record, time).
- Structured fields are extracted by code.

**Comparison.** `07_compare_coders_v2.py` compares every coded field, plus an outcome-relevant biomarker check, against the 870-record manifest. Every disagreement and every uncertain item is adjudicated by XL, with reasons recorded.

**Agreement.** Reported before adjudication as Cohen's κ with PABAK and Gwet's AC1. This measures reproducibility, not correctness.

**Human review, all before any analysis (D21):**
- **Correction:** XL reviews **every** unique candidate's origin (evidence sheet per agent) and **every** positive candidate-matched selection decision, blinded to drug origin. Ambiguous cases go to a second expert (clinical co-author).
- **Measurement:** `08_draw_validation_sample.py` (seed 20261103) draws AI-agreed negatives, never calibration records, which XL codes blind to AI output:
  - 30 exclusions;
  - 15 included trials with non-matched selection biomarkers only;
  - 25 included trials with no selection biomarker.

  Results are reported as confusion matrices with sensitivity, specificity, PPV and NPV (95% CIs) and stratum weights.
- **Escalation:** if the weighted rate of clinically important misses (an eligible trial excluded, or a candidate-matched selection missed) exceeds 5% for a variable, every record is human-coded for that variable.

**External checks.**
- The proportion of eligible ReDO-listed trials coded repurposing-containing (exact 95% CI).
- 30 random de novo agents checked against regulatory and ChEMBL records.

### Statistical models
- **Census framing.** Proportions are census values for the defined registry cohort. 95% CIs (Wilson for proportions, Newcombe for differences) are interpreted under a stated working model: trials as realisations of an ongoing development process. They do not capture registry undercoverage or classification error.
- **H1 analyses:**
  1. **Primary:** crude risk difference, one row per trial, with Newcombe 95% CI.
  2. Selection rates by primary mechanism × origin.
  3. Composition-standardised risk difference over phase group (P1/P2/P3), treatment setting, calendar period (2020–22 / 2023–24 / 2025–26) and primary mechanism. Computed only over strata with both groups present, with sparse strata reported, not modelled. Sponsorship is **not** adjusted for.
  4. Candidate-specific version: a repurposing-containing trial counts as selected only if a biomarker is matched to its repurposed candidate.
  5. Single-candidate trials only.
  6. Leave-one-dominant-agent-out, for the 5 agents with the most trials.
  7. Repeat with repurposing-2a-containing trials as the exposure.
- **Agent level:** the proportion of agents tested in at least one candidate-matched trial. The opportunity bias (agents with more trials have more chances) is disclosed.
- **Overlap:** shared agents between trials are described. A multiple-membership model is fitted only if numbers allow, and is labelled exploratory.
- **Misclassification:** a probabilistic bias analysis for origin and selection uses the validation sensitivity and specificity.
- **Small cells:** if expected cell counts are below 5, exact methods are used and phase collapses to early vs later.
- **Exploratory comparisons** (phase, sponsorship, setting, regimen, randomisation, control arm, tumour PK, target engagement): effect estimates with CIs; any P values are descriptive and unadjusted.
- **Software:** R 4.5.2 and Python 3.13.

### Effect size
Risk difference in percentage points; ≥ 10 points is practically important.

### Statistical power
Not applicable: a census of all eligible records.

### Inference criteria
Estimates and 95% CIs as described under H1. No multiplicity adjustment for the single prespecified comparison.

### Data exclusion
Eligibility rules only.

### Missing data
Values the registry does not determine are coded "unclear" and reported as their own category, never imputed. UNRESOLVED origins block the analysis until adjudicated. Trials whose status cannot be reconstructed are reported separately.

### Sensitivity analyses (prespecified)
1. Categories 2 + 3 combined.
2. Exposure restricted to 2a, excluding agents with `tumour_agnostic_at_T`.
3. Origin judged at the index date (2026-07-31).
4. Glioblastoma-only populations.
5. Exclude basket trials.
6. Exclude mixed-origin trials.
7. Count each multi-drug repurposing regimen once.
8. Include Early Phase 1 trials.
9. Actual start date only.
10. CNS5 terminology only.
11. Exclude trials whose only candidates are device-dependent.
12. Exclude trials whose only repurposing candidate is an unspecified panel.
13. Exclude `date_sensitive` classifications, or use the alternative classification.
14. Exclude candidates with `population_within_label`.

### Exploratory analyses
- The translational subset (Early Phase 1).
- Mechanism profiles.
- Description of delivery-enabling agents, established-therapy experiments and glioma-developed agents.
- An optional coverage audit against WHO ICTRP and CTIS.

All are labelled exploratory. A literature-evidence review of non-oncology candidates is out of scope and would be registered separately.

---

## Other

### Changes from the manuscript draft (v3) that this registration supersedes
- D19–D27: delivery-enabling agents are not candidates; category 2c is replaced by dated flags; the validation redesign; the H1 reporting; the translational indicators; the temporal framing; and the screening wording.
- The screening set is 870 records.
- Calibration preceded registration (disclosed above).

Future changes are dated amendments in `protocol_decisions.md`, reported in the paper.
