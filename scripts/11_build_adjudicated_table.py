"""
Step 11 - Build the adjudicated trial-level table for all screening records (post-registration processing step).

Queued trials (a priority-1/2 adjudication item): the latest proposal (proposals_v3 > proposals_v2 > proposals),
which XL accepted, with XL's overrides from adjudication_overrides_D32.json applied on top.
Other trials: no priority-1/2 disagreement, so the coders' agreed values (taken from coder A).

Output: <run>/adjudicated_trials_D32.csv, one row per record in manifest.txt; `source` says where each row came
from. Structured-field steps (study type, start date, phase, age) are not applied here.
Refuses to overwrite an existing table.

Usage: python3 scripts/11_build_adjudicated_table.py outputs/main
"""
import csv
import json
import sys
from pathlib import Path

INCLUDED_POP = ("gbm_only", "mixed_glioma_gbm_named", "basket_gbm_eligible")
FIELDS = ["gbm_population", "cns5_terminology", "basket", "has_eligible_candidate", "candidate_exclusion_reason",
          "candidates", "treatment_setting", "regimen", "combination_partners", "candidate_matched_selection",
          "imaging_assessed_selection", "matched_biomarkers", "any_molecular_selection", "tumour_pk_planned",
          "target_engagement_planned"]


def from_coder(d):
    sel = [b for b in d["biomarkers"] if b["role"] in ("eligibility", "enrichment")]
    s, t = d["screening"], d["trial"]
    return {"gbm_population": s["gbm_population"], "cns5_terminology": s["cns5_terminology"], "basket": t["basket"],
            "has_eligible_candidate": s["has_eligible_candidate"],
            "candidate_exclusion_reason": s["candidate_exclusion_reason"],
            "candidates": [{"active_moiety": a["active_moiety"], "role": a["role"],
                            "device_dependent": a.get("device_dependent", False)}
                           for a in d["agents"] if a["role"].startswith("experimental_")],
            "treatment_setting": t["treatment_setting"], "regimen": t["regimen"],
            "combination_partners": t.get("combination_partners") or [],
            "candidate_matched_selection": any(b["candidate_matched"] for b in sel),
            "imaging_assessed_selection": False,
            "matched_biomarkers": [{"biomarker": b["biomarker"], "matched_agent": b.get("matched_agent")}
                                   for b in sel if b["candidate_matched"]],
            "any_molecular_selection": bool(sel),
            "tumour_pk_planned": t["tumour_pk_planned"], "target_engagement_planned": t["target_engagement_planned"]}


def partners_from_items(d):
    vals = [i["proposed"] for i in d["items"] if "combination_partners" in str(i.get("item"))]
    if not vals:
        return None
    v = vals[-1]
    if isinstance(v, list):
        return v
    try:
        p = json.loads(v)
        return p if isinstance(p, list) else None
    except (TypeError, ValueError):
        return None


def main(run_dir):
    run = Path(run_dir)
    dst = run / "adjudicated_trials_D32.csv"
    if dst.exists():
        sys.exit(f"{dst} exists; refusing to overwrite")
    ov = {o["nct_id"]: o for o in json.loads((run / "adjudication_overrides_D32.json").read_text())["overrides"]}
    rows = []
    for n in [l.strip() for l in open(run / "manifest.txt") if l.strip()]:
        a = json.loads((run / "coderA" / f"{n}.json").read_text())
        base = from_coder(a)
        src = "coders_agreed"
        for ver, folder in (("v3", "proposals_v3"), ("v2", "proposals_v2"), ("v1", "proposals")):
            p = run / folder / f"{n}.json"
            if p.exists():
                d = json.loads(p.read_text())
                f = d["proposed_final"]
                base.update({k: f[k] for k in FIELDS if k in f})
                part = partners_from_items(d)
                if part is not None:
                    base["combination_partners"] = part
                src = f"proposal_{ver}"
                break
        basis = ""
        if n in ov:
            base.update(ov[n]["set"])
            src += "+XL_override"
            basis = ov[n]["basis"]
        if not base["has_eligible_candidate"]:
            base["regimen"] = "not_applicable"
        inc = base["gbm_population"] in INCLUDED_POP and bool(base["has_eligible_candidate"])
        rows.append({"nct_id": n, "source": src, "passes_S4_S6_llm": inc,
                     **{k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in base.items()},
                     "override_basis": basis})
    with open(dst, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    inc = [r for r in rows if r["passes_S4_S6_llm"]]
    prim = [r for r in inc if r["candidate_matched_selection"] in (True, "true", "True")]
    print(f"records {len(rows)}; sources: " + ", ".join(f"{s} {sum(r['source'] == s for r in rows)}"
                                                       for s in sorted({r['source'] for r in rows})))
    print(f"pass LLM-coded steps S5-S6: {len(inc)}; candidate-matched selection among them: {len(prim)} "
          f"({len(prim) / len(inc):.1%})")


if __name__ == "__main__":
    main(sys.argv[1])
