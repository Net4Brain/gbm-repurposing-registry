# Coding manual — GBM repurposing registry study

Version 1.4 (**frozen** for the main pass), 2026-11-02. Supersedes v1.3 (`coding_manual_v1.3.md`), v1.2, v1.1 and v1.0, all kept unchanged. It implements protocol decisions D1–D27 (`protocol_decisions.md`). It becomes Supplementary Table S3 and part of Supplementary Methods. Changes after the main pass starts are logged as dated amendments at the end of this file.

## 0. How the manual is used

Coding happens in three layers. Each variable below is tagged with the layer that codes it.

| Tag | Who codes | What it means |
|---|---|---|
| **[CODE]** | Python script | Read directly from structured registry fields. No judgement involved. |
| **[LLM]** | Coder A and Coder B, independently | Judgement from registry text. Output must follow `schema/trial_coding.schema.v1.4.json`. |
| **[LOOKUP]** | Python script against FDA / EMA / ChEMBL | Approval dates, indications, development phase and mechanism for each active moiety. The LLM never supplies these from memory. |
| **[RULE]** | Python script | Derived from the other layers using the decision rules in this manual (e.g. drug-origin category). |

General rules for LLM coders:
1. **Use only the registry record provided.** Do not use outside knowledge about the trial. Outside knowledge about a *drug* (for example, that metformin is a diabetes drug) may be used only to fill `drug_class_hint`; the [LOOKUP] layer is what counts.
2. **Quote the evidence.** Every judgement must quote the registry text that supports it (≤ 300 characters) and name the field it came from. A quote is **one unbroken span copied character for character**: no ellipses ("..." or "…"), no paraphrase, no joined fragments, no re-formatted lists. If the evidence is in two places, give two evidence items. Quotes are checked automatically against the record.
3. **Say when you are unsure — but only when it matters (C9).** If the text does not settle a variable, code `unclear` where allowed. Set `uncertain: true` **only** when the doubt could change (a) screening (S5 `gbm_population` or S6 `has_eligible_candidate`), (b) whether an agent is a candidate (its `role`), or (c) the primary biomarker outcome (`candidate_matched` on an eligibility or enrichment biomarker). Put every other doubt in `coder_notes`. Never guess. Uncertain items go to human adjudication.
4. **One trial at a time.** Do not compare with other trials.
5. **Ten-minute rule (human adjudicators):** if a trial is still ambiguous after about 10 minutes, record the best decision, flag it `pi_review`, and move on.

---

## 1. Screening (trial eligibility)

Apply the steps in this order. The first step a trial fails gives its **exclusion reason**, which is used in Figure 1.

| Step | Variable | Layer | Rule | Exclusion reason |
|---|---|---|---|---|
| S1 | `study_type` | [CODE] | Must be INTERVENTIONAL | `not_interventional` |
| S2 | `start_date` | [CODE] | 2020-01-01 to 2026-07-31 (actual or anticipated) | `start_outside_window` |
| S3 | `phase` | [CODE] | PHASE1, PHASE1/PHASE2, PHASE2, PHASE2/PHASE3 or PHASE3. EARLY_PHASE1 = Phase 0 (D8). NA and PHASE4 are excluded. EARLY_PHASE1 records are still coded in full by the LLM coders and reported as a separate **translational subset** (D23); they never enter the primary estimand. | `phase0_early_phase1`, `phase4`, `phase_not_applicable` |
| S4 | `age_scope` | [CODE] | `stdAges` must include ADULT. CHILD-only is excluded. If it also includes CHILD, flag `mixed_age`. | `paediatric_only` |
| S5 | `gbm_population` | [LLM] | See 1.1 | `not_glioblastoma`, `gbm_excluded`, `anti_gbm_disease` |
| S6 | `has_eligible_candidate` | [LLM] | At least one pharmacological antitumour agent in an experimental role (see 1.2 and section 3) | `no_pharmacological_candidate`, `excluded_intervention_type`, `established_therapy_only` |
| S7 | `withdrawn` | [CODE] | overallStatus = WITHDRAWN: counted and reported separately; contributes no agents | `withdrawn` (reported separately) |

### 1.1 `gbm_population` [LLM]

| Value | Rule | Status |
|---|---|---|
| `gbm_only` | Only glioblastoma / gliosarcoma / IDH-wildtype grade 4 astrocytic glioma is eligible. "Grade 4/IV astrocytoma" or "grade 4/IV glioma" **without** an IDH requirement is the historical (WHO 2016) name for glioblastoma and counts here, with `cns5_terminology: historical` (D27C) | include |
| `mixed_glioma_gbm_named` | Several glioma types are eligible and glioblastoma is explicitly named in the conditions or eligibility | include; flag for the GBM-only sensitivity analysis |
| `basket_gbm_eligible` | Solid-tumour or multi-cancer trial in which glioblastoma is explicitly eligible (named in the conditions, title, inclusion criteria or a registered arm/group label; D27B) | include; flag `basket` (D17; sensitivity analysis 5) |
| `high_grade_glioma_unspecified` | "High-grade glioma" / "malignant glioma" with no explicit mention of glioblastoma | exclude → `not_glioblastoma` |
| `gbm_excluded` | Glioblastoma or primary CNS tumours appear only as an exclusion | exclude |
| `anti_gbm_disease` | "GBM" means anti-glomerular basement membrane disease | exclude |
| `not_glioblastoma` | Anything else (brain metastases, paediatric DIPG/DMG only, IDH-mutant glioma only, meningioma, etc.) | exclude |

Notes:
- **Where glioblastoma must be named (C7).** Glioblastoma (or gliosarcoma, GBM, IDH-wildtype grade 4 glioma) counts as "named" only in the **conditions, title, inclusion criteria or a registered arm/group label** (D27B). A mention only in the brief summary, detailed description, keywords, outcomes or exclusion criteria does not make a trial eligible, even if it describes a planned glioblastoma cohort.
- **IDH-mutant astrocytoma, grade 4** is not glioblastoma under WHO CNS5. A trial that enrols *only* IDH-mutant tumours is `not_glioblastoma`, even if an arm or cohort is labelled "GBM" (historical usage).
- `cns5_terminology` [LLM] (C8):
  - `cns5` = the record requires IDH-wildtype status for glioblastoma, or cites WHO CNS 2021 (CNS5).
  - `historical` = the record cites WHO 2016 or earlier, uses "glioblastoma multiforme" or "grade 4/IV astrocytoma/glioma" without an IDH requirement, or explicitly allows IDH-mutant glioblastoma.
  - `unclear` = anything else (e.g. plain "glioblastoma" with no IDH or WHO reference).
  - If the record meets both `cns5` and `historical` (e.g. "glioblastoma multiforme, IDH-wildtype"), code `cns5`. Used for sensitivity analysis 10.

### 1.2 Intervention types

| Included as pharmacological candidates | Excluded intervention types |
|---|---|
| Small molecules; monoclonal and bispecific antibodies; other therapeutic proteins and peptides; antibody–drug conjugates; radiopharmaceuticals (flag `radiopharmaceutical`); licensed medicines of any origin (D16) | Cell therapy (CAR-T, NK, dendritic-cell, TIL); gene therapy; oncolytic viruses; cancer vaccines (peptide, DC, mRNA, neoantigen); devices (TTFields, focused ultrasound alone); radiotherapy alone; surgery; diets; supplements and nutraceuticals without marketing authorisation as a medicine (e.g. curcumin, CBD extracts not licensed, vitamins as supplements) |

A licensed medicine counts as pharmacological even if it is also sold as a supplement, for example ascorbic acid given intravenously at pharmacological doses. Mark this case `uncertain` for adjudication.

Excluded intervention types and diagnostic agents are still **listed** in `agents` (for transparency) with role `excluded_intervention_type` or `diagnostic_agent` (C2). They are never candidates.

**Delivery-enabling agents (C11, D19)** — drugs whose stated purpose is to get another agent into the tumour (microbubbles for focused-ultrasound BBB opening, mannitol for BBB disruption, a pharmacokinetic booster such as ritonavir or cobicistat, an efflux-pump inhibitor) — are **not** candidates. Role `delivery_enabling_agent`; reported separately.

**Drug–device therapies (C12, D19)** — a drug whose antitumour effect is tested but needs a device to be activated or delivered (5-aminolevulinic acid for photodynamic or sonodynamic therapy; carboplatin delivered across a focused-ultrasound-opened BBB) — **is** a candidate, with `device_dependent: true`. Sensitivity analysis 11 excludes trials whose only candidates are device-dependent. The device itself is not an agent. 5-ALA used only for fluorescence-guided resection is a `diagnostic_agent`.

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
| `industry_involvement` | [CODE]+[RULE] | `yes` if the lead sponsor or any collaborator has class INDUSTRY. Structured fields only; the LLM field `industry_support_in_text` was dropped (D27A). |
| `n_countries`, `lead_region` | [CODE] | Region of the first listed location (or of the sponsor if there are no locations): `north_america`, `europe`, `asia`, `other` |
| `randomised` | [CODE] | allocation = RANDOMIZED → yes; NON_RANDOMIZED or NA → no |
| `control_arm` | [CODE] | yes if any arm is ACTIVE_COMPARATOR, PLACEBO_COMPARATOR, SHAM_COMPARATOR or NO_INTERVENTION. [LLM] checks OTHER-type arms described as standard of care, as `control_arm_from_other_arms` (R8): `yes` = an OTHER- or EXPERIMENTAL-labelled arm works as the control (e.g. standard of care or placebo); `no` = more than one arm but none works as a control beyond the registered comparator types; `not_applicable` = single-arm trial. |
| `mixed_age` | [CODE] | stdAges includes CHILD and ADULT |
| `treatment_setting` | [LLM] | `newly_diagnosed`, `recurrent`, `both`, `unclear`. Newly diagnosed includes first-line adjuvant or maintenance after chemoradiation. Recurrent includes progressive and refractory disease; "advanced", "refractory", "progressive" or "after standard therapy" = `recurrent` (C10). |
| `regimen` | [LLM] | Counts **all** antitumour therapy in the experimental arm, including the standard backbone (C1). `monotherapy` = the candidate is the only antitumour drug and there is no radiotherapy in the experimental arm, ignoring supportive drugs. `combination` = any other antitumour drug (including a temozolomide backbone) or radiotherapy in the experimental arm. Record the partner(s) in `combination_partners`. So "Stupp + X" is `regimen: combination` while X is `role: experimental_monotherapy` (see 3.1). `not_applicable` whenever `has_eligible_candidate` is false (R1). |
| `basket` | [LLM] | yes/no (see 1.1) |
| `tumour_pk_planned` | [LLM] | `yes` if the record plans to measure a candidate's concentration in **tumour tissue or CSF** (e.g. "drug levels in resected tumour", "tumour-to-plasma ratio", microdialysis). Plasma-only pharmacokinetics = `no`. `unclear` **only** if PK is planned and the sample type is not stated (W7). No PK planned = `no`. Quote the evidence (D23). |
| `target_engagement_planned` | [LLM] | `yes` if the record plans a **pharmacodynamic or target-modulation** measurement for a candidate in tumour, CSF, blood or imaging (e.g. "inhibition of phospho-S6 in tumour", "2-HG reduction on MRS", "CD8 infiltration after treatment"). Safety, response and survival endpoints are not target engagement. A stated pharmacodynamic objective with paired (pre/post) tumour sampling = `yes` (W7). `unclear` only if a biomarker endpoint is planned but not linked to the candidate or its target. Quote the evidence (D23). |

---

## 3. Drug–trial pairs (one row per agent per trial) [LLM]

List **every** intervention that is a drug or biologic, including background and supportive drugs, so that the denominator is transparent. "Every" means agents that are **registered interventions**, plus agents the protocol text says **every patient receives** (e.g. temozolomide in a named Stupp regimen). Do not add agents that are only mentioned in passing, such as an imaging tracer used for routine assessment that is not a registered intervention (R9).

| Field | Rule |
|---|---|
| `agent_name_registered` | As written in the registry |
| `active_moiety` | INN of the active moiety, lower case, in **INN spelling** (e.g. phytomenadione, not phytonadione; American spelling only for words that are not INNs) (C5, W2). **Radiopharmaceuticals (W1):** use the INN if one exists; otherwise the ligand or development code **without** the isotope (e.g. "[177Lu]Lu-XT771" → xt771), with the isotope in `drug_class_hint`. A diagnostic form of the same ligand (e.g. "[68Ga]Ga-XT771" for imaging) is listed as a separate row, `role: diagnostic_agent`, named with its isotope (e.g. 68ga-xt771). **Excluded intervention types** (vaccines, cell therapies) get a short generic name (e.g. "rabies vaccine", "dendritic cell vaccine"), not a brand. Map brand to generic and salt or ester to parent (e.g. "Temodal" → temozolomide; "trametinib dimethyl sulfoxide" → trametinib). If there is no INN in the record, use the development code **exactly as first written in the record** (e.g. "ONC201" → dordaviprone if stated, otherwise onc201) and put the full descriptive name in `drug_class_hint`. Split fixed-dose combinations into components, one row each with `fixed_dose_combination: true` (C4): e.g. nabiximols (Sativex) → dronabinol + cannabidiol. Names are mapped to moieties again by script after coding, so do not invent an INN. |
| `role` | See 3.1 |
| `delivery_enabling` | true if, and only if, `role` is `delivery_enabling_agent` (C11) |
| `device_dependent` | true if the agent is a candidate whose antitumour effect needs a device for activation or delivery (C12): photodynamic/sonodynamic therapy, focused-ultrasound-enabled delivery, laser- or light-activated drugs. Set it to true whenever the record pairs the candidate with device-enabled delivery or activation, whether or not the record says the device is needed for the antitumour effect (R4). Otherwise false. |
| `formulation_flag` | `new_formulation`, `new_route` (e.g. intranasal, intra-arterial, convection-enhanced, intratumoral), `prodrug`, `biosimilar`, or `none` |
| `regimen_id` | Same ID for every component of a named multi-drug regimen (e.g. CUSP9) |
| `arms` | The registered arm/group labels in which the agent is given, copied exactly from the record's arm labels; an empty list if the record has no arms. The role is the agent's role in the **experimental** arms; if it differs between arms, note it in `coder_notes`. |
| `drug_class_hint` | Free text: what the coder believes the agent is ("antidiabetic", "investigational EGFR inhibitor"). **Not used for classification.** It only helps the [LOOKUP] step catch mapping errors. |

### 3.1 Intervention role — decision rules

Work through the rules in order and use the first that applies.

0a. Cell therapy, gene therapy, oncolytic virus or cancer vaccine (section 1.2) → `excluded_intervention_type` (C2).
0b. Imaging tracer, contrast agent, or agent used only for diagnosis or fluorescence-guided surgery → `diagnostic_agent` (C2).
1. The agent is in a comparator, placebo or control arm only → `control_comparator`.
2. Its stated purpose is symptom control (seizures, oedema, nausea, fatigue, cognition, pain, anaesthesia) and the record states **no** antitumour hypothesis or antitumour outcome → `supportive`. If the record states an antitumour hypothesis or outcome (e.g. "levetiracetam as a sensitizer of chemoradiation"), it is a candidate (rule 4 or 5). Conditioning or lymphodepleting chemotherapy given to prepare for a cell therapy (e.g. cyclophosphamide, fludarabine) is also `supportive` and is listed (R6).
2b. Its stated purpose is to enable or increase delivery or exposure of another agent (BBB opening, pharmacokinetic boosting, efflux-pump inhibition) and the record states no antitumour hypothesis for the agent itself → `delivery_enabling_agent` (C11). If the record does state its own antitumour hypothesis, it is a candidate and `uncertain: true`.
3. Standard-of-care treatment given equally in all arms, or described as background (e.g. temozolomide with radiotherapy in "Stupp + X") → `soc_backbone`. **Also** a drug patients are already receiving before entry, or that every arm receives, even if it is not GBM standard of care (C3): e.g. in "hydroxychloroquine added to ongoing dabrafenib + trametinib", dabrafenib and trametinib are `soc_backbone`. The trial's own investigational question decides which agent is the candidate.
   Two exceptions come before rule 3: (i) an established GBM therapy whose own dose, schedule or route differs between arms, or is named as the question, goes to rule 6 (R2); (ii) a drug whose device-enabled delivery or activation is the question is a candidate (rule 4 or 5, with `device_dependent: true`), even if patients were already planned to receive it (C12 overrides C3; R5).
4. It is the only **investigational** agent in an experimental arm → `experimental_monotherapy`, **even when given on a standard backbone** (C1). The components of one fixed-dose combination product count as one investigational agent: if that product is the only investigational one, each component is `experimental_monotherapy` (R3).
5. It is one of two or more **investigational** agents in an experimental arm → `experimental_combination`.
6. An **established GBM therapy** (temozolomide, carmustine IV or wafer, lomustine, bevacizumab; D6) is itself the subject of investigation in a new schedule, dose, route or setting → `established_therapy_experiment`. This is reported separately and is not a candidate.

Only roles 4 and 5 are **candidate agents**. A trial with no candidate agents is excluded at S6 (`established_therapy_only`, `excluded_intervention_type` or `no_pharmacological_candidate`).

Worked examples (C1, C3, C11–C13):

| Record says | Coding |
|---|---|
| Radiotherapy + temozolomide + chloroquine vs radiotherapy + temozolomide | chloroquine `experimental_monotherapy`; temozolomide `soc_backbone`; trial `regimen: combination` |
| Pembrolizumab + an investigational vaccine | pembrolizumab `experimental_monotherapy`; vaccine `excluded_intervention_type` |
| Nivolumab + ipilimumab, both investigational | each `experimental_combination` |
| Hydroxychloroquine added for patients already on dabrafenib + trametinib | hydroxychloroquine `experimental_monotherapy`; dabrafenib, trametinib `soc_backbone` |
| Perflutren microbubbles with focused ultrasound to open the BBB for carboplatin | perflutren `delivery_enabling_agent`, `delivery_enabling: true`; carboplatin candidate with `device_dependent: true` |
| 5-ALA sonodynamic therapy | aminolevulinic acid candidate, `device_dependent: true` |
| 5-ALA for fluorescence-guided resection only | aminolevulinic acid `diagnostic_agent` |
| [18F]-FET PET or gadolinium | `diagnostic_agent` |
| "Up to 3 FDA-approved drugs chosen by an ex vivo drug screen", no drugs named | one agent row: `active_moiety: unspecified_approved_panel`, candidate role, describe the selection in `drug_class_hint` (C13) |

---

## 4. Drug origin (per candidate agent, judged at each trial's start date)

### 4.1 [LOOKUP] fields (scripted, per active moiety)

The [LOOKUP] scripts (`05_lookup_drugs.py`) collect **current** FDA/EMA/ChEMBL records for each moiety. These are **discovery aids only** (D20). Classification uses the **dated regulatory event table** `data/reference/regulatory_events.csv`, one row per approval event:

| Column | Content |
|---|---|
| `moiety` | normalised active moiety (agent dictionary) |
| `jurisdiction` | `FDA` or `EMA` |
| `event_type` | `original` (first approval of the product) or `new_indication` (efficacy supplement / extension of indication) |
| `indication` | indication text as approved at that date |
| `oncology` | yes/no: a cancer treatment indication (supportive-care indications such as antiemesis are `no`) |
| `tumour_agnostic` | yes/no: indication defined by a molecular feature across tumour types |
| `glioma` | yes/no: a glioma treatment indication (not diagnostic or visualisation) |
| `date_lo`, `date_hi` | earliest and latest possible approval date (equal when the day is known; an interval when only month or year is known) |
| `source`, `source_url` | document the date and indication come from (Drugs@FDA approval letter, label history, EPAR procedural steps) |
| `reviewed_by`, `review_date` | human reviewer of the row |

Every row that can change a candidate's category or flags is human-reviewed before the analysis. Current label text and ChEMBL indications are used only to find events.

### 4.2 [RULE] decision tree (the trial start date is T; only events with `date_hi` ≤ T count as "before T")

```
Is the agent an established GBM therapy (D6 list)?               -> ESTABLISHED (reported separately; not a candidate)
Any FDA or EMA approval event on or before T?
 ├─ yes: Is the EARLIEST approval event a glioma treatment indication
 │       (e.g. vorasidenib, tovorafenib, dordaviprone)?
 │        └─ yes -> GLIOMA_DEVELOPED (reported separately)
 │       Any oncology approval event on or before T?
 │        ├─ no  -> 2a  non-oncology repurposing
 │        └─ yes -> 2b  oncology repurposing (approved for another tumour)
 │       Dated flags on category 2:
 │        tumour_agnostic_at_T     a tumour-agnostic approval event on or before T
 │        population_within_label  the trial's GBM population and regimen already fall within an
 │                                 approved indication at T (e.g. BRAF V600E solid tumours + dabrafenib/trametinib)
 │        glioma_label_at_T        a glioma approval event on or before T that was not the first approval
 └─ no:  Did it reach Phase 2 or later in a non-GBM indication before T (dated trial or publication)?
          ├─ yes      -> 3  investigational repositioning
          ├─ no       -> 1  operational de novo (no prior approval or later-phase non-GBM development)
          └─ unknown  -> UNRESOLVED (human adjudication; the analysis cannot run while any remain, D26)
```

Two axes are also reported for every candidate (D20c): **regulatory status at T** (approved oncology / approved non-oncology / unapproved) and **highest prior non-GBM development phase at T** (none, 1, 2, 3, approved).

**Date intervals.** If an event's interval contains T (`date_lo` ≤ T < `date_hi`), the classification is computed both ways; if it differs, the candidate is flagged `date_sensitive` and the conservative (event-not-yet-happened) result is used, with a sensitivity analysis.

**Category 2c no longer exists (D20b).** Tumour-agnostic approval is the dated flag `tumour_agnostic_at_T`.

Notes:
- **Agent-level origin** is taken from the agent's earliest eligible trial (D12). **Index-date origin** (T = 2026-07-31) is computed as well, for sensitivity analysis 3.
- **Approvals outside FDA/EMA** (e.g. China NMPA only) do not count. Set `other_regulator_only: true`.
- **Biosimilars** take the origin of the reference product.
- **New formulations or routes** of an approved moiety are coded with the moiety's origin and the `formulation_flag`.
- If the evidence for category 3 lacks dates or is ambiguous → `UNRESOLVED`, human adjudication. Record the evidence (trial ID or publication) in Table S2.
- **5-aminolevulinic acid** has a GBM *visualisation* label only. It is not an established therapy; classify it by the tree (its approvals are diagnostic).

### 4.3 Trial-origin groups [RULE]

| Group | Definition |
|---|---|
| `repurposing_containing` | At least one category-2 candidate (2a or 2b) |
| `repurposing_2a_containing` | At least one 2a candidate |
| `de_novo_only` | Only category-1 candidates |
| `repositioning_only` | Category-3 candidates and no category-2 candidates |
| `mixed_origin` | At least one category-2 candidate **and** at least one category-1 candidate (a subset of `repurposing_containing`; excluded in sensitivity analysis 6) |

**Unspecified approved-drug panels (C13, D19).** A candidate coded `unspecified_approved_panel` has no moiety, so it gets no [LOOKUP] and is **excluded from agent-level counts**. At trial level it counts as category 2 (subtype unknown), so the trial is `repurposing_containing` (not `repurposing_2a_containing`). These trials are listed separately and sensitivity analysis 12 excludes them.

**Delivery-enabling agents (C11, D19)** are not candidates and are reported separately, like established therapies, with their own origin from the tree for description only.

---

## 5. Biomarkers (per trial) [LLM]

List every **tumour** molecular biomarker mentioned in the eligibility, design, arms or outcomes, one row each (C6). Do **not** record germline pharmacogenomic or safety markers (HLA type, G6PD, DPYD, TPMT). A biomarker has role `eligibility` only if it is an **entry requirement**; a description of disease history or prior therapy (e.g. "previously treated with temozolomide regardless of MGMT") is not an eligibility biomarker.

| Field | Values |
|---|---|
| `biomarker` | `MGMT`, `IDH`, `EGFR_EGFRvIII`, `BRAF`, `NTRK`, `H3K27M`, `CDKN2A_B`, `PTEN_PI3K`, `CDK4_6_pathway`, `FGFR`, `MET`, `PD_L1`, `TMB_MMR`, `other` (specify), `none` |
| `role` | `eligibility` (required to enter the trial), `enrichment` (required for a cohort or arm), `stratification` (prospective randomisation or stratification factor), `pharmacodynamic`, `exploratory_correlative` |
| `candidate_matched` | true if the biomarker is mechanistically linked to a candidate agent in this trial (name the agent). Examples: EGFR amplification + EGFR inhibitor; BRAF V600E + BRAF/MEK inhibitor; MTAP deletion + PRMT5/MAT2A inhibitor; CDKN2A loss + CDK4/6 inhibitor. **IDH-wildtype** (a diagnostic criterion) and **MGMT status** (linked to the temozolomide backbone) are **never** candidate-matched, unless the candidate is an MGMT-targeting agent. |
| `source_quote` | Verbatim quote |
| `arms` | Registered arm/group labels the biomarker requirement applies to, copied exactly; empty list if it applies to the whole trial or the record has no arms |

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

`delivery_enabling_agent` is a **role** (section 3.1), not a mechanism. Calibrate on at least 40 agents spanning all origin categories before the main pass.

---

## 7. Adjudication, validation and outputs

1. **Coders A and B** produce JSON per trial independently (`outputs/coderA/`, `outputs/coderB/`).
2. **Compare** (`[CODE]`, `scripts/07_compare_coders_v2.py`): every disagreement on **any** coded field (including matched agent, every biomarker identity × role × match, every agent flag, arms, control-arm and industry coding), every item marked `uncertain` by either coder, and every record missing from the expected 870-record manifest goes to `adjudication_queue.csv`.
3. **Human adjudication:** XL decides; drug-origin and clinical questions go to the clinical co-author. Each decision is recorded with its reason.
4. **Agreement** before adjudication: Cohen's kappa + PABAK or Gwet's AC1 for each binary or categorical variable; percentage agreement for multi-category items. Agreement measures reproducibility between coders, not correctness; calibration agreement is development-set performance (D21).
5. **Human review (D21), before any analysis.** (a) *Correction:* XL reviews every unique candidate's origin (one evidence sheet per agent, from the event table) and every positive `candidate_matched` decision on an eligibility/enrichment biomarker, blinded to drug origin. Ambiguous reference labels go to a second expert (clinical co-author). (b) *Measurement:* a stratified random sample of AI-agreed negatives and exclusions, drawn by `scripts/08_draw_validation_sample.py` (hash frozen before the main pass) from records not used in calibration, coded by XL blind to AI output. Report variable-specific confusion matrices, sensitivity, specificity, PPV and NPV with 95% CIs and sampling weights. (c) *Escalation:* if the weighted rate of clinically important misses (an eligible trial excluded, or a candidate-matched selection missed) exceeds 5% for a variable, every record is human-coded for that variable.
6. **External checks (D10):** ReDO agreement with an exact CI; a human checks 30 random de novo agents.

## 8. Calibration (before the main pass)

- Draw 40 records stratified by search source (main vs supplementary), phase group and sponsor class. Run both coders, then XL reviews.
- Revise only how rules are applied (wording, examples). Do not change definitions without a dated amendment.
- Round 2 confirmed the v1.1 fixes; v1.2 added wording fixes R1–R9. After the methods review (2026-11-02), v1.3 added D20–D26. Round 3 (`outputs/calibration_r3/calibration_report_r3.md`, 20 fresh records) tested v1.3; v1.4 adds D27 and wording fixes W1, W2, W7 and is **frozen**: checksums in `FROZEN_v1.4.sha256`. No fourth round: none of the round-3 fixes changes candidate status or the primary outcome.

## Amendments

| Version | Date | Change |
|---|---|---|
| 1.1 | 2026-11-01 | After calibration round 1 (`outputs/calibration/calibration_report.md`). Clarifications of how rules apply: C1 (roles count investigational agents only; `regimen` includes the backbone), C2 (new roles `excluded_intervention_type`, `diagnostic_agent`), C3 (drugs already received or in every arm = `soc_backbone`), C4 (split fixed-dose combinations), C5 (moiety naming), C6 (tumour biomarkers only; entry requirements only), C7 (where glioblastoma must be named), C8 (`cns5_terminology` definitions), C9 (narrower `uncertain` rule), C10 (advanced/refractory = recurrent); verbatim-quote rule tightened. Scope decisions (D19, XL 2026-11-01): C11 delivery-enabling agents are not candidates (new role `delivery_enabling_agent`); C12 drug–device therapies are candidates with `device_dependent` (sensitivity analysis 11); C13 unspecified approved-drug panels counted at trial level only (sensitivity analysis 12). Schema v1.1. |
| 1.2 | 2026-11-01 | After calibration round 2 (`outputs/calibration_r2/calibration_report_r2.md`). Wording only, no definition changes: R1 `regimen` not_applicable without a candidate; R2 rule 6 before C3 for established therapies whose schedule differs; R3 fixed-dose combination components count as one agent for role; R4 `device_dependent` whenever device-enabled delivery or activation is paired; R5 C12 overrides C3; R6 conditioning chemotherapy = supportive; R7 prompt states `coder_notes` is a top-level field; R8 `control_arm_from_other_arms` values defined; R9 which agents to list. Schema v1.2 (manual_version only). Frozen for the main pass. |
| 1.3 | 2026-11-02 | After the methods review (`../methods_review_2026-11-02/`, decisions D20–D26). Origin derived from a dated regulatory event table; category 2c removed and replaced by the dated flags `tumour_agnostic_at_T` and `population_within_label`; explicit `UNRESOLVED` state; two dated origin axes; new trial-level variables `tumour_pk_planned` and `target_engagement_planned`; `arms` links on agents and biomarkers; Early Phase 1 records coded as a translational subset; human review and validation redesigned (D21); full-field comparison with manifest. Schema v1.3. |
| 1.4 | 2026-11-02 | After calibration round 3. D27: (A) `industry_support_in_text` dropped; (B) glioblastoma may be named in a registered arm/group label, not in summary/description; (C) grade 4/IV astrocytoma or glioma without IDH = historical glioblastoma. Wording: W1 radiopharmaceutical naming, W2 INN spelling and generic names for excluded types, W7 when `tumour_pk_planned` / `target_engagement_planned` are `unclear`. Schema v1.4 (field removed). Frozen for the main pass. |
