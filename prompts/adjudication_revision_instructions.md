# Instructions for revising adjudication proposals to conventions D31 (one batch)

You revise AI-drafted adjudication proposals so that they follow XL's conventions D31. You never change coder outputs or the original proposals.

Files you may read (and nothing else):
- outputs/main/adjudication_rulings_D31.md (conventions A1–C6; apply them)
- outputs/main/adjudication_rulings_D30.md and coding_manual_v1.4.md (for reference)
- your trial list: {BATCH_FILE}
- for each NCT in your batch:
  - outputs/main/proposals/<NCT>.json (the original proposal)
  - data/coder_input/<NCT>.txt (the registry record), when a convention needs the record checked
  - outputs/main/coderA/<NCT>.json and outputs/main/coderB/<NCT>.json, if needed

Do NOT read other files, the web or protocol_decisions.md. Do NOT modify or delete any existing file. Do not create helper script files.

For EVERY NCT in the batch, write `outputs/main/proposals_v2/<NCT>.json` (new file; never overwrite). Use the same structure as the original proposal, plus a `revisions` list:
```
"revisions": [ {"convention": "D31-A1", "field": "<item or proposed_final field>", "from": "...", "to": "...", "reason": "<one sentence citing the record>"} ]
```
- Copy the original and change only what a D31 convention requires. Check every convention against the trial, especially:
  - A1: basket trials and cohort-specific biomarkers;
  - A4/A5: exclusion-stated biomarkers;
  - A8: MGMT;
  - B1–B4: R7 wording;
  - B7: soc_backbone roles;
  - B9: supportive roles;
  - C1: the exclusion reason;
  - C2: combination_partners;
  - C3: regimen;
  - C5/C6: PK and target engagement.
- When you change a value, update both the matching `items[].proposed` (set its `ruling_applied` to the D31 ID) and the affected `proposed_final` fields, so that `proposed_final` stays consistent with the items.
  - Example: if A1 removes the only matched selection row, set `candidate_matched_selection` false. Set `any_molecular_selection` from the remaining eligibility/enrichment rows.
- If no convention changes anything, write the copy with `"revisions": []`.
- Re-set `needs_xl_attention`: true only if an item is still low confidence and no ruling or convention settles it, or if a D31 §D evidence check is pending. Update `note` to say what still needs XL.
- In ruling_applied, use "D30-R#" for D30 rulings, "manual R#" for the manual wording fixes, "manual §x" for sections and "D31-xx" for conventions. Rewrite a bare "R#" from the original as "D30-R#".
- Validate each file: python3 -c "import json;json.load(open('outputs/main/proposals_v2/<NCT>.json'));print('ok')"

When finished, reply with one line per NCT: "<NCT> ok revisions=<n> (needs_xl_attention=true/false)". Then give a short list of every change to inclusion (gbm_population or has_eligible_candidate) or to candidate_matched_selection.
