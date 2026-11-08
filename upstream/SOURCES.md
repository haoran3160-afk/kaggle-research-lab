# Bundled upstream sources

Retrieved 2026-11-04 from original public repositories. Skill content is kept as upstream supplied it; the parent workflow defines the bounded Kaggle task and how existing user authorization applies. Only the listed skill directories are bundled. No file-digest checks are required.

| Source | Selected skills | Observed repository stars / forks | License |
|---|---|---:|---|
| https://github.com/openai/skills | yeet, gh-fix-ci, gh-address-comments | 28,509 / 1,982 | Apache-2.0 LICENSE.txt accompanies each selected folder |
| https://github.com/obra/superpowers | systematic-debugging, requesting-code-review | 312,147 / 27,767 | MIT, superpowers/LICENSE |
| https://github.com/K-Dense-AI/scientific-agent-skills | scientific-brainstorming, scientific-critical-thinking | 56,053 / 4,927 | MIT, scientific/LICENSE.md |

Repository counts were read through GitHub API during this session. They indicate community attention, not per-skill deployment counts or demonstrated Kaggle gains. Reviewed recent push dates: OpenAI Oct28, Superpowers Nov3, K-Dense Nov2. Skill contents, dependencies and fit were inspected separately.

Upstream optional helpers are included for completeness, but the adapter does not invoke matrix scoring, validation certificates, paid diagrams, unrelated clinical procedures or whole-framework bootstrapping. Normal Git revisions identify code changes without additional hash manifests. For an upstream update, reread the affected skill's behavior and our adapter before changing a running competition; do not automatically update all dependencies mid-experiment.

Kaggle runtime uses https://github.com/Kaggle/kaggle-cli (official tool, 7,644stars/1,446forks, Apache-2.0), not a locally invented “official skill”. Learning resources are retrieved from actual courses and author documentation; no unsuitable high-star package is installed merely to fill a module.
