from __future__ import annotations

from pathlib import Path

import pandas as pd


LANES = [
    "diagnosis_reasoning_v3_core",
    "patient_facing_core",
    "admin_core",
    "supplemental_benchmark_implementation",
]

BETTER_PATTERNS = [
    "outperform",
    "outperformed",
    "superior",
    "better than",
    "improved",
]

WORSE_PATTERNS = [
    "inferior",
    "worse than",
    "underperform",
    "underperformed",
]

TIE_PATTERNS = [
    "comparable",
    "noninferior",
    "no significant difference",
    "similar performance",
    "equivalent",
]

ASSISTED_PATTERNS = [
    "assisted",
    "unassisted",
    "with ai",
    "without ai",
    "doctor+ai",
    "physician-only",
    "ai-only",
    "human-ai collaboration",
    "collaborative",
]


def classify_direction(text: str) -> str:
    t = (text or "").lower()
    better = any(x in t for x in BETTER_PATTERNS)
    worse = any(x in t for x in WORSE_PATTERNS)
    tie = any(x in t for x in TIE_PATTERNS)

    count = sum([better, worse, tie])
    if count == 0:
        return "no_direction"
    if count > 1:
        return "mixed"
    if better:
        return "ai_better_like"
    if worse:
        return "human_better_like"
    return "tie_or_noninferior_like"


def classify_comparison_structure(text: str) -> str:
    t = (text or "").lower()
    if any(x in t for x in ASSISTED_PATTERNS):
        if "ai-only" in t and ("physician-only" in t or "doctor+ai" in t or "human-ai collaboration" in t):
            return "three_arm_or_assisted"
        return "assisted_or_collaborative"
    return "ai_vs_human_unspecified"


def build() -> None:
    base = Path("data_v2_offline/extracted")
    all_rows = []
    summary_rows = []

    for lane in LANES:
        p = base / lane / "included.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p)
        if df.empty:
            continue

        text = (df["title"].fillna("") + " " + df["abstract"].fillna("")).astype(str)
        df = df.copy()
        df["lane"] = lane
        df["direction_class"] = text.apply(classify_direction)
        df["comparison_structure"] = text.apply(classify_comparison_structure)
        directional = df[df["direction_class"] != "no_direction"].copy()
        all_rows.append(directional)

        counts = directional["direction_class"].value_counts()
        n = len(directional)
        summary_rows.append(
            {
                "lane": lane,
                "directional_n": n,
                "ai_better_like": int(counts.get("ai_better_like", 0)),
                "human_better_like": int(counts.get("human_better_like", 0)),
                "tie_or_noninferior_like": int(counts.get("tie_or_noninferior_like", 0)),
                "mixed": int(counts.get("mixed", 0)),
                "ai_better_like_rate": round(counts.get("ai_better_like", 0) / n, 3) if n else None,
            }
        )

    directional_df = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    summary_df = pd.DataFrame(summary_rows).sort_values("lane")

    out_dir = base
    directional_path = out_dir / "win_rate_candidates.csv"
    summary_path = out_dir / "win_rate_summary.csv"
    md_path = out_dir / "WIN_RATE_SUMMARY.md"

    directional_df.to_csv(directional_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    md_lines = [
        "# Win-Rate Summary",
        "",
        "First-pass directional extraction from included abstracts.",
        "",
        "Interpretation notes:",
        "- `ai_better_like` means the abstract contains language such as `outperformed`, `superior`, or `better than`.",
        "- `human_better_like` means the abstract contains language such as `inferior` or `worse than` for the AI.",
        "- `tie_or_noninferior_like` means the abstract contains language such as `comparable`, `noninferior`, or `no significant difference`.",
        "- `mixed` means the abstract contains more than one directional pattern.",
        "- This is directional parsing from abstracts, not final arm adjudication.",
        "",
    ]
    if not summary_df.empty:
        md_lines.append("lane | directional_n | ai_better_like | human_better_like | tie_or_noninferior_like | mixed | ai_better_like_rate")
        md_lines.append("--- | --- | --- | --- | --- | --- | ---")
        for _, row in summary_df.iterrows():
            md_lines.append(
                f"{row['lane']} | {row['directional_n']} | {row['ai_better_like']} | {row['human_better_like']} | {row['tie_or_noninferior_like']} | {row['mixed']} | {row['ai_better_like_rate']}"
            )
    else:
        md_lines.append("No directional rows found.")
    md_path.write_text("\n".join(md_lines))

    print(f"candidates → {directional_path}")
    print(f"summary    → {summary_path}")
    print(f"markdown   → {md_path}")


if __name__ == "__main__":
    build()
