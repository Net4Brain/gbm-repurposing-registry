# Pathway coding rules (D42) — DRAFT for XL review

Exploratory secondary analysis, added after registration (osf.io/gn8v5) and reported as a dated deviation. Descriptive
only: no hypothesis tests. These rules, the vocabulary and the coded table are fixed and confirmed by XL **before any
pathway count is produced**.

## 1. Question and scope

*Which pathways or biological processes do repurposed drugs test in adult GBM trials, and how often is the specific
drug–pathway hypothesis reflected in patient selection?*

- **Drugs:** the 92 unique approved-drug repurposing candidates of the primary cohort (category 2a or 2b at the agent's
  earliest trial start; D36 origin, D40 agent list): 31 non-oncology (2a) and 61 oncology (2b).
- **Trials:** every cohort trial in which one of these drugs is a candidate (191 drug–trial pairs). Repositioning and
  de novo candidates are out of scope.
- **Frozen inputs:** registry text (2026-11-01 snapshots), the coders' agent rows, `data/reference/agent_mechanism.csv`
  (D40) and the XL-confirmed biomarker–candidate pairs (D33). Nothing already adjudicated is recoded.

## 2. Units and tables

1. **Drug table** `data/reference/agent_pathway_D42.csv`: one row per drug, giving its default GBM hypothesis.
2. **Trial overrides** `data/reference/agent_pathway_trial_D42.csv`: one row per drug–trial pair **only when** that
   trial's record states a different GBM mechanism from the drug default. Example: a drug stated as an autophagy inhibitor in one
   trial and as a radiosensitiser in another.
3. The **drug → target → pathway → trial → matched selection** mapping is derived by script and becomes the
   supplementary table.

## 3. Fields (drug table)

| Field | Content |
|---|---|
| `active_moiety`, `subcategory` | As in the analysis tables (2a or 2b) |
| `target` | Molecular target(s) of the proposed GBM mechanism, HGNC gene symbols where possible, `;`-separated (BRAF; MAP2K1;MAP2K2) |
| `proposed_gbm_mechanism` | One short phrase (≤ 15 words) |
| `pathway_primary` | One level-2 pathway from §5, or `unclear` |
| `process_primary` | Its level-1 process (fixed by the vocabulary, not chosen) |
| `pathway_secondary` | At most two further level-2 pathways, `;`-separated; empty if none |
| `source_type` | `registry_stated`, `published_gbm_rationale`, `established_pharmacology` or `none` |
| `source` | NCT ID + field + verbatim quote; PMID; ChEMBL mechanism ID or label section |
| `differs_from_approved_use` | `yes` if the GBM hypothesis is not the mechanism behind the approved indication (metformin: AMPK/OXPHOS, not glycaemic control) |
| `confidence` | `high`, `medium` or `low` |
| `d40_consistent` | `yes`/`no`: does `process_primary` agree with the D40 mechanism class? (see §6) |
| `note` | Free text |

## 4. Source hierarchy

1. **Registry-stated.** The mechanism or rationale given in any of the drug's cohort records (brief or detailed
   description, arm description, outcomes), quoted. If records disagree, the drug default is the mechanism stated most
   often, and the others become trial overrides.
2. **Published GBM rationale.** Used when no record states a mechanism and the drug's approved pharmacology is **not**
   itself the antitumour hypothesis (most 2a drugs: chloroquine → autophagy, atovaquone → OXPHOS). It must be a PubMed
   article proposing or testing this mechanism in glioma or GBM, preferring clinical or in vivo work. Record the PMID.
3. **Established pharmacology.** ChEMBL mechanism or FDA/EMA label, used when the drug's pharmacological target is
   itself the antitumour hypothesis (most 2b drugs: dabrafenib → BRAF).
4. **`unclear`.** When none of the above gives a specific mechanism, or published rationales conflict without one
   dominating. `unclear` is a reported category, not a failure.

Multi-target drugs take as primary the target the record names; otherwise the target of the drug's main approved
antitumour use (regorafenib → angiogenesis, as in manual §6). ADCs are classified by their target, with the payload's
mechanism as secondary. Radioligands are classified by their delivery target, with radiation as secondary. Secondary
pathways are recorded only when a source supports them; plausibility alone is not enough.

## 5. Vocabulary (two levels, fixed)

Level 1 follows the approach of the Alzheimer's pipeline reports, which group agents into about 15 disease processes
(CADRO). Level 2 is anchored to the TCGA glioblastoma core pathways (RTK/RAS/PI3K, p53, RB), extended to the
non-oncogenic processes that repurposed drugs target.

| Level 1 process | Level 2 pathways |
|---|---|
| **P1 Receptor tyrosine kinase signalling** | EGFR/HER family; PDGFR/KIT; FGFR; MET; ALK/ROS1/NTRK; RET; multi-RTK |
| **P2 RAS–MAPK and PI3K–mTOR signalling** | RAS–RAF–MEK–ERK (MAPK); PI3K–AKT–mTOR; other intracellular kinases (BTK, PKC) |
| **P3 Developmental signalling** | Hedgehog; Notch; Wnt; Hippo–YAP/TEAD |
| **P4 Cell cycle and p53** | CDK4/6–RB; other CDK and mitotic kinases; p53–MDM2 |
| **P5 DNA damage response** | PARP; ATR/ATM/WEE1/CHK1; other DNA repair |
| **P6 Cytotoxic DNA damage and mitosis** | DNA alkylation and platinum; antimetabolite; topoisomerase; microtubule |
| **P7 Proteostasis, nuclear transport and cell death** | XPO1 nuclear export; proteasome and chaperones; apoptosis (BCL-2 family); oxidative stress and ferroptosis |
| **P8 Epigenetic regulation** | HDAC; DNMT; EZH2/PRC2; BET; other chromatin |
| **P9 Immune checkpoint** | PD-1/PD-L1; CTLA-4; LAG-3; other checkpoints (TIM-3, TIGIT) |
| **P10 Other immune modulation** | Cytokine agonists (IL-2/IL-15, GM-CSF, interferon); IL-6–JAK–STAT and inflammatory signalling; myeloid and MDSC modulation; innate sensing (STING, TLR); immunosuppressive metabolism (IDO, adenosine); T-cell redirection and antibody effector (bispecifics, CD38) |
| **P11 Angiogenesis and vasculature** | VEGF/VEGFR; other vascular and adhesion (angiopoietin, selectins) |
| **P12 Tumour metabolism** | Mitochondrial respiration/OXPHOS and AMPK; glycolysis; glutamine; lipid and cholesterol synthesis; nucleotide synthesis; polyamines; NAD+ |
| **P13 Autophagy and lysosome** | Autophagy–lysosome inhibition |
| **P14 Neural and ion-channel signalling** | Glutamate receptors (AMPA, NMDA); dopamine and serotonin receptors; GABA and voltage-gated channel ligands; other ion channels; cannabinoid receptors |
| **P15 Hormone and nuclear receptors** | Thyroid hormone; sex-steroid and mineralocorticoid receptors; retinoid and vitamin D |
| **P16 Infection** | Antiviral (CMV and others); antimicrobial |
| **P17 Radiation and photo/sonodynamic sensitisation** | Tumour oxygenation and radiosensitisation; photo- or sonosensitiser (5-ALA); targeted radioligand delivery |
| **unclear** | — |

A level-2 pathway may be added during coding only if no existing one fits. It is logged with its first drug and
confirmed by XL with the table; no level-1 process is added.

## 6. Consistency with D40

`process_primary` is expected to agree with the confirmed D40 mechanism class:
- targeted_signalling ↔ P1–P5 or P7;
- cytotoxic ↔ P6;
- immunomodulatory ↔ P9–P10;
- metabolic ↔ P12;
- epigenetic ↔ P8;
- anti_angiogenic ↔ P11;
- other ↔ P13–P17, or P7, P10 or P12 when a GBM rationale is sourced.

Disagreements are flagged `d40_consistent = no` and explained in `note`. **D40 is not changed.** The pathway layer
refines it and never overrides it.

## 7. Linking selection to the drug

For each drug–trial pair:
- **`drug_matched_selection = yes`** only if an XL-confirmed pair (D33) meets all four conditions:
  - its role is `eligibility` or `enrichment` (manual §5);
  - its `matched_candidate` names this drug;
  - it governs entry to the whole trial, or to a GBM cohort or arm in which this drug is given (A1, A2);
  - it is not a biomarker that only defines GBM (A4/A5).

  Stratification, pharmacodynamic and exploratory biomarkers never count.
- **`selection_for_co_candidate = yes`** when the trial has a qualifying pair matched to a **different** candidate in the
  same regimen but none matched to this drug. Such pairs are counted as not matched for this drug and reported
  separately.
- Imaging-assessed selection (R2) counts and is flagged.
- **Not coded** unless XL decides otherwise: a looser "pathway-concordant" match, where the biomarker is in the drug's
  pathway but D33 did not match it to the drug (e.g. NF1 loss for a MEK inhibitor). It would need new judgement.

## 8. Planned summaries (computed only after the table is confirmed)

For each level-1 process and level-2 pathway, separately for 2a, 2b and both:
- unique drugs;
- distinct trials: a trial counts once per pathway, however many of its drugs map there;
- trials with drug-matched selection on that pathway, and the share of the pathway's trials that this represents;
- co-candidate-only selection.

Counts are shown for the primary pathway and for primary plus secondary.

Sensitivity checks:
- regimen-once: multi-drug panel and tailored-therapy trials count once, not once per drug;
- excluding `unclear` and low-confidence rows.

Shared drugs across trials are described; there are no P values or confidence intervals for pathway cells. Agents that
the record does not identify and unspecified panels stay excluded (D36).

**Outputs:**
- **New supplementary table:** drug → target → pathway (primary; secondary) → source → NCT IDs → drug-matched selection
  per trial.
- **Candidate main-text figure:** level-1 processes as rows, 2a and 2b panels, unique drugs and distinct trials side by
  side, with matched-selection trials shaded. Whether it goes in the main text or the supplement is decided by XL after
  seeing it, and that decision is logged.

## 9. Process

1. Claude drafts every drug row with its source. Published rationales come from a logged PubMed search per drug
   (query, date, PMIDs returned, PMID chosen).
2. An independent AI cross-check (another model, fresh context, given only these rules and the drug list) codes
   `pathway_primary` blind. Disagreements are shown to XL, as for D34/D35.
3. XL reviews and confirms every row. The table is then frozen (SHA-256 recorded in the log).
4. Only then does `scripts/22_pathway_analysis.py` compute the §8 summaries. Results go into manuscript v7, built from v6
   with tracked changes (XL.C).

## References for the vocabulary

- Cummings JL et al. Alzheimer's disease drug development pipeline: 2025. *Alzheimers Dement (N Y)* 2025;11:e70098.
  doi:10.1002/trc2.70098 (CADRO process classification).
- Brennan CW et al. The somatic genomic landscape of glioblastoma. *Cell* 2013;155:462–77. doi:10.1016/j.cell.2013.09.034
  (GBM core pathways).
