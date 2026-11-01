"""
Step 07 - Compare Coder A and Coder B (coding manual section 7, D15).

Reads outputs/coderA/<NCT>.json and outputs/coderB/<NCT>.json, validates each against the schema,
and writes:
  outputs/<run>/adjudication_queue.csv   one row per disagreement or uncertain item
  outputs/<run>/agreement.csv            per-variable agreement before adjudication:
                                         % agreement, Cohen's kappa, PABAK, Gwet's AC1, n

Usage: python3 scripts/07_compare_coders.py outputs/calibration
       (expects outputs/calibration/coderA/ and outputs/calibration/coderB/)
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema" / "trial_coding.schema.json").read_text())

FIELDS = [  # (variable name, getter)
    ("gbm_population", lambda d: d["screening"]["gbm_population"]),
    ("has_eligible_candidate", lambda d: d["screening"]["has_eligible_candidate"]),
    ("candidate_exclusion_reason", lambda d: d["screening"]["candidate_exclusion_reason"]),
    ("cns5_terminology", lambda d: d["screening"]["cns5_terminology"]),
    ("treatment_setting", lambda d: d["trial"]["treatment_setting"]),
    ("regimen", lambda d: d["trial"]["regimen"]),
    ("basket", lambda d: d["trial"]["basket"]),
    ("candidate_set", lambda d: tuple(sorted({a["active_moiety"].lower() for a in d["agents"]
                                               if a["role"].startswith("experimental_")}))),
    ("candidate_matched_selection", lambda d: any(b["candidate_matched"] and b["role"] in ("eligibility", "enrichment")
                                                  for b in d["biomarkers"])),
    ("any_molecular_selection", lambda d: any(b["role"] in ("eligibility", "enrichment") for b in d["biomarkers"])),
]


def kappa_stats(pairs):
    n = len(pairs)
    if n == 0:
        return {}
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    cats = set(ca) | set(cb)
    pe = sum(ca[c] * cb[c] for c in cats) / n ** 2
    k = len(cats)
    pi = {c: (ca[c] + cb[c]) / (2 * n) for c in cats}
    pe_ac1 = sum(p * (1 - p) for p in pi.values()) / (k - 1) if k > 1 else 0
    return {"n": n, "pct_agree": round(po, 3),
            "kappa": round((po - pe) / (1 - pe), 3) if pe < 1 else None,
            "pabak": round((k * po - 1) / (k - 1), 3) if k > 1 else None,
            "gwet_ac1": round((po - pe_ac1) / (1 - pe_ac1), 3) if k > 1 and pe_ac1 < 1 else None,
            "categories": k}


def uncertain_items(d):
    out = []
    for key in ("gbm_population_flag", "candidate_flag"):
        if d["screening"][key]["uncertain"]:
            out.append((key, d["screening"][key].get("reason", "")))
    if d["trial"]["flag"]["uncertain"]:
        out.append(("trial", d["trial"]["flag"].get("reason", "")))
    out += [(f"agent:{a['active_moiety']}", a["flag"].get("reason", "")) for a in d["agents"] if a["flag"]["uncertain"]]
    out += [(f"biomarker:{b['biomarker']}", b["flag"].get("reason", "")) for b in d["biomarkers"] if b["flag"]["uncertain"]]
    return out


def quotes(d):
    q = [e for k in ("gbm_population_evidence", "candidate_evidence") for e in d["screening"][k]]
    q += d["trial"]["treatment_setting_evidence"]
    q += [e for a in d["agents"] for e in a["role_evidence"]]
    q += [b["source_quote"] for b in d["biomarkers"]]
    return q


def not_verbatim(d, record):
    """Evidence quotes that do not appear word for word in the coder input (whitespace-normalised)."""
    norm = lambda s: " ".join(s.split())
    text = norm(record)
    return [e["quote"] for e in quotes(d) if norm(e["quote"]) not in text]


def main(run_dir):
    run = Path(run_dir)
    inputs = ROOT / "data" / "coder_input"
    queue, pairs = [], {name: [] for name, _ in FIELDS}
    ids = sorted({p.stem for p in (run / "coderA").glob("NCT*.json")} | {p.stem for p in (run / "coderB").glob("NCT*.json")})
    for nct in ids:
        docs = {}
        for c in ("A", "B"):
            path = run / f"coder{c}" / f"{nct}.json"
            if not path.exists():
                queue.append([nct, "missing_output", f"coder {c}", "", ""])
                continue
            try:
                docs[c] = json.loads(path.read_text())
                jsonschema.validate(docs[c], SCHEMA)
            except (json.JSONDecodeError, jsonschema.ValidationError) as e:
                queue.append([nct, "invalid_output", f"coder {c}", str(e)[:200], ""])
                docs.pop(c, None)
        record = (inputs / f"{nct}.txt").read_text()
        for c, d in docs.items():
            for q in not_verbatim(d, record):
                queue.append([nct, "quote_not_verbatim", f"coder {c}", q[:200], ""])
        if len(docs) < 2:
            continue
        for name, get in FIELDS:
            a, b = get(docs["A"]), get(docs["B"])
            pairs[name].append((a, b))
            if a != b:
                queue.append([nct, "disagreement", name, json.dumps(a), json.dumps(b)])
        roles = {c: {x["active_moiety"].lower(): x["role"] for x in docs[c]["agents"]} for c in docs}
        for m in sorted(set(roles["A"]) & set(roles["B"])):
            if roles["A"][m] != roles["B"][m]:
                queue.append([nct, "disagreement", f"role:{m}", roles["A"][m], roles["B"][m]])
        for c in ("A", "B"):
            for item, reason in uncertain_items(docs[c]):
                queue.append([nct, "uncertain", f"coder {c}: {item}", reason, ""])
    with open(run / "adjudication_queue.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nct_id", "type", "item", "coder_A_or_detail", "coder_B", "decision", "decided_by", "reason"])
        w.writerows(row + ["", "", ""] for row in queue)
    stats = [{"variable": name, **kappa_stats(p)} for name, p in pairs.items()]
    with open(run / "agreement.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["variable", "n", "pct_agree", "kappa", "pabak", "gwet_ac1", "categories"])
        w.writeheader()
        w.writerows(s for s in stats if s.get("n"))
    print(f"{len(ids)} trials; {len(queue)} queue rows -> {run / 'adjudication_queue.csv'}")
    for s in stats:
        if s.get("n"):
            print(f"  {s['variable']:30} agree={s['pct_agree']} kappa={s['kappa']} pabak={s['pabak']} ac1={s['gwet_ac1']}")


if __name__ == "__main__":
    main(sys.argv[1])
