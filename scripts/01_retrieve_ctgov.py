"""
Step 01 - Retrieve candidate glioblastoma trial records from ClinicalTrials.gov (API v2).

Protocol decisions implemented here (GBM repurposing study):
  - Primary cohort: interventional trials with start date 2020-01-01 to 2026-07-31,
    regardless of recruitment status. Active-on-index-date trials are a subset (flagged later).
  - Broad, sensitivity-first search; no phase/age/intervention filters at query level,
    so that every exclusion is made and counted downstream (flow diagram).

Outputs (in pipeline/data/raw/ and pipeline/logs/):
  ctgov_raw_<timestamp>.json      full study records, as returned by the API
  ctgov_query_log_<timestamp>.json exact queries, hit counts per query, retrieval time

Usage: python3 scripts/01_retrieve_ctgov.py   (run from the pipeline folder)
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://clinicaltrials.gov/api/v2/studies"
START_MIN, START_MAX = "2020-01-01", "2026-07-31"
INDEX_DATE = "2026-07-31"

# Condition terms from the manuscript Methods ("Data source and retrieval").
COND_TERMS = [
    "glioblastoma",
    "GBM",
    "glioblastoma multiforme",
    "gliosarcoma",
    "malignant glioma",
    "high-grade glioma",
    "grade 4 glioma",
]
COND_QUERY = " OR ".join(f'"{t}"' if " " in t else t for t in COND_TERMS)
FILTER = (
    "AREA[StudyType]INTERVENTIONAL AND "
    f"AREA[StartDate]RANGE[{START_MIN},{START_MAX}]"
)

# Two searches, unioned: the condition field (with CT.gov synonym expansion),
# and a free-text search that also covers titles, keywords and descriptions.
QUERIES = {
    "condition": {"query.cond": COND_QUERY, "filter.advanced": FILTER},
    "free_text": {"query.term": COND_QUERY, "filter.advanced": FILTER},
}

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR, LOG_DIR = ROOT / "data" / "raw", ROOT / "logs"


def fetch_all(params):
    studies, token = [], None
    while True:
        p = {**params, "pageSize": 1000, "format": "json", "countTotal": "true"}
        if token:
            p["pageToken"] = token
        r = requests.get(API, params=p, timeout=60)
        r.raise_for_status()
        page = r.json()
        studies.extend(page.get("studies", []))
        token = page.get("nextPageToken")
        if not token:
            return studies, page.get("totalCount")
        time.sleep(0.3)


def nct(study):
    return study["protocolSection"]["identificationModule"]["nctId"]


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    union, log = {}, {
        "retrieved_utc": stamp,
        "api": API,
        "start_date_window": [START_MIN, START_MAX],
        "index_date": INDEX_DATE,
        "queries": {},
    }
    for name, params in QUERIES.items():
        studies, total = fetch_all(params)
        ids = sorted(nct(s) for s in studies)
        log["queries"][name] = {"params": params, "total_reported": total,
                                "n_retrieved": len(studies), "nct_ids": ids}
        for s in studies:
            union.setdefault(nct(s), s)
        print(f"{name}: {len(studies)} records (API total {total})")

    cond_ids = set(log["queries"]["condition"]["nct_ids"])
    text_ids = set(log["queries"]["free_text"]["nct_ids"])
    log["union"] = {"n": len(union), "condition_only": len(cond_ids - text_ids),
                    "free_text_only": len(text_ids - cond_ids),
                    "both": len(cond_ids & text_ids)}
    print(f"union: {len(union)} unique NCT records")

    raw_path = RAW_DIR / f"ctgov_raw_{stamp}.json"
    log_path = LOG_DIR / f"ctgov_query_log_{stamp}.json"
    raw_path.write_text(json.dumps(sorted(union.values(), key=nct), indent=1))
    log_path.write_text(json.dumps(log, indent=1))
    print(f"wrote {raw_path.relative_to(ROOT)}\nwrote {log_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
