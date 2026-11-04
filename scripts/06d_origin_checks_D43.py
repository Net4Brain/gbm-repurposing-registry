"""
Step 06d - Origin input validation and start-date sensitivity check (D43). Post-registration step; reads only.
The frozen classifier (scripts/06_derive_origin_v2.py) is imported unchanged.

Gaps found by the reproducibility audit of commit 453f1d3, checked here on the real inputs:
  1. Input validation. Every regulatory row must be FDA or EMA and human-reviewed; every development row must be
     human-reviewed with a valid phase; dates must parse with date_lo <= date_hi. The classifier itself treats
     unreviewed regulatory rows as UNRESOLVED but does not check jurisdiction or development-row review.
  2. Month-only trial starts. The classifier uses the first day of the month (D12, earliest possible start), so an
     event later in the same month is "not yet happened" with no date_sensitive flag. Each candidate is classified
     at the first and the last possible start day; any change of category or of the tumour-agnostic/glioma flags
     is reported.
  3. Flag-only changes. For event intervals containing T, the classifier flags date_sensitive only when the
     category changes; a change in the tumour-agnostic or glioma flags is reported here as well.
Input : outputs/main/origin_derived_D36.csv (candidate rows with trial_start), data/reference/*_events.csv
Output: outputs/main/origin_checks_D43.csv (refuses to overwrite): one row per finding; empty findings are
        reported as a single "none" row
Usage : python3 scripts/06d_origin_checks_D43.py
"""
import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "reference"
OUT = ROOT / "outputs" / "main" / "origin_checks_D43.csv"
spec = importlib.util.spec_from_file_location("o", ROOT / "scripts" / "06_derive_origin_v2.py")
O = importlib.util.module_from_spec(spec)
spec.loader.exec_module(O)
FLAGS = ("tumour_agnostic_at_T", "glioma_label_at_T")


def state(c):
    return c["category"], tuple(f for f in FLAGS if f in c["flags"])


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite")
    findings = []
    events, dev = O.load(REF / "regulatory_events.csv"), O.load(REF / "development_events.csv")
    for name, table in (("regulatory_events.csv", events), ("development_events.csv", dev)):
        for m, rows in table.items():
            for r in rows:
                bad = []
                if not r.get("reviewed_by"):
                    bad.append("not human-reviewed")
                if name.startswith("regulatory") and r["jurisdiction"] not in ("FDA", "EMA"):
                    bad.append(f"jurisdiction {r['jurisdiction']!r}")
                if name.startswith("development") and r["phase"] not in ("1", "2", "3", "none_found"):
                    bad.append(f"phase {r['phase']!r}")
                if r.get("phase") != "none_found":
                    try:
                        r["date_lo"], _ = O.iso(r["date_lo"])
                        _, r["date_hi"] = O.iso(r["date_hi"] or r["date_lo"])
                        if r["date_lo"] > r["date_hi"]:
                            bad.append("date_lo after date_hi")
                    except ValueError as e:
                        bad.append(str(e))
                if bad:
                    findings.append({"check": "input", "table": name, "moiety": m, "nct_id": "", "detail": "; ".join(bad)})
    n_month = n_straddle = 0
    for r in csv.DictReader(open(ROOT / "outputs" / "main" / "origin_derived_D36.csv")):
        if r["role"] not in O.CANDIDATE_ROLES:
            continue
        m = r["active_moiety"].strip().lower()
        lo, hi = O.iso(r["trial_start"])
        pwl = (r.get("population_within_label") or "").strip().lower()
        a = O.classify(m, lo, events, dev, pwl)
        if lo != hi:
            n_month += 1
            b = O.classify(m, hi, events, dev, pwl)
            if state(a) != state(b):
                findings.append({"check": "month-only start", "table": "", "moiety": m, "nct_id": r["nct_id"],
                                 "detail": f"start {r['trial_start']}: {state(a)} at {lo}, {state(b)} at {hi}"})
        straddle = [e for e in events.get(m, []) if e["date_lo"] <= lo < e["date_hi"]]
        if straddle:
            n_straddle += 1
            b = O.classify(m, max(e["date_hi"] for e in straddle), events, dev, pwl)
            if state(a)[1] != state(b)[1] and state(a)[0] == state(b)[0]:
                findings.append({"check": "flag-only date sensitivity", "table": "", "moiety": m, "nct_id": r["nct_id"],
                                 "detail": f"flags {state(a)[1]} vs {state(b)[1]} if event dated at interval end"})
    rows = findings or [{"check": "none", "table": "", "moiety": "", "nct_id": "", "detail": "no findings"}]
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"regulatory rows {sum(map(len, events.values()))}, development rows {sum(map(len, dev.values()))}; "
          f"month-only candidate starts {n_month}; candidates with a straddling event {n_straddle}; findings {len(findings)}")
    for f in findings:
        print(" ", f)


if __name__ == "__main__":
    main()
