"""
Forest plot separated by comparison arm type.
All metrics combined as "performance" (point estimate difference).
Three panels stacked vertically, sorted by effect size within each.

Output: data_v2_offline/extracted/figures/forest_by_arm.png
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

ARM_ORDER = [
    "ai_vs_physician_unaided",
    "ai_plus_physician_vs_physician_unaided",
    "ai_vs_physician_with_resources",
]
ARM_LABELS = {
    "ai_vs_physician_unaided":                "Standalone AI vs unaided physician",
    "ai_plus_physician_vs_physician_unaided": "AI-assisted physician vs physician alone",
    "ai_vs_physician_with_resources":         "AI vs physician with resources",
}
ARM_COLORS = {
    "ai_vs_physician_unaided":                "#123A6D",
    "ai_plus_physician_vs_physician_unaided": "#4E9F6D",
    "ai_vs_physician_with_resources":         "#C78D24",
}

METRIC_LABELS = {
    "accuracy": "ACC", "auc": "AUC", "auroc": "AUC",
    "sensitivity": "SEN", "specificity": "SPE",
    "top1_accuracy": "TOP1", "f1": "F1", "dsc": "DSC",
    "cancer_detection_rate": "CDR",
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
        r["_diff"]   = ai_val - phy_val
        r["_ai"]     = ai_val
        r["_phy"]    = phy_val
        r["_metric"] = METRIC_LABELS.get(r.get("primary_metric", ""), "")
        kept.append(r)
    return kept


def draw_panel(ax, rows: list[dict], arm_key: str) -> None:
    color  = ARM_COLORS[arm_key]
    label  = ARM_LABELS[arm_key]
    sorted_rows = sorted(rows, key=lambda r: r["_diff"])
    n = len(sorted_rows)

    for i, r in enumerate(sorted_rows):
        diff = r["_diff"]
        ax.scatter(diff, i, color=color, s=20, zorder=3, linewidths=0)
        ax.plot([0, diff], [i, i], color=color, linewidth=0.7, alpha=0.4, zorder=2)

        # Metric label on right
        ax.text(0.42, i, r["_metric"], fontsize=6, color="#888888", va="center")

    # Zero line
    ax.axvline(0, color="#333333", linewidth=0.9, linestyle="--", zorder=1)

    # Shading
    ax.axvspan(0,    0.5, alpha=0.03, color="#123A6D", zorder=0)
    ax.axvspan(-0.5, 0,   alpha=0.03, color="#B44B33", zorder=0)

    # Median
    median = float(np.median([r["_diff"] for r in rows]))
    ax.axvline(median, color=color, linewidth=0.8, linestyle=":", alpha=0.6, zorder=1)

    # Count AI better / human better
    ai_better  = sum(1 for r in rows if r["_diff"] > 0)
    hum_better = sum(1 for r in rows if r["_diff"] < 0)

    # Direction labels at top
    ax.text( 0.02, n - 0.3, f"AI better: {ai_better}",
             fontsize=7.5, color="#123A6D", va="center")
    ax.text(-0.02, n - 0.3, f"Human better: {hum_better}",
             fontsize=7.5, color="#B44B33", va="center", ha="right")

    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(-1, n + 0.5)
    ax.set_yticks([])
    ax.set_title(f"{label}  (n={n}, median diff {median:+.3f})",
                 fontsize=10, pad=6, color=color, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)


def main() -> None:
    rows = load_rows()
    groups = {arm: [r for r in rows if r.get("comparison_type") == arm]
              for arm in ARM_ORDER}
    active = [arm for arm in ARM_ORDER if groups[arm]]

    heights = [max(3, len(groups[arm])) for arm in active]
    total_h = sum(heights) + len(active) * 1.5
    fig_h   = max(10, total_h * 0.22 + 2)

    fig, axes = plt.subplots(
        len(active), 1,
        figsize=(11, fig_h),
        gridspec_kw={"height_ratios": heights},
    )
    if len(active) == 1:
        axes = [axes]

    for ax, arm in zip(axes, active):
        draw_panel(ax, groups[arm], arm)
        ax.set_xlabel("AI − physician (point estimate, mixed metrics)", fontsize=8.5)

    fig.suptitle(
        "AI vs physician performance by comparison arm\n"
        "(156 retained studies, all metrics combined, abstract-level extraction)",
        fontsize=12, y=1.01,
    )

    plt.tight_layout(h_pad=2.5)
    out = OUTDIR / "forest_by_arm.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out}")
    for arm in active:
        print(f"  {ARM_LABELS[arm]}: n={len(groups[arm])}")


if __name__ == "__main__":
    main()
