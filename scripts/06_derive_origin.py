"""
Step 06 - [RULE] layer: drug origin per candidate agent per trial (coding manual 4.2-4.3; D5-D7, D11, D12).

Input : CSV with columns nct_id, active_moiety, role, trial_start (YYYY-MM or YYYY-MM-DD)
        (adjudicated agent table; only roles experimental_monotherapy / experimental_combination are candidates)
Lookup: data/lookup/v1.2/<moiety>.json from step 05
Output: CSV with origin at trial start (primary, D12) and at the index date (sensitivity 3), plus
        flags and the evidence used.

Usage: python3 scripts/06_derive_origin.py agents_adjudicated.csv data/processed/agent_origin.csv
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOOKUP = ROOT / "data" / "lookup" / "v1.2"
INDEX_DATE = "2026-07-31"
CANDIDATE_ROLES = {"experimental_monotherapy", "experimental_combination"}
ESTABLISHED = {"temozolomide", "carmustine", "lomustine", "bevacizumab"}   # D6


def norm_date(d):
    d = (d or "").strip()
    return d + "-01" if re.fullmatch(r"\d{4}-\d{2}", d) else d


def classify(moiety, T, lk):
    """Return (category, flags) for one moiety at date T (ISO string)."""
    fl = lk["flags"]
    flags = list(fl["needs_human_check"])
    if moiety in ESTABLISHED:
        return "ESTABLISHED", flags
    first = fl["first_approval_date"]
    if first and first <= T:
        if fl["glioma_in_first_ema_label"] or first_approval_is_glioma(lk, first):
            return "GLIOMA_DEVELOPED", flags
        if not fl["oncology_approval"]:
            return "2a", flags
        if fl["tumour_agnostic_text"]:
            flags.append("tumour_agnostic")
            # 2c only when every oncology approval is tumour-agnostic; otherwise 2b with the flag kept
            return ("2c" if only_agnostic(lk) else "2b"), flags
        if fl["glioma_in_label"]:
            flags.append("glioma_label")
        return "2b", flags
    p2 = (lk.get("first_non_gbm_phase2_trial") or {}).get("earliest")
    if p2 and norm_date(p2["start"]) < T:
        return "3", flags
    if (lk["chembl"].get("max_phase") or 0) >= 2 and not p2:
        flags.append("ChEMBL phase >=2 but no dated non-GBM trial found: adjudicate 1 vs 3")
    return "1", flags


def first_approval_is_glioma(lk, first):
    """Every available FDA label / EMA indication text is glioma-specific (openFDA labels can lag new
    approvals, so EMA text is used too); then the first approval must have been a glioma indication."""
    texts = lk["fda"]["label_indications"] + [p["indication"] for p in lk["ema"]["products"]]
    return bool(texts) and all(re.search(r"glioma|astrocytoma", t, re.I) and not
                               re.search(r"melanoma|carcinoma|lung|leuk|lymphoma|solid tumou?rs", t, re.I)
                               for t in texts)


def only_agnostic(lk):
    texts = lk["fda"]["label_indications"] + [p["indication"] for p in lk["ema"]["products"]]
    specific = re.compile(r"melanoma|carcinoma|lung cancer|breast|colorectal|thyroid|leuk|lymphoma|sarcoma", re.I)
    return not any(specific.search(t) for t in texts)


def main(src, dst):
    rows_out = []
    for r in csv.DictReader(open(src)):
        if r["role"] not in CANDIDATE_ROLES:
            continue
        m = r["active_moiety"].strip().lower()
        path = LOOKUP / f"{re.sub(r'[^a-z0-9]+', '_', m)}.json"
        if not path.exists():
            rows_out.append({**r, "origin_trial_start": "NO_LOOKUP", "origin_index_date": "NO_LOOKUP",
                             "flags": "run step 05 for this moiety", "first_approval_date": "",
                             "first_non_gbm_phase2": ""})
            continue
        lk = json.loads(path.read_text())
        T = norm_date(r["trial_start"])
        o_t, f_t = classify(m, T, lk)
        o_i, _ = classify(m, INDEX_DATE, lk)
        p2 = (lk.get("first_non_gbm_phase2_trial") or {}).get("earliest") or {}
        rows_out.append({**r, "origin_trial_start": o_t, "origin_index_date": o_i,
                         "flags": "; ".join(f_t), "first_approval_date": lk["flags"]["first_approval_date"] or "",
                         "first_non_gbm_phase2": f"{p2.get('nct', '')} {p2.get('start', '')}".strip()})
    with open(dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    print(f"wrote {len(rows_out)} candidate rows to {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
