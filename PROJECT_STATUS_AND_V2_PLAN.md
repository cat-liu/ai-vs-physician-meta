# AI vs Physician Meta: Current State and March 2026 Expansion Plan

## Current project state

The existing pipeline in this repo is an Anthropic-based systematic review workflow:

1. `run.py search`
   - searches `PubMed`, `medRxiv` via Europe PMC, and `arXiv`
   - writes raw records to `data/raw/`
2. `run.py deduplicate`
   - merges the three sources and deduplicates by DOI, then normalized title/year
3. `run.py screen`
   - uses Claude to screen title/abstracts for inclusion
4. `run.py extract`
   - uses Claude plus Unpaywall/PDF fallback to extract arm-level AI-vs-physician comparison data

## Current saved outputs

As of the files currently in the repo:

- `data/raw/pubmed_raw.csv`: 769 records
- `data/raw/medrxiv_raw.csv`: 2,693 records
- `data/raw/arxiv_raw.csv`: 25 records
- `data/raw/combined_deduped.csv`: 3,475 unique records
- `data/extracted/screened.csv`: 300 screened records
- `data/extracted/included.csv`: 43 included studies
- `data/extracted/extracted_arms.csv`: 233 comparison-arm rows

## Current scope and methodology

### Search scope

The current search is focused on:

- generative AI / LLM studies
- clinician-facing diagnostic or triage tasks
- explicit human clinician / physician comparison arms

The repo also contains broader v3 inclusion notes for:

- treatment decisions
- clinical management decisions
- risk stratification / prognosis

### Screening methodology

The original pipeline uses Claude to classify each title/abstract as:

- `include`
- `exclude`
- `uncertain`

and to flag:

- physician comparison present
- physician condition detail present
- quantitative accuracy metric present

### Extraction methodology

The original extractor is arm-level and tries to recover:

- AI arm vs physician arm type
- physician condition / specialty / expertise
- AI model
- `accuracy_ai`
- `accuracy_physician`
- metric type
- sample size
- significance
- tier (real-world vs structured cases vs vignettes)

## Why a parallel workflow was added

You asked to expand and rerun the meta-analysis without spending Anthropic API money and without breaking the original workflow.

To do that, a second workflow now exists in parallel:

- `config/queries_v2_offline.py`
- `run_offline_v2.py`
- `src/search_pubmed_v2.py`
- `src/search_medrxiv_v2.py`
- `src/search_scopus_v2.py`
- `src/screen_offline_v2.py`
- `src/extract_accuracy_offline_v2.py`

These files write only to:

- `data_v2_offline/raw/`
- `data_v2_offline/extracted/`

The original Anthropic path is untouched.

## What the v2 offline workflow changes

### Date range

The parallel workflow extends the end date to:

- `2026/03/31`

### Source coverage

The parallel workflow targets:

- `PubMed`
- `medRxiv`
- `Scopus`

It does not depend on Anthropic.

### Retrieval structure

The saved v2 workflow now uses four separate retrieval lanes:

- `diagnosis_reasoning_v3_core`
- `patient_facing_core`
- `admin_core`
- `supplemental_benchmark_implementation`

The first three are intended to be the main analytic corpora.
The supplemental lane is a recall safeguard for likely-missed benchmark,
implementation, and collaborative-workflow studies.

### Scope expansion

The v2 offline queries broaden beyond diagnosis/triage and beyond LLM-only studies to include:

- classical healthcare AI / ML studies
- deep learning and predictive model studies
- treatment decisions
- management decisions
- risk prediction / prognosis
- treatment decisions
- management decisions
- risk prediction / prognosis
- documentation
- billing
- coding
- scheduling
- other healthcare workflow tasks

### Screening approach

The v2 screener is rule-based, not model-based.

It uses text signals for:

- AI / ML presence
- clinician/physician/staff comparator presence
- healthcare task presence
- exclusion patterns like reviews, protocols, and student/exam-only papers

The output still preserves:

- `include`
- `exclude`
- `uncertain`

so you can do manual review where needed.

### Metric extraction approach

The v2 extractor is abstract-based and heuristic.

It does **not** attempt to reproduce full Claude arm extraction. Instead it creates a reviewable accuracy-candidate table with:

- guessed AI model
- guessed metric type
- candidate AI value
- candidate physician value
- metric-bearing abstract snippets
- manual review flag

This is meant to help you pull AI-vs-human comparison accuracy rates without API cost, while keeping the results auditable.

## Revised v2 scope decision

The revised v2 scope is now:

- include all healthcare AI studies
- include healthcare administrative workflow AI studies
- require a human comparison arm or explicit human-performance benchmark
- allow both quantitative and qualitative human comparisons

That means the expanded workflow is now intended to capture:

- AI vs physician
- AI vs clinician
- AI vs nurse
- AI vs staff / human workflow performance
- direct quantitative head-to-head comparisons
- qualitative clinician or staff benchmarking studies

including studies in:

- diagnosis
- triage
- treatment and management
- prognosis / risk prediction
- imaging / test interpretation
- documentation
- coding
- billing
- scheduling
- inbox or operational workflow

## Comparison types to preserve during review

Within the expanded scope, it will be useful to keep comparison type explicit:

- `quantitative_direct`
- `quantitative_partial`
- `qualitative_only`

That lets the search and screening stay broad enough to avoid missing relevant
human-comparison studies, while preserving a stricter subset later for pooled
accuracy analysis.

## Scopus note

Scopus in the new workflow supports two modes:

1. API mode
   - set `SCOPUS_API_KEY`
   - optional `SCOPUS_INSTTOKEN`
2. CSV import mode
   - export Scopus results manually and pass `--scopus-csv path/to/export.csv`

CSV import is the easiest route if API access is not available.

## Suggested next run order

From the repo root:

```bash
python run_offline_v2.py search --scopus-csv /path/to/scopus_export.csv
python run_offline_v2.py deduplicate
python run_offline_v2.py screen
python run_offline_v2.py extract
```

Or all at once:

```bash
python run_offline_v2.py all --scopus-csv /path/to/scopus_export.csv
```

## Important caveats

- The offline v2 screening is more conservative than Claude and will need human spot-checking.
- The offline v2 accuracy extraction is a candidate-harvesting step, not a final adjudicated arm table.
- Full-text extraction is still the strongest path when abstracts do not report paired AI and physician metrics.
- The original Anthropic workflow remains the better path for final structured extraction, but the v2 offline workflow lets you expand the corpus and start the metric pull without extra model cost.
