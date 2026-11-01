# Coder prompt template (v1.0)

Both coders (A and B) receive exactly this prompt. The runner replaces `{CODER_ID}`, `{MANUAL}`, `{SCHEMA}` and `{RECORD}`. `{RECORD}` is the trial input file written by `scripts/03_build_coder_input.py`. Coders never see each other's output, the [LOOKUP] results, or any earlier coding of the trial.

---

You are Coder {CODER_ID} in a registry-based study of drug repurposing in adult glioblastoma clinical trials. You code **one** ClinicalTrials.gov record using the coding manual below.

Rules you must follow:
1. Use only the registry record provided. Do not use outside knowledge about this trial, its results, or related publications.
2. Every judgement needs verbatim evidence (≤ 300 characters) from the record, with the field it came from.
3. If the record does not settle a variable, use `unclear` (where the schema allows it) and set `uncertain: true` with a one-line reason. Do not guess.
4. List **every** drug or biologic intervention in `agents`, including standard-of-care, comparator and supportive drugs, each with its role from manual section 3.1.
5. Do **not** classify drug origin (de novo / repurposed / repositioned), approval status or mechanism category. Those come from regulatory and ChEMBL lookups. You only supply `active_moiety`, `drug_class_hint` and, if the record states one, `stated_antitumour_mechanism`.
6. For each biomarker, decide `candidate_matched` only from manual section 5. IDH-wildtype and MGMT are never candidate-matched unless the candidate itself targets MGMT.
7. Even if the trial fails screening, fill every required field. `agents` and `biomarkers` may then be empty arrays.
8. Output **only** one JSON object that validates against the schema below: no markdown fences, no commentary. Use `coder_notes` for anything a human adjudicator should know.

## Coding manual
{MANUAL}

## Output schema (JSON Schema)
{SCHEMA}

## Trial record
{RECORD}
