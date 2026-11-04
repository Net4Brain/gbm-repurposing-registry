"""
Step 22d - Pathway analysis, sensitivity check: origin judged per trial (D42 addition, 2026-11-04). Reads only.

The main pathway analysis (script 22) assigns 2a/2b by each drug's category at its earliest cohort trial, the
agent-level rule of D12, and covers only the 92 drugs that are repurposed at agent level. Two drug-trial pairs
behave differently when origin is judged at each trial's own start:
  - eflornithine is 2a at its first trial but 2b in NCT07468136 (after its neuroblastoma approval);
  - retifanlimab is category 3 at its earliest trial but 2b in NCT05743595, NCT06160206 and NCT07468136
    (after its March 2023 FDA approval), so these pairs are outside the main analysis.
Here every cohort candidate whose trial-level origin is 2a or 2b is a pair, with that trial-level subcategory.
Pathways come from the frozen D42 table; retifanlimab, which is not in it, takes its row from
data/reference/agent_pathway_sensitivity_D42.csv. Drug-matched selection is judged as in script 22a; counting is
script 22's.
Output: outputs/analysis_D40/pathway_by_process_trial_origin_D42.csv (refuses to overwrite)
Usage : python3 scripts/22d_pathway_trial_origin_D42.py
"""
import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "reference"


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S = module("s", "22_pathway_analysis.py")
E = module("e", "22a_pathway_evidence.py")
A = S.A


def main():
    drugs, main_pairs = S.load()
    extra = {r["active_moiety"]: r for r in csv.DictReader(open(REF / "agent_pathway_sensitivity_D42.csv"))}
    drugs.update(extra)
    over = {(r["active_moiety"], r["nct_id"]): r for r in csv.DictReader(open(REF / "agent_pathway_trial_D42.csv"))}
    pairs = []
    for t in A.load():
        if not t["in_cohort"]:
            continue
        cand_names = {c["active_moiety"].lower() for c in t["cands"]} | {c["moiety"] for c in t["cands"]}
        for c in t["cands"]:
            m, k = c["moiety"], c["origin_trial_start"]
            if k not in ("2a", "2b"):
                continue
            assert m in drugs, f"{m} has no pathway row"
            own = [p for p in t["pairs"] if E.names(p["matched_candidate"]) & {c["active_moiety"].lower(), m}]
            other = [p for p in t["pairs"] if p not in own and E.names(p["matched_candidate"]) & cand_names]
            d, o = drugs[m], over.get((m, t["nct_id"]))
            pairs.append({"active_moiety": m, "subcategory": k, "nct_id": t["nct_id"],
                          "drug_matched_selection": "yes" if own else "no",
                          "selection_for_co_candidate": "yes" if other and not own else "no",
                          "pathway": o["pathway_primary"] if o else d["pathway_primary"],
                          "process": o["process_primary"] if o else d["process_primary"],
                          "any_pathways": {o["pathway_primary"] if o else d["pathway_primary"],
                                           *[s for s in d["pathway_secondary"].split("; ") if s]}})
    old = {(p["active_moiety"], p["nct_id"]): p for p in main_pairs}
    new = {(p["active_moiety"], p["nct_id"]): p for p in pairs}
    changed = sorted(k for k in new if k not in old or old[k]["subcategory"] != new[k]["subcategory"])
    assert set(old) <= set(new), "a main-analysis pair is missing"
    for k in set(old):
        assert old[k]["drug_matched_selection"] == new[k]["drug_matched_selection"], k
    rows = S.tabulate(drugs, pairs, "process", "trial-level origin (sensitivity)")
    A.write("pathway_by_process_trial_origin_D42.csv", rows)
    print(f"pairs {len(main_pairs)} -> {len(pairs)}; trials {len({p['nct_id'] for p in main_pairs})} -> "
          f"{len({p['nct_id'] for p in pairs})}; pairs new or re-assigned: {changed}")
    base = {(r["scope"], r["process"]): r for r in csv.DictReader(open(S.ROOT / "outputs" / "analysis_D40" / "pathway_by_process_D42.csv"))
            if r["analysis"] == "main"}
    for r in rows:
        b = base.get((r["scope"], r["process"]))
        cur = (r["unique_drugs"], r["distinct_trials"], r["trials_drug_matched_selection"])
        prev = tuple(int(b[x]) for x in ("unique_drugs", "distinct_trials", "trials_drug_matched_selection")) if b else (0, 0, 0)
        if cur != prev:
            print(f"  {r['scope']:3} {r['process']:45} drugs/trials/matched {prev} -> {cur}")


if __name__ == "__main__":
    main()
