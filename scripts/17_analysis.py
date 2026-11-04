"""
Step 17 - H1 and descriptive analyses (OSF registration osf.io/gn8v5; D22, D25, D30-R2, D36). Post-registration
processing step.

H1: repurposing-containing trials use candidate-matched molecular selection less often than de novo-only trials.
Estimand: trial-level risk difference, de novo only minus repurposing-containing, one row per trial, with a Newcombe
(hybrid Wilson score) 95% CI; whether the CI excludes 0 and whether it excludes 10 percentage points (D22).

Trial-origin groups (manual v1.4 section 4.3; D36), from each trial's candidates' categories at the trial start:
  repurposing_containing = at least one category-2 candidate (2a, 2b, unspecified panel)
  de_novo_only           = only category-1 candidates
  repositioning_only     = category-3 candidates and no category 2 (in neither H1 group; descriptive)
  UNIDENTIFIED agents (D36): an identified category-2 candidate gives repurposing_containing; otherwise the trial is
  unresolved_non_repurposing, excluded from the contrast (de novo only in sensitivity analysis 16)
Outcome: candidate_matched_selection (adjudicated; every positive trial has an XL-confirmed pair, D33).

Analyses (registration "H1 analyses" 1-7 and sensitivity analyses 1-14; 15-16 added by D30-R2 and D36):
  H1-1 primary crude risk difference              H1-2 selection by primary mechanism x origin  [needs mechanism]
  H1-3 composition-standardised risk difference over phase group, setting, calendar period [+ mechanism when coded]
  H1-4 candidate-specific selection (pair matched to the repurposed candidate, XL D21 decisions)
  H1-5 single-candidate trials                    H1-6 leave-one-dominant-agent-out (top 5 agents)
  H1-7 exposure = repurposing_2a_containing
  SA1-SA16 as listed in SENSITIVITY below; SA7 applies to the agent-level descriptive aim.
Descriptive aim: share of unique candidate agents that are approved-drug repurposing (2a/2b), with the dated
tumour-agnostic flag; reported as definition-dependent if it moves > 5 points across sensitivity analyses.

Inputs : outputs/main/cohort_D37.csv, screening_D37.csv, adjudicated_trials_D32.csv, origin_derived_D36.csv,
         d21_match_decisions_XL.csv, coderA/*.json (regimen_id); data/reference/unidentified_agents.csv
Outputs: outputs/analysis_D40/*.csv (each file refused if it exists)
Usage: python3 scripts/17_analysis.py               (all analyses that do not need mechanism)
       python3 scripts/17_analysis.py --mechanism   (H1-2 and H1-3 with mechanism; needs data/reference/agent_mechanism.csv)
"""
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
OUT = ROOT / "outputs" / "analysis_D40"
Z = 1.959963984540054
CAT2 = {"2a", "2b", "2_panel"}
ALIAS = {"star-001": "lp-184", "incmga00012": "retifanlimab"}   # same moiety counted once (D35)
IMAGING = re.compile(r"PET|SPECT|uptake|imaging", re.I)


# ------------------------------------------------------------------ statistics
def wilson(x, n):
    if n == 0:
        return (float("nan"), float("nan"))
    p = x / n
    d = 1 + Z * Z / n
    c = p + Z * Z / (2 * n)
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def newcombe(x1, n1, x2, n2):
    """Newcombe hybrid score CI (method 10) for p1 - p2."""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1)
    l2, u2 = wilson(x2, n2)
    d = p1 - p2
    return d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def summary(label, ref, exp, sel, note=""):
    x1, n1 = sum(sel(t) for t in ref), len(ref)
    x2, n2 = sum(sel(t) for t in exp), len(exp)
    row = {"analysis": label, "de_novo_selected": x1, "de_novo_n": n1, "repurposing_selected": x2, "repurposing_n": n2,
           "de_novo_pct": "", "repurposing_pct": "", "risk_difference_pp": "", "ci_low_pp": "", "ci_high_pp": "",
           "ci_excludes_0": "", "ci_excludes_10": "", "note": note}
    if n1 and n2:
        d, lo, hi = newcombe(x1, n1, x2, n2)
        row.update(de_novo_pct=round(100 * x1 / n1, 1), repurposing_pct=round(100 * x2 / n2, 1),
                   risk_difference_pp=round(100 * d, 1), ci_low_pp=round(100 * lo, 1), ci_high_pp=round(100 * hi, 1),
                   ci_excludes_0="yes" if (lo > 0 or hi < 0) else "no",
                   ci_excludes_10="yes" if (hi < 0.10 or lo > 0.10) else "no")
    return row


# ------------------------------------------------------------------ data
def load():
    cohort = {r["nct_id"]: r for r in csv.DictReader(open(RUN / "cohort_D37.csv"))}
    screen = {r["nct_id"]: r for r in csv.DictReader(open(RUN / "screening_D37.csv"))}
    adj = {r["nct_id"]: r for r in csv.DictReader(open(RUN / "adjudicated_trials_D32.csv"))}
    unid = {(r["nct_id"], r["active_moiety"]): r["certain_not_fda_ema_approved_at_trial_start"] == "yes"
            for r in csv.DictReader(open(ROOT / "data" / "reference" / "unidentified_agents.csv"))}
    cands = defaultdict(list)
    for r in csv.DictReader(open(RUN / "origin_derived_D36.csv")):
        r["moiety"] = ALIAS.get(r["active_moiety"], r["active_moiety"])
        r["unid_certain_unapproved"] = unid.get((r["nct_id"], r["active_moiety"]))
        cands[r["nct_id"]].append(r)
    pairs = defaultdict(list)
    for r in csv.DictReader(open(RUN / "d21_match_decisions_XL.csv")):
        if r["XL_decision"] == "yes":
            pairs[r["nct_id"]].append(r)
    trials = []
    for n, s in screen.items():
        a = adj[n]
        t = {"nct_id": n, "in_cohort": n in cohort, "translational": s["translational_subset"] == "yes",
             "phases": s["phases"], "start": s["start_date"], "start_type": s["start_type"],
             "gbm_population": a["gbm_population"], "cns5": a["cns5_terminology"], "setting": a["treatment_setting"],
             "basket": a["basket"] in ("True", "true"), "selected": a["candidate_matched_selection"] in ("True", "true"),
             "imaging": a["imaging_assessed_selection"] in ("True", "true"), "cands": cands.get(n, []),
             "pairs": pairs.get(n, [])}
        trials.append(t)
    return trials


def group(cands, key="origin_trial_start", drop=lambda c: False):
    cs = [c for c in cands if not drop(c)]
    cats = [c[key] for c in cs]
    ident = [c for c in cats if c != "UNIDENTIFIED"]
    if any(c in CAT2 for c in ident):
        return "repurposing_containing"
    if "UNIDENTIFIED" in cats:
        unsure = [c for c in cs if c[key] == "UNIDENTIFIED" and not c["unid_certain_unapproved"]]
        return "unresolved" if unsure else "unresolved_non_repurposing"
    if ident and all(c == "1" for c in ident):
        return "de_novo_only"
    if ident and all(c in ("1", "3") for c in ident):
        return "repositioning_only"
    return "other"


def phase_group(p):
    return {"PHASE1": "P1", "PHASE1/PHASE2": "P2", "PHASE2": "P2", "PHASE2/PHASE3": "P3", "PHASE3": "P3"}.get(p, "other")


def period(start):
    y = int(start[:4])
    return "2020-22" if y <= 2022 else ("2023-24" if y <= 2024 else "2025-26")


# ------------------------------------------------------------------ analyses
def h1(trials, label, pop=lambda t: t["in_cohort"], grp=lambda t: group(t["cands"]), sel=lambda t: t["selected"],
       exposed=("repurposing_containing",), reference=("de_novo_only",), note=""):
    ts = [t for t in trials if pop(t)]
    ref = [t for t in ts if grp(t) in reference]
    exp = [t for t in ts if grp(t) in exposed]
    return summary(label, ref, exp, sel, note)


def standardised(trials, strata_keys):
    """Composition-standardised RD: stratum-specific differences weighted by the total stratum size, over strata with
    both groups present; sparse or one-sided strata are reported, not modelled."""
    ts = [t for t in trials if t["in_cohort"] and group(t["cands"]) in ("de_novo_only", "repurposing_containing")]
    strata = defaultdict(lambda: {"de_novo_only": [], "repurposing_containing": []})
    for t in ts:
        strata[tuple(k(t) for k in strata_keys)][group(t["cands"])].append(t)
    used, dropped, num, wsum, var = [], [], 0.0, 0, 0.0
    for k, g in sorted(strata.items()):
        a, b = g["de_novo_only"], g["repurposing_containing"]
        if a and b:
            pa, pb = sum(t["selected"] for t in a) / len(a), sum(t["selected"] for t in b) / len(b)
            w = len(a) + len(b)
            num += w * (pa - pb)
            wsum += w
            var += w * w * (pa * (1 - pa) / len(a) + pb * (1 - pb) / len(b))
            used.append((k, len(a), len(b)))
        else:
            dropped.append((k, len(a), len(b)))
    d = num / wsum
    se = math.sqrt(var) / wsum
    return d, d - Z * se, d + Z * se, used, dropped


def specific_selected(t):
    """H1-4: a repurposing-containing trial counts as selected only if an XL-confirmed pair is matched to one of its
    category-2 candidates."""
    if group(t["cands"]) != "repurposing_containing":
        return t["selected"]
    rep = {c["active_moiety"] for c in t["cands"] if c["origin_trial_start"] in CAT2}
    return any(any(m.strip() in rep for m in p["matched_candidate"].split(";")) for p in t["pairs"])


def nonimaging_selected(t):
    """SA15: selection only through pairs that are not imaging-assessed."""
    return any(not IMAGING.search(p["biomarker"]) for p in t["pairs"])


def write(name, rows):
    p = OUT / name
    if p.exists():
        sys.exit(f"{p} exists; refusing to overwrite")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def agent_level(trials, label, pop=lambda t: t["in_cohort"], key="origin_trial_start", regimen_once=False):
    """Descriptive aim: unique candidate agents (UNIDENTIFIED and unspecified panels excluded), origin at the agent's
    earliest trial (D12)."""
    reg = {}
    if regimen_once:
        for t in trials:
            if not pop(t):
                continue
            j = json.loads((RUN / "coderA" / f"{t['nct_id']}.json").read_text())
            ids = defaultdict(list)
            for a in j["agents"]:
                if a.get("regimen_id"):
                    ids[a["regimen_id"]].append(a["active_moiety"].lower())
            for rid, ms in ids.items():
                c2 = [c["moiety"] for c in t["cands"] if c["active_moiety"] in ms and c[key] in CAT2]
                if len(c2) >= 2:
                    for m in c2:
                        reg[(t["nct_id"], m)] = f"regimen:{t['nct_id']}:{rid}"
    # a member moiety is folded into its regimen only if it never appears outside a multi-drug regimen
    outside = {c["moiety"] for t in trials if pop(t) for c in t["cands"] if (t["nct_id"], c["moiety"]) not in reg}
    first = {}
    for t in trials:
        if not pop(t):
            continue
        for c in t["cands"]:
            if c[key] in ("UNIDENTIFIED", "2_panel"):
                continue
            unit = c["moiety"] if c["moiety"] in outside else reg.get((t["nct_id"], c["moiety"]), c["moiety"])
            if unit not in first or c["trial_start"] < first[unit]["trial_start"]:
                first[unit] = c
    cats = Counter(c[key] for c in first.values())
    n = len(first)
    c2 = cats["2a"] + cats["2b"]
    agn = sum(1 for c in first.values() if c[key] in CAT2 and "tumour_agnostic_at_T" in c["flags"])
    lo, hi = wilson(c2, n)
    return {"analysis": label, "agents": n, "repurposing_2": c2, "pct_2": round(100 * c2 / n, 1),
            "ci_2": f"{100 * lo:.1f} to {100 * hi:.1f}", "n_2a": cats["2a"], "n_2b": cats["2b"], "n_3": cats["3"],
            "n_1": cats["1"], "tumour_agnostic_flagged": agn}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    T = load()
    coh = [t for t in T if t["in_cohort"]]
    assert len(coh) == 280, len(coh)
    G = lambda t: group(t["cands"])
    res = [h1(T, "H1-1 primary (crude, one row per trial)")]

    d, lo, hi, used, dropped = standardised(T, [lambda t: phase_group(t["phases"]), lambda t: t["setting"],
                                                lambda t: period(t["start"])])
    res.append({**summary("H1-3 composition-standardised (phase group, setting, period)",
                          [], [], lambda t: 0), "risk_difference_pp": round(100 * d, 1), "ci_low_pp": round(100 * lo, 1),
                "ci_high_pp": round(100 * hi, 1), "ci_excludes_0": "yes" if (lo > 0 or hi < 0) else "no",
                "ci_excludes_10": "yes" if (hi < 0.10 or lo > 0.10) else "no",
                "note": f"{len(used)} strata with both groups ({sum(a + b for _, a, b in used)} trials); "
                        f"{len(dropped)} one-sided strata ({sum(a + b for _, a, b in dropped)} trials) not used; "
                        "Wald CI; mechanism stratum pending mechanism coding"})
    res.append(h1(T, "H1-4 candidate-specific selection", sel=specific_selected,
                  note="repurposing-containing trial selected only if a confirmed pair matches its category-2 candidate"))
    res.append(h1(T, "H1-5 single-candidate trials", pop=lambda t: t["in_cohort"] and len(t["cands"]) == 1))
    top = Counter(c["moiety"] for t in coh for c in {c["moiety"]: c for c in t["cands"]}.values()).most_common(5)
    for m, k in top:
        res.append(h1(T, f"H1-6 leave out trials with {m}",
                      pop=lambda t, m=m: t["in_cohort"] and m not in {c["moiety"] for c in t["cands"]},
                      note=f"{k} cohort trials contain {m}"))
    has2a = lambda t: any(c["origin_trial_start"] == "2a" for c in t["cands"])
    res.append(h1(T, "H1-7 exposure = repurposing_2a_containing", grp=lambda t: "x" if has2a(t) else G(t), exposed=("x",)))

    # sensitivity analyses
    res.append(h1(T, "SA1 categories 2 + 3 combined", exposed=("repurposing_containing", "repositioning_only")))
    res.append(h1(T, "SA2 2a only, excluding agents with tumour_agnostic_at_T",
                  grp=lambda t: "x" if any(c["origin_trial_start"] == "2a" and "tumour_agnostic_at_T" not in c["flags"]
                                           for c in t["cands"]) else G(t), exposed=("x",)))
    res.append(h1(T, "SA3 origin judged at the index date (2026-07-31)",
                  grp=lambda t: group(t["cands"], key="origin_index_date")))
    res.append(h1(T, "SA4 glioblastoma-only populations", pop=lambda t: t["in_cohort"] and t["gbm_population"] == "gbm_only"))
    res.append(h1(T, "SA5 exclude basket trials", pop=lambda t: t["in_cohort"] and not t["basket"]))
    mixed = lambda t: G(t) == "repurposing_containing" and any(c["origin_trial_start"] == "1" for c in t["cands"])
    res.append(h1(T, "SA6 exclude mixed-origin trials", pop=lambda t: t["in_cohort"] and not mixed(t)))
    res.append({**summary("SA7 count each multi-drug repurposing regimen once", [], [], lambda t: 0),
                "note": "agent-level descriptive aim only; see agent_level.csv"})
    res.append(h1(T, "SA8 include Early Phase 1 trials", pop=lambda t: t["in_cohort"] or t["translational"]))
    res.append(h1(T, "SA9 actual start dates only", pop=lambda t: t["in_cohort"] and t["start_type"] == "ACTUAL"))
    res.append(h1(T, "SA10 CNS5 terminology only", pop=lambda t: t["in_cohort"] and t["cns5"] == "cns5"))
    devonly = lambda t: t["cands"] and all(c["device_dependent"] in ("True", "true") for c in t["cands"])
    res.append(h1(T, "SA11 exclude trials whose only candidates are device-dependent",
                  pop=lambda t: t["in_cohort"] and not devonly(t)))
    panelonly = lambda t: (any(c["origin_trial_start"] == "2_panel" for c in t["cands"])
                           and not any(c["origin_trial_start"] in ("2a", "2b") for c in t["cands"]))
    res.append(h1(T, "SA12 exclude trials whose only repurposing candidate is an unspecified panel",
                  pop=lambda t: t["in_cohort"] and not panelonly(t)))
    ds = lambda t: any("date_sensitive" in c["flags"] for c in t["cands"])
    res.append(h1(T, "SA13 exclude date-sensitive classifications", pop=lambda t: t["in_cohort"] and not ds(t),
                  note=f"{sum(map(ds, coh))} cohort trials have a date-sensitive candidate"))
    res.append(h1(T, "SA14 exclude candidates with population_within_label",
                  grp=lambda t: group(t["cands"], drop=lambda c: c["population_within_label"] == "yes")))
    res.append(h1(T, "SA15 exclude imaging-assessed selection from the outcome (D30-R2)", sel=nonimaging_selected))
    res.append(h1(T, "SA16 count unresolved_non_repurposing trials as de novo only (D36)",
                  reference=("de_novo_only", "unresolved_non_repurposing")))
    write("h1_and_sensitivity.csv", res)

    groups = Counter(G(t) for t in coh)
    sel_by = defaultdict(lambda: [0, 0])
    for t in coh:
        sel_by[G(t)][0] += t["selected"]
        sel_by[G(t)][1] += 1
    write("selection_by_origin_group_all.csv",
          [{"origin_group": g, "selected": x, "n": n, "pct": round(100 * x / n, 1),
            "wilson_95ci": "{:.1f} to {:.1f}".format(*(100 * v for v in wilson(x, n)))} for g, (x, n) in sorted(sel_by.items())])
    write("h1_3_strata.csv", [{"stratum": " | ".join(k), "de_novo_n": a, "repurposing_n": b, "used": "yes"} for k, a, b in used]
          + [{"stratum": " | ".join(k), "de_novo_n": a, "repurposing_n": b, "used": "no (one-sided)"} for k, a, b in dropped])
    write("h1_6_top_agents.csv", [{"agent": m, "cohort_trials": k} for m, k in top])

    ag = [agent_level(T, "descriptive aim: unique candidate agents, origin at earliest trial"),
          agent_level(T, "SA3 origin at the index date", key="origin_index_date"),
          agent_level(T, "SA7 multi-drug repurposing regimens counted once", regimen_once=True),
          agent_level(T, "SA8 include Early Phase 1 trials", pop=lambda t: t["in_cohort"] or t["translational"]),
          agent_level(T, "SA4 glioblastoma-only populations", pop=lambda t: t["in_cohort"] and t["gbm_population"] == "gbm_only"),
          agent_level(T, "SA5 exclude basket trials", pop=lambda t: t["in_cohort"] and not t["basket"]),
          agent_level(T, "SA9 actual start dates only", pop=lambda t: t["in_cohort"] and t["start_type"] == "ACTUAL"),
          agent_level(T, "SA10 CNS5 terminology only", pop=lambda t: t["in_cohort"] and t["cns5"] == "cns5")]
    base = ag[0]["pct_2"]
    for a in ag:
        a["change_vs_headline_pp"] = round(a["pct_2"] - base, 1)
        a["definition_dependent_gt5"] = "yes" if abs(a["pct_2"] - base) > 5 else "no"
    write("agent_level.csv", ag)

    print(f"cohort {len(coh)}; groups {dict(groups)}")
    for r in res:
        rd = f"{r['risk_difference_pp']} ({r['ci_low_pp']} to {r['ci_high_pp']})" if r["risk_difference_pp"] != "" else "-"
        print(f"{r['analysis'][:72]:72} {r['de_novo_selected']}/{r['de_novo_n']} vs {r['repurposing_selected']}/"
              f"{r['repurposing_n']}  RD {rd}  ex0 {r['ci_excludes_0']} ex10 {r['ci_excludes_10']}")
    for a in ag:
        print(f"{a['analysis'][:60]:60} agents {a['agents']} cat2 {a['repurposing_2']} ({a['pct_2']}%, {a['ci_2']}) "
              f"2a {a['n_2a']} 2b {a['n_2b']} 3 {a['n_3']} 1 {a['n_1']} agnostic {a['tumour_agnostic_flagged']} "
              f"Δ {a['change_vs_headline_pp']}")


def trial_mechanism(t, mech):
    """D40 rule (XL): the mechanism shared by all the trial's candidates; otherwise 'multiple'."""
    ms = {mech.get(c["active_moiety"], "unknown") for c in t["cands"] if c["active_moiety"] != "unspecified_approved_panel"}
    return ms.pop() if len(ms) == 1 else ("multiple" if ms else "not_applicable")


def mechanism_analyses():
    """H1-2 selection by primary mechanism x origin; H1-3 with the mechanism stratum added."""
    mech = {r["active_moiety"]: r["mechanism_primary"]
            for r in csv.DictReader(open(ROOT / "data" / "reference" / "agent_mechanism.csv"))}
    T = load()
    coh = [t for t in T if t["in_cohort"]]
    missing = sorted({c["active_moiety"] for t in coh for c in t["cands"]} - set(mech))
    if missing:
        sys.exit(f"agents without a reviewed mechanism: {missing}")
    G = lambda t: group(t["cands"])
    cells = defaultdict(lambda: [0, 0])
    for t in coh:
        k = (trial_mechanism(t, mech), G(t))
        cells[k][0] += t["selected"]
        cells[k][1] += 1
    rows = []
    for m in sorted({k[0] for k in cells}):
        r = {"primary_mechanism": m}
        for g in ("de_novo_only", "repositioning_only", "repurposing_containing", "unresolved_non_repurposing"):
            x, n = cells.get((m, g), [0, 0])
            r[f"{g}_selected"], r[f"{g}_n"] = x, n
            r[f"{g}_pct"] = round(100 * x / n, 1) if n else ""
        a, b = cells.get((m, "de_novo_only"), [0, 0]), cells.get((m, "repurposing_containing"), [0, 0])
        if a[1] and b[1]:
            d, lo, hi = newcombe(a[0], a[1], b[0], b[1])
            r.update(rd_pp=round(100 * d, 1), ci=f"{100 * lo:.1f} to {100 * hi:.1f}")
        else:
            r.update(rd_pp="", ci="one group absent")
        rows.append(r)
    write("h1_2_mechanism_by_origin.csv", rows)
    keys = [lambda t: phase_group(t["phases"]), lambda t: t["setting"], lambda t: period(t["start"]),
            lambda t: trial_mechanism(t, mech)]
    d, lo, hi, used, dropped = standardised(T, keys)
    write("h1_3_with_mechanism.csv", [{
        "analysis": "H1-3 composition-standardised (phase group, setting, period, primary mechanism)",
        "risk_difference_pp": round(100 * d, 1), "ci_low_pp": round(100 * lo, 1), "ci_high_pp": round(100 * hi, 1),
        "ci_excludes_0": "yes" if (lo > 0 or hi < 0) else "no", "ci_excludes_10": "yes" if (hi < 0.10 or lo > 0.10) else "no",
        "strata_used": len(used), "trials_used": sum(a + b for _, a, b in used), "strata_one_sided": len(dropped),
        "trials_not_used": sum(a + b for _, a, b in dropped), "note": "Wald CI; one-sided strata reported, not modelled"}])
    write("h1_3_with_mechanism_strata.csv",
          [{"stratum": " | ".join(k), "de_novo_n": a, "repurposing_n": b, "used": "yes"} for k, a, b in used]
          + [{"stratum": " | ".join(k), "de_novo_n": a, "repurposing_n": b, "used": "no (one-sided)"} for k, a, b in dropped])
    print("H1-2 selection by primary mechanism x origin:")
    for r in rows:
        print(f"  {r['primary_mechanism']:20} de novo {r['de_novo_only_selected']}/{r['de_novo_only_n']}  "
              f"repositioning {r['repositioning_only_selected']}/{r['repositioning_only_n']}  "
              f"repurposing {r['repurposing_containing_selected']}/{r['repurposing_containing_n']}  RD {r['rd_pp']} ({r['ci']})")
    print(f"H1-3 with mechanism: RD {100 * d:.1f} ({100 * lo:.1f} to {100 * hi:.1f}); strata used {len(used)} "
          f"({sum(a + b for _, a, b in used)} trials), one-sided {len(dropped)} ({sum(a + b for _, a, b in dropped)} trials)")


if __name__ == "__main__":
    mechanism_analyses() if sys.argv[1:] == ["--mechanism"] else main()
