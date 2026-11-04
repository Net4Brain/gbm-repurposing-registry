"""
Step 18 - Descriptive tables for the manuscript (Table 1, Table 2, pipeline composition, phase, mechanism,
translational indicators, translational subset). Post-registration processing step; reads only.

Groups and categories follow scripts/17_analysis.py (D36, D40). Structured fields (phase, lead sponsor and collaborator
class, allocation, enrolment) come from the frozen 2026-11-01 snapshots; coded fields from the adjudicated table.
  - industry lead sponsor: leadSponsor.class == INDUSTRY; any industry involvement: lead or any collaborator INDUSTRY
  - randomised: designInfo.allocation == RANDOMIZED; control arm: control_arm_from_other_arms == yes, from the latest
    proposal item where the trial was adjudicated, else the coders' agreed value (not in the adjudicated table)
  - molecularly informed design: adjudicated any_molecular_selection, or a stratification biomarker row agreed by both
    coders (stratification is not an adjudicated field)
Effect estimates: risk difference (de novo only minus repurposing-containing), Newcombe 95% CI; descriptive.

Outputs (outputs/analysis_D40/, each refused if it exists): table1_repurposing_agents.csv, table2_trial_characteristics.csv,
pipeline_composition.csv, agent_phase_by_origin.csv, mechanism_by_origin.csv, translational_indicators.csv,
translational_subset.csv
Usage: python3 scripts/18_descriptives.py
"""
import csv
import importlib.util
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
spec = importlib.util.spec_from_file_location("a", ROOT / "scripts" / "17_analysis.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
RAW = [ROOT / "data" / "raw" / "ctgov_raw_20261101T130137Z.json", ROOT / "data" / "raw" / "ctgov_supp_raw_20261101T150223Z.json"]
PHASE_RANK = {"PHASE1": 1, "PHASE1/PHASE2": 2, "PHASE2": 2, "PHASE2/PHASE3": 3, "PHASE3": 3}


def snapshot():
    out = {}
    for p in RAW:
        d = json.loads(p.read_text())
        for s in (d["studies"] if isinstance(d, dict) else d):
            ps = s.get("protocolSection", s)
            out.setdefault(ps["identificationModule"]["nctId"], ps)
    return out


def control_arm(n):
    for folder in ("proposals_v3", "proposals_v2", "proposals"):
        p = RUN / folder / f"{n}.json"
        if p.exists():
            for it in json.loads(p.read_text())["items"]:
                if "control_arm_from_other_arms" in str(it.get("item")):
                    return str(it.get("proposed")).strip('"')
            break
    return json.loads((RUN / "coderA" / f"{n}.json").read_text())["trial"]["control_arm_from_other_arms"]


def pct(x, n):
    return f"{x} ({100 * x / n:.1f}%)" if n else "0"


def main():
    T = A.load()
    snap = snapshot()
    adj = {r["nct_id"]: r for r in csv.DictReader(open(RUN / "adjudicated_trials_D32.csv"))}
    mech = {r["active_moiety"]: r["mechanism_primary"] for r in csv.DictReader(open(ROOT / "data" / "reference" / "agent_mechanism.csv"))}
    G = lambda t: A.group(t["cands"])
    coh = [t for t in T if t["in_cohort"]]
    for t in coh + [t for t in T if t["translational"]]:
        ps, a = snap[t["nct_id"]], adj[t["nct_id"]]
        sc = ps.get("sponsorCollaboratorsModule", {})
        t["industry_lead"] = sc.get("leadSponsor", {}).get("class") == "INDUSTRY"
        t["industry_any"] = t["industry_lead"] or any(c.get("class") == "INDUSTRY" for c in sc.get("collaborators", []) or [])
        di = ps.get("designModule", {})
        t["randomised"] = (di.get("designInfo") or {}).get("allocation") == "RANDOMIZED"
        t["enrolment"] = (di.get("enrollmentInfo") or {}).get("count")
        t["control_arm"] = control_arm(t["nct_id"]) == "yes"
        t["regimen"] = a["regimen"]
        t["any_molecular"] = a["any_molecular_selection"] in ("True", "true")
        strat = []
        for c in ("coderA", "coderB"):
            j = json.loads((RUN / c / f"{t['nct_id']}.json").read_text())
            strat.append(any(b["role"] == "stratification" for b in j["biomarkers"]))
        t["informed"] = t["any_molecular"] or all(strat)
        t["pk"] = a["tumour_pk_planned"]
        t["te"] = a["target_engagement_planned"]
    rep = [t for t in coh if G(t) == "repurposing_containing"]
    dn = [t for t in coh if G(t) == "de_novo_only"]
    ro = [t for t in coh if G(t) == "repositioning_only"]

    def row(label, f):
        r = {"characteristic": label, "repurposing_containing": pct(sum(map(f, rep)), len(rep)),
             "de_novo_only": pct(sum(map(f, dn)), len(dn)), "repositioning_only": pct(sum(map(f, ro)), len(ro))}
        x1, x2 = sum(map(f, dn)), sum(map(f, rep))
        d, lo, hi = A.newcombe(x1, len(dn), x2, len(rep))
        r["rd_de_novo_minus_repurposing_pp"] = f"{100 * d:.1f} ({100 * lo:.1f} to {100 * hi:.1f})"
        return r

    ph = lambda t: A.phase_group(t["phases"])
    t2 = [{"characteristic": "Number of trials", "repurposing_containing": len(rep), "de_novo_only": len(dn),
           "repositioning_only": len(ro), "rd_de_novo_minus_repurposing_pp": ""},
          row("Phase 1", lambda t: ph(t) == "P1"), row("Phase 2 (incl. Phase 1/2)", lambda t: ph(t) == "P2"),
          row("Phase 3 (incl. Phase 2/3)", lambda t: ph(t) == "P3"),
          row("Industry lead sponsor", lambda t: t["industry_lead"]), row("Any industry involvement", lambda t: t["industry_any"]),
          row("Newly diagnosed setting", lambda t: t["setting"] == "newly_diagnosed"),
          row("Recurrent/progressive setting", lambda t: t["setting"] == "recurrent"),
          row("Both/unclear setting", lambda t: t["setting"] in ("both", "unclear")),
          row("Monotherapy", lambda t: t["regimen"] == "monotherapy"), row("Combination regimen", lambda t: t["regimen"] == "combination"),
          row("Randomised design", lambda t: t["randomised"]), row("Control arm present", lambda t: t["control_arm"])]
    med = lambda g: (lambda v: f"{statistics.median(v):.0f} ({statistics.quantiles(v, n=4)[0]:.0f}-{statistics.quantiles(v, n=4)[2]:.0f})")(
        [t["enrolment"] for t in g if t["enrolment"] is not None])
    t2.append({"characteristic": "Enrolment, median (IQR)", "repurposing_containing": med(rep), "de_novo_only": med(dn),
               "repositioning_only": med(ro), "rd_de_novo_minus_repurposing_pp": ""})
    t2 += [row("Candidate-matched molecular selection", lambda t: t["selected"]),
           row("Molecularly informed design", lambda t: t["informed"]),
           row("Tumour PK planned (yes)", lambda t: t["pk"] == "yes"),
           row("Target engagement planned (yes)", lambda t: t["te"] == "yes")]
    A.write("table2_trial_characteristics.csv", t2)

    # agent level (same units as the descriptive aim)
    first, trials_of, phase_of, sel_of = {}, defaultdict(set), defaultdict(int), defaultdict(bool)
    for t in coh:
        for c in t["cands"]:
            if c["origin_trial_start"] in ("UNIDENTIFIED", "2_panel"):
                continue
            m = c["moiety"]
            if m not in first or c["trial_start"] < first[m]["trial_start"]:
                first[m] = c
            trials_of[m].add(t["nct_id"])
            phase_of[m] = max(phase_of[m], PHASE_RANK.get(t["phases"], 0))
            sel_of[m] |= t["selected"]
    cat = {m: c["origin_trial_start"] for m, c in first.items()}
    regs = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "data" / "reference" / "regulatory_events.csv")):
        regs[r["moiety"]].append(r)
    t1 = []
    for m in sorted(m for m in cat if cat[m] in ("2a", "2b")):
        ev = sorted(regs.get(m, regs.get(first[m]["active_moiety"], [])), key=lambda r: r["date_lo"])
        e0 = ev[0] if ev else {}
        t1.append({"candidate": m, "subcategory": cat[m], "first_fda_ema_approval": f"{e0.get('jurisdiction', '')} {e0.get('date_lo', '')}".strip(),
                   "first_approved_indication": (e0.get("indication") or "")[:90],
                   "tumour_agnostic_at_T": "yes" if "tumour_agnostic_at_T" in first[m]["flags"] else "",
                   "mechanism": mech.get(first[m]["active_moiety"], ""), "cohort_trials": len(trials_of[m]),
                   "in_candidate_matched_trial": "yes" if sel_of[m] else "no"})
    A.write("table1_repurposing_agents.csv", t1)
    comp = Counter(cat.values())
    n = len(cat)
    A.write("pipeline_composition.csv", [{"category": k, "agents": v, "pct": round(100 * v / n, 1),
                                          "wilson_95ci": "{:.1f} to {:.1f}".format(*(100 * x for x in A.wilson(v, n)))}
                                         for k, v in sorted(comp.items())] + [{"category": "total", "agents": n, "pct": 100, "wilson_95ci": ""}])
    A.write("agent_phase_by_origin.csv", [{"origin": k, **{f"highest_{p}": sum(1 for m in cat if cat[m] == k and phase_of[m] == r)
                                                           for p, r in (("P1", 1), ("P2", 2), ("P3", 3))},
                                           "agents_in_candidate_matched_trial": sum(1 for m in cat if cat[m] == k and sel_of[m])}
                                          for k in sorted(comp)])
    mrows = defaultdict(Counter)
    for m, k in cat.items():
        mrows[mech.get(first[m]["active_moiety"], "unknown")][k] += 1
    A.write("mechanism_by_origin.csv", [{"mechanism": me, **{k: c.get(k, 0) for k in ("1", "3", "2a", "2b")}, "total": sum(c.values())}
                                        for me, c in sorted(mrows.items())])
    A.write("translational_indicators.csv", [
        {"indicator": f"{lab} = {v}", "repurposing_containing": pct(sum(t[k] == v for t in rep), len(rep)),
         "de_novo_only": pct(sum(t[k] == v for t in dn), len(dn)), "repositioning_only": pct(sum(t[k] == v for t in ro), len(ro))}
        for lab, k in (("tumour_pk_planned", "pk"), ("target_engagement_planned", "te")) for v in ("yes", "no", "unclear")])
    tr = [t for t in T if t["translational"]]
    tg = Counter(G(t) for t in tr)
    A.write("translational_subset.csv", [{"origin_group": g, "trials": k, "candidate_matched": sum(t["selected"] for t in tr if G(t) == g),
                                          "tumour_pk_yes": sum(t["pk"] == "yes" for t in tr if G(t) == g),
                                          "target_engagement_yes": sum(t["te"] == "yes" for t in tr if G(t) == g)} for g, k in sorted(tg.items())])
    for r in t2:
        print(f"{r['characteristic'][:38]:38} rep {r['repurposing_containing']:>12} dn {r['de_novo_only']:>12} ro {r['repositioning_only']:>12}  {r['rd_de_novo_minus_repurposing_pp']}")
    print("composition", dict(comp), "| table1 rows", len(t1), "| translational", dict(tg))


if __name__ == "__main__":
    main()
