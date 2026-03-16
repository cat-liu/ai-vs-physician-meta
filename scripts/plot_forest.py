"""
Forest plot for the 160 retained quantitative studies.

Shows AI − physician difference per study, grouped by primary metric,
colored by comparison type. Studies are sorted by effect size within
each metric group.

No confidence intervals (abstract-only extraction) — point estimates only.
A dashed reference line at 0 marks parity.

Output: data_v2_offline/extracted/figures/forest_ai_vs_physician.png
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

# ── Comparison type display ───────────────────────────────────────────────────
COMP_LABELS = {
    "ai_vs_physician_unaided":                  "Standalone AI vs physician",
    "ai_plus_physician_vs_physician_unaided":   "AI-assisted physician vs physician",
    "ai_vs_physician_with_resources":           "AI vs physician with resources",
}
COMP_COLORS = {
    "ai_vs_physician_unaided":                  "#123A6D",
    "ai_plus_physician_vs_physician_unaided":   "#4E9F6D",
    "ai_vs_physician_with_resources":           "#C78D24",
}

# Metrics to show (in display order, top → bottom)
METRIC_ORDER = ["accuracy", "auc", "auroc", "sensitivity", "specificity",
                "top1_accuracy", "f1", "dsc", "cancer_detection_rate", "other"]

METRIC_LABELS = {
    "accuracy":             "Accuracy",
    "auc":                  "AUC",
    "auroc":                "AUROC",
    "sensitivity":          "Sensitivity",
    "specificity":          "Specificity",
    "top1_accuracy":        "Top-1 accuracy",
    "f1":                   "F1",
    "dsc":                  "Dice (DSC)",
    "cancer_detection_rate":"Cancer detection rate",
    "other":                "Other",
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
        r["_ai"]  = ai_val
        r["_phy"] = phy_val
        r["_diff"] = round(ai_val - phy_val, 4)
        kept.append(r)

    return kept


def short_title(title: str, max_len: int = 55) -> str:
    return title if len(title) <= max_len else title[:max_len - 1] + "…"


def main() -> None:
    rows = load_rows()
    if not rows:
        print("No usable rows found.")
        return

    # Group by metric
    groups: dict[str, list[dict]] = {}
    for r in rows:
        metric = r.get("primary_metric", "other") or "other"
        if metric not in METRIC_ORDER:
            metric = "other"
        groups.setdefault(metric, []).append(r)

    # Keep only metrics that have at least 1 row, in display order
    active_metrics = [m for m in METRIC_ORDER if m in groups]

    # ── Layout ────────────────────────────────────────────────────────────────
    # Count total rows + 1 spacer row per group header
    n_data_rows = len(rows)
    n_spacer    = len(active_metrics)
    n_total     = n_data_rows + n_spacer * 2   # header + blank separator

    row_height  = 0.28
    fig_height  = max(12, n_total * row_height + 2)
    fig, ax     = plt.subplots(figsize=(13, fig_height))

    y_cursor    = 0           # top-to-bottom; we'll invert y-axis
    yticks      = []
    ylabels     = []

    for metric in active_metrics:
        metric_rows = sorted(groups[metric], key=lambda r: r["_diff"])

        # Group header
        ax.axhline(y_cursor + 0.5, color="#CCCCCC", linewidth=0.6, zorder=0)
        ax.text(
            -0.35, y_cursor,
            METRIC_LABELS.get(metric, metric),
            fontsize=9.5, fontweight="bold", color="#444444",
            va="center", ha="left",
            transform=ax.get_yaxis_transform(),
        )
        y_cursor += 1

        for r in metric_rows:
            diff  = r["_diff"]
            comp  = r.get("comparison_type", "ai_vs_physician_unaided")
            color = COMP_COLORS.get(comp, "#888888")

            # Dot
            ax.scatter(diff, y_cursor, color=color, s=28, zorder=3, linewidths=0)

            # Thin horizontal line from 0 to diff (visual anchor)
            ax.plot([0, diff], [y_cursor, y_cursor],
                    color=color, linewidth=0.8, alpha=0.5, zorder=2)

            # Annotate with AI and physician values on the right
            ax.text(
                0.38, y_cursor,
                f"{r['_ai']:.3f} vs {r['_phy']:.3f}",
                fontsize=6.5, va="center", color="#555555",
            )

            yticks.append(y_cursor)
            ylabels.append(short_title(r["title"]))
            y_cursor += 1

        # Blank row between groups
        y_cursor += 1

    # ── Axes formatting ───────────────────────────────────────────────────────
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=7)
    ax.invert_yaxis()

    ax.axvline(0, color="#333333", linewidth=0.9, linestyle="--", zorder=1)
    ax.set_xlabel("AI − physician (same metric, point estimate)", fontsize=10)
    ax.set_title(
        f"AI vs physician: difference in primary metric across {len(rows)} retained studies\n"
        "(abstract-level extraction, no confidence intervals)",
        fontsize=12, pad=12,
    )

    ax.set_xlim(-0.40, 0.55)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False)

    # Shaded region: AI better / human better
    ax.axvspan(0, 0.55,  alpha=0.03, color="#123A6D", zorder=0)
    ax.axvspan(-0.40, 0, alpha=0.03, color="#B44B33", zorder=0)
    ax.text(0.02, 0.01, "AI better →", transform=ax.transAxes,
            fontsize=8, color="#123A6D", alpha=0.7)
    ax.text(0.35, 0.01, "← Human better", transform=ax.transAxes,
            fontsize=8, color="#B44B33", alpha=0.7)

    # Legend
    legend_patches = [
        mpatches.Patch(color=color, label=COMP_LABELS[comp])
        for comp, color in COMP_COLORS.items()
        if comp in {r.get("comparison_type") for r in rows}
    ]
    ax.legend(
        handles=legend_patches,
        loc="lower right",
        fontsize=8,
        frameon=False,
    )

    plt.tight_layout()
    out = OUTDIR / "forest_ai_vs_physician.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved → {out}")
    print(f"Studies plotted: {len(rows)}")
    from collections import Counter
    print("\nBy metric:")
    for m, g in sorted(groups.items(), key=lambda x: -len(x[1])):
        print(f"  {METRIC_LABELS.get(m, m)}: {len(g)}")
    print("\nBy comparison type:")
    for ct, n in Counter(r.get("comparison_type") for r in rows).most_common():
        print(f"  {COMP_LABELS.get(ct, ct)}: {n}")


if __name__ == "__main__":
    main()
