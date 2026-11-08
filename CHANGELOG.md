# Changelog

## 1.1.0 — 2026-11-08

- When several candidates compete for scarce formal submissions, compare the value of one noisy run (knowledge-gradient style) instead of filling quota with sub-resolution single-factor diagnostics. Shrink external best-of-many scores, check which versions public per-task data covers, and when the strong candidate is not ready today submit the most informative ready one while packaging the strong one first.
- Read results at their resolution: task counts, differences within about two standard errors are non-evidence, pool repeats, no selection by a single best public score; get a repeat or paired evaluation when the reading depends on the noise estimate.
- Intelligence uses leaderboard distribution, author/team links and public result datasets as first-hand evidence, and tries other authorized routes before marking a source unresolved.
- Add `scripts/resolution.py` (standard library): `lattice` (floor and round, no single K claimed), `noise`, `compare`, `paired` (strict outcomes), `next`. Installed with the runtime.
- Remove duplicated quota wording from SKILL and progress; the allocation rule lives once in `modules/research.md`.

No competition score improvement is claimed; see the PR for the decision replay and its limits.

## 1.0.0 — 2026-11-08

First public release as **Kaggle Research Lab**, extracted from the private Kaggle Research Loop workflow. This is a new public release line; it is not a score-based promotion.

- Include all nine active workflow modules, task-specific evaluation guidance, seven effectiveness questions, four templates, and seven licensed upstream skills.
- Add system-level research across data, representations, models, tools, loops, context/memory, harnesses, stability, feedback, and candidate selection.
- Maintain automation instructions as research stages change while preserving the user's actual schedule.
- Include system research, templates, licenses, and third-party notices in real installations; use one `VERSION` file for package version reporting.
- Preserve the latest native-result readback correction from the private source: reconcile conflicting local summaries against original reports without changing the scorer.
- Publish transferable competition lessons and evidence limitations without personal raw histories or official judging assets.
- Add English and Chinese project documentation, contribution guidance, packaging tests and GitHub Actions.

No general competition score or medal improvement is claimed. Historical dispatchers and private operational receipts are not required for the active workflow and remain outside this public package.
