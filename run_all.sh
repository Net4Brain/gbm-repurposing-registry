#!/usr/bin/env bash
# Rebuild every derived file from the frozen snapshots (no network needed except step 05 for
# moieties not yet in the cache). Retrieval (01, 02) is NOT re-run: the snapshots are the reference.
set -euo pipefail
cd "$(dirname "$0")"
MAIN=data/raw/ctgov_raw_20261101T130137Z.json
SUPP=data/raw/ctgov_supp_raw_20261101T150223Z.json
shasum -a 256 -c CHECKSUMS.sha256
python3 scripts/03_build_coder_input.py "$MAIN" "$SUPP" data/processed/supp_added_to_screening.csv
python3 scripts/04_select_calibration.py
python3 scripts/05_lookup_drugs.py --from-file outputs/calibration/candidate_moieties.txt
python3 scripts/07_compare_coders.py outputs/calibration
echo "done"
