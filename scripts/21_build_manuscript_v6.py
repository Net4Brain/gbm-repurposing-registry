"""
Step 21 - Build manuscript v6 from v5 (all v5 changes accepted by XL) with tracked changes (author XL.C).
Post-registration processing step.

Input : ../GBM_registry_NOA_structure_v5.docx (not modified)
Output: ../GBM_registry_NOA_structure_v6.docx (refuses to overwrite)
Adds the active-pipeline subset (D41) to Results, the status-reconstruction rule to Amendments after registration,
and updates the decision-log range. Numbers come from outputs/analysis_D40/ (script 20).
Usage: python3 scripts/21_build_manuscript_v6.py
"""
import csv
import html
import importlib.util
import re
import shutil
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("b", ROOT / "scripts" / "19_build_manuscript_v5.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
B.DATE = "2026-11-04T18:00:00Z"
SRC = ROOT.parent / "GBM_registry_NOA_structure_v5.docx"
DST = ROOT.parent / "GBM_registry_NOA_structure_v6.docx"
AN = ROOT / "outputs" / "analysis_D40"


def insert_before(p, anchor, new):
    """Tracked insertion of `new` immediately before `anchor` (inside one run)."""
    for r in B.runs_of(p):
        t = html.unescape(B.text_of(r))
        if anchor in t:
            i = t.index(anchor)
            rp = B.rpr_of(r)
            parts = [f'<w:r>{rp}<w:t xml:space="preserve">{B.esc(t[:i])}</w:t></w:r>'] if t[:i] else []
            parts += [B.ins_run(new, rp), f'<w:r>{rp}<w:t xml:space="preserve">{B.esc(t[i:])}</w:t></w:r>']
            return p.replace(r, "".join(parts), 1)
    raise ValueError(f"anchor not found: {anchor[:60]}")


def texts():
    st = list(csv.DictReader(open(AN / "status_at_index_D41.csv")))
    c = Counter(r["class"] for r in st)
    g = Counter(r["origin_group"] for r in st if r["class"] == "active")
    res = list(csv.DictReader(open(AN / "active_subset_results.csv")))
    h, s = res[0], res[1]
    ag = dict(re.findall(r"(agents|repurposing|2a|2b|3|1) (\d+)", res[2]["note"]))
    pct, *ci = re.search(r"\(([\d.]+)%, ([\d.]+) to ([\d.]+)\)", res[2]["note"]).groups()
    unk, stale = c["not_reconstructable (status unknown)"], c["not_reconstructable (no update within 2 years)"]
    m = lambda v: str(v).replace("-", "−")
    active = (f"Recruitment status on 31 July 2026 was reconstructed from the version history of all 280 cohort trials: "
              f"{c['active']} were active, {c['inactive']} inactive and {unk + stale} could not be reconstructed ({unk} of "
              f"unknown status and {stale} whose active status had not been updated for more than two years). The active "
              f"subset comprised {g['repurposing_containing']} repurposing-containing, {g['repositioning_only']} "
              f"repositioning-only and {g['de_novo_only']} de novo-only trials, and one that could not be assigned. Of its "
              f"{ag['agents']} unique candidate agents, {ag['repurposing']} ({pct}%; 95% CI {ci[0]}–{ci[1]}) were "
              f"approved-drug repurposing ({ag['2a']} non-oncology, {ag['2b']} oncology), {ag['3']} investigational "
              f"repositioning and {ag['1']} de novo. Candidate-matched molecular selection was used in {h['de_novo_selected']} "
              f"of {h['de_novo_n']} de novo-only trials ({h['de_novo_pct']}%) and {h['repurposing_selected']} of "
              f"{h['repurposing_n']} repurposing-containing trials ({h['repurposing_pct']}%), a risk difference of "
              f"{h['risk_difference_pp']} percentage points (95% CI {m(h['ci_low_pp'])} to {h['ci_high_pp']}); counting the "
              f"trials whose status could not be reconstructed as active gave {s['risk_difference_pp']} points "
              f"({m(s['ci_low_pp'])} to {s['ci_high_pp']}).")
    amend = ("Sixth, status on the index date was taken from each record’s ClinicalTrials.gov version history (the last "
             "version dated on or before 31 July 2026); an active status not updated in the two years before the index "
             "date was treated as not reconstructable, following the registry’s own rule for unknown status, and status "
             "changes are dated by when they were reported (D41). ")
    return active, amend


def main():
    if DST.exists():
        sys.exit(f"{DST} exists; refusing to overwrite")
    active, amend = texts()
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(SRC) as z:
        z.extractall(tmp)
    doc = (tmp / "word" / "document.xml").read_text(encoding="utf8")
    assert "<w:ins " not in doc and "<w:del " not in doc, "v5 still has tracked changes"
    spans = [(m.start(), m.end()) for m in re.finditer(r"<w:p[ >].*?</w:p>", doc, re.S)]
    P = [doc[a:b] for a, b in spans]
    T = lambda i: html.unescape("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", P[i])))
    new = list(P)

    def at(i, expect):
        assert T(i).startswith(expect), (i, T(i)[:80])
        return i

    i = at(26, "The protocol, coding manual")
    new[i] = B.replace_in_paragraph(P[i], "D1–D40", "D1–D41")
    i = at(71, "Second, two sensitivity analyses")
    new[i] = insert_before(P[i], "All analyses used Python 3.13", amend)
    i = at(92, "Of 15 glioma trials in ReDO_Trials_DB")
    new[i] = B.replace_in_paragraph(P[i], "[Probabilistic misclassification analysis and the active-on-index-date subset: TO ADD.]",
                                    "[Probabilistic misclassification analysis: TO ADD.]") + B.new_paragraph(active)
    out, last = [], 0
    for (a, b), p in zip(spans, new):
        out += [doc[last:a], p]
        last = b
    out.append(doc[last:])
    (tmp / "word" / "document.xml").write_text("".join(out), encoding="utf8")
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(tmp.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(tmp).as_posix())
    shutil.rmtree(tmp)
    print(f"wrote {DST.name}: {B._id[0] - 9000} tracked-change ids by {B.AUTHOR}")
    print(active)


if __name__ == "__main__":
    main()
