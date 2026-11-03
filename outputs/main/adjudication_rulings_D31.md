# Adjudication conventions (proposed D31) — XL, 2026-11-03

XL accepted every recommendation in `adjudication_convention_questions.md` ("Accept all recommendations", 2026-11-03). These conventions interpret coding manual v1.4 and rulings D30 for adjudication. They change no coder output; final values are set in the adjudication table. The IDs below are cited as "D31-A1" etc.

## A. Molecular selection (primary outcome and any_molecular_selection)
- **A1** A biomarker that is required only for a non-GBM cohort of a basket trial, while GBM patients enter without it, is **not** selection for this trial. Code the row `exploratory_correlative` (not eligibility or enrichment). The trial's `candidate_matched_selection` and `any_molecular_selection` follow from the GBM patients' entry requirements only.
- **A2** A biomarker that is only one optional route into the trial ("X-positive or …") is not an entry requirement and does not count.
- **A3** A biomarker counts only if the eligibility criteria or a cohort definition require it. A mention only in the title or summary does not count.
- **A4** A biomarker stated as an exclusion ("no RB1 loss", "no BRAF V600E") counts as eligibility, because it restricts entry. It is candidate-matched under manual §5 if linked to a candidate. A5 is the exception.
- **A5** Exclusions that only define CNS5 glioblastoma (IDH-mutant, H3K27M-altered, or 1p/19q-codeleted tumours excluded) are exempt from `any_molecular_selection`, like the IDH-wildtype requirement.
- **A6 (corrected 2026-11-03)** As manual §5 says, a biomarker is candidate-matched when it is mechanistically linked to a candidate. The link may be stated in the record or come from the candidate's established pharmacology (e.g. EGFR amplification + EGFR inhibitor, IDH-mutant + PARP inhibitor). If the candidate's mechanism is not known (an undisclosed code-named agent) and the record states no link, the match waits for a §D evidence check and the trial is flagged; it is not set to false. Examples: verteporfin and EGFR are not linked (verteporfin does not act on EGFR); PLX038 and MYC/MYCN are linked as stated in the record (but A1 may apply).
  - *The first wording ("only when the record states the link") was stricter than manual §5. It was applied in a few revision batches before being put on hold, and those files are re-checked.*
- **A7** If target positivity can be shown by histology or by PET, the trial is candidate-matched. `imaging_assessed_selection` is true only when PET is the only route.
- **A8** "MGMT status must be known/available" with no required value is testing, not selection (`exploratory_correlative`). A required value (e.g. unmethylated) is eligibility.

## B. Inclusion (S5 population, S6 candidate)
- **B1** D30-R7 applies to "grade 3–4 glioma" wording even when labelled paediatric (e.g. "pHGG WHO grade 3 or 4"). Age is handled at S4.
- **B2** D30-R7 does not cover "malignant primary brain tumour grade III or IV" when glioma is not mentioned. These records stay excluded (`high_grade_glioma_unspecified` or `not_glioblastoma` as the record supports).
- **B3** "Grade III or higher" counts as grade 4 allowed under D30-R7.
- **B4** If an R7 record cites WHO 2021/CNS5, `cns5_terminology` is `cns5`, by the manual's tie-break.
- **B5** C7 is kept: glioblastoma must be named in the eligibility population. An IDH-wildtype cohort, or a GBM mention only in the summary, measurability or exclusion criteria, does not qualify. Such trials are listed as near-misses in the supplement (put "near-miss" in the note).
- **B6** When the inclusion criteria name GBM but an arm or cohort label narrows the glioma population to IDH-mutant, the narrower definition applies: `not_glioblastoma`.
- **B7** A non-standard drug given identically in all arms, while another product is randomised, stays a **candidate** (`experimental_combination`). Manual C3 backbone status (`soc_backbone`) is only for established standard care of the trial population (e.g. temozolomide, radiotherapy, bevacizumab in recurrent disease).
- **B8** Drugs given to support a vaccine or cell therapy (e.g. low-dose cyclophosphamide as an immune primer), and drug components built into a cell or vaccine product (e.g. IMV-001 in IGV-001), are part of the excluded therapy (an extension of D30-R4). Role: `excluded_intervention_type`.
- **B9** A drug whose stated purpose is supportive (e.g. G-CSF, TJ107 for lymphocyte recovery, romiplostim, perampanel for seizures) is `supportive`, even if routine OS/PFS outcomes are registered. It is a candidate only if the record states an antitumour hypothesis for it.
- **B10** An unlabelled antibody given at a therapeutic dose as the carrier for its own imaging conjugate is a `diagnostic_agent`.
- **B11** In boron neutron capture therapy, the boron carrier (e.g. borofalan) is a device-dependent candidate (C12). The regimen is monotherapy, because the neutron beam is the activating device.
- **B12** Under D30-R8, drug-screen results given to the treating physician as recommendations count as `unspecified_approved_panel` when the record says the drugs are clinically approved.
- **B13** An approved drug fixed in some arms whose dose is not studied is a candidate (`experimental_combination`).
- **B14** Roles are decided from the record's description, not the registered arm type. An investigational drug in an arm registered as ACTIVE_COMPARATOR is a candidate.
- **B15** A trial that enrols glioma alongside non-glioma brain tumours is `basket_gbm_eligible` (when GBM is named).

## C. Secondary variables and Figure 1 labels
- **C1** S6 exclusion reason when the tested intervention is a device or radiotherapy (TTFields, Y-90, RT schedules, NanoTherm, focused ultrasound alone): `excluded_intervention_type`. Use `no_pharmacological_candidate` only when no non-drug intervention is under test either.
- **C2** `combination_partners` lists every other drug and radiotherapy given with the candidate, co-candidates included.
- **C3** `regimen` counts only agents given concurrently with the candidate: standard chemoradiation that follows trial treatment does not make it a combination. In baskets, code the regimen of the GBM arms.
- **C4** `control_arm_from_other_arms` is "no" for dose-escalation or dose cohorts registered as separate arms.
- **C5** `tumour_pk_planned` is "yes" for imaging dosimetry of a radioligand in tumour (it measures the drug itself). A tissue or CSF sample read only for molecular or PD change is not tumour PK.
- **C6** `target_engagement_planned` is "unclear" when a PD objective is stated but no measurement is described.

## Clarifications from applying D31 (2026-11-03)
These keep the conventions in line with the manual. They add no new rule.
- **B7 and established GBM drugs:** B7 does not apply to established GBM drugs (temozolomide, carmustine, lomustine, bevacizumab). Under manual rule 6 and D30-R1, these remain `soc_backbone` or `established_therapy_experiment` and are never candidates.
- **C2 and excluded components:** `combination_partners` lists drugs and radiotherapy given with a candidate. It does not list excluded products or their components (vaccines, cell products, conditioning chemotherapy for a cell therapy, adjuvants under D30-R4/D31-B8), because these are not pharmacological partners.
- **A2 scope:** A2 applies to an "or" inside an entry criterion ("X-positive or Y"), where some patients enter without the biomarker. A requirement for a whole GBM cohort or arm stays `enrichment` (manual §5: "required for a cohort or arm"), even if GBM patients can also enter other cohorts without it. A1 covers non-GBM cohorts. When every route requires a marker of the same pathway (e.g. PTEN/PI3K alteration or pS6), the requirement stands.
- **C1 scope:** `excluded_intervention_type` applies whenever a non-drug intervention is under test, including diagnostic, surgical and behavioural interventions. `no_pharmacological_candidate` is for trials whose only interventions are drugs that are not candidates.

## D. Evidence checks (no coding change until done)
- **R5 licensing (Table S2):** elemene, oxaloacetate, silibinin, LipoCurc, Salovum, Niacin CRT, IV ascorbate, TN-TC11G, manganese chloride / Sapylin.
- **Unidentified agents:** XS005, APG-157, NRG-103.
- **Data quality:** NCT07628062, NCT07480941, NCT07551336.

Until each check is done, the proposal stays as drafted, with `needs_xl_attention` true.
