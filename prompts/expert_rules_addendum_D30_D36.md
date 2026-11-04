# Rules addendum for expert coders (adjudication rulings D30–D36)

These rules were added after the main coding pass to settle questions that coding manual v1.4 left open. The final adjudicated data follow them. They are given here as rules only: no trial is named, and the examples are generic.

## Candidates (step S6)
- **Device-delivered established GBM drugs.** An established GBM drug (temozolomide, carmustine, lomustine, bevacizumab) given with focused-ultrasound blood–brain-barrier opening, or another device, is an established-therapy experiment (`established_therapy_experiment`), not a candidate.
- **Gene and cell suicide therapies.** A prodrug activated by a gene or cell suicide therapy (e.g. 5-FC with a cytosine-deaminase vector, valganciclovir with HSV-tk) is part of that excluded therapy (`excluded_intervention_type`).
- **Supporting agents for cell therapies and vaccines.** Cytokines, adjuvants, immune primers (e.g. low-dose cyclophosphamide) and drug components built into the product are part of the excluded therapy. The exception is an agent tested as an antitumour agent in its own right, with its own arm or as the subject of an outcome; that agent is a candidate.
- **Conditioning chemotherapy** before a cell therapy is `supportive`.
- **Botanicals, supplements and medical foods.** These are candidates only if licensed as a medicine. A product developed as an investigational drug (an FDA IND programme, Fast Track or Orphan designation) is treated as any investigational drug. A product whose active ingredients are licensed medicines is a candidate.
- **Chemosensitisers** that act on the tumour to potentiate another drug (e.g. O6-benzylguanine) are candidates.
- **Drugs assigned by a drug screen or genomic test with no drugs named.** Code `unspecified_approved_panel` only if the record says the drugs are approved; otherwise there is no candidate. This also applies when the screen results are recommendations to the treating physician.
- **Non-standard drugs given to all arms.** A non-standard drug given identically in all arms, while another product is randomised, stays a candidate (`experimental_combination`). Only established standard care is `soc_backbone`.
- **Supportive drugs.** A drug whose stated purpose is supportive (e.g. G-CSF, anti-seizure, lymphocyte recovery) is `supportive`, even if routine OS/PFS outcomes are registered. It is a candidate only if the record states an antitumour hypothesis for it.
- **Imaging carriers.** An unlabelled antibody given at a therapeutic dose only as the carrier for its own imaging conjugate is a `diagnostic_agent`.
- **Boron neutron capture therapy.** The boron carrier is a device-dependent candidate, and the regimen is monotherapy.
- **Roles are decided from the description,** not the registered arm type. An investigational drug in an arm registered as ACTIVE_COMPARATOR is a candidate.
- **Approved drugs at a fixed dose.** An approved drug fixed in some arms, whose dose is not studied, is a candidate (`experimental_combination`).
- **Unnamed agents.** If the record does not name an agent (e.g. "PD-1/VEGF bispecific antibody"), code it with the description as written and say so in the notes.
- **S6 exclusion reason.** `excluded_intervention_type` applies whenever a non-drug intervention is under test (device, radiotherapy, diagnostic, surgical or behavioural). `no_pharmacological_candidate` applies when every intervention is a drug that is not a candidate.

## Population (step S5)
- **Grade 3–4 glioma.** "WHO grade 3–4 glioma" or "high-grade glioma (grade III/IV)", with grade 4 explicitly allowed, no IDH requirement and glioblastoma not named, counts as historical glioblastoma: `mixed_glioma_gbm_named`, `cns5_terminology: historical`. This also applies when the label is paediatric ("pHGG WHO grade 3 or 4"); age is handled separately. "Grade III or higher" counts as grade 4 allowed.
  - It does not apply to "malignant primary brain tumour grade III–IV" when glioma is not mentioned.
  - If the record cites WHO 2021/CNS5, code `cns5`.
- **Plain "high-grade glioma"** with no grade 4 stated is `high_grade_glioma_unspecified`.
- **Where glioblastoma must be named.** It must appear in the conditions, title, inclusion criteria or a registered arm/group label. A mention only in the summary, keywords, outcomes, measurability or exclusion criteria does not count. An IDH-wildtype cohort that never names glioblastoma does not count.
- **IDH-mutant arm labels.** If the inclusion criteria name GBM but an arm or cohort label narrows the glioma population to IDH-mutant, code `not_glioblastoma`.
- **Glioma with other brain tumours.** Glioma enrolled alongside non-glioma brain tumours is `basket_gbm_eligible`, when GBM is named.

## Biomarkers and candidate-matched selection
- **Non-GBM cohorts.** A biomarker required only for a non-GBM cohort, while GBM patients enter without it, is not selection. Code it `exploratory_correlative`.
- **Optional routes.** One optional route inside an entry criterion ("X-positive or …") is not an entry requirement. A requirement for a whole GBM cohort or arm is `enrichment`. When every route requires a marker of the same pathway (e.g. PTEN/PI3K alteration or pS6), the requirement stands.
- **Title or summary only.** A biomarker named only in the title or summary does not count; eligibility or a cohort definition must require it.
- **Exclusion-stated biomarkers** (e.g. "no RB1 loss") count as eligibility. The exception is exclusions that only define CNS5 glioblastoma (IDH-mutant, H3K27M-altered, 1p/19q-codeleted), which do not count as selection.
- **Candidate matching.** A biomarker is candidate-matched when it is mechanistically linked to a candidate, whether the record states the link or it follows from the candidate's established pharmacology. Assignment by a marker without a mechanistic link (e.g. TP53 mutation → a PARP inhibitor) is not a match.
- **Histology or PET.** If target positivity can be shown by histology or by PET, it is candidate-matched. Imaging-assessed selection is flagged only when PET is the only route.
- **MGMT.** "MGMT status known" with no required value is not selection.
- **Basket cohorts.** In baskets, a biomarker-defined cohort counts as GBM selection only if its definition names glioblastoma or primary CNS tumours.

## Trial-level variables
- **combination_partners** lists the other drugs and radiotherapy given with the candidate in the GBM arms, co-candidates included. Do not list devices, conditioning chemotherapy or adjuvants.
- **regimen** counts only agents given concurrently with the candidate.
  - Standard chemoradiation that follows trial treatment does not count.
  - A candidate given with an excluded antitumour therapy (vaccine, cell or gene therapy, oncolytic virus) is `combination`, with that therapy listed as partner.
  - In baskets, code the regimen of the GBM arms.
- **control_arm_from_other_arms** is "no" for dose cohorts registered as separate arms.
- **tumour_pk_planned** is "yes" for imaging dosimetry of a radioligand in tumour. A tissue or CSF sample read only for molecular or pharmacodynamic change is not tumour PK.
- **target_engagement_planned** is "unclear" when a pharmacodynamic objective is stated but no measurement is described.
