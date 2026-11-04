"""
Step 15b - Build a worked example for the expert coders: the same coding workbook as the D28 packets, completed for 5
trials that are NOT in the 100-record validation sample. Post-registration processing step.

The 5 trials (chosen to show different situations) were not queued for adjudication because both AI coders agreed on
every priority 1-2 field; the example uses those agreed values. Each is checked to be outside
data/processed/expert_validation_sample.csv. The example teaches the format; it does not tell the experts how any
sample record is coded.

Output folder (refuses to overwrite): outputs/expert_packets_D28_example/
  example_README.html, example_records.html, records/NCTxxxxxxxx.txt, example_completed_workbook.xlsx
Usage: python3 scripts/15b_build_expert_example.py
       python3 scripts/15b_build_expert_example.py --into-packets
         copies the example into outputs/expert_packets_D28/expert_N/04_worked_example/, adds a pointer to each
         00_README.html and rewrites SHA256SUMS.txt (files whose name starts with '.' are skipped)
"""
import csv
import html
import importlib.util
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "expert_packets_D28_example"
EXAMPLES = [  # nct, what it shows
    ("NCT06780592", "targeted drug with a matched biomarker entry requirement (MET IHC -> vebreltinib), temozolomide backbone"),
    ("NCT05190315", "repurposed non-oncology drug added to standard of care; mixed glioma population, historical terminology"),
    ("NCT02546102", "dendritic-cell vaccine (excluded intervention type) with placebo; IDH eligibility and MGMT stratification"),
    ("NCT04487093", "not a glioblastoma trial (NSCLC brain metastases); vaccine with unnamed background drugs"),
    ("NCT04809805", "basket trial open to glioblastoma; 'other' biomarker matched to the candidate"),
]
NOTES = {
    "NCT06780592": "cns5 'unclear': GBM named without WHO 2021 wording or an IDH-wildtype requirement",
    "NCT05190315": "grade 4 glioma wording: historical terminology",
    "NCT02546102": "S6 fails: the only investigational product is a vaccine; temozolomide is the backbone",
    "NCT04487093": "S5 fails: brain metastases of NSCLC, not glioblastoma; agents still listed",
    "NCT04809805": "basket of solid tumours that names glioblastoma; candidate-matched via SLFN12/PDE3A",
}

BM_NOTES = {  # (nct, biomarker) -> note shown before the quote
    ("NCT02546102", "IDH"): "exclusion criterion (IDH-mutant excluded): recorded as eligibility, but it only defines "
                            "CNS5 glioblastoma, so it is not selection (addendum)",
    ("NCT02546102", "MGMT"): "stratification only, not an entry requirement",
}

spec = importlib.util.spec_from_file_location("p", ROOT / "scripts" / "15_build_expert_packets.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def tf(v):
    return "TRUE" if v is True else ("FALSE" if v is False else v)


def main():
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite")
    sample = {r["nct_id"] for r in csv.DictReader(open(ROOT / "data" / "processed" / "expert_validation_sample.csv"))}
    ncts = [n for n, _ in EXAMPLES]
    assert not set(ncts) & sample, "an example trial is in the validation sample"
    adj = {r["nct_id"]: r for r in csv.DictReader(open(ROOT / "outputs" / "main" / "adjudicated_trials_D32.csv"))}
    assert all(adj[n]["source"] == "coders_agreed" for n in ncts)
    (OUT / "records").mkdir(parents=True)
    wb_path = OUT / "example_completed_workbook.xlsx"
    p.workbook(wb_path, "EXAMPLE", ncts)
    wb = load_workbook(wb_path)
    wb["Instructions"]["A1"] = "EXAMPLE - completed for 5 trials that are not in your 100 records. Do not return this file."
    tr, ag, bm = wb["Trials"], wb["Agents"], wb["Biomarkers"]
    a_row, b_row = 3, 3
    for i, n in enumerate(ncts):
        A = json.loads((ROOT / "outputs" / "main" / "coderA" / f"{n}.json").read_text())
        s, t = A["screening"], A["trial"]
        vals = [n, s["gbm_population"], s["cns5_terminology"], tf(s["has_eligible_candidate"]), s["candidate_exclusion_reason"],
                t["treatment_setting"], t["regimen"], "; ".join(t.get("combination_partners") or []), tf(t["basket"]),
                t["control_arm_from_other_arms"], t["tumour_pk_planned"], t["target_engagement_planned"], "high", NOTES[n]]
        for j, v in enumerate(vals, 1):
            tr.cell(3 + i, j, v)
        for x in A["agents"]:
            for j, v in enumerate([n, x["agent_name_registered"], x["active_moiety"], x["role"], tf(x["device_dependent"]),
                                   tf(x["delivery_enabling"]), ""], 1):
                ag.cell(a_row, j, v)
            a_row += 1
        for x in A["biomarkers"]:
            for j, v in enumerate([n, x["biomarker"], x.get("biomarker_other") or "", x["role"], tf(x["candidate_matched"]),
                                   x.get("matched_agent") or "", "; ".join(x.get("arms") or []),
                                   "; ".join(filter(None, [BM_NOTES.get((n, x["biomarker"]), ""),
                                                           "quote: " + x["source_quote"]["quote"][:120]]))], 1):
                bm.cell(b_row, j, v)
            b_row += 1
        (OUT / "records" / f"{n}.txt").write_text((ROOT / "data" / "coder_input" / f"{n}.txt").read_text())
    wb.save(wb_path)
    body = "".join(f"<h2 id='{n}'>{n}</h2><p><i>{html.escape(w)}</i></p><pre>"
                   f"{html.escape((ROOT / 'data' / 'coder_input' / f'{n}.txt').read_text())}</pre>" for n, w in EXAMPLES)
    (OUT / "example_records.html").write_text(p.page("Example records", "<h1>Example records</h1>" + body))
    readme = ("<h1>Worked example</h1><p>This workbook is completed for 5 ClinicalTrials.gov records that are <b>not</b> "
              "among your 100 records. It shows how to fill the Trials, Agents and Biomarkers sheets. Use it as a guide to "
              "the format only; code your own records from the manual and the addendum.</p><ul>"
              + "".join(f"<li><a href='example_records.html#{n}'>{n}</a>: {html.escape(w)}</li>" for n, w in EXAMPLES)
              + "</ul><p>Values are those both study coders agreed on.</p>")
    (OUT / "example_README.html").write_text(p.page("Worked example", readme))
    print(f"example written to {OUT} ({len(ncts)} trials, {a_row - 3} agent rows, {b_row - 3} biomarker rows)")


def into_packets():
    import hashlib
    import shutil
    packets = ROOT / "outputs" / "expert_packets_D28"
    for d in sorted(packets.glob("expert_*")):
        dst = d / "04_worked_example"
        if dst.exists():
            sys.exit(f"{dst} exists; refusing to overwrite")
        shutil.copytree(OUT, dst)
        readme = d / "00_README.html"
        t = readme.read_text()
        add = ("<h2>Worked example</h2><p><a href='04_worked_example/example_README.html'>04_worked_example</a> shows a "
               "completed workbook for 5 trials that are not among your 100 records. It shows the format only.</p>")
        if "04_worked_example" not in t:
            readme.write_text(t.replace("</body>", add + "</body>"))
    with open(packets / "SHA256SUMS.txt", "w") as fh:
        for f in sorted(packets.rglob("*")):
            rel = f.relative_to(packets)
            if f.is_file() and f.name != "SHA256SUMS.txt" and not any(part.startswith(".") for part in rel.parts):
                fh.write(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {rel}\n")
    print(f"example added to {len(list(packets.glob('expert_*')))} packets; SHA256SUMS.txt rewritten")


if __name__ == "__main__":
    into_packets() if sys.argv[1:] == ["--into-packets"] else main()
