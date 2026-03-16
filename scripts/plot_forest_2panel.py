"""
Two-panel forest plot: Accuracy (left) and AUC (right).
No paper titles — studies shown as numbered dots sorted by effect size.
Colored by comparison type.

Output: data_v2_offline/extracted/figures/forest_2panel.png
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

COMP_LABELS = {
    "ai_vs_physician_unaided":                "Standalone AI vs physician",
    "ai_plus_physician_vs_physician_unaided": "AI-assisted physician vs physician",
    "ai_vs_physician_with_resources":         "AI vs physician with resources",
}
COMP_COLORS = {
    "ai_vs_physician_unaided":                "#123A6D",
    "ai_plus_physician_vs_physician_unaided": "#4E9F6D",
    "ai_vs_physician_with_resources":         "#C78D24",
}


def load_rows(metric: str) -> list[dict]:
    with DATA.open() as fh:
        rows = list(csv.DictReader(fh))
    kept = []
    for r in rows:
        if r["confidence"] == "low":
            continue
        if r["has_quantitative_comparison"] != "true":
            continue
        if r.get("primary_metric", "") != metric:
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
    return sorted(kept, key=lambda r: r["_diff"])


def draw_panel(ax, rows: list[dict], title: str) -> None:
    comp_types = sorted({r.get("comparison_type", "") for r in rows})

    for i, r in enumerate(rows):
        comp  = r.get("comparison_type", "ai_vs_physician_unaided")
        color = COMP_COLORS.get(comp, "#888888")
        diff  = r["_diff"]

        ax.scatter(diff, i, color=color, s=22, zorder=3, linewidths=0)
        ax.plot([0, diff], [i, i], color=color, linewidth=0.7, alpha=0.45, zorder=2)

    ax.axvline(0, color="#333333", linewidth=1.0, linestyle="--", zorder=1)
    ax.axvspan(0,    0.6,  alpha=0.03, color="#123A6D", zorder=0)
    ax.axvspan(-0.5, 0,    alpha=0.03, color="#B44B33", zorder=0)

    ax.set_xlim(-0.5, 0.6)
    ax.set_ylim(-1, len(rows))
    ax.set_yticks([])
    ax.set_xlabel("AI − physician (point estimate)", fontsize=9)
    ax.set_title(f"{title}\nn = {len(rows)}", fontsize=11, pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # Median line
    median = float(np.median([r["_diff"] for r in rows]))
    ax.axvline(median, color="#999999", linewidth=0.8, linestyle=":", zorder=1)
    ax.text(median + 0.01, -0.8, f"median {median:+.3f}",
            fontsize=7.5, color="#666666", va="bottom")

    # AI better / human better labels — placed just above the top of the data
    top_y = len(rows) - 0.5
    ax.text(0.08, top_y, "AI better →",    fontsize=8, color="#123A6D",
            alpha=0.85, va="center", ha="left")
    ax.text(-0.08, top_y, "← Human better", fontsize=8, color="#B44B33",
            alpha=0.85, va="center", ha="right")


def main() -> None:
    acc_rows = load_rows("accuracy")
    auc_rows = load_rows("auc")

    fig, axes = plt.subplots(1, 2, figsize=(13, max(8, max(len(acc_rows), len(auc_rows)) * 0.18 + 2)),
                             sharey=False)

    draw_panel(axes[0], acc_rows, "Accuracy")
    draw_panel(axes[1], auc_rows, "AUC")

    # Shared legend
    seen_comps = {r.get("comparison_type") for r in acc_rows + auc_rows}
    patches = [
        mpatches.Patch(color=COMP_COLORS[c], label=COMP_LABELS[c])
        for c in COMP_COLORS if c in seen_comps
    ]
    fig.legend(handles=patches, loc="lower center", ncol=len(patches),
               fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("AI vs physician performance: accuracy and AUC\n"
                 "(retained quantitative studies, abstract-level extraction, no CIs)",
                 fontsize=12, y=1.01)

    plt.tight_layout()
    out = OUTDIR / "forest_2panel.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out}  (accuracy n={len(acc_rows)}, AUC n={len(auc_rows)})")


if __name__ == "__main__":
    main()
