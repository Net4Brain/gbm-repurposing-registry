# Drug repurposing in the adult glioblastoma clinical trial pipeline — analysis pipeline

Code, frozen data snapshots and AI-coding records for a registry-based cross-sectional study:
*Repurposed drugs in the contemporary glioblastoma clinical trial landscape: a registry-based analysis*
(target journal: Neuro-Oncology Advances). Corresponding author: Xinzhong Li, Teesside University.

**Status:** protocol finalised, calibration of the AI coders in progress; OSF registration pending. Results are not yet available.

## What the study does
- **Cohort:** interventional adult glioblastoma drug trials on ClinicalTrials.gov that started between 2020-01-01 and 2026-07-31, regardless of status. Trials active on 2026-07-31 form a secondary subset.
- **Classification:** every experimental agent is classified, at the start date of the trial it is in, as *de novo* (1), approved-drug repurposing (2a non-oncology, 2b other-tumour oncology, 2c tumour-agnostic) or investigational repositioning (3). Classification uses FDA, EMA and ChEMBL records.
- **Primary comparison:** candidate-matched molecular selection in repurposing-containing vs *de novo*-only trials.

The full rules are in [`protocol_decisions.md`](protocol_decisions.md) (D1–D18) and [`coding_manual.md`](coding_manual.md).

## Repository layout
| Path | Contents |
|---|---|
| `protocol_decisions.md` | Dated, frozen protocol decisions and amendments |
| `coding_manual.md`, `schema/`, `prompts/` | Exactly what the AI coders and human adjudicators work from |
| `scripts/01_retrieve_ctgov.py` | Main ClinicalTrials.gov retrieval (API v2) |
| `scripts/02_supplementary_search.py` | CNS5 / brain-tumour / eligibility-text supplementary search |
| `scripts/03_build_coder_input.py` | Identical plain-text input for both coders, one per trial |
| `scripts/04_select_calibration.py` | Stratified 40-record calibration sample (seed 20261101) |
| `scripts/05_lookup_drugs.py` | FDA / EMA / ChEMBL lookups per active moiety (cached in `data/lookup/v1.2/`) |
| `scripts/06_derive_origin.py` | Drug-origin decision tree (coding manual §4.2) |
| `scripts/07_compare_coders.py` | Coder A vs B comparison, adjudication queue, κ / PABAK / AC1 |
| `scripts/00_fetch_redo.sh` | Downloads ReDO_Trials_DB and checks it against the frozen checksum |
| `data/raw/` | Frozen registry snapshots and EMA report (checksums in `CHECKSUMS.sha256`) |
| `data/processed/` | Screening additions, calibration set |
| `data/coder_input/` | The 870 coder input files |
| `outputs/calibration/` | Coder A/B outputs, adjudication queue, agreement, calibration report |
| `logs/` | Exact queries and hit counts for every retrieval |

## Reproducing the analysis
Requirements: Python 3.13 (packages in `requirements.txt`), R ≥ 4.5 for figures and statistics (added later).

```bash
pip install -r requirements.txt
sha256sum -c CHECKSUMS.sha256          # macOS: shasum -a 256 -c CHECKSUMS.sha256
bash scripts/00_fetch_redo.sh          # optional: external-validation reference (D10)
bash run_all.sh                        # rebuilds every derived file from the frozen snapshots
```

What each kind of output gives you:
- **Exactly reproducible:** everything derived from the frozen snapshots and the archived coder outputs (coder inputs, calibration sample, comparison statistics, and later all tables and figures).
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
