"""
Step 07 v2 - Compare Coder A and Coder B on EVERY coded field (coding manual v1.3 section 7; D21, D26).
Replaces 07_compare_coders.py (kept unchanged, frozen in FROZEN_v1.2.sha256), which compared a
selected set of fields, took the union of output files as the record list, and missed some
disagreements (methods review 2026-11-02, R3d).

Checks
  - every expected record (manifest) has a valid output from each coder
  - every screening and trial field, including evidence-free fields
  - per agent (matched by normalised moiety): every field except free text and evidence
  - agents present in one coder's output only
  - per biomarker: the set of (biomarker, other, role, candidate_matched, matched_agent) tuples
  - quotes not verbatim in the coder input
  - uncertain flags
Agreement statistics (kappa, PABAK, AC1) are reported for the trial-level variables of v1.0 plus the
v1.3 variables, so rounds stay comparable.

Writes <run>/adjudication_queue.csv and <run>/agreement.csv

Usage: python3 scripts/07_compare_coders_v2.py <run_dir> <schema.json> [manifest.txt]
       manifest: one NCT ID per line; default = the IDs listed in <run_dir>/batches/*.txt
"""
import csv
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from importlib.util import module_from_spec, spec_from_file_location  # noqa: E402

_s = spec_from_file_location("c1", ROOT / "scripts" / "07_compare_coders.py")
c1 = module_from_spec(_s)
_s.loader.exec_module(c1)
kappa_stats, uncertain_items, not_verbatim = c1.kappa_stats, c1.uncertain_items, c1.not_verbatim

SKIP_AGENT = {"agent_name_registered", "role_evidence", "drug_class_hint", "stated_antitumour_mechanism", "flag"}
SCREEN = ["gbm_population", "has_eligible_candidate", "candidate_exclusion_reason", "cns5_terminology"]
TRIAL = ["treatment_setting", "regimen", "combination_partners", "basket", "control_arm_from_other_arms",
         "industry_support_in_text", "tumour_pk_planned", "target_engagement_planned"]
STATS = SCREEN + ["treatment_setting", "regimen", "basket", "control_arm_from_other_arms", "industry_support_in_text",
                  "tumour_pk_planned", "target_engagement_planned", "candidate_set",
                  "candidate_matched_selection", "any_molecular_selection"]


def norm(x):
    if isinstance(x, list):
        return sorted(norm(v) for v in x)
    if isinstance(x, str):
        return " ".join(x.lower().split())
    return x


def trial_values(d):
    v = {k: d["screening"][k] for k in SCREEN}
    v.update({k: d["trial"].get(k) for k in TRIAL})
    v["combination_partners"] = tuple(norm(v["combination_partners"] or []))
    v["candidate_set"] = tuple(sorted({a["active_moiety"].lower() for a in d["agents"] if a["role"].startswith("experimental_")}))
    sel = [b for b in d["biomarkers"] if b["role"] in ("eligibility", "enrichment")]
    v["candidate_matched_selection"] = any(b["candidate_matched"] for b in sel)
    v["any_molecular_selection"] = bool(sel)
    return v


def agents_by_moiety(d):
    out = {}
    for a in d["agents"]:
        key = norm(a["active_moiety"])
        out.setdefault(key, []).append({k: norm(v) for k, v in a.items() if k not in SKIP_AGENT})
    return out


def biomarker_set(d):
    return {(b["biomarker"], norm(b.get("biomarker_other") or ""), b["role"], b["candidate_matched"], norm(b.get("matched_agent") or ""))
            for b in d["biomarkers"]}


def main(run_dir, schema_path, manifest=None):
    run = Path(run_dir)
    schema = json.loads(Path(schema_path).read_text())
    if manifest:
        ids = [l.strip() for l in open(manifest) if l.strip()]
    else:
        ids = [l.strip() for p in sorted((run / "batches").glob("*.txt")) for l in open(p) if l.strip()]
    queue, pairs = [], {k: [] for k in STATS}
    extra = {p.stem for c in "AB" for p in (run / f"coder{c}").glob("NCT*.json")} - set(ids)
    for nct in sorted(extra):
        queue.append([nct, "unexpected_output", "not in manifest", "", ""])
    for nct in ids:
        docs = {}
        for c in "AB":
            path = run / f"coder{c}" / f"{nct}.json"
            if not path.exists():
                queue.append([nct, "missing_output", f"coder {c}", "", ""])
                continue
            try:
                docs[c] = json.loads(path.read_text())
                jsonschema.validate(docs[c], schema)
            except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                queue.append([nct, "invalid_output", f"coder {c}", str(e)[:200], ""])
                docs.pop(c, None)
        record = (ROOT / "data" / "coder_input" / f"{nct}.txt").read_text()
        for c, d in docs.items():
            for q in not_verbatim(d, record):
                queue.append([nct, "quote_not_verbatim", f"coder {c}", q[:200], ""])
        if len(docs) < 2:
            continue
        A, B = docs["A"], docs["B"]
        va, vb = trial_values(A), trial_values(B)
        for k in STATS:
            pairs[k].append((va[k], vb[k]))
        for k in sorted(set(va) | set(vb)):
            if va.get(k) != vb.get(k):
                queue.append([nct, "disagreement", k, json.dumps(va.get(k)), json.dumps(vb.get(k))])
        ga, gb = agents_by_moiety(A), agents_by_moiety(B)
        for m in sorted(set(ga) | set(gb)):
            if m not in ga or m not in gb:
                queue.append([nct, "disagreement", f"agent_only_in_{'A' if m in ga else 'B'}", m, ""])
                continue
            for fa, fb in zip(sorted(ga[m], key=json.dumps), sorted(gb[m], key=json.dumps)):
                for k in sorted(set(fa) | set(fb)):
                    if fa.get(k) != fb.get(k):
                        queue.append([nct, "disagreement", f"agent:{m}:{k}", json.dumps(fa.get(k)), json.dumps(fb.get(k))])
            if len(ga[m]) != len(gb[m]):
                queue.append([nct, "disagreement", f"agent:{m}:row_count", len(ga[m]), len(gb[m])])
        ba, bb = biomarker_set(A), biomarker_set(B)
        for t in sorted(ba - bb, key=str):
            queue.append([nct, "disagreement", "biomarker_only_in_A", json.dumps(t), ""])
        for t in sorted(bb - ba, key=str):
            queue.append([nct, "disagreement", "biomarker_only_in_B", "", json.dumps(t)])
        for c in "AB":
            for item, reason in uncertain_items(docs[c]):
                queue.append([nct, "uncertain", f"coder {c}: {item}", reason, ""])
    with open(run / "adjudication_queue.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nct_id", "type", "item", "coder_A_or_detail", "coder_B", "decision", "decided_by", "reason"])
        w.writerows(row + ["", "", ""] for row in queue)
    stats = [{"variable": k, **kappa_stats(p)} for k, p in pairs.items()]
    with open(run / "agreement.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["variable", "n", "pct_agree", "kappa", "pabak", "gwet_ac1", "categories"])
        w.writeheader()
        w.writerows(s for s in stats if s.get("n"))
    types = {}
    for r in queue:
        types[r[1]] = types.get(r[1], 0) + 1
    print(f"{len(ids)} expected records; {len(queue)} queue rows {types} -> {run / 'adjudication_queue.csv'}")
    for s in stats:
        if s.get("n"):
            print(f"  {s['variable']:30} agree={s['pct_agree']} kappa={s['kappa']} pabak={s['pabak']} ac1={s['gwet_ac1']}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
