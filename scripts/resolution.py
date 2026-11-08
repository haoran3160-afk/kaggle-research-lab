#!/usr/bin/env python3
"""Read leaderboard and paired-eval results at the resolution they actually have.

Standard library only. Every subcommand prints JSON so an agent can quote it.

  lattice  task counts K consistent with public scores, under floor and round
  noise    single-run SD in tasks from repeated runs of one config
  compare  difference between two arms of repeated official scores
  paired   per-task wins/losses on the same tasks + exact sign test
  next     value of spending one noisy run on each candidate (knowledge gradient)
"""
import argparse
import json
import math
import sys
from collections import defaultdict


def _score(n, k, mode, dp):
    x = n / k
    s = 10 ** dp
    if mode == "floor":
        return math.floor(x * s + 1e-9) / s
    return math.floor(x * s + 0.5) / s


def counts_for(score, k, mode="floor", dp=2):
    """All integer task counts whose displayed score equals `score`."""
    return [n for n in range(k + 1) if abs(_score(n, k, mode, dp) - score) < 1e-9]


def lattice(scores, kmin, kmax, dp):
    out = {}
    for mode in ("floor", "round"):
        ks = [k for k in range(kmin, kmax + 1) if all(counts_for(s, k, mode, dp) for s in scores)]
        out[mode] = {"smallest_k": ks[0] if ks else None, "consistent_k": ks[:12], "n_consistent": len(ks)}
    out["note"] = ("scores alone do not identify K or the display mode; the smallest K is a guess "
                   "unless another source (rules, task list, audit) fixes K or the mode")
    return out


def to_count(score, k, mode, dp):
    c = counts_for(score, k, mode, dp)
    if not c:
        raise SystemExit(f"score {score} is impossible for K={k} ({mode}); run lattice first")
    return sum(c) / len(c)


def noise(groups, k, mode, dp):
    ambiguous = [s for g in groups for s in g if len(counts_for(s, k, mode, dp)) > 1]
    ss, dof, used = 0.0, 0, []
    for g in groups:
        n = [to_count(s, k, mode, dp) for s in g]
        if len(n) < 2:
            continue
        m = sum(n) / len(n)
        ss += sum((x - m) ** 2 for x in n)
        dof += len(n) - 1
        used.append(n)
    all_n = [to_count(s, k, mode, dp) for g in groups for s in g]
    p = sum(all_n) / len(all_n) / k
    binom = math.sqrt(k * p * (1 - p))
    out = {"k": k, "binomial_sd_tasks": round(binom, 2),
           "note": ("pool only repeats of one unchanged config; binomial assumes independent tasks and is not "
                    "a bound when timeouts or platform load move many tasks together")}
    if ambiguous:
        out["ambiguous_scores"] = ambiguous
    if dof:
        out.update(pooled_sd_tasks=round(math.sqrt(ss / dof), 2), dof=dof, repeats=used)
        if dof < 3:
            out["warning"] = "fewer than 3 degrees of freedom: treat pooled SD as a rough guess"
    return out


def _phi(z):
    return math.exp(-z * z / 2) / math.sqrt(2 * math.pi)


def _cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def compare(a, b, k, sd, mode, dp):
    na = [to_count(s, k, mode, dp) for s in a]
    nb = [to_count(s, k, mode, dp) for s in b]
    d = sum(nb) / len(nb) - sum(na) / len(na)
    se = sd * math.sqrt(1 / len(na) + 1 / len(nb))
    z = d / se if se else 0.0
    out = {"a_tasks": na, "b_tasks": nb, "diff_tasks_b_minus_a": round(d, 2), "se_tasks": round(se, 2),
           "z": round(z, 2), "p_two_sided_normal": round(2 * (1 - _cdf(abs(z))), 3),
           "mde80_tasks": round(2.8 * se, 2),
           "reading": "within 2 SE" if abs(z) < 2 else "beyond 2 SE"}
    p = (sum(na) + sum(nb)) / (len(na) + len(nb)) / k
    bsd = math.sqrt(k * p * (1 - p))
    if bsd > sd:
        bz = d / (bsd * math.sqrt(1 / len(na) + 1 / len(nb)))
        out["reading_if_sd_is_binomial"] = "within 2 SE" if abs(bz) < 2 else "beyond 2 SE"
        if out["reading_if_sd_is_binomial"] != out["reading"]:
            out["warning"] = "conclusion depends on the noise estimate; get a repeat or a paired evaluation"
    return out


def _binom_two_sided(w, n):
    if n == 0:
        return 1.0
    k = min(w, n - w)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def _outcome(v):
    if isinstance(v, bool):
        return v
    if v in (0, 1):
        return bool(v)
    if isinstance(v, str) and v.strip().lower() in ("true", "false", "0", "1", "yes", "no"):
        return v.strip().lower() in ("true", "1", "yes")
    raise SystemExit(f"cannot read outcome {v!r} as solved/unsolved")


def paired(rows, key, a, b, task, outcome):
    res = defaultdict(dict)
    for r in rows:
        if r.get(key) in (a, b):
            if r[key] in res[r[task]]:
                raise SystemExit(f"duplicate row for {r[key]} on {r[task]}; aggregate repeats first")
            res[r[task]][r[key]] = _outcome(r[outcome])
    if not res:
        raise SystemExit(f"no rows for {a} or {b} under key {key!r}")
    both = {t: v for t, v in res.items() if a in v and b in v}
    wins = sorted(t for t, v in both.items() if v[b] and not v[a])
    losses = sorted(t for t, v in both.items() if v[a] and not v[b])
    ties = len(both) - len(wins) - len(losses)
    return {"tasks_paired": len(both), "a_solved": sum(v[a] for v in both.values()),
            "b_solved": sum(v[b] for v in both.values()), "b_only": wins, "a_only": losses, "ties": ties,
            "sign_test_p": round(_binom_two_sided(len(wins), len(wins) + len(losses)), 3),
            "unpaired_tasks": len(res) - len(both)}


def _gain(delta, s):
    if s <= 0:
        return max(delta, 0.0)
    z = delta / s
    return delta * _cdf(z) + s * _phi(z)


def nxt(cands, champion, sd):
    """Knowledge-gradient style value of one noisy run against a fixed champion.

    After one run with noise sd, the posterior mean moves with spread
    s = tau^2 / sqrt(tau^2 + sd^2); a run is worth E[max(posterior mean - champion, 0)].
    Unlike plain expected improvement, the value shrinks as run noise grows relative to the prior spread.
    """
    out = []
    for c in cands:
        name, mu, tau = c.split(":")
        mu, tau = float(mu), float(tau)
        if tau < 0 or sd < 0:
            raise SystemExit("prior and run SD must be non-negative")
        s = tau * tau / math.sqrt(tau * tau + sd * sd) if tau else 0.0
        obs = math.sqrt(tau ** 2 + sd ** 2)
        moves = (1 - _cdf((champion + 2 * sd - mu) / obs)) + _cdf((champion - 2 * sd - mu) / obs) if obs else 0.0
        out.append({"candidate": name, "prior_mean_tasks": mu, "prior_sd_tasks": tau,
                    "p_better_than_champion": round(_cdf((mu - champion) / tau), 3) if tau else float(mu > champion),
                    "value_of_one_run_tasks": round(_gain(mu - champion, s), 2),
                    "p_one_run_beyond_2sd_either_way": round(moves, 3)})
    out.sort(key=lambda x: -x["value_of_one_run_tasks"])
    return {"champion_tasks": champion, "run_sd_tasks": sd, "ranked": out,
            "note": ("priors are judgement: shrink external best-of-many scores, and justify a wide prior SD from the "
                     "observed spread of comparable changes, or it will win by width alone. The value assumes "
                     "the champion is fixed and the run happens today; readiness is not modelled")}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--k", type=int, default=0, help="hidden task count (from lattice)")
    p.add_argument("--mode", choices=["floor", "round"], help="how the board shows scores (required with --k)")
    p.add_argument("--dp", type=int, default=2, help="decimals shown on the board")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("lattice"); s.add_argument("scores", type=float, nargs="+")
    s.add_argument("--kmin", type=int, default=5); s.add_argument("--kmax", type=int, default=500)
    s = sub.add_parser("noise"); s.add_argument("--group", action="append", required=True,
                                                help="comma-separated scores of one unchanged config")
    s = sub.add_parser("compare"); s.add_argument("--a", type=float, nargs="+", required=True)
    s.add_argument("--b", type=float, nargs="+", required=True); s.add_argument("--sd", type=float, required=True)
    s = sub.add_parser("paired"); s.add_argument("file", help="JSONL, one row per (arm, task)")
    s.add_argument("--a", required=True); s.add_argument("--b", required=True)
    s.add_argument("--key", default="run"); s.add_argument("--task", default="task")
    s.add_argument("--outcome", default="resolved")
    s = sub.add_parser("next"); s.add_argument("--champion", type=float, required=True, help="champion tasks")
    s.add_argument("--sd", type=float, required=True, help="single-run SD in tasks")
    s.add_argument("cands", nargs="+", help="name:prior_mean_tasks:prior_sd_tasks")
    a = p.parse_args(argv)
    if a.cmd in ("noise", "compare") and not a.k:
        p.error("--k is required; get it from lattice plus a non-score source")
    if a.cmd in ("noise", "compare") and not a.mode:
        p.error("--mode is required: scores alone cannot tell floor from round")
    if a.cmd == "lattice":
        r = lattice(a.scores, a.kmin, a.kmax, a.dp)
    elif a.cmd == "noise":
        r = noise([[float(x) for x in g.split(",")] for g in a.group], a.k, a.mode, a.dp)
    elif a.cmd == "compare":
        r = compare(a.a, a.b, a.k, a.sd, a.mode, a.dp)
    elif a.cmd == "paired":
        with open(a.file, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        r = paired(rows, a.key, a.a, a.b, a.task, a.outcome)
    else:
        r = nxt(a.cands, a.champion, a.sd)
    json.dump(r, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
