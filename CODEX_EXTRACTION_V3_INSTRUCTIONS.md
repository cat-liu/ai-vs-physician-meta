# Instructions for Codex: Abstract-Level Metric Extraction v3

## Notes from the v3 run — read before starting

The previous adjudication pass (421 papers, now in `accuracy_v3_codex.csv`) had two systematic problems to avoid this time:

1. **`physician_type` was free text and inconsistent.** "radiologist", "senior radiologist", "board-certified radiologist", "experienced radiologist", and "attending radiologist" all ended up as separate values. This makes grouping impossible. This time, keep `physician_type` to a short role/specialty label only (e.g. "radiologist", "emergency physician") and put experience level in the new `physician_experience` field with a controlled vocabulary.

2. **`ai_model` was inconsistent.** "ChatGPT-4o", "GPT-4o", and "GPT4o" are the same model. Normalize to the canonical name as stated by the developer (e.g. "GPT-4o", "Claude 3.5 Sonnet", "Gemini 1.5 Pro"). If the abstract only says "a large language model" with no name, use `""`.

The input queue for this run is `data_v2_offline/extracted/abstract_adjudication_queue_v3.csv` (~1,433 deduplicated rows). Apply the same schema as v3 and append to the existing `accuracy_v3_codex.csv` — do not overwrite it. Deduplicate on `doi` or normalized title before writing.

---

## Task for Codex — read this first

You have filesystem access to this repo. Here is exactly what to do:

1. Read `data_v2_offline/extracted/diagnosis_reasoning_v3_core/quantitative_direct_candidates.csv` first — this is the highest-priority input. Then repeat for:
   - `data_v2_offline/extracted/supplemental_benchmark_implementation/quantitative_direct_candidates.csv`
   - `data_v2_offline/extracted/admin_core/quantitative_direct_candidates.csv`
   - `data_v2_offline/extracted/patient_facing_core/quantitative_direct_candidates.csv`
2. For each row, read the `title` and `abstract` columns and apply the extraction schema defined below. Use your own reading comprehension and judgment — do not write regex or pattern matching code to pull numbers.
3. Write results to `data_v2_offline/extracted/accuracy_v3_codex.csv`. If that file already exists, append and deduplicate by `doi` or normalized title — do not overwrite from scratch.
4. Also write a `data_v2_offline/extracted/accuracy_v3_needs_review.csv` containing only rows where `confidence` is `"low"` or `has_quantitative_comparison` is `false`.
5. Do not modify any existing files. The heuristic extraction outputs (`accuracy_candidates.csv`, `quantitative_direct_candidates.csv`) stay as-is for comparison.

After finishing the quantitative-direct candidates, extend to `data_v2_offline/extracted/included_global_deduped.csv` (the full deduplicated included set).

### Phase 2: full-text extraction for inconclusive abstracts

After the abstract-level pass is complete, do a targeted full-text extraction pass on a specific subset. Do not attempt full-text extraction across the whole corpus — the access barrier makes that impractical.

The subset to target is rows in `accuracy_v3_needs_review.csv` where:
- `has_quantitative_comparison` is `false`, AND
- the title or abstract language suggests the paper *should* have paired numeric values (e.g. the abstract says "outperformed" or "achieved higher accuracy" but doesn't report the numbers)

For those papers, attempt to retrieve the full text as follows — in order:

1. **medRxiv papers** (where `source == "medrxiv"`): all medRxiv papers are open access. Use the DOI or medRxiv ID to fetch the full text directly.
2. **Unpaywall**: for PubMed papers, query `https://api.unpaywall.org/v2/{doi}?email=YOUR_EMAIL` to check for a legal open-access PDF. If a PDF URL is returned, fetch and read it.
3. **PubMed Central**: check `https://www.ncbi.nlm.nih.gov/pmc/` for a free full-text version.
4. **Skip** any paper where none of the above yields a full text. Do not attempt to access paywalled content.

When reading full text, apply the same extraction schema as above. Add a field `extraction_source` to each row: `"abstract"` for abstract-level extractions and `"full_text"` for full-text extractions, so the two can be distinguished in analysis.

Write full-text extraction results into the same `accuracy_v3_codex.csv` file, updating existing rows for the same paper (matched by DOI or normalized title) rather than creating duplicates.

---

## Context

The current `extract_accuracy_offline_v2.py` uses regex to pull numbers from abstracts. It finds the first percentage or decimal in a sentence near a role keyword ("AI", "physician") and calls that the performance value. This is wrong most of the time. The numbers it produces look precise but are not trustworthy — they cannot be pooled or cited in a report.

This document tells you what to do instead.

---

## What is wrong with the regex approach

The extractor grabs the **first** number that appears near a keyword. It cannot:

- Tell the difference between "GPT-4 achieved 80% accuracy" and "among 80 patients, GPT-4 was evaluated"
- Determine which metric is the **primary reported outcome** when abstracts report multiple (accuracy, AUC, sensitivity)
- Distinguish "physicians with AI assistance achieved 91%" (AI+physician team performance) from "AI alone achieved 91%"
- Handle sentences where the AI and physician values appear in different sentences with non-obvious structure

The result is that `accuracy_ai_candidate` and `accuracy_physician_candidate` columns have unreliable attribution. Do not pool them.

---

## What to do instead

Write a script that loads the `included_global_deduped.csv` file (or the per-lane `included.csv` files) and has Codex — you — read each abstract directly and fill in a structured output row. You do not need to call any external API. You already have the abstracts as text. Read them and make judgment calls.

The script should iterate over rows, pass the title and abstract to you as a prompt, and collect your structured response.

---

## Schema to extract per abstract

For each abstract, return a JSON object with this structure:

```json
{
  "has_quantitative_comparison": true,
  "primary_metric": "accuracy",
  "ai_value": 0.847,
  "physician_value": 0.791,
  "comparison_type": "ai_vs_physician_unaided",
  "ai_model": "GPT-4",
  "physician_type": "radiologist",
  "physician_experience": "specialist",
  "sample_size": 240,
  "significance_reported": true,
  "ai_better": true,
  "confidence": "high",
  "extraction_note": ""
}
```

### Field definitions

- **`has_quantitative_comparison`** — `true` only if both an AI value and a physician/human value are reported for the same metric. If only one side is reported, set `false`.
- **`primary_metric`** — the main performance metric. Use: `accuracy`, `auc`, `sensitivity`, `specificity`, `f1`, `precision`, `recall`, or `other`. When multiple metrics are reported, use the one the authors emphasize (typically in the conclusion sentence of the abstract).
- **`ai_value`** — AI system's value on the primary metric, as a proportion between 0 and 1. Convert percentages: 84.7% → 0.847. `null` if not reported.
- **`physician_value`** — physician/human comparator's value on the same metric, same unit. `null` if not reported.
- **`comparison_type`** — one of:
  - `ai_vs_physician_unaided` — AI alone vs physician alone without assistance
  - `ai_vs_physician_with_resources` — AI alone vs physician with reference access
  - `ai_plus_physician_vs_physician_unaided` — AI-assisted physician vs unaided physician
  - `ai_plus_physician_vs_physician_with_resources` — AI-assisted physician vs physician with resources
  - `ai_vs_ai_plus_physician` — AI alone vs AI+physician combination
  - `unclear` — cannot determine from the abstract
- **`ai_model`** — name of the AI system if mentioned (e.g. "GPT-4o", "custom CNN"). Empty string if not named. **Normalize to the canonical model name where possible** — e.g. "GPT-4o" not "ChatGPT-4o", "Claude 3.5 Sonnet" not "Claude". Do not invent model names not stated in the abstract.
- **`physician_type`** — specialty or role of the clinician comparator. Use a short controlled description: e.g. "radiologist", "emergency physician", "pathologist", "general practitioner". Do not include experience level here — that goes in `physician_experience`. Empty string if not specified.
- **`physician_experience`** — experience level of the physician comparator. Use **only** one of these values:
  - `"medical_student"` — student not yet holding an MD/DO
  - `"resident"` — postgraduate trainee (intern, PGY1–PGY5, or equivalent)
  - `"fellow"` — subspecialty fellow post-residency
  - `"attending"` — fully trained independent practicing physician
  - `"specialist"` — attending with explicit subspecialty expertise (e.g. subspecialist radiologist, disease-specific expert panel)
  - `"mixed"` — the comparator group includes multiple experience levels
  - `"unclear"` — cannot be determined from the abstract
  Use `"specialist"` when the abstract describes the comparator as experts in that specific task (e.g. "breast imaging specialists", "expert panel", "fellowship-trained"). Use `"attending"` when described as fully trained but without subspecialty emphasis. **This field matters — do not default to "unclear" unless the abstract genuinely gives no signal.**
- **`sample_size`** — total number of cases or patients evaluated, if reported. `null` if not stated.
- **`significance_reported`** — `true` if the abstract mentions a p-value, confidence interval, or states the difference is/is not statistically significant.
- **`ai_better`** — `true` if AI value > physician value, `false` if physician value > AI value, `null` if tied or cannot be determined.
- **`confidence`** — your confidence that the extracted values are correctly paired and attributed:
  - `"high"` — both values clearly attributed in the same or immediately adjacent sentences
  - `"medium"` — values are present but attribution requires inference
  - `"low"` — values are present but the pairing is uncertain; needs human review
- **`extraction_note`** — any free-text note about ambiguity, multi-arm structure, or anything a human reviewer should check.

---

## Rules

1. **Never invent values.** If the abstract does not report a numeric value for one side, set it to `null` and set `has_quantitative_comparison` to `false`.

2. **Pick the primary outcome, not the first number.** Authors usually state the main finding in the final sentence of the abstract. Use that value, not whichever number appears first.

3. **Distinguish AI-alone from AI-assisted.** This is the most important distinction. "Physicians using AI achieved 91%" is the AI+physician team's performance, not the AI's standalone performance. Set `comparison_type` accordingly.

4. **If the paper has multiple comparison arms** (e.g. junior vs senior physicians, or multiple AI models), extract only the primary or most prominently featured comparison and note the multi-arm structure in `extraction_note`.

5. **When in doubt, use low confidence.** A `"low"` row that goes to manual review is better than a `"high"` row with wrong numbers.

---

## Suggested implementation

Write a Python script `src/extract_accuracy_v3_codex.py` that:

1. Loads `data_v2_offline/extracted/included_global_deduped.csv` (or accepts a path argument)
2. For each row, constructs a prompt containing the title and abstract
3. Submits the prompt to Codex (yourself) via the OpenAI API using your code interpreter / function calling pattern — or simply writes a batch of prompts to a JSONL file for you to process as a batch
4. Collects the JSON responses and writes them to `data_v2_offline/extracted/accuracy_v3_codex.csv`
5. Flags rows where `confidence == "low"` or `has_quantitative_comparison == false` to a separate `accuracy_v3_needs_review.csv`

Prioritize the `quantitative_direct_candidates.csv` files first — these are the rows where paired values are most likely to actually exist in the abstract.

---

## What makes this output useful for the report

After extraction:

- Filter to `has_quantitative_comparison == true` for any pooled accuracy analysis
- Use `confidence == "high"` rows as the primary analytic set
- Use `confidence == "medium"` rows as a sensitivity check
- Never mix `ai_vs_physician_unaided` and `ai_plus_physician_vs_physician_unaided` in the same pooled estimate — they are different hypotheses
- The `ai_better` field feeds directly into a win-rate calculation that is grounded in actual read abstracts, not pattern matching

This is the difference between a number you can defend and a number that falls apart when someone asks how you got it.
