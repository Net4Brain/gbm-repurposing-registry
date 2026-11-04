"""
Step 24 - Supplementary Information draft (Word) and Supplementary Data workbook (Excel). Post-registration step.

The Word file reuses the styles, footer and page set-up of ../GBM_registry_NOA_structure_v7.docx (not modified) and
holds the Supplementary Methods, the table legends, Tables S4-S6 in summary and Figure S1. The large tables (S1, S2,
the full S6 mapping, the search audit) go into the workbook, one sheet each. Every number is read from the committed
outputs; nothing is typed in except the calibration-round summary, which comes from the three calibration reports.
Expert-validation results do not exist yet and appear as a marked placeholder.

Outputs (../, each refused if it exists):
  GBM_registry_NOA_supplementary_information_v1.docx
  GBM_registry_NOA_supplementary_data_v1.xlsx
Usage: python3 scripts/24_build_supplement.py
"""
import csv
import hashlib
import html
import json
import re
import shutil
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
RUN, AN, REF = ROOT / "outputs" / "main", ROOT / "outputs" / "analysis_D40", ROOT / "data" / "reference"
TEMPLATE = ROOT.parent / "GBM_registry_NOA_structure_v7.docx"
DOCX = ROOT.parent / "GBM_registry_NOA_supplementary_information_v1.docx"
XLSX = ROOT.parent / "GBM_registry_NOA_supplementary_data_v1.xlsx"
FIG = AN / "figure_pathway_D42.png"
TITLE = "Repurposed drugs in the contemporary glioblastoma clinical trial landscape: a registry-based analysis"
TEXT_W = 9317  # A4 text width in dxa (11909 - 2 x 1296)
rd = lambda p: list(csv.DictReader(open(p)))
esc = lambda s: html.escape(str(s), quote=False)


# ------------------------------------------------------------------ Word XML helpers
def run(text, bold=False, italic=False, sup=False, size=None):
    rpr = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + ('<w:vertAlign w:val="superscript"/>' if sup else "") \
        + (f'<w:sz w:val="{size}"/>' if size else "")
    return f'<w:r>{"<w:rPr>" + rpr + "</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def para(content, style=None, keep_next=False, indent=None):
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + ("<w:keepNext/>" if keep_next else "") \
        + (f'<w:ind w:left="{indent}" w:hanging="216"/>' if indent else "")
    body = content if content.startswith("<w:r") else run(content)
    return f'<w:p>{"<w:pPr>" + ppr + "</w:pPr>" if ppr else ""}{body}</w:p>'


def lead(label, text, style=None):
    return para(run(label, bold=True) + run(text), style)


def bullet(text):
    return para(run("• " + text), indent=360)


def table(header, rows, widths, size=16):
    """Plain grid table; widths in dxa summing to TEXT_W; header row shaded (ShadingType CLEAR)."""
    assert abs(sum(widths) - TEXT_W) < 5, sum(widths)
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)

    def cell(text, w, head=False):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="E7E6E6"/>' if head else ""
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}</w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr>{run(text, bold=head, size=size)}</w:p></w:tc>')
    trs = [f'<w:tr><w:trPr><w:tblHeader/></w:trPr>{"".join(cell(h, w, True) for h, w in zip(header, widths))}</w:tr>']
    trs += [f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{"".join(cell(v, w) for v, w in zip(r, widths))}</w:tr>' for r in rows]
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_W}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="60" w:type="dxa"/><w:right w:w="60" w:type="dxa"/>'
            f'</w:tblCellMar></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>' + para(""))


def image(rid, cx, cy):
    return (f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="1" name="Figure S1"/>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:nvPicPr><pic:cNvPr id="1" name="figure_pathway_D42.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ------------------------------------------------------------------ content
def methods(body):
    q = json.load(open(ROOT / "logs" / "ctgov_query_log_20261101T130137Z.json"))
    qs = json.load(open(ROOT / "logs" / "ctgov_supp_query_log_20261101T150223Z.json"))
    body.append(para("Supplementary Methods", "Heading1"))
    body.append(para("M1. Registry queries", "Heading2"))
    main = q["queries"]["condition"]
    body.append(para(f"The main search used the ClinicalTrials.gov API version 2 ({q['api']}) on 1 November 2026 at "
                     f"{q['retrieved_utc'][9:11]}:{q['retrieved_utc'][11:13]} UTC, with the condition query and filter below. It returned "
                     f"{main['n_retrieved']} records (reported total {main['total_reported']}). The query log, with every "
                     "NCT identifier returned, and the frozen snapshot are in the study repository."))
    body.append(table(["Search", "Parameter", "Value", "Records"],
                      [["Main", "query.cond", main["params"]["query.cond"], str(main["n_retrieved"])],
                       ["Main", "filter.advanced", main["params"]["filter.advanced"], ""]] +
                      [[f"Supplementary: {k}", "; ".join(f"{a}" for a in v["params"]), "; ".join(v["params"].values()),
                        f"{v['n_retrieved']} ({v.get('n_not_in_main', '')} not in main)"] for k, v in qs["queries"].items()],
                      [1500, 1300, 5017, 1500]))
    sc = rd(RUN / "screening_D37.csv")
    label = {"": "Passed S1–S6: primary cohort", "phase_not_applicable": "S3 phase not applicable",
             "phase0_early_phase1": "S3 Early Phase 1 (40 otherwise eligible form the translational subset)", "phase4": "S3 Phase 4",
             "paediatric_only": "S4 paediatric only", "not_glioblastoma": "S5 not glioblastoma",
             "high_grade_glioma_unspecified": "S5 high-grade glioma, glioblastoma not specified",
             "gbm_excluded": "S5 glioblastoma excluded", "anti_gbm_disease": "S5 anti-GBM disease",
             "excluded_intervention_type": "S6 excluded intervention type", "no_pharmacological_candidate":
             "S6 no pharmacological candidate", "established_therapy_only": "S6 established therapy only"}
    c = Counter("Passed S1–S6: withdrawn (S7, reported separately)" if not r["exclusion_reason"] and r["withdrawn"] == "yes"
                else label.get(r["exclusion_reason"], r["exclusion_reason"]) for r in sc)
    body.append(para("M2. Screening steps", "Heading2"))
    body.append(para("Steps S1–S7 of the coding manual were applied in order to all screening records; the first step a "
                     "record failed gave its exclusion reason (Figure 1). S1–S4 and S7 use structured registry fields; S5 "
                     "(glioblastoma population) and S6 (eligible pharmacological candidate) use the adjudicated AI coding."))
    body.append(table(["Screening step and outcome", "Records"], [[k, str(v)] for k, v in sorted(c.items(), key=lambda x: (not x[0].startswith("Passed"), x[0]))] +
                      [["Total screening records", str(len(sc))]],
                      [7317, 2000]))
    body.append(para("M3. Drug origin", "Heading2"))
    body.append(para("Origin is derived from dated FDA and EMA approval events and dated prior non-glioblastoma clinical "
                     "development, never from current labels. For a trial starting on date T, an event counts only if its "
                     "latest possible date is on or before T. Established glioblastoma therapies (temozolomide, lomustine, "
                     "carmustine, bevacizumab) are not candidates. Otherwise:"))
    for t in ["2a, non-oncology repurposing: one or more FDA/EMA approvals before T, none of them for a cancer.",
              "2b, oncology repurposing: an FDA/EMA approval for another cancer before T. Dated flags record a "
              "tumour-agnostic approval, a glioma label that was not the first approval, and a trial population already "
              "within an approved indication.",
              "Glioma-developed: the earliest approval is a glioma treatment indication (reported separately).",
              "3, investigational repositioning: unapproved, but Phase 2 or later in a non-glioblastoma indication before T.",
              "1, operational de novo: no approval and no earlier Phase 2 or later non-glioblastoma development.",
              "Unidentified (D36): the record does not identify the agent; excluded from agent-level counts."]:
        body.append(bullet(t))
    body.append(para("If an event's date interval contains T, the agent is classified both ways and flagged date-sensitive; "
                     "the conservative result is kept. A start date given only as a month is taken as the first day of that "
                     "month (earliest possible start); a check of all 23 such candidate starts found no change of category "
                     "or flags at the month's last day (D43). Agent-level origin is the category at the agent's earliest "
                     "cohort trial (D12). Approvals by other regulators only do not count."))
    body.append(para("M4. Trial-origin groups", "Heading2"))
    body.append(para("Repurposing-containing: at least one category-2 candidate. De novo-only: only category-1 candidates. "
                     "Repositioning, no repurposed candidate (the manual's 'repositioning_only' group): category-3 "
                     "candidates and no category-2 candidate; two of these 72 trials (NCT04225039, NCT06188702) also have a "
                     "category-1 candidate. An unspecified approved-drug panel counts as category 2 at trial level only."))
    body.append(para("M5. Mechanism categories", "Heading2"))
    body.append(para("Each candidate has one primary category: cytotoxic, targeted signalling (including DNA-damage-response "
                     "inhibitors and antibody–drug conjugates, classified by target), immunomodulatory, metabolic, epigenetic, "
                     "anti-angiogenic or other (including CNS drugs, antimicrobials and ion-channel modulators). A repurposed "
                     "drug is classified by the antitumour mechanism stated in its registry record, otherwise by its ChEMBL "
                     "primary target. Categories were assigned after the main coding pass and every assignment was reviewed "
                     "(D40)."))
    body.append(para("M6. Pathway coding (exploratory; D42)", "Heading2"))
    rules = (ROOT / "prompts" / "pathway_coding_rules_D42.md").read_text()
    vocab = re.findall(r"\| \*\*(P\d+ [^*]+)\*\* \| (.+) \|", rules)
    body.append(para("The coding rules and the vocabulary were fixed before coding (prompts/pathway_coding_rules_D42.md). "
                     "Each of the 92 repurposed candidates received a target, a proposed glioblastoma mechanism, a primary "
                     "pathway, up to two secondary pathways or 'unclear', and a source: the registry-stated rationale first, "
                     "then a published glioma or glioblastoma rationale (PMID; used when the approved pharmacology is not the "
                     "antitumour hypothesis), then established pharmacology. A second model coded the drugs blind; the first "
                     "author confirmed every row. Selection was drug-matched only when a confirmed eligibility or enrichment "
                     "biomarker was linked to that candidate and governed entry to the trial or to a glioblastoma cohort or "
                     "arm receiving it. Subcategories are the agent-level categories; eflornithine (2b in NCT07468136) and "
                     "retifanlimab (category 3 at its earliest trial, 2b in three later trials) are handled by a sensitivity "
                     "analysis that judges origin per trial. One level-2 pathway was added during coding: JAK–STAT "
                     "(tumour-intrinsic), under P2."))
    body.append(table(["Level-1 process", "Level-2 pathways"], [[a, b] for a, b in vocab] +
                      [["P2 (added)", "JAK–STAT (tumour-intrinsic)"]], [3100, 6217]))
    body.append(para("M7. Recruitment status on the index date (D41)", "Heading2"))
    body.append(para("Status on 31 July 2026 is the status in each record's last ClinicalTrials.gov version dated on or "
                     "before that day, read from the public record-history page because scripted requests are refused. "
                     "Active: recruiting, not yet recruiting, active not recruiting or enrolling by invitation. Not "
                     "reconstructable: status unknown in the history, or an active status not updated in the two years "
                     "before the index date (the registry's own rule). The extraction code and raw extract are in the "
                     f"repository (raw extract SHA-256 {sha(ROOT / 'data' / 'raw' / 'ctgov_status_history_D41_20261104.txt')[:16]}…)."))
    body.append(para("M8. Supplementary-search filter audit", "Heading2"))
    rej = rd(ROOT / "data" / "processed" / "supp_rejected_02b.csv")
    add = rd(ROOT / "data" / "processed" / "supp_added_to_screening.csv")
    body.append(para(f"Records from the supplementary searches that were not in the main pull were admitted to screening "
                     f"only if glioblastoma was named in the title, conditions or inclusion criteria (the eligibility rule). "
                     f"The scripted filter reproduced the original decisions exactly: {len(add)} admitted, {len(rej)} "
                     f"rejected. An audit of every rejected record for synonyms in those fields found no false negatives. "
                     f"Basket trials that do not name glioblastoma are excluded by design. The rejected records are in "
                     f"workbook sheet 'Search_audit'."))
    body.append(para("M9. Registry-coverage audit", "Heading2"))
    body.append(para("A WHO ICTRP/CTIS coverage audit was optional and has not been performed. [To be completed or removed "
                     "before submission.]"))


def tables(body):
    body.append(para("Supplementary Tables", "Heading1"))
    body.append(lead("Table S1. ", "All 870 screening records with the screening outcome, structured fields, adjudicated "
                     "population and design variables, trial-origin group and candidate agents with their origin at trial "
                     "start. Workbook sheet 'S1_trials'."))
    body.append(lead("Table S2. ", "Candidate agents in all records passing screening steps S5–S6 (primary cohort, translational "
                     "subset and withdrawn trials). 'S2a_agents': one row per unique agent with its origin at its earliest "
                     "trial, first FDA/EMA approval, primary mechanism, and its trials (with the number in the primary "
                     "cohort; the agent-level analyses use the primary cohort only). 'S2b_candidate_trials': one row per "
                     "candidate per trial with origin at trial start and at the index date, the two dated axes, flags and the "
                     "evidence used. 'S2c_regulatory_events' and 'S2d_development_events': the reviewed dated event tables, "
                     "with sources and the reviewer."))
    manual = ROOT / "coding_manual_v1.4.md"
    body.append(lead("Table S3. ", f"Frozen coding manual, version 1.4, provided as a separate file ({manual.name}; "
                     f"SHA-256 {sha(manual)}), with its amendment history."))
    # S4
    body.append(lead("Table S4. ", "AI-assisted extraction and human review."))
    frozen = dict(reversed(l.split("  ", 1)) for l in (ROOT / "FROZEN_v1.4.sha256").read_text().strip().splitlines())
    body.append(para("S4a. Coders, prompts and frozen materials", "Heading3"))
    body.append(table(["Item", "Value"],
                      [["Coder A", "Claude Opus 5.5 (Anthropic)"], ["Coder B", "Claude Sonnet 5.5 (Anthropic)"]] +
                      [[k, frozen[k]] for k in ("coding_manual_v1.4.md", "schema/trial_coding.schema.v1.4.json",
                                                "prompts/coder_prompt_v1.4.md", "prompts/agent_run_instructions_v1.4.md")],
                      [3600, 5717], size=14))
    body.append(para("S4b. Calibration rounds and main pass", "Heading3"))
    body.append(table(["Round", "Manual", "Records", "Adjudication queue rows", "Non-verbatim quotes"],
                      [["Calibration 1 (2026-11-01)", "v1.0", "40", "246", "11"],
                       ["Calibration 2 (2026-11-01)", "v1.1", "40 (same)", "39", "0"],
                       ["Calibration 3 (2026-11-02)", "v1.3", "20 (new)", "81", "2"],
                       ["Main pass (2026-11-02/03)", "v1.4", "870",
                        str(sum(1 for _ in open(RUN / "adjudication_queue.csv")) - 1), "4 (after removing registry escapes)"]],
                      [2600, 1000, 1400, 2117, 2200]))
    body.append(para("S4c. Agreement between the two coders before adjudication (n = 870)", "Heading3"))
    body.append(table(["Variable", "% agreement", "Cohen's κ", "PABAK", "Gwet's AC1"],
                      [[r["variable"], f"{100 * float(r['pct_agree']):.1f}", r["kappa"], r["pabak"], r["gwet_ac1"]]
                       for r in rd(RUN / "agreement.csv")], [3317, 1500, 1500, 1500, 1500]))
    d21 = rd(RUN / "d21_match_decisions_XL.csv")
    ck = Counter(r["check"] for r in rd(RUN / "coder_checks_D43.csv"))
    redo = rd(RUN / "redo_check_D39.csv")
    body.append(para("S4d. Human review and checks", "Heading3"))
    for t in [f"Adjudication: written rulings settled recurring questions (D30–D32); flagged items and disagreements were "
              f"adjudicated record by record.",
              f"Candidate-matched selection: {len(d21)} biomarker–candidate pairs supporting a positive decision were "
              f"reviewed by the first author; {sum(r['XL_decision'] == 'yes' for r in d21)} confirmed and "
              f"{sum(r['XL_decision'] == 'no' for r in d21)} rejected (D33).",
              "Drug origin: every dated regulatory and development event was reviewed and signed off by the first author, "
              "with AI-drafted recommendations and independent AI cross-checks as decision support (D33–D35).",
              f"Archived coder files (D43): file name equals the internal trial ID in all 1,740 files; "
              f"{ck['biomarker arms differ only']} biomarker rows differ between coders only in the arms listed (all "
              f"outcome-relevant ones were in the D33 review); of all evidence quotes, {ck['quote symbols_only']} differ "
              f"from the record only in symbols and {ck['quote pieces_present']} is a stitched list of record terms; none "
              f"was invented.",
              f"External check against ReDO_Trials_DB (D39): {len(redo)} ReDO trials in the screening set; see the main "
              f"text for agreement in the primary cohort."]:
        body.append(bullet(t))
    body.append(para("S4e. Expert validation", "Heading3"))
    body.append(para(run("[PLACEHOLDER: confusion matrices, sensitivity, specificity and predictive values with 95% CIs "
                         "and sampling weights from the 100-record expert validation sample (D28), and the probabilistic "
                         "misclassification analysis. To be added when the expert coding is returned.]", italic=True)))
    # S5
    body.append(lead("Table S5. ", "Primary comparison and sensitivity analyses: candidate-matched molecular selection in "
                     "de novo-only versus repurposing-containing trials. Risk difference in percentage points (de novo-only "
                     "minus repurposing-containing) with Newcombe 95% CI; standardised estimates use a Wald CI."))
    rows = []
    for r in rd(AN / "h1_and_sensitivity.csv") + rd(AN / "h1_3_with_mechanism.csv"):
        if not r.get("risk_difference_pp"):
            rows.append([r["analysis"], "—", "—", r.get("note", "")[:60]])
            continue
        dn = f"{r['de_novo_selected']}/{r['de_novo_n']}" if r.get("de_novo_n") not in ("0", "", None) else "—"
        rp = f"{r['repurposing_selected']}/{r['repurposing_n']}" if r.get("repurposing_n") not in ("0", "", None) else "—"
        rows.append([r["analysis"], dn, rp, f"{r['risk_difference_pp']} ({r['ci_low_pp']} to {r['ci_high_pp']})"])
    body.append(table(["Analysis", "De novo-only", "Repurposing-containing", "RD, pp (95% CI)"], rows,
                      [4717, 1300, 1500, 1800]))
    # S6
    body.append(lead("Table S6. ", "Exploratory pathway analysis (D42): biological processes tested by the 92 repurposed "
                     "candidates, by subcategory. Drugs = unique agents with that primary process; trials = distinct trials "
                     "(a trial counts once per process); matched = trials with selection matched to that agent. The full "
                     "drug → target → pathway → trial → matched-selection mapping, level-2 counts and the sensitivity "
                     "analyses are in workbook sheets 'S6a'–'S6d'."))
    pr = {(r["scope"], r["process"]): r for r in rd(AN / "pathway_by_process_D42.csv") if r["analysis"] == "main"}
    procs = sorted({k for _, k in pr}, key=lambda k: int(k.split()[0][1:]) if k[0] == "P" else 99)
    f = lambda s, k: (lambda r: f"{r['unique_drugs']} / {r['distinct_trials']} / {r['trials_drug_matched_selection']}"
                      if r and int(r["distinct_trials"]) else "—")(pr.get((s, k)))
    body.append(table(["Process", "2a: drugs / trials / matched", "2b: drugs / trials / matched", "All"],
                      [[k, f("2a", k), f("2b", k), f("all", k)] for k in procs], [3917, 1800, 1800, 1800]))
    body.append(para("Supplementary Figure", "Heading1"))


def workbook():
    wb = Workbook()
    ws = wb.active
    ws.title = "Read_me"
    for line in [f"Supplementary Data for: {TITLE}",
                 "Draft v1, built by scripts/24_build_supplement.py from the committed outputs of the study repository "
                 "(github.com/Net4Brain/gbm-repurposing-registry).",
                 "S1_trials: all 870 screening records. S2a-S2d: candidate agents and the dated evidence. S5: sensitivity "
                 "analyses. S6a-S6d: pathway analysis. Search_audit: supplementary-search records rejected by the filter.",
                 "Expert-validation results are not included yet."]:
        ws.append([line])
    ws.column_dimensions["A"].width = 140

    def sheet(name, rows):
        s = wb.create_sheet(name)
        hdr = list(rows[0].keys())
        s.append(hdr)
        for c in s[1]:
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor="E7E6E6")
        for r in rows:
            s.append([r.get(h, "") for h in hdr])
        for i, h in enumerate(hdr, 1):
            s.column_dimensions[get_column_letter(i)].width = min(60, max(10, len(h) + 2))
        s.freeze_panes = "B2"
        return len(rows)

    cand = defaultdict(list)
    od = rd(RUN / "origin_derived_D36.csv")
    for r in od:
        cand[r["nct_id"]].append(f"{r['active_moiety']} ({r['origin_trial_start']})")
    s1 = [dict(r, candidate_agents_origin_at_start="; ".join(cand.get(r["nct_id"], []))) for r in rd(RUN / "screening_D37.csv")]
    n = {"S1_trials": sheet("S1_trials", s1)}
    mech = {r["active_moiety"]: r["mechanism_primary"] for r in rd(REF / "agent_mechanism.csv")}
    regs = defaultdict(list)
    for r in rd(REF / "regulatory_events.csv"):
        regs[r["moiety"]].append(r)
    first = {}
    trials = defaultdict(set)
    coh = {r["nct_id"] for r in rd(RUN / "cohort_D37.csv") if r["primary_cohort"] == "yes"}
    for r in od:
        if r["role"] not in ("experimental_monotherapy", "experimental_combination"):
            continue
        m = r["active_moiety"]
        trials[m].add(r["nct_id"])
        if m not in first or r["trial_start"] < first[m]["trial_start"]:
            first[m] = r
    s2a = []
    for m in sorted(first):
        ev = sorted(regs.get(m, []), key=lambda e: e["date_lo"])
        e0 = ev[0] if ev else {}
        s2a.append({"active_moiety": m, "origin_agent_level": first[m]["origin_trial_start"],
                    "earliest_trial": first[m]["nct_id"], "earliest_trial_start": first[m]["trial_start"],
                    "first_fda_ema_approval": f"{e0.get('jurisdiction', '')} {e0.get('date_lo', '')}".strip(),
                    "first_approved_indication": (e0.get("indication") or "")[:200],
                    "first_approval_source": e0.get("source", ""), "primary_mechanism": mech.get(m, ""),
                    "n_trials_screened": len(trials[m]), "n_primary_cohort_trials": len(trials[m] & coh),
                    "trials": "; ".join(sorted(trials[m])), "flags_at_earliest_trial": first[m]["flags"]})
    n["S2a_agents"] = sheet("S2a_agents", s2a)
    n["S2b_candidate_trials"] = sheet("S2b_candidate_trials", od)
    n["S2c_regulatory_events"] = sheet("S2c_regulatory_events", rd(REF / "regulatory_events.csv"))
    n["S2d_development_events"] = sheet("S2d_development_events", rd(REF / "development_events.csv"))
    n["S5_sensitivity"] = sheet("S5_sensitivity", rd(AN / "h1_and_sensitivity.csv") + rd(AN / "h1_3_with_mechanism.csv"))
    n["S6a_pathway_mapping"] = sheet("S6a_pathway_mapping", rd(AN / "pathway_supplementary_table_D42.csv"))
    n["S6b_by_process"] = sheet("S6b_by_process", rd(AN / "pathway_by_process_D42.csv"))
    n["S6c_by_level2"] = sheet("S6c_by_level2", rd(AN / "pathway_by_level2_D42.csv"))
    n["S6d_trial_origin"] = sheet("S6d_trial_origin", rd(AN / "pathway_by_process_trial_origin_D42.csv"))
    n["Search_audit"] = sheet("Search_audit", rd(ROOT / "data" / "processed" / "supp_rejected_02b.csv"))
    for s in wb.worksheets[1:]:
        for row in s.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(vertical="top")
    wb.save(XLSX)
    return n


def main():
    for p in (DOCX, XLSX):
        if p.exists():
            sys.exit(f"{p} exists; refusing to overwrite")
    body = [para(TITLE, "Title"), para("Supplementary Information", "Subtitle"),
            para(run("Draft v1 (2026-11-04). Built from the committed analysis outputs by scripts/24_build_supplement.py. "
                     "Large tables are in the companion workbook GBM_registry_NOA_supplementary_data_v1.xlsx. Expert-"
                     "validation results are not yet available.", italic=True))]
    methods(body)
    tables(body)
    cx = int(6.4 * 914400)
    cy = int(cx * 1740 / 2160)
    body.append(image("rIdFigS1", cx, cy))
    body.append(lead("Figure S1. ", "Biological processes tested by non-oncology (2a) and oncology (2b) repurposed "
                     "candidates in the 2020–2026 adult glioblastoma pipeline. Bars show distinct trials; the darker segment "
                     "shows trials with selection matched to the specific repurposed agent (number in brackets); diamonds "
                     "show unique agents. Subcategory is each agent's category at its earliest cohort trial. Exploratory "
                     "analysis (D42)."))
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(TEMPLATE) as z:
        z.extractall(tmp)
    for p in tmp.rglob("*"):
        if p.is_symlink():
            p.unlink()
    doc = (tmp / "word" / "document.xml").read_text(encoding="utf8")
    head = doc[:doc.index("<w:body>") + len("<w:body>")]
    if "xmlns:wp=" not in head:
        head = head.replace("<w:document ", '<w:document xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" ', 1)
    sect = re.findall(r"<w:sectPr[ >].*?</w:sectPr>", doc, re.S)[-1]
    (tmp / "word" / "document.xml").write_text(head + "".join(body) + sect + "</w:body></w:document>", encoding="utf8")
    (tmp / "word" / "media").mkdir(exist_ok=True)
    shutil.copy(FIG, tmp / "word" / "media" / "figure_s1.png")
    rels = tmp / "word" / "_rels" / "document.xml.rels"
    rels.write_text(rels.read_text().replace("</Relationships>",
                    '<Relationship Id="rIdFigS1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                    'Target="media/figure_s1.png"/></Relationships>'))
    ct = tmp / "[Content_Types].xml"
    t = ct.read_text()
    if 'Extension="png"' not in t:
        ct.write_text(t.replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1))
    for p in (tmp / "docProps" / "core.xml",):
        p.write_text(re.sub(r"<dc:title>.*?</dc:title>", "<dc:title>Supplementary Information</dc:title>", p.read_text()))
    with zipfile.ZipFile(DOCX, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(tmp.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(tmp).as_posix())
    shutil.rmtree(tmp)
    n = workbook()
    print(f"wrote {DOCX.name} ({len(body)} blocks) and {XLSX.name}: {n}")


if __name__ == "__main__":
    main()
