# OSF preregistration — draft text

**Template:** OSF "Preregistration Template for Secondary Data Analysis" (Van den Akker et al., *Meta-Psychology* 2021). Paste each section into the field with the same heading. If your OSF form uses different wording, match by meaning; every template question is answered below.
**Embargo:** private, embargo up to 4 years. It becomes public at publication, or earlier if you choose.
**Frozen materials referenced:** GitHub `Net4Brain/gbm-repurposing-registry`, commit `e2e6083` (2026-11-01). The same files are uploaded to the OSF project as `gbm-repurposing-registry_e2e6083.zip`, so the registration does not depend on the private GitHub repository.

---

## Study information

### Title
Repurposed drugs in the contemporary glioblastoma clinical trial landscape: a registry-based cross-sectional analysis

### Authors / contributors
Xinzhong Li (Teesside University) — *[add co-authors only if they agree to be listed now; contributors can be added later]*

### Description
- **Design.** A registry-based cross-sectional study of interventional adult glioblastoma drug trials on ClinicalTrials.gov that started between 1 January 2020 and 31 July 2026.
- **Classification.** Each experimental drug ("candidate agent") is classified by its origin, judged at the start date of the trial that tests it: *de novo* development, approved-drug repurposing (FDA or EMA approval for another indication), or investigational repositioning. Classification uses FDA (openFDA), EMA and ChEMBL records.
- **Measures.** The study measures:
  - how much of the glioblastoma drug pipeline is repurposing;
  - whether repurposing-containing trials differ from *de novo*-only trials in trial design, particularly in molecular selection of patients matched to the candidate's mechanism.
- **Extraction.** Done by two independent large-language-model coders following a frozen coding manual, with human adjudication of disagreements and a blinded human validation sample.

### Hypotheses
- **H1 (confirmatory).** Repurposing-containing trials use candidate-matched molecular selection less often than *de novo*-only trials. This is a directional hypothesis. Candidate-matched molecular selection means a molecular biomarker, required for eligibility or enrichment, that is mechanistically linked to the candidate agent.
  - **Smallest difference of interest:** 10 percentage points.
  - **Supported** if the risk difference (*de novo*-only minus repurposing-containing) is ≥ 10 percentage points in the hypothesised direction **and** its 95% CI excludes zero.
  - **Qualified** if the point estimate favours H1 but the CI includes zero, or if the difference does not persist after stratified adjustment, within non-oncology (2a) repurposing trials, or with one trial per agent.
  - **Not supported** otherwise.
- **Descriptive aim (no hypothesis test).** The proportion of unique candidate agents that are approved-drug repurposing, overall and by subcategory 2a/2b/2c. A headline estimate that changes by more than 5 percentage points across the prespecified sensitivity analyses will be reported as definition-dependent.

---

## Data description

### Datasets used
1. **ClinicalTrials.gov full study records.** API v2, retrieved 2026-11-01 as frozen JSON snapshots:
   - main search `ctgov_raw_20261101T130137Z.json` (SHA-256 `f09ed81bd69918c7560209c341fe9201325fa9ab894ff65f453036ae960c3e7e`, 834 records);
   - supplementary search `ctgov_supp_raw_20261101T150223Z.json` (SHA-256 `8665982d6e81c0897ef3c1e3b64a6cef0dc37c282fb6edffd33ef1507b87d7b9`).
2. **EMA medicines report** (`EMA_medicines_report_20261101.xlsx`, SHA-256 `4756d6fac5904e9dc1d6a0880d4e494aa1ef46d52a8972b17d8a22fb52eb678b`).
3. **openFDA** Drugs@FDA and drug-label endpoints, and the **ChEMBL** web services. Queried per drug by script; responses are cached with access dates.
4. **ReDO_Trials_DB** (Pantziarka et al., Front Pharmacol 2021, doi:10.3389/fphar.2021.790952). Frozen copy retrieved 2026-11-01, used only for external validation.
5. **AACT** archive (Clinical Trials Transformation Initiative), dated nearest to 2026-07-31. Used only to rebuild recruitment status on the index date.

### Availability and access
All sources are publicly available. ClinicalTrials.gov and openFDA are public domain; ChEMBL is CC BY-SA 3.0; EMA content may be reused with acknowledgement. ReDO_Trials_DB states no licence, so it is not redistributed: a script fetches it and checks the frozen checksum. AACT requires free registration.

### Data collection procedures
- **Main search.** Two searches were combined: condition-field and free-text. Each used: glioblastoma, GBM, glioblastoma multiforme, gliosarcoma, malignant glioma, high-grade glioma, grade 4 glioma. Filters: `AREA[StudyType]INTERVENTIONAL AND AREA[StartDate]RANGE[2020-01-01,2026-07-31]`. The union gave 834 records.
- **Supplementary search.** Four queries: WHO CNS5 terms (condition and free text), generic brain-tumour condition terms, and glioblastoma/gliosarcoma/GBM in eligibility criteria. They returned 833 records not in the main pull. A record was added to screening only if a glioblastoma term appears in its title, conditions or inclusion criteria; 36 were added. **Screening set = 870.** Exact queries and hit counts are in `logs/`.

### Codebook
- **Coding manual v1.2 (frozen)** — `coding_manual_v1.2.md`.
- **Output schema** — `schema/trial_coding.schema.v1.2.json`.
- **Protocol decision log** — `protocol_decisions.md`, decisions D1–D19.
- **Freeze checksums** — `FROZEN_v1.2.sha256`:
  - manual `49434ba5e98445a21a14f0899c4c2e38b7e5798aee12f7bd88a61486efcf818d`
  - schema `379ac1ad4edfc78427f76847623332d32dc4e1d26abe6f5ca97ef96f8588cbd7`
  - coder prompt `11a92f8e3c9b6277bd4e41d43dd8dfc3bad1dfa050950a211f10956711290240`
  - agent instructions `713ed75fac8789a56e1216e9f0d89eb7e9cb62f2e4a1a46e39001e66ad57fbc0`
  - scripts 03/05/06/07 (in the file).

---

## Variables

### Eligibility (screening; applied in order, first failure = exclusion reason)
1. **Study type:** interventional.
2. **Start date:** 2020-01-01 to 2026-07-31, actual or anticipated.
3. **Phase:** Phase 1, 1/2, 2, 2/3 or 3. Early Phase 1 (Phase 0), Phase 4 and "not applicable" are excluded.
4. **Age:** adults eligible. Paediatric-only trials are excluded; mixed-age trials are flagged.
5. **Population:** adult glioblastoma is a target population, named in conditions, title or inclusion criteria.
   - Mixed-glioma and solid-tumour basket trials that name glioblastoma are included and flagged.
   - "High-grade/malignant glioma" without naming glioblastoma is excluded.
   - Trials enrolling only IDH-mutant tumours are excluded.
   - Anti-GBM (renal) disease records are excluded.
6. **Candidate:** at least one pharmacological antitumour candidate agent in an experimental role.
   - Included types: small molecules, biologics (antibodies, proteins, ADCs) and radiopharmaceuticals.
   - Excluded types: cell and gene therapy, oncolytic viruses, cancer vaccines, devices alone, radiotherapy, surgery, diets, and unlicensed supplements.
7. **Withdrawn trials** are reported separately and contribute no agents.

### Intervention role (per drug–trial pair)
Every drug is listed and assigned one role:
- experimental monotherapy;
- experimental combination;
- standard-of-care backbone (including drugs given in every arm or already received);
- control/comparator;
- supportive;
- established-therapy experiment (temozolomide, carmustine, lomustine, bevacizumab tested in a new schedule, dose, route or setting);
- delivery-enabling agent;
- excluded intervention type;
- diagnostic agent.

**Only experimental monotherapy and experimental combination agents are candidate agents.**

### Drug origin (per candidate agent; T = trial start date)
- **ESTABLISHED** (D6 list): reported separately.
- **GLIOMA_DEVELOPED:** first FDA/EMA approval was for a glioma indication (e.g. vorasidenib). Reported separately.
- **2 — approved-drug repurposing:** FDA or EMA approval for any indication on or before T.
  - 2a: no oncology approval (ATC L01/L02).
  - 2b: oncology approval for another tumour.
  - 2c: only tumour-agnostic oncology approvals.
- **3 — investigational repositioning:** not approved by T, but in Phase ≥ 2 for a non-glioblastoma indication before T (dated by ChEMBL-linked trials).
- **1 — de novo:** none of the above.

Notes on applying the categories:
- Approvals by other regulators alone (e.g. China NMPA) do not count; they are flagged.
- Agent-level origin comes from the agent's earliest eligible trial.

### Trial-origin groups
- **Repurposing-containing:** ≥ 1 category-2 candidate. Includes trials testing an unspecified panel of approved drugs, which count at trial level only.
- **Repurposing-2a-containing.**
- **De novo-only:** only category-1 candidates.
- **Repositioning-only.**
- **Mixed-origin:** category 2 plus category 1.

### Outcomes
- **Primary:** candidate-matched molecular selection.
  - Qualifying biomarker: a tumour biomarker required for eligibility or enrichment, mechanistically linked to a candidate agent.
  - Not qualifying: IDH-wildtype status (defines the disease) and MGMT status (linked to the temozolomide backbone). They count only if the candidate itself targets MGMT.
- **Secondary:**
  - any molecular eligibility/enrichment requirement, including MGMT;
  - molecularly informed design (eligibility, enrichment or prospective stratification).
- **Descriptive:**
  - phase group;
  - lead sponsor class and industry involvement;
  - enrolment (anticipated and actual);
  - number of countries and lead region;
  - treatment setting;
  - regimen;
  - randomisation and control arm;
  - CNS5 vs historical terminology;
  - primary mechanism category (cytotoxic, targeted signalling, immunomodulatory, metabolic, epigenetic, anti-angiogenic, other);
  - flags: delivery-enabling, device-dependent and radiopharmaceutical.

### Indices
- **Headline:** unique category-2 candidate agents ÷ all unique candidate agents in categories 1–3.
- **Phase for agent summaries:** each agent takes the highest phase among its eligible trials.

---

## Knowledge of data

### Prior publication / use
Prior work by the authors did not use these snapshots.

### Prior knowledge of the data (full disclosure)
Before this registration, the following were seen:
- **Record counts:** main 834; supplementary 833 new, 36 added; screening set 870.
- **ReDO overlap:** 85 CNS-tumour trials in ReDO_Trials_DB, 28 of them in the main pull. The 9 in-window NCT trials not in our pull were checked and are ineligible.
- **Calibration (40 records).** A stratified random sample (seed 20261101) was coded twice by both LLM coders: round 1 with manual v1.0, round 2 with v1.1.
  - Inter-coder agreement was examined for every coded variable, including the outcome variables, and disagreements were read to revise the manual's wording.
  - Disagreements that changed scope were decided by XL and recorded as D19. Delivery-enabling agents are not candidates; drug–device therapies are candidates flagged device-dependent; unspecified approved-drug panels are counted at trial level only.
- **Drug lookups.** FDA/EMA/ChEMBL results were run for the 56 candidate moieties named in the calibration records, to debug the lookup script (v1.0 to v1.2).

The following has **not** been done:
- No drug-origin category has been assigned to any trial.
- No cross-tabulation of drug origin against molecular selection, or any comparison relevant to H1, has been computed.

The 40 calibration records will be re-coded in the main pass with v1.2, like all other records.

---

## Analyses

### Extraction, adjudication and validation
**Coders.**
- Coder A = Claude Opus 5.5 (`claude-opus-5-5`); Coder B = Claude Sonnet 5.5 (`claude-sonnet-5-5`).
- Each codes every record independently in fresh contexts, using the identical prompt (`prompts/coder_prompt_v1.2.md`), from a plain-text rendering of each record.
- Every judgement cites a verbatim quote, which is checked by script.
- Structured fields (phase, dates, status, enrolment, sponsor, countries) are extracted by code.

**Adjudication.**
- Every disagreement, and every item either coder flags as uncertain, is adjudicated by a human, with reasons recorded.

**Agreement and validation.**
- Agreement before adjudication is reported as Cohen's κ with PABAK and Gwet's AC1.
- A stratified random validation sample of about 100 trials, oversampling repurposing-containing and molecularly selected trials, is coded by a human blind to AI output. Per-variable accuracy is reported with 95% CIs.
- If any key variable (eligibility, candidate role, drug origin, candidate-matched selection) is below 90% accuracy, every record is human-coded for that variable.

**External checks.**
- The proportion of eligible ReDO-listed trials coded repurposing-containing is reported with an exact 95% CI.
- A human checks 30 random *de novo* agents against regulatory and ChEMBL records.

**Index-date status.**
- Recruitment status on 2026-07-31 is reconstructed from registry version history or the nearest dated AACT archive, for the active-pipeline subset.

### Statistical models
- **Census and intervals.** The cohort is a complete census of eligible records. 95% CIs are interpreted as precision for an ongoing process, not as sampling inference. Wilson intervals are used for proportions and Newcombe intervals for differences.
- **H1 analyses:**
  1. Crude risk difference (*de novo*-only minus repurposing-containing) with Newcombe 95% CI. **This is the primary estimate.**
  2. Mantel–Haenszel risk difference stratified by phase group (P1 / P2 / P3) and treatment setting.
  3. CIs clustered by agent; and one randomly selected trial per agent (seed fixed in code).
  4. Agent-level comparison: the proportion of agents tested in at least one candidate-matched trial.
  5. Repeat with repurposing-2a-containing trials as the exposure.
- **Small cells.** If expected cell counts are below 5, exact methods are used, and phase strata collapse to early (P1) vs later (P2–P3).
- **Exploratory comparisons:** phase, sponsorship, setting, regimen, randomisation and control arm. Reported with effect estimates and CIs; any P values are descriptive and unadjusted.
- **Software:** R 4.5.2 and Python 3.13.

### Effect size
Risk difference in percentage points. The smallest difference of interest is 10 percentage points.

### Statistical power
Not applicable. All eligible records are included and no sample-size calculation is made.

### Inference criteria
See the H1 decision rules (supported / qualified / not supported). No multiplicity adjustment is made, because there is one confirmatory hypothesis.

### Data exclusion
Only by the eligibility rules above. No outlier exclusion.

### Missing data
Values that the registry does not determine are coded "unclear" and reported as their own category, never imputed. Trials whose index-date status cannot be reconstructed are reported separately.

### Reliability and robustness (prespecified sensitivity analyses)
1. Combine approved-drug repurposing with investigational repositioning (categories 2 + 3).
2. Restrict exposure to 2a, excluding 2c tumour-agnostic approvals.
3. Judge drug origin at the index date (2026-07-31) instead of trial start.
4. Glioblastoma-only populations.
5. Exclude basket trials.
6. Exclude mixed-origin trials from the H1 comparison.
7. Count each multi-drug repurposing regimen once.
8. Include Early Phase 1 trials.
9. Restrict to trials with an actual start date.
10. Restrict to trials using WHO CNS5 terminology.
11. Exclude trials whose only candidates are device-dependent (D19).
12. Exclude trials whose only repurposing candidate is an unspecified approved-drug panel (D19).

### Exploratory analyses
- Mechanism category by origin.
- Phase and sponsor profiles of repurposed agents.
- Description of delivery-enabling agents, established-therapy experiments and glioma-developed agents.
- An optional coverage audit against WHO ICTRP and CTIS.

These are labelled exploratory.

---

## Other

### Deviations from the manuscript draft (v3) that this registration supersedes
- **D19.** Delivery-enabling agents are **not** candidate agents (v3 called them flagged candidates). This adds sensitivity analyses 11 and 12.
- **Screening set.** It is 870 (834 main + 36 supplementary), not 834.
- **Calibration wording.** Calibration coded 40 records before registration (disclosed above). The v3 sentence "before any outcome variable is coded" will read "before the main coding pass".

Future changes will be dated amendments in `protocol_decisions.md` and reported in the paper.
