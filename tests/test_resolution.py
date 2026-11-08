import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("resolution", Path(__file__).resolve().parents[1] / "scripts/resolution.py")
resolution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolution)


class ResolutionTests(unittest.TestCase):
    def test_lattice_recovers_hidden_count_under_truncation(self):
        k, mode = 58, "floor"
        scores = sorted({resolution._score(n, k, mode, 2) for n in (1, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 17)})
        self.assertEqual(resolution.lattice(scores, 5, 200, mode, 2)["smallest_k"], 58)
        # The same board is impossible to render at K=58 under rounding.
        self.assertNotIn(58, resolution.lattice(scores, 5, 200, "round", 2)["consistent_k"])

    def test_counts_and_noise_from_repeats(self):
        self.assertEqual(resolution.counts_for(0.20, 58), [12])
        out = resolution.noise([[0.17, 0.13], [0.20, 0.20]], 58, "floor", 2)
        self.assertEqual(out["repeats"], [[10.0, 8.0], [12.0, 12.0]])
        self.assertAlmostEqual(out["pooled_sd_tasks"], 1.0)
        self.assertIn("warning", out)
        self.assertGreater(out["binomial_upper_sd_tasks"], out["pooled_sd_tasks"])
        with self.assertRaises(SystemExit):
            resolution.to_count(0.205, 58, "floor", 2)

    def test_compare_reads_one_task_gap_as_noise(self):
        out = resolution.compare([0.20], [0.18], 58, 1.4, "floor", 2)
        self.assertEqual(out["diff_tasks_b_minus_a"], -1.0)
        self.assertEqual(out["reading"], "within noise")
        self.assertGreater(out["mde80_tasks"], 5)

    def test_paired_sign_test_uses_only_shared_tasks(self):
        rows = [{"run": "a", "task": t, "resolved": t in "xy"} for t in "wxyz"]
        rows += [{"run": "b", "task": t, "resolved": t in "xyzw"} for t in "wxyzq"]
        out = resolution.paired(rows, "run", "a", "b", "task", "resolved")
        self.assertEqual((out["tasks_paired"], out["b_only"], out["a_only"], out["ties"]), (4, ["w", "z"], [], 2))
        self.assertEqual(out["sign_test_p"], 0.5)
        self.assertEqual(out["unpaired_tasks"], 1)

    def test_next_prefers_strong_prior_over_tweak_and_cli_prints_json(self):
        out = resolution.nxt(["tweak:12:0.7", "transfer:13:2.5"], 12, 1.0)
        self.assertEqual(out["ranked"][0]["candidate"], "transfer")
        self.assertLess(out["ranked"][1]["p_one_run_clears_2sd"], out["ranked"][0]["p_one_run_clears_2sd"])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "runs.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in [{"run": "a", "task": "t", "resolved": 0}, {"run": "b", "task": "t", "resolved": 1}]), encoding="utf-8")
            import contextlib, io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                resolution.main(["paired", str(path), "--a", "a", "--b", "b"])
            self.assertEqual(json.loads(buf.getvalue())["b_only"], ["t"])


if __name__ == "__main__":
    unittest.main()
