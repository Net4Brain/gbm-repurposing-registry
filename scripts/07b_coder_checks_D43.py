"""
Step 07b - Extra checks on the archived coder responses (D43). Post-registration step; reads only.
The frozen comparison (scripts/07_compare_coders_v2.py) is not changed.

Gaps found by the reproducibility audit of commit 453f1d3, measured here on the real coder files:
  1. File name vs internal trial ID (coderA/coderB/*.json).
  2. Biomarker rows that agree on identity, role, match and matched agent but differ only in the arms listed
     (not queued by 07 v2). For eligibility/enrichment rows the D21 review status is reported, because arms decide
     whether a requirement governs the cohort that receives the candidate (A1, A2).
  3. Evidence quotes: every {"quote": ...} in a coder file is checked against that record's coder input text
     (data/coder_input/<NCT>.txt), after collapsing whitespace and ignoring case; quotes with "..." are checked
     piece by piece. Non-verbatim quotes are graded (symbols_only, pieces_present, not_found) and listed.
Output: outputs/main/coder_checks_D43.csv (refuses to overwrite), one row per finding
Usage : python3 scripts/07b_coder_checks_D43.py
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
OUT = RUN / "coder_checks_D43.csv"
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[‘’]", "'", re.sub(r"[“”]", '"', s or ""))).strip().lower()


def quotes(obj, path=""):
    """Yield (variable path, quote) for every dict with a 'quote' key."""
    if isinstance(obj, dict):
        if isinstance(obj.get("quote"), str):
            yield path, obj["quote"]
        for k, v in obj.items():
            yield from quotes(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for v in obj:
            yield from quotes(v, path)


def match_level(q, text):
    """verbatim (after whitespace/case/quote-mark normalisation) > symbols_only (letters and digits match) >
    pieces_present (every ';'-separated piece is in the record, e.g. a stitched keyword list) > not_found"""
    an = lambda s: re.sub(r"[^a-z0-9]", "", s)
    parts = [p for p in re.split(r"\s*(?:\.\.\.|…|\[\.\.\.\])\s*", norm(q)) if len(p) >= 4]
    if all(p in text for p in parts):
        return "verbatim"
    if all(an(p) in an(text) for p in parts):
        return "symbols_only"
    if all(an(x) in an(text) for p in parts for x in p.split(";") if len(an(x)) > 3):
        return "pieces_present"
    return "not_found"


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite")
    coh = {r["nct_id"] for r in csv.DictReader(open(RUN / "cohort_D37.csv")) if r["primary_cohort"] == "yes"}
    d21 = {r["nct_id"] for r in csv.DictReader(open(RUN / "d21_match_decisions_XL.csv"))}
    findings, n_quotes, unver = [], 0, Counter()
    for f in sorted((RUN / "coderA").glob("*.json")):
        n = f.stem
        J = {c: json.loads((RUN / c / f"{n}.json").read_text()) for c in ("coderA", "coderB")}
        text = norm((ROOT / "data" / "coder_input" / f"{n}.txt").read_text())
        for c, j in J.items():
            if j["nct_id"] != n:
                findings.append({"check": "file name vs trial ID", "nct_id": n, "coder": c, "in_cohort": n in coh,
                                 "variable": "", "detail": f"internal {j['nct_id']}"})
            for var, q in quotes(j):
                n_quotes += 1
                lvl = match_level(q, text)
                if lvl != "verbatim":
                    unver[lvl] += 1
                    findings.append({"check": f"quote {lvl}", "nct_id": n, "coder": c, "in_cohort": n in coh,
                                     "variable": var, "detail": q[:200]})
        key = lambda x: (x["biomarker"], x.get("biomarker_other") or "", x["role"], bool(x["candidate_matched"]),
                         (x.get("matched_agent") or "").lower())
        a = {key(x): sorted(x.get("arms") or []) for x in J["coderA"]["biomarkers"]}
        b = {key(x): sorted(x.get("arms") or []) for x in J["coderB"]["biomarkers"]}
        for k in sorted(set(a) & set(b)):
            if a[k] != b[k]:
                findings.append({"check": "biomarker arms differ only", "nct_id": n, "coder": "A vs B", "in_cohort": n in coh,
                                 "variable": f"{k[0]} {k[2]} {'matched' if k[3] else 'unmatched'}",
                                 "detail": f"A {a[k]} | B {b[k]}" + ("; D21-reviewed" if n in d21 and k[3] else "")})
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["check", "nct_id", "coder", "in_cohort", "variable", "detail"])
        w.writeheader()
        w.writerows(findings)
    c = Counter(f["check"] for f in findings)
    print(f"quotes checked {n_quotes}; findings {dict(c)}")
    print("non-verbatim quotes by match level:", dict(unver))
    arm = [f for f in findings if f["check"].startswith("biomarker") and f["in_cohort"] and " matched" in f["variable"]
           and ("eligibility" in f["variable"] or "enrichment" in f["variable"])]
    print(f"cohort eligibility/enrichment matched rows with arm-only differences: {len(arm)}, "
          f"D21-reviewed {sum('D21-reviewed' in f['detail'] for f in arm)}")


if __name__ == "__main__":
    main()
