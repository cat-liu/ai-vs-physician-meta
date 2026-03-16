# Known Target Notes

Reference set: recent ARISE-style physician-versus-AI / clinician-AI collaboration papers used as a sanity check for retrieval.

## What the misses tend to look like

The core retrieval lanes miss some target papers not because they are outside the intended topic, but because they often do **not** foreground explicit comparison language in the title.

Common title/abstract patterns among likely misses:

- branded system names with little descriptive context
  - `TRICORDER`
  - `MASAI`
  - `DeepRare`

- implementation-forward wording rather than direct head-to-head wording
  - `real-world study`
  - `clinical decision support`
  - `complex cardiology care`
  - `collaborative workflows`

- assistance / teammate framing rather than explicit `versus` language
  - `assistance`
  - `collaborative`
  - `tool to teammate`
  - `human-AI collaboration`

- benchmark phrasing that emphasizes reasoning or safety more than comparator wording
  - `diagnostic reasoning`
  - `reasoning tasks`
  - `clinically safe`
  - `differential diagnosis`

## What the current core lanes catch well

The current core lanes catch studies that use stronger abstract/title signals such as:

- `randomized controlled trial`
- `physician performance`
- `comparative study`
- `accuracy`
- `reader study`
- `assisted` / `unassisted`

## Practical implication

The core lanes are appropriate for the main comparison corpus, but they will not recover every benchmark or implementation paper that matters.

That is why the project keeps a separate:

- `supplemental_benchmark_implementation`

lane as a recall safeguard.
