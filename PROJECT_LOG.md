# Project Log

## 2026-03-12

### Scope and workflow decisions

- Preserved the original Anthropic/Claude workflow and created a parallel offline workflow that writes only to `data_v2_offline/`.
- Extended the parallel workflow end date through `2026-03-31`.
- Broadened scope from LLM-only diagnosis/triage to all healthcare AI with human comparison allowed.
- Final scope decision:
  - include clinical and administrative/workflow healthcare AI studies
  - require a human comparison arm or explicit human benchmark
  - allow both quantitative and qualitative comparisons
- Structured the offline retrieval into four lanes:
  - `diagnosis_reasoning_v3_core`
  - `patient_facing_core`
  - `admin_core`
  - `supplemental_benchmark_implementation`
- Kept `supplemental_benchmark_implementation` as a recall safeguard for benchmark, implementation, collaborative-workflow, and branded-system studies that do not advertise head-to-head comparisons clearly in the title/abstract.

### Search count checks that led to the current design

- A very broad all-healthcare-AI query produced unworkably large counts.
- Adding stronger study-design language, healthcare comparator language, and splitting the search into clinical and admin/workflow brought the counts down to a manageable range.
- After aligning the query terms more closely to the taxonomy, the current count-only checks were:
  - `diagnosis_reasoning_v3_core`
    - PubMed: `1,989`
    - medRxiv: `1,683`
  - `patient_facing_core`
    - PubMed: `123`
    - medRxiv: `99`
  - `admin_core`
    - PubMed: `189`
    - medRxiv: `805`
  - `supplemental_benchmark_implementation`
    - PubMed: `2,469`
    - medRxiv: `1,680`

### Current saved PubMed + medRxiv corpus

- Raw and deduplicated lane-level outputs are in `data_v2_offline/raw/`.
- Current lane-level counts after screening and heuristic extraction:
  - `diagnosis_reasoning_v3_core`
    - deduped: `3,667`
    - included: `1,200`
    - uncertain: `239`
    - metric-bearing: `1,122`
  - `patient_facing_core`
    - deduped: `222`
    - included: `40`
    - uncertain: `1`
    - metric-bearing: `29`
  - `admin_core`
    - deduped: `991`
    - included: `185`
    - uncertain: `68`
    - metric-bearing: `158`
  - `supplemental_benchmark_implementation`
    - deduped: `4,141`
    - included: `1,076`
    - uncertain: `677`
    - metric-bearing: `946`

### Known-target sanity checking

- Benchmarked the retrieval against a recent ARISE-style target set from `Study Index_ Stanford ARISE - Doctor v. AI.csv`.
- Current PubMed + medRxiv saved corpus clearly contains only `3/8` of the recent target studies by title match:
  - `GPT-4 assistance for improvement of physician performance on patient care tasks: a randomized controlled trial`
  - `From Tool to Teammate: A Randomized Controlled Trial of Clinician-AI Collaborative Workflows for Diagnosis`
  - `A large language model for complex cardiology care`
- Main conclusion:
  - the core lanes have acceptable precision
  - but the overall retrieval still misses benchmark/implementation papers that use collaboration/branding/implementation framing rather than explicit comparator wording
- This is why the supplemental lane remains necessary.
- Notes on miss patterns were written to `KNOWN_TARGETS_NOTES.md`.

### Quantitative direct subset

- Built a stricter quantitative-direct subset from the heuristic metric outputs.
- Files:
  - `data_v2_offline/extracted/*/quantitative_direct_candidates.csv`
  - `data_v2_offline/extracted/quantitative_direct_summary_clean.csv`
  - `data_v2_offline/extracted/QUANTITATIVE_DIRECT_SUMMARY.md`
- Quantitative-direct candidate counts:
  - `diagnosis_reasoning_v3_core`: `211`
  - `patient_facing_core`: `7`
  - `admin_core`: `27`
  - `supplemental_benchmark_implementation`: `176`
- Clean pooled summary currently keeps only:
  - `accuracy`
  - `auc`
  - non-identical AI vs human values
  - values `<= 1`
- Current cleaned pooled medians:
  - `diagnosis_reasoning_v3_core`
    - `accuracy`: `n=46`, AI `0.836`, human `0.790`
    - `auc`: `n=21`, AI `0.850`, human `0.827`
  - `admin_core`
    - `accuracy`: `n=10`, AI `0.821`, human `0.621`
  - `patient_facing_core`
    - very sparse: `n=1` for `accuracy`, `n=1` for `auc`
  - `supplemental_benchmark_implementation`
    - `accuracy`: `n=45`, AI `0.799`, human `0.775`
    - `auc`: `n=12`, AI `0.850`, human `0.818`
- Important caveat:
  - these are abstract-level heuristic extractions, not manuscript-grade pooled meta-analysis outputs
  - many rows still need manual review

### Win-rate analysis

- Built two first-pass win-rate outputs from included abstracts:
  - `data_v2_offline/extracted/win_rate_summary.csv`
  - `data_v2_offline/extracted/WIN_RATE_SUMMARY.md`
- The raw pass was too optimistic because it treated generic words like `improved` as AI wins.
- Added a more conservative parser that separates AI-assisted improvement from AI-alone wins:
  - `data_v2_offline/extracted/win_rate_summary_conservative.csv`
  - `data_v2_offline/extracted/WIN_RATE_SUMMARY_CONSERVATIVE.md`
  - `data_v2_offline/extracted/win_rate_candidates_conservative.csv`
- Conservative win-rate summary:
  - `diagnosis_reasoning_v3_core`
    - directional abstracts: `476`
    - `ai_better_like`: `208`
    - `human_better_like`: `10`
    - `tie_or_noninferior_like`: `140`
    - `assisted_improvement`: `36`
    - `mixed`: `82`
    - `ai_better_like_rate`: `0.437`
  - `supplemental_benchmark_implementation`
    - directional abstracts: `392`
    - `ai_better_like`: `155`
    - `human_better_like`: `5`
    - `tie_or_noninferior_like`: `97`
    - `assisted_improvement`: `60`
    - `mixed`: `75`
    - `ai_better_like_rate`: `0.395`
  - `admin_core`
    - directional abstracts: `67`
    - `ai_better_like_rate`: `0.299`
  - `patient_facing_core`
    - directional abstracts: `16`
    - `ai_better_like_rate`: `0.562`
    - too small to interpret strongly

### Relationship to the original Claude arm-level results

- The original extracted-arm dataset remains the cleanest directional baseline:
  - non-null `ai_better`: `114`
  - `AI better`: `54`
  - overall win rate: `0.474`
- By arm type in the original Claude extraction:
  - `AI_vs_physician_unaided`: `32.9%`
  - `AI_vs_physician_resources`: `66.7%`
  - `AI_plus_physician_vs_physician_unaided`: `100%`
  - `AI_plus_physician_vs_physician_resources`: `100%`
  - `AI_vs_AI_plus_physician`: `33.3%`
- Current interpretation:
  - the raw offline win-rate output overcalled AI wins
  - the conservative offline win-rate output is much more directionally plausible
  - AI-assisted or AI+human gains should remain analytically distinct from AI-alone wins

### Comparison to the Nature Medicine LLM review

- Used the Nature Medicine paper `LLM-assisted systematic review of large language models in clinical medicine` as a sense check.
- Relevant headline from that paper:
  - `1,046` studies with detectable human-comparison outcomes in abstracts
  - LLMs outperformed humans in `345` (`33.0%`)
  - underperformed in `675` (`64.5%`)
  - mixed in `26` (`2.49%`)
- Our conservative offline win-rate outputs are somewhat higher in the main lanes:
  - diagnosis/reasoning: `43.7%`
  - supplemental: `39.5%`
  - admin: `29.9%`
- Interpretation:
  - our results are in the same general range, not wildly inconsistent
  - but they are still less trustworthy than the Nature Medicine estimate because our current pipeline is abstract-only, heuristic, and not yet fully adjudicated

### Manual review backlog estimates

- To improve inclusion certainty:
  - all `uncertain` studies = `985`
- To improve directional win-rate coverage:
  - included studies without directional classification = `1,114`
- To improve pooled quantitative direct-comparison coverage:
  - metric-bearing studies without clean quantitative-direct pairing = `1,834`
- Most useful next manual-review target if the goal is better win-rate coverage:
  - the `1,114` included-but-non-directional studies

### Current recommendation

- Keep the current four-lane PubMed + medRxiv workflow.
- Treat the conservative win-rate outputs as the working directional summary, not the raw version.
- Keep AI-assisted / AI+human studies analytically separate from AI-alone wins.
- Before adding Scopus, tighten the manual review flow around:
  - included-but-non-directional abstracts
  - high-priority quantitative-direct candidates
- Add Scopus after the screening and review logic feels stable.

---

## 2026-03-12 (continued) — Pipeline fixes and v3 extraction plan

### Cross-lane deduplication

- Added `src/global_dedup.py` to merge all four lane `included.csv` files and deduplicate across lanes by DOI then normalized title+year.
- Output: `data_v2_offline/extracted/included_global_deduped.csv`
- A `lanes` column (pipe-separated) records which lanes each paper appeared in.
- Added `global_dedup` command to `run_offline_v2.py`; also runs automatically as part of `all`.
- **Implication**: per-lane included counts in the project log above are not mutually exclusive. Use the global deduped file for any headline N in the report.

### Human-better pattern expansion

- Expanded `HUMAN_BETTER_PATTERNS` in `build_win_rate_outputs_v2_conservative.py` from 5 explicit phrases to 22.
- Added soft negative language that papers commonly use: `"did not outperform"`, `"failed to outperform"`, `"physicians outperformed"`, `"did not reach the performance"`, `"lagged behind"`, `"did not match"`, `"did not surpass"`, and others.
- **Why this matters**: the original pattern list systematically undercounted human-better outcomes because papers reporting AI underperformance rarely use explicit language like "worse than". The previous win-rate estimates are likely somewhat inflated as a result.
- The win-rate script now also produces `win_rate_summary_global_deduped.csv` from the deduplicated set. Use that for report-level win-rate figures, not the per-lane summaries.

### v3 abstract extraction plan

- The current heuristic extractor (`extract_accuracy_offline_v2.py`) grabs the first number near a role keyword. This is unreliable and the extracted `accuracy_ai_candidate` / `accuracy_physician_candidate` values should not be pooled.
- Added `CODEX_EXTRACTION_V3_INSTRUCTIONS.md` with instructions for Codex to read abstracts directly and make judgment calls rather than using regex.
- The v3 schema captures: primary metric, AI value, physician value, comparison type, AI model, physician type, sample size, significance, and a confidence rating.
- The most important distinction to preserve: `ai_vs_physician_unaided` vs `ai_plus_physician_vs_physician_unaided` — these are different hypotheses and must never be pooled together.
- Prioritize running v3 extraction on `quantitative_direct_candidates.csv` files first, then the full global deduped included set.
- Added shared directional review signals so `human_better` language is captured upstream as an adjudication priority, not as a final extracted outcome.
- Added a deduplicated `abstract_adjudication_queue_v3.csv` and a narrower `abstract_pdf_followup_queue_v3.csv` for the second-phase full-text pass.

### v3 manual-batched adjudication started

- Added `src/extract_accuracy_v3_codex.py` as a manual-batch writer for abstract-level adjudications.
- Wrote all shortlist lanes to:
  - `data_v2_offline/extracted/accuracy_v3_codex.csv`
  - `data_v2_offline/extracted/accuracy_v3_needs_review.csv`
- Current split:
  - `260` total adjudicated rows
  - `160` rows with quantitative paired values retained in `accuracy_v3_codex.csv`
  - `100` rows routed to `accuracy_v3_needs_review.csv`
- Early pattern from the batches:
  - the heuristic quantitative-direct shortlist does contain real paired abstracts
  - but it also pulls in trust/preference studies, agreement-only studies, and workflow-deferral papers that do not report extractable paired AI-versus-physician values in the abstract
- Additional progress:
  - finished `diagnosis_reasoning_v3_core`, `admin_core`, `patient_facing_core`, and `supplemental_benchmark_implementation` shortlist adjudication
  - added merge protection in `src/extract_accuracy_v3_codex.py` so later duplicate DOI/title entries do not overwrite stronger earlier adjudications
  - many supplemental rows were true reader-study or AI-assistance benchmarks, but the lane also contained implementation, trust, ROI, review, and documentation-quality papers that were routed to `needs_review` or kept out of the pooled paired set

### End-of-session summary

- Completed the full `quantitative_direct_candidates.csv` shortlist across all four lanes (`421/421` rows reviewed through the v3 manual-batched adjudication workflow).
- Current adjudicated outputs:
  - `data_v2_offline/extracted/accuracy_v3_codex.csv`: `260` total adjudicated rows
  - `160` retained quantitative rows with non-low-confidence paired comparisons
  - `data_v2_offline/extracted/accuracy_v3_needs_review.csv`: `100` rows requiring targeted human/PDF follow-up
- Current broad directional corpus:
  - `data_v2_offline/extracted/win_rate_candidates_conservative.csv`: `951` directional abstracts
  - `data_v2_offline/extracted/win_rate_summary_conservative.csv`: lane-level Chen-style directional summary
- Created plotting script:
  - `scripts/plot_v3_summary.py`
- Current figures saved to `data_v2_offline/extracted/figures/`:
  - `v3_direction_by_comparison_type.png`
  - `v3_metric_mix_heatmap.png`
  - `v3_direction_by_lane.png`
  - `chen_style_directional_summary.png`
- Interpretation at handoff:
  - the stricter retained quantitative set (`n=160`) supports analysis of comparison type, metric mix, and AI-vs-human direction with tighter evidence standards
  - the broader directional set (`n=951`) is useful for a Chen-style descriptive win/loss screen, but it contains many `tie/noninferior`, `assisted_improvement`, and `mixed` abstracts and should not be read as a clean standalone AI-win rate
- Likely next validation steps:
  - human validation sample of ~`100` from the `951` broad directional rows
  - human review of the `100` rows in `accuracy_v3_needs_review.csv`
  - later expansion to the broader `abstract_adjudication_queue_v3.csv` (`~1,433` deduplicated rows) if needed
