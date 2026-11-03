"""
Step 05c - Draft the dated regulatory and development event tables (D20) from the cached lookups
(data/lookup/v1.2/<moiety>.json written by 05_lookup_drugs.py). Post-registration processing step.

The output is a DRAFT for human review, not evidence. Every row has reviewed_by empty, so
06_derive_origin_v2.py returns UNRESOLVED for every candidate until XL reviews the rows (D20a, D21, D26).
The `check` column says what the reviewer must confirm.

Known limits of the draft, listed in `check`:
  - FDA rows are ORIGINAL approvals (drugsfda ORIG submissions). The date an ONCOLOGY or tumour-agnostic indication
    was added by a supplement is not in drugsfda; when a moiety has both oncology and non-oncology use, or a
    tumour-agnostic indication, the reviewer must date that indication from the label history.
  - oncology / tumour_agnostic / glioma come from today's ATC code and label text, not from the label at the
    event date.
  - Development rows: the earliest ChEMBL-referenced non-GBM Phase 2+ trial (start date from ClinicalTrials.gov),
    or `none_found` when that search found nothing. Earlier Phase 1 work and non-ChEMBL trials are not searched.

Outputs (new files; refuses to overwrite):
  data/reference/regulatory_events_draft_D32.csv   same columns as regulatory_events.csv, plus `check`
  data/reference/development_events_draft_D32.csv  same columns as development_events.csv, plus `check`

Usage: python3 scripts/05c_draft_regulatory_events.py moieties.txt [tag]
  A line "moiety=lookup_name" drafts rows for `moiety` from the cache of `lookup_name` (alias, e.g. a code name
  or INN variant whose approved name differs). With `tag`, outputs are *_draft_D32_<tag>.csv.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "lookup" / "v1.2"
REF = ROOT / "data" / "reference"
REG_COLS = ["moiety", "jurisdiction", "event_type", "indication", "oncology", "tumour_agnostic", "glioma",
            "date_lo", "date_hi", "source", "source_url", "reviewed_by", "review_date", "check"]
DEV_COLS = ["moiety", "phase", "indication", "date_lo", "date_hi", "source", "reviewed_by", "check"]
ONCO_TEXT = re.compile(r"cancer|carcinoma|tumou?r|lymphoma|leuk[a]?emia|myeloma|melanoma|sarcoma|neoplas|glioma|"
                       r"blastoma|myelodysplastic|mesothelioma|malignan", re.I)
GLIOMA_TEXT = re.compile(r"glioma|astrocytoma|oligodendroglioma|glioblastoma", re.I)
AGNOSTIC_TEXT = re.compile(r"solid tumou?rs?.{0,200}(NTRK|MSI-H|microsatellite instability|mismatch repair|dMMR|"
                           r"TMB-H|tumor mutational burden|BRAF V600E|RET fusion|HER2)|(NTRK|MSI-H|dMMR|TMB-H|"
                           r"BRAF V600E|RET fusion).{0,200}solid tumou?rs?", re.I | re.S)


def yn(b):
    return "yes" if b else "no"


def main(list_file, tag=""):
    sfx = f"_{tag}" if tag else ""
    reg_out, dev_out = REF / f"regulatory_events_draft_D32{sfx}.csv", REF / f"development_events_draft_D32{sfx}.csv"
    for p in (reg_out, dev_out):
        if p.exists():
            sys.exit(f"{p} exists; refusing to overwrite")
    reg, dev, missing = [], [], []
    for line in [l.strip().lower() for l in open(list_file) if l.strip()]:
        m, _, alias = line.partition("=")
        m, alias = m.strip(), (alias.strip() or m.strip())
        path = CACHE / f"{re.sub(r'[^a-z0-9]+', '_', alias)}.json"
        if not path.exists():
            missing.append(m)
            continue
        r = json.loads(path.read_text())
        f, e, ch, fl = r["fda"], r["ema"], r["chembl"], r["flags"]
        onco = fl["oncology_approval"]
        label = " ".join(f["label_indications"])
        mixed = onco and bool(label) and not ONCO_TEXT.search(label[:400])
        base_check = [f"looked up as alias '{alias}': confirm same active moiety"] if alias != m else []
        if fl["oncology_wording_in_label"] and not onco:
            base_check.append("cancer wording but no L01/L02 ATC: oncology or supportive use?")
        if mixed or (ch.get("atc") and onco and any(not a.startswith(("L01", "L02")) for a in ch["atc"])):
            base_check.append("has non-oncology and oncology uses: date the first oncology indication")
        for a in f["approvals"]:
            check = list(base_check)
            if AGNOSTIC_TEXT.search(label):
                check.append("tumour-agnostic indication in current label: date it (supplement)")
            if GLIOMA_TEXT.search(label):
                check.append("glioma in current label: confirm and date")
            check.append("indication text is today's label, not the label at this date")
            reg.append({"moiety": m, "jurisdiction": "FDA", "event_type": "original_approval",
                        "indication": label[:300], "oncology": yn(onco),
                        "tumour_agnostic": yn(bool(AGNOSTIC_TEXT.search(label))),
                        "glioma": yn(bool(GLIOMA_TEXT.search(label))), "date_lo": a["date"], "date_hi": a["date"],
                        "source": f"openFDA drugsfda {a['application']} ({'; '.join(x for x in a['brand'] if x)})",
                        "source_url": f"https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={a['application'][3:]}",
                        "reviewed_by": "", "review_date": "", "check": "; ".join(check)})
        for p in e["products"]:
            if not p["authorisation_date"]:
                continue
            txt = p["indication"] or ""
            check = list(base_check)
            if AGNOSTIC_TEXT.search(txt):
                check.append("tumour-agnostic indication: date it (variation)")
            if GLIOMA_TEXT.search(txt):
                check.append("glioma in indication: confirm and date")
            check.append(f"EMA status {p['status']}; indication text is the current one")
            reg.append({"moiety": m, "jurisdiction": "EMA", "event_type": "marketing_authorisation",
                        "indication": txt[:300], "oncology": yn(str(p["atc"] or "").startswith(("L01", "L02")) or onco),
                        "tumour_agnostic": yn(bool(AGNOSTIC_TEXT.search(txt))), "glioma": yn(bool(GLIOMA_TEXT.search(txt))),
                        "date_lo": p["authorisation_date"], "date_hi": p["authorisation_date"],
                        "source": f"EMA medicines report 2026-11-01: {p['product']}", "source_url": p.get("url") or "",
                        "reviewed_by": "", "review_date": "", "check": "; ".join(check)})
        if not fl["approved_fda_or_ema"]:
            note = "; ".join(fl["needs_human_check"]) or "no FDA/EMA approval found"
            reg.append({"moiety": m, "jurisdiction": "FDA+EMA", "event_type": "none_found", "indication": "",
                        "oncology": "", "tumour_agnostic": "", "glioma": "", "date_lo": "", "date_hi": "",
                        "source": "openFDA drugsfda + EMA medicines report 2026-11-01 + ChEMBL", "source_url": "",
                        "reviewed_by": "", "review_date": "",
                        "check": f"confirm unapproved (name or code mapping); {note}"})
        p2 = (r.get("first_non_gbm_phase2_trial") or {}).get("earliest")
        if p2:
            ph = "3" if "PHASE3" in p2["phases"] or "PHASE4" in p2["phases"] else "2"
            dev.append({"moiety": m, "phase": ph, "indication": "non-GBM (ChEMBL-referenced trial)",
                        "date_lo": p2["start"], "date_hi": p2["start"], "source": f"ClinicalTrials.gov {p2['nct']}",
                        "reviewed_by": "",
                        "check": "confirm non-glioma indication; search for earlier Phase 2+ trials outside ChEMBL"})
        else:
            dev.append({"moiety": m, "phase": "none_found", "indication": "", "date_lo": "", "date_hi": "",
                        "source": f"ChEMBL {ch.get('chembl_id') or 'not found'}; max_phase {ch.get('max_phase')}",
                        "reviewed_by": "",
                        "check": "search ClinicalTrials.gov and literature for non-GBM Phase 2+ before the trial start"})
    for out, cols, rows in ((reg_out, REG_COLS, reg), (dev_out, DEV_COLS, dev)):
        with open(out, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    approved = {r["moiety"] for r in reg if r["event_type"] != "none_found"}
    print(f"moieties {len(approved) + len({r['moiety'] for r in reg if r['event_type'] == 'none_found'})}, "
          f"with FDA/EMA events {len(approved)}, regulatory rows {len(reg)}, development rows {len(dev)}, "
          f"not in cache {len(missing)}: {missing}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
