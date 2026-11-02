"""
Step 08 - Draw the human validation ("measurement") sample of AI-agreed negatives and exclusions
(D21; coding manual v1.3 section 7.5b). Its SHA-256 is frozen before the main pass, so the sample
design cannot be changed after the AI output is seen.

Every positive decision (candidate origin, candidate-matched selection) is reviewed in full, so this
sample covers only what is NOT reviewed in full: records where both coders agree on a negative.

Strata (records used in any calibration round are never sampled):
  EXCL   both coders exclude the record at S5 or S6                          n = 30
  NEG_M  both include it, neither codes candidate-matched selection, and at
         least one codes some other eligibility/enrichment biomarker          n = 15
  NEG_0  both include it, neither codes any eligibility/enrichment biomarker  n = 25
If a stratum has fewer records than its target, all of its records are taken.
Sampling weight = stratum population / stratum sample size.

XL codes each sampled record blind to the AI output (fresh copy of the coder input only).

Output: <run_dir>/validation_sample.csv  (nct_id, stratum, stratum_N, stratum_n, weight)
Usage : python3 scripts/08_draw_validation_sample.py outputs/main
"""
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261103
TARGET = {"EXCL": 30, "NEG_M": 15, "NEG_0": 25}
CALIBRATION = [ROOT / "data" / "processed" / "calibration_set.csv", ROOT / "data" / "processed" / "calibration_set_r3.csv"]


def stratum(a, b):
    inc = lambda d: d["screening"]["gbm_population"] in ("gbm_only", "mixed_glioma_gbm_named", "basket_gbm_eligible") \
        and d["screening"]["has_eligible_candidate"]
    sel = lambda d: [x for x in d["biomarkers"] if x["role"] in ("eligibility", "enrichment")]
    matched = lambda d: any(x["candidate_matched"] for x in sel(d))
    if not inc(a) and not inc(b):
        return "EXCL"
    if inc(a) and inc(b) and not matched(a) and not matched(b):
        return "NEG_M" if (sel(a) or sel(b)) else "NEG_0"
    return None          # disagreement or a positive: reviewed in full, not sampled


def main(run_dir):
    run = Path(run_dir)
    used = {r["nct_id"] for p in CALIBRATION for r in csv.DictReader(open(p))}
    pools = {k: [] for k in TARGET}
    for pa in sorted((run / "coderA").glob("NCT*.json")):
        pb = run / "coderB" / pa.name
        if pa.stem in used or not pb.exists():
            continue
        s = stratum(json.loads(pa.read_text()), json.loads(pb.read_text()))
        if s:
            pools[s].append(pa.stem)
    rng = random.Random(SEED)
    rows = []
    for s, ids in pools.items():
        take = sorted(rng.sample(ids, min(TARGET[s], len(ids))))
        for n in take:
            rows.append({"nct_id": n, "stratum": s, "stratum_N": len(ids), "stratum_n": len(take),
                         "weight": round(len(ids) / len(take), 4)})
    out = run / "validation_sample.csv"
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nct_id", "stratum", "stratum_N", "stratum_n", "weight"])
        w.writeheader()
        w.writerows(rows)
    print({s: (len(pools[s]), sum(r["stratum"] == s for r in rows)) for s in TARGET}, "->", out)


if __name__ == "__main__":
    main(sys.argv[1])
