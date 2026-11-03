# Instructions for drafting adjudication proposals (one batch)

You draft **proposed** adjudication decisions for a human adjudicator (XL), who confirms or changes each one. You do not make final decisions, and you never change any coder output.

Files you may read (and nothing else):
- coding_manual_v1.4.md
- outputs/main/adjudication_rulings_D30.md (rulings R1–R8; apply them)
- outputs/main/batches are not needed; your trial list is the batch file {BATCH_FILE}
- for each NCT in your batch:
  - data/coder_input/<NCT>.txt (the registry record)
  - outputs/main/coderA/<NCT>.json and outputs/main/coderB/<NCT>.json
  - the rows for that NCT in outputs/main/adjudication_queue_prioritised.csv (read them with: grep '^[0-9],<NCT>,' outputs/main/adjudication_queue_prioritised.csv)

Do NOT read other files, the web, protocol_decisions.md or the manuscript. Do NOT modify or delete any file except your own new output files.

For each NCT, write one JSON file `outputs/main/proposals/<NCT>.json` (create it; never overwrite an existing file) with:
```
{
  "nct_id": "...",
  "items": [  // one entry per queue row with priority 1 or 2 for this NCT (skip priority 3)
    {"type": "...", "item": "...", "coder_A": "...", "coder_B": "...",
     "proposed": "<the value you propose>",
     "ruling_applied": "R1".."R8" or "manual §x" or "",
     "reason": "<one or two sentences, citing the record>",
     "confidence": "high" | "medium" | "low"}
  ],
  "proposed_final": {
    "gbm_population": "...", "cns5_terminology": "...", "basket": true/false,
    "has_eligible_candidate": true/false, "candidate_exclusion_reason": "...",
    "candidates": [{"active_moiety": "...", "role": "...", "device_dependent": true/false}],
    "treatment_setting": "...", "regimen": "...",
    "candidate_matched_selection": true/false, "imaging_assessed_selection": true/false,
    "matched_biomarkers": [{"biomarker": "...", "matched_agent": "..."}],
    "any_molecular_selection": true/false,
    "tumour_pk_planned": "...", "target_engagement_planned": "..."
  },
  "needs_xl_attention": true/false,   // true if any item is low confidence or no ruling/manual rule settles it
  "note": "<anything XL must know, or empty>"
}
```
Rules:
1. Decide from the registry record, the coding manual and rulings R1–R8. When both coders agree and the queue row is only an "uncertain" flag, say whether the agreed coding stands.
2. Prefer the reading the manual supports, not the majority. Neither coder is presumed right.
3. Quote briefly from the record in `reason` where possible.
4. Set confidence "low" whenever the record is genuinely ambiguous. Never guess silently.
5. Validate each file is valid JSON: python3 -c "import json;json.load(open('outputs/main/proposals/<NCT>.json'));print('ok')"

When finished, reply with one line per NCT: "<NCT> ok (needs_xl_attention=true/false)" or "<NCT> problem: <reason>".
