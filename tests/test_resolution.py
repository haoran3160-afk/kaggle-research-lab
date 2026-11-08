import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("resolution", Path(__file__).resolve().parents[1] / "scripts/resolution.py")
resolution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolution)

# Public Gemma 4 developer-agent scores (ours plus one public team), as displayed on the board.
BOARD = [0.29, 0.24, 0.22, 0.20, 0.18, 0.17, 0.15, 0.13, 0.12, 0.08, 0.06, 0.05, 0.01]


def run_cli(args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        resolution.main(args)
    return json.loads(buf.getvalue())


class ResolutionTests(unittest.TestCase):
    def test_lattice_reports_both_display_modes_without_picking_one(self):
        out = resolution.lattice(BOARD, 5, 200, 2)
        self.assertEqual(out["floor"]["smallest_k"], 58)
        self.assertNotIn(58, out["round"]["consistent_k"])
        self.assertIsNotNone(out["round"]["smallest_k"])  # rounding with a larger K also fits
        self.assertGreater(out["floor"]["n_consistent"], 1)
        self.assertIn("do not identify", out["note"])

    def test_noise_pools_repeats_and_rejects_ambiguous_counts(self):
        self.assertEqual(resolution.counts_for(0.20, 58), [12])
        out = resolution.noise([[0.17, 0.13], [0.20, 0.20]], 58, "floor", 2)
        self.assertEqual(out["repeats"], [[10.0, 8.0], [12.0, 12.0]])
        self.assertAlmostEqual(out["pooled_sd_tasks"], 1.0)
        self.assertIn("warning", out)
        with self.assertRaises(SystemExit):
            resolution.noise([[0.20, 0.20]], 250, "floor", 2)
        with self.assertRaises(SystemExit):
            resolution.to_count(0.205, 58, "floor", 2)

    def test_compare_warns_when_noise_estimate_decides_the_reading(self):
        out = resolution.compare([0.20, 0.20], [0.15], 58, 1.0, "floor", 2)
        self.assertEqual(out["diff_tasks_b_minus_a"], -3.0)
        self.assertEqual(out["reading"], "beyond 2 SE")
        self.assertEqual(out["reading_if_sd_is_binomial"], "within 2 SE")
        self.assertIn("warning", out)
        self.assertEqual(resolution.compare([0.20], [0.18], 58, 1.4, "floor", 2)["reading"], "within 2 SE")

    def test_paired_reads_outcomes_strictly(self):
        rows = [{"run": "a", "task": t, "resolved": t in "xy"} for t in "wxyz"]
        rows += [{"run": "b", "task": t, "resolved": "true" if t in "xyzw" else "false"} for t in "wxyzq"]
        out = resolution.paired(rows, "run", "a", "b", "task", "resolved")
        self.assertEqual((out["tasks_paired"], out["b_only"], out["a_only"], out["ties"]), (4, ["w", "z"], [], 2))
        self.assertEqual(out["sign_test_p"], 0.5)
        self.assertEqual(out["unpaired_tasks"], 1)
        one_arm = [r for r in rows if r["run"] == "a"]
        disjoint = [{"run": "a", "task": "t", "resolved": 1}, {"run": "b", "task": "u", "resolved": 1}]
        for bad in (rows + [rows[0]], [{"run": "a", "task": "t", "resolved": None}], one_arm, disjoint):
            with self.assertRaises(SystemExit):
                resolution.paired(bad, "run", "a", "b", "task", "resolved")

    def test_next_values_one_noisy_run(self):
        out = resolution.nxt(["v24:13.5:2", "F2:12:1", "K0:12:0"], 12, 2.0)
        ranked = {r["candidate"]: r for r in out["ranked"]}
        # Information gain can rank below a lower-mean candidate; deployment advantage is separate.
        self.assertEqual([r["candidate"] for r in out["ranked"]], ["F2", "v24", "K0"])
        # A run is worth less when its noise is large relative to the prior spread.
        quiet = resolution.nxt(["wild:12:5"], 12, 1.0)["ranked"][0]["value_of_one_run_tasks"]
        noisy = resolution.nxt(["wild:12:5"], 12, 6.0)["ranked"][0]["value_of_one_run_tasks"]
        self.assertLess(noisy, quiet)
        self.assertEqual(ranked["K0"]["value_of_one_run_tasks"], 0.0)
        self.assertEqual(ranked["K0"]["p_better_than_champion"], 0.0)
        # s = tau^2/sqrt(tau^2+sd^2); for F2 s = 1/sqrt(5), value = s*phi(0)
        self.assertAlmostEqual(ranked["F2"]["value_of_one_run_tasks"], round(0.4472136 * 0.3989423, 2))
        with self.assertRaises(SystemExit):
            resolution.nxt(["bad:12:-1"], 12, 1.0)

    def test_one_run_value_does_not_reward_already_known_advantage(self):
        rows = resolution.nxt(["known:15:0", "unknown:12:2"], 12, 2)["ranked"]
        self.assertEqual(rows[0]["candidate"], "unknown")
        known = next(row for row in rows if row["candidate"] == "known")
        self.assertEqual(known["prior_mean_advantage_tasks"], 3.0)
        self.assertEqual(known["value_of_one_run_tasks"], 0.0)
        near = resolution.nxt(["above:13:2", "below:11:2"], 12, 2)["ranked"]
        self.assertEqual(near[0]["value_of_one_run_tasks"], near[1]["value_of_one_run_tasks"])

    def test_zero_noise_and_rounded_count_ambiguity_are_not_false_evidence(self):
        for sd in (0, -1, float("nan")):
            with self.assertRaises(SystemExit):
                resolution.compare([0.20], [0.15], 58, sd, "floor", 2)
        with self.assertRaises(SystemExit):
            resolution.compare([0.20], [0.24], 250, 2, "floor", 2)
        with self.assertRaises(SystemExit):
            resolution.nxt(["invalid:nan:2"], 12, 2)

    def test_cli_requires_display_mode_and_reads_jsonl(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                resolution.main(["--k", "58", "noise", "--group", "0.20,0.20"])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runs.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in [{"run": "a", "task": "t", "resolved": 0}, {"run": "b", "task": "t", "resolved": 1}]), encoding="utf-8")
            self.assertEqual(run_cli(["paired", str(path), "--a", "a", "--b", "b"])["b_only"], ["t"])


if __name__ == "__main__":
    unittest.main()
