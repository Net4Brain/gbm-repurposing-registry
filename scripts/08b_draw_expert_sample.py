"""
Step 08b - Draw the 100-record expert validation sample (option b; replaces the negatives-only design of
08_draw_validation_sample.py, which is kept unchanged).

Drawn BEFORE the main pass, from structured registry fields only (no AI output exists for these records):
  population : the 870 screening records minus the 60 calibration records (rounds 1-3) = 810
  strata     : phase group (EP1 / P1 / P2 / P3 / other) x lead sponsor class (industry / non-industry)
  allocation : proportional to stratum size (largest remainder), so the sample is self-weighting;
               the stratum sizes are written out so weights can be checked
  seed       : 20261104

Two invited experts code every sampled record independently, blind to the AI output and to each other,
with the frozen coding manual; their consensus is the reference standard.

Output: data/processed/expert_validation_sample.csv (nct_id, stratum, stratum_N, stratum_n, weight)
Usage : python3 scripts/08b_draw_expert_sample.py
"""
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED, N = 20261104, 100
MAIN = ROOT / "data" / "raw" / "ctgov_raw_20261101T130137Z.json"
SUPP = ROOT / "data" / "raw" / "ctgov_supp_raw_20261101T150223Z.json"
SUPP_LIST = ROOT / "data" / "processed" / "supp_added_to_screening.csv"
CALIBRATION = [ROOT / "data" / "processed" / "calibration_set.csv", ROOT / "data" / "processed" / "calibration_set_r3.csv"]
OUT = ROOT / "data" / "processed" / "expert_validation_sample.csv"


def phase_group(p):
    ph = p.get("designModule", {}).get("phases", [])
    for code, g in (("EARLY_PHASE1", "EP1"), ("PHASE3", "P3"), ("PHASE2", "P2"), ("PHASE1", "P1")):
        if code in ph:
            return g
    return "other"


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite")
    used = {r["nct_id"] for p in CALIBRATION for r in csv.DictReader(open(p))}
    supp_ids = {r["nct_id"] for r in csv.DictReader(open(SUPP_LIST))}
    studies = json.load(open(MAIN)) + [s for s in json.load(open(SUPP))
                                       if s["protocolSection"]["identificationModule"]["nctId"] in supp_ids]
    strata = {}
    for s in studies:
        p = s["protocolSection"]
        nct = p["identificationModule"]["nctId"]
        if nct in used:
            continue
        spons = "industry" if p["sponsorCollaboratorsModule"]["leadSponsor"].get("class") == "INDUSTRY" else "non_industry"
        strata.setdefault(f"{phase_group(p)}_{spons}", []).append(nct)
    total = sum(len(v) for v in strata.values())
    quota = {k: N * len(v) / total for k, v in strata.items()}
    alloc = {k: int(q) for k, q in quota.items()}
    for k in sorted(quota, key=lambda k: (-(quota[k] - alloc[k]), k))[:N - sum(alloc.values())]:
        alloc[k] += 1
    rng = random.Random(SEED)
    rows = []
    for k in sorted(strata):
        ids = sorted(strata[k])
        for nct in sorted(rng.sample(ids, alloc[k])):
            rows.append({"nct_id": nct, "stratum": k, "stratum_N": len(ids), "stratum_n": alloc[k],
                         "weight": round(len(ids) / alloc[k], 4) if alloc[k] else ""})
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nct_id", "stratum", "stratum_N", "stratum_n", "weight"])
        w.writeheader()
        w.writerows(rows)
    print(f"population {total}; sample {len(rows)} -> {OUT}")
    for k in sorted(strata):
        print(f"  {k:22} N={len(strata[k]):4}  n={alloc[k]}")


if __name__ == "__main__":
    main()
