"""
Step 22a - Evidence pack for the pathway coding (D42). Post-registration processing step; reads only.

For each of the 92 repurposed candidates (2a/2b at the agent's earliest cohort trial start, as in scripts 17/18):
D40 mechanism class, ChEMBL mechanisms (frozen lookup v1.2), and per trial the coders' drug-class notes and stated
antitumour mechanisms with quotes. For each drug-trial pair: XL-confirmed D33 pairs matched to this drug, or only to a
co-candidate (rules section 7).
Outputs (outputs/main/, each refused if it exists): pathway_evidence_D42.csv (one row per drug),
pathway_pairs_D42.csv (one row per drug-trial pair)
Usage: python3 scripts/22a_pathway_evidence.py
"""
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
spec = importlib.util.spec_from_file_location("a", ROOT / "scripts" / "17_analysis.py")
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
LOOKUP = ROOT / "data" / "lookup" / "v1.2"


def write(name, rows):
    p = RUN / name
    if p.exists():
        sys.exit(f"{p} exists; refusing to overwrite")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def chembl(moiety):
    p = LOOKUP / (re.sub(r"[^a-z0-9]+", "_", moiety.lower()).strip("_") + ".json")
    if not p.exists():
        return ""
    c = json.loads(p.read_text()).get("chembl") or {}
    return "; ".join(sorted({m["mechanism"] for m in c.get("mechanisms") or []}))


def names(s):
    return {A.ALIAS.get(x.strip().lower(), x.strip().lower()) for x in s.split(";") if x.strip()}


def main():
    T = A.load()
    coh = [t for t in T if t["in_cohort"]]
    mech = {r["active_moiety"]: r["mechanism_primary"] for r in csv.DictReader(open(ROOT / "data" / "reference" / "agent_mechanism.csv"))}
    first = {}
    for t in coh:
        for c in t["cands"]:
            if c["origin_trial_start"] in ("UNIDENTIFIED", "2_panel"):
                continue
            if c["moiety"] not in first or c["trial_start"] < first[c["moiety"]]["trial_start"]:
                first[c["moiety"]] = c
    rep = sorted(m for m, c in first.items() if c["origin_trial_start"] in ("2a", "2b"))
    drugs, pairs = {m: {"trials": [], "hints": set(), "stated": []} for m in rep}, []
    for t in coh:
        here = {c["moiety"]: c for c in t["cands"]}
        cand_names = {c["active_moiety"].lower() for c in t["cands"]} | set(here)
        coder = {k: json.loads((RUN / k / f"{t['nct_id']}.json").read_text()) for k in ("coderA", "coderB")}
        for m in sorted(set(here) & set(rep)):
            am = here[m]["active_moiety"].lower()
            d = drugs[m]
            d["trials"].append(t["nct_id"])
            for k, j in coder.items():
                for a in j["agents"]:
                    if a["active_moiety"].lower() in (am, m):
                        if a.get("drug_class_hint"):
                            d["hints"].add(a["drug_class_hint"])
                        if a.get("stated_antitumour_mechanism"):
                            d["stated"].append(f"{t['nct_id']} [{k}] {a['stated_antitumour_mechanism']}")
            own = [p for p in t["pairs"] if names(p["matched_candidate"]) & {am, m}]
            other = [p for p in t["pairs"] if p not in own and names(p["matched_candidate"]) & cand_names]
            pairs.append({"active_moiety": m, "subcategory": first[m]["origin_trial_start"], "nct_id": t["nct_id"],
                          "role": here[m]["role"], "drug_matched_selection": "yes" if own else "no",
                          "matched_biomarkers": "; ".join(p["biomarker"] for p in own),
                          "selection_for_co_candidate": "yes" if other and not own else "no",
                          "co_candidate_biomarkers": "; ".join(f"{p['biomarker']} ({p['matched_candidate']})" for p in other) if not own else "",
                          "n_candidates_in_trial": len(t["cands"])})
    rows = [{"active_moiety": m, "subcategory": first[m]["origin_trial_start"], "d40_mechanism": mech.get(first[m]["active_moiety"], ""),
             "n_trials": len(d["trials"]), "trials": "; ".join(d["trials"]), "chembl_mechanisms": chembl(first[m]["active_moiety"]),
             "coder_drug_class": " | ".join(sorted(d["hints"])), "registry_stated_mechanisms": " || ".join(d["stated"])}
            for m, d in drugs.items()]
    write("pathway_evidence_D42.csv", rows)
    write("pathway_pairs_D42.csv", pairs)
    print(f"drugs {len(rows)} (2a {sum(r['subcategory'] == '2a' for r in rows)}, 2b {sum(r['subcategory'] == '2b' for r in rows)}); "
          f"pairs {len(pairs)}; drug-matched {sum(p['drug_matched_selection'] == 'yes' for p in pairs)}; "
          f"co-candidate only {sum(p['selection_for_co_candidate'] == 'yes' for p in pairs)}; "
          f"with registry-stated mechanism {sum(bool(r['registry_stated_mechanisms']) for r in rows)}; "
          f"with ChEMBL mechanism {sum(bool(r['chembl_mechanisms']) for r in rows)}")


if __name__ == "__main__":
    main()
