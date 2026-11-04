"""
Step 14 - Apply the screening steps S1-S7 (coding manual v1.4 section 1) to every screening record and build the
analytic cohort. Post-registration processing step.

[CODE] steps from the frozen ClinicalTrials.gov snapshots (data/raw/, retrieved 2026-11-01):
  S1 study_type  must be INTERVENTIONAL                                   -> not_interventional
  S2 start_date  2020-01-01 to 2026-07-31, actual or anticipated (D2, D24) -> start_outside_window
  S3 phase       PHASE1, PHASE1/2, PHASE2, PHASE2/3, PHASE3; EARLY_PHASE1 -> phase0_early_phase1 (translational subset,
                 D8, D23), PHASE4 -> phase4, NA or missing -> phase_not_applicable
  S4 age_scope   stdAges must include ADULT (CHILD-only excluded; CHILD + ADULT flagged mixed_age) -> paediatric_only
[LLM, adjudicated] steps from outputs/main/adjudicated_trials_D32.csv (D30-D33):
  S5 gbm_population in gbm_only / mixed_glioma_gbm_named / basket_gbm_eligible, else its value is the reason
  S6 has_eligible_candidate, else candidate_exclusion_reason
S7 overallStatus WITHDRAWN: removed from the cohort and reported separately; contributes no agents.
The first failed step gives the exclusion reason (Figure 1). Month-only start dates are compared by their first day.

Outputs (new files; refuses to overwrite):
  outputs/main/screening_D37.csv   one row per record: structured fields, step results, exclusion reason, cohort flags
  outputs/main/cohort_D37.csv      the primary analytic cohort (pass S1-S6, not withdrawn) with origin group (D36) and
                                   candidate-matched selection
Usage: python3 scripts/14_apply_screening.py
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
RAW = [ROOT / "data" / "raw" / "ctgov_raw_20261101T130137Z.json", ROOT / "data" / "raw" / "ctgov_supp_raw_20261101T150223Z.json"]
WINDOW = ("2020-01-01", "2026-07-31")
OK_PHASES = [["PHASE1"], ["PHASE1", "PHASE2"], ["PHASE2"], ["PHASE2", "PHASE3"], ["PHASE3"]]
INCLUDED_POP = ("gbm_only", "mixed_glioma_gbm_named", "basket_gbm_eligible")


def studies():
    out = {}
    for p in RAW:
        d = json.loads(p.read_text())
        for s in (d["studies"] if isinstance(d, dict) else d):
            ps = s.get("protocolSection", s)
            out.setdefault(ps["identificationModule"]["nctId"], ps)
    return out


def first_day(d):
    d = (d or "").strip()
    return d if len(d) == 10 else (d + "-01" if len(d) == 7 else (d + "-01-01" if len(d) == 4 else ""))


def main():
    out_s, out_c = RUN / "screening_D37.csv", RUN / "cohort_D37.csv"
    for p in (out_s, out_c):
        if p.exists():
            sys.exit(f"{p} exists; refusing to overwrite")
    snap = studies()
    adj = {r["nct_id"]: r for r in csv.DictReader(open(RUN / "adjudicated_trials_D32.csv"))}
    groups = {r["nct_id"]: r for r in csv.DictReader(open(RUN / "origin_trial_groups_D36.csv"))}
    manifest = [l.strip() for l in open(RUN / "manifest.txt") if l.strip()]
    rows = []
    for n in manifest:
        ps, a = snap[n], adj[n]
        design, status, elig = ps.get("designModule", {}), ps.get("statusModule", {}), ps.get("eligibilityModule", {})
        stype = design.get("studyType", "")
        sd = status.get("startDateStruct") or {}
        start, stype_date = sd.get("date", ""), sd.get("type", "")
        phases = sorted(design.get("phases", []) or [])
        ages = elig.get("stdAges", []) or []
        overall = status.get("overallStatus", "")
        reason = ""
        if stype != "INTERVENTIONAL":
            reason = "not_interventional"
        elif not start or not (WINDOW[0] <= first_day(start) <= WINDOW[1]):
            reason = "start_outside_window"
        elif phases not in OK_PHASES:
            reason = ("phase0_early_phase1" if "EARLY_PHASE1" in phases else
                      "phase4" if phases == ["PHASE4"] else "phase_not_applicable")
        elif "ADULT" not in ages:
            reason = "paediatric_only"
        elif a["gbm_population"] not in INCLUDED_POP:
            reason = a["gbm_population"]
        elif str(a["has_eligible_candidate"]) not in ("True", "true"):
            reason = a["candidate_exclusion_reason"] or "no_candidate"
        withdrawn = overall == "WITHDRAWN"
        translational = (reason == "phase0_early_phase1" and "ADULT" in ages and a["gbm_population"] in INCLUDED_POP
                         and str(a["has_eligible_candidate"]) in ("True", "true") and not withdrawn)
        g = groups.get(n, {})
        rows.append({"nct_id": n, "study_type": stype, "start_date": start, "start_type": stype_date,
                     "phases": "/".join(phases) or "NA", "std_ages": "/".join(ages), "overall_status": overall,
                     "mixed_age": "yes" if ("ADULT" in ages and "CHILD" in ages) else "no",
                     "exclusion_reason": reason, "withdrawn": "yes" if withdrawn else "no",
                     "primary_cohort": "yes" if (not reason and not withdrawn) else "no",
                     "translational_subset": "yes" if translational else "no",
                     "gbm_population": a["gbm_population"], "cns5_terminology": a["cns5_terminology"],
                     "treatment_setting": a["treatment_setting"],
                     "candidate_matched_selection": a["candidate_matched_selection"],
                     "imaging_assessed_selection": a["imaging_assessed_selection"],
                     "any_molecular_selection": a["any_molecular_selection"],
                     "origin_primary_group": g.get("primary_group", ""),
                     "repurposing_2a_containing": g.get("repurposing_2a_containing", ""),
                     "mixed_origin": g.get("mixed_origin", "")})
    with open(out_s, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    cohort = [r for r in rows if r["primary_cohort"] == "yes"]
    with open(out_c, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(cohort)

    # Figure 1 flow: first failed step, in order
    order = ["not_interventional", "start_outside_window", "phase0_early_phase1", "phase4", "phase_not_applicable",
             "paediatric_only"]
    c = Counter(r["exclusion_reason"] for r in rows)
    print(f"screening records {len(rows)}")
    for k in order:
        print(f"  excluded {k}: {c.get(k, 0)}")
    s5 = {k: v for k, v in c.items() if k and k not in order and k in
          ("not_glioblastoma", "high_grade_glioma_unspecified", "gbm_excluded", "anti_gbm_disease")}
    s6 = {k: v for k, v in c.items() if k and k not in order and k not in s5}
    print(f"  excluded S5 (population): {s5}")
    print(f"  excluded S6 (candidate): {s6}")
    passed = [r for r in rows if not r["exclusion_reason"]]
    print(f"pass S1-S6: {len(passed)}; withdrawn among them (S7, reported separately): "
          f"{sum(r['withdrawn'] == 'yes' for r in passed)}")
    print(f"PRIMARY COHORT: {len(cohort)}; translational subset (Early Phase 1): "
          f"{sum(r['translational_subset'] == 'yes' for r in rows)}")
    print("origin groups in cohort:", dict(Counter(r["origin_primary_group"] for r in cohort)))
    pos = sum(r["candidate_matched_selection"] in ("True", "true") for r in cohort)
    print(f"candidate-matched selection in cohort: {pos} ({pos / len(cohort):.1%})")


if __name__ == "__main__":
    main()
