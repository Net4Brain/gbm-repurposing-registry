"""
Step 02 - Supplementary ClinicalTrials.gov search (manuscript v3, Data source and retrieval).

Adds records missed by step 01 because they use
  (a) WHO CNS5 terminology (e.g. "astrocytoma, IDH-wildtype", "diffuse glioma"),
  (b) generic brain-tumour condition terms (e.g. "primary brain tumor"), or
  (c) basket/solid-tumour designs that name glioblastoma only in the eligibility criteria.
Same filters as step 01: interventional, start date 2020-01-01 to 2026-07-31.

Outputs:
  data/raw/ctgov_supp_raw_<timestamp>.json       records NOT already in the step-01 snapshot
  logs/ctgov_supp_query_log_<timestamp>.json     queries, hit counts, overlap with step 01

Usage: python3 scripts/02_supplementary_search.py data/raw/ctgov_raw_20261101T130137Z.json
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://clinicaltrials.gov/api/v2/studies"
START_MIN, START_MAX = "2020-01-01", "2026-07-31"
BASE_FILTER = ("AREA[StudyType]INTERVENTIONAL AND "
               f"AREA[StartDate]RANGE[{START_MIN},{START_MAX}]")

CNS5_TERMS = ['"astrocytoma, IDH-wildtype"', '"IDH-wildtype"', '"IDH wild-type"',
              '"diffuse glioma"', '"astrocytoma grade 4"', '"grade IV astrocytoma"',
              '"diffuse astrocytic glioma"']
BRAIN_TERMS = ['"primary brain tumor"', '"brain tumor"', '"brain neoplasm"',
               '"CNS tumor"', '"central nervous system tumor"']
GBM_ELIG = "AREA[EligibilityCriteria](glioblastoma OR gliosarcoma OR GBM)"

QUERIES = {
    "cns5_condition": {"query.cond": " OR ".join(CNS5_TERMS), "filter.advanced": BASE_FILTER},
    "cns5_free_text": {"query.term": " OR ".join(CNS5_TERMS), "filter.advanced": BASE_FILTER},
    "brain_tumour_condition": {"query.cond": " OR ".join(BRAIN_TERMS), "filter.advanced": BASE_FILTER},
    "gbm_in_eligibility": {"filter.advanced": f"{BASE_FILTER} AND {GBM_ELIG}"},
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


def main(main_snapshot):
    have = {nct(s) for s in json.loads(Path(main_snapshot).read_text())}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new, log = {}, {"retrieved_utc": stamp, "api": API, "main_snapshot": str(main_snapshot),
                    "start_date_window": [START_MIN, START_MAX], "queries": {}}
    for name, params in QUERIES.items():
        studies, total = fetch_all(params)
        ids = sorted(nct(s) for s in studies)
        added = [i for i in ids if i not in have]
        log["queries"][name] = {"params": params, "total_reported": total, "n_retrieved": len(ids),
                                "n_not_in_main": len(added), "nct_ids_not_in_main": added}
        for s in studies:
            if nct(s) not in have:
                new.setdefault(nct(s), s)
        print(f"{name}: {len(ids)} records, {len(added)} not in main snapshot")
    log["n_new_unique"] = len(new)
    print(f"new unique records: {len(new)}")

    raw_path = RAW_DIR / f"ctgov_supp_raw_{stamp}.json"
    log_path = LOG_DIR / f"ctgov_supp_query_log_{stamp}.json"
    raw_path.write_text(json.dumps(sorted(new.values(), key=nct), indent=1))
    log_path.write_text(json.dumps(log, indent=1))
    print(f"wrote {raw_path.relative_to(ROOT)}\nwrote {log_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1])
