"""
Step 18b - Table 2 corrected (D43). Post-registration processing step; reads only. Supersedes
outputs/analysis_D40/table2_trial_characteristics.csv (kept unchanged for the audit trail).

Corrections after the reproducibility audit of commit 453f1d3:
  - control arm (manual section 2): yes if any registered arm is ACTIVE_COMPARATOR, PLACEBO_COMPARATOR,
    SHAM_COMPARATOR or NO_INTERVENTION, OR the coded control_arm_from_other_arms is yes. Script 18 used only the
    coded supplement.
  - enrolment: anticipated (ESTIMATED) and actual counts reported separately, as the Methods state.
  - labels: the manual's repositioning_only group (category-3 candidates and no category-2 candidate) may also
    contain category-1 candidates (2 trials), so it is labelled "repositioning, no repurposed candidate";
    "molecularly informed design" is labelled as a proxy (adjudicated selection, or a stratification biomarker
    listed by both coders, not necessarily the same one).
All other rows are computed as in script 18 and must reproduce its values (checked below).
Output: outputs/analysis_D40/table2_trial_characteristics_D43.csv (refuses to overwrite)
Usage : python3 scripts/18b_table2_D43.py
"""
import csv
import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("d", ROOT / "scripts" / "18_descriptives.py")
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
A = D.A
COMPARATOR = {"ACTIVE_COMPARATOR", "PLACEBO_COMPARATOR", "SHAM_COMPARATOR", "NO_INTERVENTION"}
OLD = ROOT / "outputs" / "analysis_D40" / "table2_trial_characteristics.csv"


def main():
    T = A.load()
    snap = D.snapshot()
    adj = {r["nct_id"]: r for r in csv.DictReader(open(D.RUN / "adjudicated_trials_D32.csv"))}
    G = lambda t: A.group(t["cands"])
    coh = [t for t in T if t["in_cohort"]]
    for t in coh:
        ps, a = snap[t["nct_id"]], adj[t["nct_id"]]
        sc = ps.get("sponsorCollaboratorsModule", {})
        t["industry_lead"] = sc.get("leadSponsor", {}).get("class") == "INDUSTRY"
        t["industry_any"] = t["industry_lead"] or any(c.get("class") == "INDUSTRY" for c in sc.get("collaborators", []) or [])
        di = ps.get("designModule", {})
        t["randomised"] = (di.get("designInfo") or {}).get("allocation") == "RANDOMIZED"
        t["enrol"] = di.get("enrollmentInfo") or {}
        arms = ps.get("armsInterventionsModule", {}).get("armGroups", []) or []
        t["control_coded"] = D.control_arm(t["nct_id"]) == "yes"
        t["control_arm"] = t["control_coded"] or any(x.get("type") in COMPARATOR for x in arms)
        t["regimen"] = a["regimen"]
        strat = [any(b["role"] == "stratification" for b in json.loads((D.RUN / c / f"{t['nct_id']}.json").read_text())["biomarkers"])
                 for c in ("coderA", "coderB")]
        t["informed"] = a["any_molecular_selection"] in ("True", "true") or all(strat)
        t["pk"], t["te"] = a["tumour_pk_planned"], a["target_engagement_planned"]
    rep = [t for t in coh if G(t) == "repurposing_containing"]
    dn = [t for t in coh if G(t) == "de_novo_only"]
    ro = [t for t in coh if G(t) == "repositioning_only"]
    RO = "repositioning_no_repurposed_candidate"

    def row(label, f):
        x1, x2 = sum(map(f, dn)), sum(map(f, rep))
        d, lo, hi = A.newcombe(x1, len(dn), x2, len(rep))
        return {"characteristic": label, "repurposing_containing": D.pct(x2, len(rep)), "de_novo_only": D.pct(x1, len(dn)),
                RO: D.pct(sum(map(f, ro)), len(ro)), "rd_de_novo_minus_repurposing_pp": f"{100 * d:.1f} ({100 * lo:.1f} to {100 * hi:.1f})"}

    def med(g, typ):
        v = [t["enrol"]["count"] for t in g if t["enrol"].get("type") == typ and t["enrol"].get("count") is not None]
        q = statistics.quantiles(v, n=4)
        return f"{statistics.median(v):.0f} ({q[0]:.0f}-{q[2]:.0f}); n={len(v)}"

    ph = lambda t: A.phase_group(t["phases"])
    t2 = [{"characteristic": "Number of trials", "repurposing_containing": len(rep), "de_novo_only": len(dn), RO: len(ro),
           "rd_de_novo_minus_repurposing_pp": ""},
          row("Phase 1", lambda t: ph(t) == "P1"), row("Phase 2 (incl. Phase 1/2)", lambda t: ph(t) == "P2"),
          row("Phase 3 (incl. Phase 2/3)", lambda t: ph(t) == "P3"),
          row("Industry lead sponsor", lambda t: t["industry_lead"]), row("Any industry involvement", lambda t: t["industry_any"]),
          row("Newly diagnosed setting", lambda t: t["setting"] == "newly_diagnosed"),
          row("Recurrent/progressive setting", lambda t: t["setting"] == "recurrent"),
          row("Both/unclear setting", lambda t: t["setting"] in ("both", "unclear")),
          row("Monotherapy", lambda t: t["regimen"] == "monotherapy"), row("Combination regimen", lambda t: t["regimen"] == "combination"),
          row("Randomised design", lambda t: t["randomised"]), row("Control arm present", lambda t: t["control_arm"])]
    for typ, lab in (("ACTUAL", "actual"), ("ESTIMATED", "anticipated")):
        t2.append({"characteristic": f"Enrolment, {lab}, median (IQR)", "repurposing_containing": med(rep, typ),
                   "de_novo_only": med(dn, typ), RO: med(ro, typ), "rd_de_novo_minus_repurposing_pp": ""})
    t2 += [row("Candidate-matched molecular selection", lambda t: t["selected"]),
           row("Molecularly informed design (proxy)", lambda t: t["informed"]),
           row("Tumour PK planned (yes)", lambda t: t["pk"] == "yes"),
           row("Target engagement planned (yes)", lambda t: t["te"] == "yes")]
    # every unchanged row must reproduce script 18
    old = {r["characteristic"]: r for r in csv.DictReader(open(OLD))}
    for r in t2:
        o = old.get(r["characteristic"].replace(" (proxy)", ""))
        if o and r["characteristic"] not in ("Control arm present",):
            assert [str(r["repurposing_containing"]), str(r["de_novo_only"]), str(r[RO]), r["rd_de_novo_minus_repurposing_pp"]] == \
                   [o["repurposing_containing"], o["de_novo_only"], o["repositioning_only"], o["rd_de_novo_minus_repurposing_pp"]], r["characteristic"]
    A.write("table2_trial_characteristics_D43.csv", t2)
    added = [t["nct_id"] for t in coh if t["control_arm"] and not t["control_coded"]]
    print(f"control arm: rep {sum(t['control_arm'] for t in rep)}/{len(rep)}, de novo {sum(t['control_arm'] for t in dn)}/{len(dn)}, "
          f"{RO} {sum(t['control_arm'] for t in ro)}/{len(ro)}; added by structured arm types: {len(added)}")
    for r in t2:
        if r["characteristic"].startswith(("Control", "Enrolment")):
            print(r)


if __name__ == "__main__":
    main()
