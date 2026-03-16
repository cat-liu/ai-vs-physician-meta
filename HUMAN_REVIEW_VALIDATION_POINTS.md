# Human Review Validation Points

Use these checks when validating rows in `data_v2_offline/extracted/accuracy_v3_codex.csv` and `data_v2_offline/extracted/accuracy_v3_needs_review.csv`.

## Core validation questions

1. Is this a real AI-versus-human comparison, or is it actually:
   - a trust/perception study,
   - an agreement-only study,
   - a workflow/collaboration study, or
   - a model-versus-model benchmark without a clinician arm?
2. Are the AI and physician values reported for the same metric?
3. Is the retained metric really the primary outcome emphasized in the abstract?
4. Is the comparison type correct?
   - `ai_vs_physician_unaided`
   - `ai_plus_physician_vs_physician_unaided`
   - another structured type
5. If the abstract has multiple AI models or multiple clinician groups, is the retained row the right one to keep?
6. Are any values inferred from deltas or percentages rather than reported directly?
7. Should this row stay in the quantitative pooled set, move to `needs_review`, or move to a separate directional/collaboration analysis bucket?

## Priority guidance

- `high`
  - likely misfit for the pooled quantitative dataset
  - missing one side of the comparison
  - needs full-text pull to recover paired values
- `medium`
  - paired comparison exists but arm selection or metric choice is debatable
  - values require mild inference
- `low`
  - abstract-level extraction looks straightforward
  - reviewer is mainly confirming the retained metric and comparator
