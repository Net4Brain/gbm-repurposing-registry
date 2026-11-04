"""
Step 19 - Build manuscript v5 from v4_clean with tracked changes (author XL.C). Post-registration processing step.

Input : ../GBM_registry_NOA_structure_v4_clean.docx (not modified)
Output: ../GBM_registry_NOA_structure_v5.docx (refuses to overwrite)
Every change is a Word tracked change (w:ins / w:del, author "XL.C"), so v5 with all changes rejected equals v4_clean.
Numbers come from outputs/analysis_D40/ (scripts 17 and 18) and the decision log (D28-D40).
Usage: python3 scripts/19_build_manuscript_v5.py
"""
import csv
import html
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "GBM_registry_NOA_structure_v4_clean.docx"
DST = ROOT.parent / "GBM_registry_NOA_structure_v5.docx"
AN = ROOT / "outputs" / "analysis_D40"
AUTHOR, DATE = "XL.C", "2026-11-04T15:00:00Z"
_id = [9000]


def nid():
    _id[0] += 1
    return _id[0]


def esc(s):
    return html.escape(s, quote=False)


def ins_run(text, rpr=""):
    return (f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"><w:r>{rpr}'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:ins>')


def del_run(text, rpr=""):
    return (f'<w:del w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"><w:r>{rpr}'
            f'<w:delText xml:space="preserve">{esc(text)}</w:delText></w:r></w:del>')


def runs_of(p):
    return re.findall(r"<w:r>.*?</w:r>|<w:r [^>]*>.*?</w:r>", p, re.S)


def rpr_of(r):
    m = re.search(r"<w:rPr>.*?</w:rPr>", r, re.S)
    return m.group(0) if m else ""


def text_of(r):
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", r))


def replace_in_paragraph(p, old, new):
    """Tracked replacement of `old` (inside one run) by `new` ('' = deletion only)."""
    for r in runs_of(p):
        t = html.unescape(text_of(r))
        if old in t:
            i = t.index(old)
            rp = rpr_of(r)
            before, after = t[:i], t[i + len(old):]
            parts = []
            if before:
                parts.append(f'<w:r>{rp}<w:t xml:space="preserve">{esc(before)}</w:t></w:r>')
            parts.append(del_run(old, rp))
            if new:
                parts.append(ins_run(new, rp))
            if after:
                parts.append(f'<w:r>{rp}<w:t xml:space="preserve">{esc(after)}</w:t></w:r>')
            return p.replace(r, "".join(parts), 1)
    raise ValueError(f"text not found: {old[:60]}")


def delete_paragraph(p):
    """Track deletion of all runs and of the paragraph mark."""
    for r in runs_of(p):
        p = p.replace(r, del_run(html.unescape(text_of(r)), rpr_of(r)), 1)
    mark = f'<w:del w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"/>'
    if "<w:pPr>" in p:
        if re.search(r"<w:pPr>.*?<w:rPr>", p, re.S) and "</w:pPr>" in p and p.index("<w:rPr>") < p.index("</w:pPr>"):
            p = p.replace("<w:rPr>", "<w:rPr>" + mark, 1)
        else:
            p = p.replace("</w:pPr>", f"<w:rPr>{mark}</w:rPr></w:pPr>", 1)
    else:
        p = re.sub(r"(<w:p[ >][^>]*>|<w:p>)", lambda m: m.group(1) + f"<w:pPr><w:rPr>{mark}</w:rPr></w:pPr>", p, count=1)
    return p


def new_paragraph(text, style=None, bold_lead=None):
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "")
    mark = f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"/>'
    body = ""
    if bold_lead:
        body += ins_run(bold_lead, "<w:rPr><w:b/></w:rPr>")
    body += ins_run(text)
    return f"<w:p><w:pPr>{ppr}<w:rPr>{mark}</w:rPr></w:pPr>{body}</w:p>"


def replace_placeholder(p, paragraphs):
    """Delete a placeholder paragraph and insert new body paragraphs after it."""
    return delete_paragraph(p) + "".join(new_paragraph(t) for t in paragraphs)


def table1_xml(rows):
    widths = [2200, 800, 1700, 1900, 900, 1763]
    head = ["Candidate", "Sub-category", "First FDA/EMA approval", "Primary mechanism", "Cohort trials",
            "In a candidate-matched trial"]

    def cell(text, w, bold=False):
        rpr = f'<w:rPr>{"<w:b/>" if bold else ""}<w:sz w:val="16"/></w:rPr>'
        mark = f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"/>'
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr><w:p><w:pPr>'
                f'<w:spacing w:line="240" w:lineRule="auto"/><w:rPr>{mark}</w:rPr></w:pPr>{ins_run(text, rpr)}</w:p></w:tc>')

    def row(vals, bold=False):
        mark = f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"/>'
        return f'<w:tr><w:trPr><w:jc w:val="center"/>{mark}</w:trPr>' + "".join(cell(v, w, bold) for v, w in zip(vals, widths)) + "</w:tr>"

    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    body = row(head, True) + "".join(row(r) for r in rows)
    return (f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/>'
            f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" '
            f'w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{body}</w:tbl>')


MECH = {"targeted_signalling": "Targeted signalling", "immunomodulatory": "Immunomodulatory", "cytotoxic": "Cytotoxic",
        "metabolic": "Metabolic", "epigenetic": "Epigenetic", "anti_angiogenic": "Anti-angiogenic", "other": "Other"}

TEXT = {
 "abstract_results": "Of 870 screening records, 280 trials were eligible. Of 229 unique candidate agents, 92 (40.2%; 95% CI 34.0–46.6) were approved-drug repurposing (31 non-oncology, 61 oncology), 67 (29.3%) investigational repositioning and 70 (30.6%) de novo; 143 trials (51.1%) contained a repurposed candidate. Candidate-matched molecular selection was used in 14/64 de novo-only trials (21.9%) and 17/143 repurposing-containing trials (11.9%; risk difference 10.0 percentage points, 95% CI −0.5 to 22.3). The direction was consistent across sensitivity analyses (1.0 to 18.5 points), no interval excluded the 10-point margin, and the difference was smaller within mechanism classes. [Expert-validation accuracy: TO ADD.]",
 "key_points": ["40% of candidate drugs in 2020–26 adult GBM trials were approved-drug repurposing",
                "Repurposing trials were mostly academic-led Phase 2 combination trials",
                "Biomarker-matched selection: 12% vs 22% (de novo); the difference was uncertain"],
 "osf": "The protocol, coding manual (version 1.4) and analysis plan were registered on the Open Science Framework on 2 November 2026, before the main coding pass (osf.io/gn8v5; embargoed until publication). The analysis code, frozen inputs and dated decision log (protocol decisions D1–D40) are in the study repository (github.com/Net4Brain/gbm-repurposing-registry; [DOI at deposition]).",
 "validation": "Because two LLM coders from the same vendor may share errors that agreement cannot detect, human review has two parts. First, for correction, every disagreement and flagged item was adjudicated: a separate AI process (Claude) drafted adjudication proposals, and the first author accepted, changed or deferred each one under written rulings (protocol decisions D30–D32). The first author then reviewed every positive candidate-matched selection decision, blinded to drug origin, and the dated origin evidence for every unique candidate agent (D33–D35). Second, for measurement, two invited experts independently code a stratified random sample of 100 records (phase group × lead sponsor class, proportional allocation, seed 20261104), drawn before the main pass from the 810 records not used in calibration. They code blind to the AI output and to each other, using the frozen manual and a rules addendum that states the adjudication rulings (D28, D38). Their consensus is the reference standard; inter-expert agreement and AI accuracy (confusion matrices, sensitivity, specificity and positive and negative predictive values with 95% confidence intervals and sampling weights) are reported. If the AI misses more than 5% of reference positives for trial eligibility or candidate-matched selection, all records will be coded by a human for that variable. Inter-coder agreement before adjudication is reported as Cohen’s kappa together with prevalence-adjusted bias-adjusted kappa and Gwet’s AC1; it measures reproducibility, not correctness.",
 "amend_head": "Amendments after registration",
 "amend": [
  "All changes after registration are dated protocol decisions in the study repository and are reported here. First, recurring questions from the main coding pass were settled by written adjudication rulings before final values were set (D30–D32). Drugs that support a cell therapy, gene therapy or vaccine (cytokines, adjuvants, prodrugs of suicide-gene therapies, immune primers) are part of that excluded therapy. Imaging-assessed target expression with a matched radioligand counts as candidate-matched selection and is flagged. A biomarker required only for a non-glioblastoma cohort of a basket trial is not selection. A mechanistic match may follow from the candidate’s established pharmacology as well as from the record’s stated rationale.",
  "Second, two sensitivity analyses were added: excluding imaging-assessed selection from the primary outcome (sensitivity analysis 15), and counting the one trial whose candidates were not identified in the record, but were certainly unapproved at its start, as de novo-only (sensitivity analysis 16). Agents that the record does not identify are excluded from agent-level counts (D36). Third, the expert validation materials include a rules addendum stating the adjudication rulings (D38). Fourth, primary mechanism was assigned after the main pass, not by the LLM coders: prespecified categories were applied to the registry-stated rationale, the coders’ drug-class notes and ChEMBL, and every assignment was reviewed (D40). Fifth, AI-drafted recommendations and independent AI cross-checks were used as decision support in the human review; every dated regulatory and development event was signed off by the first author (D33–D35). All analyses used Python 3.13; R was not needed."],
 "selection": [
  "The main and supplementary searches gave 870 screening records (834 and 36). By the structured-field steps, 273 records were excluded for phase (186 phase not applicable, 78 Early Phase 1 and 9 Phase 4) and 10 for paediatric-only eligibility; no record failed the study-type or start-date steps, which the retrieval query already enforced. By the adjudicated coding, 99 records were excluded because the population was not glioblastoma (55 not glioblastoma, 34 high-grade glioma without glioblastoma or grade 4 specified, 7 glioblastoma excluded and 3 anti-GBM disease) and 192 because no eligible candidate was tested (123 excluded intervention types such as cell or gene therapies and vaccines, 46 no pharmacological candidate and 23 established glioblastoma therapy only). Of the 296 trials passing every step, 16 were withdrawn and are reported separately, leaving 280 trials in the primary cohort (Figure 1). Forty otherwise eligible Early Phase 1 trials form the translational subset. Ten cohort trials tested an established glioblastoma therapy as an experiment (a new schedule, route or device for temozolomide, lomustine, carmustine or bevacizumab) and six used a delivery-enabling agent; neither counted as a candidate. No candidate had a glioma approval before its trial started.",
  "Before adjudication, the two AI coders agreed on the primary outcome for 99.2% of the 870 records (κ 0.96) and on population, candidate status and exclusion reason for 93.9–98.3% (κ 0.91–0.97) (Supplementary Table S4). Disagreements and flagged items in 384 records were adjudicated. In the correction review, 95 biomarker–candidate pairs supporting a positive selection decision were examined; 87 were confirmed and 8 rejected, and every trial with a positive decision kept at least one confirmed pair. Of the 20 cohort trials also listed in ReDO_Trials_DB, 19 (95%; exact 95% CI 75.1–99.9) were coded repurposing-containing; the exception paired a dendritic-cell vaccine with tetanus–diphtheria toxoid preconditioning, which our protocol counts as part of the excluded vaccine therapy. [Expert validation: inter-expert agreement and AI sensitivity, specificity, PPV and NPV against the expert consensus — TO ADD when the expert coding is complete.]"],
 "composition": ["The 280 trials tested 229 unique identified candidate agents. At each agent’s earliest trial start, 92 (40.2%; 95% CI 34.0–46.6) were approved-drug repurposing: 31 (13.5%) approved only for non-oncology indications (2a) and 61 (26.6%) approved for another cancer (2b). A further 67 (29.3%) were investigational repositioning candidates with earlier non-glioblastoma Phase 2 or later development, and 70 (30.6%) were operational de novo agents (Table 1). Three repurposed agents held a tumour-agnostic approval at their trial’s start. At trial level, 143 trials (51.1%) contained at least one repurposed candidate, 72 (25.7%) only repositioning candidates and 64 (22.9%) only de novo candidates; one trial whose two bispecific antibodies were not identified in the record could not be assigned. No classification depended on an imprecise approval date, and the headline proportion changed by at most 2.6 percentage points across the sensitivity analyses, so it is not definition-dependent."],
 "phase": ["De novo-only trials were mostly Phase 1 (41 of 64, 64.1%), whereas repurposing-containing trials were mostly Phase 2, including Phase 1/2 (96 of 143, 67.1%); Phase 3 trials were rare in both groups (1 and 7) (Table 2). At agent level, the highest registered phase was Phase 2 or later for 79 of 92 repurposed agents (85.9%), 53 of 67 repositioning candidates (79.1%) and 29 of 70 de novo agents (41.4%)."],
 "sponsor": ["An industry sponsor led 47 of 64 de novo-only trials (73.4%) but 33 of 143 repurposing-containing trials (23.1%; difference 50.4 percentage points, 95% CI 36.2 to 61.5). Industry was involved as lead sponsor or collaborator in 82.8% and 46.9%, respectively."],
 "design": ["Repurposing-containing trials were more often in newly diagnosed disease (32.2% vs 15.6%) and more often tested a combination regimen (77.6% vs 35.9%), whereas 64.1% of de novo-only trials tested monotherapy. Repurposing-containing trials were also more often randomised (25.9% vs 10.9%) and more often had a control arm (8.4% vs 1.6%). Median registered enrolment was similar (38 [IQR 20–83] vs 40 [19–80]) (Table 2)."],
 "selection_results": [
  "Candidate-matched molecular selection was used in 14 of 64 de novo-only trials (21.9%; 95% CI 13.5–33.4) and 17 of 143 repurposing-containing trials (11.9%; 7.6–18.2), a risk difference of 10.0 percentage points (95% CI −0.5 to 22.3). The interval included zero and did not exclude the prespecified 10-point margin. Standardised over phase group, treatment setting and calendar period, the difference was 7.2 points (−3.2 to 17.6); with primary mechanism added it was 7.0 points (−3.3 to 17.3), although only 88 of 207 trials fell in strata containing both groups. The candidate-specific analysis (10.7 points, 0.3 to 23.0), single-candidate trials (12.1, 0.4 to 25.2) and restriction to non-oncology (2a) repurposing (16.0, 0.4 to 28.3; 2 of 34 trials selected) gave similar or larger differences, and leaving out each of the five most frequent agents gave 8.5 to 10.7 points.",
  "Within targeted-signalling trials, selection was nearly identical (7 of 24 de novo-only vs 7 of 25 repurposing-containing trials). Repurposing-containing trials were dominated by immunomodulatory (48) and other (21) agents, which rarely used selection (2 and 0 trials, respectively). Among the 42 trials with candidate-matched selection, the confirmed markers were most often EGFR alterations (12 pairs), BRAF (4), FGFR (3) and mismatch-repair deficiency or high tumour mutational burden (3); 31 pairs involved other markers, including MTAP deletion and imaging-assessed target expression for radioligands. At agent level, 37 of 92 repurposed agents (2a 2 of 31; 2b 35 of 61) and 16 of 70 de novo agents were tested in at least one candidate-matched trial, largely because oncology drugs were assigned by genomic markers within multi-drug trials; agents tested more often had more opportunities to qualify.",
  "A molecularly informed design (any eligibility, enrichment or stratification biomarker) was present in 30 of 64 de novo-only (46.9%) and 49 of 143 repurposing-containing trials (34.3%). Planned measurement of the candidate in tumour tissue or cerebrospinal fluid was more common in de novo-only trials (21.9% vs 7.0%; difference 14.9 points, 4.9 to 26.9), whereas planned target-engagement measurement was similar (26.6% vs 24.5%)."],
 "mechanism": ["Targeted-signalling agents formed the largest class (85 of 229 agents), followed by immunomodulatory (48), other (35), cytotoxic (29), metabolic (14), epigenetic (11) and anti-angiogenic (7) agents. Non-oncology (2a) repurposing was dominated by other mechanisms, mainly central nervous system, antimicrobial and ion-channel drugs (15 of 31), and by metabolic agents (6), whereas oncology (2b) repurposing was mostly targeted-signalling (34 of 61) and immunomodulatory (12) agents."],
 "sensitivity": [
  "Across the 14 prespecified and 2 added sensitivity analyses, the risk difference ranged from 1.0 point (restriction to CNS5 terminology; −14.8 to 20.1) to 18.5 points (glioblastoma-only populations; 4.3 to 38.2) (Supplementary Table S5). The interval excluded zero in four sensitivity analyses (2a-only exposure, glioblastoma-only populations, inclusion of Early Phase 1 trials and exclusion of candidates within an existing label) and excluded 10 points in none. Excluding imaging-assessed selection gave 8.3 points (−1.5 to 20.2). In the translational subset of 40 Early Phase 1 trials, candidate-matched selection was used in 5 of 7 de novo-only, 5 of 24 repurposing-containing and 1 of 9 repositioning-only trials.",
  "Of 15 glioma trials in ReDO_Trials_DB that started within the study window but were absent from the screening set, 11 were registered only outside ClinicalTrials.gov, 3 were not glioblastoma trials and 1 had a registry start date outside the window. [Probabilistic misclassification analysis and the active-on-index-date subset: TO ADD.]"],
 "ai": "Use of artificial intelligence: Large language models were used in four ways. First, for data extraction, two independent LLM coders (Claude Opus 5.5 and Claude Sonnet 5.5, Anthropic) screened registry records and coded judgement-based variables under the frozen coding manual. Second, an AI assistant (Claude, Anthropic) drafted adjudication proposals and recommendations for drug-origin evidence and primary-mechanism categories, and wrote and ran the analysis code under the authors’ direction; the first author accepted, changed or deferred every proposal and recommendation, and all code is archived. Third, ChatGPT/Codex (OpenAI) independently cross-checked selected Claude-generated coding and adjudication results against the source records, including the positive candidate-matched selection decisions and the drug-origin evidence, and the authors resolved every discrepancy. [ChatGPT also checked the reproducibility of the GitHub pipeline by rerunning [stages] from an isolated copy of commit [hash] — TO CONFIRM once completed.] Fourth, ChatGPT (OpenAI) and Claude (Anthropic) assisted with manuscript structuring and language drafting. Separately from these AI uses, two human experts independently coded a blinded validation sample, against which the accuracy of the AI coding is reported (see Methods) [TO UPDATE when complete]. All methodological decisions, adjudications, interpretation, references and final wording are the responsibility of the authors.",
}


def main():
    if DST.exists():
        sys.exit(f"{DST} exists; refusing to overwrite")
    assert all(len(k) <= 85 for k in TEXT["key_points"]), [len(k) for k in TEXT["key_points"]]
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(SRC) as z:
        z.extractall(tmp)
    doc = (tmp / "word" / "document.xml").read_text(encoding="utf8")
    spans = [(m.start(), m.end()) for m in re.finditer(r"<w:p[ >].*?</w:p>", doc, re.S)]
    P = [doc[a:b] for a, b in spans]
    T = lambda i: "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", P[i]))
    new = list(P)

    def at(i, expect):
        assert html.unescape(T(i)).startswith(expect), (i, T(i)[:80])
        return i

    i = at(9, "Results:")
    new[i] = replace_in_paragraph(P[i], "[TO COMPLETE AFTER PROTOCOL-FROZEN ANALYSIS.]", TEXT["abstract_results"])
    for k, i in enumerate((13, 14, 15)):
        at(i, "•")
        new[i] = replace_in_paragraph(P[i], html.unescape(T(i))[2:], TEXT["key_points"][k])
    new[at(24, "Protocol text.")] = delete_paragraph(P[24])
    new[at(27, "[Insert OSF")] = replace_placeholder(P[27], [TEXT["osf"]])
    i = at(57, "Screening and abstraction")
    new[i] = replace_in_paragraph(P[i], "biomarker role and identity, translational indicators, and mechanism)",
                                  "biomarker role and identity, and translational indicators; primary mechanism was assigned after the main pass, see Amendments after registration)")
    i = at(58, "Because two LLM coders")
    new[i] = delete_paragraph(P[i]) + new_paragraph(TEXT["validation"])
    i = at(66, "No sample-size")
    new[i] = replace_in_paragraph(P[i], "in R (version 4.5.2) and Python (version 3.13)", "in Python (version 3.13)")
    i = at(69, "An optional supplementary")
    new[i] = P[i] + new_paragraph(TEXT["amend_head"], style="Heading2") + "".join(new_paragraph(t) for t in TEXT["amend"])
    new[at(71, "ENTIRE SECTION")] = delete_paragraph(P[71])
    for i, key in ((73, "selection"), (75, "composition"), (77, "phase"), (79, "sponsor"), (81, "design"),
                   (83, "selection_results"), (85, "mechanism"), (87, "sensitivity")):
        at(i, "[")
        new[i] = replace_placeholder(P[i], TEXT[key])
    i = at(118, "Use of artificial intelligence")
    new[i] = delete_paragraph(P[i]) + new_paragraph(TEXT["ai"])
    # Table 1
    t1 = list(csv.DictReader(open(AN / "table1_repurposing_agents.csv")))
    rows = [[r["candidate"], r["subcategory"] + (" (TA)" if r["tumour_agnostic_at_T"] else ""), r["first_fda_ema_approval"],
             MECH.get(r["mechanism"], r["mechanism"]), r["cohort_trials"], r["in_candidate_matched_trial"]]
            for r in sorted(t1, key=lambda r: (r["subcategory"], r["candidate"]))]
    i = at(138, "Table 1. Unique")
    old = html.unescape(T(i)).split("pipeline. ", 1)[1]
    new[i] = replace_in_paragraph(P[i], old, "Candidates are grouped by subcategory (2a, approved only for non-oncology "
                                  "indications; 2b, approved for another cancer; TA, tumour-agnostic approval at trial start) "
                                  "and listed with their first FDA or EMA approval, primary mechanism, number of cohort trials "
                                  "and whether they were tested in at least one trial with candidate-matched molecular "
                                  "selection. Original indications, sources and NCT identifiers are in Supplementary Table S2.") \
        + table1_xml(rows)
    i = at(139, "Table 2. Characteristics")
    new[i] = replace_in_paragraph(P[i], "Planned rows are provided below; all result cells remain blank.",
                                  "Values are n (%) unless stated. Effect estimates are risk differences (de novo-only minus "
                                  "repurposing-containing) in percentage points with Newcombe 95% confidence intervals and "
                                  "are descriptive.")
    # Table 2 cells
    t2 = {r["characteristic"]: r for r in csv.DictReader(open(AN / "table2_trial_characteristics.csv"))}
    label = {"Number of trials": "Number of trials", "Phase 1": "Phase 1", "Phase 2 (incl. Phase 1/2)": "Phase 2 (incl. Phase 1/2)",
             "Phase 3 (incl. Phase 2/3)": "Phase 3 (incl. Phase 2/3)", "Industry lead sponsor": "Industry lead sponsor",
             "Any industry involvement": "Any industry involvement", "Newly diagnosed setting": "Newly diagnosed setting",
             "Recurrent/progressive setting": "Recurrent/progressive setting", "Both/unclear setting": "Both/unclear setting",
             "Monotherapy": "Monotherapy", "Combination regimen": "Combination regimen", "Randomised design": "Randomised design",
             "Control arm present": "Control arm present", "Enrolment, median (IQR)‡": "Enrolment, median (IQR)",
             "Candidate-matched molecular selection†": "Candidate-matched molecular selection",
             "Molecularly informed design*": "Molecularly informed design"}
    filled = 0
    for i in range(140, 209):
        lab = html.unescape(T(i))
        if lab in label:
            r = t2[label[lab]]
            vals = [str(r["repurposing_containing"]), str(r["de_novo_only"]), r["rd_de_novo_minus_repurposing_pp"] or "—"]
            for k, v in enumerate(vals, 1):
                assert html.unescape(T(i + k)) == "[ ]", (i + k, T(i + k))
                new[i + k] = replace_in_paragraph(P[i + k], "[ ]", v)
                filled += 1
        if lab == "Effect estimate / exploratory P value":
            new[i] = replace_in_paragraph(P[i], "Effect estimate / exploratory P value", "Risk difference, pp (95% CI)")
    assert filled == 48, filled
    i = at(209, "*Molecularly informed")
    new[i] = replace_in_paragraph(P[i], "‡Anticipated and actual enrolment reported separately.",
                                  "‡Registered enrolment (anticipated or actual).")
    new[i] = replace_in_paragraph(new[i], "[Add rows: planned tumour drug-exposure measurement; planned target-engagement "
                                  "measurement; device-dependent candidate.]",
                                  "Planned tumour drug-exposure and target-engagement measurement are reported in the text.")
    out = []
    last = 0
    for (a, b), p in zip(spans, new):
        out.append(doc[last:a])
        out.append(p)
        last = b
    out.append(doc[last:])
    (tmp / "word" / "document.xml").write_text("".join(out), encoding="utf8")
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(tmp.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(tmp).as_posix())
    shutil.rmtree(tmp)
    print(f"wrote {DST.name}: {_id[0] - 9000} tracked-change ids by {AUTHOR}; Table 2 cells filled {filled}; Table 1 rows {len(rows)}")


if __name__ == "__main__":
    main()
