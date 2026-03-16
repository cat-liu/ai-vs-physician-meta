"""
Cross-lane deduplication of included studies.

After lane-level screening produces included.csv files per lane, the same paper
can appear in multiple lanes. This script merges all lane included files,
deduplicates by DOI then normalized title+year, and writes a single global
deduplicated included set.

The `lanes` column records every lane the paper appeared in (pipe-separated),
so per-lane breakdowns remain possible on the global file.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def _normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def global_dedup(
    lane_included_paths: list[tuple[str, Path]],
    out_path: Path,
    force_refresh: bool = False,
) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[global_dedup] using cached {out_path}")
        return pd.read_csv(out_path)

    frames = []
    for lane_name, p in lane_included_paths:
        if not p.exists():
            print(f"[global_dedup] skip missing {p}")
            continue
        df = pd.read_csv(p)
        df["lane"] = lane_name
        frames.append(df)
        print(f"[global_dedup] loaded {len(df):,} from {lane_name}")

    if not frames:
        raise FileNotFoundError("No lane included files found. Run screen first.")

    combined = pd.concat(frames, ignore_index=True)
    print(f"[global_dedup] total across lanes before dedup: {len(combined):,}")

    combined["_norm_title"] = combined["title"].fillna("").apply(_normalize_title)
    combined["_doi_key"] = combined["doi"].fillna("").str.lower().str.strip()

    # ── Step 1: DOI-based dedup ───────────────────────────────────────────────
    has_doi = combined[combined["_doi_key"] != ""].copy()
    no_doi = combined[combined["_doi_key"] == ""].copy()

    if not has_doi.empty:
        # Aggregate all lane names per DOI before dropping duplicates
        lane_agg = (
            has_doi.groupby("_doi_key")["lane"]
            .apply(lambda x: "|".join(sorted(set(x))))
            .reset_index()
            .rename(columns={"lane": "lanes"})
        )
        source_rank = {"pubmed": 0, "medrxiv": 1, "scopus": 2, "arxiv": 3}
        has_doi["_rank"] = has_doi["source"].map(source_rank).fillna(9)
        has_doi = (
            has_doi.sort_values("_rank")
            .drop_duplicates(subset="_doi_key", keep="first")
            .drop(columns=["_rank", "lane"])
            .merge(lane_agg, on="_doi_key", how="left")
        )
    else:
        has_doi["lanes"] = ""

    # ── Step 2: title+year dedup for no-DOI records ──────────────────────────
    seen_titles = set(has_doi["_norm_title"])
    no_doi = no_doi[~no_doi["_norm_title"].isin(seen_titles)].copy()

    if not no_doi.empty:
        lane_agg_no_doi = (
            no_doi.groupby(["_norm_title", "year"])["lane"]
            .apply(lambda x: "|".join(sorted(set(x))))
            .reset_index()
            .rename(columns={"lane": "lanes"})
        )
        no_doi = (
            no_doi.drop_duplicates(subset=["_norm_title", "year"], keep="first")
            .drop(columns="lane")
            .merge(lane_agg_no_doi, on=["_norm_title", "year"], how="left")
        )
    else:
        no_doi["lanes"] = ""

    deduped = pd.concat([has_doi, no_doi], ignore_index=True).drop(
        columns=["_norm_title", "_doi_key"], errors="ignore"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    deduped.to_csv(out_path, index=False)
    print(f"[global_dedup] {len(deduped):,} unique studies after cross-lane dedup → {out_path}")
    print(f"[global_dedup] papers appearing in more than one lane: {(deduped['lanes'].str.contains('|', regex=False)).sum():,}")
    return deduped
