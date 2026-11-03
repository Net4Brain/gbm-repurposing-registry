"""
Step 10 - Build the adjudication review sheet from the AI-drafted proposals (post-registration processing
step; reads only, changes no coded value or proposal).

Inputs (in <run>):  proposals/<NCT>.json, coderA/, coderB/, adjudication_queue_prioritised.csv
Output: <run>/adjudication_review_sheet.xlsx with sheets
  Read_me   how to use the sheet
  Trials    one row per proposed trial; flagged trials first, then grouped by the D30 ruling applied
  Items     one row per priority-1/2 queue item with both coder values, the proposal and its reason
XL fills the XL_decision / XL_value / XL_note columns. Refuses to overwrite an existing sheet.

Ruling labels: proposal batches 1-16 wrote D30 rulings as bare "R1".."R8"; later batches wrote "D30-R1".."R8"
and "manual R1".."R9" for the manual's wording fixes. Column ruling_norm rewrites bare R# as D30-R#;
the original label is kept in ruling_applied.

Usage: python3 scripts/10_build_review_sheet.py outputs/main
"""
import csv
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

INCLUDED_POP = ("gbm_only", "mixed_glioma_gbm_named", "basket_gbm_eligible")
BARE_R = re.compile(r"(?<![\w-])(?<!manual )R([1-9])\b")


def coder_vals(d):
    sel = [b for b in d["biomarkers"] if b["role"] in ("eligibility", "enrichment")]
    return {"inc": d["screening"]["gbm_population"] in INCLUDED_POP and d["screening"]["has_eligible_candidate"],
            "prim": any(b["candidate_matched"] for b in sel),
            "pop": d["screening"]["gbm_population"],
            "cands": sorted({a["active_moiety"].lower() for a in d["agents"] if a["role"].startswith("experimental_")})}


def norm_ruling(s):
    return BARE_R.sub(r"D30-R\1", s or "")


def change(a, b, p):
    if a == b == p:
        return ""
    if a == b:
        return f"both {yn(a)} -> {yn(p)}"
    return f"split -> {yn(p)}"


def yn(x):
    return "yes" if x else "no"


def write_sheet(ws, header, rows, widths):
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions


def main(run_dir):
    run = Path(run_dir)
    dst = run / "adjudication_review_sheet.xlsx"
    if dst.exists():
        sys.exit(f"{dst} exists; refusing to overwrite")
    prio = {}
    for r in csv.DictReader(open(run / "adjudication_queue_prioritised.csv")):
        if r["priority"] in ("1", "2"):
            prio.setdefault(r["nct_id"], set()).add(r["priority"])

    trials, items = [], []
    for p in sorted((run / "proposals").glob("NCT*.json")):
        d = json.loads(p.read_text())
        n = d["nct_id"]
        a = coder_vals(json.loads((run / "coderA" / f"{n}.json").read_text()))
        b = coder_vals(json.loads((run / "coderB" / f"{n}.json").read_text()))
        f = d["proposed_final"]
        p_inc = f.get("gbm_population") in INCLUDED_POP and bool(f.get("has_eligible_candidate"))
        p_prim = bool(f.get("candidate_matched_selection"))
        rulings = sorted({m for i in d["items"] for m in re.findall(r"D30-R[1-8]", norm_ruling(i.get("ruling_applied")))})
        low = sum(i.get("confidence") == "low" for i in d["items"])
        flagged = bool(d.get("needs_xl_attention"))
        inc_ch = change(a["inc"], b["inc"], p_inc)
        prim_ch = change(a["prim"], b["prim"], p_prim) if (a["inc"] or b["inc"] or p_inc) else ""
        section = "1 flagged" if flagged else (f"2 {rulings[0]}" if rulings else "3 manual only")
        trials.append([section, n, yn(flagged), "1" if "1" in prio.get(n, ()) else "2",
                       yn(a["inc"]), yn(b["inc"]), yn(p_inc), inc_ch,
                       yn(a["prim"]), yn(b["prim"]), yn(p_prim), prim_ch, yn(bool(f.get("imaging_assessed_selection"))),
                       "; ".join(rulings), len(d["items"]), low,
                       f.get("gbm_population"), "; ".join(c.get("active_moiety", "") for c in f.get("candidates") or []),
                       f.get("candidate_exclusion_reason") or "", d.get("note", ""), "", "", ""])
        for i in d["items"]:
            items.append([section, n, i.get("type"), i.get("item"), str(i.get("coder_A")), str(i.get("coder_B")),
                          str(i.get("proposed")), i.get("confidence"), norm_ruling(i.get("ruling_applied")),
                          i.get("ruling_applied"), i.get("reason"), "", "", ""])

    # order: flagged; then trials that change inclusion or the primary outcome; then by ruling; then the rest
    key = lambda r: (r[0], r[7] == "" and r[11] == "", r[1])
    trials.sort(key=key)
    order = {r[1]: k for k, r in enumerate(trials)}
    items.sort(key=lambda r: (order[r[1]], r[2], r[3]))

    wb = Workbook()
    ws = wb.active
    ws.title = "Read_me"
    for line in [
        "Adjudication review sheet - AI-drafted proposals for XL (main pass, manual v1.4, rulings D30 R1-R8)",
        "",
        f"{len(trials)} trials (all with a priority-1 or -2 queue item), {len(items)} items.",
        "Proposals were drafted by Claude Opus 5.5 subagents from the registry record, manual v1.4 and rulings D30. "
        "They are proposals only: no coder output was changed.",
        "",
        "Trials sheet: one row per trial. Sections: '1 flagged' = needs_xl_attention (a low-confidence item, or no rule "
        "settles it); '2 D30-Rx' = settled mainly by that ruling; '3 manual only' = settled by the manual. Within a "
        "section, trials whose proposal changes inclusion or the primary outcome come first.",
        "  inclusion_change / primary_change: 'both no -> yes' means both coders agreed and the proposal reverses them; "
        "'split -> yes' means the coders disagreed and the proposal picks yes. Primary outcome = candidate-matched "
        "molecular selection; shown only for trials that a coder or the proposal includes.",
        "  'includes' here means passing the LLM-coded steps S4-S6 (population and candidate). Structured steps "
        "(study type, dates, phase, age) are applied later by code.",
        "Items sheet: one row per queue item with both coder values, the proposed value, confidence, the rule cited and "
        "the reason.",
        "",
        "How to review: fill XL_decision with accept / change / defer. For 'change' put the value in XL_value. "
        "A trial-level 'accept' accepts all its items unless an item row says otherwise.",
        "Ruling labels: ruling_norm rewrites bare R1-R8 (batches 1-16) as D30-R1..R8; 'manual R#' = manual v1.2 "
        "wording fixes. The original label is kept in ruling_applied.",
        "Open convention questions are listed separately in adjudication_convention_questions.md.",
    ]:
        ws.append([line])
    ws.column_dimensions["A"].width = 140
    for row in ws.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A1"].font = Font(bold=True)

    write_sheet(wb.create_sheet("Trials"),
                ["section", "nct_id", "flagged", "top_priority", "A_includes", "B_includes", "proposed_includes",
                 "inclusion_change", "A_primary", "B_primary", "proposed_primary", "primary_change",
                 "imaging_assessed", "D30_rulings", "n_items", "n_low_conf", "proposed_gbm_population",
                 "proposed_candidates", "proposed_exclusion_reason", "note", "XL_decision", "XL_value", "XL_note"],
                trials, [12, 13, 8, 8, 8, 8, 9, 15, 8, 8, 9, 15, 9, 14, 7, 7, 18, 24, 20, 70, 12, 16, 30])
    write_sheet(wb.create_sheet("Items"),
                ["section", "nct_id", "type", "item", "coder_A", "coder_B", "proposed", "confidence", "ruling_norm",
                 "ruling_applied", "reason", "XL_decision", "XL_value", "XL_note"],
                items, [12, 13, 14, 30, 20, 20, 22, 10, 16, 16, 70, 12, 16, 30])
    wb.save(dst)

    n_inc = sum(r[7] != "" for r in trials)
    n_prim = sum(r[11] != "" for r in trials)
    print(f"trials {len(trials)}, items {len(items)}, flagged {sum(r[2] == 'yes' for r in trials)}")
    print(f"inclusion changed vs a coder: {n_inc}; primary outcome changed vs a coder: {n_prim}")
    for lab in ("inclusion_change", "primary_change"):
        col = 7 if lab == "inclusion_change" else 11
        cnt = {}
        for r in trials:
            if r[col]:
                cnt[r[col]] = cnt.get(r[col], 0) + 1
        print(lab, cnt)


if __name__ == "__main__":
    main(sys.argv[1])
