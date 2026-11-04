"""
Step 05d - Search ClinicalTrials.gov for prior NON-GBM Phase 2+ development of candidate agents (D20, category 3 vs 1).
Post-registration processing step. Complements 05_lookup_drugs.py, whose development search used only
ChEMBL-referenced trials and so found nothing for agents missing from ChEMBL (mostly code-named agents).

For each agent: query the ClinicalTrials.gov API v2 by intervention name, keep studies that
  - list the agent among their interventions (name or other names, ignoring case, spaces and hyphens),
  - are Phase 2, 2/3, 3 or 4,
  - have no glioma condition (same pattern as 05: glioblastoma, gliosarcoma, GBM, glioma),
  - started before the agent's earliest eligible GBM trial (origin_agents_D32.csv).
The earliest such study becomes a DRAFT development row (reviewed_by empty); otherwise a `none_found` row records the
search. Live registry data (searched today), not the 1 November snapshot; the query date is in `source`.

Output (new file; refuses to overwrite): data/reference/development_events_draft_D32_ctgov.csv
Usage: python3 scripts/05d_search_development_ctgov.py agents.txt
"""
import csv
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reference" / "development_events_draft_D32_ctgov.csv"
API = "https://clinicaltrials.gov/api/v2/studies"
GLIOMA = re.compile(r"glioblastoma|gliosarcoma|\bGBM\b|glioma", re.I)
PHASES = {"PHASE2", "PHASE3", "PHASE4"}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def get(params):
    for attempt in range(4):
        try:
            r = requests.get(API, params=params, timeout=90)
            if r.ok:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"search failed: {params}")


def earliest_starts():
    out = {}
    for r in csv.DictReader(open(ROOT / "outputs" / "main" / "origin_agents_D32.csv")):
        m = r["active_moiety"]
        out[m] = min(out.get(m, "9999"), r["trial_start"])
    return out


def search(agent, before):
    key = norm(agent)
    hits, token = [], None
    for _ in range(10):
        p = {"query.intr": agent, "pageSize": 100,
             "fields": "NCTId,BriefTitle,Condition,Phase,StartDate,InterventionName,InterventionOtherName"}
        if token:
            p["pageToken"] = token
        d = get(p)
        for s in d.get("studies", []):
            ps = s["protocolSection"]
            names = []
            for i in ps.get("armsInterventionsModule", {}).get("interventions", []):
                names += [i.get("name", "")] + i.get("otherNames", [])
            if not any(key and key in norm(n) for n in names):
                continue
            phases = set(ps.get("designModule", {}).get("phases", []))
            conds = ps.get("conditionsModule", {}).get("conditions", [])
            start = (ps.get("statusModule", {}).get("startDateStruct") or {}).get("date", "")
            if phases & PHASES and start and start < before and not any(GLIOMA.search(c) for c in conds) \
                    and not GLIOMA.search(ps["identificationModule"].get("briefTitle", "")):
                hits.append({"nct": ps["identificationModule"]["nctId"], "start": start, "phases": sorted(phases),
                             "conditions": "; ".join(conds)[:200]})
        token = d.get("nextPageToken")
        if not token:
            break
        time.sleep(0.3)
    return sorted(hits, key=lambda h: h["start"])


def main(list_file):
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite")
    starts = earliest_starts()
    today = date.today().isoformat()
    rows = []
    for agent in [l.strip().lower() for l in open(list_file) if l.strip()]:
        T = starts[agent]
        hits = search(agent, T)
        if hits:
            h = hits[0]
            ph = "3" if {"PHASE3", "PHASE4"} & set(h["phases"]) else "2"
            rows.append({"moiety": agent, "phase": ph, "indication": h["conditions"], "date_lo": h["start"],
                         "date_hi": h["start"], "source": f"ClinicalTrials.gov {h['nct']} (searched {today})",
                         "reviewed_by": "",
                         "check": f"confirm same agent and non-glioma indication; {len(hits)} non-glioma Phase 2+ "
                                  f"started before {T}: " + ", ".join(x["nct"] for x in hits[:5])})
        else:
            rows.append({"moiety": agent, "phase": "none_found", "indication": "", "date_lo": "", "date_hi": "",
                         "source": f"ClinicalTrials.gov intervention search '{agent}' (searched {today})",
                         "reviewed_by": "",
                         "check": f"no non-glioma Phase 2+ before {T} found under this name; check code-name "
                                  f"synonyms and literature"})
        print(f"{agent:32} T={T} hits={len(hits)} {hits[0]['nct'] + ' ' + hits[0]['start'] if hits else ''}")
        time.sleep(0.3)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"agents {len(rows)}; with prior non-glioma Phase 2+: {sum(r['phase'] != 'none_found' for r in rows)}")


if __name__ == "__main__":
    main(sys.argv[1])
