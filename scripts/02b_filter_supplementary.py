"""
Step 02b - Rule-based filter for the supplementary search (D17; scripted per D26).

A supplementary record joins the screening set only if a glioblastoma term appears in its
title, conditions or INCLUSION criteria (eligibility text before the exclusion heading):
glioblastoma, gliosarcoma, GBM (not "anti-GBM"), IDH-wildtype, grade 4 astrocytoma/glioma.

Outputs:
  data/processed/supp_added_to_screening_02b.csv   records kept (nct_id, gbm_term_location, brief_title)
  data/processed/supp_rejected_02b.csv             records rejected, with any GBM term found elsewhere
                                                   and basket/solid-tumour wording (for the false-negative audit)

Usage: python3 scripts/02b_filter_supplementary.py data/raw/ctgov_supp_raw_20261101T150223Z.json
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GBM = re.compile(r"(?<!anti-)(?<!anti )\b(glioblastomas?|gliosarcomas?|GBMs?|IDH[- ]?wild[- ]?type|"
                 r"grade (4|IV) (astrocytoma|glioma)|(astrocytoma|glioma),? (WHO )?grade (4|IV))\b", re.I)
EXCL_HEAD = re.compile(r"exclusion criteria", re.I)
BASKET = re.compile(r"solid tumou?rs?|basket|tumou?r[- ]agnostic|any (advanced|metastatic) (cancer|malignancy)|"
                    r"primary (CNS|brain) (tumou?r|malignanc)|brain tumou?rs?|CNS tumou?rs?", re.I)


def fields(s):
    p = s["protocolSection"]
    title = " ".join(filter(None, [p["identificationModule"].get("briefTitle"), p["identificationModule"].get("officialTitle")]))
    conds = " ; ".join(p.get("conditionsModule", {}).get("conditions", []))
    elig = p.get("eligibilityModule", {}).get("eligibilityCriteria", "") or ""
    m = EXCL_HEAD.search(elig)
    incl, excl = (elig[:m.start()], elig[m.start():]) if m else (elig, "")
    other = " ".join([p.get("descriptionModule", {}).get("briefSummary", "") or "",
                      p.get("descriptionModule", {}).get("detailedDescription", "") or "",
                      " ".join(p.get("conditionsModule", {}).get("keywords", []))])
    return p["identificationModule"]["nctId"], p["identificationModule"].get("briefTitle", ""), title, conds, incl, excl, other


def main(src):
    kept, rejected = [], []
    for s in json.load(open(src)):
        nct, brief, title, conds, incl, excl, other = fields(s)
        loc = next((name for name, txt in (("title", title), ("conditions", conds), ("inclusion criteria", incl)) if GBM.search(txt)), None)
        if loc:
            kept.append({"nct_id": nct, "gbm_term_location": loc, "brief_title": brief})
        else:
            elsewhere = [name for name, txt in (("exclusion criteria", excl), ("description/keywords", other)) if GBM.search(txt)]
            basket = sorted({m.group(0).lower() for m in BASKET.finditer(" ".join([title, conds, incl, other]))})
            rejected.append({"nct_id": nct, "brief_title": brief, "gbm_term_elsewhere": "; ".join(elsewhere),
                             "basket_or_brain_wording": "; ".join(basket)})
    out = ROOT / "data" / "processed"
    for name, rows in (("supp_added_to_screening_02b.csv", kept), ("supp_rejected_02b.csv", rejected)):
        with open(out / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(sorted(rows, key=lambda r: r["nct_id"]))
    print(f"kept {len(kept)}, rejected {len(rejected)}")


if __name__ == "__main__":
    main(sys.argv[1])
