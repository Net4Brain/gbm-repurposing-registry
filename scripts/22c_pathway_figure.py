"""
Step 22c - Candidate figure for the pathway analysis (D42; exploratory). Post-registration step; reads only.

Input : outputs/analysis_D40/pathway_by_process_D42.csv (script 22, analysis "main", primary pathway)
Figure: level-1 processes as rows; non-oncology (2a) and oncology (2b) repurposing as two panels on one shared count
        axis. Bar = distinct trials (darker segment = trials with drug-matched selection); diamond = unique drugs.
Output: outputs/analysis_D40/figure_pathway_D42.png and .pdf (each refused if it exists)
Usage : python3 scripts/22c_pathway_figure.py
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
AN = ROOT / "outputs" / "analysis_D40"
TRIALS, MATCHED, DRUGS = "#86b6ef", "#1c5cab", "#eb6834"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def main():
    outs = [AN / "figure_pathway_D42.png", AN / "figure_pathway_D42.pdf"]
    for p in outs:
        if p.exists():
            sys.exit(f"{p} exists; refusing to overwrite")
    rows = [r for r in csv.DictReader(open(AN / "pathway_by_process_D42.csv")) if r["analysis"] == "main"]
    get = {(r["scope"], r["process"]): r for r in rows}
    procs = sorted({r["process"] for r in rows if r["scope"] == "all" and int(r["distinct_trials"]) > 0},
                   key=lambda k: (-int(get[("all", k)]["distinct_trials"]), k))
    short = {"Radiation and photo/sonodynamic sensitisation": "Radiation and photo/sono-\ndynamic sensitisation",
             "Proteostasis, nuclear transport and cell death": "Proteostasis, nuclear\ntransport and cell death",
             "RAS–MAPK and PI3K–mTOR signalling": "RAS–MAPK and\nPI3K–mTOR signalling",
             "Receptor tyrosine kinase signalling": "Receptor tyrosine\nkinase signalling",
             "Cytotoxic DNA damage and mitosis": "Cytotoxic DNA\ndamage and mitosis"}
    label = lambda k: short.get(k.split(" ", 1)[1], k.split(" ", 1)[1]) if k[0] == "P" else "Unclear"
    xmax = max(int(r["distinct_trials"]) for r in rows if r["scope"] in ("2a", "2b")) + 6
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "text.color": INK, "axes.labelcolor": MUTED,
                         "xtick.color": MUTED, "ytick.color": INK})
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 5.8), sharey=True, gridspec_kw={"wspace": 0.06})
    y = range(len(procs))
    for ax, scope, title in ((axes[0], "2a", "Non-oncology repurposing (2a)"), (axes[1], "2b", "Oncology repurposing (2b)")):
        for i, k in zip(y, procs):
            r = get.get((scope, k))
            t, m, d = (int(r["distinct_trials"]), int(r["trials_drug_matched_selection"]), int(r["unique_drugs"])) if r else (0, 0, 0)
            if t:
                ax.barh(i, t, height=0.62, color=TRIALS, edgecolor="white", linewidth=0)
                if m:
                    ax.barh(i, m, height=0.62, color=MATCHED, edgecolor="white", linewidth=0)
                ax.text(max(t, d) + 1.2, i, f"{t}" + (f" ({m})" if m else ""), va="center", fontsize=7.5, color=INK)
            if d:
                ax.plot(d, i, marker="D", markersize=5.5, color=DRUGS, markeredgecolor="white", markeredgewidth=1.2,
                        linestyle="none", zorder=3)
        ax.set_title(title, fontsize=9, loc="left", color=INK)
        ax.set_xlim(0, xmax)
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel("Number of trials or drugs")
    axes[0].set_yticks(list(y))
    axes[0].set_yticklabels([label(k) for k in procs])
    axes[0].invert_yaxis()
    fig.legend(handles=[Patch(color=TRIALS, label="Distinct trials"),
                        Patch(color=MATCHED, label="Trials with drug-matched selection (n in brackets)"),
                        Line2D([], [], marker="D", color=DRUGS, linestyle="none", markeredgecolor="white", label="Unique drugs")],
               loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.55, -0.01))
    fig.subplots_adjust(left=0.30, right=0.98, top=0.93, bottom=0.14)
    for p in outs:
        fig.savefig(p, dpi=300)
    print("wrote", ", ".join(p.name for p in outs), "| rows", len(procs))


if __name__ == "__main__":
    main()
