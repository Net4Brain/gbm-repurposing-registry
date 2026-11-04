"""
Step 16 - External validation against ReDO_Trials_DB (D10). Post-registration processing step; reads only.

Every ReDO trial that is in the final eligible cohort should be coded as approved-drug repurposing (trial in
repurposing_containing, with the ReDO drug coded category 2). Discrepancies are listed for adjudication and reported.
ReDO is used only as a check: it never adds or removes trials.

Inputs : data/raw/ReDO_Trials_DB_20261101.txt (frozen, tab-separated), outputs/main/screening_D37.csv,
         outputs/main/origin_derived_D36.csv, outputs/main/origin_trial_groups_D36.csv
Output (new file; refuses to overwrite): outputs/main/redo_check_D39.csv, one row per ReDO trial in the screening set:
  screening outcome, cohort membership, origin group, ReDO drug(s), how each was coded, and the check result.
Second output: outputs/main/redo_unmatched_glioma_D39.csv, a retrieval-completeness audit: ReDO glioma trials starting in
the D2 window that are NOT in our screening set, with the registry and the reason (ReDO never adds trials).
Usage: python3 scripts/16_redo_check.py
"""
import csv
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
REDO = ROOT / "data" / "raw" / "ReDO_Trials_DB_20261101.txt"


REASONS = {  # checked against the live registry 2026-11-04
    "NCT05634707": "not glioblastoma: 'primary brain tumor', glioblastoma not named (also Early Phase 1)",
    "NCT04576117": "not glioblastoma: paediatric low-grade glioma (selumetinib)",
    "NCT04166409": "not glioblastoma: low-grade glioma (selumetinib); start 2020-01-31",
    "NCT07758062": "start outside window: registry start date 2026-09-01 (estimated); first posted 2026-08-11",
}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def main():
    out, out_u = RUN / "redo_check_D39.csv", RUN / "redo_unmatched_glioma_D39.csv"
    if out_u.exists():
        sys.exit(f"{out_u} exists; refusing to overwrite")
    redo = {}
    for r in csv.DictReader(open(REDO, encoding="utf-8", errors="replace"), delimiter="\t"):
        n = (r.get("NCT Number") or "").strip()   # also non-ClinicalTrials.gov IDs (CTIS, ChiCTR, ...)
        if n:
            redo.setdefault(n, []).append(r)
    screen = {r["nct_id"]: r for r in csv.DictReader(open(RUN / "screening_D37.csv"))}
    groups = {r["nct_id"]: r for r in csv.DictReader(open(RUN / "origin_trial_groups_D36.csv"))}
    cands = {}
    for r in csv.DictReader(open(RUN / "origin_derived_D36.csv")):
        cands.setdefault(r["nct_id"], []).append(r)
    rows = []
    for n in sorted(set(redo) & set(screen)):
        s, rr = screen[n], redo[n]
        inns = sorted({x.strip() for r in rr for x in re.split(r"[;,|/]| \+ ", r.get("Drug_INN") or "") if x.strip()})
        coded = []
        for inn in inns:
            hit = [c for c in cands.get(n, []) if norm(inn) in norm(c["active_moiety"]) or norm(c["active_moiety"]) in norm(inn)]
            coded.append(f"{inn}: " + (", ".join(f"{c['active_moiety']}={c['origin_trial_start']}" for c in hit) if hit else "not a coded candidate"))
        in_cohort = s["primary_cohort"] == "yes"
        grp = groups.get(n, {}).get("primary_group", "")
        if not in_cohort:
            result = "not in cohort (" + (s["exclusion_reason"] or ("withdrawn" if s["withdrawn"] == "yes" else "")) + ")"
        elif grp == "repurposing_containing":
            drug2 = any(("=2a" in c or "=2b" in c or "=2_panel" in c) for c in coded)
            result = "agree" if drug2 else "agree at trial level; ReDO drug not coded category 2"
        else:
            result = f"DISCREPANCY: coded {grp}"
        rows.append({"nct_id": n, "in_cohort": "yes" if in_cohort else "no", "exclusion_reason": s["exclusion_reason"],
                     "withdrawn": s["withdrawn"], "origin_primary_group": grp, "redo_drug_inn": "; ".join(inns),
                     "redo_removed": "; ".join(sorted({r.get("Removed", "") for r in rr})),
                     "redo_title": rr[0].get("Title", "")[:150], "our_coding_of_redo_drugs": " | ".join(coded),
                     "result": result})
    if not out.exists():
        with open(out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    unmatched = []
    for n, rr in sorted(redo.items()):
        r = rr[0]
        text = " ".join([r.get("Conditions", ""), r.get("Title", ""), r.get("Cancer_Type", "")])
        if n in screen or not re.search(r"glioblastoma|\bGBM\b|gliosarcoma|glioma", text, re.I):
            continue
        try:
            d = datetime.strptime(r.get("Start Date", ""), "%d/%m/%Y").date().isoformat()
        except ValueError:
            continue
        if not ("2020-01-01" <= d <= "2026-07-31"):
            continue
        unmatched.append({"trial_id": n, "registry": "ClinicalTrials.gov" if n.startswith("NCT") else "other registry",
                          "redo_start": d, "redo_phase": r.get("Phase", ""), "title": r.get("Title", "")[:150],
                          "drug_inn": r.get("Drug_INN", ""),
                          "reason_not_in_screening_set": REASONS.get(n, "not on ClinicalTrials.gov (outside D3 source)"
                                                                     if not n.startswith("NCT") else "to check")})
    with open(out_u, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(unmatched[0].keys()))
        w.writeheader()
        w.writerows(unmatched)
    print(f"unmatched ReDO glioma trials in window: {len(unmatched)}; "
          + str(dict(Counter(u["reason_not_in_screening_set"].split(":")[0] for u in unmatched))))
    coh = [r for r in rows if r["in_cohort"] == "yes"]
    agree = sum(r["result"].startswith("agree") for r in coh)
    print(f"ReDO records {sum(len(v) for v in redo.values())} ({sum(k.startswith('NCT') for k in redo)} NCT IDs); in our screening set: {len(rows)}; "
          f"in the primary cohort: {len(coh)}")
    print(f"cohort ReDO trials coded repurposing_containing: {agree}/{len(coh)}")
    print("results:", dict(Counter(r["result"].split(" (")[0] for r in rows)))


if __name__ == "__main__":
    main()
