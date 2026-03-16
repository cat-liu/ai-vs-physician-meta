"""
Rule-based abstract metric extractor for the parallel v2 offline workflow.

This does not attempt to perfectly reproduce the Anthropic arm-level extraction.
Instead it creates a reviewable table of metric-bearing studies and candidate
AI/physician accuracy values from abstracts.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from src.extraction_review_signals import (
    adjudication_review_priority,
    build_dedup_key,
    classify_comparison_structure,
    classify_direction_signal,
    normalize_title,
)

AI_MODEL_PATTERNS = [
    "gpt-4o",
    "gpt-4.1",
    "gpt-4",
    "gpt-3.5",
    "chatgpt",
    "claude",
    "gemini",
    "llama",
    "deepseek",
    "palm",
    "bard",
]

PERCENT_RE = re.compile(r"\b(\d{1,3}(?:\.\d+)?)%")
DECIMAL_RE = re.compile(r"\b(0\.\d{2,4}|1\.0+)\b")
METRIC_RE = re.compile(r"\b(accuracy|auc|auroc|sensitivity|specificity|f1|precision|recall)\b", re.I)


def _guess_ai_model(text: str) -> str:
    lower = text.lower()
    for pattern in AI_MODEL_PATTERNS:
        if pattern in lower:
            return pattern.upper().replace("CHATGPT", "ChatGPT")
    return ""


def _extract_metric_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = []
    for sentence in sentences:
        if METRIC_RE.search(sentence) or PERCENT_RE.search(sentence):
            kept.append(sentence.strip())
    return kept


def _extract_role_value(sentence: str, role_terms: list[str]) -> float | None:
    lower = sentence.lower()
    if not any(term in lower for term in role_terms):
        return None

    percent_match = PERCENT_RE.search(sentence)
    if percent_match:
        return round(float(percent_match.group(1)) / 100.0, 4)

    decimal_match = DECIMAL_RE.search(sentence)
    if decimal_match:
        return round(float(decimal_match.group(1)), 4)
    return None


def _extract_row(row: dict) -> dict:
    title = str(row.get("title", "") or "")
    abstract = str(row.get("abstract", "") or "")
    text = f"{title}. {abstract}"
    snippets = _extract_metric_sentences(text)
    snippet_text = " || ".join(snippets)
    lower = snippet_text.lower()

    metric_match = METRIC_RE.search(snippet_text)
    metric = metric_match.group(1).lower() if metric_match else ""

    ai_value = None
    physician_value = None
    paired_sentence = ""
    for sentence in snippets:
        sentence_lower = sentence.lower()
        sentence_ai = _extract_role_value(sentence, ["ai", "llm", "chatgpt", "gpt", "claude", "gemini", "llama", "deepseek"])
        sentence_physician = _extract_role_value(sentence, ["physician", "clinician", "doctor", "radiologist", "surgeon", "human"])
        if sentence_ai is not None and ai_value is None:
            ai_value = sentence_ai
        if sentence_physician is not None and physician_value is None:
            physician_value = sentence_physician
        if sentence_ai is not None and sentence_physician is not None and not paired_sentence:
            paired_sentence = sentence

    comparator_present = any(
        term in lower
        for term in ["physician", "clinician", "doctor", "radiologist", "surgeon", "human performance"]
    )
    confidence = 0.2
    if snippets:
        confidence += 0.2
    if metric:
        confidence += 0.2
    if comparator_present:
        confidence += 0.2
    if ai_value is not None or physician_value is not None:
        confidence += 0.1
    if ai_value is not None and physician_value is not None:
        confidence += 0.1
    signal_text = f"{title} {abstract}"
    direction_meta = classify_direction_signal(signal_text)
    has_quantitative_comparison = ai_value is not None and physician_value is not None and bool(metric)
    review_priority = adjudication_review_priority(
        has_quantitative_comparison=has_quantitative_comparison,
        direction_signal=str(direction_meta["direction_signal"]),
        needs_manual_review=not has_quantitative_comparison,
    )

    return {
        "source": row.get("source", ""),
        "source_id": row.get("source_id", ""),
        "doi": row.get("doi", ""),
        "title": title,
        "year": row.get("year", ""),
        "ai_model_guess": _guess_ai_model(text),
        "metric_guess": metric,
        "accuracy_ai_candidate": ai_value,
        "accuracy_physician_candidate": physician_value,
        "has_quantitative_comparison": has_quantitative_comparison,
        "comparator_present": comparator_present,
        "paired_sentence": paired_sentence,
        "metric_snippets": snippet_text,
        "needs_manual_review": not (ai_value is not None and physician_value is not None and metric),
        "extraction_confidence": round(confidence, 2),
        "comparison_structure_signal": classify_comparison_structure(signal_text),
        "normalized_title": normalize_title(title),
        "dedup_key": build_dedup_key(str(row.get("doi", "") or ""), title),
        "review_priority": review_priority,
        **direction_meta,
    }


def extract_accuracy_offline_v2(
    input_path: Path,
    out_path: Path,
    force_refresh: bool = False,
    limit: int | None = None,
) -> pd.DataFrame:
    if out_path.exists() and not force_refresh:
        print(f"[extract_accuracy_offline_v2] using cached {out_path}")
        return pd.read_csv(out_path)

    df = pd.read_csv(input_path)
    if limit:
        df = df.head(limit)

    extracted = pd.DataFrame([_extract_row(row) for row in df.to_dict("records")])
    metric_only = extracted[extracted["metric_snippets"].fillna("") != ""].copy()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    metric_only.to_csv(out_path, index=False)
    metric_only[metric_only["needs_manual_review"]].to_csv(
        out_path.parent / "accuracy_candidates_needing_review.csv", index=False
    )

    print(f"[extract_accuracy_offline_v2] metric-bearing studies: {len(metric_only):,}")
    return metric_only


if __name__ == "__main__":
    extract_accuracy_offline_v2(
        input_path=Path("data_v2_offline/extracted/included.csv"),
        out_path=Path("data_v2_offline/extracted/accuracy_candidates.csv"),
        force_refresh=True,
    )
