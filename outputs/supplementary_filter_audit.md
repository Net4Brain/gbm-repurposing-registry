# Supplementary-search filter: scripted reproduction and false-negative audit (D26, review R6a)

Date: 2026-11-02. Snapshot: `data/raw/ctgov_supp_raw_20261101T150223Z.json` (833 records not in the main pull).

## Reproduction
`scripts/02b_filter_supplementary.py` reproduces the original screening additions **exactly**: 36 kept (all because of the inclusion criteria), identical to `data/processed/supp_added_to_screening.csv`; 797 rejected.
- Outputs: `data/processed/supp_added_to_screening_02b.csv`, `data/processed/supp_rejected_02b.csv`.
- The first scripted version kept 34. It missed plural forms ("glioblastomas" in NCT04591431 and NCT06322342), which the original ad-hoc rule had matched. The regex now accepts plurals.

## False-negative audit of the 797 rejected records
The rule is the same as the eligibility rule (coding manual C7): glioblastoma must be named in the **title, conditions or inclusion criteria**. A rejected record is a false negative only if it names glioblastoma there in a form the regex misses.

| Check | Records |
|---|---|
| A glioblastoma term appears only in exclusion criteria, description or keywords | 29. Ineligible by rule C7 (named only where it does not count). |
| Only looser terms anywhere ("high-grade glioma", "malignant glioma", "GB", "grade IV") | 55 |
| Basket / solid-tumour / brain-tumour wording without naming glioblastoma | 413. Ineligible by rule (a basket must name glioblastoma). |
| Glioblastoma term in arm or intervention descriptions | 0 |
| **Synonyms in title, conditions or inclusion criteria** ("GB", "grade 4/IV" within 40 characters of glio-/astro-, glioblast-, gliosarc- stems) | **0** |

**Result:** no false negatives under the study's eligibility definition.

**Remaining limitation (for the Discussion):** basket trials open to "any solid tumour" without naming glioblastoma may enrol GBM patients but are excluded by design. 413 rejected records carry basket or brain-tumour wording; they are not eligible under the prespecified rule, and the paper should say so.
