"""
Tests for scripts/06_derive_origin_v2.py with small FIXTURE tables (test data, not the study's
reference tables). Covers the two errors found by the 2026-11-02 methods review, plus the
UNRESOLVED gate, date intervals, glioma-first and the panel rule.

Run: python3 tests/test_origin_v2.py
"""
import csv
import importlib.util
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("o2", ROOT / "scripts" / "06_derive_origin_v2.py")
o2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(o2)

EVENTS = """moiety,jurisdiction,event_type,indication,oncology,tumour_agnostic,glioma,date_lo,date_hi,source,source_url,reviewed_by,review_date
dabrafenib,FDA,original,BRAF V600E melanoma,yes,no,no,2013-05-29,2013-05-29,fixture,,test,2026-11-02
dabrafenib,FDA,new_indication,BRAF V600E unresectable or metastatic solid tumours (with trametinib),yes,yes,no,2022-06-22,2022-06-22,fixture,,test,2026-11-02
dabrafenib,FDA,new_indication,BRAF V600E paediatric low-grade glioma,yes,no,yes,2023-03-16,2023-03-16,fixture,,test,2026-11-02
pembrolizumab,FDA,original,melanoma,yes,no,no,2014-09-04,2014-09-04,fixture,,test,2026-11-02
pembrolizumab,FDA,new_indication,MSI-H/dMMR solid tumours,yes,yes,no,2017-05-23,2017-05-23,fixture,,test,2026-11-02
metformin,FDA,original,type 2 diabetes,no,no,no,1995-03,1995-03,fixture,,test,2026-11-02
vorasidenib,FDA,original,IDH-mutant grade 2 astrocytoma or oligodendroglioma,yes,no,yes,2024-08-06,2024-08-06,fixture,,test,2026-11-02
newdrug,FDA,original,lung cancer,yes,no,no,2021,2021,fixture,,test,2026-11-02
unchecked,FDA,original,melanoma,yes,no,no,2015-01-01,2015-01-01,fixture,,,
"""
DEV = """moiety,phase,indication,date_lo,date_hi,source,reviewed_by
vorasidenib,1,IDH-mutant solid tumours,2015-06,2015-06,fixture,test
abc123,2,pancreatic cancer,2018-01-10,2018-01-10,fixture,test
xyz999,none_found,,,,documented search,test
"""


def table(text):
    rows = {}
    for r in csv.DictReader(io.StringIO(text)):
        if r.get("phase") != "none_found":
            r["date_lo"], _ = o2.iso(r["date_lo"])
            _, r["date_hi"] = o2.iso(r["date_hi"] or r["date_lo"])
        rows.setdefault(r["moiety"], []).append(r)
    return rows


E, D = table(EVENTS), table(DEV)
c = lambda m, T, pwl="": o2.classify(m, T, E, D, pwl)
fails = []


def check(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


# review R2: dabrafenib in 2020 is 2b WITHOUT the tumour-agnostic flag (approval came 2022-06-22)
r = c("dabrafenib", "2020-01-01")
check("dabrafenib 2020 category", r["category"], "2b")
check("dabrafenib 2020 not agnostic", "tumour_agnostic_at_T" in r["flags"], False)
r = c("dabrafenib", "2023-06-01")
check("dabrafenib 2023 agnostic", "tumour_agnostic_at_T" in r["flags"], True)
check("dabrafenib 2023 glioma label (not first)", "glioma_label_at_T" in r["flags"], True)
check("dabrafenib 2023 needs population decision", any("population_within_label: needs" in f for f in r["flags"]), True)
check("dabrafenib 2023 population yes", "population_within_label" in c("dabrafenib", "2023-06-01", "yes")["flags"], True)
# review R2: pembrolizumab tumour-agnostic from 2017-05-23
check("pembro 2017-05-22", "tumour_agnostic_at_T" in c("pembrolizumab", "2017-05-22")["flags"], False)
check("pembro 2017-05-23", "tumour_agnostic_at_T" in c("pembrolizumab", "2017-05-23")["flags"], True)
# non-oncology
check("metformin 2a", c("metformin", "2020-01-01")["category"], "2a")
# glioma-first
check("vorasidenib 2025", c("vorasidenib", "2025-01-01")["category"], "GLIOMA_DEVELOPED")
check("vorasidenib 2020 unapproved, prior phase 1 only -> 1", c("vorasidenib", "2020-01-01")["category"], "1")
check("vorasidenib 2020 axis", c("vorasidenib", "2020-01-01")["prior_dev_phase"], "1")
# category 3 and UNRESOLVED
check("abc123 2019 -> 3", c("abc123", "2019-01-01")["category"], "3")
check("abc123 2017 -> 1", c("abc123", "2017-01-01")["category"], "1")
check("unknown agent -> UNRESOLVED", c("nothing_known", "2021-01-01")["category"], "UNRESOLVED")
check("documented none_found -> 1", c("xyz999", "2021-01-01")["category"], "1")
check("unreviewed event -> UNRESOLVED", c("unchecked", "2021-01-01")["category"], "UNRESOLVED")
# year-only approval date: T inside the interval -> conservative + date_sensitive
r = c("newdrug", "2021-06-01")
check("newdrug mid-2021 conservative", r["category"], "UNRESOLVED")   # unapproved, no dev evidence
check("newdrug mid-2021 date_sensitive", any(f.startswith("date_sensitive") for f in r["flags"]), True)
check("newdrug 2022 -> 2b", c("newdrug", "2022-01-01")["category"], "2b")
# panel and established
check("panel", c("unspecified_approved_panel", "2021-01-01")["category"], "2_panel")
check("established", c("temozolomide", "2021-01-01")["category"], "ESTABLISHED")
# start-date parsing
check("iso month", o2.iso("2021-02"), ("2021-02-01", "2021-02-28"))

print("\n".join(fails) if fails else "all tests passed")
sys.exit(1 if fails else 0)
