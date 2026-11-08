# Changelog

## 1.1.0 — 2026-11-08

- Allocate scarce high-resolution evaluation (formal submissions, full evaluations) by expected gain against measured channel resolution instead of filling quota with sub-resolution single-factor diagnostics. Strong same-leaderboard evidence is no longer parked behind weaker n=1 screens.
- Read results at their resolution: convert scores to task counts, treat differences within about two run-noise SDs as non-evidence, pool repeated runs of one configuration, and do not select by a single best public score.
- Intelligence uses leaderboard distribution, author/team links and public result datasets as first-hand evidence, and tries other authorized routes before marking a source unresolved.
- Add `scripts/resolution.py` (standard library): `lattice`, `noise`, `compare`, `paired`, `next`. Installed with the runtime.
- Sync two later private-mainline corrections: distinguish not-offered / not-chosen / bad-arguments / failed tool use from real requests and artifacts; reuse mature SDK create/update semantics and confirmed immutable receipts.
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
