"""
Parliament-style dot chart showing directional win-rate.
Each dot = one study, colored by outcome.
One panel per lane, dots arranged in rows of 20.

Output: data_v2_offline/extracted/figures/winrate_parliament.png
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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
    "diagnosis_reasoning_v3_core":           "Diagnosis & Reasoning",
    "supplemental_benchmark_implementation": "Benchmark & Implementation",
    "admin_core":                            "Admin & Workflow",
    "patient_facing_core":                   "Patient-Facing",
}

# Direction order within each row: AI wins left → human wins right
DIRECTION_ORDER = [
    "ai_better_like",
    "assisted_improvement",
    "tie_or_noninferior_like",
    "mixed",
    "human_better_like",
]
DIRECTION_COLORS = {
    "ai_better_like":          "#123A6D",
    "assisted_improvement":    "#4E9F6D",
    "tie_or_noninferior_like": "#9AA3AD",
    "mixed":                   "#C78D24",
    "human_better_like":       "#B44B33",
}
DIRECTION_LABELS = {
    "ai_better_like":          "AI better",
    "assisted_improvement":    "AI-assisted improvement",
    "tie_or_noninferior_like": "Tie / noninferior",
    "mixed":                   "Mixed",
    "human_better_like":       "Human better",
}

DOTS_PER_ROW = 25
DOT_SIZE     = 55
DOT_SPACING  = 1.0


def draw_panel(ax, rows: list[dict], lane_key: str) -> None:
    label = LANE_LABELS[lane_key]
    n     = len(rows)

    # Sort by direction order
    order_map = {d: i for i, d in enumerate(DIRECTION_ORDER)}
    sorted_rows = sorted(rows, key=lambda r: order_map.get(r["direction_class"], 99))

    # Lay out dots in rows
    for idx, r in enumerate(sorted_rows):
        col   = idx % DOTS_PER_ROW
        row   = idx // DOTS_PER_ROW
        color = DIRECTION_COLORS.get(r["direction_class"], "#cccccc")
        ax.scatter(col * DOT_SPACING, row * DOT_SPACING,
                   color=color, s=DOT_SIZE, zorder=2, linewidths=0)

    n_rows   = math.ceil(n / DOTS_PER_ROW)
    counts   = Counter(r["direction_class"] for r in rows)
    ai_pct   = (counts["ai_better_like"] + counts["assisted_improvement"]) / n * 100
    hum_pct  = counts["human_better_like"] / n * 100

    ax.set_xlim(-0.5, DOTS_PER_ROW * DOT_SPACING)
    ax.set_ylim(-0.8, n_rows * DOT_SPACING + 0.5)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # Title with win rate summary
    ax.set_title(
        f"{label}  (n={n})    "
        f"AI better: {counts['ai_better_like']} ({counts['ai_better_like']/n*100:.0f}%)  "
        f"Assisted: {counts['assisted_improvement']} ({counts['assisted_improvement']/n*100:.0f}%)  "
        f"Tie: {counts['tie_or_noninferior_like']} ({counts['tie_or_noninferior_like']/n*100:.0f}%)  "
        f"Human better: {counts['human_better_like']} ({counts['human_better_like']/n*100:.0f}%)",
        fontsize=9, pad=6, loc="left",
    )


def main() -> None:
    with DATA.open() as fh:
        all_rows = list(csv.DictReader(fh))

    groups = {lane: [r for r in all_rows if r["lane"] == lane]
              for lane in LANE_ORDER}
    active = [lane for lane in LANE_ORDER if groups[lane]]

    # Height proportional to number of dot rows per lane
    heights = [math.ceil(len(groups[lane]) / DOTS_PER_ROW) for lane in active]
    fig_h   = max(6, sum(heights) * 0.9 + 2)

    fig, axes = plt.subplots(
        len(active), 1,
        figsize=(13, fig_h),
        gridspec_kw={"height_ratios": heights},
    )
    if len(active) == 1:
        axes = [axes]

    for ax, lane in zip(axes, active):
        draw_panel(ax, groups[lane], lane)

    # Legend
    patches = [
        mpatches.Patch(color=DIRECTION_COLORS[d], label=DIRECTION_LABELS[d])
        for d in DIRECTION_ORDER
    ]
    fig.legend(handles=patches, loc="lower center", ncol=len(patches),
               fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, -0.03))

    total = sum(len(groups[l]) for l in active)
    fig.suptitle(
        f"Directional win-rate across {total} studies  (each dot = one study)",
        fontsize=13, y=1.01,
    )

    plt.tight_layout(h_pad=2.0)
    out = OUTDIR / "winrate_parliament.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out}")
    for lane in active:
        c = Counter(r["direction_class"] for r in groups[lane])
        n = len(groups[lane])
        print(f"  {LANE_LABELS[lane]}: n={n}  AI={c['ai_better_like']} ({c['ai_better_like']/n*100:.0f}%)  Human={c['human_better_like']} ({c['human_better_like']/n*100:.0f}%)")


if __name__ == "__main__":
    main()
