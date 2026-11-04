"""
Step 15 - Build the blinded expert validation packets (D28). Post-registration processing step.

The 100 records of data/processed/expert_validation_sample.csv (drawn 2026-11-02 before the main pass,
08b_draw_expert_sample.py) are coded independently by two experts, blind to the AI output and to each other.
The packets contain ONLY the frozen registry record text (data/coder_input/, the same input the AI coders saw),
coding manual v1.4, the rules addendum (prompts/expert_rules_addendum_D30_D36.md: rules only, no trial named) and an
empty coding workbook. No coder output, proposal, adjudication, origin or stratum information is included.
Record order is shuffled (seed 20261107), so the sampling strata are not visible.

Output folder (refuses to overwrite): outputs/expert_packets_D28/
  expert_1/ and expert_2/, each with:
    00_README.html                 instructions
    01_coding_manual_v1.4.html     the frozen manual (rendered; the .md source is included too)
    02_rules_addendum.html         adjudication rules D30-D36
    03_records.html                all 100 records, in coding order, with an index
    records/NNN_NCTxxxxxxxx.txt    one plain-text file per record
    coding_workbook_expert_N.xlsx  Instructions, Trials (100 pre-filled rows), Agents, Biomarkers, Lists
  SHA256SUMS.txt                   checksums of every packet file
Usage: python3 scripts/15_build_expert_packets.py
"""
import csv
import hashlib
import html
import json
import random
import shutil
import sys
from pathlib import Path

import markdown
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "expert_packets_D28"
SEED = 20261107
SCHEMA = json.loads((ROOT / "schema" / "trial_coding.schema.v1.4.json").read_text())["properties"]
CSS = ("<style>body{font-family:-apple-system,Segoe UI,Arial,sans-serif;max-width:60em;margin:2em auto;padding:0 1em;"
       "line-height:1.5;color:#222}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px 6px;"
       "vertical-align:top}pre{white-space:pre-wrap;background:#f6f6f6;padding:1em;border-radius:4px}"
       "h2{border-top:1px solid #ddd;padding-top:1em}</style>")

TRIAL_FIELDS = [  # (column, enum or None for free text, help)
    ("gbm_population", SCHEMA["screening"]["properties"]["gbm_population"]["enum"], "S5, manual 1.1"),
    ("cns5_terminology", SCHEMA["screening"]["properties"]["cns5_terminology"]["enum"], "manual 1.1 (C8)"),
    ("has_eligible_candidate", ["TRUE", "FALSE"], "S6, manual 1.2 and 3"),
    ("candidate_exclusion_reason", SCHEMA["screening"]["properties"]["candidate_exclusion_reason"]["enum"], "S6 reason; 'none' if a candidate"),
    ("treatment_setting", SCHEMA["trial"]["properties"]["treatment_setting"]["enum"], "manual 2"),
    ("regimen", SCHEMA["trial"]["properties"]["regimen"]["enum"], "manual 2"),
    ("combination_partners", None, "free text, separate with ;"),
    ("basket", ["TRUE", "FALSE"], "manual 2"),
    ("control_arm_from_other_arms", SCHEMA["trial"]["properties"]["control_arm_from_other_arms"]["enum"], "manual 2"),
    ("tumour_pk_planned", SCHEMA["trial"]["properties"]["tumour_pk_planned"]["enum"], "manual 2"),
    ("target_engagement_planned", SCHEMA["trial"]["properties"]["target_engagement_planned"]["enum"], "manual 2"),
    ("confidence", ["high", "medium", "low"], "your confidence in this record"),
    ("notes", None, "anything uncertain"),
]
AGENT_FIELDS = [
    ("nct_id", "NCT", "record"), ("agent_name_registered", None, "as written in the record"),
    ("active_moiety", None, "INN, lower case (manual 3, C5)"),
    ("role", SCHEMA["agents"]["items"]["properties"]["role"]["enum"], "manual 3.1"),
    ("device_dependent", ["TRUE", "FALSE"], "C12"), ("delivery_enabling", ["TRUE", "FALSE"], "C11"),
    ("notes", None, ""),
]
BIOMARKER_FIELDS = [
    ("nct_id", "NCT", "record"), ("biomarker", SCHEMA["biomarkers"]["items"]["properties"]["biomarker"]["enum"], "manual 5"),
    ("biomarker_other", None, "describe if 'other'"),
    ("role", SCHEMA["biomarkers"]["items"]["properties"]["role"]["enum"], "manual 5"),
    ("candidate_matched", ["TRUE", "FALSE"], "manual 5 and addendum"), ("matched_agent", None, "active moiety"),
    ("arms", None, "arm labels the requirement applies to; empty = whole trial"), ("notes", None, ""),
]


def page(title, body):
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>{CSS}</head><body>{body}</body></html>"


def sheet(wb, name, fields, n_rows, ncts, lists, prefill=None):
    ws = wb.create_sheet(name)
    ws.append([f[0] for f in fields])
    ws.append([f"({f[2]})" for f in fields])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
    for c in ws[2]:
        c.font = Font(italic=True, color="666666")
    for i in range(n_rows):
        ws.append([(prefill[i] if (prefill and j == 0) else None) for j in range(len(fields))])
    for j, (col, enum, _) in enumerate(fields, 1):
        letter = get_column_letter(j)
        ws.column_dimensions[letter].width = 26 if enum else 34
        if enum == "NCT":
            ref = f"Lists!$A$2:$A${len(ncts) + 1}"
        elif enum:
            if col not in lists:
                lists[col] = enum
            k = list(lists).index(col) + 2
            ref = f"Lists!${get_column_letter(k)}$2:${get_column_letter(k)}${len(enum) + 1}"
        else:
            continue
        dv = DataValidation(type="list", formula1=f"={ref}", allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{letter}3:{letter}{n_rows + 2}")
    ws.freeze_panes = "B3"
    return ws


def workbook(path, expert, ncts):
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    for line in [f"Expert coding workbook - expert {expert}", "",
                 "Code each record independently, using coding manual v1.4 and the rules addendum. Do not discuss "
                 "records with the other expert until both workbooks are returned.",
                 "Trials: one pre-filled row per record (coding order = 03_records.html). Fill every column.",
                 "Agents: one row per drug or biologic in the record (manual 3, R9: registered interventions plus "
                 "drugs every patient receives). Pick the record in nct_id.",
                 "Biomarkers: one row per tumour molecular biomarker (manual 5); leave empty if none.",
                 "Use the dropdowns; write anything uncertain in notes and set confidence.",
                 "Return the workbook to XL, renamed with your initials and the date."]:
        ws.append([line])
    ws.column_dimensions["A"].width = 120
    for row in ws.iter_rows():
        row[0].alignment = Alignment(wrap_text=True)
    lists = {}
    sheet(wb, "Trials", [("nct_id", None, "do not edit")] + TRIAL_FIELDS, len(ncts), ncts, lists, prefill=ncts)
    sheet(wb, "Agents", AGENT_FIELDS, 600, ncts, lists)
    sheet(wb, "Biomarkers", BIOMARKER_FIELDS, 400, ncts, lists)
    lw = wb.create_sheet("Lists")
    lw.cell(1, 1, "nct_id")
    for i, n in enumerate(ncts, 2):
        lw.cell(i, 1, n)
    for k, (col, enum) in enumerate(lists.items(), 2):
        lw.cell(1, k, col)
        for i, v in enumerate(enum, 2):
            lw.cell(i, k, v)
    lw.sheet_state = "hidden"
    wb.save(path)


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite")
    ncts = [r["nct_id"] for r in csv.DictReader(open(ROOT / "data" / "processed" / "expert_validation_sample.csv"))]
    assert len(ncts) == 100 and len(set(ncts)) == 100
    random.Random(SEED).shuffle(ncts)
    manual_md = (ROOT / "coding_manual_v1.4.md").read_text()
    addendum_md = (ROOT / "prompts" / "expert_rules_addendum_D30_D36.md").read_text()
    readme = f"""<h1>GBM trial coding - expert validation packet</h1>
<p>Thank you for coding these 100 ClinicalTrials.gov records. Your coding, with the other expert's, becomes the reference
standard for measuring the accuracy of the study's AI-assisted coding (protocol decision D28, OSF registration
osf.io/gn8v5).</p>
<h2>What to do</h2><ol>
<li>Read the coding manual (<a href='01_coding_manual_v1.4.html'>01</a>) and the rules addendum (<a href='02_rules_addendum.html'>02</a>).</li>
<li>Code every record in <a href='03_records.html'>03_records.html</a> (or the matching files in <code>records/</code>), in the order given, in the
coding workbook: one row per record in <b>Trials</b>, plus <b>Agents</b> and <b>Biomarkers</b> rows.</li>
<li>Code only from the record text. Do not look the trials up online, and do not discuss them with the other expert
until both workbooks are returned.</li>
<li>Steps S1-S4 (study type, start date, phase, age) are computed from structured fields and are <b>not</b> coded by you.
Code population (S5), candidate (S6), agents, biomarkers and the trial-level variables for every record, even if a
record would fail S1-S4.</li>
<li>Drug origin (approval history) is not coded by you.</li></ol>
<p>The records are the frozen snapshot of 1 November 2026. Some records are not glioblastoma trials; code them as the manual says.</p>"""
    for e in (1, 2):
        d = OUT / f"expert_{e}"
        (d / "records").mkdir(parents=True)
        (d / "00_README.html").write_text(page("Expert coding - README", readme))
        (d / "01_coding_manual_v1.4.html").write_text(page("Coding manual v1.4", markdown.markdown(manual_md, extensions=["tables"])))
        shutil.copy(ROOT / "coding_manual_v1.4.md", d / "01_coding_manual_v1.4.md")
        (d / "02_rules_addendum.html").write_text(page("Rules addendum D30-D36", markdown.markdown(addendum_md, extensions=["tables"])))
        idx, body = [], []
        for i, n in enumerate(ncts, 1):
            text = (ROOT / "data" / "coder_input" / f"{n}.txt").read_text()
            (d / "records" / f"{i:03d}_{n}.txt").write_text(text)
            idx.append(f"<li><a href='#r{i}'>{i:03d} {n}</a></li>")
            body.append(f"<h2 id='r{i}'>{i:03d} - {n}</h2><pre>{html.escape(text)}</pre>")
        (d / "03_records.html").write_text(page("Records", "<h1>Records (coding order)</h1><ol>" + "".join(idx) + "</ol>" + "".join(body)))
        workbook(d / f"coding_workbook_expert_{e}.xlsx", e, ncts)
    with open(OUT / "SHA256SUMS.txt", "w") as fh:
        for p in sorted(OUT.rglob("*")):
            if p.is_file() and p.name != "SHA256SUMS.txt":
                fh.write(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT)}\n")
    print(f"packets written to {OUT}: 2 experts x 100 records; order seed {SEED}")


if __name__ == "__main__":
    main()
