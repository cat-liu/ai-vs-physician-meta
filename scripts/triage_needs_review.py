"""
Triage the needs_review CSV into three buckets:

  A — Quick exclude  : can decide from title/abstract alone, almost certainly out-of-scope
  B — Abstract re-read : needs careful abstract reading but probably no PDF
  C — PDF required   : missing numbers or qualitative claims that need full text

Output: data_v2_offline/extracted/needs_review_triaged.csv
"""
from __future__ import annotations

import csv
from pathlib import Path

BASE   = Path("/Users/anastasiaperezternent/Documents/ai-vs-physician-meta")
INPUT  = BASE / "data_v2_offline" / "extracted" / "accuracy_v3_needs_review.csv"
OUTPUT = BASE / "data_v2_offline" / "extracted" / "needs_review_triaged.csv"


# ── Keyword rules ─────────────────────────────────────────────────────────────
# Each bucket is checked in order; first match wins.

BUCKET_A_KEYWORDS = [
    # clinician as labeler / reference standard
    "labeling reference",
    "reference standard",
    "ground truth",
    "clinician labeler",
    "clinicians are the labeling",
    "annotated",
    "annotation",
    # surveys, attitudes, trust, perception
    "survey",
    "attitude",
    "trust",
    "perception",
    "confidence of doctor",
    "usability",
    "patient attitude",
    "patient preference",
    # scoping reviews, meta-analyses, frameworks
    "scoping review",
    "systematic review",
    "meta-analysis",
    "benchmark-generation framework",
    "benchmark generation",
    # wrong comparator type
    "guideline",
    "return on investment",
    "roi",
    "patient satisfaction",
    "discharge letter",
    "handoff note",
    "traditional chinese medicine",
    "prostate cancer trust",
    # concordance / agreement only (not head-to-head performance)
    "concordance",
    "agreement with clinician",
    "clinician mapping",
    "inter-rater",
    "interrater",
]

BUCKET_C_KEYWORDS = [
    # explicitly needs full text
    "full text",
    "full paper",
    "pdf",
    "buried",
    "supplementary",
    "supplemental",
    "table",
    "figure",
    # qualitative only, no numbers
    "qualitative",
    "no numerical",
    "no metric",
    "no extractable",
    "non-extractable",
    "cannot be extracted",
    "not reported in abstract",
    "not stated in abstract",
    "truncated",
    "abstract is truncated",
    "improvement delta",
    "delta without absolute",
    "without absolute value",
    "percentage improvement",
    # missing physician metric specifically
    "physician metric missing",
    "physician value missing",
    "physician performance not reported",
    "human metric not provided",
    "human performance not reported",
    "human comparator metric",
    "physician score metric is absent",
    "radiologist metric missing",
]


def classify(row: dict) -> str:
    combined = " ".join([
        (row.get("human_review_points") or ""),
        (row.get("extraction_note") or ""),
        (row.get("title") or ""),
    ]).lower()

    for kw in BUCKET_A_KEYWORDS:
        if kw in combined:
            return "A_quick_exclude"

    for kw in BUCKET_C_KEYWORDS:
        if kw in combined:
            return "C_pdf_required"

    return "B_abstract_reread"


BUCKET_LABELS = {
    "A_quick_exclude":   "A — Quick exclude (abstract/title sufficient)",
    "B_abstract_reread": "B — Abstract re-read (no PDF needed)",
    "C_pdf_required":    "C — PDF required",
}

BUCKET_ORDER = ["A_quick_exclude", "B_abstract_reread", "C_pdf_required"]


def main() -> None:
    with INPUT.open() as fh:
        rows = list(csv.DictReader(fh))

    for row in rows:
        row["review_bucket"] = classify(row)
        row["review_bucket_label"] = BUCKET_LABELS[row["review_bucket"]]

    rows.sort(key=lambda r: BUCKET_ORDER.index(r["review_bucket"]))

    fieldnames = ["review_bucket", "review_bucket_label"] + [
        k for k in rows[0].keys()
        if k not in ("review_bucket", "review_bucket_label")
    ]

    with OUTPUT.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    from collections import Counter
    counts = Counter(r["review_bucket"] for r in rows)
    print(f"Wrote {len(rows)} rows → {OUTPUT}\n")
    for bucket in BUCKET_ORDER:
        print(f"  {BUCKET_LABELS[bucket]}: {counts[bucket]}")


if __name__ == "__main__":
    main()
