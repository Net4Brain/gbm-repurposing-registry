"""
Step 20 - Active-pipeline subset (D2, D13, D24): trials of the primary cohort that were active on the index date,
31 July 2026, with recruitment status reconstructed from each record's ClinicalTrials.gov version history.
Post-registration processing step.

Input : data/reference/status_history_index_D41.csv, the status of the last registry version on or before 2026-07-31
        (and of the next version), captured 2026-11-04 from the public record-history page
Rules :
  active      = RECRUITING, NOT_YET_RECRUITING, ACTIVE_NOT_RECRUITING or ENROLLING_BY_INVITATION (manuscript Methods)
  inactive    = COMPLETED, TERMINATED, SUSPENDED or WITHDRAWN
  not reconstructable = status UNKNOWN in the history, or an active status whose last update before the index date was
                more than two years earlier (the registry's own rule for "unknown status"); reported separately
  The version date is the registry update date; status changes reported late are attributed to their report date.
Outputs (outputs/analysis_D40/, each refused if it exists): status_at_index_D41.csv, active_subset_results.csv
Usage: python3 scripts/20_active_subset.py
"""
import csv
import importlib.util
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("a", ROOT / "scripts" / "17_analysis.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
ACTIVE = {"RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING", "ENROLLING_BY_INVITATION"}
INACTIVE = {"COMPLETED", "TERMINATED", "SUSPENDED", "WITHDRAWN"}
STALE_BEFORE = "2024-07-31"


def classify(s, date):
    if s in ACTIVE:
        return "active" if date >= STALE_BEFORE else "not_reconstructable (no update within 2 years)"
    if s in INACTIVE:
        return "inactive"
    return "not_reconstructable (status unknown)"


def main():
    hist = {r["nct_id"]: r for r in csv.DictReader(open(ROOT / "data" / "reference" / "status_history_index_D41.csv"))}
    T = A.load()
    coh = [t for t in T if t["in_cohort"]]
    assert {t["nct_id"] for t in coh} == set(hist), "history does not match the cohort"
    rows = []
    for t in coh:
        h = hist[t["nct_id"]]
        s, d = h["status_last_version_on_or_before_2026-07-31"], h["version_date"]
        t["index_class"] = classify(s, d)
        rows.append({"nct_id": t["nct_id"], "status_at_index": s, "version_date": d, "class": t["index_class"],
                     "origin_group": A.group(t["cands"]), "selected": t["selected"]})
    A.write("status_at_index_D41.csv", rows)
    act = lambda t: t["in_cohort"] and t.get("index_class") == "active"
    res = [A.h1(T, "Active subset (31 July 2026): H1 primary", pop=act)]
    res.append(A.h1(T, "Active subset, counting not-reconstructable trials as active (sensitivity)",
                    pop=lambda t: t["in_cohort"] and t.get("index_class", "").startswith(("active", "not_reconstructable"))))
    ag = A.agent_level(T, "Active subset: unique candidate agents", pop=act)
    res_rows = res + [{"analysis": ag["analysis"], "note": f"agents {ag['agents']}; repurposing {ag['repurposing_2']} "
                       f"({ag['pct_2']}%, {ag['ci_2']}); 2a {ag['n_2a']}; 2b {ag['n_2b']}; 3 {ag['n_3']}; 1 {ag['n_1']}"}]
    keys = list(res[0].keys())
    A.write("active_subset_results.csv", [{k: r.get(k, "") for k in keys} for r in res_rows])
    c = Counter(r["class"] for r in rows)
    print("status at index:", dict(c))
    print("active trials by origin group:", dict(Counter(r["origin_group"] for r in rows if r["class"] == "active")))
    for r in res:
        print(f"{r['analysis']}: {r['de_novo_selected']}/{r['de_novo_n']} vs {r['repurposing_selected']}/{r['repurposing_n']}"
              f"  RD {r['risk_difference_pp']} ({r['ci_low_pp']} to {r['ci_high_pp']})")
    print(res_rows[-1]["note"])


if __name__ == "__main__":
    main()
