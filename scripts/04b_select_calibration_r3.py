"""
Step 04b - Draw the 20-record calibration round-3 set (coding manual v1.3 section 8; D23, D26).

Fresh records only: never one of the 40 round-1/2 records. Stratified, fixed seed:
  - 4 Early Phase 1 records (translational subset, D23)
  - 6 records whose text mentions tumour/CSF drug levels or pharmacodynamic/target endpoints,
    to exercise tumour_pk_planned and target_engagement_planned
  - 10 further main-search records spread over phase groups P1 / P2 / P3 and sponsor class
Records used here are also excluded from the D21 validation sample.

Output: data/processed/calibration_set_r3.csv

Usage: python3 scripts/04b_select_calibration_r3.py
"""
import csv
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261102
MAIN = ROOT / "data" / "raw" / "ctgov_raw_20261101T130137Z.json"
SUPP = ROOT / "data" / "raw" / "ctgov_supp_raw_20261101T150223Z.json"
SUPP_LIST = ROOT / "data" / "processed" / "supp_added_to_screening.csv"
R1 = ROOT / "data" / "processed" / "calibration_set.csv"
OUT = ROOT / "data" / "processed" / "calibration_set_r3.csv"
PKPD = re.compile(r"(tumou?r|tissue|CSF|cerebrospinal)[^.]{0,60}(concentration|level|penetration|exposure)|"
                  r"pharmacodynamic|target (engagement|modulation|inhibition)|window[- ]of[- ]opportunity|phase 0", re.I)


def phase_group(s):
    ph = s["protocolSection"].get("designModule", {}).get("phases", [])
    if "EARLY_PHASE1" in ph:
        return "EP1"
    if "PHASE3" in ph:
        return "P3"
    if "PHASE2" in ph:
        return "P2"
    if "PHASE1" in ph:
        return "P1"
    return "other"


def main():
    used = {r["nct_id"] for r in csv.DictReader(open(R1))}
    supp_ids = {r["nct_id"] for r in csv.DictReader(open(SUPP_LIST))}
    studies = json.load(open(MAIN)) + [s for s in json.load(open(SUPP)) if s["protocolSection"]["identificationModule"]["nctId"] in supp_ids]
    pool = sorted((s for s in studies if s["protocolSection"]["identificationModule"]["nctId"] not in used),
                  key=lambda s: s["protocolSection"]["identificationModule"]["nctId"])
    nct = lambda s: s["protocolSection"]["identificationModule"]["nctId"]
    sponsor = lambda s: "industry" if s["protocolSection"]["sponsorCollaboratorsModule"]["leadSponsor"].get("class") == "INDUSTRY" else "non_industry"
    rng = random.Random(SEED)
    chosen = []
    take = lambda cands, k, why: chosen.extend((s, why) for s in rng.sample([c for c in cands if c not in [x for x, _ in chosen]], k))
    take([s for s in pool if phase_group(s) == "EP1"], 4, "early_phase1")
    take([s for s in pool if phase_group(s) in ("P1", "P2", "P3") and PKPD.search(json.dumps(s["protocolSection"]))], 6, "pk_pd_text")
    for pg, spons, k in (("P1", "industry", 2), ("P1", "non_industry", 2), ("P2", "industry", 2), ("P2", "non_industry", 2),
                         ("P3", "industry", 1), ("P3", "non_industry", 1)):
        take([s for s in pool if phase_group(s) == pg and sponsor(s) == spons], k, f"{pg}_{spons}")
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nct_id", "stratum", "phase_group", "sponsor_class"])
        for s, why in sorted(chosen, key=lambda x: nct(x[0])):
            w.writerow([nct(s), why, phase_group(s), sponsor(s)])
    print(f"wrote {len(chosen)} records to {OUT}")


if __name__ == "__main__":
    main()
