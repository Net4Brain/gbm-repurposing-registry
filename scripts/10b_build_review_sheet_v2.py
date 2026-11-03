"""
Step 10b - Build review sheet v2 from the latest proposal of each trial (post-registration processing step;
reads only, changes no coded value or proposal).

Latest proposal = proposals_v3/<NCT>.json (final harmonisation, D31 corrected) if present, else
proposals_v2/<NCT>.json (D31 revision), else proposals/<NCT>.json (first draft).
Compared against both coders and against the first-draft proposal.

Output: <run>/adjudication_review_sheet_v2.xlsx with sheets
  Read_me    how to use the sheet
  Trials     one row per trial: flagged first, then trials whose proposal changes inclusion or the primary
             outcome against a coder, then the rest
  Items      one row per item of the latest proposal
  Changes    every D31 revision and harmonisation change, with its reason
  Pending    evidence checks (D31 section D, A6 mechanism checks) and near-misses (D31-B5)
Refuses to overwrite an existing sheet.

Usage: python3 scripts/10b_build_review_sheet_v2.py outputs/main
"""
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

INCLUDED_POP = ("gbm_only", "mixed_glioma_gbm_named", "basket_gbm_eligible")
BARE_R = re.compile(r"(?<![\w-])(?<!manual )R([1-9])\b")


def yn(x):
    return "yes" if x else "no"


def coder_vals(d):
    sel = [b for b in d["biomarkers"] if b["role"] in ("eligibility", "enrichment")]
    return {"inc": d["screening"]["gbm_population"] in INCLUDED_POP and d["screening"]["has_eligible_candidate"],
            "prim": any(b["candidate_matched"] for b in sel)}


def prop_vals(d):
    f = d["proposed_final"]
    return {"inc": f.get("gbm_population") in INCLUDED_POP and bool(f.get("has_eligible_candidate")),
            "prim": bool(f.get("candidate_matched_selection"))}


def change(a, b, p):
    if a == b == p:
        return ""
    if a == b:
        return f"both {yn(a)} -> {yn(p)}"
    return f"split -> {yn(p)}"


def write_sheet(ws, header, rows, widths):
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
    for r in rows:
        ws.append([json.dumps(v) if isinstance(v, (list, dict)) else v for v in r])
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions


def main(run_dir):
    run = Path(run_dir)
    dst = run / "adjudication_review_sheet_v2.xlsx"
    if dst.exists():
        sys.exit(f"{dst} exists; refusing to overwrite")
    trials, items, changes, pending = [], [], [], []
    versions = {"v1": 0, "v2": 0, "v3": 0}
    for p1 in sorted((run / "proposals").glob("NCT*.json")):
        n = p1.stem
        v1 = json.loads(p1.read_text())
        for ver, folder in (("v3", "proposals_v3"), ("v2", "proposals_v2"), ("v1", "proposals")):
            p = run / folder / f"{n}.json"
            if p.exists():
                d = json.loads(p.read_text())
                break
        versions[ver] += 1
        a = coder_vals(json.loads((run / "coderA" / f"{n}.json").read_text()))
        b = coder_vals(json.loads((run / "coderB" / f"{n}.json").read_text()))
        pv, p0 = prop_vals(d), prop_vals(v1)
        f = d["proposed_final"]
        flagged = bool(d.get("needs_xl_attention"))
        note = d.get("note", "") or ""
        inc_ch = change(a["inc"], b["inc"], pv["inc"])
        prim_ch = change(a["prim"], b["prim"], pv["prim"]) if (a["inc"] or b["inc"] or pv["inc"]) else ""
        vs_v1 = "; ".join(s for s, k in (("inclusion", "inc"), ("primary", "prim")) if pv[k] != p0[k])
        section = "1 flagged" if flagged else ("2 changes coder result" if (inc_ch or prim_ch) else "3 other")
        trials.append([section, n, ver, yn(flagged), yn(a["inc"]), yn(b["inc"]), yn(pv["inc"]), inc_ch,
                       yn(a["prim"]), yn(b["prim"]), yn(pv["prim"]), prim_ch, vs_v1,
                       yn(bool(f.get("imaging_assessed_selection"))), yn(bool(f.get("any_molecular_selection"))),
                       f.get("gbm_population"), "; ".join(c.get("active_moiety", "") for c in f.get("candidates") or []),
                       f.get("candidate_exclusion_reason") or "", len(d.get("revisions", [])),
                       len(d.get("harmonisation", [])), note, "", "", ""])
        for i in d["items"]:
            items.append([section, n, i.get("type"), i.get("item"), str(i.get("coder_A")), str(i.get("coder_B")),
                          str(i.get("proposed")), i.get("confidence"),
                          BARE_R.sub(r"D30-R\1", i.get("ruling_applied") or ""), i.get("reason"), "", "", ""])
        for stage, key in (("D31 revision", "revisions"), ("harmonisation", "harmonisation")):
            for r in d.get(key, []):
                changes.append([n, stage, r.get("convention") or r.get("check"), r.get("field"),
                                r.get("from"), r.get("to"), r.get("reason")])
        low = note.lower()
        if "near-miss" in low:
            pending.append([n, "near-miss (D31-B5)", note])
        if "evidence check" in low or "licens" in low or "unidentified" in low or "data-quality" in low \
                or "data quality" in low:
            pending.append([n, "evidence check", note])

    key = lambda r: (r[0], r[1])
    trials.sort(key=key)
    order = {r[1]: k for k, r in enumerate(trials)}
    items.sort(key=lambda r: (order[r[1]], r[2], str(r[3])))

    wb = Workbook()
    ws = wb.active
    ws.title = "Read_me"
    n_inc = sum(r[7] != "" for r in trials)
    n_prim = sum(r[11] != "" for r in trials)
    for line in [
        "Adjudication review sheet v2 - proposals after conventions D31 (A6 corrected) and final harmonisation",
        "",
        f"{len(trials)} trials. Latest proposal used: v3 (harmonised) {versions['v3']}, v2 (D31 revision) "
        f"{versions['v2']}, v1 (first draft) {versions['v1']}.",
        f"Flagged for XL: {sum(r[3] == 'yes' for r in trials)}. Proposal changes inclusion against a coder: {n_inc}; "
        f"changes the primary outcome against a coder: {n_prim}.",
        "Sheets: Trials (one row per trial), Items (each queue item with both coders and the proposal), Changes "
        "(every D31 revision and harmonisation change with its reason), Pending (evidence checks and near-misses).",
        "Trials columns: inclusion_change / primary_change compare the proposal with the two coders ('both no -> yes' "
        "= both coders agreed and the proposal reverses them). changed_vs_first_draft shows where D31 moved the "
        "proposal away from the first draft.",
        "'includes' = passes the LLM-coded steps S4-S6; structured steps (study type, dates, phase, age) come later.",
        "How to review: fill XL_decision with accept / change / defer; for change, put the value in XL_value. A "
        "trial-level accept accepts all its items unless an item row says otherwise.",
        "Rules: coding manual v1.4, rulings D30 (adjudication_rulings_D30.md), conventions D31 "
        "(adjudication_rulings_D31.md).",
    ]:
        ws.append([line])
    ws.column_dimensions["A"].width = 140
    for row in ws.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A1"].font = Font(bold=True)

    write_sheet(wb.create_sheet("Trials"),
                ["section", "nct_id", "version", "flagged", "A_includes", "B_includes", "proposed_includes",
                 "inclusion_change", "A_primary", "B_primary", "proposed_primary", "primary_change",
                 "changed_vs_first_draft", "imaging_assessed", "any_molecular_selection", "proposed_gbm_population",
                 "proposed_candidates", "proposed_exclusion_reason", "n_D31_revisions", "n_harmonisation", "note",
                 "XL_decision", "XL_value", "XL_note"],
                trials, [14, 13, 6, 7, 8, 8, 9, 15, 8, 8, 9, 15, 14, 9, 9, 18, 24, 20, 8, 8, 70, 12, 16, 30])
    write_sheet(wb.create_sheet("Items"),
                ["section", "nct_id", "type", "item", "coder_A", "coder_B", "proposed", "confidence",
                 "ruling_applied", "reason", "XL_decision", "XL_value", "XL_note"],
                items, [14, 13, 14, 30, 20, 20, 22, 10, 18, 70, 12, 16, 30])
    write_sheet(wb.create_sheet("Changes"),
                ["nct_id", "stage", "rule", "field", "from", "to", "reason"],
                changes, [13, 13, 12, 28, 24, 24, 70])
    write_sheet(wb.create_sheet("Pending"), ["nct_id", "kind", "note"], pending, [13, 20, 110])
    wb.save(dst)

    print(f"trials {len(trials)} (v3 {versions['v3']}, v2 {versions['v2']}, v1 {versions['v1']}), items {len(items)}, "
          f"changes {len(changes)}, pending rows {len(pending)}")
    print(f"flagged {sum(r[3] == 'yes' for r in trials)}; inclusion changed vs a coder {n_inc}; "
          f"primary changed vs a coder {n_prim}")
    for col, lab in ((7, "inclusion_change"), (11, "primary_change")):
        cnt = {}
        for r in trials:
            if r[col]:
                cnt[r[col]] = cnt.get(r[col], 0) + 1
        print(lab, cnt)
    inc_p = sum(r[6] == "yes" for r in trials)
    prim_p = sum(r[6] == "yes" and r[10] == "yes" for r in trials)
    print(f"among the {len(trials)} queued trials: proposed included {inc_p}, of which primary outcome yes {prim_p}")


if __name__ == "__main__":
    main(sys.argv[1])
