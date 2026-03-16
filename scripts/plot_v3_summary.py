from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


BASE = Path("/Users/anastasiaperezternent/Documents/ai-vs-physician-meta")
DATA = BASE / "data_v2_offline" / "extracted" / "accuracy_v3_codex.csv"
OUTDIR = BASE / "data_v2_offline" / "extracted" / "figures"
WINRATE = BASE / "data_v2_offline" / "extracted" / "win_rate_summary_conservative.csv"


def load_usable_rows() -> list[dict[str, str]]:
    with DATA.open() as handle:
        rows = list(csv.DictReader(handle))
    return [
        row
        for row in rows
        if row["confidence"] != "low" and row["has_quantitative_comparison"] == "true"
    ]


def direction_label(value: str) -> str:
    if value == "true":
        return "AI better"
    if value == "false":
        return "Human better"
    return "Unclear / tie"


def prettify_comparison_type(value: str) -> str:
    mapping = {
        "ai_vs_physician_unaided": "Standalone AI vs physician",
        "ai_plus_physician_vs_physician_unaided": "AI-assisted physician vs physician alone",
        "ai_vs_physician_with_resources": "AI vs physician with resources",
    }
    return mapping.get(value, value)


def prettify_lane(value: str) -> str:
    mapping = {
        "diagnosis_reasoning_v3_core": "Diagnosis / reasoning",
        "supplemental_benchmark_implementation": "Supplemental",
        "admin_core": "Admin",
        "patient_facing_core": "Patient-facing",
    }
    return mapping.get(value, value)


def save_stacked_direction_by_comparison(rows: list[dict[str, str]]) -> Path:
    order = [
        "ai_vs_physician_unaided",
        "ai_plus_physician_vs_physician_unaided",
        "ai_vs_physician_with_resources",
    ]
    labels = [prettify_comparison_type(v) for v in order]
    directions = ["AI better", "Human better", "Unclear / tie"]
    colors = {
        "AI better": "#123A6D",
        "Human better": "#B44B33",
        "Unclear / tie": "#9AA3AD",
    }

    counts = {direction: [] for direction in directions}
    for comp in order:
        comp_rows = [r for r in rows if r["comparison_type"] == comp]
        counter = Counter(direction_label(r["ai_better"]) for r in comp_rows)
        for direction in directions:
            counts[direction].append(counter.get(direction, 0))

    fig, ax = plt.subplots(figsize=(11, 6.5))
    bottom = [0] * len(order)
    for direction in directions:
        ax.bar(labels, counts[direction], bottom=bottom, label=direction, color=colors[direction])
        for i, value in enumerate(counts[direction]):
            if value:
                ax.text(i, bottom[i] + value / 2, str(value), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        bottom = [b + v for b, v in zip(bottom, counts[direction])]

    ax.set_title("Direction of retained quantitative rows by comparison type", fontsize=15, pad=14)
    ax.set_ylabel("Number of adjudicated rows")
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=0, ha="center")
    plt.tight_layout()

    out = OUTDIR / "v3_direction_by_comparison_type.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out


def save_metric_heatmap(rows: list[dict[str, str]]) -> Path:
    comparison_order = [
        "ai_vs_physician_unaided",
        "ai_plus_physician_vs_physician_unaided",
        "ai_vs_physician_with_resources",
    ]
    metric_order = [
        "accuracy",
        "auc",
        "sensitivity",
        "specificity",
        "top1_accuracy",
        "cancer_detection_rate",
        "auroc",
    ]

    matrix = []
    for metric in metric_order:
        row_counts = []
        for comp in comparison_order:
            row_counts.append(
                sum(1 for r in rows if r["primary_metric"] == metric and r["comparison_type"] == comp)
            )
        matrix.append(row_counts)

    fig, ax = plt.subplots(figsize=(11, 6.5))
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(comparison_order)))
    ax.set_xticklabels([prettify_comparison_type(v) for v in comparison_order], rotation=20, ha="right")
    ax.set_yticks(range(len(metric_order)))
    ax.set_yticklabels(metric_order)
    ax.set_title("Metric mix within retained quantitative rows", fontsize=15, pad=14)

    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            ax.text(j, i, str(value), ha="center", va="center", color="#111111", fontsize=10)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Count")
    plt.tight_layout()

    out = OUTDIR / "v3_metric_mix_heatmap.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out


def save_direction_by_lane(rows: list[dict[str, str]]) -> Path:
    lane_order = ["diagnosis_reasoning_v3_core", "supplemental_benchmark_implementation", "admin_core"]
    labels = [prettify_lane(v) for v in lane_order]
    directions = ["AI better", "Human better", "Unclear / tie"]
    colors = {
        "AI better": "#123A6D",
        "Human better": "#B44B33",
        "Unclear / tie": "#9AA3AD",
    }

    counts = defaultdict(list)
    for lane in lane_order:
        lane_rows = [r for r in rows if r["lane"] == lane]
        counter = Counter(direction_label(r["ai_better"]) for r in lane_rows)
        for direction in directions:
            counts[direction].append(counter.get(direction, 0))

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = [0] * len(lane_order)
    for direction in directions:
        ax.bar(labels, counts[direction], bottom=bottom, label=direction, color=colors[direction])
        for i, value in enumerate(counts[direction]):
            if value:
                ax.text(i, bottom[i] + value / 2, str(value), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        bottom = [b + v for b, v in zip(bottom, counts[direction])]

    ax.set_title("Direction of retained quantitative rows by source lane", fontsize=15, pad=14)
    ax.set_ylabel("Number of adjudicated rows")
    ax.legend(frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = OUTDIR / "v3_direction_by_lane.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out


def save_chen_style_directional_plot() -> Path:
    with WINRATE.open() as handle:
        summary = list(csv.DictReader(handle))

    order = [
        "diagnosis_reasoning_v3_core",
        "supplemental_benchmark_implementation",
        "admin_core",
        "patient_facing_core",
    ]
    lane_map = {row["lane"]: row for row in summary}
    labels = [prettify_lane(v) for v in order]
    series = {
        "AI better-like": [int(lane_map[v]["ai_better_like"]) for v in order],
        "Human better-like": [int(lane_map[v]["human_better_like"]) for v in order],
        "Tie / noninferior-like": [int(lane_map[v]["tie_or_noninferior_like"]) for v in order],
        "Assisted improvement": [int(lane_map[v]["assisted_improvement"]) for v in order],
        "Mixed": [int(lane_map[v]["mixed"]) for v in order],
    }
    colors = {
        "AI better-like": "#123A6D",
        "Human better-like": "#B44B33",
        "Tie / noninferior-like": "#9AA3AD",
        "Assisted improvement": "#4E9F6D",
        "Mixed": "#C78D24",
    }

    fig, ax = plt.subplots(figsize=(11.5, 7))
    bottom = [0] * len(order)
    for name, values in series.items():
        ax.bar(labels, values, bottom=bottom, label=name, color=colors[name])
        for i, value in enumerate(values):
            if value >= 10:
                ax.text(i, bottom[i] + value / 2, str(value), ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        bottom = [b + v for b, v in zip(bottom, values)]

    total_directional = sum(int(row["directional_n"]) for row in summary)
    ax.set_title(f"Chen-style broad directional read of current corpus (n={total_directional})", fontsize=15, pad=14)
    ax.set_ylabel("Directional abstracts")
    ax.legend(frameon=False, ncol=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out = OUTDIR / "chen_style_directional_summary.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    rows = load_usable_rows()
    outputs = [
        save_stacked_direction_by_comparison(rows),
        save_metric_heatmap(rows),
        save_direction_by_lane(rows),
        save_chen_style_directional_plot(),
    ]
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
