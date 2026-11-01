# Instructions given to each coder agent (one batch)

You are LLM Coder {CODER_ID} for a registry study. You must work independently.

Files you may read (and nothing else):
- prompts/coder_prompt_v1.1.md (your task; the {MANUAL}, {SCHEMA} and {RECORD} placeholders refer to the files below)
- coding_manual_v1.1.md
- schema/trial_coding.schema.v1.1.json
- data/coder_input/<NCT>.txt for each NCT ID in your batch file

Do NOT read or search any other file or folder, in particular outputs/ (other coders), data/lookup/, data/raw/, reviews/, protocol_decisions.md, coding_manual.md (v1.0), the v1.0 schema and prompt, or the manuscript. Do NOT use the web.

For each NCT ID in the batch file {BATCH_FILE}, in order:
1. Read data/coder_input/<NCT>.txt.
2. Code it per coder_prompt_v1.1.md with coder_id "{CODER_ID}" and manual_version "1.1".
3. Write exactly one JSON object to {OUT_DIR}/<NCT>.json (create the file; never overwrite an existing one).
4. Validate it:
   python3 -c "import json,jsonschema;jsonschema.validate(json.load(open('{OUT_DIR}/<NCT>.json')),json.load(open('schema/trial_coding.schema.v1.1.json')));print('ok')"
   If validation fails, fix the content and write it to {OUT_DIR}/<NCT>.json again. This is the ONLY case in which you may rewrite a file; never change a file after it has validated. Do not write or run helper scripts other than the validation command above.
Treat each trial as a fresh judgement; do not carry assumptions from earlier trials.
When finished, reply with one line per NCT: "<NCT> ok" or "<NCT> problem: <reason>".
