"""
Step 20a - Rebuild the D41 status-history reference table from the raw browser extract (D43). Reads only.

The raw extract was captured on 2026-11-04 in the public ClinicalTrials.gov record-history page, because scripted
requests to the history endpoint return 403. The extraction code is scripts/20a_status_history_extract.js (run in
the browser console on https://clinicaltrials.gov/study/<any NCT>?tab=history). Each raw line is
  nct_id|status of the last version on or before 2026-07-31|its date|its version|status of the next version|its date|n versions
Input : data/raw/ctgov_status_history_D41_20261104.txt (SHA-256 b48c8cc5...e518)
Check : the rebuilt table must equal data/reference/status_history_index_D41.csv byte for byte.
Usage : python3 scripts/20a_status_history_from_raw.py
"""
import csv
import hashlib
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ctgov_status_history_D41_20261104.txt"
REF = ROOT / "data" / "reference" / "status_history_index_D41.csv"
RAW_SHA = "b48c8cc5b5e6cdc40f031d7c9729b106b9b2f3278e06b7b28e7d01ce2058e518"
SOURCE = ("ClinicalTrials.gov record history (api/int/studies/{nct}?history=true via the public history page), "
          f"accessed 2026-11-04; raw extract SHA-256 {RAW_SHA}")


def main():
    raw = RAW.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RAW_SHA, "raw extract hash differs"
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["nct_id", "status_last_version_on_or_before_2026-07-31", "version_date", "version_number",
                "status_next_version_after", "next_version_date", "n_versions", "source"])
    for line in raw.decode().splitlines():
        if line.strip():
            w.writerow(line.split("|") + [SOURCE])
    same = buf.getvalue().encode() == REF.read_bytes()
    print(f"rows {buf.getvalue().count(chr(10)) - 1}; identical to {REF.name}: {same}")
    assert same


if __name__ == "__main__":
    main()
