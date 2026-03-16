"""
Forest plot separated by clinical task (lane), colored by comparison arm type.
Three panels stacked vertically, sorted by effect size within each.

Output: data_v2_offline/extracted/figures/forest_by_task.png
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

BASE   = Path("/Users/anastasiaperezternent/Documents/ai-vs-physician-meta")
DATA   = BASE / "data_v2_offline" / "extracted" / "accuracy_v3_codex.csv"
OUTDIR = BASE / "data_v2_offline" / "extracted" / "figures"
OUTDIR.mkdir(parents=True, exist_ok=True)

LANE_ORDER = [
    "diagnosis_reasoning_v3_core",
    "supplemental_benchmark_implementation",
    "admin_core",
]
LANE_LABELS = {
    "diagnosis_reasoning_v3_core":            "Diagnosis & Reasoning",
    "supplemental_benchmark_implementation":  "Benchmark & Implementation",
    "admin_core":                             "Admin & Workflow",
}

COMP_COLORS = {
    "ai_vs_physician_unaided":                "#123A6D",
    "ai_plus_physician_vs_physician_unaided": "#4E9F6D",
    "ai_vs_physician_with_resources":         "#C78D24",
}
COMP_LABELS = {
    "ai_vs_physician_unaided":                "Standalone AI vs physician",
    "ai_plus_physician_vs_physician_unaided": "AI-assisted physician vs physician",
    "ai_vs_physician_with_resources":         "AI vs physician with resources",
}


def load_rows() -> list[dict]:
    with DATA.open() as fh:
        rows = list(csv.DictReader(fh))
    kept = []
    for r in rows:
        if r["confidence"] == "low":
            continue
        if r["has_quantitative_comparison"] != "true":
            continue
        try:
            ai_val  = float(r["ai_value"])
            phy_val = float(r["physician_value"])
        except (ValueError, TypeError):
            continue
        if ai_val > 1.0 or phy_val > 1.0:
            continue
        r["_diff"] = ai_val - phy_val
        kept.append(r)
    return kept


def draw_panel(ax, rows: list[dict], lane_key: str) -> None:
    label       = LANE_LABELS[lane_key]
    sorted_rows = sorted(rows, key=lambda r: r["_diff"])
    n           = len(sorted_rows)

    for i, r in enumerate(sorted_rows):
        diff  = r["_diff"]
        comp  = r.get("comparison_type", "ai_vs_physician_unaided")
        color = COMP_COLORS.get(comp, "#888888")
        ax.scatter(diff, i, color=color, s=20, zorder=3, linewidths=0)
        ax.plot([0, diff], [i, i], color=color, linewidth=0.7, alpha=0.4, zorder=2)

    ax.axvline(0, color="#333333", linewidth=0.9, linestyle="--", zorder=1)
    ax.axvspan( 0,    0.5, alpha=0.03, color="#123A6D", zorder=0)
    ax.axvspan(-0.5,  0,   alpha=0.03, color="#B44B33", zorder=0)

    median    = float(np.median([r["_diff"] for r in rows]))
    ai_better = sum(1 for r in rows if r["_diff"] > 0)
    hum_better= sum(1 for r in rows if r["_diff"] < 0)

    ax.axvline(median, color="#999999", linewidth=0.8, linestyle=":", alpha=0.7, zorder=1)
    ax.text(median + 0.01, -0.8, f"median {median:+.3f}",
            fontsize=7, color="#666666", va="bottom")

    ax.text( 0.02, n - 0.3, f"AI better: {ai_better}",
             fontsize=7.5, color="#123A6D", va="center")
    ax.text(-0.02, n - 0.3, f"Human better: {hum_better}",
             fontsize=7.5, color="#B44B33", va="center", ha="right")

    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(-1, n + 0.5)
    ax.set_yticks([])
    ax.set_title(f"{label}  (n={n}, median diff {median:+.3f})",
                 fontsize=10, pad=6, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)


def main() -> None:
    rows   = load_rows()
    groups = {lane: [r for r in rows if r.get("lane") == lane]
              for lane in LANE_ORDER}
    active = [lane for lane in LANE_ORDER if groups[lane]]

    heights = [max(3, len(groups[lane])) for lane in active]
    fig_h   = max(10, sum(heights) * 0.22 + 2)

    fig, axes = plt.subplots(
        len(active), 1,
        figsize=(11, fig_h),
        gridspec_kw={"height_ratios": heights},
    )
    if len(active) == 1:
        axes = [axes]

    for ax, lane in zip(axes, active):
        draw_panel(ax, groups[lane], lane)
        ax.set_xlabel("AI − physician (point estimate, mixed metrics)", fontsize=8.5)

    # Shared legend
    seen_comps = {r.get("comparison_type") for r in rows}
    patches = [
        mpatches.Patch(color=COMP_COLORS[c], label=COMP_LABELS[c])
        for c in COMP_COLORS if c in seen_comps
    ]
    fig.legend(handles=patches, loc="lower center", ncol=len(patches),
               fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle(
        "AI vs physician performance by clinical task\n"
        "(156 retained studies, all metrics combined, colored by comparison arm)",
        fontsize=12, y=1.01,
    )

    plt.tight_layout(h_pad=2.5)
    out = OUTDIR / "forest_by_task.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out}")
    for lane in active:
        print(f"  {LANE_LABELS[lane]}: n={len(groups[lane])}")


if __name__ == "__main__":
    main()
