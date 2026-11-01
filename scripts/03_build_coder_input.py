"""
Step 03 - Build the identical text input that both LLM coders see for each trial.

Takes the frozen snapshots (main + supplementary records listed in
data/processed/supp_added_to_screening.csv) and writes one plain-text record per
trial with only the fields the coding manual refers to.

Outputs: data/coder_input/<NCT>.txt   and   data/coder_input/index.csv

Usage: python3 scripts/03_build_coder_input.py data/raw/ctgov_raw_20261101T130137Z.json \
           data/raw/ctgov_supp_raw_20261101T150223Z.json data/processed/supp_added_to_screening.csv
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "coder_input"


def section(name, text):
    text = (text or "").strip()
    return f"### {name}\n{text if text else '(not provided)'}\n"


def render(study):
    p = study["protocolSection"]
    ident, cond = p["identificationModule"], p.get("conditionsModule", {})
    desc, elig = p.get("descriptionModule", {}), p.get("eligibilityModule", {})
    design, arms = p.get("designModule", {}), p.get("armsInterventionsModule", {})
    outc, spon = p.get("outcomesModule", {}), p.get("sponsorCollaboratorsModule", {})

    arm_lines = [f"- [{a.get('type', '')}] {a.get('label', '')}: {a.get('description', '')} "
                 f"(interventions: {'; '.join(a.get('interventionNames', []))})"
                 for a in arms.get("armGroups", [])]
    int_lines = [f"- [{i.get('type', '')}] {i.get('name', '')}"
                 f"{' (other names: ' + ', '.join(i['otherNames']) + ')' if i.get('otherNames') else ''}: "
                 f"{i.get('description', '')}"
                 for i in arms.get("interventions", [])]
    out_lines = [f"- [{kind}] {o.get('measure', '')}: {o.get('description', '')}"
                 for kind in ("primaryOutcomes", "secondaryOutcomes", "otherOutcomes")
                 for o in outc.get(kind, [])]
    collabs = ", ".join(c.get("name", "") for c in spon.get("collaborators", []))

    return "\n".join([
        f"NCT ID: {ident['nctId']}",
        section("title", f"{ident.get('briefTitle', '')}\nOfficial: {ident.get('officialTitle', '')}"),
        section("conditions", "; ".join(cond.get("conditions", []))),
        section("keywords", "; ".join(cond.get("keywords", []))),
        section("brief_summary", desc.get("briefSummary")),
        section("detailed_description", desc.get("detailedDescription")),
        section("design", f"Phase: {', '.join(design.get('phases', []))}; "
                          f"allocation: {design.get('designInfo', {}).get('allocation', '')}; "
                          f"model: {design.get('designInfo', {}).get('interventionModel', '')}"),
        section("arms", "\n".join(arm_lines)),
        section("interventions", "\n".join(int_lines)),
        section("eligibility", f"Ages: {', '.join(elig.get('stdAges', []))}\n{elig.get('eligibilityCriteria', '')}"),
        section("outcomes", "\n".join(out_lines)),
        section("sponsor", f"Lead: {spon.get('leadSponsor', {}).get('name', '')}; collaborators: {collabs}"),
    ])


def main(main_snapshot, supp_snapshot, supp_list):
    studies = json.loads(Path(main_snapshot).read_text())
    keep = {r["nct_id"] for r in csv.DictReader(open(supp_list))}
    studies += [s for s in json.loads(Path(supp_snapshot).read_text())
                if s["protocolSection"]["identificationModule"]["nctId"] in keep]
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "index.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nct_id", "source", "n_chars"])
        for s in studies:
            nct = s["protocolSection"]["identificationModule"]["nctId"]
            text = render(s)
            (OUT / f"{nct}.txt").write_text(text)
            w.writerow([nct, "supplementary" if nct in keep else "main", len(text)])
    print(f"wrote {len(studies)} coder input files to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
