#!/usr/bin/env bash
# Rebuild the derived files that exist so far, stage by stage, from the frozen snapshots and the
# archived coder outputs. Retrieval (01, 02) and AI coding are NOT re-run: the snapshots and the
# archived outputs are the reference. Stages are added here as the study reaches them; this script
# only covers what is listed below.
# Requires data/raw/ReDO_Trials_DB_20261101.txt (bash scripts/00_fetch_redo.sh).
set -euo pipefail
cd "$(dirname "$0")"
MAIN=data/raw/ctgov_raw_20261101T130137Z.json
SUPP=data/raw/ctgov_supp_raw_20261101T150223Z.json

echo "== stage 0: input checksums"
shasum -a 256 -c CHECKSUMS.sha256
[ -e data/raw/ReDO_Trials_DB_20261101.txt ] || { echo "missing ReDO snapshot: run bash scripts/00_fetch_redo.sh" >&2; exit 1; }

echo "== stage 1: screening set (supplementary filter, coder inputs)"
python3 scripts/02b_filter_supplementary.py "$SUPP"
cmp -s <(cut -d, -f1 data/processed/supp_added_to_screening.csv | sort) <(cut -d, -f1 data/processed/supp_added_to_screening_02b.csv | sort) \
  || { echo "02b does not reproduce the screening additions" >&2; exit 1; }
python3 scripts/03_build_coder_input.py "$MAIN" "$SUPP" data/processed/supp_added_to_screening.csv

echo "== stage 2: calibration samples"
python3 scripts/04_select_calibration.py
python3 scripts/04b_select_calibration_r3.py

echo "== stage 3: drug lookups for calibration candidates (cache; discovery aid only, D20)"
python3 scripts/05_lookup_drugs.py --from-file outputs/calibration/candidate_moieties.txt

echo "== stage 4: coder comparisons"
python3 scripts/07_compare_coders.py outputs/calibration                                        # round 1 (manual v1.0)
python3 scripts/07_compare_coders.py outputs/calibration_r2 schema/trial_coding.schema.v1.1.json  # round 2 (v1.1)
if [ -d outputs/calibration_r3/coderA ] && [ -n "$(ls outputs/calibration_r3/coderA)" ]; then
  python3 scripts/07_compare_coders_v2.py outputs/calibration_r3 schema/trial_coding.schema.v1.3.json  # round 3 (v1.3)
fi

echo "== tests"
python3 tests/test_origin_v2.py

echo "done (not yet included: main pass, origin derivation on adjudicated data, validation, analyses)"
