"""
Step 12 - Build the D21 correction-review sheet for every positive candidate-matched selection (post-registration
processing step; reads only).

D21: XL personally reviews every positive candidate-matched selection decision before analysis, blind to drug
origin. The sheet therefore shows the biomarker requirement, its quote, the matched candidate and the candidate's
mechanism, but no approval or origin information.

Input:  <run>/adjudicated_trials_D32.csv (trials passing S5-S6 with candidate_matched_selection true),
        coderA/, coderB/, latest proposal (proposals_v3 > proposals_v2 > proposals), data/coder_input/
Output: <run>/d21_match_review_D32_v2.xlsx (v1 output d21_match_review_D32.xlsx kept) with sheets Read_me, Trials (one row per trial) and Matches (one row per
        matched biomarker-candidate pair). XL fills XL_confirm (yes / no / unsure) and XL_note.
Refuses to overwrite an existing sheet.

Usage: python3 scripts/12_build_d21_match_review.py outputs/main
"""
import csv
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]


def latest(run, n):
    for folder in ("proposals_v3", "proposals_v2", "proposals"):
        p = run / folder / f"{n}.json"
        if p.exists():
            return json.loads(p.read_text())
    return None


def title(n):
    lines = (ROOT / "data" / "coder_input" / f"{n}.txt").read_text().splitlines()
    return lines[2].strip() if len(lines) > 2 else ""


def sel_rows(d):
    return [b for b in d["biomarkers"] if b["role"] in ("eligibility", "enrichment") and b["candidate_matched"]]


def key(b):
    return (b["biomarker"], (b.get("matched_agent") or "").lower())


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
    dst = run / "d21_match_review_D32_v2.xlsx"
    if dst.exists():
        sys.exit(f"{dst} exists; refusing to overwrite")
    adj = [r for r in csv.DictReader(open(run / "adjudicated_trials_D32.csv"))
           if r["passes_S4_S6_llm"] == "True" and r["candidate_matched_selection"] in ("True", "true")]
    trials, matches = [], []
    for r in adj:
        n = r["nct_id"]
        a = json.loads((run / "coderA" / f"{n}.json").read_text())
        b = json.loads((run / "coderB" / f"{n}.json").read_text())
        prop = latest(run, n)
        mech = {}
        for d in (a, b):
            for ag in d["agents"]:
                m = ag.get("stated_antitumour_mechanism") or ag.get("drug_class_hint") or ""
                mech.setdefault(ag["active_moiety"].lower(), m)
        final = json.loads(r["matched_biomarkers"] or "[]")
        # v2 (2026-11-04): keep every coder row (v1 kept one row per biomarker category and agent, so two
        # requirements of the same category in one trial showed the same quote), and use each row once
        coder_rows = {"A": sel_rows(a), "B": sel_rows(b)}
        used = set()
        reasons = {}
        if prop:
            for it in prop["items"]:
                if "biomarker" in str(it.get("item")).lower() or "selection" in str(it.get("item")).lower():
                    reasons.setdefault("all", []).append(f"{it.get('item')}: {it.get('reason')}")
        for mb in final:
            bm, ag = mb.get("biomarker"), (mb.get("matched_agent") or "")
            # proposals write 'other' biomarkers as "other: <text>" or "other (<text>)"; coders use biomarker
            # 'other' with the text in biomarker_other
            bm_key = "other" if str(bm).lower().startswith("other") else bm
            agents = {x.strip() for x in ag.lower().replace(",", ";").split(";") if x.strip()}
            label = set(re.findall(r"[a-z0-9]+", str(bm).lower())) - {"other"}
            hit = {}
            for who, rows_ in coder_rows.items():
                def score(cr):
                    cr_agents = {x.strip() for x in (cr.get("matched_agent") or "").lower().replace(",", ";").split(";")}
                    words = set(re.findall(r"[a-z0-9]+", (cr.get("biomarker_other") or "").lower()))
                    return ((who, id(cr)) not in used, bool(cr_agents & agents), len(words & label))
                cands = [cr for cr in rows_ if cr["biomarker"] == bm_key]
                if cands:
                    best = max(cands, key=score)
                    if score(best)[1] or not agents:
                        hit[who] = best
                        used.add((who, id(best)))
            row = hit.get("A") or hit.get("B")
            quote = row["source_quote"]["quote"] if row else "(no coder row; set at adjudication, see proposal reason)"
            other = (row.get("biomarker_other") or "") if row else ""
            matches.append([n, bm + (f" ({other})" if other else ""), ag, mech.get(ag.lower(), ""),
                            row["role"] if row else "", "; ".join(row.get("arms") or []) if row else "",
                            quote, "A+B" if len(hit) == 2 else ("A only" if "A" in hit else ("B only" if hit else "neither")),
                            "", ""])
        trials.append([n, title(n), r["gbm_population"], r["treatment_setting"],
                       "; ".join(c.get("active_moiety", "") for c in json.loads(r["candidates"] or "[]")),
                       "; ".join(f"{m.get('biomarker')} -> {m.get('matched_agent')}" for m in final),
                       r["imaging_assessed_selection"], r["source"],
                       (prop or {}).get("note", "") if prop else "coders agreed; not queued",
                       "\n".join(reasons.get("all", []))[:3000], "", ""])

    # v2: carry XL's D21 decisions (d21_match_decisions_XL.csv, keyed by the v1 Excel row) when present
    dec_path = run / "d21_match_decisions_XL.csv"
    if dec_path.exists():
        dec = {}
        for d in csv.DictReader(open(dec_path)):
            dec.setdefault(int(d["source_excel_row"]), []).append(d)
        for i, m in enumerate(matches, start=2):
            ds = dec.get(i, [])
            if ds and all(d["nct_id"] == m[0] for d in ds):
                m[8] = ds[0]["XL_decision"] if len(ds) == 1 else "; ".join(f"{d['biomarker']}: {d['XL_decision']}" for d in ds)
                m[9] = " | ".join(d["basis"] for d in ds) + f" (XL {ds[0]['review_date']})"
            elif ds:
                sys.exit(f"decision row {i} is for {ds[0]['nct_id']}, sheet row is {m[0]}: row order changed")
    wb = Workbook()
    ws = wb.active
    ws.title = "Read_me"
    for line in [
        "D21 correction review - positive candidate-matched selection (primary outcome)",
        "",
        f"{len(trials)} trials pass the LLM-coded steps S5-S6 with candidate_matched_selection = true "
        f"(adjudicated_trials_D32.csv), {len(matches)} matched biomarker-candidate pairs.",
        "Question for each trial: does entry (whole trial, or a GBM-eligible cohort or arm) require a tumour biomarker "
        "that is mechanistically linked to a candidate drug (manual section 5, D31-A6 corrected)?",
        "Blinded to drug origin: no approval or regulatory information is shown (D21).",
        "Matches sheet: one row per pair, with the requirement's role, arms and verbatim quote, and the candidate's "
        "mechanism as the coders recorded it. 'coder_support' says which coder coded the pair.",
        "Fill XL_confirm with yes / no / unsure on each Matches row; a trial stays positive if any pair is confirmed. "
        "Imaging-assessed selection (D30-R2) is marked in the Trials sheet and excluded in sensitivity analysis 15.",
        "Rules: coding manual v1.4 section 5; D30-R2, R6; D31-A1-A8; D32-3.",
    ]:
        ws.append([line])
    ws.column_dimensions["A"].width = 140
    for row in ws.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A1"].font = Font(bold=True)
    write_sheet(wb.create_sheet("Trials"),
                ["nct_id", "title", "gbm_population", "treatment_setting", "candidates", "matched_pairs",
                 "imaging_assessed", "source", "proposal_note", "proposal_biomarker_reasons", "XL_confirm", "XL_note"],
                trials, [13, 40, 18, 14, 24, 34, 9, 18, 60, 60, 10, 30])
    write_sheet(wb.create_sheet("Matches"),
                ["nct_id", "biomarker", "matched_candidate", "candidate_mechanism", "role", "arms", "quote",
                 "coder_support", "XL_confirm", "XL_note"],
                matches, [13, 26, 20, 30, 11, 24, 70, 10, 10, 30])
    wb.save(dst)
    sup = {}
    for m in matches:
        sup[m[7]] = sup.get(m[7], 0) + 1
    print(f"trials {len(trials)}, pairs {len(matches)}, coder support {sup}, "
          f"imaging-assessed {sum(t[6] in ('True', 'true') for t in trials)}")


if __name__ == "__main__":
    main(sys.argv[1])
