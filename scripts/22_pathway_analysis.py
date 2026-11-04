"""
Step 22 - Pathway analysis of the repurposed candidates (D42; exploratory, descriptive). Post-registration step.

Inputs : data/reference/agent_pathway_D42.csv (frozen, XL-confirmed), data/reference/agent_pathway_trial_D42.csv
         (trial-level override), outputs/main/pathway_pairs_D42.csv (script 22a: drug-trial pairs with drug-matched
         and co-candidate-only selection from the D33 pairs)
Rules  : prompts/pathway_coding_rules_D42.md section 8.
  - a pair takes the trial override if one exists, else the drug default
  - unique drugs: by the drug default; distinct trials: a trial counts once per pathway however many of its drugs map there
  - drug-matched trials: trials with at least one drug-matched pair on that pathway; co-candidate only: trials whose
    pairs on that pathway are all unmatched but at least one has selection matched to another candidate
  - "any" counts use primary plus secondary pathways
  - sensitivities: excluding the tailored-therapy trial where a molecular tumour board assigns drugs by genotype
    (NCT04591431, 22 repurposed drugs; the regimen-once check of section 8), and excluding `unclear` and
    low-confidence drugs
No P values or confidence intervals.
Origin: each drug's 2a/2b subcategory is its category at its earliest cohort trial (the agent-level rule, D12), and
the drug list is the 92 agents that are repurposed at that trial. So 140 of the 143 repurposing-containing trials
contribute: NCT05743595 and NCT06160206 are repurposing-containing only through retifanlimab (category 3 at its
earliest trial, 2b later), and NCT05857969 only through an unspecified approved-drug panel (D36). Eflornithine
counts as 2a although it is 2b in NCT07468136. scripts/22d_pathway_trial_origin_D42.py repeats the counts with
origin judged per trial (sensitivity check).
Outputs (outputs/analysis_D40/, each refused if it exists): pathway_supplementary_table_D42.csv,
pathway_by_process_D42.csv, pathway_by_level2_D42.csv
Usage: python3 scripts/22_pathway_analysis.py
"""
import csv
import importlib.util
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "reference"
spec = importlib.util.spec_from_file_location("a", ROOT / "scripts" / "17_analysis.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
TAILORED = {"NCT04591431"}
SCOPES = (("2a", {"2a"}), ("2b", {"2b"}), ("all", {"2a", "2b"}))


def load():
    drugs = {r["active_moiety"]: r for r in csv.DictReader(open(REF / "agent_pathway_D42.csv"))}
    over = {(r["active_moiety"], r["nct_id"]): r for r in csv.DictReader(open(REF / "agent_pathway_trial_D42.csv"))}
    pairs = list(csv.DictReader(open(ROOT / "outputs" / "main" / "pathway_pairs_D42.csv")))
    assert {p["active_moiety"] for p in pairs} == set(drugs)
    for p in pairs:
        d, o = drugs[p["active_moiety"]], over.get((p["active_moiety"], p["nct_id"]))
        p["pathway"] = o["pathway_primary"] if o else d["pathway_primary"]
        p["process"] = o["process_primary"] if o else d["process_primary"]
        sec = [s for s in d["pathway_secondary"].split("; ") if s]
        p["any_pathways"] = {p["pathway"], *sec}
    return drugs, pairs


def proc_of(drugs):
    """Level-2 -> level-1 map from the rules vocabulary (section 5), plus pathways added during coding."""
    m = {}
    for line in open(ROOT / "prompts" / "pathway_coding_rules_D42.md"):
        hit = re.match(r"\| \*\*(P\d+ [^*]+)\*\* \| (.+) \|$", line.strip())
        if hit:
            for l2 in hit.group(2).split("; "):
                m[l2.strip()] = hit.group(1)
    for d in drugs.values():
        m.setdefault(d["pathway_primary"], d["process_primary"])
    missing = {s for d in drugs.values() for s in d["pathway_secondary"].split("; ") if s and s not in m}
    assert not missing, missing
    return m


def tabulate(drugs, pairs, level, analysis, keep_pair=lambda p: True, keep_drug=lambda d: True):
    l2proc = proc_of(drugs)
    key = (lambda p: p["process"]) if level == "process" else (lambda p: p["pathway"])
    anykeys = (lambda p: {l2proc.get(x, "unclear") for x in p["any_pathways"]}) if level == "process" else (lambda p: p["any_pathways"])
    rows = []
    for scope, cats in SCOPES:
        P = [p for p in pairs if p["subcategory"] in cats and keep_pair(p) and keep_drug(drugs[p["active_moiety"]])]
        by = defaultdict(list)
        for p in P:
            by[key(p)].append(p)
        anyd, anyt = defaultdict(set), defaultdict(set)
        for p in P:
            for k in anykeys(p):
                anyd[k].add(p["active_moiety"])
                anyt[k].add(p["nct_id"])
        for k in sorted(set(by) | set(anyd)):
            ps = by.get(k, [])
            trials = {p["nct_id"] for p in ps}
            matched = {p["nct_id"] for p in ps if p["drug_matched_selection"] == "yes"}
            co = {p["nct_id"] for p in ps if p["selection_for_co_candidate"] == "yes"} - matched
            rows.append({"analysis": analysis, "scope": scope, level: k,
                         "unique_drugs": len({p["active_moiety"] for p in ps}), "distinct_trials": len(trials),
                         "trials_drug_matched_selection": len(matched),
                         "pct_trials_drug_matched": round(100 * len(matched) / len(trials), 1) if trials else "",
                         "trials_co_candidate_selection_only": len(co),
                         "unique_drugs_any": len(anyd[k]), "distinct_trials_any": len(anyt[k]),
                         "drugs": "; ".join(sorted({p["active_moiety"] for p in ps}))})
    return rows


def main():
    drugs, pairs = load()
    by_drug = defaultdict(list)
    for p in pairs:
        by_drug[p["active_moiety"]].append(p)
    supp = []
    for m in sorted(drugs, key=lambda m: (drugs[m]["subcategory"], drugs[m]["process_primary"], m)):
        d, ps = drugs[m], by_drug[m]
        supp.append({"candidate": m, "subcategory": d["subcategory"], "target": d["target"],
                     "proposed_gbm_mechanism": d["proposed_gbm_mechanism"], "process_primary": d["process_primary"],
                     "pathway_primary": d["pathway_primary"], "pathway_secondary": d["pathway_secondary"],
                     "source_type": d["source_type"], "source": d["source"], "confidence": d["confidence"],
                     "trials": "; ".join(sorted(p["nct_id"] for p in ps)),
                     "trial_level_pathway": "; ".join(f"{p['nct_id']}: {p['pathway']}" for p in ps if p["pathway"] != d["pathway_primary"]),
                     "drug_matched_selection_trials": "; ".join(f"{p['nct_id']} ({p['matched_biomarkers']})" for p in ps
                                                               if p["drug_matched_selection"] == "yes"),
                     "co_candidate_selection_only_trials": "; ".join(p["nct_id"] for p in ps if p["selection_for_co_candidate"] == "yes")})
    A.write("pathway_supplementary_table_D42.csv", supp)
    variants = [("main", lambda p: True, lambda d: True),
                ("excluding tailored-therapy trial NCT04591431", lambda p: p["nct_id"] not in TAILORED, lambda d: True),
                ("excluding unclear and low-confidence drugs", lambda p: True,
                 lambda d: d["pathway_primary"] != "unclear" and d["confidence"] != "low")]
    proc_rows = [r for name, kp, kd in variants for r in tabulate(drugs, pairs, "process", name, kp, kd)]
    A.write("pathway_by_process_D42.csv", proc_rows)
    A.write("pathway_by_level2_D42.csv", [r for name, kp, kd in variants[:2] for r in tabulate(drugs, pairs, "pathway", name, kp, kd)])
    trials = {p["nct_id"] for p in pairs}
    print(f"drugs {len(drugs)}; pairs {len(pairs)}; trials {len(trials)}; drug-matched trials "
          f"{len({p['nct_id'] for p in pairs if p['drug_matched_selection'] == 'yes'})}")
    print(f"{'process':52} {'2a d/t/m':>10} {'2b d/t/m':>10} {'all d/t/m':>11}   all excl. tailored")
    main_rows = {(r["scope"], r["process"]): r for r in proc_rows if r["analysis"] == "main"}
    exc = {(r["scope"], r["process"]): r for r in proc_rows if r["analysis"].startswith("excluding tailored")}
    f = lambda r: f"{r['unique_drugs']}/{r['distinct_trials']}/{r['trials_drug_matched_selection']}" if r else "-"
    for k in sorted({k for _, k in main_rows}, key=lambda k: (int(k.split()[0][1:]) if k[0] == "P" else 99)):
        print(f"{k:52} {f(main_rows.get(('2a', k))):>10} {f(main_rows.get(('2b', k))):>10} {f(main_rows.get(('all', k))):>11}   {f(exc.get(('all', k)))}")


if __name__ == "__main__":
    main()
