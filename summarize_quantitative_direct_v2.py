from __future__ import annotations

from pathlib import Path

import pandas as pd


LANES = [
    "diagnosis_reasoning_v3_core",
    "patient_facing_core",
    "admin_core",
    "supplemental_benchmark_implementation",
]

KEEP_METRICS = {"accuracy", "auc"}


def main() -> None:
    base = Path("data_v2_offline/extracted")
    rows = []
    review_rows = []

    for lane in LANES:
        path = base / lane / "quantitative_direct_candidates.csv"
        if not path.exists():
            continue

        df = pd.read_csv(path)
        if df.empty:
            continue

        clean = df[
            (~df["same_value_flag"].fillna(False))
            & (df["metric_guess"].fillna("").isin(KEEP_METRICS))
            & (df["accuracy_ai_candidate"] <= 1.0)
            & (df["accuracy_physician_candidate"] <= 1.0)
        ].copy()

        flagged = clean[clean["review_priority"].fillna("normal") == "high"].copy()
        if not flagged.empty:
            flagged = flagged.assign(lane=lane)
            review_rows.append(flagged)

        for metric, sub in clean.groupby("metric_guess"):
            rows.append(
                {
                    "lane": lane,
                    "metric": metric,
                    "n": len(sub),
                    "ai_median": round(sub["accuracy_ai_candidate"].median(), 3),
                    "human_median": round(sub["accuracy_physician_candidate"].median(), 3),
                    "ai_range": f"{sub['accuracy_ai_candidate'].min():.3f}-{sub['accuracy_ai_candidate'].max():.3f}",
                    "human_range": f"{sub['accuracy_physician_candidate'].min():.3f}-{sub['accuracy_physician_candidate'].max():.3f}",
                    "high_review_rows": int((sub["review_priority"].fillna("normal") == "high").sum()),
                }
            )

    summary = pd.DataFrame(rows).sort_values(["lane", "metric"])
    summary_path = base / "quantitative_direct_summary_clean.csv"
    summary.to_csv(summary_path, index=False)

    review_df = pd.concat(review_rows, ignore_index=True) if review_rows else pd.DataFrame()
    review_path = base / "quantitative_direct_high_review_flags.csv"
    review_df.to_csv(review_path, index=False)

    md_lines = [
        "# Quantitative Direct Summary",
        "",
        "Cleaned pooled summary from `quantitative_direct_candidates.csv`.",
        "",
        "Filters applied:",
        "- metrics restricted to `accuracy` and `auc`",
        "- rows with identical AI and human values removed",
        "- rows with extracted values > 1 removed",
        "",
        "Important caveat:",
        "- this is still abstract-level heuristic extraction and should be treated as a review summary, not a final pooled meta-analysis table",
        "",
    ]
    if not summary.empty:
        md_lines.append("lane | metric | n | ai_median | human_median | ai_range | human_range | high_review_rows")
        md_lines.append("--- | --- | --- | --- | --- | --- | --- | ---")
        for _, row in summary.iterrows():
            md_lines.append(
                f"{row['lane']} | {row['metric']} | {row['n']} | {row['ai_median']} | {row['human_median']} | {row['ai_range']} | {row['human_range']} | {row['high_review_rows']}"
            )
    else:
        md_lines.append("No clean rows available.")

    md_path = base / "QUANTITATIVE_DIRECT_SUMMARY.md"
    md_path.write_text("\n".join(md_lines))

    print(f"summary → {summary_path}")
    print(f"review  → {review_path}")
    print(f"markdown → {md_path}")


if __name__ == "__main__":
    main()
