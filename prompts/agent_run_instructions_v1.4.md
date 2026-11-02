# Instructions given to each coder agent (one batch)

You are LLM Coder {CODER_ID} for a registry study. You must work independently.

Files you may read (and nothing else):
- prompts/coder_prompt_v1.4.md (your task; the {MANUAL}, {SCHEMA} and {RECORD} placeholders refer to the files below)
- coding_manual_v1.4.md
- schema/trial_coding.schema.v1.4.json
- data/coder_input/<NCT>.txt for each NCT ID in your batch file

Do NOT read or search any other file or folder, in particular outputs/ (other coders), data/lookup/, data/raw/, reviews/, protocol_decisions.md, coding_manual.md, coding_manual_v1.1.md, coding_manual_v1.2.md, coding_manual_v1.3.md, the older schemas and prompts, or the manuscript. Do NOT use the web.

For each NCT ID in the batch file {BATCH_FILE}, in order:
1. Read data/coder_input/<NCT>.txt.
2. Code it per coder_prompt_v1.4.md with coder_id "{CODER_ID}" and manual_version "1.4".
3. Write exactly one JSON object to {OUT_DIR}/<NCT>.json (create the file; never overwrite an existing one).
4. Validate it:
   python3 -c "import json,jsonschema;jsonschema.validate(json.load(open('{OUT_DIR}/<NCT>.json')),json.load(open('schema/trial_coding.schema.v1.4.json')));print('ok')"
   If validation fails, fix the content and write it to {OUT_DIR}/<NCT>.json again. This is the ONLY case in which you may rewrite a file; never change a file after it has validated. Do not write or run helper scripts other than the validation command above.
Treat each trial as a fresh judgement; do not carry assumptions from earlier trials.
After the last record, append one line per NCT to {OUT_DIR}/run_log.tsv with tab-separated fields: coder_id, model you are running as, NCT, UTC time written, "ok" or problem. Create the file if absent; only append.
When finished, reply with one line per NCT: "<NCT> ok" or "<NCT> problem: <reason>".
