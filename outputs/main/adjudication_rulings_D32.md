# Adjudication decisions on the flagged proposals (proposed D32) — XL, 2026-11-03

XL accepted the recommendations for all 40 flagged trials in `adjudication_review_sheet_v2.xlsx` ("do as you recommend"). Overrides of the latest proposal are listed with their basis in `adjudication_overrides_D32.json`. Final values are in `adjudicated_trials_D32.csv`, built by `scripts/11_build_adjudicated_table.py`.

## Groups
- **7 trials with no effect on the main analysis:** accepted as proposed. NCT02756312, NCT05313191 and NCT06964815 are registered as phase NA and fail S3. NCT04135807, NCT05182905, NCT05589961 and NCT06636162 are Early Phase 1 and count only in the translational subset.
- **13 evidence checks:** results below. The sources are web records found on 2026-11-03, plus established drug knowledge where marked.
- **20 judgement calls:** accepted as proposed, except NCT04642937, NCT05278208, NCT05914116, NCT06264388 and NCT07130149, which are overridden (see the JSON file).

## Rules
- **D32-1 (regimen):** a candidate given with an excluded antitumour therapy (vaccine, cell therapy, gene therapy, oncolytic virus) has `regimen: combination`, and that therapy is listed in `combination_partners`. This follows manual §2: "regimen counts all antitumour therapy in the experimental arm". Conditioning chemotherapy (supportive, manual R6) and adjuvants (part of the excluded therapy, D30-R4) are not listed. This supersedes the C2 clarification of D31 for excluded antitumour therapies.
- **D32-2 (scope of D30-R5):**
  - R5 applies to products tested as marketed botanicals, supplements or foods.
  - A product developed as an investigational drug (an FDA IND programme with Fast Track or Orphan designation, or a botanical drug programme) is assessed as any investigational drug. Examples: anhydrous enol-oxaloacetate, LipoCurc, APG-157.
  - A product whose active moieties are licensed medicines is a candidate. Examples: niacin, ascorbic acid injection, dronabinol + cannabidiol (TN-TC11G), manganese chloride injection.
- **D32-3 (biomarker cohorts in baskets):** a biomarker-defined cohort counts as GBM selection only if its definition names glioblastoma or primary CNS tumours, e.g. NCT06161519 cohort IIC, "any other ... primary CNS tumor with MYC or MYCN amplifications". A generic "other solid tumours" cohort does not count, e.g. NCT05933265 Supplement A.

## Evidence checks
| Trial | Agent | Finding | Result |
|---|---|---|---|
| NCT04674527 | elemene | Elemene injection was approved in China as an antitumour drug in 1994–1995 (CFDA, now NMPA). Sources: Molecules 2021;26:1499; Frontiers in Pharmacology 2023;14:1185987 | Candidate (R5, licensed), as proposed |
| NCT03529448 | TN-TC11G (THC+CBD) | A 1:1 THC/CBD oral product (Tilray, GEINO). Both moieties are licensed medicines (dronabinol, cannabidiol) | Candidate, as proposed (D32-2) |
| NCT04450160 | anhydrous enol-oxaloacetate | Investigational drug; MetVital press release reports FDA Fast Track for newly diagnosed GBM | **Candidate** (D32-2), which restores the coders' inclusion |
| NCT05768919 | LipoCurc (IV liposomal curcumin) | No marketing approval; FDA Orphan Drug Designation for GBM (SignPath, Dec 2025) | **Candidate** (D32-2); S5 decides inclusion |
| NCT05669820 | Salovum | EU food for special medical purposes, not a licensed medicine | Excluded (R5), as proposed |
| NCT04677049 | Niacin CRT | Controlled-release niacin; niacin is a licensed medicine | Candidate, as proposed |
| NCT04900792 | IV ascorbate | Ascorbic acid injection is a licensed medicine (FDA) | Candidate, as proposed |
| NCT05131711 | manganese chloride, Sapylin (OK-432) | Manganese chloride injection is licensed (trace element). OK-432 is a licensed streptococcal preparation (Picibanil, Japan; Sapylin, China; licence not found in the search, from drug knowledge) | Candidates under the R4 exception (in situ vaccination with no antigen product), as proposed |
| NCT06011109 | APG-157 | Botanical drug (curcumin-containing polyphenols) in an FDA programme with Fast Track/Orphan designation | Candidate (D32-2), as proposed |
| NCT06147505 | XS005 | NK-cell injection (trial protocol) | **Excluded**: cell therapy (D16) |
| NCT07710690 | NRG-103 | Oncolytic virus (NCT06757153 description) | **Excluded**: oncolytic virus (D16) |
| NCT07583771 | CS08399 | MTA-cooperative PRMT5 inhibitor (Chipscreen) | MTAP/CDKN2A matched (corrected D31-A6); trial still fails S5 (near-miss) |
| NCT07628062 | (record) | Live record checked 2026-11-03: the official title describes a recurrent glioblastoma study, but the brief title, conditions and eligibility describe HPV-positive oropharyngeal cancer | not_glioblastoma; listed as a registry data-quality issue |

## Still required by the protocol (not done by these decisions)
D21 correction review: XL must still personally review every **positive candidate-matched selection** decision and every candidate's **drug origin** before analysis. Accepting the recommendations here does not replace that review.
