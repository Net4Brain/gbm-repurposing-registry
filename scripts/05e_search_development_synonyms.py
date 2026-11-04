"""
Step 05e - Repeat the 05d ClinicalTrials.gov development search under each agent's OTHER NAMES (code names, INNs,
brand names) from the curated table data/reference/agent_synonyms_D32.csv (source per row: the GBM trial record's
"other names", or drug knowledge to verify). Post-registration processing step, for agents where 05d found nothing under the moiety name.

The same filters as 05d apply (agent listed among the interventions, Phase 2+, no glioma condition or title, start
before the agent's earliest eligible GBM trial). Names of 3 characters or fewer and generic class words are skipped.
Output (new file; refuses to overwrite): data/reference/development_events_draft_D32_synonyms.csv, one row per agent:
the earliest hit across synonyms, or `none_found` listing the names searched. All rows unreviewed.

Usage: python3 scripts/05e_search_development_synonyms.py agents.txt
"""
import csv
import importlib.util
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reference" / "development_events_draft_D32_synonyms.csv"
spec = importlib.util.spec_from_file_location("d", ROOT / "scripts" / "05d_search_development_ctgov.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
SKIP = re.compile(r"^(placebo|drug|injection|tablet|capsule|vaccine|antibody|monoclonal antibody|bispecific antibody|"
                  r"standard of care|chemotherapy|radiotherapy|other|treatment|arm [a-z0-9]+|group [a-z0-9]+|cohort [a-z0-9]+|"
                  r"experimental|dose escalation|dose expansion)$", re.I)
PROCEDURE = re.compile(r"radiat|radiosurg|radiotherap|surgery|resection|biopsy|imaging|\bscan\b", re.I)
MAX_WORDS = 4   # longer strings are arm or intervention descriptions, not names


def synonyms(agent):
    """Curated synonyms (data/reference/agent_synonyms_D32.csv). Automatic extraction from the trial records was
    tried and rejected: intervention lines also carry arm descriptions, partner drugs and class words."""
    return sorted({r["synonym"] for r in csv.DictReader(open(ROOT / "data" / "reference" / "agent_synonyms_D32.csv"))
                   if r["active_moiety"] == agent})


def main(list_file):
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite")
    starts = d.earliest_starts()
    today = date.today().isoformat()
    rows = []
    for agent in [l.strip().lower() for l in open(list_file) if l.strip()]:
        T = starts[agent]
        syns = synonyms(agent)
        hits = []
        failed = []
        for s in syns:
            try:
                for h in d.search(s, T):
                    hits.append(dict(h, name=s))
            except RuntimeError:
                failed.append(s)
            time.sleep(0.3)
        hits.sort(key=lambda h: h["start"])
        if hits:
            h = hits[0]
            ph = "3" if {"PHASE3", "PHASE4"} & set(h["phases"]) else "2"
            rows.append({"moiety": agent, "phase": ph, "indication": h["conditions"], "date_lo": h["start"],
                         "date_hi": h["start"], "source": f"ClinicalTrials.gov {h['nct']} as '{h['name']}' (searched {today})",
                         "reviewed_by": "",
                         "check": f"confirm '{h['name']}' is the same agent and the indication is not glioma; hits: "
                                  + ", ".join(sorted({x['nct'] for x in hits})[:5])})
        else:
            rows.append({"moiety": agent, "phase": "none_found", "indication": "", "date_lo": "", "date_hi": "",
                         "source": f"ClinicalTrials.gov intervention search under: {'; '.join(syns) or '(no other names)'} "
                                   f"(searched {today})", "reviewed_by": "",
                         "check": f"no non-glioma Phase 2+ before {T} under the moiety name (05d) or these names"
                                  + (f"; search failed for: {'; '.join(failed)}" if failed else "")})
        print(f"{agent:32} T={T} names={len(syns)} hits={len(hits)} {hits[0]['nct'] + ' ' + hits[0]['start'] + ' ' + hits[0]['name'] if hits else ''}")
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"agents {len(rows)}; with a hit under a synonym: {sum(r['phase'] != 'none_found' for r in rows)}")


if __name__ == "__main__":
    main(sys.argv[1])
