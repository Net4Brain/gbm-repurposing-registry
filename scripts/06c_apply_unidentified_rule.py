"""
Step 06c - Apply the unidentified-agent rule (D36) to the output of the frozen 06_derive_origin_v2.py, and derive
trial-origin groups (manual v1.4 section 4.3). Post-registration processing step; 06_derive_origin_v2.py is not
changed.

Rule (D36): a candidate that the registry record does not identify gets origin UNIDENTIFIED. It is excluded from
agent-level counts. At trial level the origin group comes from the identified candidates plus what is certain about the
unidentified one (data/reference/unidentified_agents.csv, column certain_not_fda_ema_approved_at_trial_start):
  - any identified category-2 candidate -> repurposing_containing; repurposing_2a_containing and mixed_origin are
    marked uncertain if an unidentified candidate could itself be category 2;
  - no identified category-2 candidate and every unidentified candidate certainly unapproved at T ->
    unresolved_non_repurposing (category 1 or 3 unknown): excluded from the primary de-novo vs repurposing contrast,
    counted as de_novo_only in sensitivity analysis 16;
  - otherwise -> unresolved.
Release gate (D26): stops with an error if any UNRESOLVED row is not covered by the rule.

Inputs : outputs/main/origin_derived_D35.csv, data/reference/unidentified_agents.csv
Outputs (new files; refuses to overwrite):
  outputs/main/origin_derived_D36.csv      candidate x trial rows, UNRESOLVED -> UNIDENTIFIED where the rule applies
  outputs/main/origin_trial_groups_D36.csv one row per trial: categories present and the section 4.3 groups

Usage: python3 scripts/06c_apply_unidentified_rule.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs" / "main"
CAT2 = {"2a", "2b", "2_panel"}


def main():
    out_rows, out_groups = RUN / "origin_derived_D36.csv", RUN / "origin_trial_groups_D36.csv"
    for p in (out_rows, out_groups):
        if p.exists():
            sys.exit(f"{p} exists; refusing to overwrite")
    unid = {(r["nct_id"], r["active_moiety"]): r["certain_not_fda_ema_approved_at_trial_start"] == "yes"
            for r in csv.DictReader(open(ROOT / "data" / "reference" / "unidentified_agents.csv"))}
    rows = list(csv.DictReader(open(RUN / "origin_derived_D35.csv")))
    for r in rows:
        k = (r["nct_id"], r["active_moiety"])
        if k in unid and r["origin_trial_start"] == "UNRESOLVED":
            r["origin_trial_start"] = r["origin_index_date"] = "UNIDENTIFIED"
            r["flags"] = "; ".join(x for x in [r["flags"], "D36 unidentified agent"] if x)
    left = [(r["nct_id"], r["active_moiety"]) for r in rows if r["origin_trial_start"] == "UNRESOLVED"]
    if left:
        sys.exit(f"release gate closed: UNRESOLVED rows not covered by D36: {left}")
    with open(out_rows, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    by_trial = {}
    for r in rows:
        by_trial.setdefault(r["nct_id"], []).append(r)
    groups = []
    for n, rs in sorted(by_trial.items()):
        cats = [r["origin_trial_start"] for r in rs]
        ident = [c for c in cats if c != "UNIDENTIFIED"]
        un = [r for r in rs if r["origin_trial_start"] == "UNIDENTIFIED"]
        un_can_be_2 = any(not unid[(r["nct_id"], r["active_moiety"])] for r in un)
        g = {"nct_id": n, "categories": "; ".join(sorted(cats)), "n_unidentified": len(un),
             "repurposing_containing": "", "repurposing_2a_containing": "", "de_novo_only": "", "repositioning_only": "",
             "mixed_origin": "", "primary_group": "", "note": ""}
        has2 = any(c in CAT2 for c in ident)
        if has2:
            g["repurposing_containing"] = "yes"
            g["repurposing_2a_containing"] = "yes" if "2a" in ident else ("uncertain" if un_can_be_2 else "no")
            g["mixed_origin"] = "yes" if "1" in ident else ("uncertain" if un else "no")
            g["de_novo_only"] = g["repositioning_only"] = "no"
            g["primary_group"] = "repurposing_containing"
        elif un and not un_can_be_2:
            g.update(repurposing_containing="no", repurposing_2a_containing="no", mixed_origin="no",
                     de_novo_only="uncertain", repositioning_only="uncertain", primary_group="unresolved_non_repurposing",
                     note="D36: excluded from the primary contrast; de_novo_only in sensitivity analysis 16")
        elif un:
            g.update(primary_group="unresolved", note="D36: unidentified candidate may be category 2")
        else:
            g["repurposing_containing"] = g["repurposing_2a_containing"] = g["mixed_origin"] = "no"
            only1, only13 = all(c == "1" for c in ident), all(c in ("1", "3") for c in ident)
            g["de_novo_only"] = "yes" if only1 else "no"
            g["repositioning_only"] = "yes" if (only13 and "3" in ident) else "no"
            g["primary_group"] = "de_novo_only" if only1 else ("repositioning_only" if only13 else "other")
            if not only13:
                g["note"] = "categories outside section 4.3 groups: " + ", ".join(sorted(set(ident) - {"1", "3"}))
        groups.append(g)
    with open(out_groups, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(groups[0].keys()))
        w.writeheader()
        w.writerows(groups)
    from collections import Counter
    print(f"candidate rows {len(rows)} (UNIDENTIFIED {sum(r['origin_trial_start'] == 'UNIDENTIFIED' for r in rows)}); "
          f"trials {len(groups)}; primary groups {dict(Counter(g['primary_group'] for g in groups))}")
    print("release gate open: no UNRESOLVED rows")


if __name__ == "__main__":
    main()
