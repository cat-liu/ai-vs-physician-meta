"""
Build stricter quantitative-direct subsets from the heuristic accuracy candidates.

Goal:
- keep records with explicit comparator signal
- require paired numeric AI and human values
- preserve a review flag because heuristic extraction can still mis-pair values
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.extraction_review_signals import adjudication_review_priority


def build_quantitative_direct_subset(input_path: Path, out_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    if df.empty:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        return df

    metric_present = df["metric_guess"].fillna("") != ""
    paired_numeric = df["accuracy_ai_candidate"].notna() & df["accuracy_physician_candidate"].notna()
    comparator_present = df["comparator_present"].fillna(False).astype(bool)

    direct = df[metric_present & paired_numeric & comparator_present].copy()
    direct["same_value_flag"] = (
        direct["accuracy_ai_candidate"].round(6) == direct["accuracy_physician_candidate"].round(6)
    )
    direct["review_priority"] = direct.apply(
        lambda row: adjudication_review_priority(
            has_quantitative_comparison=bool(row.get("has_quantitative_comparison", False)),
            direction_signal=str(row.get("direction_signal", "no_direction")),
            same_value_flag=bool(row.get("same_value_flag", False)),
            needs_manual_review=bool(row.get("needs_manual_review", False)),
        ),
        axis=1,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    direct.to_csv(out_path, index=False)
    return direct


if __name__ == "__main__":
    base = Path("data_v2_offline/extracted")
    for lane_dir in base.iterdir():
        if not lane_dir.is_dir():
            continue
        input_path = lane_dir / "accuracy_candidates.csv"
        if not input_path.exists():
            continue
        out_path = lane_dir / "quantitative_direct_candidates.csv"
        df = build_quantitative_direct_subset(input_path, out_path)
        print(f"{lane_dir.name}: {len(df):,} quantitative-direct candidates → {out_path}")
