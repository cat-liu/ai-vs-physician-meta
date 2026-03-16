"""
Grouped bar chart of directional win-rate by lane.
Output: data_v2_offline/extracted/figures/winrate_bar.png
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BASE   = Path("/Users/anastasiaperezternent/Documents/ai-vs-physician-meta")
DATA   = BASE / "data_v2_offline" / "extracted" / "win_rate_candidates_conservative.csv"
OUTDIR = BASE / "data_v2_offline" / "extracted" / "figures"
OUTDIR.mkdir(parents=True, exist_ok=True)

LANE_ORDER = [
    "diagnosis_reasoning_v3_core",
    "supplemental_benchmark_implementation",
    "admin_core",
    "patient_facing_core",
]
LANE_LABELS = {
    "diagnosis_reasoning_v3_core":           "Diagnosis &\nReasoning",
    "supplemental_benchmark_implementation": "Benchmark &\nImplementation",
    "admin_core":                            "Admin &\nWorkflow",
    "patient_facing_core":                   "Patient-\nFacing",
}

DIRECTION_ORDER  = ["ai_better_like", "assisted_improvement", "tie_or_noninferior_like", "mixed", "human_better_like"]
DIRECTION_LABELS = {
    "ai_better_like":          "AI better",
    "assisted_improvement":    "AI-assisted improvement",
    "tie_or_noninferior_like": "Tie / noninferior",
    "mixed":                   "Mixed",
    "human_better_like":       "Human better",
}
DIRECTION_COLORS = {
    "ai_better_like":          "#123A6D",
    "assisted_improvement":    "#4E9F6D",
    "tie_or_noninferior_like": "#9AA3AD",
    "mixed":                   "#C78D24",
    "human_better_like":       "#B44B33",
}


def main() -> None:
    with DATA.open() as fh:
        all_rows = list(csv.DictReader(fh))

    groups = {lane: [r for r in all_rows if r["lane"] == lane] for lane in LANE_ORDER}
    active = [lane for lane in LANE_ORDER if groups[lane]]

    # Build % matrix: rows=direction, cols=lane
    pcts = {d: [] for d in DIRECTION_ORDER}
    ns   = []
    for lane in active:
        rows = groups[lane]
        n    = len(rows)
        ns.append(n)
        c = Counter(r["direction_class"] for r in rows)
        for d in DIRECTION_ORDER:
            pcts[d].append(c[d] / n * 100)

    x      = np.arange(len(active))
    labels = [LANE_LABELS[l] for l in active]

    fig, ax = plt.subplots(figsize=(10, 6))

    bottom = np.zeros(len(active))
    for d in DIRECTION_ORDER:
        vals = np.array(pcts[d])
        bars = ax.bar(x, vals, bottom=bottom, color=DIRECTION_COLORS[d],
                      label=DIRECTION_LABELS[d], width=0.55)
        # Label segments > 5%
        for i, (v, b) in enumerate(zip(vals, bottom)):
            if v >= 5:
                ax.text(x[i], b + v / 2, f"{v:.0f}%",
                        ha="center", va="center", fontsize=9,
                        color="white", fontweight="bold")
        bottom += vals

    # n labels above bars
    for i, n in enumerate(ns):
        ax.text(x[i], 101, f"n={n}", ha="center", va="bottom", fontsize=8.5, color="#555555")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("% of directional abstracts", fontsize=10)
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title(
        "Directional outcome across 951 studies\n(abstract-level language classification)",
        fontsize=12, pad=10,
    )
    ax.legend(loc="upper right", fontsize=8.5, frameon=False)

    plt.tight_layout()
    out = OUTDIR / "winrate_bar.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out}")


if __name__ == "__main__":
    main()
