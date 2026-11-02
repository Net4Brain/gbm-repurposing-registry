# Drug repurposing in the adult glioblastoma clinical trial pipeline — analysis pipeline

Code, frozen data snapshots and AI-coding records for a registry-based cross-sectional study:
*Repurposed drugs in the contemporary glioblastoma clinical trial landscape: a registry-based analysis*
(target journal: Neuro-Oncology Advances). Corresponding author: Xinzhong Li, Teesside University.

**Status:** coding manual **v1.4 frozen** for the main pass (`FROZEN_v1.4.sha256`), after three calibration rounds and a methods review (2026-11-02). v1.2 was frozen earlier but superseded before any main pass. Registered on OSF (https://osf.io/gn8v5, embargoed, 2026-11-02). Two-expert validation sample of 100 records drawn (D28). No main-pass coding has been done and results are not yet available.

## What the study does
- **Cohort:** interventional adult glioblastoma drug trials on ClinicalTrials.gov that started between 2020-01-01 and 2026-07-31, regardless of status. Trials active on 2026-07-31 form a secondary subset.
- **Classification:** every experimental agent is classified, at the start date of the trial it is in, as *de novo* (1), approved-drug repurposing (2a non-oncology, 2b other-tumour oncology, 2c tumour-agnostic) or investigational repositioning (3). Classification uses FDA, EMA and ChEMBL records.
- **Primary comparison:** candidate-matched molecular selection in repurposing-containing vs *de novo*-only trials.

The full rules are in [`protocol_decisions.md`](protocol_decisions.md) (D1–D27) and [`coding_manual_v1.4.md`](coding_manual_v1.4.md) (frozen; v1.0–v1.3 are kept for the record).

## Repository layout
| Path | Contents |
|---|---|
| `protocol_decisions.md` | Dated, frozen protocol decisions and amendments |
| `coding_manual_v1.4.md`, `schema/*.v1.4.json`, `prompts/*_v1.4.md` | Frozen versions the AI coders and human adjudicators work from (older versions kept alongside) |
| `FROZEN_v1.4.sha256` | Checksums of the frozen manual, schema, prompts, decision log, scripts and tests for the main pass |
| `FROZEN_v1.2.sha256` | Checksums of the earlier v1.2 freeze (historical) |
| `data/reference/` | Dated regulatory event and development event tables (human-reviewed; D20) |
| `tests/` | Tests for the origin rules |
| `scripts/01_retrieve_ctgov.py` | Main ClinicalTrials.gov retrieval (API v2) |
| `scripts/02_supplementary_search.py` | CNS5 / brain-tumour / eligibility-text supplementary search |
| `scripts/03_build_coder_input.py` | Identical plain-text input for both coders, one per trial |
| `scripts/04_select_calibration.py` | Stratified 40-record calibration sample (seed 20261101) |
| `scripts/05_lookup_drugs.py` | FDA / EMA / ChEMBL lookups per active moiety (cached in `data/lookup/v1.2/`) |
| `scripts/02b_filter_supplementary.py` | Rule that selects the 36 supplementary records for screening; writes the rejected list for audit |
| `scripts/04b_select_calibration_r3.py` | 20 fresh records for calibration round 3 (seed 20261102) |
| `scripts/06_derive_origin.py` | Drug-origin decision tree, v1.2 (superseded; kept unchanged) |
| `scripts/06_derive_origin_v2.py` | Drug-origin decision tree from dated events, with `UNRESOLVED` gate (manual v1.3 §4.2) |
| `scripts/07_compare_coders.py` | Coder comparison used for rounds 1–2 (kept unchanged) |
| `scripts/07_compare_coders_v2.py` | Full-field coder comparison checked against the expected record list, plus an outcome-relevant biomarker check |
| `scripts/08_draw_validation_sample.py` | Negatives-only validation sample (D21; superseded by D28, not used) |
| `scripts/08b_draw_expert_sample.py` | Draws the 100-record two-expert validation sample (D28) |
| `scripts/00_fetch_redo.sh` | Downloads ReDO_Trials_DB and stops with an error if it differs from the frozen checksum |
| `data/raw/` | Frozen registry snapshots and EMA report (checksums in `CHECKSUMS.sha256`) |
| `data/processed/` | Screening additions, calibration set |
| `data/coder_input/` | Coder input files for the 870 **screening records** (not 870 eligible trials) |
| `outputs/calibration/` | Calibration round 1 (manual v1.0): coder A/B outputs, adjudication queue, agreement, report |
| `outputs/calibration_r2/` | Calibration round 2 (manual v1.1): same 40 records, outputs, agreement, report |
| `outputs/calibration_r3/` | Calibration round 3 (manual v1.3): 20 fresh records, outputs, run logs, agreement, report |
| `outputs/supplementary_filter_audit.md` | Reproduction of the 36 supplementary additions and audit of the 797 rejected records |
| `logs/` | Exact queries and hit counts for every retrieval |

## Reproducing the analysis
Requirements: Python 3.13 (packages in `requirements.txt`), R ≥ 4.5 for figures and statistics (added later).

```bash
pip install -r requirements.txt
sha256sum -c CHECKSUMS.sha256          # macOS: shasum -a 256 -c CHECKSUMS.sha256
bash scripts/00_fetch_redo.sh          # REQUIRED: calibration sampling (04) and external validation (D10)
bash run_all.sh                        # rebuilds the stages listed in run_all.sh (screening set, samples, comparisons, tests)
```

What each kind of output gives you:
- **Exactly reproducible now:** the stages in `run_all.sh`: supplementary filter, coder inputs, calibration samples, coder comparisons and origin-rule tests. Origin derivation, validation, statistics, tables and figures will be added as they are built.
- **Re-runnable, but results may drift:**
  - *Retrieval* (`01`, `02`): ClinicalTrials.gov changes over time. The frozen snapshots and query logs are the reference.
  - *Drug lookups* (`05`): FDA, EMA and ChEMBL change over time. The dated cache in `data/lookup/v1.2/` is the reference.
  - *AI coding*: model outputs are not deterministic. The exact prompts, manual version, model IDs (Claude Opus 5.5 = coder A, Claude Sonnet 5.5 = coder B; D18) and every coder output are archived. Re-running the coding tests agreement; it does not reproduce outputs byte for byte.

## Data sources and licences
| Source | Terms |
|---|---|
| ClinicalTrials.gov (NLM) | Public domain (U.S. Government) |
| openFDA / Drugs@FDA | Public domain (U.S. Government) |
| EMA medicines report | EMA content reusable with acknowledgement of the source |
| ChEMBL (EMBL-EBI) | CC BY-SA 3.0 (cached excerpts in `data/lookup/`) |
| ReDO_Trials_DB (Pantziarka et al., Front Pharmacol 2021) | Licence not stated. **Not redistributed**; fetch with `scripts/00_fetch_redo.sh` and verify the checksum. |

Code: MIT licence (`LICENSE`). Derived data created by this project: CC BY 4.0.

## Superseded files (kept locally, not in the repository)
Drug-lookup caches from script versions 1.0 and 1.1 (`data/lookup/*.json`, `data/lookup/v1.1/`) had two bugs that version 1.2 fixed: loose FDA ingredient matching, and an oncology flag triggered by supportive-care label wording (see `outputs/calibration/calibration_report.md` §4).

## Citation
To be added (Zenodo DOI at OSF registration / publication).
