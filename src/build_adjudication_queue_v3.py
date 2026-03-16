from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.extraction_review_signals import (
    adjudication_review_priority,
    build_dedup_key,
    classify_comparison_structure,
    classify_direction_signal,
    normalize_title,
)


LANES = [
    "diagnosis_reasoning_v3_core",
    "supplemental_benchmark_implementation",
    "admin_core",
    "patient_facing_core",
]


def _annotate(df: pd.DataFrame, lane: str, lane_base: Path) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    included_path = lane_base / lane / "included.csv"
    if included_path.exists():
        included = pd.read_csv(included_path)
        included["join_key"] = included.apply(
            lambda row: build_dedup_key(str(row.get("doi", "") or ""), str(row.get("title", "") or "")),
            axis=1,
        )
        if "join_key" not in out.columns:
            out["join_key"] = out.apply(
                lambda row: build_dedup_key(str(row.get("doi", "") or ""), str(row.get("title", "") or "")),
                axis=1,
            )
        enrich = included[["join_key", "abstract"]].drop_duplicates("join_key")
        out = out.merge(enrich, on="join_key", how="left", suffixes=("", "_included"))

    out["lane"] = lane
    out["title"] = out["title"].fillna("").astype(str)
    if "abstract" not in out.columns:
        out["abstract"] = ""
    out["abstract"] = out["abstract"].fillna(out.get("metric_snippets", "")).fillna("").astype(str)
    text = (out["title"] + " " + out["abstract"]).astype(str)
    signals = text.apply(classify_direction_signal).apply(pd.Series)
    out = pd.concat([out, signals], axis=1)
    out["comparison_structure_signal"] = text.apply(classify_comparison_structure)
    out["normalized_title"] = out["title"].apply(normalize_title)
    out["dedup_key"] = out.apply(lambda row: build_dedup_key(str(row.get("doi", "") or ""), str(row.get("title", "") or "")), axis=1)
    if "has_quantitative_comparison" not in out.columns:
        out["has_quantitative_comparison"] = (
            out.get("accuracy_ai_candidate").notna()
            & out.get("accuracy_physician_candidate").notna()
            & out.get("metric_guess").fillna("").ne("")
        )
    if "review_priority" not in out.columns:
        out["review_priority"] = out.apply(
            lambda row: adjudication_review_priority(
                has_quantitative_comparison=bool(row.get("has_quantitative_comparison", False)),
                direction_signal=str(row.get("direction_signal", "no_direction")),
                same_value_flag=bool(row.get("same_value_flag", False)),
                needs_manual_review=bool(row.get("needs_manual_review", False)),
            ),
            axis=1,
        )
    out["adjudication_reason"] = out.apply(
        lambda row: "human_better_signal"
        if row["direction_signal"] == "human_better_like"
        else "mixed_direction_signal"
        if row["direction_signal"] == "mixed"
        else "assisted_signal"
        if row["direction_signal"] == "assisted_improvement"
        else "quantitative_direct"
        if bool(row.get("has_quantitative_comparison", False))
        else "abstract_needs_review",
        axis=1,
    )
    return out


def build_adjudication_queue(base: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    lane_frames: list[pd.DataFrame] = []
    for lane in LANES:
        path = base / lane / "accuracy_candidates.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if df.empty:
            continue
        lane_frames.append(_annotate(df, lane, base))

    combined = pd.concat(lane_frames, ignore_index=True) if lane_frames else pd.DataFrame()
    if combined.empty:
        out = base / "abstract_adjudication_queue_v3.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(out, index=False)
        combined.to_csv(base / "abstract_pdf_followup_queue_v3.csv", index=False)
        return combined, combined

    combined["review_priority_rank"] = combined["review_priority"].map({"high": 0, "normal": 1}).fillna(1)
    combined["lane_rank"] = combined["lane"].map({name: i for i, name in enumerate(LANES)}).fillna(99)
    combined = combined.sort_values(
        by=["review_priority_rank", "lane_rank", "extraction_confidence"],
        ascending=[True, True, False],
    )

    queue = combined.drop_duplicates(subset=["dedup_key"], keep="first").copy()
    queue["needs_pdf_followup"] = (
        (~queue["has_quantitative_comparison"].fillna(False))
        & queue["direction_signal"].isin(["ai_better_like", "human_better_like", "mixed"])
    )

    followup = queue[queue["needs_pdf_followup"]].copy()

    out_path = base / "abstract_adjudication_queue_v3.csv"
    followup_path = base / "abstract_pdf_followup_queue_v3.csv"
    queue.to_csv(out_path, index=False)
    followup.to_csv(followup_path, index=False)
    return queue, followup


if __name__ == "__main__":
    base = Path("data_v2_offline/extracted")
    queue, followup = build_adjudication_queue(base)
    print(f"adjudication queue → {base / 'abstract_adjudication_queue_v3.csv'} ({len(queue):,} rows)")
    print(f"pdf followup      → {base / 'abstract_pdf_followup_queue_v3.csv'} ({len(followup):,} rows)")
