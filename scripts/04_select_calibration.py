"""
Step 04 - Draw the 40-record calibration set (coding manual section 8).

Stratified, reproducible (fixed seed) draw from the 870-record screening set:
  - 8 supplementary-search records, 32 main-search records
  - main records spread across registry phase groups (P1, P2, P3, excluded phases) and sponsor class
  - at least 6 records listed in ReDO_Trials_DB (known repurposing) so every origin path is exercised
Calibration records are coded again in the main pass under the frozen manual.

Output: data/processed/calibration_set.csv

Usage: python3 scripts/04_select_calibration.py
"""
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261101
MAIN = ROOT / "data" / "raw" / "ctgov_raw_20261101T130137Z.json"
SUPP = ROOT / "data" / "raw" / "ctgov_supp_raw_20261101T150223Z.json"
SUPP_LIST = ROOT / "data" / "processed" / "supp_added_to_screening.csv"
REDO = ROOT / "data" / "raw" / "ReDO_Trials_DB_20261101.txt"


def phase_group(s):
    ph = set(s["protocolSection"].get("designModule", {}).get("phases", []))
    if ph & {"PHASE3"}:
        return "P3"
    if ph & {"PHASE2"}:
        return "P2"
    if ph & {"PHASE1"}:
        return "P1"
    return "excluded_phase"


def sponsor(s):
    c = s["protocolSection"]["sponsorCollaboratorsModule"]["leadSponsor"].get("class")
    return "industry" if c == "INDUSTRY" else "non_industry"


def main():
    rng = random.Random(SEED)
    nct = lambda s: s["protocolSection"]["identificationModule"]["nctId"]
    main_studies = json.loads(MAIN.read_text())
    keep = {r["nct_id"] for r in csv.DictReader(open(SUPP_LIST))}
    supp = [s for s in json.loads(SUPP.read_text()) if nct(s) in keep]
    redo = {line.split("\t")[0] for line in REDO.read_text(encoding="latin-1").splitlines()[1:]}

    chosen = []
    redo_pool = sorted((s for s in main_studies if nct(s) in redo), key=nct)
    chosen += [(s, "redo") for s in rng.sample(redo_pool, 6)]
    taken = {nct(s) for s, _ in chosen}

    quota = {("P1", "industry"): 4, ("P1", "non_industry"): 5, ("P2", "industry"): 4,
             ("P2", "non_industry"): 6, ("P3", "industry"): 2, ("P3", "non_industry"): 2,
             ("excluded_phase", "industry"): 1, ("excluded_phase", "non_industry"): 2}
    for (pg, sp), k in quota.items():
        pool = sorted((s for s in main_studies if nct(s) not in taken and phase_group(s) == pg and sponsor(s) == sp), key=nct)
        pick = rng.sample(pool, min(k, len(pool)))
        chosen += [(s, f"main_{pg}_{sp}") for s in pick]
        taken |= {nct(s) for s in pick}
    chosen += [(s, "supplementary") for s in rng.sample(sorted(supp, key=nct), 8)]

    out = ROOT / "data" / "processed" / "calibration_set.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nct_id", "stratum", "phase_group", "sponsor_class", "brief_title"])
        for s, stratum in chosen:
            w.writerow([nct(s), stratum, phase_group(s), sponsor(s),
                        s["protocolSection"]["identificationModule"]["briefTitle"]])
    print(f"{len(chosen)} calibration records (seed {SEED}) -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
