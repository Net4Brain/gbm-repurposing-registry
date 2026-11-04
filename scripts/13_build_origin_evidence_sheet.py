"""
Step 13 - Build the D21 drug-origin evidence sheet (post-registration processing step; reads only).

For every candidate agent of the trials that pass S5-S6 (adjudicated_trials_D32.csv), the sheet shows the DRAFT
dated regulatory and development events (data/reference/*_draft_D32*.csv) and the PROVISIONAL origin category that
06_derive_origin_v2.classify() would give if the draft rows were correct, at the earliest and the latest trial start
(D12: the agent-level origin uses the earliest eligible trial). Provisional categories are a guide for XL's review,
never final values: the reference tables stay unreviewed until XL signs rows off.

Rows are sorted by review tier:
  1 category in doubt - alias lookup, approval between two of the agent's trial starts, date-sensitive, tumour-agnostic
    or glioma wording, oncology vs non-oncology uncertainty, approved elsewhere but not FDA/EMA (ChEMBL phase 4)
  2 approved, one clear category for all its trials
  3 unapproved, prior non-GBM Phase 2+ found (provisional category 3): confirm indication and date
  4 unapproved, no prior non-GBM Phase 2+ found (provisional category 1): confirm by a registry search

Trial start dates come from the frozen ClinicalTrials.gov snapshots in data/raw/.
Outputs:
  outputs/main/origin_agents_D32.csv     one row per candidate per trial (input for 06_derive_origin_v2.py);
                                         written once, later runs check it is unchanged
  outputs/main/origin_review_D32_v2.xlsx Read_me, Agents (one row per agent), Events, Development (refuses to
                                         overwrite; v1 origin_review_D32.xlsx kept)
v2 (2026-11-04): adds development_events_draft_D32_ctgov.csv (05d registry search), which supersedes a ChEMBL
`none_found` row for the same agent; agents with a generic, unidentifiable name go to tier 1.

Usage: python3 scripts/13_build_origin_evidence_sheet.py
"""
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
REF = ROOT / "data" / "reference"
RAW = [ROOT / "data" / "raw" / "ctgov_raw_20261101T130137Z.json", ROOT / "data" / "raw" / "ctgov_supp_raw_20261101T150223Z.json"]
CACHE = ROOT / "data" / "lookup" / "v1.2"
GENERIC = re.compile(r"^.{1,3}$|bispecific antibody|unspecified", re.I)

spec = importlib.util.spec_from_file_location("origin", ROOT / "scripts" / "06_derive_origin_v2.py")
origin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(origin)


def studies(path):
    d = json.loads(path.read_text())
    return d["studies"] if isinstance(d, dict) and "studies" in d else d


def start_dates():
    out = {}
    for p in RAW:
        for s in studies(p):
            ps = s.get("protocolSection", s)
            n = ps["identificationModule"]["nctId"]
            out[n] = (ps.get("statusModule", {}).get("startDateStruct") or {}).get("date", "")
    return out


def load_draft(names):
    rows = []
    for n in names:
        p = REF / n
        if p.exists():
            rows += list(csv.DictReader(open(p)))
    return rows


def as_table(rows, dated=True):
    """Draft rows in the shape 06_derive_origin_v2.load() returns, marked reviewed so classify() evaluates them."""
    t = {}
    for r in rows:
        r = dict(r, reviewed_by="DRAFT")
        if r.get("event_type") == "none_found":
            continue
        if dated and r.get("phase") != "none_found":
            if not r.get("date_lo"):
                continue
            r["date_lo"], _ = origin.iso(r["date_lo"])
            _, r["date_hi"] = origin.iso(r["date_hi"] or r["date_lo"])
        t.setdefault(r["moiety"].strip().lower(), []).append(r)
    return t


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


def main():
    agents_out, xlsx_out = RUN / "origin_agents_D32.csv", RUN / "origin_review_D32_v2.xlsx"
    if xlsx_out.exists():
        sys.exit(f"{xlsx_out} exists; refusing to overwrite")
    starts = start_dates()
    trials = [r for r in csv.DictReader(open(RUN / "adjudicated_trials_D32.csv")) if r["passes_S4_S6_llm"] == "True"]
    agent_rows = []
    for t in trials:
        for c in json.loads(t["candidates"] or "[]"):
            agent_rows.append({"nct_id": t["nct_id"], "active_moiety": c["active_moiety"].lower(),
                               "role": c.get("role", "experimental_monotherapy"), "trial_start": starts.get(t["nct_id"], ""),
                               "device_dependent": c.get("device_dependent", False), "population_within_label": ""})
    missing = [a["nct_id"] for a in agent_rows if not a["trial_start"]]
    if missing:
        sys.exit(f"no start date for {sorted(set(missing))}")
    if agents_out.exists():
        old = list(csv.DictReader(open(agents_out)))
        if old != [{k: str(v) for k, v in a.items()} for a in agent_rows]:
            sys.exit(f"{agents_out} differs from the current agents; refusing to overwrite")
    else:
        with open(agents_out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(agent_rows[0].keys()))
            w.writeheader()
            w.writerows(agent_rows)

    reg = load_draft(["regulatory_events_draft_D32.csv", "regulatory_events_draft_D32_aliases.csv"])
    dev = load_draft(["development_events_draft_D32.csv", "development_events_draft_D32_aliases.csv"])
    ctgov = load_draft(["development_events_draft_D32_ctgov.csv"])
    generic = {r["moiety"] for r in ctgov if GENERIC.search(r["moiety"])}
    for r in ctgov:
        if r["moiety"] in generic:
            r.update(phase="none_found", indication="", date_lo="", date_hi="",
                     check="generic or abbreviated name: identify the agent before searching; registry hits not used")
    searched = {r["moiety"] for r in ctgov}
    dev = [r for r in dev if not (r["moiety"] in searched and r["phase"] == "none_found")] + ctgov
    aliased = {r["moiety"] for r in load_draft(["regulatory_events_draft_D32_aliases.csv"])}
    # an alias supersedes the moiety's own (failed) lookup
    reg = [r for r in reg if not (r["moiety"] in aliased and r["event_type"] == "none_found")]
    alias_dev = {r["moiety"] for r in load_draft(["development_events_draft_D32_aliases.csv"])}
    dev = [r for r in dev if not (r["moiety"] in alias_dev and r["phase"] == "none_found"
                                  and r["source"].startswith("ChEMBL"))]
    ev_t, dev_t = as_table(reg), as_table(dev)

    by_agent = {}
    for a in agent_rows:
        by_agent.setdefault(a["active_moiety"], []).append(a)
    out = []
    for m, rows in sorted(by_agent.items()):
        Ts = sorted(origin.iso(a["trial_start"])[0] for a in rows)
        early = origin.classify(m, Ts[0], ev_t, dev_t)
        late = origin.classify(m, Ts[-1], ev_t, dev_t)
        idx = origin.classify(m, origin.INDEX_DATE, ev_t, dev_t)
        evs = [r for r in reg if r["moiety"] == m]
        dvs = [r for r in dev if r["moiety"] == m]
        approved = [r for r in evs if r["event_type"] != "none_found"]
        checks = sorted({c.strip() for r in evs + dvs for c in r.get("check", "").split(";") if c.strip()})
        cache = CACHE / f"{re.sub(r'[^a-z0-9]+', '_', m)}.json"
        chembl_max = json.loads(cache.read_text())["chembl"].get("max_phase") if cache.exists() else None
        why = []
        if m in aliased:
            why.append("looked up under another name")
        if GENERIC.search(m):
            why.append("agent not identified (generic or abbreviated name)")
        if early["category"] != late["category"]:
            why.append(f"category changes between its trials ({early['category']} at {Ts[0]}, {late['category']} at {Ts[-1]})")
        if any("date_sensitive" in f for f in early["flags"] + late["flags"]):
            why.append("date-sensitive")
        if any(r["tumour_agnostic"] == "yes" for r in approved):
            why.append("tumour-agnostic indication: date it and decide population_within_label")
        if any(r["glioma"] == "yes" for r in approved):
            why.append("glioma in label: confirm and date")
        if any("non-oncology and oncology" in c or "cancer wording" in c for c in checks):
            why.append("oncology vs non-oncology to confirm")
        if not approved and (chembl_max or 0) >= 4:
            why.append("ChEMBL phase 4 but no FDA/EMA approval found (other regulator, or name mismatch)")
        if early["category"] in ("ESTABLISHED", "2_panel"):
            tier, todo = 2, "no review needed beyond confirming the rule"
        elif why:
            tier, todo = 1, "; ".join(why)
        elif approved:
            tier, todo = 2, "confirm first approval date, jurisdiction and oncology status"
        elif any(d["phase"] in ("1", "2", "3") for d in dvs):
            tier, todo = 3, "confirm the earliest non-GBM Phase 2+ trial (indication not glioma, start before trial)"
        else:
            tier, todo = 4, "confirm no FDA/EMA approval and no non-GBM Phase 2+ before the trial (registry search)"
        fda = min((r["date_lo"] for r in approved if r["jurisdiction"] == "FDA"), default="")
        ema = min((r["date_lo"] for r in approved if r["jurisdiction"] == "EMA"), default="")
        p2 = min((d for d in dvs if d["phase"] in ("1", "2", "3")), key=lambda d: d["date_lo"], default=None)
        out.append([tier, m, len({a["nct_id"] for a in rows}), Ts[0], Ts[-1], early["category"], late["category"],
                    idx["category"], early["regulatory_status"], fda, ema,
                    "yes" if any(r["oncology"] == "yes" for r in approved) else ("no" if approved else ""),
                    "yes" if any(r["tumour_agnostic"] == "yes" for r in approved) else "",
                    "yes" if any(r["glioma"] == "yes" for r in approved) else "",
                    chembl_max, (p2 or {}).get("date_lo", ""), (p2 or {}).get("source", ""), todo,
                    "; ".join(checks), "; ".join(sorted({a["nct_id"] for a in rows})), "", "", ""])
    out.sort(key=lambda r: (r[0], -r[2], r[1]))

    wb = Workbook()
    ws = wb.active
    ws.title = "Read_me"
    n_t = {k: sum(r[0] == k for r in out) for k in (1, 2, 3, 4)}
    for line in [
        "D21 correction review, part 2 - drug origin of every candidate agent",
        "",
        f"{len(out)} candidate agents in {len(trials)} trials passing S5-S6 (before structured-field steps). "
        f"Tier 1 (category in doubt): {n_t[1]}; tier 2 (approved, clear): {n_t[2]}; tier 3 (unapproved, prior "
        f"non-GBM Phase 2+ found): {n_t[3]}; tier 4 (unapproved, none found): {n_t[4]}.",
        "Provisional categories are what 06_derive_origin_v2 would give IF the draft event rows were correct. They are "
        "not final: the reference tables stay unreviewed until you sign rows off.",
        "Categories: ESTABLISHED (D6), GLIOMA_DEVELOPED, 2a approved non-oncology, 2b approved oncology, 3 unapproved "
        "with prior non-GBM Phase 2+, 1 operational de novo. Origin is judged at the earliest trial start (D12); the "
        "latest-start and index-date columns show whether the category changes across the agent's trials.",
        "How to review: for each agent fill XL_confirm (yes = the draft events are correct and complete; no = see note) "
        "and, if needed, XL_category and XL_note (e.g. a missing approval with its date and source). Work top-down: "
        "tier 1 needs real checking; tiers 2-4 are mostly confirmations.",
        "Events and Development sheets list every draft row with its source and check note.",
        "Rules: D4-D7, D12, D20 (dated events, 2c dropped, tumour_agnostic_at_T flag), D21, D26.",
    ]:
        ws.append([line])
    ws.column_dimensions["A"].width = 140
    for row in ws.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A1"].font = Font(bold=True)
    write_sheet(wb.create_sheet("Agents"),
                ["tier", "active_moiety", "n_trials", "earliest_start", "latest_start", "provisional_cat_earliest",
                 "provisional_cat_latest", "provisional_cat_index_date", "regulatory_status_at_earliest",
                 "first_FDA", "first_EMA", "oncology", "tumour_agnostic", "glioma", "chembl_max_phase",
                 "first_nonGBM_phase2plus", "phase2_source", "what_to_check", "draft_check_notes", "trials",
                 "XL_confirm", "XL_category", "XL_note"],
                out, [5, 24, 7, 11, 11, 12, 12, 12, 16, 11, 11, 8, 8, 7, 7, 12, 22, 45, 60, 40, 10, 12, 30])
    write_sheet(wb.create_sheet("Events"), list(reg[0].keys()),
                [[r[k] for k in reg[0].keys()] for r in sorted(reg, key=lambda r: (r["moiety"], r["date_lo"]))],
                [22, 9, 18, 50, 8, 8, 7, 11, 11, 40, 30, 10, 10, 60])
    write_sheet(wb.create_sheet("Development"), list(dev[0].keys()),
                [[r[k] for k in dev[0].keys()] for r in sorted(dev, key=lambda r: r["moiety"])],
                [22, 10, 30, 11, 11, 40, 10, 60])
    wb.save(xlsx_out)
    print(f"agents {len(out)} in {len(trials)} trials; candidate-trial rows {len(agent_rows)}; tiers {n_t}")
    cats = {}
    for r in out:
        cats[r[5]] = cats.get(r[5], 0) + 1
    print("provisional category at earliest start:", cats)


if __name__ == "__main__":
    main()
