# Instructions for the final harmonisation of adjudication proposals (one batch)

You make revised proposals consistent with conventions D31 as **corrected and clarified** on 2026-11-03. You never change coder outputs or earlier proposals.

Files you may read (and nothing else):
- outputs/main/adjudication_rulings_D31.md. Read all of it, especially the corrected A6 and the section "Clarifications from applying D31".
- outputs/main/adjudication_rulings_D30.md and coding_manual_v1.4.md (for reference)
- your trial list: {BATCH_FILE}
- for each NCT in your batch:
  - outputs/main/proposals_v2/<NCT>.json (the current proposal; it has a `revisions` list)
  - data/coder_input/<NCT>.txt (the registry record)
  - outputs/main/coderA/<NCT>.json and outputs/main/coderB/<NCT>.json, if needed

Do NOT read other files or protocol_decisions.md. You may use your own knowledge of a drug's established pharmacology for A6, and must say so in the reason. Do NOT use the web. Do NOT modify or delete any existing file, and do not create helper script files.

For EVERY NCT in the batch, write `outputs/main/proposals_v3/<NCT>.json` (new file; never overwrite). Start from the v2 file, keep its `revisions` list, and append a `harmonisation` list:
```
"harmonisation": [ {"check": "A6|A2|B7|C1|C2|flag", "field": "...", "from": "...", "to": "...", "reason": "<one sentence>"} ]
```
Check each trial for the following:
1. **A6, corrected.** A biomarker is candidate-matched when it is mechanistically linked to a candidate, either as stated in the record or from the candidate's established pharmacology.
   - Undo any change made under the old wording ("record must state the link"), and resolve every "A6 pending XL" note.
   - If the mechanism of a code-named agent is genuinely unknown to you, keep the row's current value, set `needs_xl_attention` true, and write "A6 evidence check: mechanism of <agent> unknown" in the note.
   - The row's `candidate_matched` flag should reflect the mechanistic link even when the row's role is `exploratory_correlative` (for example after A1). That flag has no effect on the outcomes.
2. **A2, clarified.** A2 applies only to an "or" inside an entry criterion. A requirement for a whole GBM cohort or arm stays `enrichment`. When every route requires a marker of the same pathway, the requirement stands.
3. **B7, clarified.** Temozolomide, carmustine, lomustine and bevacizumab are never candidates under B7. Restore them to `soc_backbone` or `established_therapy_experiment` (manual rule 6, D30-R1). Then re-derive the roles of the other agents (monotherapy vs combination) and `has_eligible_candidate`.
4. **C1, clarified.** Use `excluded_intervention_type` whenever a non-drug intervention is under test, including diagnostic, surgical, behavioural, device or radiotherapy. Use `no_pharmacological_candidate` only when every intervention is a drug that is not a candidate (supportive, diagnostic agent or backbone only).
5. **C2, clarified.** `combination_partners` lists drugs and radiotherapy given with the candidate in the GBM arms. It does not list devices (TTFields), excluded products or their components (vaccines, cell products, conditioning chemotherapy, D30-R4/D31-B8 adjuvants), or drugs given only in non-GBM arms.
6. **Consistency.** `proposed_final` must agree with the items:
   - `candidate_matched_selection` = any eligibility or enrichment row with candidate_matched true;
   - `any_molecular_selection` = any eligibility or enrichment row, except those exempt under A5 and IDH-wildtype.
   - Set `needs_xl_attention` true if any item is still low confidence with no ruling to settle it, if an A6 evidence check or D31 §D check is pending, or if a primary-outcome value rests on a judgement call. Say why in the note.

Use "D31-xx" for convention citations in `ruling_applied`. Validate each file with python3 -c "import json;json.load(open('outputs/main/proposals_v3/<NCT>.json'));print('ok')".

When finished, reply with one line per NCT: "<NCT> ok changes=<n> (needs_xl_attention=true/false)". Then list every change to gbm_population, has_eligible_candidate, candidate_matched_selection, the candidate set, or an agent's role.
