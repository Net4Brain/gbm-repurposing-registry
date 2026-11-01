"""
Step 05 - [LOOKUP] layer: regulatory and development facts for each active moiety
(coding manual section 4.1). LLM coders never supply these.

Sources (D4):
  FDA   openFDA drug/drugsfda (NDA/BLA approvals; ANDA ignored) + drug/label (indication text)
  EMA   frozen medicines report  data/raw/EMA_medicines_report_20261101.xlsx (human, non-generic)
  ChEMBL parent molecule, max phase, ATC, indications (with NCT refs), mechanism of action
  CT.gov start dates of ChEMBL-referenced non-GBM Phase 2+ trials -> date the moiety first
         reached Phase 2+ outside GBM (needed for category 3 vs 1, D12)

Output: data/lookup/v1.2/<moiety>.json (one cached file per moiety; delete nothing, re-run skips cached)

Usage: python3 scripts/05_lookup_drugs.py temozolomide metformin ...
       python3 scripts/05_lookup_drugs.py --from-file moieties.txt
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "lookup" / "v1.2"   # earlier caches kept: data/lookup/ (v1.0), data/lookup/v1.1/
EMA_XLSX = ROOT / "data" / "raw" / "EMA_medicines_report_20261101.xlsx"
CHEMBL = "https://www.ebi.ac.uk/chembl/api/data/"
FDA = "https://api.fda.gov/drug/"
CTGOV = "https://clinicaltrials.gov/api/v2/studies/"

ONCO_TEXT = re.compile(r"cancer|carcinoma|tumou?r|lymphoma|leuk[a]?emia|myeloma|melanoma|sarcoma|"
                       r"neoplas|glioma|blastoma|myelodysplastic|mesothelioma|malignan", re.I)
GLIOMA_TEXT = re.compile(r"glioma|astrocytoma|oligodendroglioma|glioblastoma", re.I)
AGNOSTIC_TEXT = re.compile(r"solid tumou?rs?.{0,200}(NTRK|MSI-H|microsatellite instability|mismatch repair|"
                           r"dMMR|TMB-H|tumor mutational burden|BRAF V600E|RET fusion|HER2)|"
                           r"(NTRK|MSI-H|dMMR|TMB-H|BRAF V600E|RET fusion).{0,200}solid tumou?rs?", re.I | re.S)
GBM_COND = re.compile(r"glioblastoma|gliosarcoma|\bGBM\b|glioma", re.I)


def get(url, **params):
    """GET with retries. A 404 means 'not found'; any other persistent failure raises, so a network
    problem is never cached as 'not found'."""
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, timeout=90)
        except requests.RequestException:
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 404:
            return None
        if r.ok:
            return r.json()
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"lookup failed after retries: {url} {params}")


def iso(d):  # 'YYYYMMDD' or 'DD/MM/YYYY' -> 'YYYY-MM-DD'
    if not d:
        return None
    d = str(d)
    if re.fullmatch(r"\d{8}", d):
        return f"{d[:4]}-{d[4:6]}-{d[6:]}"
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", d)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else d


# ------------------------------------------------------------------ FDA
def fda(moiety):
    # Active-ingredient names carry salts ("METFORMIN HYDROCHLORIDE"); a quoted phrase matches the moiety
    # inside them. openfda.generic_name misses older applications without SPL metadata (e.g. Glucophage 1995).
    # v1.2: phrase is quoted and each application must name the moiety in an ingredient (v1.1 matched
    # single tokens, e.g. "cells", "acid").
    q = f'products.active_ingredients.name:"{moiety}"'
    apps, skip = [], 0
    while True:
        page = (get(FDA + "drugsfda.json", search=q, limit=100, skip=skip) or {}).get("results", [])
        apps += page
        skip += 100
        if len(page) < 100 or skip >= 1000:
            break
    apps = [a for a in apps if any(moiety in i.get("name", "").lower()
                                   for p in a.get("products", []) for i in p.get("active_ingredients", []))]
    approvals = []
    for a in apps:
        num = a.get("application_number", "")
        if not num.startswith(("NDA", "BLA")):
            continue
        for s in a.get("submissions", []):
            if s.get("submission_type") == "ORIG" and s.get("submission_status") == "AP":
                approvals.append({"application": num, "date": iso(s.get("submission_status_date")),
                                  "brand": [p.get("brand_name") for p in a.get("products", [])][:3]})
    labels = (get(FDA + "label.json", search=f'openfda.generic_name:"{moiety}"', limit=5) or {}).get("results", [])
    indications = sorted({" ".join(l.get("indications_and_usage", []))[:3000] for l in labels} - {""})
    return {"approvals": sorted(approvals, key=lambda x: x["date"] or "9999"),
            "first_approval_date": min((a["date"] for a in approvals if a["date"]), default=None),
            "label_indications": indications,
            "query": q}


# ------------------------------------------------------------------ EMA
_EMA = None
def ema_rows():
    global _EMA
    if _EMA is None:
        ws = openpyxl.load_workbook(EMA_XLSX, read_only=True).worksheets[0]
        rows = list(ws.iter_rows(values_only=True))
        hdr = [str(h).split("\n")[0].strip() if h else "" for h in rows[8]]
        _EMA = [dict(zip(hdr, r)) for r in rows[9:] if r and r[0] == "Human"]
    return _EMA


def ema(moiety):
    m = moiety.lower()
    hits = [r for r in ema_rows()
            if r.get("Generic") != "Yes"
            and (m == str(r.get("International non-proprietary name (INN)") or "").lower().strip()
                 or m in [s.strip() for s in str(r.get("Active substance") or "").lower().split(",")])]
    out = [{"product": r["Name of medicine"], "status": r["Medicine status"],
            "authorisation_date": iso(r.get("Marketing authorisation date")),
            "atc": r.get("ATC code (human)"), "therapeutic_area": r.get("Therapeutic area (MeSH)"),
            "indication": str(r.get("Therapeutic indication") or "")[:3000],
            "url": r.get("Medicine URL")} for r in hits]
    dates = [h["authorisation_date"] for h in out if h["authorisation_date"]]
    return {"products": out, "first_authorisation_date": min(dates, default=None)}


# ------------------------------------------------------------------ ChEMBL
def chembl(moiety):
    mol = None
    for field in ("pref_name__iexact", "molecule_synonyms__molecule_synonym__iexact"):
        res = (get(CHEMBL + "molecule.json", **{field: moiety, "limit": 5}) or {}).get("molecules", [])
        if res:
            mol = res[0]
            break
    if not mol:
        return {"found": False}
    parent = (mol.get("molecule_hierarchy") or {}).get("parent_chembl_id") or mol["molecule_chembl_id"]
    if parent != mol["molecule_chembl_id"]:
        mol = get(CHEMBL + f"molecule/{parent}.json")
    inds = (get(CHEMBL + "drug_indication.json", molecule_chembl_id=parent, limit=1000) or {}).get("drug_indications", [])
    mechs = (get(CHEMBL + "mechanism.json", molecule_chembl_id=parent, limit=100) or {}).get("mechanisms", [])
    indications = [{"efo_term": i.get("efo_term"), "mesh_heading": i.get("mesh_heading"),
                    "max_phase": float(i["max_phase_for_ind"]) if i.get("max_phase_for_ind") else None,
                    "refs": [{"type": r.get("ref_type"), "id": r.get("ref_id")} for r in i.get("indication_refs", [])]}
                   for i in inds]
    return {"found": True, "chembl_id": parent, "pref_name": mol.get("pref_name"),
            "max_phase": float(mol["max_phase"]) if mol.get("max_phase") else None,
            "atc": mol.get("atc_classifications") or [],
            "molecule_type": mol.get("molecule_type"),
            "indications": indications,
            "mechanisms": [{"mechanism": m.get("mechanism_of_action"), "action_type": m.get("action_type"),
                            "target": m.get("target_chembl_id")} for m in mechs]}


def first_non_gbm_phase2(ch):
    """Earliest start date of a ChEMBL-referenced Phase 2+ trial in a non-GBM/glioma indication."""
    ncts = set()
    for i in ch.get("indications", []):
        term = f"{i['efo_term']} {i['mesh_heading']}"
        if (i["max_phase"] or 0) >= 2 and not GBM_COND.search(term):
            for r in i["refs"]:
                if r["type"] == "ClinicalTrials":
                    ncts.update(n.strip() for n in str(r["id"]).split(",") if n.strip().startswith("NCT"))
    found = []
    for n in sorted(ncts)[:200]:
        s = get(CTGOV + n, fields="NCTId,StartDate,Phase,Condition")
        if not s:
            continue
        p = s["protocolSection"]
        phases = p.get("designModule", {}).get("phases", [])
        conds = " ".join(p.get("conditionsModule", {}).get("conditions", []))
        start = p.get("statusModule", {}).get("startDateStruct", {}).get("date")
        if start and any(ph in phases for ph in ("PHASE2", "PHASE3", "PHASE4")) and not GBM_COND.search(conds):
            found.append({"nct": n, "start": start, "phases": phases})
        time.sleep(0.2)
    found.sort(key=lambda x: x["start"])
    return {"n_refs_checked": len(ncts), "earliest": found[0] if found else None}


# ------------------------------------------------------------------ flags
def flags(f, e, ch):
    texts = f["label_indications"] + [p["indication"] for p in e["products"]]
    atc = [a for a in ch.get("atc", [])] + [str(p["atc"] or "") for p in e["products"]]
    onco_atc = any(a.startswith(("L01", "L02")) for a in atc)
    first = min([d for d in (f["first_approval_date"], e["first_authorisation_date"]) if d], default=None)
    first_texts = [p["indication"] for p in e["products"] if p["authorisation_date"] == first]
    return {
        "approved_fda_or_ema": bool(first),
        "first_approval_date": first,
        # v1.2: ATC L01/L02 decides; label wording alone (e.g. dronabinol "chemotherapy-induced nausea")
        # only triggers a human check, because supportive-care drugs mention cancer too.
        "oncology_approval": onco_atc,
        "oncology_by_atc": onco_atc,
        "oncology_wording_in_label": any(ONCO_TEXT.search(t) for t in texts),
        "tumour_agnostic_text": any(AGNOSTIC_TEXT.search(t) for t in texts),
        "glioma_in_label": any(GLIOMA_TEXT.search(t) for t in texts),
        "glioma_in_first_ema_label": any(GLIOMA_TEXT.search(t) for t in first_texts),
        "needs_human_check": [],
    }


def lookup(moiety):
    moiety = moiety.strip().lower()
    path = OUT / f"{re.sub(r'[^a-z0-9]+', '_', moiety)}.json"
    if path.exists():
        return json.loads(path.read_text())
    f, e, ch = fda(moiety), ema(moiety), chembl(moiety)
    rec = {"moiety": moiety, "accessed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "fda": f, "ema": e, "chembl": ch}
    rec["first_non_gbm_phase2_trial"] = first_non_gbm_phase2(ch) if ch.get("found") else None
    rec["flags"] = fl = flags(f, e, ch)
    if not ch.get("found") and not fl["approved_fda_or_ema"]:
        fl["needs_human_check"].append("not found in FDA, EMA or ChEMBL (check name mapping)")
    if fl["approved_fda_or_ema"] and fl["oncology_wording_in_label"] and not fl["oncology_by_atc"]:
        fl["needs_human_check"].append("cancer wording in label but no L01/L02 ATC: oncology drug or supportive use?")
    if fl["glioma_in_label"]:
        fl["needs_human_check"].append("glioma in label: confirm established / glioma-developed / glioma_label")
    if (ch.get("max_phase") or 0) >= 4 and not fl["approved_fda_or_ema"]:
        fl["needs_human_check"].append("ChEMBL max_phase 4 but no FDA/EMA approval found (other regulator?)")
    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=1))
    return rec


if __name__ == "__main__":
    args = sys.argv[1:]
    names = Path(args[1]).read_text().split("\n") if args[:1] == ["--from-file"] else args
    for n in filter(None, (x.strip() for x in names)):
        try:
            r = lookup(n)
        except RuntimeError as e:
            print(f"{n:22} LOOKUP FAILED (not cached, re-run later): {e}")
            continue
        fl = r["flags"]
        p2 = (r["first_non_gbm_phase2_trial"] or {}).get("earliest")
        print(f"{n:22} approved={fl['approved_fda_or_ema']!s:5} first={fl['first_approval_date']} "
              f"onco={fl['oncology_approval']!s:5} agnostic={fl['tumour_agnostic_text']!s:5} "
              f"glioma={fl['glioma_in_label']!s:5} chembl_max={r['chembl'].get('max_phase')} "
              f"p2_nonGBM={p2['start'] if p2 else None} check={fl['needs_human_check']}")
