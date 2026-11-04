"""
Step 23 - Build manuscript v7 from v6 with tracked changes (author XL.C). Post-registration processing step.

Input : ../GBM_registry_NOA_structure_v6.docx (not modified; its own 7 tracked changes by XL.C are still pending
        and are kept as they are)
Output: ../GBM_registry_NOA_structure_v7.docx (refuses to overwrite)
Adds:
  - D42 pathway analysis: an exploratory Results subsection, an Amendments paragraph (Seventh: origin rule stated,
    naming eflornithine and retifanlimab; Eighth: D43), reference 15 (TCGA core pathways), Supplementary Table S6
    and Supplementary Figure S1 in the supplementary list (with S5, which the text already cites)
  - D43 corrections: Table 2 control-arm row (registered comparator types) and enrolment (actual and anticipated
    separately), the matching Results sentence, "repositioning, no repurposed candidate" wording, and
    "molecularly informed design" described as a proxy
Two edits fall inside v6's pending insertions (the decision-log range in the data paragraph and the
active-subset paragraph). They are made in the inserted text itself, so they stay one pending insertion by XL.C.
Every new change is a w:ins/w:del by XL.C dated 2026-11-04T21:00:00Z. Rejecting the changes of that date gives v6;
rejecting all changes gives v5.
Numbers come from outputs/analysis_D40/ (scripts 18b, 22, 22d) and are checked against those files.
Usage: python3 scripts/23_build_manuscript_v7.py
"""
import csv
import html
import importlib.util
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("b", ROOT / "scripts" / "19_build_manuscript_v5.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
B.DATE = "2026-11-04T21:00:00Z"
B._id[0] = 20000
SRC = ROOT.parent / "GBM_registry_NOA_structure_v6.docx"
DST = ROOT.parent / "GBM_registry_NOA_structure_v7.docx"
AN = ROOT / "outputs" / "analysis_D40"
SUP = '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'


def edit_pending_insertion(p, old, new):
    """Change text inside a run that is already a pending insertion (v6), without nesting a new change."""
    for m in re.finditer(r"<w:ins [^>]*>.*?</w:ins>", p, re.S):
        if html.escape(old, quote=False) in m.group(0):
            return p.replace(m.group(0), m.group(0).replace(html.escape(old, quote=False), html.escape(new, quote=False), 1), 1)
    raise ValueError(f"pending insertion not found: {old}")


def paragraph(parts, style=None):
    """New tracked paragraph from (text, superscript?) parts."""
    ppr = f'<w:pStyle w:val="{style}"/>' if style else ""
    mark = f'<w:ins w:id="{B.nid()}" w:author="{B.AUTHOR}" w:date="{B.DATE}"/>'
    return f"<w:p><w:pPr>{ppr}<w:rPr>{mark}</w:rPr></w:pPr>" + "".join(B.ins_run(t, SUP if s else "") for t, s in parts) + "</w:p>"


def check_numbers():
    t2 = {r["characteristic"]: r for r in csv.DictReader(open(AN / "table2_trial_characteristics_D43.csv"))}
    assert t2["Control arm present"]["repurposing_containing"] == "32 (22.4%)"
    assert t2["Control arm present"]["de_novo_only"] == "2 (3.1%)"
    assert t2["Control arm present"]["rd_de_novo_minus_repurposing_pp"] == "-19.3 (-27.1 to -9.6)"
    assert t2["Enrolment, actual, median (IQR)"]["repurposing_containing"].startswith("24 (14-61)")
    assert t2["Enrolment, actual, median (IQR)"]["de_novo_only"].startswith("21 (8-48)")
    assert t2["Enrolment, anticipated, median (IQR)"]["repurposing_containing"].startswith("50 (28-96)")
    assert t2["Enrolment, anticipated, median (IQR)"]["de_novo_only"].startswith("50 (36-93)")
    pr = {(r["analysis"], r["scope"], r["process"].split()[0]): r for r in csv.DictReader(open(AN / "pathway_by_process_D42.csv"))}
    g = lambda s, p, k="main": tuple(int(pr[(k, s, p)][x]) for x in ("unique_drugs", "distinct_trials", "trials_drug_matched_selection"))
    assert [g("2a", p)[0] for p in ("P10", "P14", "P12", "P13")] == [7, 6, 4, 4]
    assert [g("2b", p)[0] for p in ("P1", "P2", "P9", "P6")] == [16, 9, 8, 8]
    assert g("2b", "P9") == (8, 49, 3) and g("2b", "P1") == (16, 8, 5) and g("2b", "P4") == (3, 5, 2)
    assert g("2b", "P17") == (3, 14, 3) and g("2b", "P5") == (3, 9, 2)
    assert all(g(s, p)[2] == 0 for s in ("2a", "2b") for p in ("P7", "P8", "P10", "P11", "P13", "P14") if ("main", s, p) in pr)
    assert g("all", "P1", "excluding tailored-therapy trial NCT04591431") == (7, 8, 5)
    pairs = list(csv.DictReader(open(ROOT / "outputs" / "main" / "pathway_pairs_D42.csv")))
    tr = lambda k, f: {p["nct_id"] for p in pairs if p["subcategory"] == k and f(p)}
    assert len(tr("2a", lambda p: 1)) == 35 and len(tr("2a", lambda p: p["drug_matched_selection"] == "yes")) == 2
    assert len(tr("2b", lambda p: 1)) == 108 and len(tr("2b", lambda p: p["drug_matched_selection"] == "yes")) == 14
    assert len({p["nct_id"] for p in pairs}) == 140


TEXT = {
    "pathway_head": "Pathways tested by repurposed candidates (exploratory)",
    "pathway": "The 92 repurposed agents, tested in 140 trials, mapped to 16 of the 17 prespecified biological processes, "
               "and one agent's mechanism was unclear (Supplementary Table S6; Supplementary Figure S1). Non-oncology (2a) "
               "agents most often tested immune modulation (7 agents), neural and ion-channel signalling (6), tumour "
               "metabolism (4) and autophagy (4), whereas oncology (2b) agents concentrated in receptor tyrosine kinase "
               "(16), RAS–MAPK and PI3K–mTOR (9), immune-checkpoint (8) and cytotoxic (8) processes. Agent and trial counts "
               "diverged: eight checkpoint antibodies were tested in 49 trials, whereas the 16 receptor tyrosine kinase "
               "agents were tested in eight trials, ten of them only within one tailored-therapy trial that assigned drugs "
               "by genotype. Selection matched to the specific repurposed agent was used in 2 of 35 trials containing a "
               "non-oncology agent (metformin with an oxidative-phosphorylation subtype assay; atorvastatin with EGFR) and "
               "in 14 of 108 trials containing an oncology agent. Drug-matched selection was concentrated in receptor "
               "tyrosine kinase (5 of 8 trials), cell-cycle (2 of 5), radioligand and photosensitiser (3 of 14) and DNA "
               "damage response (2 of 9) processes, was rare for checkpoint inhibitors (3 of 49) and was not used for any "
               "other immune-modulating, neural, autophagy, epigenetic or anti-angiogenic agent. These patterns were "
               "unchanged after excluding the tailored-therapy trial or judging origin at each trial's own start.",
    "amend": [("Seventh, an exploratory pathway analysis of the 92 repurposed candidates was added after its coding rules "
               "had been fixed (D42). Each agent was assigned a molecular target, a proposed glioblastoma mechanism and a "
               "primary pathway within 17 prespecified biological processes, adapted from the process classification of "
               "neurodegenerative pipeline reports", False), ("3", True),
              (" and the glioblastoma core pathways", False), ("15", True),
              (". Sources were, in order, the registry rationale, published glioma or glioblastoma evidence and "
               "established pharmacology. A blind coding by a second model agreed for 85 of 92 agents, and every "
               "assignment was confirmed by the first author. Selection counted as drug-matched only when a confirmed "
               "eligibility or enrichment biomarker was linked to that agent. Subcategories (2a, 2b) are each agent's "
               "category at its earliest cohort trial, as for the agent-level results. Eflornithine therefore counts as "
               "non-oncology although it held an oncology approval before one of its trials, and retifanlimab, unapproved "
               "at its earliest trial, is not included. Judging origin at each trial's start was a sensitivity analysis. "
               "Eighth, after an independent reproducibility audit of the analysis code, the control-arm variable in "
               "Table 2 was recomputed to include the registered comparator arm types that the coding manual specifies, "
               "which the first computation had omitted, and enrolment is reported as actual and anticipated separately "
               "(D43).", False)],
    "ref15": "15. Brennan CW, Verhaak RGW, McKenna A, Campos B, Noushmehr H, Salama SR, et al. The somatic genomic landscape "
             "of glioblastoma. Cell. 2013;155:462–77. doi:10.1016/j.cell.2013.09.034.",
    "supp": ["• Supplementary Table S5: the 14 prespecified and 2 added sensitivity analyses of the primary comparison.",
             "• Supplementary Table S6: exploratory pathway analysis: each repurposed candidate with its target, proposed "
             "glioblastoma mechanism, primary and secondary pathway, source, cohort trials (NCT identifiers) and "
             "drug-matched selection, with counts by process and the sensitivity analyses.",
             "• Supplementary Figure S1: biological processes tested by non-oncology (2a) and oncology (2b) repurposed "
             "candidates: distinct trials, trials with drug-matched selection and unique agents."],
}


def main():
    if DST.exists():
        sys.exit(f"{DST} exists; refusing to overwrite")
    check_numbers()
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(SRC) as z:
        z.extractall(tmp)
    doc = (tmp / "word" / "document.xml").read_text(encoding="utf8")
    spans = [(m.start(), m.end()) for m in re.finditer(r"<w:p[ >].*?</w:p>", doc, re.S)]
    P = [doc[a:b] for a, b in spans]
    T = lambda i: html.unescape("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", P[i])))
    new = list(P)

    def at(i, expect):
        assert T(i).startswith(expect), (i, T(i)[:80])
        return i

    r = B.replace_in_paragraph
    i = at(26, "The protocol, coding manual")
    new[i] = edit_pending_insertion(P[i], "D1–D41", "D1–D43")
    i = at(71, "Second, two sensitivity analyses")
    new[i] = P[i] + paragraph(TEXT["amend"])
    i = at(77, "The 280 trials tested")
    new[i] = r(P[i], "72 (25.7%) only repositioning candidates",
               "72 (25.7%) repositioning but no repurposed candidates (two of them also with a de novo candidate)")
    i = at(83, "Repurposing-containing trials were more often")
    p = r(P[i], "more often had a control arm (8.4% vs 1.6%)", "more often had a control arm (22.4% vs 3.1%)")
    new[i] = r(p, "Median registered enrolment was similar (38 [IQR 20–83] vs 40 [19–80]) (Table 2).",
               "Median actual enrolment was 24 (IQR 14–61) vs 21 (8–48), and median anticipated enrolment was 50 in both "
               "groups (28–96 and 36–93) (Table 2).")
    i = at(87, "A molecularly informed design")
    new[i] = r(P[i], "(any eligibility, enrichment or stratification biomarker)",
               "(a proxy: an adjudicated eligibility or enrichment biomarker, or a stratification biomarker listed by both "
               "AI coders)")
    i = at(89, "Targeted-")
    new[i] = P[i] + paragraph([(TEXT["pathway_head"], False)], style="Heading2") + paragraph([(TEXT["pathway"], False)])
    i = at(91, "Across the 14 prespecified")
    new[i] = r(P[i], "1 of 9 repositioning-only trials", "1 of 9 trials with repositioning but no repurposed candidates")
    i = at(93, "Recruitment status on 31 July 2026")
    new[i] = edit_pending_insertion(P[i], "41 repositioning-only", "41 with repositioning but no repurposed candidates")
    i = at(139, "14. European Medicines Agency")
    new[i] = P[i] + paragraph([(TEXT["ref15"], False)])
    for i, old, val in ((758, "12 (8.4%)", "32 (22.4%)"), (759, "1 (1.6%)", "2 (3.1%)"),
                        (760, "-6.8 (-12.7 to 0.8)", "-19.3 (-27.1 to -9.6)"),
                        (761, "Enrolment, median (IQR)", "Enrolment, median (IQR): actual; anticipated"),
                        (762, "38 (20-83)", "24 (14-61); 50 (28-96)"), (763, "40 (19-80)", "21 (8-48); 50 (36-93)"),
                        (769, "Molecularly informed design", "Molecularly informed design (proxy)")):
        assert T(i).startswith(old), (i, T(i))
        new[i] = r(P[i], old, val)
    assert T(757) == "Control arm present", T(757)
    i = at(773, "*Molecularly informed design")
    p = r(P[i], "*Molecularly informed design = eligibility/enrichment or prospectively specified stratification.",
          "*Molecularly informed design (proxy) = an adjudicated eligibility or enrichment biomarker, or a stratification "
          "biomarker listed by both AI coders (not necessarily the same biomarker).")
    p = r(p, "‡Registered enrolment (anticipated or actual).",
          "‡Actual and anticipated enrolment reported separately (actual: 51 repurposing-containing and 24 de novo-only "
          "trials; anticipated: 92 and 40). Control arm: any registered active, placebo or sham comparator or "
          "no-intervention arm, or another arm working as the control (D43).")
    new[i] = p
    i = at(780, "• Supplementary Table S4")
    new[i] = P[i] + "".join(paragraph([(t, False)]) for t in TEXT["supp"])
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
    print(f"wrote {DST.name}: {B._id[0] - 20000} new tracked-change ids by {B.AUTHOR}")


if __name__ == "__main__":
    main()
