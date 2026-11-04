"""
Step 22b - Pathway review sheet for XL (D42). Post-registration processing step; reads only.

Inputs : outputs/main/pathway_draft_D42.csv (Claude's draft, rules prompts/pathway_coding_rules_D42.md),
         outputs/main/pathway_crosscheck_D42.csv (blind second-model coding), outputs/main/pathway_pairs_D42.csv,
         outputs/main/pathway_evidence_D42.csv
Rows are sorted by review tier:
  1 different level-1 process from the cross-check, inconsistent with D40, `unclear`, or low confidence
  2 same process, different level-2 pathway
  3 agreement
Output : outputs/main/pathway_review_D42.xlsx (refuses to overwrite): Read_me, Drugs, Pairs
Usage  : python3 scripts/22b_pathway_review_sheet.py
"""
import csv
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
OUT = RUN / "pathway_review_D42.xlsx"
FILL = {1: "F8CBAD", 2: "FFE699", 3: "E2EFDA"}


def proc(p):
    return (p or "unclear").split()[0]


def sheet(ws, header, rows, widths):
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in rows:
        ws.append([r.get(h, "") for h in header])
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "C2"


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite")
    draft = list(csv.DictReader(open(RUN / "pathway_draft_D42.csv")))
    cross = {r["active_moiety"]: r for r in csv.DictReader(open(RUN / "pathway_crosscheck_D42.csv"))}
    ev = {r["active_moiety"]: r for r in csv.DictReader(open(RUN / "pathway_evidence_D42.csv"))}
    assert {r["active_moiety"] for r in draft} == set(cross) == set(ev), "drug lists differ"
    pairs = list(csv.DictReader(open(RUN / "pathway_pairs_D42.csv")))
    rows = []
    for d in draft:
        x = cross[d["active_moiety"]]
        same_proc = proc(d["process_primary"]) == proc(x["process_primary"])
        same_l2 = d["pathway_primary"].split(" [")[0].lower() == x["pathway_primary"].split(" [")[0].lower()
        tier = 1 if (not same_proc or d["d40_consistent"] == "no" or d["pathway_primary"] == "unclear"
                     or d["confidence"] == "low") else (2 if not same_l2 else 3)
        own = [p for p in pairs if p["active_moiety"] == d["active_moiety"]]
        rows.append({"tier": tier, **d, "crosscheck_pathway": x["pathway_primary"], "crosscheck_process": x["process_primary"],
                     "crosscheck_secondary": x["pathway_secondary"], "crosscheck_source": x["source_type"],
                     "crosscheck_pmids": x["pmids"], "crosscheck_reason": x["reason"],
                     "drug_matched_trials": "; ".join(p["nct_id"] + " (" + p["matched_biomarkers"] + ")" for p in own
                                                      if p["drug_matched_selection"] == "yes"),
                     "registry_stated": ev[d["active_moiety"]]["registry_stated_mechanisms"][:600],
                     "trials": ev[d["active_moiety"]]["trials"],
                     "XL_decision": "", "XL_pathway_primary": "", "XL_pathway_secondary": "", "XL_note": ""})
    rows.sort(key=lambda r: (r["tier"], r["subcategory"], r["active_moiety"]))
    wb = Workbook()
    ws = wb.active
    ws.title = "Read_me"
    for line in [
        "Pathway coding review (D42) - exploratory secondary analysis of the 92 repurposed candidates",
        "Rules: prompts/pathway_coding_rules_D42.md. Vocabulary: rules section 5 (one added level-2 pathway: "
        "'JAK–STAT (tumour-intrinsic)' under P2, used for ruxolitinib, tofacitinib and atovaquone).",
        "Drugs sheet: Claude's draft (columns target ... note) next to a blind coding by a second model (crosscheck_*).",
        "Tier 1 (red): different level-1 process, inconsistent with D40, unclear, or low confidence. "
        "Tier 2 (yellow): same process, different level-2 pathway. Tier 3 (green): agreement.",
        "Please fill XL_decision for every row: accept_draft, accept_crosscheck or change. For 'change', give "
        "XL_pathway_primary (and secondary if needed) using the level-2 names of section 5.",
        "drug_matched_trials comes from your D33 decisions and is not recoded here (rules section 7).",
        "Pairs sheet: one row per drug-trial pair, for reference. Trial-level override proposed: sulfasalazine in "
        "NCT05664464 (glutamate-secretion blockade).",
        "No pathway count is produced until you confirm every row; the confirmed table is then frozen with its checksum."]:
        ws.append([line])
    ws.column_dimensions["A"].width = 150
    ws["A1"].font = Font(bold=True)
    hdr = ["tier", "active_moiety", "subcategory", "d40_mechanism", "n_trials", "target", "proposed_gbm_mechanism",
           "pathway_primary", "process_primary", "pathway_secondary", "source_type", "source", "confidence",
           "differs_from_approved_use", "d40_consistent", "note", "crosscheck_pathway", "crosscheck_process",
           "crosscheck_secondary", "crosscheck_source", "crosscheck_pmids", "crosscheck_reason", "drug_matched_trials",
           "registry_stated", "trials", "XL_decision", "XL_pathway_primary", "XL_pathway_secondary", "XL_note"]
    sheet(wb.create_sheet("Drugs"), hdr, rows,
               [5, 22, 6, 14, 6, 18, 34, 24, 22, 22, 14, 40, 9, 9, 9, 34, 24, 22, 22, 14, 14, 34, 30, 50, 30, 16, 24, 24, 30])
    ws2 = wb["Drugs"]
    for i, r in enumerate(rows, 2):
        ws2.cell(i, 1).fill = PatternFill("solid", fgColor=FILL[r["tier"]])
    dv = DataValidation(type="list", formula1='"accept_draft,accept_crosscheck,change"', allow_blank=True)
    ws2.add_data_validation(dv)
    dv.add(f"Z2:Z{len(rows) + 1}")
    sheet(wb.create_sheet("Pairs"), list(pairs[0].keys()), pairs, [22, 6, 14, 22, 10, 40, 10, 50, 8])
    wb.save(OUT)
    tiers = {t: sum(r["tier"] == t for r in rows) for t in (1, 2, 3)}
    print(f"wrote {OUT.name}: {len(rows)} drugs, tiers {tiers}")


if __name__ == "__main__":
    main()
