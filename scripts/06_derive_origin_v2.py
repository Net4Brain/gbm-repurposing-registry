"""
Step 06 v2 - [RULE] layer: drug origin per candidate agent per trial, from DATED evidence
(coding manual v1.3 section 4; D6, D12, D20, D26). Replaces 06_derive_origin.py (kept unchanged,
frozen in FROZEN_v1.2.sha256), which used current label flags and defaulted to de novo.

Inputs
  agents CSV   : nct_id, active_moiety, role, trial_start (YYYY, YYYY-MM or YYYY-MM-DD),
                 optional population_within_label (yes / no; human decision, D20b)
  events CSV   : data/reference/regulatory_events.csv   (one row per FDA/EMA approval event)
                 moiety, jurisdiction, event_type, indication, oncology, tumour_agnostic, glioma,
                 date_lo, date_hi, source, source_url, reviewed_by, review_date
  dev CSV      : data/reference/development_events.csv  (prior non-GBM clinical development)
                 moiety, phase (1/2/3), indication, date_lo, date_hi, source, reviewed_by
                 plus rows with phase "none_found" when a documented search found nothing

Output CSV: one row per candidate with origin at trial start (primary) and at the index date,
the two dated axes, flags, and the evidence rows used.

Rules
  - An event counts as "on or before T" only if date_hi <= T. If date_lo <= T < date_hi the
    classification is computed both ways; if they differ the row is flagged date_sensitive and the
    conservative result (event not yet happened) is kept.
  - Category 2c does not exist; tumour-agnostic approval is the flag tumour_agnostic_at_T.
  - Missing or unreviewed evidence gives UNRESOLVED, never a default category.
  - unspecified_approved_panel: category 2 at trial level, subtype unknown (manual 4.3).

Usage: python3 scripts/06_derive_origin_v2.py agents.csv out.csv
       [--events data/reference/regulatory_events.csv] [--dev data/reference/development_events.csv]
"""
import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_DATE = "2026-07-31"
CANDIDATE_ROLES = {"experimental_monotherapy", "experimental_combination"}
ESTABLISHED = {"temozolomide", "carmustine", "lomustine", "bevacizumab"}   # D6
PANEL = "unspecified_approved_panel"


def iso(d, end=False):
    """YYYY / YYYY-MM / YYYY-MM-DD -> (lo, hi) ISO dates."""
    d = (d or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        return d, d
    if re.fullmatch(r"\d{4}-\d{2}", d):
        y, m = map(int, d.split("-"))
        last = [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
        return f"{d}-01", f"{d}-{last:02d}"
    if re.fullmatch(r"\d{4}", d):
        return f"{d}-01-01", f"{d}-12-31"
    raise ValueError(f"bad date {d!r}")


def yes(v):
    return str(v).strip().lower() in ("yes", "true", "1")


def load(path):
    rows = {}
    if Path(path).exists():
        for r in csv.DictReader(open(path)):
            rows.setdefault(r["moiety"].strip().lower(), []).append(r)
    return rows


def classify(moiety, T, events, dev, population_within_label=""):
    """Return dict(category, regulatory_status, prior_dev_phase, flags, evidence) at date T (ISO)."""
    out = {"category": None, "regulatory_status": "", "prior_dev_phase": "", "flags": [], "evidence": []}
    if moiety in ESTABLISHED:
        out.update(category="ESTABLISHED", regulatory_status="approved_glioblastoma")
        return out
    if moiety == PANEL:
        out.update(category="2_panel", regulatory_status="approved_unspecified")
        out["flags"].append("unspecified_approved_panel: trial-level only")
        return out
    ev = events.get(moiety, [])
    unreviewed = [e for e in ev if not e.get("reviewed_by")]
    if unreviewed:
        out["flags"].append(f"{len(unreviewed)} regulatory event(s) not human-reviewed")
    before = [e for e in ev if e["date_hi"] <= T]
    straddle = [e for e in ev if e["date_lo"] <= T < e["date_hi"]]
    if before:
        first = min(ev, key=lambda e: (e["date_lo"], e["date_hi"]))
        if yes(first["glioma"]) and first in before:
            out["category"] = "GLIOMA_DEVELOPED"
        else:
            onco = any(yes(e["oncology"]) for e in before)
            out["category"] = "2b" if onco else "2a"
        out["regulatory_status"] = "approved_oncology" if any(yes(e["oncology"]) for e in before) else "approved_non_oncology"
        if any(yes(e["tumour_agnostic"]) for e in before):
            out["flags"].append("tumour_agnostic_at_T")
        if any(yes(e["glioma"]) for e in before) and out["category"] != "GLIOMA_DEVELOPED":
            out["flags"].append("glioma_label_at_T")
        if ("tumour_agnostic_at_T" in out["flags"] or "glioma_label_at_T" in out["flags"]):
            if population_within_label in ("yes", "no"):
                if population_within_label == "yes":
                    out["flags"].append("population_within_label")
            else:
                out["flags"].append("population_within_label: needs human decision")
        out["evidence"] = [f'{e["jurisdiction"]} {e["date_lo"]} {e["indication"][:60]}' for e in before]
    else:
        out["regulatory_status"] = "unapproved"
    if straddle:
        alt = classify(moiety, max(e["date_hi"] for e in straddle), events, dev, population_within_label)
        if alt["category"] != out["category"]:
            out["flags"].append(f"date_sensitive (would be {alt['category']} if event dated at interval end)")
    # prior non-GBM development (axis 2, and category 3 vs 1 for unapproved agents)
    dv = dev.get(moiety, [])
    dated = [d for d in dv if d["phase"] in ("1", "2", "3") and d["date_hi"] < T]
    phase = max((int(d["phase"]) for d in dated), default=0)
    # any reviewed row means the agent's development history was documented, so absence of an
    # earlier row means no earlier development
    searched = any(d.get("reviewed_by") for d in dv)
    out["prior_dev_phase"] = "approved" if before else (str(phase) if phase else ("none" if searched or dated else "unknown"))
    if out["category"] is None:
        if phase >= 2:
            out["category"] = "3"
            out["evidence"] += [f'{d["source"]} phase {d["phase"]} {d["date_lo"]}' for d in dated if int(d["phase"]) >= 2]
        elif searched or dated:
            out["category"] = "1"
        else:
            out["category"] = "UNRESOLVED"
            out["flags"].append("no reviewed development evidence: adjudicate 1 vs 3")
    if not ev and out["category"] in ("1", "3") and not searched:
        out["flags"].append("no regulatory events recorded: confirm unapproved")
    if unreviewed and out["category"] not in ("ESTABLISHED", "2_panel"):
        out["category"] = "UNRESOLVED"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agents")
    ap.add_argument("out")
    ap.add_argument("--events", default=str(ROOT / "data" / "reference" / "regulatory_events.csv"))
    ap.add_argument("--dev", default=str(ROOT / "data" / "reference" / "development_events.csv"))
    a = ap.parse_args()
    events, dev = load(a.events), load(a.dev)
    for table in (events, dev):
        for rows in table.values():
            for r in rows:
                if r.get("phase") != "none_found":
                    r["date_lo"], _ = iso(r["date_lo"])
                    _, r["date_hi"] = iso(r["date_hi"] or r["date_lo"])
    rows_out = []
    for r in csv.DictReader(open(a.agents)):
        if r["role"] not in CANDIDATE_ROLES:
            continue
        m = r["active_moiety"].strip().lower()
        T, _ = iso(r["trial_start"])          # earliest possible start (D12); month-only start -> first day
        pwl = (r.get("population_within_label") or "").strip().lower()
        t = classify(m, T, events, dev, pwl)
        i = classify(m, INDEX_DATE, events, dev, pwl)
        rows_out.append({**r, "origin_trial_start": t["category"], "origin_index_date": i["category"],
                         "regulatory_status_at_T": t["regulatory_status"], "prior_non_gbm_phase_at_T": t["prior_dev_phase"],
                         "flags": "; ".join(t["flags"]), "evidence": " | ".join(t["evidence"])})
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    unresolved = sum(r["origin_trial_start"] == "UNRESOLVED" for r in rows_out)
    print(f"wrote {len(rows_out)} candidate rows to {a.out}; UNRESOLVED: {unresolved}")


if __name__ == "__main__":
    main()
