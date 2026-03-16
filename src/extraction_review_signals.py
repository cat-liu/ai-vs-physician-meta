from __future__ import annotations

import re

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


def normalize_title(title: str) -> str:
    title = (title or "").lower()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def build_dedup_key(doi: str, title: str) -> str:
    doi = (doi or "").strip().lower()
    return doi if doi else f"title::{normalize_title(title)}"


def classify_direction_signal(text: str) -> dict[str, object]:
    t = (text or "").lower()
    ai_better = any(x in t for x in AI_BETTER_PATTERNS)
    human_better = any(x in t for x in HUMAN_BETTER_PATTERNS)
    tie = any(x in t for x in TIE_PATTERNS)
    assisted = any(x in t for x in ASSISTED_PATTERNS)

    flags = sum([ai_better, human_better, tie, assisted])
    if flags == 0:
      direction = "no_direction"
    elif flags > 1:
      direction = "mixed"
    elif assisted:
      direction = "assisted_improvement"
    elif ai_better:
      direction = "ai_better_like"
    elif human_better:
      direction = "human_better_like"
    else:
      direction = "tie_or_noninferior_like"

    return {
        "direction_signal": direction,
        "ai_better_signal": ai_better,
        "human_better_signal": human_better,
        "tie_signal": tie,
        "assisted_signal": assisted,
        "direction_signal_conflict": flags > 1,
    }


def classify_comparison_structure(text: str) -> str:
    t = (text or "").lower()
    if "physician-only" in t or "ai-only" in t or "unassisted" in t:
        return "three_arm_or_assisted"
    if "with ai assistance" in t or "human-ai collaboration" in t or "collaborative" in t:
        return "assisted_or_collaborative"
    return "ai_vs_human_unspecified"


def adjudication_review_priority(
    *,
    has_quantitative_comparison: bool,
    direction_signal: str,
    same_value_flag: bool = False,
    needs_manual_review: bool = False,
) -> str:
    if not has_quantitative_comparison:
        return "high"
    if same_value_flag or needs_manual_review:
        return "high"
    if direction_signal in {"human_better_like", "mixed", "assisted_improvement"}:
        return "high"
    return "normal"
