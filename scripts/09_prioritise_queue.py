"""
Step 09 - Prioritise the main-pass adjudication queue (post-registration processing step; does not
change 07_compare_coders_v2.py or any coded value).

Adds two columns to a copy of <run>/adjudication_queue.csv:
  priority  1 = can change trial inclusion, candidate status or the primary outcome
            2 = trial-level variable of a trial that at least one coder includes
            3 = detail (naming, regimen_id, arms, non-selection biomarker rows) or a trial both coders exclude
  quote_unescaped_ok  for quote_not_verbatim rows: "yes" if the quote matches the record once
                      ClinicalTrials.gov backslash escapes (\\> \\< \\[ \\] \\^ \\* \\- \\~ \\_ \\&) are removed
Also writes <run>/adjudication_summary.csv: one row per trial with counts by priority and whether
each coder includes the trial.

Usage: python3 scripts/09_prioritise_queue.py outputs/main
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P1_ITEMS = {"gbm_population", "has_eligible_candidate", "candidate_exclusion_reason", "candidate_set",
            "candidate_matched_selection"}
P2_ITEMS = {"cns5_terminology", "treatment_setting", "regimen", "basket", "control_arm_from_other_arms",
            "tumour_pk_planned", "target_engagement_planned", "any_molecular_selection", "combination_partners"}
CANDIDATE_ROLES = {"experimental_monotherapy", "experimental_combination"}
UNESC = re.compile(r"\\([><\[\]^*\-~_&#])")


def included(d):
    return d["screening"]["gbm_population"] in ("gbm_only", "mixed_glioma_gbm_named", "basket_gbm_eligible") \
        and d["screening"]["has_eligible_candidate"]


def priority(row, inc_any):
    item, typ = row["item"], row["type"]
    if typ in ("missing_output", "invalid_output", "unexpected_output", "disagreement_outcome"):
        return 1
    if typ == "uncertain":
        detail = row["item"].split(": ", 1)[-1]
        if detail in ("gbm_population_flag", "candidate_flag"):
            return 1
        if detail.startswith("agent:") or detail.startswith("biomarker:"):
            return 1 if inc_any else 3
        return 2 if inc_any else 3
    if typ == "quote_not_verbatim":
        return 3
    if item in P1_ITEMS:
        return 1
    m = re.match(r"agent:[^:]+:role", item)
    if m and (row["coder_A_or_detail"].strip('"') in CANDIDATE_ROLES or row["coder_B"].strip('"') in CANDIDATE_ROLES):
        return 1 if inc_any else 3
    if item in P2_ITEMS:
        return 2 if inc_any else 3
    return 3


def main(run_dir):
    run = Path(run_dir)
    inc = {}
    for p in sorted((run / "coderA").glob("NCT*.json")):
        a = json.loads(p.read_text())
        b = json.loads((run / "coderB" / p.name).read_text())
        inc[p.stem] = (included(a), included(b))
    rows = list(csv.DictReader(open(run / "adjudication_queue.csv")))
    out = []
    for r in rows:
        ia, ib = inc.get(r["nct_id"], (False, False))
        r["priority"] = priority(r, ia or ib)
        r["quote_unescaped_ok"] = ""
        if r["type"] == "quote_not_verbatim":
            text = " ".join(UNESC.sub(r"\1", (ROOT / "data" / "coder_input" / f"{r['nct_id']}.txt").read_text()).split())
            r["quote_unescaped_ok"] = "yes" if " ".join(r["coder_A_or_detail"].split()) in text else "no"
        out.append(r)
    dst = run / "adjudication_queue_prioritised.csv"
    if dst.exists():
        sys.exit(f"{dst} exists; refusing to overwrite")
    with open(dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["priority"] + list(rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(out, key=lambda r: (r["priority"], r["nct_id"])))
    summ = {}
    for r in out:
        s = summ.setdefault(r["nct_id"], {"p1": 0, "p2": 0, "p3": 0})
        s[f"p{r['priority']}"] += 1
    with open(run / "adjudication_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nct_id", "coder_A_includes", "coder_B_includes", "priority1_items", "priority2_items", "priority3_items"])
        for n in sorted(inc):
            s = summ.get(n, {"p1": 0, "p2": 0, "p3": 0})
            w.writerow([n, inc[n][0], inc[n][1], s["p1"], s["p2"], s["p3"]])
    by = {k: sum(1 for r in out if r["priority"] == k) for k in (1, 2, 3)}
    trials = {k: len({r["nct_id"] for r in out if r["priority"] == k}) for k in (1, 2, 3)}
    nv = [r for r in out if r["type"] == "quote_not_verbatim"]
    print(f"queue rows by priority: {by}; trials with any item: {trials}")
    print(f"non-verbatim quotes: {len(nv)}, of which match after unescaping: {sum(r['quote_unescaped_ok']=='yes' for r in nv)}")


if __name__ == "__main__":
    main(sys.argv[1])
