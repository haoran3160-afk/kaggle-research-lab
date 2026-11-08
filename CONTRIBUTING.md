# Contributing

Start with a concrete competition failure, useful mechanism, or reproducible package problem. Explain which decision or final outcome the proposed change improves.

1. Read [AGENTS.md](AGENTS.md) and the relevant module.
2. Work on a focused branch and preserve existing project interfaces.
3. For research changes, report the control, actual intervention, complete outcomes, costs, validation exposure, and limitations. A negative result can still justify a better next decision.
4. For helper changes, run the relevant tests and an actual installation when packaging behavior changes.
5. Open a PR with the problem, final behavior, verification, and material limitations.

Do not include credentials, signed download URLs, hidden tests, reference solutions, private task data, or personal run archives. Use a small public or synthetic example where possible. Do not alter an official scorer or make undocumented benchmark exceptions.

Keep instructions focused. Prefer strengthening an existing module over adding a framework, universal scoring formula, mandatory approval gate, or a new document for every failure. Treat upstream licenses and user authorization as real boundaries.

Test command:

```bash
python -m unittest discover -s tests -v
```

Report competition efficacy separately from package correctness. Repeated trials and correction attempts must retain their original failures and full opportunity costs.
