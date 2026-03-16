from __future__ import annotations

from pathlib import Path

import pandas as pd


LANES = [
    "diagnosis_reasoning_v3_core",
    "patient_facing_core",
    "admin_core",
    "supplemental_benchmark_implementation",
]

AI_BETTER_PATTERNS = [
    "outperformed",
    "outperforming",
    "superior to",
    "better than",
    "exceeded the performance of",
    "exceeded clinician",
]

HUMAN_BETTER_PATTERNS = [
    "inferior to",
    "worse than",
    "underperformed compared with",
    "lower than clinicians",
    "lower than radiologists",
    # softer negative language that papers use instead of explicit "worse than"
    "did not outperform",
    "failed to outperform",
    "no significant improvement over",
    "not significantly better than",
    "did not significantly exceed",
    "did not surpass",
    "did not reach the performance",
    "did not match",
    "fell short",
    "underperformed",
    "lagged behind",
    "below physician",
    "below clinician",
    "physicians outperformed",
    "clinicians outperformed",
    "doctors outperformed",
    "radiologists outperformed",
    "nurses outperformed",
    "humans outperformed",
    "human experts outperformed",
]

TIE_PATTERNS = [
    "comparable",
    "noninferior",
    "no significant difference",
    "similar performance",
    "equivalent",
    "on par with",
]

ASSISTED_PATTERNS = [
    "with ai assistance",
    "ai assistance",
    "human-ai collaboration",
    "collaborative workflow",
    "collaborative",
    "combined (clinical+ml)",
    "combined clinical+ml",
    "augment human performance",
    "augmented human performance",
    "improved rating accuracy",
    "improved physician performance",
    "improved clinician performance",
    "incremental value",
]


def classify_direction(text: str) -> str:
    t = (text or "").lower()
    ai_better = any(x in t for x in AI_BETTER_PATTERNS)
    human_better = any(x in t for x in HUMAN_BETTER_PATTERNS)
    tie = any(x in t for x in TIE_PATTERNS)
    assisted = any(x in t for x in ASSISTED_PATTERNS)

    flags = sum([ai_better, human_better, tie, assisted])
    if flags == 0:
        return "no_direction"
    if flags > 1:
        return "mixed"
    if assisted:
        return "assisted_improvement"
    if ai_better:
        return "ai_better_like"
    if human_better:
        return "human_better_like"
    return "tie_or_noninferior_like"


def classify_comparison_structure(text: str) -> str:
    t = (text or "").lower()
    if "physician-only" in t or "ai-only" in t or "unassisted" in t:
        return "three_arm_or_assisted"
    if "with ai assistance" in t or "human-ai collaboration" in t or "collaborative" in t:
        return "assisted_or_collaborative"
    return "ai_vs_human_unspecified"


def _summarize(df: pd.DataFrame, label: str) -> dict:
    counts = df["direction_class"].value_counts()
    n = len(df)
    return {
        "lane": label,
        "directional_n": n,
        "ai_better_like": int(counts.get("ai_better_like", 0)),
        "human_better_like": int(counts.get("human_better_like", 0)),
        "tie_or_noninferior_like": int(counts.get("tie_or_noninferior_like", 0)),
        "assisted_improvement": int(counts.get("assisted_improvement", 0)),
        "mixed": int(counts.get("mixed", 0)),
        "ai_better_like_rate": round(counts.get("ai_better_like", 0) / n, 3) if n else None,
    }


def _classify_df(df: pd.DataFrame, lane: str) -> pd.DataFrame:
    df = df.copy()
    text = (df["title"].fillna("") + " " + df["abstract"].fillna("")).astype(str)
    df["lane"] = lane
    df["direction_class"] = text.apply(classify_direction)
    df["comparison_structure"] = text.apply(classify_comparison_structure)
    return df[df["direction_class"] != "no_direction"].copy()


def build() -> None:
    base = Path("data_v2_offline/extracted")
    all_rows = []
    summary_rows = []

    # ── Per-lane summaries (counts may overlap across lanes) ──────────────────
    for lane in LANES:
        p = base / lane / "included.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p)
        if df.empty:
            continue
        directional = _classify_df(df, lane)
        all_rows.append(directional)
        summary_rows.append(_summarize(directional, lane))

    directional_df = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    summary_df = pd.DataFrame(summary_rows).sort_values("lane")

    directional_path = base / "win_rate_candidates_conservative.csv"
    summary_path = base / "win_rate_summary_conservative.csv"
    md_path = base / "WIN_RATE_SUMMARY_CONSERVATIVE.md"

    directional_df.to_csv(directional_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    # ── Global deduped summary (use this for report-level totals) ─────────────
    global_path = base / "included_global_deduped.csv"
    global_summary_rows = []
    if global_path.exists():
        gdf = pd.read_csv(global_path)
        if not gdf.empty:
            # Classify on the deduplicated set
            gdf_classified = _classify_df(gdf, "global_deduped")
            gdf_classified.to_csv(base / "win_rate_candidates_global_deduped.csv", index=False)
            global_summary_rows.append(_summarize(gdf_classified, "GLOBAL_DEDUPED"))
            # Per-lane breakdown from the lanes column in the global file
            if "lanes" in gdf_classified.columns:
                for lane in LANES:
                    lane_subset = gdf_classified[gdf_classified["lanes"].str.contains(lane, na=False)]
                    if not lane_subset.empty:
                        global_summary_rows.append(_summarize(lane_subset, f"global_{lane}"))

    global_summary_df = pd.DataFrame(global_summary_rows)
    if not global_summary_df.empty:
        global_summary_df.to_csv(base / "win_rate_summary_global_deduped.csv", index=False)

    # ── Markdown report ───────────────────────────────────────────────────────
    md_lines = [
        "# Conservative Win-Rate Summary",
        "",
        "Directional parsing from included abstracts using stricter patterns.",
        "",
        "Interpretation notes:",
        "- `ai_better_like` requires explicit phrasing such as `outperformed`, `superior to`, or `better than`.",
        "- `human_better_like` captures both explicit and soft negative language (e.g. `did not outperform`, `physicians outperformed`).",
        "- `assisted_improvement` captures AI+human or AI-assisted gains and is kept separate from AI-alone wins.",
        "- `mixed` means the abstract contains multiple directional signals.",
        "- Per-lane counts may overlap (the same paper can appear in multiple lanes).",
        "- Use GLOBAL_DEDUPED row for report-level totals.",
        "- This is still abstract-level parsing, not final arm adjudication.",
        "",
    ]

    all_summary = pd.concat(
        [df for df in [summary_df, global_summary_df] if not df.empty],
        ignore_index=True,
    ) if not global_summary_df.empty else summary_df

    if not all_summary.empty:
        md_lines.append("lane | directional_n | ai_better_like | human_better_like | tie_or_noninferior_like | assisted_improvement | mixed | ai_better_like_rate")
        md_lines.append("--- | --- | --- | --- | --- | --- | --- | ---")
        for _, row in all_summary.iterrows():
            md_lines.append(
                f"{row['lane']} | {row['directional_n']} | {row['ai_better_like']} | {row['human_better_like']} | {row['tie_or_noninferior_like']} | {row['assisted_improvement']} | {row['mixed']} | {row['ai_better_like_rate']}"
            )
    else:
        md_lines.append("No directional rows found.")
    md_path.write_text("\n".join(md_lines))

    print(f"candidates → {directional_path}")
    print(f"summary    → {summary_path}")
    print(f"markdown   → {md_path}")
    if not global_summary_df.empty:
        print(f"global summary → {base / 'win_rate_summary_global_deduped.csv'}")


if __name__ == "__main__":
    build()
