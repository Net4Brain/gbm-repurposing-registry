# Coding manual — GBM repurposing registry study

Version 1.0 (draft for calibration), 2026-11-01. It implements protocol decisions D1–D17 (`protocol_decisions.md`) and the Methods of `GBM_registry_NOA_structure_v3.docx`. After calibration it becomes Supplementary Table S3 and part of Supplementary Methods. Changes after the main pass starts are logged as dated amendments at the end of this file.

## 0. How the manual is used

Coding happens in three layers. Each variable below is tagged with the layer that codes it.

| Tag | Who codes | What it means |
|---|---|---|
| **[CODE]** | Python script | Read directly from structured registry fields. No judgement involved. |
| **[LLM]** | Coder A and Coder B, independently | Judgement from registry text. Output must follow `schema/trial_coding.schema.json`. |
| **[LOOKUP]** | Python script against FDA / EMA / ChEMBL | Approval dates, indications, development phase and mechanism for each active moiety. The LLM never supplies these from memory. |
| **[RULE]** | Python script | Derived from the other layers using the decision rules in this manual (e.g. drug-origin category). |

General rules for LLM coders:
1. **Use only the registry record provided.** Do not use outside knowledge about the trial. Outside knowledge about a *drug* (for example, that metformin is a diabetes drug) may be used only to fill `drug_class_hint`; the [LOOKUP] layer is what counts.
2. **Quote the evidence.** Every judgement must quote the registry text that supports it (≤ 300 characters, verbatim) and name the field it came from.
3. **Say when you are unsure.** If the text does not settle a variable, code `unclear` and set `uncertain: true` with a reason. Never guess. Uncertain items go to human adjudication.
4. **One trial at a time.** Do not compare with other trials.
5. **Ten-minute rule (human adjudicators):** if a trial is still ambiguous after about 10 minutes, record the best decision, flag it `pi_review`, and move on.

---

## 1. Screening (trial eligibility)

Apply the steps in this order. The first step a trial fails gives its **exclusion reason**, which is used in Figure 1.

| Step | Variable | Layer | Rule | Exclusion reason |
|---|---|---|---|---|
| S1 | `study_type` | [CODE] | Must be INTERVENTIONAL | `not_interventional` |
| S2 | `start_date` | [CODE] | 2020-01-01 to 2026-07-31 (actual or anticipated) | `start_outside_window` |
| S3 | `phase` | [CODE] | PHASE1, PHASE1/PHASE2, PHASE2, PHASE2/PHASE3 or PHASE3. EARLY_PHASE1 = Phase 0 (D8). NA and PHASE4 are excluded. | `phase0_early_phase1`, `phase4`, `phase_not_applicable` |
| S4 | `age_scope` | [CODE] | `stdAges` must include ADULT. CHILD-only is excluded. If it also includes CHILD, flag `mixed_age`. | `paediatric_only` |
| S5 | `gbm_population` | [LLM] | See 1.1 | `not_glioblastoma`, `gbm_excluded`, `anti_gbm_disease` |
| S6 | `has_eligible_candidate` | [LLM] | At least one pharmacological antitumour agent in an experimental role (see 1.2 and section 3) | `no_pharmacological_candidate`, `excluded_intervention_type`, `established_therapy_only` |
| S7 | `withdrawn` | [CODE] | overallStatus = WITHDRAWN: counted and reported separately; contributes no agents | `withdrawn` (reported separately) |

### 1.1 `gbm_population` [LLM]

| Value | Rule | Status |
|---|---|---|
| `gbm_only` | Only glioblastoma / gliosarcoma / IDH-wildtype grade 4 astrocytic glioma is eligible | include |
| `mixed_glioma_gbm_named` | Several glioma types are eligible and glioblastoma is explicitly named in the conditions or eligibility | include; flag for the GBM-only sensitivity analysis |
| `basket_gbm_eligible` | Solid-tumour or multi-cancer trial in which glioblastoma is explicitly eligible (named in inclusion criteria, a cohort, or the conditions) | include; flag `basket` (D17; sensitivity analysis 5) |
| `high_grade_glioma_unspecified` | "High-grade glioma" / "malignant glioma" with no explicit mention of glioblastoma | exclude → `not_glioblastoma` |
| `gbm_excluded` | Glioblastoma or primary CNS tumours appear only as an exclusion | exclude |
| `anti_gbm_disease` | "GBM" means anti-glomerular basement membrane disease | exclude |
| `not_glioblastoma` | Anything else (brain metastases, paediatric DIPG/DMG only, IDH-mutant glioma only, meningioma, etc.) | exclude |

Notes:
- **IDH-mutant astrocytoma, grade 4** is not glioblastoma under WHO CNS5. A trial that enrols *only* IDH-mutant tumours is `not_glioblastoma`.
- `cns5_terminology` [LLM]: `cns5` if eligibility says "glioblastoma, IDH-wildtype" (or explicitly requires IDH-wildtype); `historical` if it says "glioblastoma (multiforme)" with no IDH requirement or explicitly allows IDH-mutant GBM; `unclear` otherwise. Used for sensitivity analysis 10.

### 1.2 Intervention types

| Included as pharmacological candidates | Excluded intervention types |
|---|---|
| Small molecules; monoclonal and bispecific antibodies; other therapeutic proteins and peptides; antibody–drug conjugates; radiopharmaceuticals (flag `radiopharmaceutical`); licensed medicines of any origin (D16) | Cell therapy (CAR-T, NK, dendritic-cell, TIL); gene therapy; oncolytic viruses; cancer vaccines (peptide, DC, mRNA, neoantigen); devices (TTFields, focused ultrasound alone); radiotherapy alone; surgery; diets; supplements and nutraceuticals without marketing authorisation as a medicine (e.g. curcumin, CBD extracts not licensed, vitamins as supplements) |

A licensed medicine counts as pharmacological even if it is also sold as a supplement, for example ascorbic acid given intravenously at pharmacological doses. Mark this case `uncertain` for adjudication.

---

## 2. Trial-level variables

| Variable | Layer | Values / rule |
|---|---|---|
| `phase_registry` | [CODE] | As registered |
| `phase_group` | [RULE] | Higher phase wins: Phase 1 → `P1`; Phase 1/2 and Phase 2 → `P2`; Phase 2/3 and Phase 3 → `P3`. For small cells, collapse to `early` (P1) vs `later` (P2–P3). |
| `status_retrieval` | [CODE] | overallStatus on 2026-11-01 |
| `status_index` | [CODE] | Status on 2026-07-31, rebuilt from record history or the AACT archive (D13); `not_reconstructable` if neither works |
| `start_date`, `start_date_type` | [CODE] | ACTUAL / ESTIMATED |
| `primary_completion_date` | [CODE] | |
| `enrolment`, `enrolment_type` | [CODE] | ACTUAL / ESTIMATED, reported separately |
| `lead_sponsor_class` | [CODE]+[RULE] | Registry class INDUSTRY → `industry`; NIH, FED, OTHER_GOV, NETWORK, OTHER, INDIV → `non_industry` |
| `industry_involvement` | [CODE]+[RULE] | `yes` if the lead sponsor or any collaborator has class INDUSTRY. [LLM] may add `yes` if the text says drug is supplied or funded by a named company. |
| `n_countries`, `lead_region` | [CODE] | Region of the first listed location (or of the sponsor if there are no locations): `north_america`, `europe`, `asia`, `other` |
| `randomised` | [CODE] | allocation = RANDOMIZED → yes; NON_RANDOMIZED or NA → no |
| `control_arm` | [CODE] | yes if any arm is ACTIVE_COMPARATOR, PLACEBO_COMPARATOR, SHAM_COMPARATOR or NO_INTERVENTION. [LLM] checks OTHER-type arms described as standard of care. |
| `mixed_age` | [CODE] | stdAges includes CHILD and ADULT |
| `treatment_setting` | [LLM] | `newly_diagnosed`, `recurrent`, `both`, `unclear`. Newly diagnosed includes first-line adjuvant or maintenance after chemoradiation. Recurrent includes progressive and refractory disease. |
| `regimen` | [LLM] | `monotherapy` = the candidate is the only antitumour drug in the experimental arm, ignoring supportive drugs. `combination` = any other antitumour drug or radiotherapy in the experimental arm. Record the partner(s) in `combination_partners`. |
| `basket` | [LLM] | yes/no (see 1.1) |

---

## 3. Drug–trial pairs (one row per agent per trial) [LLM]

List **every** intervention that is a drug or biologic, including background and supportive drugs, so that the denominator is transparent.

| Field | Rule |
|---|---|
| `agent_name_registered` | As written in the registry |
| `active_moiety` | INN of the active moiety. Map brand to generic and salt or ester to parent (e.g. "Temodal" → temozolomide; "trametinib dimethyl sulfoxide" → trametinib). Split fixed-dose combinations into components, one row each with `fixed_dose_combination: true`. Use the development code if there is no INN yet (e.g. "ONC201" → dordaviprone if stated, otherwise ONC201). |
| `role` | See 3.1 |
| `delivery_enabling` | true if the agent's stated purpose is to improve delivery of another drug (e.g. BBB opening, efflux-pump inhibition, a CYP inhibitor used as a booster) |
| `formulation_flag` | `new_formulation`, `new_route` (e.g. intranasal, intra-arterial, convection-enhanced, intratumoral), `prodrug`, `biosimilar`, or `none` |
| `regimen_id` | Same ID for every component of a named multi-drug regimen (e.g. CUSP9) |
| `drug_class_hint` | Free text: what the coder believes the agent is ("antidiabetic", "investigational EGFR inhibitor"). **Not used for classification.** It only helps the [LOOKUP] step catch mapping errors. |

### 3.1 Intervention role — decision rules

Work through the rules in order and use the first that applies.

1. The agent is in a comparator, placebo or control arm only → `control_comparator`.
2. Its stated purpose is symptom control (seizures, oedema, nausea, fatigue, cognition, pain, anaesthesia) and the record states **no** antitumour hypothesis or antitumour outcome → `supportive`. If the record states an antitumour hypothesis or outcome (e.g. "levetiracetam as a sensitizer of chemoradiation"), it is a candidate (rule 4 or 5).
3. Standard-of-care treatment given equally in all arms, or described as background (e.g. temozolomide with radiotherapy in "Stupp + X") → `soc_backbone`.
4. It is the only investigational antitumour agent in an experimental arm → `experimental_monotherapy`.
5. It is one of the investigational antitumour components of an experimental arm → `experimental_combination`.
6. An **established GBM therapy** (temozolomide, carmustine IV or wafer, lomustine, bevacizumab; D6) is itself the subject of investigation in a new schedule, dose, route or setting → `established_therapy_experiment`. This is reported separately and is not a candidate.

Only roles 4 and 5 are **candidate agents**. A trial with no candidate agents is excluded at S6 (`established_therapy_only` or `no_pharmacological_candidate`).

---

## 4. Drug origin (per candidate agent, judged at each trial's start date)

### 4.1 [LOOKUP] fields (scripted, per active moiety)

`fda_first_approval_date`, `fda_indications`, `ema_first_authorisation_date`, `ema_indications`, `chembl_id`, `chembl_max_phase`, `chembl_indications` (with max phase per indication and earliest year where available), `glioma_lineage_approval` (any FDA/EMA approval for paediatric glioma or IDH-mutant glioma), `tumour_agnostic_approval`, `oncology_approval` (any approved cancer indication). Each field keeps its source URL or ID and the access date.

### 4.2 [RULE] decision tree (the trial start date is T)

```
Is the agent an established GBM therapy (D6 list)?          -> ESTABLISHED (reported separately; not a candidate)
Was it approved (FDA or EMA) for any indication on or before T?
 ├─ yes: Was its FIRST approval (FDA or EMA) for a glioma indication
 │       (paediatric glioma / IDH-mutant glioma), e.g. vorasidenib, tovorafenib?
 │        └─ yes -> GLIOMA_DEVELOPED (reported separately)
 │       (Drugs first approved elsewhere that later gained a glioma label, e.g.
 │        dabrafenib + trametinib, stay in category 2 with flag `glioma_label`.)
 │      Any oncology approval?
 │        ├─ no  -> 2a  non-oncology repurposing
 │        └─ yes: only tumour-agnostic oncology approval(s)?
 │                 ├─ yes -> 2c tumour-agnostic
 │                 └─ no  -> 2b other-tumour oncology
 │      (2c flag also kept on 2b agents that also hold a tumour-agnostic approval)
 └─ no:  Had it reached Phase 2 or later in a non-GBM indication before T?
          ├─ yes -> 3  investigational repositioning
          └─ no  -> 1  de novo
```

Notes:
- **Agent-level origin** is taken from the agent's earliest eligible trial (D12). **Index-date origin** (T = 2026-07-31) is computed as well, for sensitivity analysis 3.
- **Approvals outside FDA/EMA** (e.g. China NMPA only) do not count. Set `other_regulator_only: true`.
- **Biosimilars** take the origin of the reference product.
- **New formulations or routes** of an approved moiety are coded with the moiety's origin and the `formulation_flag`.
- If the ChEMBL phase evidence for category 3 lacks dates or is ambiguous → `uncertain`, human adjudication. Record the evidence (trial ID or publication) in Table S2.
- **5-aminolevulinic acid** has a GBM *visualisation* label only. It is not an established therapy; classify it by the tree (its approvals are diagnostic).

### 4.3 Trial-origin groups [RULE]

| Group | Definition |
|---|---|
| `repurposing_containing` | At least one category-2 candidate (2a, 2b or 2c) |
| `repurposing_2a_containing` | At least one 2a candidate |
| `de_novo_only` | Only category-1 candidates |
| `repositioning_only` | Category-3 candidates and no category-2 candidates |
| `mixed_origin` | At least one category-2 candidate **and** at least one category-1 candidate (a subset of `repurposing_containing`; excluded in sensitivity analysis 6) |

---

## 5. Biomarkers (per trial) [LLM]

List every biomarker mentioned in the eligibility, design, arms or outcomes, one row each.

| Field | Values |
|---|---|
| `biomarker` | `MGMT`, `IDH`, `EGFR_EGFRvIII`, `BRAF`, `NTRK`, `H3K27M`, `CDKN2A_B`, `PTEN_PI3K`, `CDK4_6_pathway`, `FGFR`, `MET`, `PD_L1`, `TMB_MMR`, `other` (specify), `none` |
| `role` | `eligibility` (required to enter the trial), `enrichment` (required for a cohort or arm), `stratification` (prospective randomisation or stratification factor), `pharmacodynamic`, `exploratory_correlative` |
| `candidate_matched` | true if the biomarker is mechanistically linked to a candidate agent in this trial (name the agent). Examples: EGFR amplification + EGFR inhibitor; BRAF V600E + BRAF/MEK inhibitor; MTAP deletion + PRMT5/MAT2A inhibitor; CDKN2A loss + CDK4/6 inhibitor. **IDH-wildtype** (a diagnostic criterion) and **MGMT status** (linked to the temozolomide backbone) are **never** candidate-matched, unless the candidate is an MGMT-targeting agent. |
| `source_quote` | Verbatim quote |

Derived trial outcomes [RULE]:
- `candidate_matched_selection` (**primary outcome**) = any biomarker row with role eligibility or enrichment and `candidate_matched: true`.
- `any_molecular_selection` = any eligibility or enrichment biomarker, including MGMT (excluding IDH-wildtype used only to define GBM).
- `molecularly_informed_design` = any eligibility, enrichment or stratification biomarker.
- `mgmt_requirement`, `idh_requirement` = reported separately.

Routine histology, routine MRI response assessment and imaging-only markers are not molecular biomarkers. Record them only as `other` if they are explicitly described as a biomarker endpoint.

---

## 6. Mechanism (per candidate agent)

One **primary** category. Optional secondary categories. Source order: (1) ChEMBL mechanism of action [LOOKUP]; (2) the FDA/EMA label; (3) the mechanism stated in the registry rationale [LLM, quoted]. A repurposed drug is classified by its **proposed antitumour mechanism** as stated in the registry; if none is stated, by its ChEMBL primary target.

| Category | Includes | Examples |
|---|---|---|
| `cytotoxic` | DNA alkylation/damage, antimetabolites, topoisomerase or microtubule agents | lomustine, irinotecan, VAL-083 |
| `targeted_signalling` | Kinase and pathway inhibitors; non-immune receptor antibodies; DNA-damage-response inhibitors (PARP, ATR, WEE1); ADCs (classified by target) | abemaciclib, dabrafenib, olaparib, depatux-m |
| `immunomodulatory` | Checkpoint antibodies, cytokines, immune agonists, IDO/myeloid modulators | nivolumab, pembrolizumab |
| `metabolic` | Tumour metabolism (OXPHOS, glycolysis, glutamine, polyamines, IDH-pathway enzymes) | metformin, DFMO, CB-839 |
| `epigenetic` | HDAC, DNMT, EZH2, BET, LSD1 | valproate (as HDAC inhibitor), tazemetostat |
| `anti_angiogenic` | Agents whose primary target is VEGF/VEGFR or angiogenesis | regorafenib, cediranib |
| `other` | Everything else, including CNS drugs with undefined antitumour mechanisms, antimicrobials, ion-channel modulators | |

`delivery_enabling` is a **role flag** (section 3), not a mechanism. Calibrate on at least 40 agents spanning all origin categories before the main pass.

---

## 7. Adjudication, validation and outputs

1. **Coders A and B** produce JSON per trial independently (`outputs/coderA/`, `outputs/coderB/`).
2. **Compare** (`[CODE]`): every disagreement, and every item marked `uncertain` by either coder, goes to `adjudication_queue.csv`.
3. **Human adjudication:** XL decides; drug-origin and clinical questions go to the clinical co-author. Each decision is recorded with its reason.
4. **Agreement** before adjudication: Cohen's kappa + PABAK or Gwet's AC1 for each binary or categorical variable; percentage agreement for multi-category items.
5. **Validation sample (D15):** about 100 trials, stratified (oversampling repurposing-containing and molecularly selected trials), coded by XL blind to AI output using this manual. Report accuracy per variable with 95% CIs. If any key variable (eligibility, role, origin, candidate-matched selection) is below 90%, every record is coded by a human for that variable.
6. **External checks (D10):** ReDO agreement with an exact CI; a human checks 30 random de novo agents.

## 8. Calibration (before the main pass)

- Draw 40 records stratified by search source (main vs supplementary), phase group and sponsor class. Run both coders, then XL reviews.
- Revise only how rules are applied (wording, examples). Do not change definitions without a dated amendment.
- After calibration, freeze as v1.1 and record its SHA-256 in the OSF registration.

## Amendments
(none yet)
