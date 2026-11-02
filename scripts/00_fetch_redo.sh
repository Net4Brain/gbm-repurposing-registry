#!/usr/bin/env bash
# ReDO_Trials_DB (Pantziarka et al. 2021, doi:10.3389/fphar.2021.790952) is not redistributed here
# because its licence is not stated. This fetches the current file and compares it with the frozen
# copy used in the study (retrieved 2026-11-01). It is REQUIRED by step 04 (calibration sample) and
# by the external validation (D10). A mismatch is a fatal error: the database has changed since.
set -euo pipefail
cd "$(dirname "$0")/.."
EXPECTED=00b3113d0fb0fd0ffd24b6c5323b25307002b3cc5c2945a80f47f25aa208197d
OUT=data/raw/ReDO_Trials_DB_20261101.txt
[ -e "$OUT" ] && { echo "$OUT already present"; } || curl -sL -o "$OUT" https://data.tp53.org.uk/ReDO_Trials_DB.txt
GOT=$(shasum -a 256 "$OUT" | cut -d' ' -f1)
if [ "$GOT" = "$EXPECTED" ]; then
  echo "checksum OK (identical to study snapshot)"
else
  echo "ERROR: $OUT differs from the study snapshot (got $GOT, expected $EXPECTED)." >&2
  echo "The download URL is mutable; the frozen hash is the reference. Step 04 (calibration sample) needs the" >&2
  echo "frozen version: obtain it from the authors or the study archive and place it at $OUT." >&2
  exit 1
fi
