# Open convention questions from the adjudication proposals (for XL)

Source: the 384 AI-drafted proposals (`proposals/`, review sheet `adjudication_review_sheet.xlsx`), 2026-11-03.
These are cases that manual v1.4 and rulings D30 R1–R8 do not settle, or that the proposal batches settled inconsistently. Each has a recommendation; the proposals already follow it unless marked **(proposals differ)**. Once XL rules, I will make every affected proposal follow the ruling before adjudication is finalised.

## A. Questions that can change the primary outcome (candidate-matched molecular selection)

| # | Question | Trials | Recommendation |
|---|---|---|---|
| A1 | A selection biomarker required only for a **non-GBM cohort** of a basket trial (GBM patients enter without it) | NCT04678648 (RAS), NCT06258018 (IDH-mut), NCT04908176 (KIT), NCT05538572 (CDKN2A), NCT06058988 (HER2), NCT05495295, NCT05082259 (PD-L1), NCT04430842 (LAT1), NCT06161519 (MYC/MYCN) | **Does not count.** The outcome describes how GBM patients are selected. Record the row as `exploratory_correlative` for GBM. **(proposals differ: most count it literally, at low confidence)** |
| A2 | Biomarker that is one optional route into the trial (e.g. "DLL3-positive **or** …") | NCT06814496 | Does not count as an entry requirement (as proposed). |
| A3 | Biomarker named only in the title or summary, not in eligibility or cohort definitions | NCT04430842 (LAT1), NCT03776071 (DGM1, contradictory) | Counts only if eligibility or a cohort definition requires it (as proposed for NCT03776071). |
| A4 | Biomarker stated only as an **exclusion** (e.g. "no RB1 loss", "no BRAF V600E") | NCT05843253, NCT06894979 | Counts as eligibility, because it restricts entry. Exception: A5. |
| A5 | Exclusions that only define CNS5 glioblastoma (IDH-mutant, H3K27M, 1p/19q-codeleted excluded) | NCT07338539, NCT06860594, NCT07431216, others | **Exempt** from `any_molecular_selection`, like the IDH-wildtype requirement. |
| A6 | Drug–target link not standard but stated in the record (MYC→TOP1 for PLX038); link not stated (EGFR for verteporfin) | NCT06161519, NCT04590664 | Matched only when the record states the link (manual §5): PLX038 yes (but see A1), verteporfin no. |
| A7 | Target positivity shown "by histology **or** PET" | NCT07648823 | Candidate-matched yes. Set `imaging_assessed` only when PET is the only route. |
| A8 | MGMT "status must be known/available" with no required value | NCT04225039, NCT05439278 vs NCT04552977 | Not selection (testing only). A required value (e.g. unmethylated) is eligibility. **(proposals differ)** |

## B. Questions that can change inclusion (S5 population, S6 candidate)

| # | Question | Trials | Recommendation |
|---|---|---|---|
| B1 | R7 scope: paediatric-labelled "pHGG WHO grade 3 or 4" | NCT06624371 (changes inclusion), NCT05553041, NCT07331064 | R7 applies whatever the paediatric label; age is handled at S4. |
| B2 | R7 scope: "malignant primary brain tumour grade III or IV" with no mention of glioma | NCT05169944 | Not covered: excluded (as proposed). |
| B3 | R7 scope: "grade III or higher" | NCT04521946 | Counts as grade 4 allowed. |
| B4 | R7 says terminology `historical`, but the record cites WHO 2021 | NCT07710690, NCT07306299 | `cns5`, by the manual's tie-break (as proposed). |
| B5 | Glioblastoma never named, but an IDH-wildtype cohort, or GBM only in the summary or measurability criteria | NCT05188508, NCT04190628, NCT05892653, NCT06832982 | Keep the registered rule C7 (excluded). List them as near-misses in the supplement. For NCT06832982, GBM appears only in exclusions, so not_glioblastoma. **(proposal said basket_gbm_eligible)** |
| B6 | Inclusion names GBM, but the arm label limits the glioma cohort to IDH1-mutant | NCT04851834 (both coders included it) | Follow the narrower definition: not_glioblastoma (as proposed). |
| B7 | A non-standard drug given identically in all arms, while only another product is randomised | NCT04888611 (camrelizumab), NCT05106296 (indoximod) | Keep it a **candidate**: C3 backbone status is for standard care only. **(proposals differ: they made it soc_backbone; NCT04888611 would then stay included)** |
| B8 | Low-dose cyclophosphamide, or a drug built into the product (IMV-001 in IGV-001), given to support a vaccine or cell therapy | NCT05366062, NCT04485949 | Part of the excluded therapy (an extension of R4), with role `excluded_intervention_type`. |
| B9 | Supportive drug with a stated non-antitumour purpose but survival outcomes (G-CSF, TJ107, romiplostim, perampanel) | NCT06649851, NCT04600817, others | `supportive`, unless the record states an antitumour hypothesis. Routine OS/PFS outcomes alone do not make it a candidate. |
| B10 | Unlabelled therapeutic-dose antibody given as a carrier with its imaging conjugate | NCT07210632 | `diagnostic_agent` (as proposed). |
| B11 | Boron neutron capture therapy: boron carrier (borofalan) | NCT05737212 | Device-dependent candidate (C12). Regimen monotherapy: the beam is the activating device. **(proposal said combination)** |
| B12 | R8: drug-screen results given to the treating physician as recommendations ("clinically approved drugs") | NCT05857969 | `unspecified_approved_panel` (as proposed). |
| B13 | Approved drug fixed in some arms, dose not studied | NCT05785754 (pembrolizumab) | Candidate (`experimental_combination`), as proposed. |
| B14 | Investigational drug in an arm registered as ACTIVE_COMPARATOR | NCT05120284, NCT07284069, NCT06749925, NCT03776071 | Decide from the description, not the arm type: candidate (as proposed). |
| B15 | Glioma enrolled alongside non-glioma brain tumours | NCT06753617, NCT05096481, NCT05278208 | `basket_gbm_eligible` (as proposed). |

## C. Secondary variables and Figure 1 labels

| # | Question | Recommendation |
|---|---|---|
| C1 | S6 reason when the tested intervention is a device or radiotherapy (TTFields, Y-90, RT schedules, NanoTherm) | `excluded_intervention_type`; `no_pharmacological_candidate` only when no non-drug intervention is tested either. **(proposals differ)** |
| C2 | `combination_partners`: include co-candidates? | List every other drug and radiotherapy given with the candidate, co-candidates included. **(batch 23 differs)** |
| C3 | Regimen when standard chemoradiation follows trial treatment sequentially; regimen in baskets | Only concurrent agents count (NCT05074992 monotherapy). In baskets, code the GBM arms (NCT06047379). |
| C4 | `control_arm_from_other_arms` for dose-escalation cohorts registered as arms | "no" (as proposed). |
| C5 | Tumour PK from imaging dosimetry of a radioligand; a "PK/PD" tissue sample read only for molecular change | Dosimetry = yes (it measures the drug itself); PD-only readout = no. NCT07655869, NCT05644080 yes; NCT07416188 no. **(proposal said yes for NCT07416188)** |
| C6 | Target engagement when a PD objective is stated but no measurement is described | "unclear". **(proposals said yes for NCT04982926, NCT04430842, NCT04195555)** |

## D. Evidence checks needed outside the registry

- **R5 licensing (Table S2):** a candidate only if licensed as a medicine anywhere. To check:
  - elemene (NCT04674527; the agent's claim of a China licence needs a source)
  - oxaloacetate (NCT04450160)
  - silibinin (NCT06964815)
  - LipoCurc curcumin (NCT05768919)
  - Salovum (NCT05669820)
  - Niacin CRT (NCT04677049)
  - IV ascorbate (NCT04900792)
  - TN-TC11G THC+CBD (NCT03529448)
  - manganese chloride and Sapylin (NCT05131711)
- **Agents the record never identifies:** XS005 (NCT06147505), APG-157 (NCT06011109), NRG-103 (NCT07710690).
- **Data quality:**
  - NCT07628062 has a GBM official title but HPV-positive throat cancer in every other field; check the live entry.
  - NCT07480941 and NCT07551336 describe themselves as "example records".

## E. Changes to coder agreement (for awareness; each also appears in the review sheet)
- **40 trials:** the proposal changes inclusion relative to at least one coder.
  - 15 that both coders included would be excluded: 12 through R3/R4/R8, 1 through R5 licensing (NCT04450160), 1 through the R4 exception (NCT04642937) and 1 through B6 (NCT04851834).
  - 5 that both coders excluded would be included, through R7.
- **8 trials:** the proposal changes the primary outcome relative to a coder.
